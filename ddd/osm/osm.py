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


# Get instance of logger for this module
logger = logging.getLogger(__name__)

mat_highlight = ddd.material(color='#ff00ff')

mat_lane = ddd.material(color='#1db345')
mat_terrain = ddd.material(color='#e6821e')
mat_border = ddd.material(color='#f0f0ff')

mat_asphalt = ddd.material(color='#202020')
mat_dirt = ddd.material(color="#b58800")
mat_railway = ddd.material(color="#47443e")
mat_sidewalk = ddd.material(color='#e0d0d0')
mat_pathwalk = ddd.material(color='#78281e')
mat_park = ddd.material(color='#1db345')
mat_sea = ddd.material(color='#3d43b5')

DDD_OSM_CONFIG_DEFAULT = {
    'road_mat': ddd.material('#303030'),
}


WayConnection = namedtuple("WayConnection", "other self_idx other_idx") 


def download():
    # https://www.openstreetmap.org/api/0.6/map?bbox=-8.71921%2C42.23409%2C-8.71766%2C42.23527
    pass

def project_coordinates(coords, transformer):
    if isinstance(coords[0], list):
        coords = [project_coordinates(c, transformer) for c in coords]
    elif isinstance(coords[0], float):
        x, y = transformer.transform(coords[0], coords[1])
        coords = [x, y]
        #c = _c(coords)
    else:
        raise AssertionError()
    
    return coords

