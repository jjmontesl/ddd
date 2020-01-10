# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

from collections import defaultdict, namedtuple
import logging
import math
import random
import sys

from csg import geom as csggeom
from csg.core import CSG
import geojson
import noise
import pyproj
from shapely import geometry
from shapely.geometry import shape
from shapely.geometry.geo import shape
from shapely.ops import transform

from ddd.ddd import DDDObject2, DDDObject3
from ddd.ddd import ddd
from ddd.pack.sketchy import terrain, plants, urban
from trimesh import creation, primitives, boolean
import trimesh
from trimesh.base import Trimesh
from trimesh.path import segments
from trimesh.path.path import Path
from trimesh.scene.scene import Scene, append_scenes
from trimesh.visual.material import SimpleMaterial
from shapely.geometry.linestring import LineString
from ddd.osm.buildings import BuildingOSMBuilder
import numpy


# Get instance of logger for this module
logger = logging.getLogger(__name__)

WayConnection = namedtuple("WayConnection", "other self_idx other_idx")


class WaysOSMBuilder():

    def __init__(self, osmbuilder):

        self.osm = osmbuilder

    def generate_ways_1d(self):

        # Generate paths
        logger.info("Generating 1D way path objects.")
        ways = []
        for feature in self.osm.features:
            if feature['geometry']['type'] != 'LineString': continue
            way = self.generate_way_1d(feature)
            if way:
                way.extra['connections'] = []
                ways.append(way)

        self.osm.ways_1d = ddd.group(ways)

        # Find connections
        # TODO: this shall possibly come from OSM relations (or maybe not, or optional)
        logger.info("Resolving connections between ways (%d ways).", len(ways))
        vertex_cache = defaultdict(list)
        for way in self.osm.ways_1d.children:
            #start = way.geom.coords[0]
            #end = way.geom.coords[-1]
            for way_idx, c in enumerate(way.geom.coords):
                if c in vertex_cache:
                    for other in vertex_cache[c]:
                        if other == way: continue
                        self.connect_ways_1d(way, other)  #, way_idx)

                if way not in vertex_cache[c]:
                    vertex_cache[c].append(way)

        # Divide end-to-middle connections
        logger.info("Ways before splitting mid connections: %d", len(self.osm.ways_1d.children))
        split = True
        while split:
            split = False
            for way in self.osm.ways_1d.children:
                for other, way_idx, other_idx in way.extra['connections']:
                    if other.extra['layer'] == way.extra['layer']: continue
                    if (other_idx > 0 and other_idx != len(other.geom.coords) - 1):
                        #if not way.extra['layer_transition']: continue
                        #logger.info("Mid point connection: %s <-> %s", way, other)
                        self.split_way_1d(other, other_idx)
                        # Restart after each split
                        split = True
                    if split: break
                if split: break
        logger.debug("Ways after splitting mid connections: %d", len(self.osm.ways_1d.children))

        # Find transitions between more than one layer (ie tunnel to bridge) and split
        for way in self.osm.ways_1d.children:
            way.extra['layer_transition'] = False
            way.extra['layer_int'] = int(way.extra['layer'])
            way.extra['layer_min'] = int(way.extra['layer'])
            way.extra['layer_max'] = int(way.extra['layer'])
            #way.extra['layer_height'] = self.layer_height(str(way.extra['layer_min']))

        # Search transitions between layers
        for way in self.osm.ways_1d.children:
            for other, way_idx, other_idx in way.extra['connections']:
                way.extra['layer_min'] = min(way.extra['layer_min'], int(other.extra['layer_int']))
                way.extra['layer_max'] = max(way.extra['layer_max'], int(other.extra['layer_int']))

                # Hack, we should follow paths and propagate heights
                if other.extra['layer_int'] == way.extra['layer_max']:
                    way.extra['layer_dir_up'] = 1 if (way_idx == 0) else -1
                else:
                    way.extra['layer_dir_up'] = -1 if (way_idx == 0) else 1

            if way.extra['layer_min'] != way.extra['layer_max'] and way.extra['layer_int'] == 0:
                #logger.debug("Layer transition (%s <-> %s): %s <-> %s", way.extra['layer_min'],other.extra['layer_max'], way, other)
                way.extra['layer_transition'] = True
                way.extra['layer'] = str(way.extra['layer_min']) + "a"

        # Propagate height across connections for transitions
        self.generate_ways_1d_heights()

        # Propagate height beyond transition layers if gradient is too large?!

        # Soften / subdivide roads if height angle is larger than X (try as alternative to massive subdivision of roads?)

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

    def get_height_apply_func(self, way):
        def height_apply_func(x, y, z, idx):
            # Find nearest point in path, and return its height
            path = way
            closest_in_path = path.geom.coords[0]
            closest_dist = math.inf
            for idx, p in enumerate(path.geom.coords):
                pd = math.sqrt((x - p[0]) ** 2 + (y - p[1]) ** 2)
                if idx == 0: pd = pd - 20.0
                if idx == len(path.geom.coords) - 1: pd = pd - 20.0
                if pd < closest_dist:
                    closest_in_path = p
                    closest_dist = pd
            #logger.debug("Closest in path: %s", closest_in_path)
            return (x, y, z + closest_in_path[2])
        return height_apply_func

    def split_way_1d(self, way, coord_idx):
        if coord_idx == 0 or coord_idx >= len(way.geom.coords):
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

    def connect_ways_1d(self, way, other):
        #other_idx = 0 if r_start in (start, end) else -1
        if other in way.extra['connections'] or way in other.extra['connections']: return

        #other_idx = list(other.geom.coords).index(way.geom.coords[way_idx])
        found = False
        for way_idx, wc in enumerate(way.geom.coords):
            for other_idx, oc in enumerate(other.geom.coords):
                if wc == oc:
                    found = True
                    break
            if found: break

        if not found:
            raise ValueError("Cannot find vertex index by which two paths are connected.")

        #logger.debug("Way connection: %s (idx: %d) <-> %s (idx: %d)", way, way_idx, other, other_idx)
        if not other in way.extra['connections']:
            way.extra['connections'].append(WayConnection(other, way_idx, other_idx))
        if not way in other.extra['connections']:
            other.extra['connections'].append(WayConnection(way, other_idx, way_idx))

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

    def generate_way_1d(self, feature):

        highway = feature['properties'].get('highway', None)
        barrier = feature['properties'].get('barrier', None)
        railway = feature['properties'].get('railway', None)
        historic = feature['properties'].get('historic', None)
        natural = feature['properties'].get('natural', None)
        man_made = feature['properties'].get('man_made', None)
        path = ddd.shape(feature['geometry'])
        #path.geom = path.geom.simplify(tolerance=self.simplify_tolerance)

        width = None  # if not set will be discarded
        material = self.osm.mat_asphalt
        extra_height = 0.0
        lanes = None
        lamps = False
        if highway == "motorway":
            lanes = 2.4
            width = (lanes * 3.30)
        elif highway == "primary":
            lanes = 2.2
            width = (lanes * 3.30)
        elif highway == "primary_link":
            lanes = 2.0
            width = (lanes * 3.30)
        elif highway == "secondary":
            lanes = 2.1
            width = (lanes * 3.30)
            lamps = True
        elif highway == "tertiary":
            lanes = 2.0
            width = (lanes * 3.30)
            lamps = True  # shall be only in city?
        elif highway == "service":
            lanes = 1.0
            width = (lanes * 3.30)
            lamps = True  # shall be only in city?
        elif highway in ("residential", "living_street"):
            #lanes = 1.0  # Using 1 lane for residential/living causes too small roads
            extra_height = 0.1
            lanes = 2.0
            width = (lanes * 3.30)
            lamps = True  # shall be only in city?
        elif highway in ("footway", "path"):
            lanes = 0.6
            material = self.osm.mat_dirt
            extra_height = 0.2
            width = (lanes * 3.30)
        elif highway in ("steps", "stairs"):
            lanes = 0.6
            material = self.osm.mat_pathwalk
            extra_height = 0.2
            width = (lanes * 3.30)
        elif highway == "pedestrian":
            lanes = 2.0
            material = self.osm.mat_pathwalk
            extra_height = 0.2
            width = (lanes * 3.30)
            lamps = True  # shall be only in city?
        elif highway == "cycleway":
            lanes = 0.6
            material = self.osm.mat_sidewalk
            extra_height = 0.2
            width = (lanes * 3.30)
        elif highway == "unclassified":
            lanes = 1.2
            material = self.osm.mat_dirt
            #extra_height = 0.2
            width = (lanes * 3.30)

        elif natural == "coastline":
            lanes = None
            width = 0.5
            material = self.osm.mat_sea

        elif railway:
            lanes = None
            width = 0.6
            material = self.osm.mat_railway
            extra_height = 0.5

        elif barrier == 'city_wall':
            width = 1.0
            material = self.osm.mat_stone
            extra_height = 2.0
        elif historic == 'castle_wall':
            width = 3.0
            material = self.osm.mat_stone
            extra_height = 3.5

        # Fixme: do a proper hedge, do not use ways/areas for everything
        elif barrier == 'hedge':
            width = 0.6
            material = self.osm.mat_leaves
            extra_height = 1.2

        elif man_made == 'pier':
            width = 1.8
            material = self.osm.mat_wood

        elif barrier == 'retaining_wall':
            width = 1.0
            material = self.osm.mat_stone
            extra_height = 1.5
        elif barrier == 'wall':
            # TODO: Get height and material from metadata
            width = 0.4
            material = self.osm.mat_brick
            extra_height = 1.8

        else:
            if highway and width is None:
                logger.warn("Unknown highway type: %s (%s)", highway, feature['properties'])
                lanes = 2.0
                width = (lanes * 3.30)
            else:
                logger.warn("Unknown way (discarding): %s", feature['properties'])
                return None

        flanes = feature['properties'].get('lanes', None)
        if flanes:
            lanes = float(flanes)
            width = (lanes * 3.30)

        path = path.material(material)
        path.name = "Way: %s" % (feature['properties'].get('name', None))
        path.extra['highway'] = highway
        path.extra['barrier'] = barrier
        path.extra['railway'] = railway
        path.extra['historic'] = historic
        path.extra['feature'] = feature
        path.extra['width'] = width
        path.extra['lanes'] = lanes
        path.extra['layer'] = feature['properties']['layer']
        path.extra['extra_height'] = extra_height
        path.extra['ddd_lamps'] = lamps
        #print(feature['properties'].get("name", None))

        return path

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

        weight = 2
        if highway == "motorway": weight = 5
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
        else: weight = 99

        if junction == "roundabout": weight = 1

        return weight

    def generate_ways_2d(self):
        for layer_idx in self.osm.layer_indexes:
            self.generate_ways_2d_layer(layer_idx)

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

        ways_1d.sort(key=lambda w: self.road_weight(w.extra['feature']))

        ways_2d = defaultdict(list)
        for w in ways_1d:
            f = w.extra['feature']
            way_2d = self.generate_way_2d(w)
            weight = self.road_weight(f)
            if way_2d:
                ways_2d[weight].append(way_2d)

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

        roads = sum(ways_2d.values(), [])
        if roads:
            roads = ddd.group(roads, name="Ways (layer: %s)" % layer_idx)  #translate([0, 0, 50])
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

        feature = way_1d.extra['feature']

        #highway = feature['properties'].get('highway', None)
        #if highway is None: return

        path = way_1d

        width = path.extra['width']
        road_2d = path.buffer(distance=width / 2.0, cap_style=2, join_style=2)

        # Avoid gaps and eliminate small polygons
        #path = path.buffer(distance=0.05)
        if width > 2.0:
            road_2d = road_2d.buffer(distance=1.0, cap_style=2, join_style=2)
            road_2d = road_2d.buffer(distance=-1.0, cap_style=2, join_style=2)
            road_2d = road_2d.buffer(distance=0.1, cap_style=2, join_style=2)
            #road_2d = road_2d.simplify(0.5)

        #print(feature['properties'].get("name", None))
        #road_2d.extra['feature'] = feature
        road_2d.extra['path'] = path
        road_2d.extra['way_1d'] = path

        road_2d.name = "Way: %s" % (feature['properties'].get('name', None))
        return road_2d

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

        self.generate_subways()
        self.generate_elevated_ways()
        '''

    def layer_height(self, layer_idx):
        return self.osm.layer_heights[layer_idx]

    def generate_ways_3d_layer(self, layer_idx):
        '''
        - Sorts ways (more important first),
        - Generates 2D shapes
        - Resolve intersections
        - Add metadata (road name, surface type, connections?)
        - Consider elevation and level roads on the transversal axis
        '''
        ways_2d = self.osm.ways_2d[layer_idx]
        layer_height = self.layer_height(layer_idx)
        logger.info("Generating 3D ways for layer %s: %s", layer_idx, ways_2d)

        ways_3d = []
        for way_2d in ways_2d.children:
            extra_height = way_2d.extra['extra_height']
            way_3d = way_2d.extrude(-0.2 - extra_height).translate([0, 0, layer_height + extra_height])
            way_3d = terrain.terrain_geotiff_elevation_apply(way_3d, self.osm.ddd_proj)
            way_3d.extra['way_2d'] = way_2d
            ways_3d.append(way_3d)
        ways_3d = ddd.group(ways_3d) if ways_3d else DDDObject3()

        #ways_3d = ways_2d.extrude(-(0.2)).translate([0, 0, layer_height])
        #ways_3d = terrain.terrain_geotiff_elevation_apply(ways_3d, self.osm.ddd_proj)

        #if layer_idx.endswith('a'):
        #    ways_3d = ways_3d.material(mat_highlight)

        for way in ways_3d.children:
            if way.extra['layer_transition']:
                #logger.debug("3D layer transition: %s", way)
                path = way.extra['way_2d'].extra['way_1d']
                vertex_func = self.get_height_apply_func(path)
                way.mesh = way.vertex_func(vertex_func).mesh

        self.osm.ways_3d[layer_idx] = ways_3d

    def generate_subways(self):
        """
        Generates boxing for sub ways.
        """
        logger.info("Generating subways.")

        # Take roads
        union = self.roads_2d_lm1.children[0]
        for r in self.roads_2d_lm1.children[1:]:
            union = union.union(r)

        # Find transit roads
        roads_2d_transition_lm1_l0 = [r for r in self.roads_2d_l0.children if r.extra.get('transition_lm1', False) is True]
        roads_2d_transition_lm1_l1 = [r for r in self.roads_2d_l1.children if r.extra.get('transition_lm1', False) is True]


        transitions = DDDObject2()
        for r in roads_2d_transition_lm1_l0 + roads_2d_transition_lm1_l1:
            transitions = transitions.union(r)

        union_with_transitions = union.union(transitions)

        union_sidewalks = union_with_transitions.buffer(0.6, cap_style=2, join_style=2)

        self.sidewalks_2d_lm1 = union_sidewalks.subtract(union)
        self.walls_2d_lm1 = self.sidewalks_2d_lm1.buffer(0.5, cap_style=2, join_style=2).subtract(union_sidewalks)

        self.sidewalks_3d_lm1 = self.sidewalks_2d_lm1.extrude(0.3).translate([0, 0, -5]).material(mat_sidewalk)
        self.walls_3d_lm1 = self.walls_2d_lm1.extrude(5).translate([0, 0, -5])
        self.ceiling_3d_lm1 = union.buffer(0.6 + 0.5).extrude(0.3).subtract(transitions).translate([0, 0, -0.3]).material(mat_sidewalk)

        self.sidewalks_3d_lm1  = terrain.terrain_geotiff_elevation_apply(self.sidewalks_3d_lm1, self.ddd_proj)
        self.walls_3d_lm1  = terrain.terrain_geotiff_elevation_apply(self.walls_3d_lm1, self.ddd_proj)
        self.ceiling_3d_lm1 = terrain.terrain_geotiff_elevation_apply(self.ceiling_3d_lm1, self.ddd_proj)

    def generate_elevated_ways(self):

        logger.info("Generating elevated ways.")

        # Take roads
        union = self.roads_2d_l1.children[0]
        for r in self.roads_2d_l1.children[1:]:
            union = union.union(r)

        # Find transit roads
        roads_2d_transition_l1_l0 = [r for r in self.roads_2d_l0.children if r.extra.get('transition_l1', False) is True and r.extra.get('transition_lm1', False) is False]

        transitions = DDDObject2()
        for r in roads_2d_transition_l1_l0:
            transitions = transitions.union(r)

        union_with_transitions = union.union(transitions)

        union_sidewalks = union.buffer(0.3, cap_style=2, join_style=2)

        self.sidewalks_2d_l1 = union_sidewalks.subtract(union_with_transitions)

        # Create elevated walls (need to remove start and end caps.
        union_l0 = DDDObject2().union(self.roads_2d_l0).buffer(0.5, cap_style=2, join_style=2)
        self.walls_2d_l1 = union_sidewalks.buffer(0.2, cap_style=2, join_style=2).subtract(union_sidewalks).subtract(union_with_transitions)

        self.sidewalks_3d_l1 = self.sidewalks_2d_l1.extrude(0.3).translate([0, 0, 6]).material(mat_sidewalk)

        self.walls_3d_l1 = self.walls_2d_l1.extrude(0.85).translate([0, 0, 6])

        self.floor_3d_l1 = union.buffer(0.3 + 0.2).extrude(0.3).translate([0, 0, 6 - 0.3 - 0.2]).material(mat_sidewalk)

        #self.walls_3d_l1 = self._apply_path_height(self.walls_3d_l1)

        # Hack floor
        #floor_3d_hack_ground = transitions.extrude(0.3).material(mat_terrain)
        #self.floor_3d_l1 = ddd.group([self.floor_3d_l1, floor_3d_hack_ground])

        self.sidewalks_3d_l1  = terrain.terrain_geotiff_elevation_apply(self.sidewalks_3d_l1, self.ddd_proj)
        self.walls_3d_l1  = terrain.terrain_geotiff_elevation_apply(self.walls_3d_l1, self.ddd_proj)
        self.floor_3d_l1  = terrain.terrain_geotiff_elevation_apply(self.floor_3d_l1, self.ddd_proj)


    '''
    def generate_transitions_lm1_l0(self):

        logger.info("Processing road layer connections (tunnels to ground).")
        # FIXME: this shall be done in preprocessing and account for shared nodes inside geoms
        # (not only start/finish)


        # Transitions from tunnel to ground
        for r in self.roads_2d_lm1.children:
            #print(r.extra['feature'])
            connecteds = self.find_connected_ways(r, ddd.group(self.roads_2d_l0.children + self.roads_2d_l1.children))
            if connecteds:

                hstart = -5.0
                hend = 0.0

                for connected, road_con_idx, link_con_idx in connecteds:

                    for subcon, _, _ in self.find_connected_ways(connected, self.roads_2d_l1):
                        # Check if there is a bridge (connects layer-1 with layer1)
                        f = subcon.extra['feature']
                        if int(f['properties'].get('layer', 0)) == 1:
                            logger.info("Found tunnel to bridge link: %s", connected)
                            hend = 6.0

                    path = connected.extra['path']
                    logger.debug("Processing tunnel to ground transitions (%.2f m): %s -> %s", path.geom.length, r, connected)

                    # Tag (FIXME: shall be done in preprocessing?)
                    connected.extra['transition_lm1'] = True

                    # Reverse coordinates depending on
                    coords = path.geom.coords
                    if link_con_idx != 0:
                        coords = list(reversed(coords))

                    # Walk segment
                    # Interpolate path between lower and ground height
                    l = 0.0
                    ncoords = [ (coords[0][0], coords[0][1], hstart) ]
                    for idx in range(len(coords) - 1):
                        p, pn = coords[idx:idx+2]
                        pl = math.sqrt((pn[0] - p[0]) ** 2 + (pn[1] - p[1]) ** 2)
                        l += pl
                        h = hstart + (hend - hstart) * (l / path.geom.length)
                        #logger.debug("  Distance: %.2f  Height: %.2f", l, h)
                        ncoords.append((pn[0], pn[1], h))

                    path.geom.coords = ncoords

                    # TODO: Update path and shape vertexes

                    # Find closest vertexes to path and adjust their height accordingly

                    # Find corresponding 3d meshes
                    for r3 in self.roads_3d_l0.children + self.roads_3d_l1.children:
                        if r3.extra['feature'] == connected.extra['feature']:
                            logger.debug("Found road corresponding 3D mesh: %s", r3)

                            def road_layer_link_height(x, y, z, idx):
                                # Find nearest point in path, and return its height
                                closest_in_path = path.geom.coords[0]
                                closest_dist = math.inf
                                for idx, p in enumerate(path.geom.coords):
                                    pd = math.sqrt((x - p[0]) ** 2 + (y - p[1]) ** 2)
                                    if idx == 0: pd = pd - 20.0
                                    if idx == len(path.geom.coords) - 1: pd = pd - 20.0
                                    if pd < closest_dist:
                                        closest_in_path = p
                                        closest_dist = pd
                                #logger.debug("Closest in path: %s", closest_in_path)
                                return (x, y, z + closest_in_path[2])

                            r3.mesh = r3.vertex_func(road_layer_link_height).mesh


                #hole = connected.extrude(100).translate([0, 0, -50])
                #ddd.group([hole, self.ground_3d]).show()
                #connected.save("/tmp/fail.svg")
                #self.ground_3d = self.ground_3d.subtract(hole)
                #print(hole)

            # Walk L0 feature top to bottom

    def generate_transitions_l0_l1(self):

        logger.info("Processing road layer connections (ground to elevations).")
        # FIXME: this shall be done in preprocessing and account for shared nodes inside geoms
        # (not only start/finish)

        # Transitions from tunnel to ground
        for r in self.roads_2d_l1.children:
            #print(r.extra['feature'])
            connecteds = self.find_connected_ways(r, ddd.group(self.roads_2d_l0.children))
            if connecteds:

                hstart = 6.0
                hend = 0.0

                for connected, road_con_idx, link_con_idx in connecteds:

                    skip = False
                    for subcon, _, _ in self.find_connected_ways(connected, self.roads_2d_l1):
                        # Check if there is a bridge (connects layer-1 with layer1)
                        f = subcon.extra['feature']
                        if int(f['properties'].get('layer', 0)) == -1:
                            logger.info("Found tunnel to bridge link: %s (skipping, already processed by lm1-l1)", connected)
                            skip = True

                    if skip: continue

                    path = connected.extra['path']
                    logger.debug("Processing bridge to ground transitions (%.2f m): %s -> %s", path.geom.length, r, connected)

                    # Tag (FIXME: shall be done in preprocessing?)
                    connected.extra['transition_l1'] = True

                    # Reverse coordinates depending on
                    coords = path.geom.coords
                    if link_con_idx != 0:
                        coords = list(reversed(coords))

                    # Walk segment
                    # Interpolate path between lower and ground height
                    l = 0.0
                    ncoords = [ (coords[0][0], coords[0][1], hstart) ]
                    for idx in range(len(coords) - 1):
                        p, pn = coords[idx:idx+2]
                        pl = math.sqrt((pn[0] - p[0]) ** 2 + (pn[1] - p[1]) ** 2)
                        l += pl
                        h = hstart + (hend - hstart) * (l / path.geom.length)
                        #logger.debug("  Distance: %.2f  Height: %.2f", l, h)
                        ncoords.append((pn[0], pn[1], h))

                    path.geom.coords = ncoords

                    # TODO: Update path and shape vertexes

                    # Find closest vertexes to path and adjust their height accordingly

                    # Find corresponding 3d meshes
                    for r3 in self.roads_3d_l0.children + self.roads_3d_l1.children:
                        if r3.extra['feature'] == connected.extra['feature']:
                            logger.debug("Found road corresponding 3D mesh: %s", r3)

                            def road_layer_link_height(x, y, z, idx):
                                # Find nearest point in path, and return its height
                                closest_in_path = path.geom.coords[0]
                                closest_dist = math.inf
                                for idx, p in enumerate(path.geom.coords):
                                    pd = math.sqrt((x - p[0]) ** 2 + (y - p[1]) ** 2)
                                    if idx == 0: pd = pd - 20.0
                                    if idx == len(path.geom.coords) - 1: pd = pd - 20.0
                                    if pd < closest_dist:
                                        closest_in_path = p
                                        closest_dist = pd
                                #logger.debug("Closest in path: %s", closest_in_path)
                                return (x, y, z + closest_in_path[2])

                            r3.mesh = r3.vertex_func(road_layer_link_height).mesh

                #hole = connected.extrude(100).translate([0, 0, -50])
                #ddd.group([hole, self.ground_3d]).show()
                #connected.save("/tmp/fail.svg")
                #self.ground_3d = self.ground_3d.subtract(hole)
                #print(hole)

            # Walk L0 feature top to bottom

    def _apply_path_height(self, obj):
        """
        Receives 3D objects and looks for their path, applying path Z to vertexes.
        """

        path = obj.extra.get('path', None)
        print(path)

        def road_layer_link_height(x, y, z, idx):
            # Find nearest point in path, and return its height
            closest_in_path = path.geom.coords[0]
            closest_dist = math.inf
            for idx, p in enumerate(path.geom.coords):
                pd = math.sqrt((x - p[0]) ** 2 + (y - p[1]) ** 2)
                if idx == 0: pd = pd - 20.0
                if idx == len(path.geom.coords) - 1: pd = pd - 20.0
                if pd < closest_dist:
                    closest_in_path = p
                    closest_dist = pd
            #logger.debug("Closest in path: %s", closest_in_path)
            return (x, y, z + closest_in_path[2])

        if obj.mesh and path:
            logger.info("Applying path height to: %s", obj)
            obj = obj.vertex_func(road_layer_link_height)
        else:
            obj.children = [self._apply_path_height(c) for c in obj.children]

        return obj
    '''

    def generate_props_2d(self):
        """
        Road props (traffic lights, lampposts...).
        Need roads, areas, coastline, etc... and buildings
        """
        logger.info("Generating props linked to ways (%d ways)", len(self.osm.ways_2d["0"].children))
        ways_2d = self.osm.ways_2d["0"]

        for way_2d in ways_2d.children:
            self.generate_props_2d_way(way_2d)

    def generate_props_2d_way(self, way_2d):

        path = way_2d.extra['way_1d']
        #print(path.geom.type)
        #if path.geom.type != "LineString": return
        length = path.geom.length

        # Check if to generate
        if not path.extra['ddd_lamps']:
            return

        # Generate lamp posts

        # Lamp every 50m
        interval = 50.0
        numlamps = int(length / interval)

        # Ignore if street is short
        if numlamps == 0: return

        logger.debug("Props for way (length=%s, num=%d, way=%s)", length, numlamps, way_2d)
        for d in numpy.linspace(0.0, length, numlamps, endpoint=False):
            if d == 0.0: continue

            # Calculate left and right perpendicular intersections with sidewalk, park, land...
            #point = path.geom.interpolate(d)
            p, segment_idx, segment_coords_a, segment_coords_b = path.interpolate_segment(d)
            #logger.error("Could not generate props for way %s: %s", way_2d, e)
            #print(d, p, segment_idx, segment_coords_a, segment_coords_b)

            #segment = ddd.line([segment_coords_a, segment_coords_b])
            dir_vec = (segment_coords_b[0] - segment_coords_a[0], segment_coords_b[1] - segment_coords_a[1])
            dir_vec_length = math.sqrt(dir_vec[0] ** 2 + dir_vec[1] ** 2)
            dir_vec = (dir_vec[0] / dir_vec_length, dir_vec[1] / dir_vec_length)
            perpendicular_vec = (-dir_vec[1], dir_vec[0])
            lightlamp_dist = path.extra['width'] * 0.5 + 0.5
            right = (p[0] + perpendicular_vec[0] * lightlamp_dist, p[1] + perpendicular_vec[1] * lightlamp_dist)
            left = (p[0] - perpendicular_vec[0] * lightlamp_dist, p[1] - perpendicular_vec[1] * lightlamp_dist)

            for point in (left, right):
                item = ddd.point(point, name="LampPost %s" % way_2d.name)

                #area = self.osm.areas_2d.intersect(item)
                # Check type of area point is on

                item.extra['way_2d'] = way_2d
                item.extra['ddd_osm'] = 'way_lamppost'
                self.osm.items_1d.children.append(item)

