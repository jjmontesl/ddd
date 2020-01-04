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
        item.extra['amenity'] = feature['properties'].get('amenity', None)
        item.extra['natural'] = feature['properties'].get('natural', None)
        item.extra['tourism'] = feature['properties'].get('tourism', None)
        item.extra['artwork_type'] = feature['properties'].get('artwork_type', None)
        
        return item

    def generate_items_3d(self):
        logger.info("Generating 3D items")
        
        for item_2d in self.osm.items_1d.children:
            item_3d = self.generate_item_3d(item_2d)
            if item_3d:
                item_3d.name = item_2d.name
                logger.debug("Generated item: %s", item_3d)
                self.osm.items_3d.children.append(item_3d)

        # FIXME: Do not alter every vertex, move the entire object instead
        self.osm.items_3d = terrain.terrain_geotiff_elevation_apply(self.osm.items_3d, self.osm.ddd_proj) 
        #self.osm.items_3d = self.osm.items_3d.translate([0, 0, -0.20])  # temporary fix snapping
            
    def generate_item_3d(self, item_2d):
        item_3d = None
        if item_2d.extra['amenity'] == 'fountain':
            item_3d = self.generate_item_3d_fountain(item_2d)
        elif item_2d.extra['natural'] == 'tree':
            item_3d = self.generate_item_3d_tree(item_2d)
        elif item_2d.extra['tourism'] == 'artwork' and item_2d.extra['artwork_type'] == 'sculpture':
            item_3d = self.generate_item_3d_sculpture(item_2d)
        
        return item_3d
                
    def generate_item_3d_tree(self, item_2d):
        #print("Tree")
        coords = item_2d.geom.coords[0]
        item_3d = plants.plant().translate([coords[0], coords[1], 0.0])
        item_3d.name = 'Tree: %s' % item_2d.name
        return item_3d
        
    def generate_item_3d_fountain(self, item_2d):
        # Todo: Use fountain shape if available, instead of centroid
        coords = item_2d.geom.coords[0]
        item_3d = urban.fountain(r=1.75).translate([coords[0], coords[1], 0.0])
        item_3d.name = 'Fountain: %s' % item_2d.name
        return item_3d
    
    def generate_item_3d_sculpture(self, item_2d):
        # Todo: Use fountain shape if available, instead of centroid
        coords = item_2d.geom.coords[0]
        item_3d = urban.sculpture(1.75).translate([coords[0], coords[1], 0.0]).material(self.osm.mat_steel)  # mat_bronze
        item_3d.name = 'Sculpture: %s' % item_2d.name
        return item_3d
    

