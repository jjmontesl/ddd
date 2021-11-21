# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

from collections import defaultdict, namedtuple
import logging
import math
import random

import numpy
from shapely.geometry.linestring import LineString

from ddd.ddd import DDDObject2, DDDObject3
from ddd.ddd import ddd
from ddd.geo import terrain
from ddd.ops import uvmapping
from ddd.core.exception import DDDException
import sys
from shapely import ops
from shapely.ops import linemerge
from shapely.errors import TopologicalError

# Get instance of logger for this module
logger = logging.getLogger(__name__)


class Ways2DOSMBuilder():

    def __init__(self, osmbuilder):
        self.osm = osmbuilder

    def get_way_2d(self, way_1d, ways_2d):
        """
        Gets Way2 give the Way1 object. It uses the reference to `way_1d` in metadata for matching.
        """
        for way_2d in ways_2d.children:
            if 'way_1d' in way_2d.extra and way_2d.extra['way_1d'] == way_1d:
                return way_2d
        logger.warn("Tried to get way 2D for not existing way 1D: %s", way_1d)
        # raise ValueError("Tried to get way 2D for not existing way 1D: %s" % way_1d)
        return DDDObject2()

    def generate_ways_2d(self, ways_1d):

        ways_2d = ddd.group2(name="Ways")

        # Generate layers
        for layer_idx in self.osm.layer_indexes:
            layerways = self.generate_ways_2d_layer(layer_idx, ways_1d)
            if layerways:
                ways_2d.children.extend(layerways.children)

        # These two calls are now done from the pipeline (TODO: remove from here)
        #self.generate_ways_2d_intersections(ways_2d)
        #self.generate_ways_2d_intersection_intersections(ways_2d)

        return ways_2d

    def generate_ways_2d_layer(self, layer_idx, ways_1d):
        '''
        - Sorts ways (more important first),
        - Generates 2D shapes
        '''
        ways_1d = [w for w in ways_1d.children if w.extra['ddd:layer'] == layer_idx]
        logger.info("Generating 2D ways for layer %s (%d ways)", layer_idx, len(ways_1d))

        ways_1d.sort(key=lambda w: w.extra['ddd:way:weight'])

        result = None
        accum = ddd.group2()

        ways_2d = defaultdict(list)
        for w in ways_1d:
            #f = w.extra['osm:feature']
            way_2d = self.generate_way_2d(w)
            if way_2d:

                '''
                try:
                    way_2d = way_2d.clean().subtract(accum).clean()
                    accum = accum.append(way_2d).clean()
                except Exception as e:
                    #way_2d.show()
                    #accum.show()
                    logger.error("Could not subtract existing ways from created way: %s", way_2d)
                    pass
                '''

                weight = way_2d.extra['ddd:way:weight']
                ways_2d[weight].append(way_2d)

        roads = sum(ways_2d.values(), [])
        if roads:
            result = ddd.group(roads, name="Ways (layer: %s)" % layer_idx)  # translate([0, 0, 50])

        # Subtract previous ways, which have lower weight (bigger priority)
        '''
        #ways_2d = defaultdict(list)
        ways_2d = ddd.group2(name="Ways (layer: %s)" % layer_idx)
        for w in ways_1d:
            #f = w.extra['osm:feature']
            way_2d = self.generate_way_2d(w)
            if way_2d:
                #weight = way_2d.extra['ddd:way:weight']
                #ways_2d[weight] = ways_2d[weight].subtract(way_2d) # Subtract (avoid overlapping roads?)
                if (way_2d.overlaps(ways_2d)):
                    way_2d = way_2d.subtract(ways_2d).clean()
                #ways_2d[weight].append(way_2d)
                if (way_2d.geom):
                    ways_2d.append(way_2d)

        #roads = sum(ways_2d.values(), [])
        if ways_2d.children:
            result = ways_2d  #ddd.group(roads, name="Ways (layer: %s)" % layer_idx)  # translate([0, 0, 50])
        '''

        return result

    def generate_way_2d(self, way_1d):

        feature = way_1d.extra['osm:feature']

        path = way_1d

        width = path.extra['ddd:way:width']
        way_2d = path.buffer(distance=width / 2.0, cap_style=ddd.CAP_FLAT, join_style=ddd.JOIN_MITRE)

        # Avoid gaps and eliminate small polygons
        # FIXME: this should be done by continuating path joins/intersections between roads of same type
        # Currently this is done from intersections only (but may be incorrect)
        '''
        if width > 2.0:
            way_2d = way_2d.buffer(distance=1.0, cap_style=2, join_style=2)
            way_2d = way_2d.buffer(distance=-1.0, cap_style=2, join_style=2)
            #way_2d = way_2d.buffer(distance=0.1, cap_style=2, join_style=2)
            # way_2d = way_2d.simplify(0.5)
        '''
        way_2d = way_2d.clean(eps=-0.01)

        # print(feature['properties'].get("name", None))
        # way_2d.extra['osm:feature'] = feature
        # way_2d.extra['path'] = path
        way_2d.extra['way_1d'] = path

        way_2d.name = "Way: %s" % (feature['properties'].get('name', None))
        return way_2d

    def generate_ways_2d_intersections(self, ways_2d):

        logger.info("Generating ways intersections (%d ways).", len(ways_2d.children))

        # Generate intersections (crossroads)
        intersections_2d = []
        for intersection in self.osm.intersections:

            # Discard intersections if they include the same way twice
            for i in range(1, len(intersection)):
                for j in range(0, i):
                    if intersection[i].way == intersection[j].way:
                        logger.warn("Discarding intersection (way contained multiple times)")
                        continue

            # Get intersection "highest ways", which dictate the aspect of the intersection.
            # Currently the road weight with most connections wins, then the lower weight (weight is really priority)
            # Criteria: weight, surface/material, same original street
            # Although ideally, it would be better to use weight/name for name assignation, and surface/material for material assignation. Heights might be involved too.
            #ways = intersection.sort_criteria(['ddd:way:weight', 'ddd:material', 'ddd:name'])
            votes = defaultdict(list)
            votes_surf = defaultdict(list)
            votes_name = defaultdict(list)
            for join in intersection:
                # TODO: 1 to 1 intersections need to be resolved acconting for connectors and surface changes
                if (join.way.get('ddd:way:crosswalk', None)): continue

                votes[join.way.extra['ddd:way:weight']].append(join.way)
                votes_surf[join.way.mat].append(join.way)
                votes_name[join.way.name].append(join.way)
            #max_voted_ways_weight = list(reversed(sorted(votes.items(), key=lambda w: len(w[1]))))[0][0]
            #highest_ways = votes[max_voted_ways_weight]
            #max_voted_ways_count = max([len(v) for k, v in votes.items()])
            #max_weight_max_voted = sorted([vw for vw, vways in votes.items() if len(vways) == max_voted_ways_count])[0]
            if len(votes) > 0:
                votes_weight_list = sorted([(k, v) for k, v in votes.items()], key=lambda o: (len(o[1]), -o[0]) )  # Sort by votes, then weight
                highest_ways = votes_weight_list[-1][1]
                if len(highest_ways) == len(intersection):
                    votes_surf_list = sorted([(k, v) for k, v in votes_surf.items()], key=lambda o: len(o[1]))  # Sort by surfaces
                    highest_ways = votes_surf_list[-1][1]
                    if len(highest_ways) == len(intersection):
                        votes_name_list = sorted([(k, v) for k, v in votes_name.items()], key=lambda o: len(o[1]))  # Sort by surfaces
                        highest_ways = votes_name_list[-1][1]
            else:
                logger.warn("Intersection with no highest ways: %s", intersection)
                highest_ways = [j.way for j in intersection]

            # Generate intersection geometry
            join_ways = ddd.group([self.get_way_2d(j.way, ways_2d) for j in intersection]).flatten().clean()

            #print(join_ways.children)
            #join_geoms = join_ways.geom_recursive()
            #join_points = []
            join_shapes = []

            # First calculation of intersection points (consider all ways)
            intersection_shape = ddd.group2()
            for i in range(len(join_ways.children)):
                for j in range(i + 1, len(join_ways.children)):  #i + 1
                    shape1 = join_ways.children[i]
                    shape2 = join_ways.children[j]
                    part_int = shape1.intersection(shape2)
                    intersection_shape.append(part_int)

            intersection_shape = intersection_shape.union()

            # This converts invalid linearrings (without 3 coordinate tuples or with null area)
            intersection_shape = intersection_shape.clean()

            if intersection_shape.is_empty():
                #logger.debug("Intersection shape with no geometry (skipping): %s (%s)", intersection_shape, intersection)
                continue

            # Point intersections should be from 1 to 1 continuous ways (eg. crosswalks), they are not constructed
            # as they don't have 2d representation.
            if intersection_shape.geom.type in ('Point', 'LineString'):
                logger.debug("Intersection shape of 1D type (skipping): %s (%s)", intersection_shape, intersection)
                continue

            #if (any([('Nicaragua' in ii[0].name) for ii in intersection])):
            #    ddd.group([ii[0].buffer(2.0) for ii in intersection] + [intersection_shape.material(ddd.MAT_HIGHLIGHT)]).show()

            # Calculate way continuation and retract along it from intersection point
            for i in range(len(join_ways.children)):
                for j in range(i + 1, len(join_ways.children)):  #i + 1

                    shape1 = join_ways.children[i]
                    shape2 = join_ways.children[j]
                    if (shape1 == shape2): continue
                    #if shape1.get('way_1d') not in highest_ways or shape2.get('way_1d') not in highest_ways: continue

                    '''
                    shape = shape1.intersection(shape2).clean(eps=0.01)
                    join_shapes.append(shape)
                    #points = shape1.outline().intersection(shape2.outline())
                    #join_points.append(points)
                    '''

                    width = min([shape1.get('ddd:way:width'), shape2.get('ddd:way:width')])

                    # Get continued line
                    way1 = shape1.get('way_1d').remove_z()
                    way2 = shape2.get('way_1d').remove_z()
                    #intersection_shape = shape1.intersection(shape2)
                    #intersection_shape = shape1.outline().intersection(shape2.outline())
                    continued_way_1d = ddd.shape(linemerge([way1.geom, ops.snap(way2.geom, way1.geom, 0.05)]))

                    #ddd.group2([join_ways, intersection_shape.material(ddd.mats.highlight)]).show()

                    # TODO: Call 2d road generator if needed (to account for center, lanes, etc)
                    continued_way_2d = continued_way_1d.buffer(width * 0.5, cap_style=ddd.CAP_FLAT, join_style=ddd.JOIN_BEVEL)

                    # Retract ways
                    for shape in (shape1, shape2):

                        #if shape.get('way_1d') not in highest_ways: continue
                        way_1d = shape.get('way_1d')
                        way_1d = way_1d.orient_from(intersection_shape.centroid())  # Remember that this makes a copy with current API

                        #logger.info("Way 2D: %s", join_way)
                        #logger.info("Way 1D: %s", way_1d)
                        max_dist = 0
                        max_d = 0
                        max_o = None
                        max_p = None
                        min_dist = float("inf")
                        min_d = 0
                        min_o = None
                        min_p = None

                        try:
                            coords_list = list(intersection_shape.coords_iterator())
                        except Exception as e:
                            logger.error("Intersection shape of invalid type %s (%s with %s): %s", intersection_shape, way1, way2, e)
                            continue

                        for intersection_point in coords_list:
                        #for intersection_point in list(g.coords for g in intersection_shape.geom.geoms):
                            closest_seg = way_1d.closest_segment(ddd.point(intersection_point))
                            (coords_p, segment_idx, segment_coords_a, segment_coords_b, closest_object, closest_object_d) = closest_seg
                            #dist = ddd.point(coords_p).distance(continued_way_1d)
                            dist = closest_object_d
                            if dist > max_dist:
                                max_dist = dist
                                max_d = closest_object_d
                                max_o = closest_object
                                max_p = coords_p
                            if dist < min_dist:
                                min_dist = dist
                                min_d = closest_object_d
                                min_o = closest_object
                                min_p = coords_p

                        if (min_o != max_o):
                            logger.error("Invalid intersection cut point distances (%s with %s): %s", way1, way2, intersection_shape)
                            continue

                        way_sub = ddd.shape(ops.substring(max_o.geom, max_d, max_o.geom.length))
                        # TODO: Call 2d road generator if needed (to account for center, lanes, etc)
                        way_sub = way_sub.buffer(shape.get('ddd:way:width') * 0.5, cap_style=ddd.CAP_FLAT)
                        #way_sub = way_sub.buffer(0.05)
                        way_sub = way_sub.clean(eps=-0.05)

                        #ddd.group([continued_way_2d,
                        #           way_sub.material(ddd.mats.highlight)]).show()

                        continued_way_2d = continued_way_2d.subtract(way_sub).clean(eps=-0.05)

                    #continued_way_2d.show()
                    #ddd.group([join_ways, continued_way_2d.material(ddd.mats.highlight)]).show()
                    join_shapes.append(continued_way_2d)

            #intersection_shape = ddd.group2(join_points).union()
            intersection_shape = ddd.group2(join_shapes).union()  #.convex_hull()
            intersection_shape = intersection_shape.clean(eps=0.01)

            #if (any([('Nicaragua' in ii[0].name) for ii in intersection])):
            #    ddd.group([ii[0].buffer(2.0) for ii in intersection] + [intersection_shape.material(ddd.MAT_HIGHLIGHT)]).show()

            #ddd.group2([join_ways, intersection_shape.material(ddd.mats.highlight)]).show()

            if intersection_shape.is_empty():  # geom is None:
                #logger.debug("Ignoring intersection as intersection shape is empty.")
                continue

            try:
                intersection_shape.validate()
            except Exception as e:
                logger.warn("Invalid intersection shape generated: %s", intersection_shape)
                continue

            #intersection_shape.show()

            # Retract intersection: perpendicularize intersection towards paths
            #logger.info("Intersection: %s", join_ways)
            #join_ways.show()
            join_splits = ddd.group2()
            for join_way in join_ways.children:

                way_1d = join_way.extra.get('way_1d', None)

                if way_1d is None:
                    logger.warn("No way 1D found for join_way: %s", join_way)

                # Do not retract way if it is not part of the main ways (highest count) of the intersection
                if way_1d not in highest_ways: continue

                # Project each intersection point to the line
                #logger.info("Way 2D: %s", join_way)
                #logger.info("Way 1D: %s", way_1d)
                max_dist = 0
                max_d = 0
                max_o = None
                for intersection_point in intersection_shape.coords_iterator():
                #for intersection_g in list(intersection_shape.geom.geoms):
                    #    for intersection_point in list(intersection_g.coords):
                    #        #intersection_point = intersection_point[0]
                    #        if not intersection_point: continue
                    closest_seg = way_1d.closest_segment(ddd.point(intersection_point))
                    (coords_p, segment_idx, segment_coords_a, segment_coords_b, closest_object, closest_object_d) = closest_seg
                    dist = ddd.point(coords_p).distance(ddd.point(intersection_shape.geom.centroid.coords))
                    if dist > max_dist:
                        max_dist = dist
                        max_d = closest_object_d
                        max_o = closest_object
                    #logger.info("  max_dist=%s, max_d=%s", max_dist, max_d)

                # Cut line at the specified point.
                if max_o:
                    try:
                        perpendicular = max_o.perpendicular(distance=max_d, length=way_1d.extra['ddd:way:width'], double=True)  # + 0.1
                        join_way_splits = ops.split(join_way.geom, perpendicular.geom)
                        #logger.info("Split: %s", join_way_splits)

                        #ddd.group([join_ways, intersection_shape, perpendicular.buffer(1.0).material(ddd.mats.highlight), join_ways]).show()

                        join_way_split = None

                        # TODO: Use ddd's overlap
                        imargin = 0.05  # 0.05
                        if len(join_way_splits) == 0 or join_way_splits.empty:
                            logger.debug("Could not find split side for intersection extension (join_way_splits is empty): %s", join_way)
                        elif join_way_splits[0].overlaps(intersection_shape.buffer(-imargin).geom):
                            join_way_split = join_way_splits[0]
                        elif len(join_way_splits) > 1 and join_way_splits[1].overlaps(intersection_shape.buffer(-imargin).geom):
                            join_way_split = join_way_splits[1]
                        elif len(join_way_splits) > 2 and join_way_splits[2].overlaps(intersection_shape.buffer(-imargin).geom):
                            join_way_split = join_way_splits[1]
                        else:
                            logger.debug("Could not find split side for intersection extension: %s", join_way)
                            #raise AssertionError()

                        if join_way_split:
                            join_splits.append(ddd.shape(join_way_split))
                    except DDDException as e:
                        logger.error("Could not calculate intersection cut for: %s (%s)", intersection, e)

            #intersection_shape = intersection_shape.union(join_splits.union()).clean(eps=0.005)
            intersection_shape = intersection_shape.union(join_splits.union()).individualize()
            intersection_shape = intersection_shape.clean(eps=0.005)

            #ddd.group2([join_ways, intersection_shape.material(ddd.mats.highlight)]).show()

            # Resolve intersection
            if intersection_shape and intersection_shape.geom and intersection_shape.geom.type in ('Polygon', 'MultiPolygon') and not intersection_shape.geom.is_empty:

                # Prepare way_1d (joining ways if needed)
                highest_way = highest_ways[0].copy()
                if len(highest_ways) == 2:
                    try:
                        #print([list(g.geom.coords) for g in highest_ways])
                        #ddd.group(highest_ways).buffer(0.1).show()

                        highest_way.geom = linemerge([g.geom for g in highest_ways])
                        highest_way.children = []
                        #print(list(highest_way.geom.coords))

                        logger.debug("Merged intersection lines %s: %s", highest_ways, highest_way)
                    except ValueError as e:
                        logger.error("Cannot merge intersection lines %s: %s", highest_ways, e)
                        #ddd.group(highest_ways).buffer(0.1).show()
                        #raise DDDException("Cannot merge intersection lines: %s" % e, ddd_obj=ddd.group(highest_ways).buffer(1).triangulate())

                intersection_2d = highest_way.copy(name="Intersection (%s)" % highest_way.name)
                intersection_2d.extra['way_1d'] = highest_way
                # intersection_2d.extra['way_1d'].geom = ddd.group2(highest_ways).union().geom
                #intersection_2d.extra['way_1d'].children = highest_ways
                #intersection_2d.extra['way_1d_highest'] = highest_ways
                # Combine highest paths and their elevations

                # Remove connections (or at least we should join them all), store the highest way (currently for troubleshooting)
                intersection_2d.extra['ddd:intersection:highest'] = highest_ways
                intersection_2d.extra['ddd:connections'] = []

                if len(intersection) > 3 or len(intersection) == len(highest_ways):  # 2
                    intersection_2d.extra['ddd:way:lamps'] = False
                    intersection_2d.extra['ddd:way:traffic_signals'] = False
                    intersection_2d.extra['ddd:way:traffic_signs'] = False
                    intersection_2d.extra['ddd:way:roadlines'] = False

                intersection_2d.geom = intersection_shape.geom  # ddd.shape(intersection_shape, name="Intersection")
                intersection_2d.extra['intersection'] = intersection
                for join in intersection:
                    if join.way.extra['intersection_start'] == intersection:
                        join.way.extra['intersection_start_2d'] = intersection_2d
                    if join.way.extra['intersection_end'] == intersection:
                        join.way.extra['intersection_end_2d'] = intersection_2d

                intersections_2d.append(intersection_2d)

        intersections_2d = ddd.group(intersections_2d, empty="2", name="Intersections")
        #self.osm.intersections_2d = intersections_2d

        # Add intersections to respective layers
        for int_2d in intersections_2d.children:
            # print(int_2d.extra)
            int_2d = int_2d.clean()
            if int_2d.geom: ways_2d.append(int_2d)

        # Subtract intersections from ways
        ways = []
        for way in ways_2d.children:

            if 'intersection' in way.extra:
                ways.append(way)
                continue
            # logger.debug("Way: %s  Way 1D: %s  Intersections: %s", way, way.extra['way_1d'], way.extra['way_1d'].extra)
            if 'intersection_start_2d' in way.extra['way_1d'].extra:
                way = way.subtract(way.extra['way_1d'].extra['intersection_start_2d'])
            if 'intersection_end_2d' in way.extra['way_1d'].extra:
                way = way.subtract(way.extra['way_1d'].extra['intersection_end_2d'])
            '''
            connected = self.follow_way(way.extra['way_1d'], 1)
            connected.remove(way.extra['way_1d'])
            connected_2d = ddd.group([self.get_way_2d(c) for c in connected])
            wayminus = way.subtract(connected_2d).buffer(0.001)
            '''

            # WARN: This buffer(0.001) is critical for the resolution of roads and intersections, but why? (20210502)
            way = way.buffer(0.001)
            #way = way.clean(eps=0.01)

            # Checks
            if True or (way.geom and way.geom.is_valid):

                if way:
                    try:
                        way.extrude(1.0)  # Note: just testing, not actually changing the object
                        ways.append(way)
                    except Exception as e:
                        logger.warn("Could not generate way due to exception in extrude check: %s (trying cleanup)", way )
                        way = way.clean(eps=0.01)
                        try:
                            way.extrude(1.0)  # Note: just testing, not actually changing the object
                            ways.append(way)
                        except Exception as e:
                            logger.error("Could not generate way due to exception in extrude check: %s", way)

        ways_2d.replace(ddd.group2(ways, name="Ways"))


    def generate_ways_2d_intersection_intersections(self, ways_2d):
        """
        """

        intersections = ways_2d.select('["intersection"]', recurse=False)
        logger.info("Resolving intersection intersections (%d objects)", len(intersections.children))
        #intersections.show()

        intersections.children.sort(key=lambda c: c.get('ddd:way:weight'))
        for idx, way in enumerate(intersections.children):

            if way.geom is None: continue

            # Find ovelap with other intersections
            for other in intersections.children[idx+1:]:

                if other == way or other.geom is None: continue
                #if other.get("ddd:layer") != way.get("ddd:layer"): continue

                if way.intersects(other):

                    try:
                        isec = way.intersection(other).union()
                    except TopologicalError as e:
                        logger.error("Could not resolve intersection intersection %s - %s: %s", way, other)
                        continue

                    if isec.geom and isec.geom.area > 0:  #and not way.touches(other):
                        #logger.debug("Intersection intersection: %s > %s", way, other)

                        #ddd.group2([main, minor.material(ddd.mats.highlight), way.intersection(other).material(ddd.mats.red)]).show()
                        #ddd.group2([way.intersection(other).material(ddd.mats.red)]).show()

                        new_other = other.subtract(way).clean().union().clean()
                        #if new_other.geom and new_other.geom.area < 0.01: new_other.geom = None
                        if new_other.geom and new_other.is_empty(): new_other.geom.type = None

                        other.replace(new_other)


    def generate_roadlines(self, pipeline, way_2d):

        # Get the 1D line reference
        path = way_2d.extra['way_1d']

        # print(path.geom.type)

        if path.geom.type != "LineString" or path.is_empty():
            logger.warn("Cannot generate roadlines for %s: way_1d %s is not a LineString.", way_2d, path)
            return

        path = path.copy()

        # Subdivide lines
        if int(pipeline.data.get('ddd:way:roadlines:subdivide', 0)) > 0:
            ddd.geomops.subdivide_to_size(path, int(pipeline.data.get('ddd:way:roadlines:subdivide')))

        length = path.geom.length

        if way_2d.is_empty():
            return

        # Generate lines
        if way_2d.extra.get('ddd:way:roadlines', False):

            lanes = way_2d.extra['ddd:way:lanes']
            numlines = lanes - 1 + 2
            for lineind in range(numlines):

                width = path.extra['ddd:width']
                lane_width = path.extra['ddd:way:lane_width']  # lanes_width / lanes
                lane_width_left = path.extra['ddd:way:lane_width_left']
                lane_width_right = path.extra['ddd:way:lane_width_right']

                oneway = path.extra.get('osm:oneway', False)
                if (oneway in ("no", "false")): oneway = False

                line_continuous = False
                if lineind in [0, numlines - 1]: line_continuous = True
                if lanes >= 2 and lineind == int(numlines / 2) and not oneway and path.extra.get('osm:highway', None) != 'roundabout':
                    line_continuous = True
                line_x_offset = 0.076171875 if line_continuous else 0.5

                line_0_distance = -(width / 2) + lane_width_right
                line_distance = line_0_distance + lane_width * lineind

                # Create line
                pathline = path.copy()
                if abs(line_distance) > 0.01:
                    try:
                        pathline.geom = pathline.geom.parallel_offset(line_distance, "left", resolution=2)
                    except Exception as e:
                        logger.warn("Cannot create roadline for %s: %s", path, e)
                        # This return is done since it avoids a subsequent TopologyError if using "continue"
                        return
                line = pathline.buffer(0.15).material(ddd.mats.roadline)
                line.extra['way_1d'] = pathline


                # FIXME: Move cropping to generic site, use intermediate osm.something for storage
                # Also, cropping shall interpolate UVs (and propagated heights?)
                line = line.intersection(self.osm.area_crop2)
                line = line.intersection(way_2d)
                line = line.individualize()

                if line.is_empty():
                    continue

                #ddd.group([way_2d, line]).show()

                if line.geom and not line.geom.is_empty and line.geom.area > 0:
                    try:
                        uvmapping.map_2d_path(line, pathline, line_x_offset / 0.05)
                    except DDDException as e:
                        logger.error("Error mapping UV coordinates for road line for %s: %s", way_2d, e)
                        continue
                    pipeline.root.find("/Roadlines2").append(line)
                else:
                    continue

                try:
                    line_3d = line.triangulate()
                except ValueError as e:  # TODO: This shall be an appropriate DDDException
                    logger.warn("Could not generate roadline for way %s: %s", way_2d, e)
                    continue

                line_3d = line_3d.translate([0, 0, 0.01])
                vertex_func = self.osm.ways1.get_height_apply_func(path)
                line_3d = line_3d.vertex_func(vertex_func)
                line_3d = terrain.terrain_geotiff_elevation_apply(line_3d, self.osm.ddd_proj)
                line_3d.extra['ddd:collider'] = False
                line_3d.extra['ddd:shadows'] = False
                line_3d.extra['ddd:occluder'] = False
                line_3d.extra['ddd:area:container'] = way_2d
                # print(line)
                # print(line.geom)
                uvmapping.map_3d_from_2d(line_3d, line)
                # uvmapping.map_2d_path(line_3d, path)

                pipeline.data["Roadlines3"].append(line_3d)

    def generate_crosswalk(self, pipeline, way_2d):
        path = way_2d.extra['way_1d']
        length = path.geom.length

        if path.geom.type != "LineString":
            logger.warn("Cannot generate crosswalk for %s: way_1d %s is not a LineString.", way_2d, path)
            return

        width = way_2d.get('ddd:way:width')
        bar_interval = 1.5
        bar_width = 0.6
        numlines = int(width / bar_interval)

        for lineind in range(numlines + 1):

            line_0_distance = -( (bar_interval * numlines) / 2)
            line_distance = line_0_distance + bar_interval * lineind

            # Create line
            pathline = path.copy()
            line_margin = 0.5
            pathline = pathline.intersection(way_2d.buffer(-line_margin))  # It's better to reduce the line, this seems to cause multilinestrings
            if (pathline.geom.type != "LineString"):
                logger.warn("Cannot generate crosswalk for %s: way_1d %s is not a LineString after reducing.", way_2d, path)
                return

            if abs(line_distance) > 0.01:
                pathline.geom = pathline.geom.parallel_offset(line_distance, "left", resolution=2)
            line = pathline.buffer(bar_width / 2, cap_style=ddd.CAP_FLAT).material(ddd.mats.roadline)
            line.extra['way_1d'] = pathline

            # FIXME: Move cropping to generic site, use intermediate osm.something for storage
            # Also, cropping shall interpolate UVs (and propagated heights?)
            line = line.intersection(self.osm.area_crop2)
            line = line.intersection(way_2d)
            line = line.individualize()

            line_continuous = True
            line_x_offset = 0.076171875 if line_continuous else 0.5
            if line.geom and not line.geom.is_empty and line.geom.area > 0:
                uvmapping.map_2d_path(line, pathline, line_x_offset / 0.05, line_d_offset=random.uniform(0, 1))
                pipeline.root.find("/Roadlines2").append(line)
            else:
                continue

            # except Exception as e:
            #    logger.error("Could not UV map Way 2D from path: %s %s %s: %s", line, line.geom, pathline.geom, e)
            #    continue
            line_3d = line.triangulate().translate([0, 0, 0.05])  # Temporary hack until fitting lines properly
            vertex_func = self.osm.ways1.get_height_apply_func(path)
            line_3d = line_3d.vertex_func(vertex_func)
            line_3d = terrain.terrain_geotiff_elevation_apply(line_3d, self.osm.ddd_proj)
            line_3d.extra['ddd:collider'] = False
            line_3d.extra['ddd:shadows'] = False
            line_3d.extra['ddd:occluder'] = False
            # print(line)
            # print(line.geom)
            uvmapping.map_3d_from_2d(line_3d, line)
            # uvmapping.map_2d_path(line_3d, path)

            pipeline.data["Roadlines3"].append(line_3d)


    def generate_lamps(self, pipeline, way_2d):

        path = way_2d.extra['way_1d']
        length = path.geom.length

        if path.geom.type != "LineString":
            logger.warn("Cannot generate lamps for %s: way_1d %s is not a LineString.", way_2d, path)
            return

        # Check if to generate lamps
        if path.extra.get('ddd:way:lamps', False) and (path.extra['ddd:layer'] in (0, "0") or path.extra['osm:layer'] in (0, "0")):

            # Generate lamp posts
            interval = 25.0
            numlamps = int(length / interval)
            idx = 0
            idx_offset = random.choice([0, 1])

            # Ignore if street is short
            if numlamps > 0:

                logger.debug("Props for way (length=%s, num=%d, way=%s)", length, numlamps, way_2d)
                for d in numpy.linspace(0.0, length, numlamps, endpoint=False):
                    if d == 0.0: continue

                    # Calculate left and right perpendicular intersections with sidewalk, park, land...
                    # point = path.geom.interpolate(d)
                    p, segment_idx, segment_coords_a, segment_coords_b = path.interpolate_segment(d)
                    # logger.error("Could not generate props for way %s: %s", way_2d, e)
                    # print(d, p, segment_idx, segment_coords_a, segment_coords_b)

                    # Only for the correct part of the line (since path is not adjusted by intersections)
                    if not way_2d.intersects(ddd.point(p)): continue

                    # segment = ddd.line([segment_coords_a, segment_coords_b])
                    dir_vec = (segment_coords_b[0] - segment_coords_a[0], segment_coords_b[1] - segment_coords_a[1])
                    dir_vec_length = math.sqrt(dir_vec[0] ** 2 + dir_vec[1] ** 2)
                    dir_vec = (dir_vec[0] / dir_vec_length, dir_vec[1] / dir_vec_length)
                    perpendicular_vec = (-dir_vec[1], dir_vec[0])
                    lightlamp_dist = path.extra['ddd:way:width'] * 0.5 + 0.5
                    left = (p[0] + perpendicular_vec[0] * lightlamp_dist, p[1] + perpendicular_vec[1] * lightlamp_dist)
                    right = (p[0] - perpendicular_vec[0] * lightlamp_dist, p[1] - perpendicular_vec[1] * lightlamp_dist)

                    alternate_lampposts = True
                    if alternate_lampposts:
                        points = [left] if (idx + idx_offset) % 2 == 0 else [right]
                    else:
                        points = left, right

                    for point in points:
                        idx = idx + 1
                        item = ddd.point(point, name="Lamppost: %s" % way_2d.name)

                        # area = self.osm.areas_2d.intersect(item)
                        # Check type of area point is on

                        item.extra['way_2d'] = way_2d
                        item.extra['osm:highway'] = 'street_lamp'
                        item.extra['ddd:aug:status'] = 'added'
                        pipeline.root.find("/ItemsNodes").append(item)


    def generate_traffic_signals(self, pipeline, way_2d):

        path = way_2d.extra['way_1d']
        length = path.geom.length

        # Generate traffic lights
        if True and path.geom.length > 45.0 and path.extra['ddd:way:traffic_signals'] and path.extra['ddd:layer'] in (0, "0"):

            for end in (1, -1):

                if end == -1 and path.extra.get('osm:oneway', None): continue

                if end == 1:
                    p, segment_idx, segment_coords_a, segment_coords_b = path.interpolate_segment(path.geom.length - 10.0)
                else:
                    p, segment_idx, segment_coords_a, segment_coords_b = path.interpolate_segment(10.0)

                # Only for the correct part of the line (since path is not adjusted by intersections)
                if not way_2d.intersects(ddd.point(p)): continue

                dir_vec = (segment_coords_b[0] - segment_coords_a[0], segment_coords_b[1] - segment_coords_a[1])
                dir_vec_length = math.sqrt(dir_vec[0] ** 2 + dir_vec[1] ** 2)
                dir_vec = (dir_vec[0] / dir_vec_length, dir_vec[1] / dir_vec_length)
                perpendicular_vec = (-dir_vec[1], dir_vec[0])
                lightlamp_dist = path.extra['ddd:way:width'] * 0.5 + 0.5
                left = (p[0] + perpendicular_vec[0] * lightlamp_dist, p[1] + perpendicular_vec[1] * lightlamp_dist)
                right = (p[0] - perpendicular_vec[0] * lightlamp_dist, p[1] - perpendicular_vec[1] * lightlamp_dist)

                if end == 1:
                    item = ddd.point(right, name="Traffic lights: %s" % way_2d.name)
                    angle = math.atan2(dir_vec[1], dir_vec[0])
                else:
                    item = ddd.point(left, name="Traffic lights: %s" % way_2d.name)
                    angle = math.atan2(dir_vec[1], dir_vec[0]) + math.pi

                # area = self.osm.areas_2d.intersect(item)
                # Check type of area point is on
                item.extra['way_2d'] = way_2d
                item.extra['ddd:aug:status'] = 'added'
                item.extra['osm:highway'] = 'traffic_signals'
                item.extra['ddd:angle'] = angle #+ math.pi/2
                pipeline.root.find("/ItemsNodes").append(item)


    def generate_traffic_signs(self, pipeline, way_2d):

        path = way_2d.extra['way_1d']
        length = path.geom.length

        if path.geom.type != "LineString":
            logger.warn("Cannot generate traffic signs for %s: way_1d %s is not a LineString.", way_2d, path)
            return

        # Generate traffic signs
        if path.extra.get('ddd:way:traffic_signs', False) and path.geom.length > 20.0 and path.extra['ddd:layer'] == "0":

            for end in (1, -1):

                if end == -1 and path.extra.get('osm:oneway', None): continue

                if end == 1:
                    # End right
                    p, segment_idx, segment_coords_a, segment_coords_b = path.interpolate_segment(path.geom.length - 11.5 - random.uniform(0.0, 8.0))
                else:
                    p, segment_idx, segment_coords_a, segment_coords_b = path.interpolate_segment(11.5 + random.uniform(0.0, 8.0))

                # Only for the correct part of the line (since path is not adjusted by intersections)
                if way_2d.intersects(ddd.point(p)):

                    dir_vec = (segment_coords_b[0] - segment_coords_a[0], segment_coords_b[1] - segment_coords_a[1])
                    dir_vec_length = math.sqrt(dir_vec[0] ** 2 + dir_vec[1] ** 2)
                    dir_vec = (dir_vec[0] / dir_vec_length, dir_vec[1] / dir_vec_length)
                    perpendicular_vec = (-dir_vec[1], dir_vec[0])
                    item_dist = path.extra['ddd:way:width'] * 0.5 + 0.5
                    left = (p[0] + perpendicular_vec[0] * item_dist, p[1] + perpendicular_vec[1] * item_dist)
                    right = (p[0] - perpendicular_vec[0] * item_dist, p[1] - perpendicular_vec[1] * item_dist)

                    if end == 1:
                        item = ddd.point(right, name="Traffic sign: %s" % way_2d.name)
                        angle = math.atan2(dir_vec[1], dir_vec[0])
                    else:
                        item = ddd.point(left, name="Traffic sign: %s" % way_2d.name)
                        angle = math.atan2(dir_vec[1], dir_vec[0]) + math.pi

                    # area = self.osm.areas_2d.intersect(item)
                    # Check type of area point is on
                    item.extra['way_2d'] = way_2d
                    item.extra['ddd:aug:status'] = 'added'
                    item.extra['ddd:angle'] = angle - math.pi / 2
                    item.extra['osm:traffic_sign'] = random.choice(['es:r1', 'es:r2', 'es:p1', 'es:r101', 'es:r303', 'es:r305',
                                                                    'es:r308', 'es:r400c', 'es:r500', 'es:s13'])  # 'es:r301_50',
                    pipeline.root.find("/ItemsNodes").append(item)


    def generate_stairs_simple(self, pipeline, obj):
        """
        Takes a 2D area and splits in steps according to original way_1d and metadata.

        This takes the remaning area and keeps splitting it along path perpendiculars.
        """

        path = obj.extra['way_1d']
        length = path.geom.length

        # Interpolate path line and split area with perpendiculars
        #step_depth = obj.get('ddd:steps:depth', 0.375)
        step_depth = obj.get('ddd:steps:depth', 0.75)

        # Generate lamp posts
        interval = step_depth
        numsteps = int(length / interval)


        # Ignore if street is short
        if numsteps > 1:
            remaining = obj.copy()
            stairs = ddd.group2(name="Stairs: %s" % obj.name)

            logger.debug("Steps for way (length=%s, num=%d, way=%s)", length, numsteps, obj)
            idx = 0
            for d in numpy.linspace(0.0, length, numsteps, endpoint=False):
                if d == 0.0: continue
                idx += 1

                cut_dist = path.extra['ddd:way:width'] * 0.5 + 0.5
                perp = path.perpendicular(d, length=cut_dist, double=True)

                if (remaining.is_empty()):
                    break

                splits = None

                if remaining.geom.type != 'Point' and remaining.geom.type not in ('MultiPoint', 'GeometryCollection'):
                    splits = ops.split(remaining.geom, perp.geom)
                    splits = [s for s in splits]
                    splits.sort(key=lambda s: s.area)

                if splits and len(splits) > 1:

                    step = obj.copy(name="Step %s: %s" % (idx, obj.name))
                    step.children = []
                    step.geom = splits[0]
                    step.extra['ddd:elevation:level'] = 0.90
                    step.extra['ddd:area:elevation'] = 'max'
                    step.extra['ddd:area:type'] = 'default'
                    #step.extra['ddd:extra_height'] = 0.0
                    stairs.append(step)

                    remaining.geom = splits[1]
                    for s in splits[2:]:
                        remaining.geom = remaining.geom.union(s)

            remaining.name = "Step 0: %s" % (obj.name)
            remaining.extra['ddd:elevation:level'] = 0.90
            remaining.extra['ddd:area:elevation'] = 'max'
            remaining.extra['ddd:area:type'] = 'default'
            stairs.append(remaining)
            stairs = stairs.individualize().flatten()
            stairs.extra = obj.extra

            obj.replace(stairs)
            #obj.show()

        return obj



