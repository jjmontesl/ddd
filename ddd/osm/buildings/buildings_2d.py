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


# Get instance of logger for this module
logger = logging.getLogger(__name__)



class Buildings2DOSMBuilder():

    def __init__(self, osmbuilder):

        self.osm = osmbuilder

    def preprocess_buildings_features(self, features_2d):
        """
        """

        logger.info("Preprocessing buildings and bulding parts 2D")
        # TODO: create nested buildings them separately, consider them part of the bigger building for subtraction)

        # Assign each building part to a building, or transform it into a building if needed
        #features = sorted(features_2d.children, key=lambda f: f.geom.area)
        features_2d_original = list(features_2d.children)
        for feature in list(features_2d.children):
            if feature.geom.type == 'Point': continue

            if feature.extra.get('osm:building:part', None) is None and feature.extra.get('osm:building', None) is None: continue

            # Find building
            #buildings = features_2d.select(func=lambda o: o.extra.get('osm:building', None) and ddd.polygon(o.geom.exterior.coords).contains(feature))
            buildings = features_2d.select(func=lambda o: o.extra.get('osm:building', None) and o != feature and o.contains(feature) and o in features_2d_original)

            if len(buildings.children) == 0:
                if feature.extra.get('osm:building', None) is None:
                    logger.warn("Building part with no building: %s", feature)
                    building = ddd.shape(feature.geom, name="Building (added): %s" % feature.name)
                    building.extra['osm:building'] = feature.extra.get('osm:building:part', 'yes')
                    building.extra['ddd:building:parts'] = [feature]
                    feature.extra['ddd:building:parent'] = building
                    features_2d.append(building)

            elif len(buildings.children) > 1:
                # Sort by area and get the smaller one
                buildings.children.sort(key=lambda b: b.geom.area, reverse=False)
                logger.warn("Building part with multiple buildings: %s -> %s", feature, buildings.children)

                feature.extra['ddd:building:parent'] = buildings.children[0]
                if 'ddd:building:parts' not in buildings.children[0].extra:
                    buildings.children[0].extra['ddd:building:parts'] = []
                buildings.children[0].extra['ddd:building:parts'].append(feature)

            else:
                logger.debug("Associating building part to building: %s -> %s", feature, buildings.children[0])
                feature.extra['ddd:building:parent'] = buildings.children[0]
                if 'ddd:building:parts' not in buildings.children[0].extra:
                    buildings.children[0].extra['ddd:building:parts'] = []
                buildings.children[0].extra['ddd:building:parts'].append(feature)


    def process_buildings_analyze(self, buildings, ways_ref):
        """
        This is part of the "structured" stage.
        This phase processes building (parts) and generates floors, segments, facades, building contact information, etc...

        Buildings must already have been selected, parent child relationships resolved, and building parts are all independent.
        """

        logger.info("Adding building analysis data (%d buildings)", len(buildings.children))

        self._vertex_cache = defaultdict(list)
        selected_parts = buildings.select(func=lambda o: o.geom, recurse=True)
        for part in selected_parts.children:
            if part.is_empty(): continue
            vertices = part.vertex_list(recurse=False)  # This will fail if part had no geometry (eg. it was empty or children-only)
            for vidx, v in enumerate(vertices[:-1]):  # ignoring last vertex, repeated
                self._vertex_cache[v].append((part, vidx))

        for part in selected_parts.children:
            if part.is_empty(): continue
            if part.geom.type != 'Polygon':
                logger.warn("Skipping building with non Polygon geometry (not implemented): %s", part)
                continue
            self.process_building_contacts(part)
            self.process_building_hull_create(part)
            self.process_building_segments_analyze(part, ways_ref)
            self.process_building_hull_analyze(part, ways_ref)


    def process_building_contacts(self, part):
        """
        Note that elevation is not yet available at this point.
        """

        # Find contacted building parts
        vertices = part.vertex_list(recurse=False)  # This will fail if part had no geometry (eg. it was empty or children-only)
        contacted = []
        for vidx, v in enumerate(vertices[:-1]):
            contacted = contacted + [BuildingContact(pc[0], vidx, pc[1]) for pc in self._vertex_cache[v] if pc[0] != part]
        part.set('ddd:building:contacts', list(set(contacted)))

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


    def process_building_hull_create(self, part):

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


    def process_building_segments_analyze(self, part, ways_ref):
        segments = part.get('ddd:building:segments')
        for s in segments:
            self.process_building_segment_analyze(s, ways_ref)

    def process_building_hull_analyze(self, part, ways_ref):
        segments = part.get('ddd:building:convex:segments')
        for s in segments:
            self.process_building_segment_analyze(s, ways_ref)

    def process_building_segment_analyze(self, segment, ways_ref):
        """
        Analyze a segment of a building, resolving:

        - Forward object/way/area (ways only?): distance + link + type  # not soo significative if a single ray is cast from center, line cast? (?)
        - Segment type: interior, detail, facade.... # interiors may be missed if using single ray cast from segment center
        - Type of convex hull segment: facade_main, facade_secondary, interior
        """

        # Get the closest (forward) way to the segment,
        seg_center = (np.array(segment.p2) + np.array(segment.p1)) / 2
        point = ddd.point(seg_center)

        if not ways_ref.is_empty():
        #try:
            coords_p, segment_idx, segment_coords_a, segment_coords_b, closest_obj, closest_d = ways_ref.closest_segment(point)
            segment.closest_way = closest_obj
        #except DDDException as e:
        #    logger.warn("Cannot find closest way to segment.")


        # Check if there is a building between building and way

        # Check if any segment (or original non-convex segment) is contacting another building (so this would be a building lateral)




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

            feature.extra['osm:building'] = building

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
                buildings.children.sort(key=lambda b: b.geom.area, reverse=True)

            if len(buildings.children) > 0:
                building = buildings.children[0]
                logger.info("Associating item (way) %s to building %s.", item, building)
                item.extra['ddd:building:parent'] = building
                #building.extra['ddd:building:items_ways'].append(item)


    def closest_building(self, buildings_2d, point):
        """
        Returns the closest building to a given point.
        """
        closest_building = None
        closest_distance = math.inf
        for building in buildings_2d.children:
            distance = point.distance(building)
            if distance < closest_distance:
                closest_building = building
                closest_distance = distance
        return closest_building, closest_distance


