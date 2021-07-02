# DDD(123) - Library for procedural generation of 2D and 3D geometries and scenes
# Copyright (C) 2021 Jose Juan Montes
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import logging
import math
import random
import sys
import numpy as np

from ddd.ddd import DDDObject2, DDDObject3
from ddd.ddd import ddd
from ddd.pack.sketchy import plants, urban
from ddd.geo import terrain
from ddd.core.exception import DDDException
from ddd.util.dddrandom import weighted_choice
from ddd.pack.sketchy.buildings import window_with_border, door
from collections import defaultdict
from ddd.osm.buildings.building import BuildingContact, BuildingSegment
from shapely.strtree import STRtree


# Get instance of logger for this module
logger = logging.getLogger(__name__)



class Buildings2DOSMBuilder():

    def __init__(self, osmbuilder):

        self.osm = osmbuilder

    def preprocess_buildings_parenting(self, buildings_2d):
        """
        Resolves ddd:building:parts and ddd:building:parent relationships between all building parts.
        """

        logger.info("Preprocessing buildings and bulding parts 2D (%d objects)", len(buildings_2d.children))

        # Initialization of technical metadata
        for building in list(buildings_2d.children):
            if 'ddd:building:parts' not in building.extra:
                building.extra['ddd:building:parts'] = []
            #building.extra['ddd:building:items'] = []

        '''
        logger.info("Sorting 2D buildings (%d).", len(buildings_2d.children))
        buildings_2d.children.sort(key=lambda a: a.get('ddd:area:area'))  # extra['ddd:area:area'])
        '''

        #buildings_2d.index_create()

        # TODO: create nested buildings separately, consider them part of the bigger building for subtraction)
        # Assign each building part to a building, or transform it into a building if needed
        #features = sorted(features_2d.children, key=lambda f: f.geom.area)
        features_2d_original = list(buildings_2d.children)
        for feature in list(buildings_2d.children):

            if feature.geom.type == 'Point': continue

            # Skip parents, so nested buildings (eg. Torre de Hercules) are considered independently
            if feature.extra.get('osm:building', None): continue

            if feature.extra.get('osm:building:part', None) is None and feature.extra.get('osm:building', None) is None: continue

            # Find building
            #buildings = features_2d.select(func=lambda o: o.extra.get('osm:building', None) and ddd.polygon(o.geom.exterior.coords).contains(feature))
            feature_margin = feature.buffer(-0.05)
            building_parents = buildings_2d.select(func=lambda o: o.extra.get('osm:building', None) and o != feature and o.contains(feature_margin) and o in features_2d_original)

            if len(building_parents.children) == 0:
                if feature.extra.get('osm:building', None) is None:

                    # TODO: Maybe we could group "touching" building parts into building/new building (eg. Aquarium Finisterrae, Torre de Hercules stairs...)
                    logger.debug("Building part with no building: %s", feature)
                    #building = ddd.shape(feature.geom, name="Building (added): %s" % feature.name)
                    #building.extra['osm:building'] = feature.extra.get('osm:building:part', 'yes')  # TODO: Should be DDD
                    #building.extra['ddd:building:parts'].append(feature)
                    #feature.extra['ddd:building:parent'] = building
                    #buildings_2d.append(building)
                    feature.extra['osm:building'] = feature.extra.get('osm:building:part', 'yes')  # TODO: Should be DDD

            elif len(building_parents.children) > 1:
                # Sort by area and get the smallest one
                # Needs to be multilevel as buildings can be multilevel (eg Torre de Hercules)
                building_parents.children.sort(key=lambda b: b.geom.area, reverse=False)
                logger.debug("Building part with multiple buildings: %s -> %s", feature, building_parents.children)

                feature.extra['ddd:building:parent'] = building_parents.children[0]
                #if 'ddd:building:parts' not in building_parents.children[0].extra:
                #    building_parents.children[0].extra['ddd:building:parts'] = []
                building_parents.children[0].extra['ddd:building:parts'].append(feature)

            else:
                logger.debug("Associating building part to building: %s -> %s", feature, building_parents.children[0])
                feature.extra['ddd:building:parent'] = building_parents.children[0]
                #if 'ddd:building:parts' not in building_parents.children[0].extra:
                #    building_parents.children[0].extra['ddd:building:parts'] = []
                building_parents.children[0].extra['ddd:building:parts'].append(feature)

        #buildings_2d.index_clear()


    def preprocess_building_fixes(self, buildings_2d):
        """
        Arranges different building parts, subtracting them as needed. The building footprint
        is taken as what remains after subtracting other parts inside. Floors and height need
        to be considered here (?)

        Following: https://wiki.openstreetmap.org/wiki/Simple_3D_Buildings

        This needs to be done before calculating contacts (buildings analyze), as it may alter building geometry.
        """

        # Normalize: check if there are building parts, and if needed create a building part to
        # fill the footprint (for buildings that do not meet the new "entirely filled" norm).

        # Resolve heights (by floor height, height_min, etc)

        # Subtract overlapping areas that match exactly (or at min_height?)
        # Subtracting should not be needed for new buildings with building parts and filled footprint, which should be ignored.
        # But for those non following that, first calculate if the remaining footprint is significant and needs to be added.

        #logger.info("Fixing building parts as needed.")

        for building_2d in list(buildings_2d.children):

            # Process only parents, as children are processed inside
            if building_2d.extra.get('ddd:building:parent', None) in (None, building_2d):

                '''
                if 'Antigo' in building_2d.get('osm:name', ""):
                    building_2d.dump(data=True)
                    ddd.group([ddd.group2(building_2d.get('ddd:building:parts')).triangulate(),
                               building_2d.material(ddd.MAT_HIGHLIGHT).triangulate().translate([0, 0, -5])]).show()
                '''

                parts = building_2d.extra.get('ddd:building:parts', None)
                if not parts: continue

                entire_building_2d = ddd.group2()
                #building_2d.geom = None  # Geom is needed for centroid, but this geometry shall not be considered :-?

                for part in (parts + [building_2d]):

                    if part != building_2d:  #  and part.extra.get('osm:building', None) is not None:
                        #part.set('ddd:building:elevation:min', default=elevation_min)
                        #part.set('ddd:building:elevation:max', default=elevation_max)
                        part.set('osm:building:part', default=building_2d.get('osm:building'))  ## TODO: Should be DDD
                        entire_building_2d.append(part)

                    # Remove the rest of the building
                    # TODO: Only ground parts
                    if part == building_2d and parts:
                        #building_2d.dump(data=True)
                        part = part.copy()
                        entire_building_2d = entire_building_2d  # Tolerance margin for "not-entirelly-filled" building footprints
                        part_remaining = part.subtract(entire_building_2d.buffer(0.05)).clean(0.01)
                        part_remaining.validate()

                        if not part_remaining.is_empty():
                            part = part.subtract(entire_building_2d).clean(-0.01)
                            #part.validate()

                            logger.info("Fixing building with non-filled footprint: %s (%d parts)", building_2d, len(parts))

                            '''
                            if 'Antigo' in building_2d.get('osm:name', ""):
                                building_2d.dump(data=True)
                                ddd.group([building_2d, part.material(ddd.MAT_HIGHLIGHT)]).show()
                            '''

                            del part.extra['osm:building']
                            part.set('ddd:building:parts', [])
                            part.set('osm:building:part', building_2d.get('osm:building'))  # TODO: Shall be ddd:building...
                            part.set('ddd:building:parent', building_2d)
                            part.set('ddd:building:part:fixed', True)
                            building_2d.geom = None
                            for b2d in part.individualize(always=True).children:  # Flatten multipolygons
                                building_2d.get('ddd:building:parts').append(b2d)
                                buildings_2d.append(b2d)

                        #logger.debug("Removing parent building geometry: %s", building_2d)
                        building_2d.geom = None  # TODO: We may need this footprint for convex shape calculation :?

                '''
                if 'Antigo' in building_2d.get('osm:name', ""):
                    building_2d.dump(data=True)
                    ddd.group(building_2d.get('ddd:building:parts') + [building_2d.material(ddd.MAT_HIGHLIGHT)]).show()
                '''

        #buildings_2d.dump()
        #buildings_2d.show()

    def preprocess_building_reparent(self, buildings_2d):
        """
        This uses building:parent relations to build the node hierarchy.
        Buildings are kept in a flatten hierarchy (as they came in) until this point.
        """

        for building in list(buildings_2d.children):
            parent = building.extra.get('ddd:building:parent', None)
            #logger.debug(f"Building: {building} Parent: {parent}")
            if parent:
                buildings_2d.remove(building)
                parent.append(building)
                building.set('ddd:building:items', [])
            elif not building.children:
                building.set('ddd:building:items', [])
            else:
                # Has children and no parent: should not have own geometry
                building.geom = None  # Geom is needed for centroid, but this geometry shall not be considered :-?


    def process_buildings_analyze(self, buildings, ways_ref):
        """
        This is part of the "structured" stage.
        This phase processes building (parts) and generates floors, segments, facades, building contact information, etc...

        Buildings must already have been selected, parent child relationships resolved, and building parts are all independent.
        """

        logger.info("Adding building analysis data (%d buildings)", len(buildings.children))

        buildings_ref = buildings

        buildings_ref.index_create()
        ways_ref.index_create()

        self._vertex_cache = defaultdict(list)
        # Note that parts are processed in an unordered (flattened) way here
        selected_parts = buildings.select(func=lambda o: o.geom, recurse=True)
        for part in selected_parts.children:
            if part.is_empty(): continue
            if part.get('ddd:building:parts', None): continue  # Ignore parents as they are not rendered
            vertices = part.vertex_list(recurse=False)  # This will fail if part had no geometry (eg. it was empty or children-only)
            for vidx, v in enumerate(vertices[:-1]):  # ignoring last vertex, repeated
                vidx = vidx % (len(vertices) - 1)
                self._vertex_cache[v].append((part, vidx))

        for part in selected_parts.children:
            if part.is_empty():
                logger.warn("Skipping analysis of building with empty geometry: %s", part)
                continue
            if part.geom.type != 'Polygon':
                logger.warn("Skipping analysis of building with non Polygon geometry (not implemented): %s", part)
                continue
            if part.get('ddd:building:parts', None): continue  # Ignore parents as they are not rendered
            self.process_building_contacts(part)
            self.process_building_convex_hull_create(part)
            self.process_building_segments_analyze(part, buildings_ref, ways_ref)
            self.process_building_hull_analyze(part, buildings_ref, ways_ref)

        buildings_ref.index_clear()
        ways_ref.index_clear()


    def process_building_contacts(self, part):
        """
        Note that elevation is not yet available at this point.
        """

        # Find contacted building parts
        vertices = part.vertex_list(recurse=False)  # This will fail if part had no geometry (eg. it was empty or children-only)
        contacted = []
        for vidx, v in enumerate(vertices[:-1]):
            vidx = vidx % (len(vertices) - 1)
            contacted = contacted + [BuildingContact(pc[0], vidx, pc[1]) for pc in self._vertex_cache[v] if pc[0] != part]
        #part.set('ddd:building:contacts', list(set(contacted)))
        part.set('ddd:building:contacts', {c.self_idx: c for c in list(set(contacted))} )

        # Mark each segment with:
        #seg_length = np.sqrt(dir_vec.dot(dir_vec))
        # Segment length, corresponding convex_hull_segment, building + segment contacts (no floor, elevation is not yet) + vertex contacts?, floors spanned...
        # Forward_object ref + distance
        segments = []
        for sidx, (s1, s2) in enumerate(zip(vertices[:-1], vertices[1:])):
            segment = BuildingSegment(part, sidx, s1, s2)
            #v0, v1 = (np.array(v0), np.array(v1))
            #dir_vec = v1 - v0
            #dir_angle = math.atan2(dir_vec[1], dir_vec[0])

            segments.append(segment)  # Use type!
        part.set('ddd:building:segments', segments)


    def process_building_convex_hull_create(self, part):

        # Convex hull
        # Generate convex hull segment,
        convex = part.convex_hull()

        # Align vertex order and winding (also used eg. extrude_between_geoms_wrap)
        convex = ddd.geomops.vertex_order_align_snap(convex, part)

        vertices = convex.vertex_list(recurse=False)
        segments = []
        for sidx, (s1, s2) in enumerate(zip(vertices[:-1], vertices[1:])):
            segment = BuildingSegment(part, sidx, s1, s2)
            segments.append(segment)  # Use type!

        part.set('ddd:building:convex', convex)
        part.set('ddd:building:convex:segments', segments)

        # Link segments in the geometry to the convex hull, using common vertices to define shared segments
        # This method requires the second to have equal or less segments than the first one
        # This also requires polygon windings to be equal, and start/end vertices to be aligned (see vertex_order_align_snap() before)
        segs_part = part.get('ddd:building:segments')
        segs_convex = segments

        seg_convex_idx = 0
        try:
            for seg_part_idx, seg_part in enumerate(segs_part):
                seg_part.seg_convex_idx = seg_convex_idx
                if seg_part.p2 == segs_convex[seg_convex_idx].p2:
                    seg_convex_idx = (seg_convex_idx + 1) % len(segs_convex)
        except IndexError as e:
            logger.warn("Could not associate building part and convex hull segments for part %s (convex=%s): %s", part, convex, e)

        ## Per floor (ddd:building:floor:N) -> Floor profile (facade elements, windows yes/no, etc) (initialize to defaults, use styling)
        ## Floor profiles


    def process_building_segments_analyze(self, part, buildings_ref, ways_ref):
        segments = part.get('ddd:building:segments')
        for s in segments:
            self.process_building_segment_analyze(part, s, buildings_ref, ways_ref)

    def process_building_hull_analyze(self, part, buildings_ref, ways_ref):
        #segments = part.get('ddd:building:convex:segments')
        #for s in segments:
        #    self.process_building_segment_analyze(part, s, buildings_ref, ways_ref)
        #    # (?) Combine original segments information (eg. other buildings contact)
        #    # (?) Leave forward / back-propagation to style rules?
        pass

    def process_building_segment_analyze(self, part, segment, buildings_ref, ways_ref):
        """
        Analyze a segment of a building, resolving:

        - Forward object/way/area (ways only?): distance + link + type  # not so significative if a single ray is cast from center, line cast? (?)
        - Segment type: interior, detail, facade.... # interiors may be missed if using single ray cast from segment center
        - Type of convex hull segment: facade_main, facade_secondary, interior
        """

        # Check if segment touches another segment in this or other building
        contacts = part.get('ddd:building:contacts')

        seg_vert_idx_a = segment.seg_idx
        seg_vert_idx_b = (segment.seg_idx + 1) % (len(part.vertex_list()) - 1)
        contact_a = contacts.get(seg_vert_idx_a, None)
        contact_b = contacts.get(seg_vert_idx_b, None)
        if contact_a and contact_b and contact_a.other == contact_b.other:
            coa = contact_a.other_idx
            cob = contact_b.other_idx
            # Check that segment is contiguous on the "other" geometry (note it can also cycle around vertex list)
            if abs(coa - cob) == 1 or (abs(coa - cob) == len(contact_a.other.vertex_list()) - 2):
                segment.contact = contact_a.other

        #    if
        #if BuildingSegment

        # Get the closest (forward) way to the segment,
        seg_center = (np.array(segment.p2) + np.array(segment.p1)) / 2
        point = ddd.point(seg_center)

        if not ways_ref.is_empty():
            try:
                coords_p, segment_idx, segment_coords_a, segment_coords_b, closest_obj, closest_d = ways_ref.closest_segment(point)
                segment.closest_way = closest_obj

                # Check if there is another building between building segment and way
                ray = ddd.line([seg_center, coords_p]).line_substring(1.0, -1.0)
                segment.building_front = buildings_ref.intersects(ray)

            except DDDException as e:
                logger.warn("Cannot find closest to building segment %s: %s", segment, e)
                pass

        # Facade classification
        # TODO: Do this in styling, study cases
        if segment.contact:
            segment.facade_type = 'contact'
        elif segment.building_front:
            # TODO: Check distance too
            segment.facade_type = 'lateral'  # / vieable/non-viewable
        else:
            # TODO: Check way weights for main/secondary facades
            segment.facade_type = 'main'  # secondary / lateral / back




    def process_buildings_link_items_to_buildings(self, buildings_2d, items_1d):

        logger.info("Linking items to buildings.")
        # TODO: Link to building parts, inspect facade, etc.

        for feature in items_1d.children:
            # Find closest building
            #point = feature.copy(name="Point: %s" % (feature.extra.get('name', None)))
            point = feature
            building, distance = self.closest_building(buildings_2d, point)
            if not building:
                continue

            if distance > 10:
                continue

            feature.extra['ddd:building'] = building

            if feature.extra.get('osm:amenity', None) or feature.extra.get('osm:shop', None):
                # TODO: Do the opposite, create items we are interested in, avoid this exception
                if point.extra.get('osm:amenity', None) in ('waste_disposal', 'waste_basket', 'recycling', 'bicycle_parking', 'parking_space'):
                    continue

                logger.debug("Associating item %s to building %s.", feature, building)
                #logger.debug("Point: %s  Building: %s  Distance: %s", point, building, distance)
                building.extra['ddd:building:items'].append(feature)

    def process_buildings_link_items_ways_to_buildings(self, buildings_all, items):
        for item in items.children:

            '''
            for building in buildings.children:
                if building.contains(item):
                    logger.info("Associating item %s to building %s.", item, building)
                    item.extra['ddd:building:parent'] = building
                    #building.extra['ddd:building:items_ways'].append(item)
            '''

            buildings = buildings_all.select(func=lambda o: o.extra.get('osm:building', None) and not o.extra.get('ddd:building:parent', None) and o.contains(item))

            if len(buildings.children) > 1:
                logger.warn("Item with multiple buildings: %s -> %s", item, buildings.children)
                # Sort by area
                buildings.children.sort(key=lambda b: b.geom.area if b.geom else 0, reverse=True)

            if len(buildings.children) > 0:
                building = buildings.children[0]
                logger.info("Associating item (way) %s to building %s.", item, building)
                item.extra['ddd:building:parent'] = building
                #building.extra['ddd:building:items_ways'].append(item)


    def closest_building(self, buildings_2d, point):
        """
        Returns the closest building to a given point.

        TODO: this method predates selectors and pipelines. This can possibly be done directly or trough with ddd.closest() now. Check usages.
        """
        #closest_building = None
        #closest_distance = math.inf
        closest_building, closest_distance = buildings_2d.closest(point)

        #for building in buildings_2d.children:
        #    distance = point.distance(building)
        #    if distance < closest_distance:
        #        closest_building = building
        #        closest_distance = distance
        return closest_building, closest_distance


