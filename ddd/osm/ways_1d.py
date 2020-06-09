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

WayConnection = namedtuple("WayConnection", "other self_idx other_idx")
JoinConnection = namedtuple("JoinConnection", "way way_idx")


class Ways1DOSMBuilder():

    def __init__(self, osmbuilder):
        self.osm = osmbuilder

    def layer_height(self, layer_idx):
        lh = self.osm.layer_heights.get(layer_idx, None)
        if lh is None:
            if layer_idx.endswith("a"): layer_idx = layer_idx[:-1]
            lh = 5 * int(layer_idx)

        return lh

    def follow_way(self, way, depth=1, visited=None):

        if depth < 0: return []

        if visited is None:
            visited = set()

        # FIXME: Requires tagging the depth to account for nodes visited multiuple times through different ways
        # if way in visited: return []

        # logger.debug("Way: %s (connections: %s)", way, len(way.extra['ddd:connections']))
        for other, way_idx, other_idx in way.extra['ddd:connections']:
            # if other in visited: continue
            # logger.debug(indent_string + "  from %d/%d to %d/%d:", way_idx, len(way.geom.coords), other_idx, len(other.geom.coords))
            self.follow_way(other, depth - 1, visited)

        visited.add(way)

        return list(visited)

    '''
    def generate_ways_1d(self):

        # Generate paths
        logger.info("Generating 1D way path objects (requires /Items in order to match items to way nodes).")

        for feature in self.osm.features_2d.children:
            if feature.geom.type != 'LineString': continue
            way = self.generate_way_1d(feature)
            if way and not way.extra['ddd:item']:
                way.extra['ddd:connections'] = []
                self.osm.ways_1d.append(way)
            elif way and way.extra['ddd:item']:
                self.osm.items_1d.append(way)
            #else:
            #    logger.warn("Ignoring way (unknown feature type): %s", way)
    '''

    def split_ways_1d(self):

        # Splitting
        logger.info("Ways before splitting mid connections: %d", len(self.osm.ways_1d.children))

        # Way schema
        for way in self.osm.ways_1d.children:
            way.extra['ddd:connections'] = []

        # Split ways on joins
        vertex_cache = defaultdict(list)
        for way in self.osm.ways_1d.children:
            start = way.geom.coords[0]
            end = way.geom.coords[-1]
            #for c in (start, end):
            for c in list(way.geom.coords):
                vertex_cache[c].append(way)

        split = True
        while split:
            split = False
            for way in self.osm.ways_1d.children:
                for way_idx, c in enumerate(way.geom.coords[1:-1]):
                    # If vertex is shared (in cache and more than one feature uses it)
                    if c in vertex_cache and len(vertex_cache[c]) > 1:
                        split1, split2 = self.split_way_1d_vertex(way, c)
                        if split1 and split2:
                            for way_coords in (way.geom.coords[0], way.geom.coords[-1]):
                                vertex_cache[way_coords].remove(way)
                            for way_coords in (split1.geom.coords[0], split1.geom.coords[-1]):
                                vertex_cache[way_coords].append(split1)
                            for way_coords in (split2.geom.coords[0], split2.geom.coords[-1]):
                                vertex_cache[way_coords].append(split2)
                            split = True
                        if split: break
                if split: break
        vertex_cache = None

        logger.debug("Ways after splitting mid connections: %d", len(self.osm.ways_1d.children))

        # Assign item nodes
        # TODO: this shall better come from osm node-names/relations directly, but supporting geojson is also nice
        # TODO: Before or after splitting?
        vertex_cache = defaultdict(list)
        for way in self.osm.ways_1d.children:
            for c in list(way.geom.coords):
                vertex_cache[c].append(way)
        for item in self.osm.items_1d.children:
            if item.geom.coords[0] in vertex_cache:
                #logger.debug("Associating item to ways: %s (%s) to %s", item, item.extra, vertex_cache[item.geom.coords[0]])
                item.extra['osm:item:way'] = vertex_cache[item.geom.coords[0]][0]
                item.extra['osm:item:ways'] = vertex_cache[item.geom.coords[0]]
                #if len(vertex_cache[item.geom.coords[0]]):
                #    raise NotImplementedError()

        # Find connections
        # TODO: this shall possibly come from OSM relations (or maybe not, or optional)
        logger.info("Resolving connections between ways (%d ways).", len(self.osm.ways_1d.children))
        vertex_cache = defaultdict(list)
        for way in self.osm.ways_1d.children:
            # start = way.geom.coords[0]
            # end = way.geom.coords[-1]
            for way_idx, c in enumerate(way.geom.coords):
                # cidx = "%.0f,%.0f" % (c[0], c[1])
                cidx = c
                vertex_cache[cidx].append(way)
                for other in vertex_cache[cidx]:
                    if other == way: continue
                    # way.extra['ddd:connections'].append(WayConnection(other, way_idx, 0))
                    self.connect_ways_1d(way, other)  # , way_idx)
        vertex_cache = None

        # Find transitions between more than one layer (ie tunnel to bridge) and split
        for way in self.osm.ways_1d.children:
            way.extra['ddd:layer_transition'] = False
            way.extra['ddd:layer'] = way.extra['osm:layer']
            way.extra['ddd:layer_int'] = int(way.extra['osm:layer'])
            way.extra['ddd:layer_min'] = int(way.extra['osm:layer'])
            way.extra['ddd:layer_max'] = int(way.extra['osm:layer'])
            # way.extra['ddd:layer_height'] = self.layer_height(str(way.extra['ddd:layer_min']))

        # Search transitions between layers
        for way in self.osm.ways_1d.children:
            for other, way_idx, other_idx in way.extra['ddd:connections']:
                way.extra['ddd:layer_min'] = min(way.extra['ddd:layer_min'], int(other.extra['ddd:layer_int']))
                way.extra['ddd:layer_max'] = max(way.extra['ddd:layer_max'], int(other.extra['ddd:layer_int']))

                '''
                # Hack, we should follow paths and propagate heights
                if other.extra['ddd:layer_int'] == way.extra['ddd:layer_max']:
                    way.extra['ddd:layer_dir_up'] = 1 if (way_idx == 0) else -1
                else:
                    way.extra['ddd:layer_dir_up'] = -1 if (way_idx == 0) else 1
                '''

            # FIXME: This shall be done below possibly (when processing connections ?)
            if way.extra['ddd:layer_min'] != way.extra['ddd:layer_max'] and way.extra['ddd:layer_int'] == 0:
                # logger.debug("Layer transition (%s <-> %s): %s <-> %s", way.extra['ddd:layer_min'],other.extra['ddd:layer_max'], way, other)
                # way.extra['ddd:layer_transition'] = True
                way.extra['ddd:layer'] = str(way.extra['ddd:layer_min']) + "a"

        # Propagate height across connections for transitions
        # self.generate_ways_1d_heights()

        # Generate interesections
        self.ways_1d_intersections()

        # Road 1D heights
        self.ways_1d_heights_initial()
        self.ways_1d_heights_connections()  # and_layers_and_transitions_etc
        self.ways_1d_heights_propagate()

        # Propagate height beyond transition layers if gradient is too large?!

        # Soften / subdivide roads if height angle is larger than X (try as alternative to massive subdivision of roads?)

    def ways_1d_intersections(self):
        """
        Intersections are just data structures, they are not geometries.
        """

        logger.info("Generating intersections from %d ways.", len(self.osm.ways_1d.children))

        intersections = []
        intersections_cache = defaultdict(default=list)

        def get_create_intersection(joins):
            if not joins or len(joins) < 2:
                return None

            for j in joins:
                if j in intersections_cache.keys():
                    return intersections_cache[j]

            # if len(joins) == 2:
            #    logger.debug("Intersection of only 2 ways.")
            intersection = [j for j in joins]
            intersections.append(intersection)
            for j in joins: intersections_cache[j] = intersection

            return intersection

        # Walk connected ways and generate intersections
        for way in self.osm.ways_1d.children:

            # For each vertex (start / end), evaluate the connection
            connections_start = [c for c in way.extra['ddd:connections'] if c.self_idx == 0]
            connections_end = [c for c in way.extra['ddd:connections'] if c.self_idx == len(way.geom.coords) - 1]

            joins_start = [JoinConnection(way, 0)] + [JoinConnection(c.other, c.other_idx) for c in connections_start]
            joins_end = [JoinConnection(way, len(way.geom.coords) - 1)] + [JoinConnection(c.other, c.other_idx) for c in connections_end]

            way.extra['intersection_start'] = get_create_intersection(joins_start)
            way.extra['intersection_end'] = get_create_intersection(joins_end)

        self.osm.intersections = intersections
        logger.info("Generated %d intersections", len(self.osm.intersections))

    def ways_1d_heights_initial(self):
        """
        Heights in 1D, regarding connections with bridges, tunnels...
        Road flatness is to be resolved afterwards in 2D.

        We have several height concepts:
        - relative height (relative to layer 0: 0)
        - terrain and absolute height (when considering terrain)
        TODO: these concepts still need to be pinpointed, when we resolve what

        We need to define for each vertex / node / road:
        # height, "nominal layer?", and transition=layers-affected
        # tunnels cannot be transitions up  (actually, we should check if there are objects)
        # bridges cannot be transitions down but can go a bit down if needed (actually, we should check if there are objects9
        # all can go up or down depending on min/max limits (inside minor streets lower tunnels, highways have higher tunnels, etc)

        """
        for way in self.osm.ways_1d.children:

            height = 0.0

            '''
            if way.extra['tunnel']:
                height = -5
            elif way.extra['bridge']:
                height = 6
            '''
            height = self.layer_height(way.extra['ddd:layer'])

            way.extra['ddd:way_height'] = height
            way.extra['ddd:way_height_start'] = height
            way.extra['ddd:way_height_end'] = height

            # way.extra['ddd:way_height_low_min'] = height - 1
            # way.extra['ddd:way_height_low_max'] = height + 1
            # way.extra['ddd:way_height_high_min'] = height - 1
            # way.extra['ddd:way_height_high_max'] = height + 1
            way.extra['ddd:way_height_min'] = height - 1
            way.extra['ddd:way_height_max'] = height + 1
            way.extra['ddd:way_height_weight'] = 0.001  # do not affect height
            # way.extra['ddd:way_height_start_min'] = height - 1
            # way.extra['ddd:way_height_start_max'] = height + 1
            # way.extra['ddd:way_height_end_min'] = height - 1
            # way.extra['ddd:way_height_end_max'] = height + 1

            if way.extra.get('osm:tunnel', None):
                way.extra['ddd:way_height_min'] = height - 3
                way.extra['ddd:way_height_weight'] = 1.0
            elif way.extra.get('osm:bridge', None):
                way.extra['ddd:way_height_min'] = height - 2
                way.extra['ddd:way_height_max'] = height + 3
                way.extra['ddd:way_height_weight'] = 1.0
            elif way.extra.get('osm:roundabout', None) == "roundabout":
                # way.extra['ddd:way_leveling'] = height - 2
                way.extra['ddd:way_height_min'] = height - 2
                way.extra['ddd:way_height_max'] = height + 3
                way.extra['ddd:way_height_weight'] = 0.001  # Actually height could move, but altogether
                # way.extra['ddd:way_height_leveling'] = 0.9  # Actually height could move, but altogether
            else:
                way.extra['osm:way_height_max'] = height + 5
                way.extra['ddd:way_height_min'] = height - 5  # (take from settings / next layer)

            # way.geom = LineString([(c[0], c[1], 0.0) for c in way.geom.coords])

    def ways_1d_heights_connections_way(self, way, visited_vertexes):
        # logger.debug("Stepping: %s", way)

        # At the end, examine gap with connections
        end_vertex_idx = len(way.geom.coords) - 1

        # For each vertex (start / end), evaluate the connection
        connections_start = [c for c in way.extra['ddd:connections'] if c.self_idx == 0]
        connections_end = [c for c in way.extra['ddd:connections'] if c.self_idx == end_vertex_idx]

        self_idx = None
        for cons in (connections_start, connections_end):
            self_idx = 0 if self_idx is None else end_vertex_idx
            if not cons: continue
            vertex_coords = way.geom.coords[self_idx]
            if vertex_coords in visited_vertexes: continue
            visited_vertexes.add(vertex_coords)
            # heights = [way.extra['ddd:way_height']] + [c.other.extra['ddd:way_height'] for c in cons]
            heights_weighted = [way.extra['ddd:way_height'] * way.extra['ddd:way_height_weight']] + [c.other.extra['ddd:way_height'] * c.other.extra['ddd:way_height_weight'] for c in cons]
            heights_span = [way.extra['ddd:way_height_weight']] + [c.other.extra['ddd:way_height_weight'] for c in cons]
            heights_weighted_avg = (sum(heights_weighted) / sum(heights_span)) if sum(heights_span) > 0 else way.extra['ddd:way_height']

            # logger.debug("Connections at %s (height=%.5f, heights_avg=%.5f)", way, way.extra['ddd:way_height'], heights_weighted_avg)

            if self_idx == 0:
                way.extra['ddd:way_height_start'] = heights_weighted_avg
            else:
                way.extra['ddd:way_height_end'] = heights_weighted_avg

            for con in cons:
                if con.other_idx == 0:
                    con.other.extra['ddd:way_height_start'] = heights_weighted_avg
                else:
                    con.other.extra['ddd:way_height_end'] = heights_weighted_avg

    def ways_1d_heights_connections(self):
        """
        """
        visited = set()
        for way in self.osm.ways_1d.children:
            self.ways_1d_heights_connections_way(way, visited)

    def ways_1d_heights_propagate(self):

        for way in self.osm.ways_1d.children:

            # if not way.extra['ddd:layer_transition']: continue

            height_start = way.extra['ddd:way_height_start']
            height_end = way.extra['ddd:way_height_end']

            if way.extra.get('osm:natural', None) == "coastline": continue

            # if height_start == height_end: continue

            # logger.info("Transition from %s to %s", height_start, height_end)

            coords = way.geom.coords

            # Walk segment
            # Interpolate path between lower and ground height
            l = 0.0
            ncoords = [ (coords[0][0], coords[0][1], height_start) ]
            for idx in range(len(coords) - 1):
                p, pn = coords[idx:idx + 2]
                # p, pn = coords[idx:idx+2]
                pl = math.sqrt((pn[0] - p[0]) ** 2 + (pn[1] - p[1]) ** 2)
                l += pl
                h = height_start + (height_end - height_start) * (l / way.geom.length)
                # logger.debug("  Distance: %.2f  Height: %.2f", l, h)
                ncoords.append((pn[0], pn[1], h))

            way.geom.coords = ncoords

            # way.extra['height_start'] = height_start
            # way.extra['height_end'] = height_end
            # logger.debug("Heights [height_start=%.1f, height_end=%.1f]: %s", height_start, height_end, way)

    def get_height_apply_func(self, way):

        def height_apply_func(x, y, z, idx):
            # Find nearest point in path, and return its height
            coords = way.geom.coords if way.geom.type == "LineString" else sum([list(g.coords) for g in way.geom.geoms], [])

            closest_in_path = None  # path.geom.coords[0]
            closest_dist = math.inf
            for idx, p in enumerate(coords):
                pd = math.sqrt((x - p[0]) ** 2 + (y - p[1]) ** 2)
                if idx == 0: pd = pd - 20.0
                if idx == len(coords) - 1: pd = pd - 20.0
                if pd < closest_dist:
                    closest_in_path = p
                    closest_dist = pd
            # logger.debug("Closest in path: %s", closest_in_path)
            return (x, y, z + (closest_in_path[2] if way.extra.get('osm:natural', None) != "coastline" else 0.0))  #  if len(closest_in_path) > 2 else 0.0

        return height_apply_func

    def split_way_1d_vertex(self, way, v):

        coord_idx = None
        for idx, c in enumerate(way.geom.coords):
            if v == c:
                coord_idx = idx
                break

        if coord_idx is None:
            logger.debug("Coordinates: %s", list(way.geom.coords))
            raise ValueError("Coordinate not found (%s) to split a path (%s) by coordinates." % (v, way))
        if coord_idx == 0 or coord_idx >= len(way.geom.coords) - 1:
            # raise ValueError("Cannot split a path (%s) by the first or last index (%s)." % (way, coord_idx))
            return None, None

        # logger.debug("Splitting %s at %d (%s)", way, coord_idx, v)

        part1 = way.copy()
        part1.geom = LineString(way.geom.coords[:coord_idx + 1])
        part1.extra['ddd:connections'] = []
        part2 = way.copy()
        part2.geom = LineString(way.geom.coords[coord_idx:])
        part2.extra['ddd:connections'] = []
        '''
        part1 = DDDObject2(name=way.name + "/1", geom=LineString(way.geom.coords[:coord_idx + 1]), extra=copy.deepcopy(way.extra))
        part1.extra['ddd:connections'] = []
        part2 = DDDObject2(name=way.name + "/2", geom=LineString(way.geom.coords[coord_idx:]), extra=copy.deepcopy(way.extra))
        part2.extra['ddd:connections'] = []
        '''

        self.osm.ways_1d.children.remove(way)
        self.osm.ways_1d.children.extend([part1, part2])

        return part1, part2

    def connect_ways_1d(self, way, other):
        # other_idx = 0 if r_start in (start, end) else -1
        # other_idx = list(other.geom.coords).index(way.geom.coords[way_idx])
        found = False
        for way_idx, wc in enumerate(way.geom.coords):
            for other_idx, oc in enumerate(other.geom.coords):
                if wc == oc:
                    found = True
                    other_con = WayConnection(other, way_idx, other_idx)
                    if other_con not in way.extra['ddd:connections']:
                        way.extra['ddd:connections'].append(other_con)
                    way_con = WayConnection(way, other_idx, way_idx)
                    if way_con not in other.extra['ddd:connections']:
                        other.extra['ddd:connections'].append(way_con)
                if found: break
            if found: break

        if not found:
            raise ValueError("Cannot find vertex index by which two paths are connected.")

        # logger.debug("Way connection: %s (idx: %d) <-> %s (idx: %d)", way, way_idx, other, other_idx)

        '''
        for r in self.ways_1d.children:
            r_start = r.extra['path'].geom.coords[0]
            r_end = r.extra['path'].geom.coords[-1]

            if start in (r_start, r_end) or end in (r_start, r_end):
                source_idx = 0 if start in (r_start, r_end) else -1
                target_idx = 0 if r_start in (start, end) else -1
                connected.append((r, source_idx, target_idx))
                # TODO: modify roads metadata
        '''

        pass

    '''
    def find_connected_ways(self, way, roads):
        """
        Finds features connected to this one.

        Notes:
        - Currently for roads/ways only.
        - Using vertex coordinates (OSM shared nodes should be used, but input is
          not OSM directly and osmtogeojson erases that info)
        """
        connected = []
        start = way.extra['path'].geom.coords[0]
        end = way.extra['path'].geom.coords[-1]
        for r in roads.children:
            r_start = r.extra['path'].geom.coords[0]
            r_end = r.extra['path'].geom.coords[-1]

            if start in (r_start, r_end) or end in (r_start, r_end):
                source_idx = 0 if start in (r_start, r_end) else -1
                target_idx = 0 if r_start in (start, end) else -1
                connected.append((r, source_idx, target_idx))
                # TODO: modify roads metadata

        return connected
    '''

    def get_way_2d(self, way_1d):
        for l in self.osm.ways_2d.values():
            for way_2d in l.children:
                if 'way_1d' in way_2d.extra and way_2d.extra['way_1d'] == way_1d:
                    return way_2d
        logger.warn("Tried to get way 2D for not existing way 1D: %s", way_1d)
        # raise ValueError("Tried to get way 2D for not existing way 1D: %s" % way_1d)
        return DDDObject2()

    def generate_ways_2d(self):

        # Generate layers
        for layer_idx in self.osm.layer_indexes:
            self.generate_ways_2d_layer(layer_idx)

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

            join_ways = ddd.group([self.get_way_2d(j.way) for j in intersection])
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

                """
                if ('666643710' in intersection_2d.name):
                    print(intersection_2d.extra)
                    sys.exit(1)
                """

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
        self.osm.intersections_2d = intersections_2d

        # Add intersections to respective layers
        for int_2d in intersections_2d.children:
            # print(int_2d.extra)
            self.osm.ways_2d[int_2d.extra['ddd:layer']].children.append(int_2d)

        # Subtract intersections from ways
        for layer_idx in self.osm.ways_2d.keys():  # ["-1a", "0a", "1a"]
            ways = []
            for way in self.osm.ways_2d[layer_idx].children:

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

            self.osm.ways_2d[layer_idx] = ddd.group(ways, empty="2", name="Ways 2D %s" % layer_idx)

        # logger.info("Saving intersections 2D.")
        # ddd.group([self.osm.ways_2d["0"].extrude(1.0), self.osm.intersections_2d.material(ddd.mats.highlight).extrude(1.5)]).save("/tmp/ddd-intersections.glb")

        # Subtract connected ways
        # TODO: This shall be possibly done when creating ways not after
        # union_lm1 = self.osm.ways_2d["-1"].union()
        # union_l0 = self.osm.ways_2d["0"].union()
        # union_l1 = self.osm.ways_2d["1"].union()
        '''
        for layer_idx in ["-1a", "0a", "1a"]:
            ways = []
            for way in self.osm.ways_2d[layer_idx].children:
                connected = self.follow_way(way.extra['way_1d'], 1)
                connected.remove(way.extra['way_1d'])
                connected_2d = ddd.group([self.get_way_2d(c) for c in connected])
                wayminus = way.subtract(connected_2d).buffer(0.001)
                ways.append(wayminus)
            self.osm.ways_2d[layer_idx] = ddd.group(ways, empty="2")
        '''

        # self.osm.ways_2d["-1a"] = self.osm.ways_2d["-1a"].material(ddd.mat_highlight)
        # self.osm.ways_2d["-1a"].children[0].dump()
        # print(self.osm.ways_2d["-1a"].children[0].extra)
        # print(list(self.osm.ways_2d["-1a"].children[0].extra['way_1d'].geom.coords))
        # sys.exit(0)

        # self.osm.ways_2d["0a"] = self.osm.ways_2d["0a"].subtract(union_l0).subtract(union_l1)
        # self.osm.ways_2d["1a"] = self.osm.ways_2d["1a"].subtract(union_l1)

    def generate_ways_2d_layer(self, layer_idx):
        '''
        - Sorts ways (more important first),
        - Generates 2D shapes
        - Resolve intersections
        - Add metadata (road name, surface type, connections?)
        - Consider elevation and level roads on the transversal axis
        '''
        ways_1d = [w for w in self.osm.ways_1d.children if w.extra['ddd:layer'] == layer_idx]
        logger.info("Generating 2D ways for layer %s (%d ways)", layer_idx, len(ways_1d))

        ways_1d.sort(key=lambda w: w.extra['ddd:way:weight'])

        ways_2d = defaultdict(list)
        for w in ways_1d:
            #f = w.extra['osm:feature']
            way_2d = self.generate_way_2d(w)
            if way_2d:
                weight = way_2d.extra['ddd:way:weight']
                ways_2d[weight].append(way_2d)

        '''
        # Trim roads
        accum_roads = DDDObject2()
        for weight in sorted(ways_2d.keys()):
            weight_roads = ways_2d[weight]
            new_weight_roads = []
            for r in weight_roads:
                new_road = r.subtract(accum_roads)  # Higher vertex count, precission issues
                new_road = new_road.buffer(0.001)    # Avoids precission issues after subtraction
                accum_roads = accum_roads.union(r)
                new_weight_roads.append(new_road)
            ways_2d[weight] = new_weight_roads
        '''

        roads = sum(ways_2d.values(), [])
        if roads:
            roads = ddd.group(roads, name="Ways (layer: %s)" % layer_idx)  # translate([0, 0, 50])
            self.osm.ways_2d[layer_idx] = roads

    '''
    def generate_roads_2d(self, layer_idx):
        """
        - Sorts ways (more important first),
        - Generates 2D shapes
        - Resolve intersections
        - Add metadata (road name, surface type, connections?)
        - Consider elevation and level roads on the transversal axis
        """
        logger.info("Generating 2D roads for layer %d", layer_idx)

        features = [f for f in self.osm.features if int(f['properties'].get('ddd:layer', 0)) == layer_idx]

        features.sort(key=lambda f: self.road_weight(f))

        roads_2d = defaultdict(list)
        for f in features:
            road_2d = self.generate_road_2d(f)
            weight = self.road_weight(f)
            if road_2d:
                roads_2d[weight].append(road_2d)

        # Trim roads
        accum_roads = DDDObject2()
        for weight in sorted(roads_2d.keys()):
            weight_roads = roads_2d[weight]
            new_weight_roads = []
            for r in weight_roads:
                new_road = r.subtract(accum_roads)  # Higher vertex count, precission issues
                new_road = new_road.buffer(0.001)    # Avoids precission issues after subtraction
                accum_roads = accum_roads.union(r)
                new_weight_roads.append(new_road)
            roads_2d[weight] = new_weight_roads

        roads = sum(roads_2d.values(), [])
        roads = ddd.group(roads, name="Ways (layer: %s)" % layer_idx)  #translate([0, 0, 50])

        return roads
    '''

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



    def generate_props_2d(self):
        """
        Road props (traffic lights, lampposts...).
        Need roads, areas, coastline, etc... and buildings
        """

        ways = []
        for wg in self.osm.ways_2d.values():
            ways.extend(wg.children)
        # ways = self.osm.ways_2d["0"].children

        logger.info("Generating props linked to ways (%d ways)", len(ways))

        for way_2d in ways:
            try:
                self.generate_props_2d_way(way_2d)
            except Exception as e:
                #raise DDDException("Could not generate props for way: %s" % e, ddd_obj=way_2d)
                logger.error("Error generating props for way %s: %s", way_2d, e)

    def generate_props_2d_way(self, way_2d):

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

                self.osm.roadlines_2d.children.append(line)

                # except Exception as e:
                #    logger.error("Could not UV map Way 2D from path: %s %s %s: %s", line, line.geom, pathline.geom, e)
                #    continue
                line_3d = line.triangulate().translate([0, 0, 0.05])  # Temporary hack until fitting lines properly
                vertex_func = self.get_height_apply_func(path)
                line_3d = line_3d.vertex_func(vertex_func)
                line_3d = terrain.terrain_geotiff_elevation_apply(line_3d, self.osm.ddd_proj)
                line_3d.extra['ddd:collider'] = False
                line_3d.extra['ddd:shadows'] = False
                line_3d.extra['ddd:occluder'] = False
                # print(line)
                # print(line.geom)
                uvmapping.map_3d_from_2d(line_3d, line)
                # uvmapping.map_2d_path(line_3d, path)

                self.osm.roadlines_3d.children.append(line_3d)

        # Check if to generate lamps
        if path.extra['ddd:way:lamps'] and path.extra['ddd:layer'] == "0":

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
                        self.osm.items_1d.children.append(item)

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
        if True and path.geom.length > 45.0 and path.extra['ddd:way:traffic_signals'] and path.extra['ddd:layer'] == "0":

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
                self.osm.items_1d.children.append(item)

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
                    item.extra['ddd:angle'] = angle
                    item.extra['osm:traffic_sign'] = random.choice(['es:r1', 'es:r2', 'es:p1', 'es:r101', 'es:r303', 'es:r305',
                                                                    'es:r308', 'es:r400c', 'es:r500', 'es:s13'])  # 'es:r301_50',
                    self.osm.items_1d.children.append(item)

