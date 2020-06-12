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

# Get instance of logger for this module
logger = logging.getLogger(__name__)


class Ways2DOSMBuilder():

    def __init__(self, osmbuilder):
        self.osm = osmbuilder


    def get_way_2d(self, way_1d, ways_2d):
        for way_2d in ways_2d.children:
            if 'way_1d' in way_2d.extra and way_2d.extra['way_1d'] == way_1d:
                return way_2d
        logger.warn("Tried to get way 2D for not existing way 1D: %s", way_1d)
        # raise ValueError("Tried to get way 2D for not existing way 1D: %s" % way_1d)
        return DDDObject2()
    '''
    def get_way_2d(self, way_1d, ways_2d):
        for l in ways_2d.values():
            for way_2d in l.children:
                if 'way_1d' in way_2d.extra and way_2d.extra['way_1d'] == way_1d:
                    return way_2d
        logger.warn("Tried to get way 2D for not existing way 1D: %s", way_1d)
        # raise ValueError("Tried to get way 2D for not existing way 1D: %s" % way_1d)
        return DDDObject2()
    '''

    def generate_ways_2d(self, ways_1d):

        ways_2d = ddd.group2(name="Ways")

        # Generate layers
        for layer_idx in self.osm.layer_indexes:
            layerways = self.generate_ways_2d_layer(layer_idx, ways_1d)
            if layerways:
                ways_2d.children.extend(layerways.children)

        self.generate_ways_2d_intersections(ways_2d)

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

        ways_2d = defaultdict(list)
        for w in ways_1d:
            #f = w.extra['osm:feature']
            way_2d = self.generate_way_2d(w)
            if way_2d:
                weight = way_2d.extra['ddd:way:weight']
                ways_2d[weight].append(way_2d)

        roads = sum(ways_2d.values(), [])
        if roads:
            result = ddd.group(roads, name="Ways (layer: %s)" % layer_idx)  # translate([0, 0, 50])

        return result

    def generate_way_2d(self, way_1d):

        feature = way_1d.extra['osm:feature']

        # highway = feature['properties'].get('osm:highway', None)
        # if highway is None: return

        path = way_1d

        width = path.extra['ddd:way:width']
        way_2d = path.buffer(distance=width / 2.0, cap_style=2, join_style=2)

        # Avoid gaps and eliminate small polygons
        # path = path.buffer(distance=0.05)
        # FIXME: this should be done by continuating path joins/intersections between roads of same type
        if width > 2.0:
            way_2d = way_2d.buffer(distance=1.0, cap_style=2, join_style=2)
            way_2d = way_2d.buffer(distance=-1.0, cap_style=2, join_style=2)
            way_2d = way_2d.buffer(distance=0.1, cap_style=2, join_style=2)
            # way_2d = way_2d.simplify(0.5)

        # Remove buildings
        if way_2d.extra.get('ddd:subtract_buildings', False):
            #buildings_2d_union = self.osm.buildings_2d.union()
            #way_2d = way_2d.subtract(self.osm.buildings_2d_union)
            way_2d = way_2d.clean(eps=0.05)
            try:
                way_2d = way_2d.subtract(self.osm.buildings_2d)
            except Exception as e:
                logger.error("Could not subtract buildings %s from way %s: %s", self.osm.buildings_2d, way_2d, e)
                return None

        # print(feature['properties'].get("name", None))
        # way_2d.extra['osm:feature'] = feature
        # way_2d.extra['path'] = path
        way_2d.extra['way_1d'] = path

        way_2d.name = "Way: %s" % (feature['properties'].get('name', None))
        return way_2d

    def generate_ways_2d_intersections(self, ways_2d):

        # Generate intersections (crossroads)
        intersections_2d = []
        for intersection in self.osm.intersections:

            # Discard intersections if they include the same way twice
            for i in range(1, len(intersection)):
                for j in range(0, i):
                    if intersection[i].way == intersection[j].way:
                        logger.warn("Discarding intersection (way contained multiple times)")
                        continue

            # Get intersection way type by vote
            votes = defaultdict(list)
            for join in intersection:
                votes[join.way.extra['ddd:way:weight']].append(join.way)
            max_voted_ways_weight = list(reversed(sorted(votes.items(), key=lambda w: len(w[1]))))[0][0]
            highest_ways = votes[max_voted_ways_weight]

            # Generate intersection geometry

            join_ways = ddd.group([self.get_way_2d(j.way, ways_2d) for j in intersection])
            # print(join_ways.children)
            #join_geoms = join_ways.geom_recursive()
            #join_points = []
            join_shapes = []
            # Calculate intersection points as lines
            for i in range(len(join_ways.children)):
                for j in range(i + 1, len(join_ways.children)):
                    shape1 = join_ways.children[i]
                    shape2 = join_ways.children[j]
                    shape = shape1.intersection(shape2).clean(eps=0.01)
                    join_shapes.append(shape)
                    #points = shape1.outline().intersection(shape2.outline())
                    #join_points.append(points)
            #intersection_shape = ddd.group2(join_points).union()
            intersection_shape = ddd.group2(join_shapes).union().convex_hull()

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
                for intersection_point in list(intersection_shape.geom.exterior.coords):
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
                    perpendicular = max_o.perpendicular(distance=max_d, length=way_1d.extra['ddd:way:width'], double=True)  # + 0.1
                    join_way_splits = ops.split(join_way.geom, perpendicular.geom)
                    #logger.info("Split: %s", join_way_splits)

                    #ddd.group([join_ways, intersection_shape, perpendicular.buffer(1.0).material(ddd.mats.highlight), join_ways]).show()

                    join_way_split = None
                    '''
                    if join_way_splits:
                        if join_way_splits[0].intersects(intersection_shape.geom):
                            join_way_split = join_way_splits[0]
                        elif len(join_way_splits) > 1 and join_way_splits[1].intersects(intersection_shape.geom):
                            join_way_split = join_way_splits[1]
                        elif len(join_way_splits) > 2 and join_way_splits[2].intersects(intersection_shape.geom):
                            join_way_split = join_way_splits[1]
                        else:
                            logger.error("Could not find split side for intersection extension: %s", join_way)
                        #else:
                        #    logger.error("Could not find split side for intersection extension (no splits): %s", join_way)
                        #    #raise AssertionError()
                    '''
                    if join_way_splits[0].overlaps(intersection_shape.buffer(-0.05).geom):
                        join_way_split = join_way_splits[0]
                    elif len(join_way_splits) > 1 and join_way_splits[1].overlaps(intersection_shape.buffer(-0.05).geom):
                        join_way_split = join_way_splits[1]
                    elif len(join_way_splits) > 2 and join_way_splits[2].overlaps(intersection_shape.buffer(-0.05).geom):
                        join_way_split = join_way_splits[1]
                    else:
                        logger.debug("Could not find split side for intersection extension: %s", join_way)
                        #raise AssertionError()

                    if join_way_split:
                        join_splits.append(ddd.shape(join_way_split))

            intersection_shape = intersection_shape.union(join_splits.union()).clean(eps=0.005)

            #ddd.group([intersection_shape.material(ddd.mats.highlight), join_ways]).dump()
            #ddd.group([intersection_shape.material(ddd.mats.highlight), join_ways]).show()

            # Resolve intersection
            # print(intersection_shape)
            if intersection_shape and intersection_shape.geom and intersection_shape.geom.type in ('Polygon', 'MultiPolygon') and not intersection_shape.geom.is_empty:

                '''
                # Get intersection way type by vote
                votes = defaultdict(list)
                for join in intersection:
                    votes[join.way.extra['ddd:way:weight']].append(join.way)
                max_voted_ways_weight = list(reversed(sorted(votes.items(), key=lambda w: len(w[1]))))[0][0]
                highest_ways = votes[max_voted_ways_weight]
                '''

                # Createintersection from highest way value from joins
                '''
                highest_way = None
                for join in intersection:
                    if highest_way is None or join.way.extra['ddd:way:weight'] < highest_way.extra['ddd:way:weight'] :
                        highest_way = join.way
                '''

                # Prepare way_1d (joining ways if needed)
                highest_way = highest_ways[0].copy()
                if len(highest_ways) == 2:
                    #highest_way.geom = ddd.group(highest_ways).union().geom  # Leaves multilinestrings
                    try:
                        highest_way.geom = linemerge(ddd.group(highest_ways).union().remove_z().geom)  # Merges multilinestrings into linestrings if possible
                    except ValueError as e:
                        logger.error("Cannot merge intersection lines: %s", e)
                        #raise DDDException("Cannot merge intersection lines: %s" % e, ddd_obj=ddd.group(highest_ways).buffer(1).triangulate())


                intersection_2d = highest_way.copy(name="Intersection (%s)" % highest_way.name)
                intersection_2d.extra['way_1d'] = highest_way
                # intersection_2d.extra['way_1d'].geom = ddd.group2(highest_ways).union().geom
                #intersection_2d.extra['way_1d'].children = highest_ways
                #intersection_2d.extra['way_1d_highest'] = highest_ways
                # Combine highest paths and their elevations

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
            ways_2d.append(int_2d)

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
            way = way.buffer(0.001)
            if True or (way.geom and way.geom.is_valid):

                # print(way)
                # print(way.geom.type)
                '''
                if way.geom.type == "Polygon":
                    #way.geom = way.geom.buffer(0.0)
                    if way.geom.exterior == None:
                        way = None
                    else:
                        #print(list(way.geom.exterior.coords))
                        pass
                    if way.geom.interiors:
                        #print("INTERIORS:")
                        #print([list(i.coords) for i in way.geom.interiors])
                        #print([i.is_valid for i in way.geom.interiors])
                        pass

                #elif way.geom.type == "MultiPolygon":
                #    print([list(p.exterior.coords) for p in way.geom])
                #else:
                #    print(list(way.geom.coords))
                '''

                if way:
                    try:
                        way.extrude(1.0)
                        ways.append(way)
                    except Exception as e:
                        logger.warn("Could not generate way due to exception in extrude check: %s (trying cleanup)", way )
                        way = way.clean(eps=0.01)
                        try:
                            way.extrude(1.0)
                            ways.append(way)
                        except Exception as e:
                            logger.error("Could not generate way due to exception in extrude check: %s", way)

        ways_2d.replace(ddd.group(ways, empty="2", name="Ways"))

        # logger.info("Saving intersections 2D.")
        # ddd.group([ways_2d["0"].extrude(1.0), self.osm.intersections_2d.material(ddd.mats.highlight).extrude(1.5)]).save("/tmp/ddd-intersections.glb")

        # Subtract connected ways
        # TODO: This shall be possibly done when creating ways not after
        # union_lm1 = ways_2d["-1"].union()
        # union_l0 = ways_2d["0"].union()
        # union_l1 = ways_2d["1"].union()
        '''
        for layer_idx in ["-1a", "0a", "1a"]:
            ways = []
            for way in ways_2d[layer_idx].children:
                connected = self.follow_way(way.extra['way_1d'], 1)
                connected.remove(way.extra['way_1d'])
                connected_2d = ddd.group([self.get_way_2d(c) for c in connected])
                wayminus = way.subtract(connected_2d).buffer(0.001)
                ways.append(wayminus)
            ways_2d[layer_idx] = ddd.group(ways, empty="2")
        '''

        # ways_2d["-1a"] = ways_2d["-1a"].material(ddd.mat_highlight)
        # ways_2d["-1a"].children[0].dump()
        # print(ways_2d["-1a"].children[0].extra)
        # print(list(ways_2d["-1a"].children[0].extra['way_1d'].geom.coords))
        # sys.exit(0)

        # ways_2d["0a"] = ways_2d["0a"].subtract(union_l0).subtract(union_l1)
        # ways_2d["1a"] = ways_2d["1a"].subtract(union_l1)


    def generate_props_2d(self, ways_2d, pipeline):
        """
        Road props (traffic lights, lampposts...).
        Need roads, areas, coastline, etc... and buildings
        """

        logger.info("Generating props linked to ways (%d ways)", len(ways_2d.children))

        for way_2d in ways_2d.children:
            try:
                self.generate_props_2d_way(way_2d, pipeline)
            except Exception as e:
                #raise DDDException("Could not generate props for way: %s" % e, ddd_obj=way_2d)
                logger.error("Error generating props for way %s: %s", way_2d, e)

    def generate_props_2d_way(self, way_2d, pipeline):

        #if 'way_1d' not in way_2d.extra:
        #    # May be an intersection, should generate roadlines too
        #    return

        path = way_2d.extra['way_1d']

        # print(path.geom.type)
        # if path.geom.type != "LineString": return
        length = path.geom.length

        crop = ddd.shape(self.osm.area_crop)

        # Generate lines
        if way_2d.extra['ddd:way:roadlines']:

            lanes = way_2d.extra['ddd:way:lanes']
            numlines = lanes - 1 + 2
            for lineind in range(numlines):

                width = path.extra['ddd:width']
                lane_width = path.extra['ddd:way:lane_width']  # lanes_width / lanes
                lane_width_left = path.extra['ddd:way:lane_width_left']
                lane_width_right = path.extra['ddd:way:lane_width_right']

                line_continuous = False
                if lineind in [0, numlines - 1]: line_continuous = True
                if lanes >= 2 and lineind == int(numlines / 2) and not path.extra.get('osm:oneway', False) and path.extra.get('osm:highway', None) != 'roundabout': line_continuous = True
                line_x_offset = 0.076171875 if line_continuous else 0.5

                line_0_distance = -(width / 2) + lane_width_right
                line_distance = line_0_distance + lane_width * lineind

                # Create line
                pathline = path.copy()
                if abs(line_distance) > 0.01:
                    pathline.geom = pathline.geom.parallel_offset(line_distance, "left", resolution=2)
                line = pathline.buffer(0.15).material(ddd.mats.roadline)
                line.extra['way_1d'] = pathline

                # FIXME: Move cropping to generic site, use itermediate osm.something for storage
                # Also, cropping shall interpolate UVs (and propagated heights?)
                line = line.intersection(crop)
                line = line.intersection(way_2d)
                line = line.individualize()

                # if line.geom and not line.geom.is_empty:
                # try:
                uvmapping.map_2d_path(line, pathline, line_x_offset / 0.05)

                pipeline.root.find("/Roadlines2").append(line)

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

        # Check if to generate lamps
        if path.extra['ddd:way:lamps'] and (path.extra['ddd:layer'] in (0, "0") or path.extra['osm:layer'] in (0, "0")):

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
                        pipeline.root.find("/Items").append(item)

        '''
        # Check if to generate bridge posts
        if path.geom.length > 15.0 and path.extra['ddd:bridge:posts']:

            # Generate lamp posts
            interval = 20.0
            numposts = int(length / interval)
            idx = 0

            # Ignore if street is short
            #if numposts == 0: return

            logger.debug("Posts for bridge (length=%s, num=%d, way=%s)", length, numlamps, way_2d)
            for d in numpy.linspace(0.0, length, numlamps, endpoint=False):
                if d == 0.0: continue

                # Calculate left and right perpendicular intersections with sidewalk, park, land...
                p, segment_idx, segment_coords_a, segment_coords_b = path.interpolate_segment(d)

                dir_vec = (segment_coords_b[0] - segment_coords_a[0], segment_coords_b[1] - segment_coords_a[1])
                dir_vec_length = math.sqrt(dir_vec[0] ** 2 + dir_vec[1] ** 2)
                dir_vec = (dir_vec[0] / dir_vec_length, dir_vec[1] / dir_vec_length)

                #perpendicular_vec = (-dir_vec[1], dir_vec[0])
                #lightlamp_dist = path.extra['ddd:way:width'] * 0.5 + 0.5
                #left = (p[0] + perpendicular_vec[0] * lightlamp_dist, p[1] + perpendicular_vec[1] * lightlamp_dist)
                #right = (p[0] - perpendicular_vec[0] * lightlamp_dist, p[1] - perpendicular_vec[1] * lightlamp_dist)

                idx = idx + 1
                item = ddd.point(p, name="Bridge Post %s" % way_2d.name)
                #area = self.osm.areas_2d.intersect(item)
                # Check type of area point is on

                item.extra['way_2d'] = way_2d
                item.extra['ddd:bridge:post'] = True
                self.osm.items_1d.children.append(item)
        '''

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
                item.extra['osm:highway'] = 'traffic_signals'
                item.extra['ddd:angle'] = angle #+ math.pi/2
                pipeline.root.find("/Items").append(item)

        # Generate traffic signs
        if True and path.geom.length > 20.0 and path.extra['ddd:way:traffic_signs'] and path.extra['ddd:layer'] == "0":

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
                    item.extra['ddd:angle'] = angle - math.pi / 2
                    item.extra['osm:traffic_sign'] = random.choice(['es:r1', 'es:r2', 'es:p1', 'es:r101', 'es:r303', 'es:r305',
                                                                    'es:r308', 'es:r400c', 'es:r500', 'es:s13'])  # 'es:r301_50',
                    pipeline.root.find("/Items").append(item)