class OSMBuilder():

    def __init__(self, features=None, area=None, osm_proj=None, ddd_proj=None, config=None):
        
        self.simplify_tolerance = 0.01
        
        self.layer_indexes = ('-2', '-1', '0', '1', '2', '-2a', '-1a', '0a', '1a')
        
        self.layer_heights = {'-2': -12.0, 
                              '-1': -5.0, 
                              '0': 0.0, 
                              '1': 6.0, 
                              '2': 12.0, 
                              '-2a': 9.0, '-1a': -2.5, '0a': 3.0, '1a': 9.0}

        
        self.features = features if features else []
        self.area = area  # Polygon or shape for initial selectionof features (ie: city)
        #self.area_crop = ddd.rect([-500, -500, 1500, 750]).geom # Square to generate
        self.area_crop = ddd.rect([-1000, -750, 2000, 750]).geom # Square to generate
        
        self.osm_proj = osm_proj
        self.ddd_proj = ddd_proj
        
        self.ways_2d = defaultdict(DDDObject2)
        self.ways_3d = defaultdict(DDDObject3)
        
        self.areas_2d = DDDObject2()
        self.areas_3d = DDDObject3()
        
        self.buildings_2d = None
        self.buildings_3d = None
        
        self.water_3d = DDDObject3()
        self.ground_3d = DDDObject3()
        
        #self.sidewalks_3d_l1 = DDDObject3()
        #self.walls_3d_l1 = DDDObject3()
        #self.floor_3d_l1 = DDDObject3()
        
        
    '''
    # Deprecated, but may be needed (but as preprocessing) if we support attributes without osmimporter in the pipeline
    def other_tags(sfeature):
        other_tags = {}
        other_tags_str = feature['properties'].get('other_tags', None)
        if other_tags_str:
            for t in other_tags_str.split(","):
                try:
                    k, v = t.split("=>")
                    other_tags[k.replace('"', "").strip()] = v.replace('"', "").strip() 
                except:
                    print("Invalid Tag: %s" % t)
        return other_tags
    '''

    def load_geojson(self, files):
        
        features = []
        for f in files:
            fs = geojson.load(open(f, 'r'))
            features.extend(fs['features'])
    
        seen = set()
        dedup = []
        for f in features:
            oid = hash(str(f))  # f['properties']['osm_id']
            if oid not in seen:
                seen.add(oid)
                dedup.append(f)
        
        logger.info("Loaded %d features (%d unique)" % (len(features), len(dedup)))
        features = dedup
                
        # Filter features
        '''
        filtered = []
        for f in features:
            geom = shape(f['geometry'])
            try:
                if self.area.contains(geom):
                    filtered.append(f)
            except Exception as e:
                logger.warn("Ignored geometry: %s" % e)
        features = filtered
        logger.info("Using %d features after filtering" % (len(features)))
        '''
                
        # Project to local
        transformer = pyproj.Transformer.from_proj(self.osm_proj, self.ddd_proj)
        for f in features:
            f['geometry']['coordinates'] = project_coordinates(f['geometry']['coordinates'], transformer)
    
        # Crop
        # FIXME: this shall be done later or twice, to allow for external objects, slice some, etc...
        filtered = []
        for f in features:
            geom = shape(f['geometry'])
            if self.area_crop.contains(geom.centroid):
                filtered.append(f)
        features = filtered
        logger.info("Using %d features after cropping" % (len(features)))
        
        self.features = features

    def preprocess_features(self):
        """
        Corrects inconsistencies and adapts OSM data for generation.
        """
        
        # Correct layers
        for f in self.features:
            if f.properties.get('tunnel', None) == 'yes' and f.properties.get('layer', None) is None:
                f.properties['layer'] = "-1"
            if f.properties.get('layer', None) is None:
                f.properties['layer'] = "0"
        
        # Assign point features to buildings

    def generate_ways_1d(self):
        
        # Generate paths
        logger.info("Generating way path objects.")
        ways = []
        for feature in self.features:
            if feature['geometry']['type'] != 'LineString': continue
            way = self.generate_way_1d(feature)
            way.extra['connections'] = []
            ways.append(way)
            
        self.ways_1d = ddd.group(ways)
        
        # Find connections
        # TODO: this shall possibly come from OSM relations (or maybe not, or optional)
        logger.info("Resolving connections between ways (%d ways).", len(ways))
        vertex_cache = defaultdict(list)
        for way in self.ways_1d.children:
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
        split = False
        while split:
            split = False
            for way in self.ways_1d.children:
                for other, way_idx, other_idx in way.extra['connections']:
                    if (other_idx > 0 and other_idx != len(other.geom.coords) - 1):
                        #if not way.extra['layer_transition']: continue
                        #logger.info("Mid point connection: %s <-> %s", way, other)
                        self.split_way_1d(other, other_idx)
                        # Restart after each split
                        split = True
                    if split: break
                if split: break

        # Find transitions between more than one layer (ie tunnel to bridge) and split
        for way in self.ways_1d.children:
            way.extra['layer_transition'] = False
            way.extra['layer_int'] = int(way.extra['layer'])
            way.extra['layer_min'] = int(way.extra['layer'])
            way.extra['layer_max'] = int(way.extra['layer'])

        # Search transitions between layers
        for way in self.ways_1d.children:
            for other, way_idx, other_idx in way.extra['connections']:
                way.extra['layer_min'] = min(way.extra['layer_min'], int(other.extra['layer_int']))
                way.extra['layer_max'] = max(way.extra['layer_max'], int(other.extra['layer_int']))
            if way.extra['layer_min'] != way.extra['layer_max'] and way.extra['layer_int'] == 0: 
                #logger.debug("Layer transition (%s <-> %s): %s <-> %s", way.extra['layer_min'],other.extra['layer_max'], way, other)
                way.extra['layer_transition'] = True
                way.extra['layer'] = str(way.extra['layer_min']) + "a"
        
        # Propagate height across connections for transitions
        
        # Propagate height beyond transition layers if gradient is too large?!
        
        # Soften / subdivide roads if height angle is larger than X (try as alternative to massive subdivision of roads?)

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
        self.ways_1d.children.remove(way)
        self.ways_1d.children.extend([part1, part2])
                
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
        railway = feature['properties'].get('railway', None)
        path = ddd.shape(feature['geometry'])
        #path.geom = path.geom.simplify(tolerance=self.simplify_tolerance)
        
        lanes = None
        material = mat_asphalt
        if highway == "motorway": lanes = 2.4
        elif highway == "primary": lanes = 2.2
        elif highway == "secondary": lanes = 2.1
        elif highway == "tertiary": lanes = 2.0
        elif highway == "service": lanes = 1.0
        elif highway == "footway": 
            lanes = 0.6
            material = mat_dirt
        elif highway == "steps": 
            lanes = 0.5
            material = mat_pathwalk
        
        else: lanes = 2.0
        
        lanes = int(feature['properties'].get('lanes', lanes))

        width = (lanes * 3.30)
        
        if railway:
            lanes = 1
            width = 0.6
            material = mat_railway
        
        path = path.material(material)
        path.name = "Way: %s" % (feature['properties'].get('name', None))
        path.extra['feature'] = feature
        path.extra['width'] = width
        path.extra['lanes'] = lanes
        path.extra['layer'] = feature['properties']['layer']
        #print(feature['properties'].get("name", None))
        
        return path

    def generate(self):

        self.preprocess_features()
        
        self.generate_ways_1d() 
        
        # Roads sorted + intersections + metadata
        self.generate_ways_2d()
        
        #self.roads_2d_lm1 = self.generate_roads_2d(-1)
        #self.roads_2d_l0 = self.generate_roads_2d(0)
        #self.roads_2d_l1 = self.generate_roads_2d(1)
        
        # Regions
        # - fill (order) + correct types if interesect or marker: (park, forest, etc...)
        # - ground (fill rest of space)
        # - holes (for layer beyond)
        
        self.generate_areas_2d()
        self.generate_areas_2d_interways()  # and assign types
        #self.generate_unbounded_squares_2d() # this is current cropped ground, and assign types
        #self.assign_square_types() #

        #TODO: Find small squares (also ground?) with a lot of gradient and use walls (ie Alfonso XIII tunnel)
        # Parks (if a park touches a square, it becomes a park entirely?)
        # Football fields
        # Schools (small wall / fence...)
        
        # Buildings
        self.generate_buildings_2d()
        
        # Associate features (amenities, etc) to 2D objects (buildings, etc)
        self.associate_features()
        
        # 3D Build
        
        # Ways 3D
        self.generate_ways_3d() 
        # Areas 3D
        self.generate_areas_3d()
        # Buildings 3D
        self.generate_buildings_3d()
        
        # Walls and fences(!) (2D?)

        # Ammenities (buildings?)
        
        # Urban decoration (fountains, etc)
        
        # Trees, parks, gardens... 
        
        # Terrain (ground)
        self.generate_ground_3d(self.area_crop)
        
        #self.water_3d = terrain.terrain_grid(self.area_crop.bounds, height=0.1, detail=200.0).translate([0, 0, 1]).material(mat_sea)
        
        scene = [self.areas_3d, self.ground_3d,
                 #self.sidewalks_3d_lm1, self.walls_3d_lm1, self.ceiling_3d_lm1,
                 #self.sidewalks_3d_l1, self.walls_3d_l1, self.floor_3d_l1,
                 self.buildings_3d, self.water_3d]
        
        scene = ddd.group(scene + list(self.ways_3d.values()))
        
        return scene 

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
        elif highway == "footway": weight = 31
        else: weight = 19
        
        if junction == "roundabout": weight = 1 
        
        return weight

    def generate_ways_2d(self):
        for layer_idx in self.layer_indexes:
            self.generate_ways_2d_layer(layer_idx)
        
    def generate_ways_2d_layer(self, layer_idx):
        '''
        - Sorts ways (more important first), 
        - Generates 2D shapes 
        - Resolve intersections
        - Add metadata (road name, surface type, connections?)
        - Consider elevation and level roads on the transversal axis
        '''
        ways_1d = [w for w in self.ways_1d.children if w.extra['layer'] == layer_idx]
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
            self.ways_2d[layer_idx] = roads
        
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
        
        features = [f for f in self.features if int(f['properties'].get('layer', 0)) == layer_idx]
        
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
        for layer_idx in self.layer_indexes:
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
        return self.layer_heights[layer_idx]
        
    def generate_ways_3d_layer(self, layer_idx):
        '''
        - Sorts ways (more important first), 
        - Generates 2D shapes 
        - Resolve intersections
        - Add metadata (road name, surface type, connections?)
        - Consider elevation and level roads on the transversal axis
        '''
        ways_2d = self.ways_2d[layer_idx]
        logger.info("Generating 3D ways for layer %s: %s", layer_idx, ways_2d)
        
        layer_height = self.layer_height(layer_idx)
        ways_3d = ways_2d.extrude(-0.2).translate([0, 0, layer_height])
        ways_3d = terrain.terrain_geotiff_elevation_apply(ways_3d, self.ddd_proj)
        #ways_3d = ways_3d.material(ways_2d.mat)
        
        if layer_idx.endswith('a'):
            ways_3d = ways_3d.material(mat_highlight)
        
        self.ways_3d[layer_idx] = ways_3d
    
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
        
    def generate_elevated_way_2d(self):
        pass
        
    
    def generate_areas_2d(self):
        logger.info("Generating 2D areas")
        logger.warn("FIXME: Use DDD, not features, and preprocess Points to areas")
        
        # Union all roads in the plane to subtract
        union = ddd.group([self.ways_2d['0'], self.ways_2d['-1a'], self.areas_2d]).union()
        
        for feature in self.features:
            area = None

            if feature['geometry']['type'] == 'Point':
                continue

            if feature['properties'].get('leisure', None) in ('park', 'garden'):
                area = self.generate_area_2d_park(feature)
            elif feature['properties'].get('landuse', None) in ('railway', ):
                area = self.generate_area_2d_railway(feature)
            elif feature['properties'].get('amenity', None) in ('school', ):
                area = self.generate_area_2d_school(feature)
        
            if area:
                logger.info("Area: %s", area)
                area = area.subtract(union)
                self.areas_2d.children.append(area)
         
    def generate_areas_2d_interways(self):
        
        logger.info("Generating 2D areas between ways")
        
        union = ddd.group([self.ways_2d['0'], self.ways_2d['-1a'], self.areas_2d]).union()
        
        #union = union.buffer(0.5)
        #union = union.buffer(-0.5)
        for c in union.geom:
            for interior in c.interiors:
                area = ddd.polygon(interior.coords, name="Interways area")
                if area:
                    area = area.subtract(union)
                    self.areas_2d.children.append(area)
                else:
                    logger.warn("Invalid square.")
         
    def generate_area_2d_park(self, feature):
        area = ddd.shape(feature["geometry"], name="Park: %s" % feature['properties'].get('name', None))
        area = area.material(mat_park)
        return area
    
    def generate_area_2d_railway(self, feature):
        area = ddd.shape(feature["geometry"], name="Railway area: %s" % feature['properties'].get('name', None))
        area = area.material(mat_dirt)
        return area
     
    def generate_area_2d_school(self, feature):
        area = ddd.shape(feature["geometry"], name="School: %s" % feature['properties'].get('name', None))
        area = area.material(mat_dirt)
        return area 

    def generate_areas_3d(self):
        logger.info("Generating 3D areas (%d)", len(self.areas_2d.children))
        for area in self.areas_2d.children:
            try:
                area_3d = area.extrude(0.5).translate([0, 0, 0.2])
                area_3d = terrain.terrain_geotiff_elevation_apply(area_3d, self.ddd_proj)
                self.areas_3d.children.append(area_3d)
                #parks_3d = self.parks_2d.extrude(-0.6).translate([0, 0, 0.4 - 0.7]).material(mat_park)
                #parks_3d  = terrain.terrain_geotiff_elevation_apply(parks_3d, self.ddd_proj)
            except ValueError as e:
                logger.warn("Could not generate area %s: %s", area, e)
            except IndexError as e:
                logger.warn("Could not generate area %s: %s", area, e)

    def generate_ground_3d(self, area_crop):
        
        logger.info("Generating terrain (bounds: %s)", area_crop.bounds)
        
        #terr = terrain.terrain_grid(distance=500.0, height=1.0, detail=25.0).translate([0, 0, -0.5]).material(mat_terrain)
        #terr = terrain.terrain_geotiff(area_crop.bounds, detail=10.0, ddd_proj=self.ddd_proj).material(mat_terrain)
        #terr2 = terrain.terrain_grid(distance=60.0, height=10.0, detail=5).translate([0, 0, -20]).material(mat_terrain)
        terr = ddd.rect(area_crop.bounds, name="Ground")
        terr = terr.subtract(self.ways_2d['0'])
        terr = terr.subtract(self.ways_2d['-1a'])
        terr = terr.subtract(self.areas_2d)
        terr.save("/tmp/test.svg")
        #terr = terr.triangulate()
        terr = terr.extrude(0.3)
        terr = terrain.terrain_geotiff_elevation_apply(terr, self.ddd_proj)
        terr = terr.material(mat_terrain)
        
        self.ground_3d = terr

    def generate_ground_3d_old(self, area_crop):
        
        logger.info("Generating terrain (bounds: %s)", area_crop.bounds)
        
        #terr = terrain.terrain_grid(distance=500.0, height=1.0, detail=25.0).translate([0, 0, -0.5]).material(mat_terrain)
        terr = terrain.terrain_geotiff(area_crop.bounds, detail=10.0, ddd_proj=self.ddd_proj).material(mat_terrain)
        #terr2 = terrain.terrain_grid(distance=60.0, height=10.0, detail=5).translate([0, 0, -20]).material(mat_terrain)
        
        self.ground_3d = terr 
        
    def generate_buildings_2d(self):
        
        logger.info("Generating buildings (2D)")
         
        buildings = []
        for feature in self.features:
            building = feature['properties'].get('building', None)
            if building is None: continue
            if feature['geometry']['type'] == 'Point': continue
            building_2d = self.generate_building_2d(feature)
            
            if building_2d:
                buildings.append(building_2d)

        self.buildings_2d = ddd.group(buildings, name="Buildings")  #translate([0, 0, 50])

    def generate_building_2d(self, feature):
        building_2d = ddd.shape(feature["geometry"], name="Building (%s)" % (feature['properties'].get("name", None)))
        building_2d.extra['feature'] = feature
        return building_2d

    def generate_buildings_3d(self):
        logger.info("Generating 3D buildings (%d)", len(self.buildings_2d.children))

        buildings = []
        for building_2d in self.buildings_2d.children:
            building_3d = self.generate_building_3d(building_2d)
            if building_3d:
                buildings.append(building_3d)
        
        self.buildings_3d = ddd.group(buildings)
    
    def generate_building_3d(self, building_2d):

        feature = building_2d.extra['feature']
        
        floors = feature.properties.get('building:levels', None) 
        if not floors:
            floors = random.randint(2, 8)
        floors = int(floors)
        
        building_3d = None
        try:
            building_3d = building_2d.extrude(floors * 3.00)
        except ValueError as e:
            print("Cannot generate building: %s (geom: %s)" % (e, building_2d.geom))
            return None

        building_3d.extra['building_2d'] = building_2d
        
        self.generate_building_3d_ammenities(building_3d)
        
        building_3d = terrain.terrain_geotiff_elevation_apply(building_3d, self.ddd_proj)
        building_3d = building_3d.translate([0, 0, -0.20])  # temporary fix snapping
        
        return building_3d

    def associate_features(self):
        pass
        
    def generate_building_3d_ammenities(self, building_3d):
        pass
        '''
        for amenity in building_3d.extra['amenities']:
            
            amenity_type = amenity['properties'].get("amenity", None)
        
            #amenity = feature['properties'].get("amenity", None) 
    
            if amenity_type == "pharmacy":
                #print("Pharmacy")
                # Todo: Use building shape if available, instead of centroid
                coords = ddd.shape(amenity['geometry']).geom.centroid.coords[0]
                item = urban.sign_pharmacy(size=1.5).translate([coords[0], coords[1], 2.0])
                return item
        '''
