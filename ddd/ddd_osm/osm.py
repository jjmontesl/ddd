'''
'''
import math
from shapely.geometry.geo import shape
from shapely.ops import transform
from ddd import DDDObject2

'''
'''

from shapely import geometry
from trimesh.path import segments
from trimesh.scene.scene import Scene, append_scenes 
from trimesh.base import Trimesh
from trimesh.path.path import Path
from trimesh.visual.material import SimpleMaterial 
from trimesh import creation, primitives, boolean
import trimesh
from csg.core import CSG
from csg import geom as csggeom 
import random
from ddd import ddd
import noise
import geojson
from ddd_sketchy import terrain, plants, urban
import pyproj


mat_lane = ddd.material(color='#1db345')
mat_terrain = ddd.material(color='#e6821e')
mat_border = ddd.material(color='#f0f0ff')

mat_asphalt = ddd.material(color='#202020')
mat_sidewalk = ddd.material(color='#e0d0d0')
mat_park = ddd.material(color='#1db345')
mat_sea = ddd.material(color='#3d43b5')

DDD_OSM_CONFIG_DEFAULT = {
    'road_mat': ddd.material('#303030'),
}

'''
def _c(p):
    offset_x = -8.723
    offset_y = 42.238
    #offset_x = -8.708727
    #offset_y = 42.238811
    return [(p[0] - offset_x) * 100000, (p[1] - offset_y) * 100000, 0]
'''

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

def generate_geojson(files, osm_proj, ddd_proj, config=None):
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
    
    print("Loaded %d features (%d unique)" % (len(features), len(dedup)))
    features = dedup
            
    # Project to local
    transformer = pyproj.Transformer.from_proj(osm_proj, ddd_proj)
    for f in features:
        f['geometry']['coordinates'] = project_coordinates(f['geometry']['coordinates'], transformer)
        
    return generate(features, ddd_proj, config)

def _is_road(f):
    if f['geometry']['type'] == 'LineString':
        highway = f['properties'].get('highway', None)
        if highway:
            return True
    return False

def _is_building(f):
    building = f['properties'].get('building', None)
    if building:
        #if f['geometry']['type'] == 'Polygon':
        return True
    return False

def generate(features, ddd_proj, config=None, gen_terrain=True):

    # Generate, using biomes and varying configurations, from OSM features

    # Load DEM and generate terrain
    terr = None
    if gen_terrain:
        print("Generating terrain")
        #terr = terrain.terrain_grid(distance=500.0, height=1.0, detail=25.0).translate([0, 0, -0.5]).material(mat_terrain)
        terr = terrain.terrain_geotiff(distance=1000.0, detail=10.0, ddd_proj=ddd_proj).material(mat_terrain)
        #terr2 = terrain.terrain_grid(distance=60.0, height=10.0, detail=5).translate([0, 0, -20]).material(mat_terrain)
        #water = terrain.terrain_grid(distance=500.0, height=0.1, detail=100.0).translate([0, 0, 1]).material(mat_sea)

    # Generate roads (delegate depending on config)
    print("Generating roads")
    roads2 = []
    roads3 = []
    roads_fs = [f for f in features if _is_road(f)]
    for rf in roads_fs:
        (road2, road3) = generate_road(rf)
        if road2: roads2.append(road2)
        if road3: roads3.append(road3)

    roads = ddd.group(roads3)  #translate([0, 0, 50])
    roads = terrain.terrain_geotiff_elevation_apply(roads, ddd_proj)
    
    # Parks
    print("Generating parks (and trees)")
    parks = []
    for f in features:
        park = generate_park(f)
        if park: parks.append(park)
        tree = generate_tree(f)
        if tree: parks.append(tree) 
    parks = ddd.group(parks)  #translate([0, 0, 50])
    parks = terrain.terrain_geotiff_elevation_apply(parks, ddd_proj)
    
    # Union all roads in the plane and get squares (inner holes)
    print("Generating squares")
    squares = []
    union = roads2[0]
    for r in roads2[1:]:
        union = union.union(r)
    for c in union.geom:
        for interior in c.interiors:
            square = ddd.polygon(interior.coords)
            squares.append(square) 
    #union.save("/tmp/test.svg")
    
    squares3 = []
    for square in squares:
        # If it intersects with parks, ignore
        #if square.intersects()
        square3 = square.extrude(height=-1.40).translate([0, 0, 0.40])
        square3 = square3.material(mat_sidewalk)
        squares3.append(square3)
    squares3 = ddd.group(squares3)
    squares3 = terrain.terrain_geotiff_elevation_apply(squares3, ddd_proj)
    

    # Generate sidewalks (squares, delegate depending on config)
    
    # Generate urban blocks
    # Generate buildings
    print("Generating buildings")
    buildings = []
    buildings_fs = [f for f in features if _is_building(f)]
    for bf in buildings_fs:
        building = generate_building(bf)
        if building: buildings.append(building)

    buildings = ddd.group(buildings)  #translate([0, 0, 50])
    buildings = terrain.terrain_geotiff_elevation_apply(buildings, ddd_proj)
    buildings = buildings.translate([0, 0, -0.10])  # temporary fix snapping

    # Lighting
    # Traffic lights
    
    # Generate vegetation

    # Generate objects
    print("Generating objects (fountains...)")
    urbans = []
    for f in features:
        item = generate_urban(f)
        if item: urbans.append(item)
    urbans = ddd.group(urbans)  #translate([0, 0, 50])
    urbans = terrain.terrain_geotiff_elevation_apply(urbans, ddd_proj)
    urbans = urbans.translate([0, 0, +0.30])  # temporary fix snapping
    
    result = ddd.group([terr] + [parks] + [roads] + [squares3] + [buildings] + [urbans])

    return result 

