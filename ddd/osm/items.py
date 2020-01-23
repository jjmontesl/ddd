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
from ddd.text import fonts


# Get instance of logger for this module
logger = logging.getLogger(__name__)

class ItemsOSMBuilder():

    def __init__(self, osmbuilder):
        self.osm = osmbuilder

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
        item = ddd.shape(feature['geometry'], name="Item: %s" % feature['properties'].get('name', None))
        item.extra['feature'] = feature
        item.extra['name'] = feature['properties'].get('name', None)
        item.extra['amenity'] = feature['properties'].get('amenity', None)
        item.extra['natural'] = feature['properties'].get('natural', None)
        item.extra['tourism'] = feature['properties'].get('tourism', None)
        item.extra['historic'] = feature['properties'].get('historic', None)
        item.extra['artwork_type'] = feature['properties'].get('artwork_type', None)

        return item

    def generate_items_3d(self):
        logger.info("Generating 3D items (from %d items_1d)", len(self.osm.items_1d.children))

        for item_2d in self.osm.items_1d.children:
            #if item_2d.geom.empty: continue
            item_3d = self.generate_item_3d(item_2d)
            if item_3d:
                item_3d.name = item_3d.name if item_3d.name else item_2d.name
                logger.debug("Generated item: %s", item_3d)
                self.osm.items_3d.children.append(item_3d)

        # FIXME: Do not alter every vertex, move the entire object instead
        self.osm.items_3d = terrain.terrain_geotiff_elevation_apply(self.osm.items_3d, self.osm.ddd_proj)
        #self.osm.items_3d = self.osm.items_3d.translate([0, 0, -0.20])  # temporary fix snapping

    def generate_item_3d(self, item_2d):
        item_3d = None
        if item_2d.extra.get('amenity', None) == 'fountain':
            item_3d = self.generate_item_3d_fountain(item_2d)
        elif item_2d.extra.get('natural', None) == 'tree':
            item_3d = self.generate_item_3d_tree(item_2d)
        elif item_2d.extra.get('tourism', None) == 'artwork' and item_2d.extra.get('artwork_type', None) == 'sculpture':
            item_3d = self.generate_item_3d_sculpture(item_2d)
        elif item_2d.extra.get('historic', None) == 'monument':  # Monumento grande
            item_3d = self.generate_item_3d_monument(item_2d)
        elif item_2d.extra.get('historic', None) == 'memorial':
            item_3d = self.generate_item_3d_monument(item_2d)
        elif item_2d.extra.get('historic', None) == 'wayside_cross':
            item_3d = self.generate_item_3d_wayside_cross(item_2d)
        elif item_2d.extra.get('ddd_osm', None) == 'way_lamppost':
            item_3d = self.generate_item_3d_lamppost(item_2d)
        elif item_2d.extra.get('ddd_osm', None) == 'way_trafficlights':
            item_3d = self.generate_item_3d_trafficlights(item_2d)

        return item_3d

    def generate_item_3d_tree(self, item_2d):
        #print("Tree")
        coords = item_2d.geom.coords[0]
        item_3d = plants.plant().translate([coords[0], coords[1], 0.0])
        #for i in item_3d.select(".foliage"):
        #    i.extra['ddd:collider'] = False  # TODO: generation details shall be optional
        item_3d.name = 'Tree: %s' % item_2d.name
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

    def generate_item_3d_lamppost(self, item_2d):
        coords = item_2d.geom.coords[0]
        item_3d = urban.lamppost(height=3.3).translate([coords[0], coords[1], 0.0])
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


