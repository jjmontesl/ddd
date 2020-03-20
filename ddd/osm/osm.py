# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

from collections import defaultdict, namedtuple
import logging

import geojson
import pyproj

from ddd.ddd import DDDObject2, DDDObject3
from ddd.ddd import ddd
from ddd.osm.areaitems import AreaItemsOSMBuilder
from ddd.osm.areas import AreasOSMBuilder
from ddd.osm.buildings import BuildingOSMBuilder
from ddd.osm.custom import CustomsOSMBuilder
from ddd.osm.items import ItemsOSMBuilder
from ddd.osm.ways import WaysOSMBuilder
from shapely.geometry.geo import shape
from ddd.prefab.catalog import PrefabCatalog


# Get instance of logger for this module
logger = logging.getLogger(__name__)

WayConnection = namedtuple("WayConnection", "other self_idx other_idx")

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

    # Golf
    #mat_lane = ddd.material(color='#1db345')
    #mat_border = ddd.material(color='#f0f0ff')

    '''
    # Ways
    mat_asphalt = ddd.material(name="Asphalt", color='#202020')
    mat_dirt = ddd.material(color="#b58800")
    mat_railway = ddd.material(color="#47443e")
    mat_sidewalk = ddd.material(name="Sidewalk", color='#e0d0d0')
    mat_pavement = ddd.material(name="Sidewalk", color='#c0c0b0')
    mat_pathwalk = ddd.material(name="WayPedestrian", color='#78281e')

    mat_roadline = ddd.material(name="Roadline", color='#e8e8e8')

    # Areas
    mat_park = ddd.material(name="Park", color='#1db345')
    mat_pitch = ddd.material(color='#196118')
    mat_sea = ddd.material(name="Water4Advanced", color='#3d43b5')
    mat_terrain = ddd.material(name="Ground", color='#e6821e')

    # Structural / building materials
    mat_bronze = ddd.material(color='#f0cb11')
    mat_steel = ddd.material(color='#78839c')
    mat_stone = ddd.material(color='#9c9378')
    mat_cement = ddd.material(name="Concrete", color='#b8b8a0')
    mat_brick = ddd.material(color='#d49156')
    mat_forgery = ddd.material(color='#1e1118')
    mat_wood = ddd.material(color='#efae85')
    mat_water = ddd.material(name="WaterBasicDaytime", color='#4d53c5')

    # Trees
    mat_bark = ddd.material(name="Bark", color='#df9e75')
    mat_leaves = ddd.material(color='#1da345')

    # Urban props materials
    mat_lightbulb = ddd.material(color='e8e0e4')
    mat_railing = ddd.material(color='282024')

    # Buildings
    mat_building_1 = ddd.material(color='#f7f0be')
    mat_building_2 = ddd.material(color='#bdb9a0')
    mat_building_3 = ddd.material(color='#c49156')
    mat_roof_tile = ddd.material(color='#f25129')
    '''

    def __init__(self, features=None, area_filter=None, area_crop=None, osm_proj=None, ddd_proj=None, config=None):

        self.catalog = PrefabCatalog()

        self.items = ItemsOSMBuilder(self)
        self.items2 = AreaItemsOSMBuilder(self)
        self.ways = WaysOSMBuilder(self)
        self.areas = AreasOSMBuilder(self)
        self.buildings = BuildingOSMBuilder(self)
        self.customs = CustomsOSMBuilder(self)

        self.area_filter = area_filter
        self.area_crop = area_crop

        #self.simplify_tolerance = 0.01

        self.layer_indexes = ('-2', '-1', '0', '1', '2', '3', '-2a', '-1a', '0a', '1a')

        self.layer_heights = {'-2': -12.0,
                              '-1': -5.0,
                              '0': 0.0,
                              '1': 6.0,
                              '2': 12.0,
                              '3': 18.0,
                              #'-2a': -9.0, '-1a': -2.5, '0a': 3.0, '1a': 9.0}
                              #'-2a': -12.0, '-1a': -5.0, '0a': 0.0, '1a': 6.0}
                              '-2a': 0.0, '-1a': 0.0, '0a': 0.0, '1a': 0.0}


        self.features = features if features else []

        self.osm_proj = osm_proj
        self.ddd_proj = ddd_proj

        self.items_1d = DDDObject2(name="Items 1D")  # Point items
        self.items_2d = DDDObject2(name="Items 2D")  # Area items
        self.items_3d = DDDObject3(name="Items")

        self.ways_1d = None
        self.ways_2d = defaultdict(DDDObject2)
        self.ways_3d = defaultdict(DDDObject3)

        self.roadlines_2d = DDDObject2(name="Roadlines 2D")
        self.roadlines_3d = DDDObject3(name="Roadlines")

        self.areas_2d = DDDObject2("Areas 2D")
        self.areas_2d_objects = DDDObject2(name="Areas 2D Objects")
        self.areas_3d = DDDObject3(name="Areas")

        self.buildings_2d = None
        self.buildings_3d = None

        self.water_2d = DDDObject2(name="Water 2D")
        self.water_3d = DDDObject3(name="Water")

        self.ground_3d = DDDObject3(name="Ground")

        self.other_3d = DDDObject3(name="Other")

        self.customs_1d = DDDObject2(name="Customs 1D")
        self.customs_3d = DDDObject3(name="Customs")

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
        features_custom = []
        for f in features:
            #oid = hash(str(f))  # f['properties']['osm_id']

            # TODO: better way to distinguish custom features
            if 'id' not in f:
                features_custom.append(f)
                continue

            oid = f['id']
            if oid not in seen:
                seen.add(oid)
                dedup.append(f)

        logger.info("Loaded %d features (%d unique)" % (len(features), len(dedup)))
        features = dedup

        # Project to local
        transformer = pyproj.Transformer.from_proj(self.osm_proj, self.ddd_proj)
        for f in features:
            f['geometry']['coordinates'] = project_coordinates(f['geometry']['coordinates'], transformer)

        # Filter "supertile"
        filtered = []
        for f in features:
            geom = shape(f['geometry'])
            #if self.area_filter.contains(geom.centroid):
            if self.area_filter.intersects(geom):
                filtered.append(f)
        features = filtered
        logger.info("Using %d features after filtering to %s" % (len(features), self.area_filter.bounds))

        self.features = features
        self.features_custom = features_custom

        #logger.debug("Custom features: %s", self.custom)

    def preprocess_features(self):
        """
        Corrects inconsistencies and adapts OSM data for generation.
        """

        # Correct layers
        for f in self.features:
            f.properties['id'] = f.properties['id'].replace("/", "-")
            if f.properties.get('tunnel', None) == 'yes' and f.properties.get('layer', None) is None:
                f.properties['layer'] = "-1"
            if f.properties.get('brige', None) == 'yes' and f.properties.get('layer', None) is None:
                f.properties['layer'] = "1"
            if f.properties.get('layer', None) is None:
                f.properties['layer'] = "0"

    def generate(self):

        logger.info("Generating geometry (area_filter=%s, area_crop=%s)", self.area_filter, self.area_crop)

        self.preprocess_features()

        # Generate items for point features
        self.items.generate_items_1d()

        # Roads sorted + intersections + metadata
        self.ways.generate_ways_1d()

        # Test: get a way and walk connections
        #ways = [w for w in self.ways_1d.children if 'de Ceta' in w.name or 'way/165386383' in w.name or 'way/666643707' in w.name or 'way/700343244' in w.name]
        '''
        ways = [w for w in self.ways_1d.children if 'de Ceta' in w.name]
        ddd.group(ways).save("/tmp/test.svg")  #group(see).show()

        #for way in ways:
        ways[-1] = ways[-1].material(ddd.mat_highlight)
        way = ways[-1]
        for d in range(15):  #range():
            dumped = self.ways.dump_way(way, depth=d)
            #ddd.group(dumped).save("/tmp/test%02d.svg" % d)  #group(see).show()
            ddd.group(dumped).buffer(1).show()
        sys.exit(1)
        '''

        self.ways.generate_ways_2d()

        # Regions
        # - fill (order) + correct types if interesect or marker: (park, forest, etc...)
        # - ground (fill rest of space)
        # - holes (for layer beyond)

        self.areas.generate_areas_2d()
        self.areas.generate_areas_2d_interways()  # and assign types

        #self.generate_unbounded_squares_2d() # this is current cropped ground, replace with this, assign types
        #self.assign_area_types() #


        # Buildings
        self.buildings.generate_buildings_2d()
        self.buildings.link_features_2d()

        '''
        self.areas_2d = self.areas_2d.subtract(self.buildings_2d)
        '''

        # Associate features (amenities, etc) to 2D objects (buildings, etc)
        #self.buildings.associate_features()

        self.areas.generate_coastline_3d(self.area_crop if self.area_crop else self.area_filter)  # must come before ground
        self.areas.generate_ground_3d(self.area_crop if self.area_crop else self.area_filter) # separate in 2d + 3d, also subdivide (calculation is huge - core dump-)

        # Generates items defined as areas (area fountains, football fields...)
        self.items2.generate_items_2d()  # Objects related to areas (fountains, playgrounds...)

        # Road props (traffic lights, lampposts, fountains, football fields...) - needs. roads, areas, coastline, etc... and buildings
        self.ways.generate_props_2d()  # Objects related to ways

        # Crop if necessary
        if self.area_crop:
            logger.info("Cropping to: %s" % (self.area_crop.bounds, ))
            crop = ddd.shape(self.area_crop)
            self.areas_2d = self.areas_2d.intersect(crop)
            self.ways_2d = {k: self.ways_2d[k].intersect(crop) for k in self.layer_indexes}

            #self.items_1d = self.items_1d.intersect(crop)
            self.items_1d = ddd.group([b for b in self.items_1d.children if self.area_crop.contains(b.geom.centroid)], empty=2)
            self.items_2d = ddd.group([b for b in self.items_2d.children if self.area_crop.contains(b.geom.centroid)], empty=2)
            self.buildings_2d = ddd.group([b for b in self.buildings_2d.children if self.area_crop.contains(b.geom.centroid)], empty=2)

        # 3D Build

        # Ways 3D
        self.ways.generate_ways_3d()
        self.ways.generate_ways_3d_intersections()
        # Areas 3D
        self.areas.generate_areas_3d()
        # Buildings 3D
        self.buildings.generate_buildings_3d()

        # Walls and fences(!) (2D?)

        # Urban decoration (trees, fountains, etc)
        self.items.generate_items_3d()
        self.items2.generate_items_3d()

        # Generate custom items
        self.customs.generate_customs()

        # Trees, parks, gardens...

        scene = [self.areas_3d, self.ground_3d, self.water_3d,
                 #self.sidewalks_3d_lm1, self.walls_3d_lm1, self.ceiling_3d_lm1,
                 #self.sidewalks_3d_l1, self.walls_3d_l1, self.floor_3d_l1,
                 self.buildings_3d, self.items_3d,
                 self.other_3d, self.roadlines_3d]

        scene = ddd.group(scene + list(self.ways_3d.values()), name="Scene")

        return scene

