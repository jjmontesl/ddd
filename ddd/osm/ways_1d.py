# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

from collections import defaultdict, namedtuple
import logging
import math
import random
import sys

import numpy
from shapely import ops
from shapely.geometry.linestring import LineString
from shapely.ops import linemerge

from ddd.core.exception import DDDException
from ddd.ddd import ddd
from ddd.geo import terrain
from ddd.ops import uvmapping


# Get instance of logger for this module
logger = logging.getLogger(__name__)

"""
Each of the connections between ways during first stage (to a way, with own and other's vertex index).
"""
WayConnection = namedtuple("WayConnection", "other self_idx other_idx")

"""
Each of the connections in a Join (to a way, with its incoming vertex index).
"""
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

    '''
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


    def split_ways_1d(self, ways_1d):
        """
        Splits all ways into the minimum pieces that have only an intersection at each end.

        This method modifies the passed in node, manipulating children.
        """

        # Splitting
        logger.info("Ways before splitting mid connections: %d", len(ways_1d.children))

        # Way schema
        for way in ways_1d.children:
            way.extra['ddd:connections'] = []

        # Split ways on joins
        vertex_cache = defaultdict(list)
        for way in ways_1d.children:
            start = way.geom.coords[0]
            end = way.geom.coords[-1]
            #for c in (start, end):
            for c in list(way.geom.coords):
                vertex_cache[c].append(way)

        split = True
        while split:
            split = False
            for way in ways_1d.children:
                for way_idx, c in enumerate(way.geom.coords[1:-1]):
                    # If vertex is shared (in cache and more than one feature uses it)
                    if c in vertex_cache and len(vertex_cache[c]) > 1:
                        split1, split2 = self.split_way_1d_vertex(ways_1d, way, c)
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

        logger.debug("Ways after splitting mid connections: %d", len(ways_1d.children))

        # Assign item nodes
        # TODO: this shall better come from osm node-names/relations directly, but supporting geojson is also nice
        # TODO: Before or after splitting?
        vertex_cache = defaultdict(list)
        for way in ways_1d.children:
            for c in list(way.geom.coords):
                vertex_cache[c].append(way)


        # Find connections
        # TODO: this shall possibly come from OSM relations (or maybe not, or optional)
        logger.info("Resolving connections between ways (%d ways).", len(ways_1d.children))
        vertex_cache = defaultdict(list)
        for way in ways_1d.children:
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
        for way in ways_1d.children:
            way.extra['ddd:layer_transition'] = False
            way.extra['ddd:layer'] = way.extra['osm:layer']
            way.extra['ddd:layer_int'] = int(way.extra['osm:layer'])
            way.extra['ddd:layer_min'] = int(way.extra['osm:layer'])
            way.extra['ddd:layer_max'] = int(way.extra['osm:layer'])
            # way.extra['ddd:layer_height'] = self.layer_height(str(way.extra['ddd:layer_min']))

        # Search transitions between layers
        for way in ways_1d.children:
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


        # At this point all ways 'connections' should have be resolved.


    def ways_1d_link_items(self, ways_1d, items_1d):
        """
        Links items to ways, and ways to items.

        Note: currenty matching node coordinates as nodes are not referenced in current geojson input.

        FIXME: currently sets first found way as 'osm:item:way' key.
        """

        # Assign item nodes
        # TODO: this shall better come from osm node-names/relations directly, but supporting geojson is also nice
        # TODO: Before or after splitting?
        vertex_cache = defaultdict(list)
        for way in ways_1d.children:
            for c in list(way.geom.coords):
                vertex_cache[tuple(c[:2])].append(way)

        logger.warn("Asociating Items to Ways via nodes (only Point items).")
        for item in items_1d.children:
            if item.geom.type in ('Polygon', 'MultiPolygon', 'LineString'):
                continue
            if tuple(item.geom.coords[0][:2]) in vertex_cache:
                logger.debug("Associating item to way: %s (%s) to %s", item, item.extra, vertex_cache[item.geom.coords[0]])
                item_coords =  vertex_cache[item.geom.coords[0]]
                if len(item_coords) > 0:
                    item.extra['osm:item:way'] = item_coords[0]
                    item.extra['osm:item:ways'] = item_coords
                    for w in vertex_cache[item.geom.coords[0]]:
                        if 'osm:way:items' not in w.extra:
                            w.extra['osm:way:items'] = []
                        w.extra['osm:way:items'].append(item)


    def ways_1d_intersections(self, ways_1d):
        """
        Evaluates all ways and creates a structure for each intersection between 2 or more ways.

        Intersections are just data structures, they are not geometries.
        They are a list of joins (JoinConnection).
        """

        logger.info("Generating intersections from %d ways.", len(ways_1d.children))

        intersections = []
        intersections_cache = defaultdict(default=list)  # Map WayJoin to to intersections

        def get_create_intersection(joins):
            """Gets or creates an intersection for a given set of joins (way + idx)."""
            if not joins or len(joins) < 2:
                return None

            for j in joins:
                if j in intersections_cache.keys():
                    return intersections_cache[j]

            # if len(joins) == 2:
            #    logger.debug("Intersection of only 2 ways.")
            intersection = sorted([j for j in joins], key=id)

            intersections.append(intersection)
            for j in joins:
                intersections_cache[j] = intersection

            return intersection

        # Walk connected ways and generate intersections
        for way in ways_1d.children:

            # For each vertex (start / end), evaluate the connection
            connections_start = [c for c in way.extra['ddd:connections'] if c.self_idx == 0]
            connections_end = [c for c in way.extra['ddd:connections'] if c.self_idx == len(way.geom.coords) - 1]

            joins_start = [JoinConnection(way, 0)] + [JoinConnection(c.other, c.other_idx) for c in connections_start]
            joins_end = [JoinConnection(way, len(way.geom.coords) - 1)] + [JoinConnection(c.other, c.other_idx) for c in connections_end]

            way.extra['intersection_start'] = get_create_intersection(joins_start)
            way.extra['intersection_end'] = get_create_intersection(joins_end)


        self.osm.intersections = intersections
        logger.warn("Generated %d intersections.", len(self.osm.intersections))

        # TODO: Should add intersection as points to Features or Meta, in order to use them later?


    def ways_1d_heights_initial(self, ways_1d):
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
        for way in ways_1d.children:

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

    def ways_1d_heights_connections(self, ways_1d):
        """
        """
        visited = set()
        for way in ways_1d.children:
            self.ways_1d_heights_connections_way(way, visited)

    def ways_1d_heights_propagate(self, ways_1d):

        for way in ways_1d.children:

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

        '''
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
        '''
        def height_apply_func(x, y, z, idx):
            # Find nearest points in path, then interpolate z
            coords = way.geom.coords if way.geom.type == "LineString" else sum([list(g.coords) for g in way.geom.geoms], [])

            way.dump(data='ddd')
            coords_p, segment_idx, segment_coords_a, segment_coords_b, closest_obj, closest_d = way.closest_segment(ddd.point([x, y]))
            dist_a = math.sqrt( (segment_coords_a[0] - coords_p[0]) ** 2 + (segment_coords_a[1] - coords_p[1]) ** 2 )
            dist_b = math.sqrt( (segment_coords_b[0] - coords_p[0]) ** 2 + (segment_coords_b[1] - coords_p[1]) ** 2 )
            factor_b = dist_a / (dist_a + dist_b)
            factor_a = 1 - factor_b  # dist_b / (dist_a + dist_b)
            interp_z = (segment_coords_a[2] * factor_a + segment_coords_b[2] * factor_b) if len(segment_coords_a) > 2 else 0

            return (x, y, z + (interp_z if way.extra.get('osm:natural', None) != "coastline" else 0.0))

        return height_apply_func

    def split_way_1d_vertex(self, ways_1d, way, v):

        coord_idx = way.vertex_index(v)

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

        ways_1d.children.remove(way)
        ways_1d.children.extend([part1, part2])

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
