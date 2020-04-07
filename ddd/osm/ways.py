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

# Get instance of logger for this module
logger = logging.getLogger(__name__)

WayConnection = namedtuple("WayConnection", "other self_idx other_idx")
JoinConnection = namedtuple("JoinConnection", "way way_idx")


class WaysOSMBuilder():

    config_ways = {
        '_default': {'lanes': None,
                     'width': None,
                     'material': None,
                     'max_inclination': 15,
                     'leveling_factor': 0.5,

                     'allows_cars': True,
                     'allows_trucks': True,
                     'allows_pedestrians': True,

                     'lamps_interval': 25,
                     'lamps_alternate': True,
                     'traffic_lights': True },

        'highway': {},

        'stairs': {'lanes': None, 'width': None, 'material': None},
        'pedestrian': {'lanes': None, 'width': None, 'material': None},

    }

    def __init__(self, osmbuilder):

        self.osm = osmbuilder

    def layer_height(self, layer_idx):
        return self.osm.layer_heights[layer_idx]

    def follow_way(self, way, depth=1, visited=None):

        if depth < 0: return []

        if visited is None:
            visited = set()

        # FIXME: Requires tagging the depth to account for nodes visited multiuple times through different ways
        # if way in visited: return []

        # logger.debug("Way: %s (connections: %s)", way, len(way.extra['connections']))
        for other, way_idx, other_idx in way.extra['connections']:
            # if other in visited: continue
            # logger.debug(indent_string + "  from %d/%d to %d/%d:", way_idx, len(way.geom.coords), other_idx, len(other.geom.coords))
            self.follow_way(other, depth - 1, visited)

        visited.add(way)

        return list(visited)

    def generate_ways_1d(self):

        # Generate paths
        logger.info("Generating 1D way path objects.")

        for feature in self.osm.features:
            if feature['geometry']['type'] != 'LineString': continue
            way = self.generate_way_1d(feature)
            if way and not way.extra['ddd:item']:
                way.extra['connections'] = []
                self.osm.ways_1d.append(way)
            elif way and way.extra['ddd:item']:
                self.osm.items_1d.append(way)

        # Splitting
        logger.info("Ways before splitting mid connections: %d", len(self.osm.ways_1d.children))

        '''
        # Split all
        vertex_cache = defaultdict(list)
        for way in self.osm.ways_1d.children:
            #start = way.geom.coords[0]
            #end = way.geom.coords[-1]
            for way_idx, c in enumerate(way.geom.coords):
                vertex_cache[c].append(way)

        split = True
        while split:
            split = False
            for c, ways in vertex_cache.items():
                if len(ways) > 1:
                    for w in ways:
                        #if w.extra['natural'] == 'coastline': continue
                        split1, split2 = self.split_way_1d_vertex(w, c)
                        if split1 and split2:
                            for way_coords in w.geom.coords:
                                vertex_cache[way_coords].remove(w)
                            for way_coords in split1.geom.coords:
                                vertex_cache[way_coords].append(split1)
                            for way_coords in split2.geom.coords:
                                vertex_cache[way_coords].append(split2)
                            split = True
                        if split: break
                if split: break
        vertex_cache = None
        '''

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
                        # if w.extra['natural'] == 'coastline': continue
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
                    # way.extra['connections'].append(WayConnection(other, way_idx, 0))
                    self.connect_ways_1d(way, other)  # , way_idx)
        vertex_cache = None

        # Divide end-to-middle connections
        '''
        logger.info("Ways before splitting mid connections: %d", len(self.osm.ways_1d.children))
        split = False
        while split:
            split = False
            for way in self.osm.ways_1d.children:
                for other, way_idx, other_idx in way.extra['connections']:
                    #if other.extra['layer'] == way.extra['layer']: continue
                    if (other_idx > 0 and other_idx != len(other.geom.coords) - 1):
                        #if not way.extra['layer_transition']: continue
                        #logger.info("Mid point connection: %s <-> %s", way, other)
                        self.split_way_1d(other, other_idx)
                        # Restart after each split
                        split = True
                        break
                if split: break

        logger.debug("Ways after splitting mid connections: %d", len(self.osm.ways_1d.children))
        '''

        # Find transitions between more than one layer (ie tunnel to bridge) and split
        for way in self.osm.ways_1d.children:
            way.extra['layer_transition'] = False
            way.extra['layer_int'] = int(way.extra['layer'])
            way.extra['layer_min'] = int(way.extra['layer'])
            way.extra['layer_max'] = int(way.extra['layer'])
            # way.extra['layer_height'] = self.layer_height(str(way.extra['layer_min']))

        # Search transitions between layers
        for way in self.osm.ways_1d.children:
            for other, way_idx, other_idx in way.extra['connections']:
                way.extra['layer_min'] = min(way.extra['layer_min'], int(other.extra['layer_int']))
                way.extra['layer_max'] = max(way.extra['layer_max'], int(other.extra['layer_int']))

                '''
                # Hack, we should follow paths and propagate heights
                if other.extra['layer_int'] == way.extra['layer_max']:
                    way.extra['layer_dir_up'] = 1 if (way_idx == 0) else -1
                else:
                    way.extra['layer_dir_up'] = -1 if (way_idx == 0) else 1
                '''

            # FIXME: This shall be done below possibly (when processing connections ?)
            if way.extra['layer_min'] != way.extra['layer_max'] and way.extra['layer_int'] == 0:
                # logger.debug("Layer transition (%s <-> %s): %s <-> %s", way.extra['layer_min'],other.extra['layer_max'], way, other)
                # way.extra['layer_transition'] = True
                way.extra['layer'] = str(way.extra['layer_min']) + "a"

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

    def generate_way_1d(self, feature):

        highway = feature['properties'].get('highway', None)
        footway = feature['properties'].get('footway', None)
        barrier = feature['properties'].get('barrier', None)
        railway = feature['properties'].get('railway', None)
        historic = feature['properties'].get('historic', None)
        natural = feature['properties'].get('natural', None)
        man_made = feature['properties'].get('man_made', None)
        tunnel = feature['properties'].get('tunnel', None)
        bridge = feature['properties'].get('bridge', None)
        junction = feature['properties'].get('junction', None)
        waterway = feature['properties'].get('waterway', None)
        oneway = feature['properties'].get('oneway', None)
        ref = feature['properties'].get('ref', None)
        maxspeed = feature['properties'].get('maxspeed', None)
        power = feature['properties'].get('power', None)
        route = feature['properties'].get('route', None)
        indoor = feature['properties'].get('indoor', None)
        disused = feature['properties'].get('disused', None)

        if junction == "roundabout": oneway = True

        path = ddd.shape(feature['geometry'])
        # path.geom = path.geom.simplify(tolerance=self.simplify_tolerance)

        name_id = (feature['properties'].get('name', feature['properties'].get('id')))
        name = "Way: %s" % name_id
        width = None  # if not set will be discarded
        material = ddd.mats.asphalt
        extra_height = 0.0
        lanes = None
        lamps = False
        trafficlights = False
        roadlines = False

        layer = None

        lane_width = 3.3
        lane_width_right = 0.30
        lane_width_left = 0.30

        create_as_item = False

        if highway in ('proposed', 'construction', ):
            return None

        elif highway == "motorway":
            lane_width = 3.6
            lane_width_right = 1.5
            lane_width_left = 1.0
            lanes = 2
            roadlines = True
        elif highway == "motorway_link":
            lanes = 1
            lane_width = 3.6
            lane_width_right = 1.5
            lane_width_left = 1.0
            roadlines = True
        elif highway == "trunk":
            lanes = 1
            lane_width = 3.4
            lane_width_right = 1.5
            lane_width_left = 0.5
            roadlines = True
        elif highway == "trunk_link":
            lanes = 1
            lane_width = 3.5
            lane_width_right = 1.5
            lane_width_left = 1.0
            roadlines = True

        elif highway == "primary":
            lanes = 2
            lane_width = 3.4
            lane_width_right = 1.0
            lane_width_left = 0.5
            roadlines = True
        elif highway == "primary_link":
            lanes = 2
            lane_width = 3.4
            lane_width_right = 1.0
            lane_width_left = 0.5
            roadlines = True
        elif highway == "secondary":
            lanes = 2 if oneway else 3
            lane_width = 3.4
            lamps = True
            trafficlights = True
            roadlines = True
        elif highway in ("tertiary", "road"):
            lanes = 2
            lane_width = 3.4
            lamps = True  # shall be only in city?
            trafficlights = True
            roadlines = True
        elif highway == "service":
            lanes = 1
            lamps = True  # shall be only in city?
            roadlines = True
        elif highway in ("residential", "living_street"):
            # lanes = 1.0  # Using 1 lane for residential/living causes too small roads
            # extra_height = 0.1
            lanes = 2
            lamps = True  # shall be only in city?
            trafficlights = False
            roadlines = True
        elif highway in ("footway",):
            lanes = 0
            material = ddd.mats.dirt
            extra_height = 0.0
            width = 0.6 * 3.3
            if footway == 'sidewalk': return None
        elif highway in ("path", "track"):
            lanes = 0
            material = ddd.mats.dirt
            # extra_height = 0.2
            width = 0.6 * 3.3
        elif highway in ("steps", "stairs"):
            lanes = 0
            material = ddd.mats.pathwalk
            extra_height = 0.2  # 0.2 allows easy car driving
            width = 0.6 * 3.3
        elif highway == "pedestrian":
            lanes = 0
            material = ddd.mats.pathwalk
            extra_height = 0.2
            width = 2 * 3.30
            lamps = True  # shall be only in city?
        elif highway == "cycleway":
            lanes = 1
            lane_width = 1.5
            material = ddd.mats.pitch
            extra_height = 0.2
            roadlines = True
        elif highway == "unclassified":
            lanes = 1
            material = ddd.mats.dirt

        elif highway == "raceway":
            lanes = 1
            lane_width = 10.0
            material = ddd.mats.dirt
            # extra_height = 0.2

        elif natural == "coastline":
            lanes = None
            name = "Coastline: %s" % name_id
            width = 0.5
            material = ddd.mats.terrain
            extra_height = 5.0  # FIXME: Things could cross othis, height shall reach sea precisely
        elif waterway == "river":
            lanes = None
            name = "River: %s" % name_id
            width = 6.0
            material = ddd.mats.sea

        elif railway:
            lanes = None
            width = 3.6
            material = ddd.mats.dirt
            name = "Railway: %s" % name_id
            #extra_height = 0.0

        elif barrier == 'city_wall':
            width = 1.0
            material = ddd.mats.stone
            extra_height = 2.0
            name = "City Wall: %s" % name_id
            path.extra['ddd:subtract_buildings'] = True
        elif historic == 'castle_wall':
            width = 3.0
            material = ddd.mats.stone
            extra_height = 3.5
            name = "Castle Wall: %s" % name_id
            path.extra['ddd:subtract_buildings'] = True

        elif barrier == 'hedge':
            width = 0.6
            lanes = None
            material = ddd.mats.treetop
            extra_height = 1.2
            create_as_item = True
            name = "Hedge: %s" % name_id
            path.extra['ddd:subtract_buildings'] = True

        elif barrier == 'fence':
            width = 0.05
            lanes = None
            material = ddd.mats.fence
            extra_height = 1.2
            create_as_item = True
            name = "Fence: %s" % name_id
            path.extra['ddd:subtract_buildings'] = True

        elif barrier == 'kerb':
            logger.debug("Ignoring kerb")
            return None

        elif man_made == 'pier':
            width = 1.8
            material = ddd.mats.wood

        elif barrier == 'retaining_wall':
            width = 0.7
            material = ddd.mats.stone
            extra_height = 1.5
            name = "Wall Retaining: %s" % name_id
            path.extra['ddd:subtract_buildings'] = True
        elif barrier == 'wall':
            # TODO: Get height and material from metadata
            width = 0.35
            material = ddd.mats.bricks
            extra_height = 1.8
            name = "Wall: %s" % name_id
            path.extra['ddd:subtract_buildings'] = True

        elif power == 'line':
            width = 0.1
            material = ddd.mats.steel
            layer = "3"
            create_as_item = True

        elif route:
            # Ignore routes
            return None

        elif highway:
            logger.info("Unknown highway type: %s (%s)", highway, feature['properties'])
            lanes = 2.0

        else:
            logger.debug("Unknown way (discarding): %s", feature['properties'])
            return None

        # Calculated properties

        flanes = feature['properties'].get('lanes', None)
        if flanes:
            lanes = int(float(flanes))

        lanes = int(lanes) if lanes is not None else None
        if lanes is None or lanes < 1:
            roadlines = False

        if not path.extra.get('oneway', False):
            lane_width_left = lane_width_right

        if width is None:
            try:
                if lanes == 1: lane_width = lane_width * 1.25
                width = lanes * lane_width + lane_width_left + lane_width_right
            except Exception as e:
                logger.error("Cannot calculate width from lanes: %s", feature['properties'])
                raise

        path = path.material(material)
        path.name = name
        path.extra['osm:feature'] = feature
        path.extra['highway'] = highway
        path.extra['barrier'] = barrier
        path.extra['railway'] = railway
        path.extra['historic'] = historic
        path.extra['natural'] = natural
        path.extra['tunnel'] = tunnel
        path.extra['bridge'] = bridge
        path.extra['junction'] = junction
        path.extra['waterway'] = waterway
        path.extra['ref'] = ref
        path.extra['maxspeed'] = maxspeed
        path.extra['man_made'] = man_made
        path.extra['power'] = power
        path.extra['width'] = width
        path.extra['lanes'] = lanes
        path.extra['layer'] = layer if layer is not None else feature['properties']['layer']
        path.extra['extra_height'] = extra_height
        path.extra['ddd_trafficlights'] = trafficlights
        path.extra['ddd:width'] = width
        path.extra['ddd:way:lane_width'] = lane_width
        path.extra['ddd:way:lane_width_left'] = lane_width_left
        path.extra['ddd:way:lane_width_right'] = lane_width_right
        path.extra['ddd:way:lamps'] = lamps
        path.extra['ddd:way:weight'] = self.road_weight(feature)
        path.extra['ddd:way:oneway'] = oneway
        path.extra['ddd:way:roadlines'] = roadlines  # should be ddd:road:roadlines ?
        path.extra['ddd:item'] = create_as_item
        path.extra['ddd:item:height'] = extra_height
        # print(feature['properties'].get("name", None))

        return path

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
            connections_start = [c for c in way.extra['connections'] if c.self_idx == 0]
            connections_end = [c for c in way.extra['connections'] if c.self_idx == len(way.geom.coords) - 1]

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
            height = self.layer_height(way.extra['layer'])

            way.extra['way_height'] = height
            way.extra['way_height_start'] = height
            way.extra['way_height_end'] = height

            # way.extra['way_height_low_min'] = height - 1
            # way.extra['way_height_low_max'] = height + 1
            # way.extra['way_height_high_min'] = height - 1
            # way.extra['way_height_high_max'] = height + 1
            way.extra['way_height_min'] = height - 1
            way.extra['way_height_max'] = height + 1
            way.extra['way_height_weight'] = 0.001  # do not affect height
            # way.extra['way_height_start_min'] = height - 1
            # way.extra['way_height_start_max'] = height + 1
            # way.extra['way_height_end_min'] = height - 1
            # way.extra['way_height_end_max'] = height + 1

            if way.extra['tunnel']:
                way.extra['way_height_min'] = height - 3
                way.extra['way_height_weight'] = 1.0
            elif way.extra['bridge']:
                way.extra['way_height_min'] = height - 2
                way.extra['way_height_max'] = height + 3
                way.extra['way_height_weight'] = 1.0
            elif way.extra['junction'] == "roundabout":
                # way.extra['way_leveling'] = height - 2
                way.extra['way_height_min'] = height - 2
                way.extra['way_height_max'] = height + 3
                way.extra['way_height_weight'] = 0.001  # Actually height could move, but altogether
                # way.extra['way_height_leveling'] = 0.9  # Actually height could move, but altogether
            else:
                way.extra['way_height_max'] = height + 5
                way.extra['way_height_min'] = height - 5  # (take from settings / next layer)

            # way.geom = LineString([(c[0], c[1], 0.0) for c in way.geom.coords])

    def ways_1d_heights_connections_way(self, way, visited_vertexes):
        # logger.debug("Stepping: %s", way)

        # At the end, examine gap with connections
        end_vertex_idx = len(way.geom.coords) - 1

        # For each vertex (start / end), evaluate the connection
        connections_start = [c for c in way.extra['connections'] if c.self_idx == 0]
        connections_end = [c for c in way.extra['connections'] if c.self_idx == end_vertex_idx]

        self_idx = None
        for cons in (connections_start, connections_end):
            self_idx = 0 if self_idx is None else end_vertex_idx
            if not cons: continue
            vertex_coords = way.geom.coords[self_idx]
            if vertex_coords in visited_vertexes: continue
            visited_vertexes.add(vertex_coords)
            # heights = [way.extra['way_height']] + [c.other.extra['way_height'] for c in cons]
            heights_weighted = [way.extra['way_height'] * way.extra['way_height_weight']] + [c.other.extra['way_height'] * c.other.extra['way_height_weight'] for c in cons]
            heights_span = [way.extra['way_height_weight']] + [c.other.extra['way_height_weight'] for c in cons]
            heights_weighted_avg = (sum(heights_weighted) / sum(heights_span)) if sum(heights_span) > 0 else way.extra['way_height']

            # logger.debug("Connections at %s (height=%.5f, heights_avg=%.5f)", way, way.extra['way_height'], heights_weighted_avg)

            if self_idx == 0:
                way.extra['way_height_start'] = heights_weighted_avg
            else:
                way.extra['way_height_end'] = heights_weighted_avg

            for con in cons:
                if con.other_idx == 0:
                    con.other.extra['way_height_start'] = heights_weighted_avg
                else:
                    con.other.extra['way_height_end'] = heights_weighted_avg

    def ways_1d_heights_connections(self):
        """
        """
        """
        Agent = namedtuple("Agent", "way direction")

        remaining_ways = list(self.osm.ways_1d.children)
        agents = []

        agent = Agent(remaining_ways[0], 1)
        agents.append(agent)

        for a in agents:
            self.ways_1d_propagate_heights_step(a)
        """
        visited = set()
        for way in self.osm.ways_1d.children:
            self.ways_1d_heights_connections_way(way, visited)

    def ways_1d_heights_propagate(self):

        for way in self.osm.ways_1d.children:

            # if not way.extra['layer_transition']: continue

            height_start = way.extra['way_height_start']
            height_end = way.extra['way_height_end']

            if way.extra['natural'] == "coastline": continue

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

    '''
    def generate_ways_1d_heights(self):

        for way in self.osm.ways_1d.children:
            if not way.extra['layer_transition']: continue

            height_start = self.layer_height(str(way.extra['layer_min']))
            height_end = self.layer_height(str(way.extra['layer_max']))
            #for other, way_idx, other_idx in way.extra['connections']:

            #logger.info("Transition from %s to %s", height_start, height_end)

            coords = way.geom.coords
            if way.extra['layer_dir_up'] == 1:
                height_start, height_end = height_end, height_start

            # Walk segment
            # Interpolate path between lower and ground height
            l = 0.0
            ncoords = [ (coords[0][0], coords[0][1], height_start) ]
            for idx in range(len(coords) - 1):
                p, pn = coords[idx:idx+2]
                #p, pn = coords[idx:idx+2]
                pl = math.sqrt((pn[0] - p[0]) ** 2 + (pn[1] - p[1]) ** 2)
                l += pl
                h = height_start + (height_end - height_start) * (l / way.geom.length)
                #logger.debug("  Distance: %.2f  Height: %.2f", l, h)
                ncoords.append((pn[0], pn[1], h))

            way.geom.coords = ncoords

            way.extra['height_start'] = height_start
            way.extra['height_end'] = height_end

            logger.debug("Transition [height_start=%.1f, height_end=%.1f]: %s", height_start, height_end, way)
    '''

    def get_height_apply_func(self, way):

        def height_apply_func(x, y, z, idx):
            # Find nearest point in path, and return its height
            path = way
            closest_in_path = None  # path.geom.coords[0]
            closest_dist = math.inf
            for idx, p in enumerate(path.geom.coords):
                pd = math.sqrt((x - p[0]) ** 2 + (y - p[1]) ** 2)
                if idx == 0: pd = pd - 20.0
                if idx == len(path.geom.coords) - 1: pd = pd - 20.0
                if pd < closest_dist:
                    closest_in_path = p
                    closest_dist = pd
            # logger.debug("Closest in path: %s", closest_in_path)
            return (x, y, z + (closest_in_path[2] if way.extra['natural'] != "coastline" else 0.0))  #  if len(closest_in_path) > 2 else 0.0

        return height_apply_func

    '''
    def split_way_1d(self, way, coord_idx):
        logger.debug("Splitting %s at %d", way, coord_idx)
        if coord_idx == 0 or coord_idx >= len(way.geom.coords) - 1:
            raise ValueError("Cannot split a path (%s) by the first or last index (%s)." % (way, coord_idx))
        part1 = way.copy()
        part1.geom = LineString(way.geom.coords[:coord_idx + 1])
        part2 = way.copy()
        part2.geom = LineString(way.geom.coords[coord_idx:])

        # Update related ways to point to the new parts
        for connection in way.extra['connections']:
            # Remove old way from every connection
            #print(len(connection.other.extra['connections']))
            connection.other.extra['connections'] = [c for c in connection.other.extra['connections'] if c.other != way]
            #print(len(connection.other.extra['connections']))
            part1.extra['connections'] = [c for c in part1.extra['connections'] if c.other != connection.other]
            part2.extra['connections'] = [c for c in part2.extra['connections'] if c.other != connection.other]

            # Find to which new part it's connected
            for part in (part1, part2):
                if any([(p in list(connection.other.geom.coords)) for p in part.geom.coords]):
                    self.connect_ways_1d(connection.other, part)

        # Update ways
        self.osm.ways_1d.children.remove(way)
        self.osm.ways_1d.children.extend([part1, part2])
    '''

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
        part1.extra['connections'] = []
        part2 = way.copy()
        part2.geom = LineString(way.geom.coords[coord_idx:])
        part2.extra['connections'] = []
        '''
        part1 = DDDObject2(name=way.name + "/1", geom=LineString(way.geom.coords[:coord_idx + 1]), extra=copy.deepcopy(way.extra))
        part1.extra['connections'] = []
        part2 = DDDObject2(name=way.name + "/2", geom=LineString(way.geom.coords[coord_idx:]), extra=copy.deepcopy(way.extra))
        part2.extra['connections'] = []
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
                    if other_con not in way.extra['connections']:
                        way.extra['connections'].append(other_con)
                    way_con = WayConnection(way, other_idx, way_idx)
                    if way_con not in other.extra['connections']:
                        other.extra['connections'].append(way_con)
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

    def road_weight(self, feature):
        """
        Primary roads weight is 1. Lower weights are more important roads.
        """
        highway = feature['properties'].get('highway', None)
        junction = feature['properties'].get('junction', None)

        weight = 99
        if highway == "motorway": weight = 5
        elif highway == "trunk": weight = 10
        elif highway == "primary": weight = 11
        elif highway == "secondary": weight = 12
        elif highway == "tertiary": weight = 13
        elif highway == "service": weight = 21
        elif highway == "living_street": weight = 22
        elif highway == "residential": weight = 23
        elif highway == "steps": weight = 31
        elif highway == "pedestrian": weight = 32
        elif highway == "footway": weight = 33
        elif highway == "path": weight = 34

        if junction == "roundabout": weight = 1

        return weight

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

            join_ways = ddd.group([self.get_way_2d(j.way) for j in intersection])

            # print(join_ways.children)
            join_geoms = join_ways.geom_recursive()
            join_points = []
            join_shapes = []
            # Calculate intersection points as lines
            for i in range(len(join_ways.children)):
                for j in range(i + 1, len(join_ways.children)):
                    shape1 = join_ways.children[i]
                    shape2 = join_ways.children[j]
                    # points = shape1.exterior.intersection(shape2.exterior)
                    # join_points.extend(points)
                    shape = shape1.intersection(shape2).clean(eps=0.01)
                    join_shapes.append(shape)
            # intersection_shape = MultiPoint(join_points).convex_hull
            intersection_shape = ddd.group(join_shapes, empty=2).union().convex_hull()

            # print(intersection_shape)
            if intersection_shape and intersection_shape.geom and intersection_shape.geom.type in ('Polygon', 'MultiPolygon') and not intersection_shape.geom.is_empty:

                # Get intersection way type by vote
                votes = defaultdict(list)
                for join in intersection:
                    votes[join.way.extra['ddd:way:weight']].append(join.way)
                max_voted_ways_weight = list(reversed(sorted(votes.items(), key=lambda w: len(w[1]))))[0][0]
                highest_ways = votes[max_voted_ways_weight]
                highest_way = highest_ways[0]

                '''
                # Createintersection from highest way value from joins
                highest_way = None
                for join in intersection:
                    if highest_way is None or join.way.extra['ddd:way:weight'] < highest_way.extra['ddd:way:weight'] :
                        highest_way = join.way
                '''

                intersection_2d = highest_way.copy(name="Intersection (%s)" % highest_way.name)
                intersection_2d.extra['way_1d'] = highest_way.copy()
                # intersection_2d.extra['way_1d'].geom = ddd.group2(highest_ways).union().geom
                intersection_2d.extra['way_1d'].children = highest_ways

                """
                if ('666643710' in intersection_2d.name):
                    print(intersection_2d.extra)
                    sys.exit(1)
                """

                intersection_2d.extra['connections'] = []
                if len(intersection) > 3:  # 2
                    intersection_2d.extra['ddd:way:lamps'] = False
                    intersection_2d.extra['ddd_trafficlights'] = False
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
            self.osm.ways_2d[int_2d.extra['layer']].children.append(int_2d)

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
        ways_1d = [w for w in self.osm.ways_1d.children if w.extra['layer'] == layer_idx]
        logger.info("Generating 2D ways for layer %s (%d ways)", layer_idx, len(ways_1d))

        ways_1d.sort(key=lambda w: w.extra['ddd:way:weight'])

        ways_2d = defaultdict(list)
        for w in ways_1d:
            f = w.extra['osm:feature']
            way_2d = self.generate_way_2d(w)
            if way_2d:
                weight = self.road_weight(f)
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

        features = [f for f in self.osm.features if int(f['properties'].get('layer', 0)) == layer_idx]

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

        # highway = feature['properties'].get('highway', None)
        # if highway is None: return

        path = way_1d

        width = path.extra['width']
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

    def generate_ways_3d(self):
        for layer_idx in self.osm.layer_indexes:
            self.generate_ways_3d_layer(layer_idx)

        '''
        self.roads_3d_lm1 = self.roads_2d_lm1.extrude(-0.2).translate([0, 0, -5]).material(mat_asphalt)
        self.roads_3d_lm1  = terrain.terrain_geotiff_elevation_apply(self.roads_3d_lm1, self.ddd_proj)

        self.roads_3d_l0 = self.roads_2d_l0.extrude(-0.2).material(mat_asphalt)
        self.roads_3d_l0  = terrain.terrain_geotiff_elevation_apply(self.roads_3d_l0, self.ddd_proj)

        self.roads_3d_l1 = self.roads_2d_l1.extrude(-0.2).translate([0, 0, 6]).material(mat_asphalt)
        self.roads_3d_l1  = terrain.terrain_geotiff_elevation_apply(self.roads_3d_l1, self.ddd_proj)

        self.generate_transitions_lm1_l0()
        self.generate_transitions_l0_l1()

        '''
        self.generate_ways_3d_subways()
        self.generate_ways_3d_elevated()

    def generate_ways_3d_intersections(self):
        pass

    def generate_ways_3d_layer(self, layer_idx):
        '''
        - Sorts ways (more important first),
        - Generates 2D shapes
        - Resolve intersections
        - Add metadata (road name, surface type, connections?)
        - Consider elevation and level roads on the transversal axis
        '''
        ways_2d = self.osm.ways_2d[layer_idx]
        logger.info("Generating 3D ways for layer %s: %s", layer_idx, ways_2d)

        ways_3d = []
        for way_2d in ways_2d.children:
            # if way_2d.extra['natural'] == "coastline": continue
            #layer_height = self.layer_height(layer_idx)
            try:
                if way_2d.extra['railway']:
                    way_3d = self.generate_way_3d_railway(way_2d)
                else:
                    way_3d = self.generate_way_3d_common(way_2d)

                way_3d.extra['way_2d'] = way_2d
                way_3d = terrain.terrain_geotiff_elevation_apply(way_3d, self.osm.ddd_proj)
                ways_3d.append(way_3d)

            except ValueError as e:
                logger.error("Could not generate 3D way: %s", e)
            except IndexError as e:
                logger.error("Could not generate 3D way: %s", e)

        ways_3d = ddd.group(ways_3d, empty=3)

        nways = []
        for way in ways_3d.children:
            # logger.debug("3D layer transition: %s", way)
            # if way.extra['layer_transition']:
            if 'way_1d' in way.extra['way_2d'].extra:
                path = way.extra['way_2d'].extra['way_1d']
                vertex_func = self.get_height_apply_func(path)
                nway = way.vertex_func(vertex_func)
            else:
                nway = way.translate([0, 0, self.layer_height(way.extra['layer'])])
            nways.append(nway)

        self.osm.ways_3d[layer_idx] = ddd.group(nways, empty=3, name="Ways (%s)" % layer_idx)

    def generate_way_3d_common(self, way_2d):
        '''
        '''

        way_2d = way_2d.individualize()

        extra_height = way_2d.extra['extra_height']
        if extra_height:
            try:
                way_3d = way_2d.extrude(-0.2 - extra_height).translate([0, 0, extra_height])  # + layer_height
            except DDDException as e:
                logger.error("Could not extrude (1st try) way %s: %s", way_2d, e)
                way_2d = way_2d.clean(eps=0.001)
                way_3d = way_2d.extrude(-0.2 - extra_height).translate([0, 0, extra_height])  # + layer_height

            way_3d = ddd.uv.map_cubic(way_3d)
        else:
            way_3d = way_2d.triangulate()  # + layer_height
            way_3d = ddd.uv.map_cubic(way_3d)
        if way_2d.extra['natural'] == "coastline": way_3d = way_3d.translate([0, 0, -5 + 0.3])  # FIXME: hacks coastline wall with extra_height
        return way_3d

    def generate_way_3d_railway(self, way_2d):
        '''
        '''
        rail_height = 0.30
        way_2d = way_2d.individualize()
        way_2d_interior = way_2d.buffer(-0.3).individualize()
        #way_3d = way_2d.extrude(-0.2 - extra_height).translate([0, 0, extra_height])  # + layer_height
        way_3d = way_2d.extrude_step(way_2d_interior, rail_height, base=False, cap=False)
        way_3d = way_3d.material(ddd.mats.dirt)
        way_3d = ddd.uv.map_cubic(way_3d)

        pathline = way_2d_interior.extra['way_1d'].copy()
        way_2d_interior = uvmapping.map_2d_path(way_2d_interior, pathline, line_x_offset=0.5, line_x_width=0.5)
        railroad_3d = way_2d_interior.triangulate().translate([0, 0, rail_height]).material(ddd.mats.railway)
        railroad_3d.extra['ddd:collider'] = False
        railroad_3d.extra['ddd:shadows'] = False
        try:
            uvmapping.map_3d_from_2d(railroad_3d, way_2d_interior)
        except Exception as e:
            logger.error("Could not map railway UV coordinates: %s", e)
            railroad_3d.extra['uv'] = None

        return ddd.group3([way_3d, railroad_3d])

    def generate_ways_3d_subways(self):
        """
        Generates boxing for sub ways.
        """
        logger.info("Generating subways.")
        logger.warn("IMPLEMENT 2D/3D separation for this, as it needs to be cropped, and it's being already cropped earlier")

        # Take roads
        ways = [w for w in self.osm.ways_2d["-1a"].children] + [w for w in self.osm.ways_2d["-1"].children]

        union = self.osm.ways_2d["-1"].union()
        union_with_transitions = ddd.group(ways, empty="2").union()
        union_sidewalks = union_with_transitions.buffer(0.6, cap_style=2, join_style=2)

        sidewalks_2d = union_sidewalks.subtract(union_with_transitions)  # we include transitions
        walls_2d = sidewalks_2d.buffer(0.5, cap_style=2, join_style=2).subtract(union_sidewalks)
        floors_2d = union_sidewalks.copy()
        ceilings_2d = union.buffer(0.6, cap_style=2, join_style=2).subtract(self.osm.ways_2d["-1a"])

        # FIXME: Move cropping to generic site, use itermediate osm.something for storage
        crop = ddd.shape(self.osm.area_crop)
        sidewalks_2d = sidewalks_2d.intersection(crop)
        walls_2d = walls_2d.intersection(crop)
        floors_2d = floors_2d.intersection(crop)
        ceilings_2d = ceilings_2d.intersection(crop)

        sidewalks_3d = sidewalks_2d.extrude(0.3).translate([0, 0, -5]).material(ddd.mats.sidewalk)
        walls_3d = walls_2d.extrude(5).translate([0, 0, -5]).material(ddd.mats.cement)
        #floors_3d = floors_2d.extrude(-0.3).translate([0, 0, -5]).material(ddd.mats.sidewalk)
        floors_3d = floors_2d.triangulate().translate([0, 0, -5]).material(ddd.mats.sidewalk)
        ceilings_3d = ceilings_2d.extrude(0.5).translate([0, 0, -1.0]).material(ddd.mats.cement)

        sidewalks_3d = terrain.terrain_geotiff_elevation_apply(sidewalks_3d, self.osm.ddd_proj)
        sidewalks_3d = ddd.uv.map_cubic(sidewalks_3d)
        walls_3d = terrain.terrain_geotiff_elevation_apply(walls_3d, self.osm.ddd_proj)
        walls_3d = ddd.uv.map_cubic(walls_3d)
        floors_3d = terrain.terrain_geotiff_elevation_apply(floors_3d, self.osm.ddd_proj)
        ceilings_3d = terrain.terrain_geotiff_elevation_apply(ceilings_3d, self.osm.ddd_proj)
        ceilings_3d = ddd.uv.map_cubic(ceilings_3d)

        subway = ddd.group([sidewalks_3d, walls_3d, floors_3d, ceilings_3d], empty=3).translate([0, 0, -0.2])
        self.osm.other_3d.children.append(subway)

    def generate_ways_3d_elevated(self):

        logger.info("Generating elevated ways.")
        logger.warn("IMPLEMENT 2D/3D separation for this, as it needs to be cropped")

        elevated = []

        # Walk roads
        ways = ([w for w in self.osm.ways_2d["1"].children] +
                [w for w in self.osm.ways_2d["0a"].children] +
                [w for w in self.osm.ways_2d["-1a"].children])
        # ways_union = ddd.group(ways).union()

        sidewalk_width = 0.4

        elevated_union = DDDObject2()
        for way in ways:
            # way_longer = way.buffer(0.3, cap_style=1, join_style=2)

            if 'intersection' in way.extra: continue

            way_with_sidewalk_2d = way.buffer(sidewalk_width, cap_style=2, join_style=2)
            #way_with_sidewalk_2d_extended = osmops.extend_way(way).buffer(sidewalk_width, cap_style=2, join_style=2)
            sidewalk_2d = way_with_sidewalk_2d.subtract(way).material(ddd.mats.sidewalk)
            wall_2d = way_with_sidewalk_2d.buffer(0.25, cap_style=2, join_style=2).subtract(way_with_sidewalk_2d).buffer(0.001, cap_style=2, join_style=2).material(ddd.mats.cement)
            floor_2d = way_with_sidewalk_2d.buffer(0.3, cap_style=2, join_style=2).buffer(0.001, cap_style=2, join_style=2).material(ddd.mats.cement)

            sidewalk_2d.extra['way_2d'] = way
            wall_2d.extra['way_2d'] = way
            floor_2d.extra['way_2d'] = way

            # Get connected ways
            connected = self.follow_way(way.extra['way_1d'], 1)
            connected_2d = ddd.group([self.get_way_2d(c) for c in connected])
            if 'intersection_start_2d' in way.extra['way_1d'].extra:
                connected_2d.append(way.extra['way_1d'].extra['intersection_start_2d'])
            if 'intersection_end_2d' in way.extra['way_1d'].extra:
                connected_2d.append(way.extra['way_1d'].extra['intersection_end_2d'])
            # print(connected)

            sidewalk_2d = sidewalk_2d.subtract(connected_2d).buffer(0.001)
            wall_2d = wall_2d.subtract(connected_2d.buffer(sidewalk_width))
            # TODO: Subtract floors from connected or resolve intersections
            wall_2d = wall_2d.subtract(elevated_union)

            # FIXME: Move cropping to generic site, use itermediate osm.something for storage
            crop = ddd.shape(self.osm.area_crop)
            sidewalk_2d = sidewalk_2d.intersection(crop.buffer(-0.003)).clean(eps=0.01)
            wall_2d = wall_2d.intersection(crop.buffer(-0.003)).clean(eps=0.01)
            floor_2d = floor_2d.intersection(crop.buffer(-0.003)).clean(eps=0.01)

            # ddd.group((sidewalk_2d, wall_2d)).show()
            elevated.append((sidewalk_2d, wall_2d, floor_2d))
            elevated_union = elevated_union.union(ddd.group([sidewalk_2d, wall_2d, floor_2d]))

            # Bridge piers
            path = way.extra['way_1d']
            if path.geom.length > 15.0:  # and path.extra['ddd:bridge:posts']:
                # Generate posts
                interval = 35.0
                length = path.geom.length
                numposts = int(length / interval)
                idx = 0

                logger.debug("Piers for bridge (length=%s, num=%d, way=%s)", length, numposts, way)
                for d in numpy.linspace(0.0, length, numposts, endpoint=False):
                    if d == 0.0: continue

                    # Calculate left and right perpendicular intersections with sidewalk, park, land...
                    p, segment_idx, segment_coords_a, segment_coords_b = path.interpolate_segment(d)

                    # FIXME: Use items and crop in a generic way (same for subways) (so ignore below in common etc)
                    if not self.osm.area_crop.contains(ddd.point(p).geom):
                        continue

                    dir_vec = (segment_coords_b[0] - segment_coords_a[0], segment_coords_b[1] - segment_coords_a[1])
                    dir_vec_length = math.sqrt(dir_vec[0] ** 2 + dir_vec[1] ** 2)
                    dir_vec = (dir_vec[0] / dir_vec_length, dir_vec[1] / dir_vec_length)
                    angle = math.atan2(dir_vec[1], dir_vec[0])

                    idx = idx + 1

                    if len(p) < 3:
                        logger.error("Bridge path with less than 3 components when building bridge piers.")
                        continue

                    if p[2] > 1.0:  # If no height, no pilar, but should be a margin and also corrected by base_height
                        item = ddd.rect([-way.extra['width'] * 0.3, -0.5, way.extra['width'] * 0.3, 0.5], name="Bridge Post %s" % way.name)
                        item = item.extrude(-(math.fabs(p[2]) - 0.5)).material(ddd.mats.cement)
                        item = item.rotate([0, 0, angle - math.pi / 2]).translate([p[0], p[1], 0])
                        vertex_func = self.get_height_apply_func(path)
                        item = item.vertex_func(vertex_func)
                        item = terrain.terrain_geotiff_elevation_apply(item, self.osm.ddd_proj)
                        item = item.translate([0, 0, -0.8])
                        item.extra['way_2d'] = way
                        item.extra['ddd:bridge:post'] = True
                        self.osm.other_3d.children.append(item)

        elevated_3d = []
        for item in elevated:
            sidewalk_2d, wall_2d, floor_2d = item
            sidewalk_3d = sidewalk_2d.extrude(0.2).translate([0, 0, -0.2])
            wall_3d = wall_2d.extrude(0.6)
            floor_3d = floor_2d.extrude(-0.5).translate([0, 0, -0.2])
            # extra_height = way_2d.extra['extra_height']
            # way_3d = way_2d.extrude(-0.2 - extra_height).translate([0, 0, extra_height])  # + layer_height

            elevated_3d.append(sidewalk_3d)
            elevated_3d.append(wall_3d)
            elevated_3d.append(floor_3d)

        # Raise items to their way height position
        nitems = []
        for item in elevated_3d:
            # print(item.extra)
            path = item.extra['way_1d']
            vertex_func = self.get_height_apply_func(path)
            nitem = item.vertex_func(vertex_func)
            nitems.append(nitem)

        result = ddd.group(nitems, empty=3)
        result = terrain.terrain_geotiff_elevation_apply(result, self.osm.ddd_proj)
        self.osm.other_3d.children.append(result)

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
                pass

    def generate_props_2d_way(self, way_2d):

        if 'way_1d' not in way_2d.extra:
            # May be an intersection, should generate roadlines too
            return

        path = way_2d.extra['way_1d']

        # print(path.geom.type)
        # if path.geom.type != "LineString": return
        length = path.geom.length

        # Generate lines
        if way_2d.extra['ddd:way:roadlines']:

            lanes = path.extra['lanes']
            numlines = lanes - 1 + 2
            for lineind in range(numlines):

                width = path.extra['ddd:width']
                lane_width = path.extra['ddd:way:lane_width']  # lanes_width / lanes
                lane_width_left = path.extra['ddd:way:lane_width_left']
                lane_width_right = path.extra['ddd:way:lane_width_right']

                line_continuous = False
                if lineind in [0, numlines - 1]: line_continuous = True
                if lanes > 2 and lineind == int(numlines / 2) and not path.extra.get('oneway', False): line_continuous = True
                line_x_offset = 0.076171875 if line_continuous else 0.5

                line_0_distance = -(width / 2) + lane_width_left
                line_distance = line_0_distance + lane_width * lineind

                # Create line
                pathline = path.copy()
                if abs(line_distance) > 0.01:
                    pathline.geom = pathline.geom.parallel_offset(line_distance, "left", resolution=2)
                line = pathline.buffer(0.15).material(ddd.mats.roadline)
                line.extra['way_1d'] = pathline

                # FIXME: Move cropping to generic site, use itermediate osm.something for storage
                # Also, cropping shall interpolate UVs
                crop = ddd.shape(self.osm.area_crop)
                line = line.intersection(crop)
                line = line.intersection(way_2d)
                line = line.individualize()

                # if line.geom and not line.geom.is_empty:
                # try:
                uvmapping.map_2d_path(line, pathline, line_x_offset / 0.05)

                # except Exception as e:
                #    logger.error("Could not UV map Way 2D from path: %s %s %s: %s", line, line.geom, pathline.geom, e)
                #    continue
                line_3d = line.triangulate().translate([0, 0, 0.05])  # Temporary hack until fitting lines properly
                vertex_func = self.get_height_apply_func(path)
                line_3d = line_3d.vertex_func(vertex_func)
                line_3d = terrain.terrain_geotiff_elevation_apply(line_3d, self.osm.ddd_proj)
                line_3d.extra['ddd:collider'] = False
                line_3d.extra['ddd:shadows'] = False
                # print(line)
                # print(line.geom)
                uvmapping.map_3d_from_2d(line_3d, line)
                # uvmapping.map_2d_path(line_3d, path)

                self.osm.roadlines_3d.children.append(line_3d)

        # Check if to generate lamps
        if path.extra['ddd:way:lamps'] and path.extra['layer'] == "0":

            # Generate lamp posts
            interval = 25.0
            numlamps = int(length / interval)
            idx = 0
            idx_offset = random.choice([0, 1])

            # Ignore if street is short
            if numlamps == 0: return

            logger.debug("Props for way (length=%s, num=%d, way=%s)", length, numlamps, way_2d)
            for d in numpy.linspace(0.0, length, numlamps, endpoint=False):
                if d == 0.0: continue

                # Calculate left and right perpendicular intersections with sidewalk, park, land...
                # point = path.geom.interpolate(d)
                p, segment_idx, segment_coords_a, segment_coords_b = path.interpolate_segment(d)
                # logger.error("Could not generate props for way %s: %s", way_2d, e)
                # print(d, p, segment_idx, segment_coords_a, segment_coords_b)

                # segment = ddd.line([segment_coords_a, segment_coords_b])
                dir_vec = (segment_coords_b[0] - segment_coords_a[0], segment_coords_b[1] - segment_coords_a[1])
                dir_vec_length = math.sqrt(dir_vec[0] ** 2 + dir_vec[1] ** 2)
                dir_vec = (dir_vec[0] / dir_vec_length, dir_vec[1] / dir_vec_length)
                perpendicular_vec = (-dir_vec[1], dir_vec[0])
                lightlamp_dist = path.extra['width'] * 0.5 + 0.5
                left = (p[0] + perpendicular_vec[0] * lightlamp_dist, p[1] + perpendicular_vec[1] * lightlamp_dist)
                right = (p[0] - perpendicular_vec[0] * lightlamp_dist, p[1] - perpendicular_vec[1] * lightlamp_dist)

                alternate_lampposts = True
                if alternate_lampposts:
                    points = [left] if (idx + idx_offset) % 2 == 0 else [right]
                else:
                    points = left, right

                for point in points:
                    idx = idx + 1
                    item = ddd.point(point, name="LampPost %s" % way_2d.name)

                    # area = self.osm.areas_2d.intersect(item)
                    # Check type of area point is on

                    item.extra['way_2d'] = way_2d
                    item.extra['ddd_osm'] = 'way_lamppost'
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
                #lightlamp_dist = path.extra['width'] * 0.5 + 0.5
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

        # Generate trafficlights
        if path.geom.length > 45.0 and path.extra['ddd_trafficlights'] and path.extra['layer'] == "0":

            # End right
            p, segment_idx, segment_coords_a, segment_coords_b = path.interpolate_segment(path.geom.length - 10.0)
            dir_vec = (segment_coords_b[0] - segment_coords_a[0], segment_coords_b[1] - segment_coords_a[1])
            dir_vec_length = math.sqrt(dir_vec[0] ** 2 + dir_vec[1] ** 2)
            dir_vec = (dir_vec[0] / dir_vec_length, dir_vec[1] / dir_vec_length)
            perpendicular_vec = (-dir_vec[1], dir_vec[0])
            lightlamp_dist = path.extra['width'] * 0.5 + 0.5
            left = (p[0] + perpendicular_vec[0] * lightlamp_dist, p[1] + perpendicular_vec[1] * lightlamp_dist)
            right = (p[0] - perpendicular_vec[0] * lightlamp_dist, p[1] - perpendicular_vec[1] * lightlamp_dist)

            item = ddd.point(right, name="Traffic Lights %s" % way_2d.name)

            angle = math.atan2(dir_vec[1], dir_vec[0])

            # area = self.osm.areas_2d.intersect(item)
            # Check type of area point is on
            item.extra['way_2d'] = way_2d
            item.extra['ddd_osm'] = 'way_trafficlights'
            item.extra['ddd:angle'] = angle
            self.osm.items_1d.children.append(item)
