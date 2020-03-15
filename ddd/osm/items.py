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
from ddd.pack.sketchy import terrain, plants, urban, landscape
from trimesh import creation, primitives, boolean
import trimesh
from trimesh.base import Trimesh
from trimesh.path import segments
from trimesh.path.path import Path
from trimesh.scene.scene import Scene, append_scenes
from trimesh.visual.material import SimpleMaterial
from shapely.geometry.linestring import LineString
from ddd.text import fonts


# Get instance of logger for this module
logger = logging.getLogger(__name__)

class ItemsOSMBuilder():

    def __init__(self, osmbuilder):
        self.osm = osmbuilder

        #logger.info("Generating item pools")
        self.pool = {}
        #self.pool['tree'] = [self.generate_item_3d_tree(ddd.point([0, 0, 0])) for i in range(8)]

        self.tree_decimate = 1
        self.tree_decimate_idx = 0

    def generate_items_1d(self):
        logger.info("Generating 1D items")

        for feature in self.osm.features:

            if feature['geometry']['type'] == 'Point':
                item = self.generate_item_1d(feature)
                if item:
                    #logger.debug("Item: %s", item)
                    self.osm.items_1d.children.append(item)
            else:
                #logger.warn("Unknown item geometry type: %s", feature['geometry']['type'])
                pass

    def generate_item_1d(self, feature):
        item = ddd.shape(feature['geometry'], name="Item: %s" % feature['properties'].get('name', feature['properties'].get('id', None)))
        item.extra['feature'] = feature
        item.extra['name'] = feature['properties'].get('name', None)
        item.extra['amenity'] = feature['properties'].get('amenity', None)
        item.extra['natural'] = feature['properties'].get('natural', None)
        item.extra['tourism'] = feature['properties'].get('tourism', None)
        item.extra['highway'] = feature['properties'].get('highway', None)
        item.extra['historic'] = feature['properties'].get('historic', None)
        item.extra['artwork_type'] = feature['properties'].get('artwork_type', None)
        item.extra['man_made'] = feature['properties'].get('man_made', None)

        return item

    def generate_items_3d(self):
        logger.info("Generating 3D items (from %d items_1d)", len(self.osm.items_1d.children))

        for item_2d in self.osm.items_1d.children:
            #if item_2d.geom.empty: continue
            item_3d = self.generate_item_3d(item_2d)
            if item_3d:
                item_3d.name = item_3d.name if item_3d.name else item_2d.name
                logger.debug("Generated item: %s", item_3d)
                item_3d = terrain.terrain_geotiff_min_elevation_apply(item_3d, self.osm.ddd_proj)
                self.osm.items_3d.children.append(item_3d)

        # FIXME: Do not alter every vertex, move the entire object instead
        #self.osm.items_3d = terrain.terrain_geotiff_elevation_apply(self.osm.items_3d, self.osm.ddd_proj)
        #self.osm.items_3d = self.osm.items_3d.translate([0, 0, -0.20])  # temporary fix snapping

    def generate_item_3d(self, item_2d):

        item_3d = None
        if item_2d.extra.get('amenity', None) == 'fountain':
            item_3d = self.generate_item_3d_fountain(item_2d)
        if item_2d.extra.get('amenity', None) == 'bench':
            item_3d = self.generate_item_3d_bench(item_2d)

        elif item_2d.extra.get('natural', None) == 'tree':
            self.tree_decimate_idx += 1
            if self.tree_decimate <= 1 or self.tree_decimate_idx % self.tree_decimate == 0:
                #item_3d = random.choice(self.pool['tree']).instance()
                #coords = item_2d.geom.coords[0]
                #item_3d = item_3d.translate([coords[0], coords[1], 0.0])

                item_3d = self.generate_item_3d_tree(item_2d)

        elif item_2d.extra.get('tourism', None) == 'artwork' and item_2d.extra.get('artwork_type', None) == 'sculpture':
            item_3d = self.generate_item_3d_sculpture(item_2d)
        elif item_2d.extra.get('historic', None) == 'monument':  # Monumento grande
            item_3d = self.generate_item_3d_monument(item_2d)
        elif item_2d.extra.get('historic', None) == 'memorial':
            item_3d = self.generate_item_3d_monument(item_2d)
        elif item_2d.extra.get('historic', None) == 'wayside_cross':
            item_3d = self.generate_item_3d_wayside_cross(item_2d)
        elif item_2d.extra.get('man_made', None) == 'lighthouse':
            item_3d = self.generate_item_3d_lighthouse(item_2d)

        elif item_2d.extra.get('highway', None) == 'bus_stop':
            item_3d = self.generate_item_3d_bus_stop(item_2d)

        elif item_2d.extra.get('ddd_osm', None) == 'way_lamppost':
            item_3d = self.generate_item_3d_lamppost(item_2d)
        elif item_2d.extra.get('ddd_osm', None) == 'way_trafficlights':
            item_3d = self.generate_item_3d_trafficlights(item_2d)

        else:
            logger.debug("Unknown item: %s", item_2d.extra)

        return item_3d

    def generate_item_3d_tree(self, item_2d):
        #print("Tree")
        coords = item_2d.geom.coords[0]

        plant_height = random.normalvariate(8.0, 3.0)
        if plant_height < 3.0: plant_height=random.uniform(3.0, 5.5)
        if plant_height > 15.0: plant_height=random.uniform(12.0, 15.0)
        #item_3d = plants.plant(height=random.uniform(3.0, 5.5)).translate([coords[0], coords[1], 0.0])
        item_3d = plants.plant(height=plant_height).translate([coords[0], coords[1], 0.0])
        for i in item_3d.filter(lambda o: o.extra.get('foliage', None)).children:
            i.extra['ddd:collider'] = False  # TODO: generation details shall be optional
        item_3d.name = 'Tree: %s' % item_2d.name
        #item_3d.extra['ddd:instance'] = 'tree_1'
        return item_3d

    def generate_item_3d_fountain(self, item_2d):
        # Todo: Use fountain shape if available, instead of centroid
        coords = item_2d.geom.coords[0]
        item_3d = urban.fountain(r=1.75).translate([coords[0], coords[1], 0.0])
        item_3d.name = 'Fountain: %s' % item_2d.name
        item_3d.children[0] = item_3d.children[0].material(self.osm.mat_stone)  # mat_bronze
        item_3d.children[1] = item_3d.children[1].material(self.osm.mat_stone)  # FIXME: do not access children by index, assign mat in lib anyway
        item_3d.children[2] = item_3d.children[2].material(self.osm.mat_water)  # FIXME: do not access children by index, assign mat in lib anyway
        return item_3d

    def generate_item_3d_bench(self, item_2d):
        # Todo: Use fountain shape if available, instead of centroid
        coords = item_2d.geom.coords[0]
        item_3d = urban.bench(length=2.0).translate([coords[0], coords[1], 0.0])
        #item_3d = urban.trafficlights().rotate([0, 0, item_2d.extra['ddd_angle'] - math.pi / 2])
        item_3d.name = 'Bench: %s' % item_2d.name
        item_3d.material(self.osm.mat_stone)
        return item_3d

    def generate_item_3d_sculpture(self, item_2d):
        # Todo: Use fountain shape if available, instead of centroid
        coords = item_2d.geom.coords[0]
        item_3d = urban.sculpture(1.5).translate([coords[0], coords[1], 0.0]).material(self.osm.mat_steel)  # mat_bronze
        item_3d.name = 'Sculpture: %s' % item_2d.name
        return item_3d

    def generate_item_3d_monument(self, item_2d):
        # Todo: Use fountain shape if available, instead of centroid
        coords = item_2d.geom.coords[0]
        item_name = item_2d.extra['feature']['properties'].get('name', None)
        if item_name:
            item_3d = urban.sculpture_text(item_name[:1], 2.0, 5.0).translate([coords[0], coords[1], 0.0]).material(self.osm.mat_bronze)
        else:
            item_3d = urban.sculpture(2.0, 5.0).translate([coords[0], coords[1], 0.0]).material(self.osm.mat_bronze)
        item_3d.name = 'Monument: %s' % item_2d.name
        return item_3d

    def generate_item_3d_wayside_cross(self, item_2d):
        coords = item_2d.geom.coords[0]
        item_3d = urban.wayside_cross().translate([coords[0], coords[1], 0.0]).material(self.osm.mat_stone)  # mat_bronze
        item_3d.name = 'Wayside Cross: %s' % item_2d.name
        return item_3d

    def generate_item_3d_lighthouse(self, item_2d):
        coords = item_2d.geom.coords[0]
        item_3d = landscape.lighthouse().translate([coords[0], coords[1], 0.0])
        item_3d = item_3d.material(self.osm.mat_stone)  # mat_bronze
        item_3d.name = 'Lighthouse: %s' % item_2d.name
        return item_3d

    def generate_item_3d_bus_stop(self, item_2d):
        coords = item_2d.geom.coords[0]
        text = item_2d.extra.get("name", None)
        item_3d = urban.busstop_small(text=text).translate([coords[0], coords[1], 0.0])
        item_3d.name = 'Bus Stop: %s' % item_2d.name
        return item_3d

    def generate_item_3d_lamppost(self, item_2d):
        coords = item_2d.geom.coords[0]
        item_3d = urban.lamppost(height=5.5, r=0.35).translate([coords[0], coords[1], 0.0])
        item_3d.children[0] = item_3d.children[0].material(self.osm.mat_forgery)  # mat_bronze
        item_3d.children[1] = item_3d.children[1].material(self.osm.mat_lightbulb)  # FIXME: do not access children by index, assign mat in lib anyway

        item_3d.name = 'Lampppost: %s' % item_2d.name
        #item_3d.material(self.osm.mat_highlight)
        return item_3d

    def generate_item_3d_trafficlights(self, item_2d):
        coords = item_2d.geom.coords[0]
        item_3d = urban.trafficlights().rotate([0, 0, item_2d.extra['ddd_angle'] - math.pi / 2])
        item_3d = item_3d.translate([coords[0], coords[1], 0.0])
        item_3d.name = 'Traffic Lights %s' % item_2d.name
        return item_3d