def generate_road(feature, config=None):

    highway = feature['properties'].get('highway', None)
    z_order = int(feature['properties'].get('z_order', 0))
    
    other_tags = {}
    other_tags_str = feature['properties'].get('other_tags', None)
    if other_tags_str:
        for t in other_tags_str.split(","):
            try:
                k, v = t.split("=>")
                other_tags[k.replace('"', "").strip()] = v.replace('"', "").strip() 
            except:
                print("Invalid Tag: %s" % t)
        
    if z_order < 0:
        return None, None
    
    start_coords = feature['geometry']['coordinates'][0]

    #if (start_coords[0] < -500.0 or start_coords[0] > 500.0 or
    #    start_coords[1] < -500.0 or start_coords[1] > 500.0):
    #    # print("Rejected")
    #    return None, None

    path = ddd.point(start_coords)
    for c in feature['geometry']['coordinates'][1:]:
        path = path.line_to(c)

    # if oneoway, 2 lanes

    material = mat_asphalt
    extra_height = 0.15
    if highway == "footway":
        lanes = 0.6
        material = mat_sidewalk
        extra_height = 0.10
    elif highway == "service":
        lanes = 1
    elif highway == "service":
        lanes = 1
    else:    
        lanes = int(other_tags.get('lanes', '4'))

    distance = (lanes * 2.30) / 2.0
    
    path = path.buffer(distance=distance, cap_style=2, join_style=2)
    #path = path.union(ddd.disc(ddd.point(start_coords), r=2))
    #path.save("/tmp/test.svg")
    #print(path.geom)
    
    elevation = 0.0
    #if z_order > 1:
    #    elevation = 2.0 * min(z_order, 3)
    path3 = path.extrude(height=-1 - extra_height).translate([0, 0, extra_height + elevation])
    path3 = path3.material(material)

    return path, path3


def generate_building(feature, config=None):
    # TODO: delegate to buildings.py
    #print(feature)
    obj = DDDObject2(geom=shape(feature["geometry"]))

    floors = random.randint(2, 8)
    obj = obj.extrude(floors * 2.05)
    return obj
    

def generate_park(feature, config=None):

    if feature['properties'].get('leisure', None) not in ('park', 'garden'): return 
    
    # TODO: delegate to urban/landscape.py
    #print(feature)
    park_area = DDDObject2(geom=shape(feature["geometry"]))

    obj = DDDObject2(geom=shape(feature["geometry"]))

    obj = obj.extrude(-1.05).translate([0, 0, 0.05])
    obj = obj.material(mat_park)
    
    # Populate trees, fountains and hedges in the park
    vegs = []
    for p in park_area.random_points(num_points=25):
        plant = plants.plant().translate([p[0], p[1], 0.0])
        vegs.append(plant)
    
    result = ddd.group([obj] + vegs)
    
    return result

def generate_tree(feature, config=None):
    other_tags = feature['properties'].get('other_tags', None)
    if not other_tags or '"natural"=>"tree"' not in other_tags: return
    
    #print("Tree")
    coords = feature['geometry']['coordinates']
    plant = plants.plant().translate([coords[0], coords[1], 0.0])
    
    return plant
    
def generate_urban(feature, config=None):
    other_tags = feature['properties'].get('other_tags', None)
    if not other_tags or '"amenity"=>"fountain"' not in other_tags: return
    
    #print("Tree")
    coords = feature['geometry']['coordinates']
    item = urban.fountain().translate([coords[0], coords[1], 0.0])
    return item
        
    