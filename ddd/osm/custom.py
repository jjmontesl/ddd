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

class CustomsOSMBuilder():

    def __init__(self, osmbuilder):
        self.osm = osmbuilder

    def generate_customs(self):
        self.generate_customs_1d()
        #self.generate_customs_2d()
        self.generate_customs_3d()

    def generate_customs_1d(self):
        logger.info("Generating 1D custom items")

        for feature in self.osm.features_custom:

            if feature['geometry']['type'] == 'MultiPoint':
                item = self.generate_custom_1d(feature)
                if item:
                    #logger.debug("Item: %s", item)
                    self.osm.customs_1d.children.append(item)
            else:
                logger.warn("Unknown custom geometry type: %s", feature['geometry']['type'])
                pass

    def generate_custom_1d(self, feature):

        otype = 'checkpoint'
        layer = feature.properties.get('layer')

        if otype == 'checkpoint':
            race = layer
            idx = int(feature.properties.get('fid'))
            item = ddd.shape(feature['geometry'], name="Checkpoint %d (race): %s" % (idx, race))
            item.extra['checkpoint_idx'] = idx
            item.extra['type'] = otype
        else:
            logger.warn("Unknown custom feature: %s", feature)
            return

        return item

    def generate_customs_3d(self):
        logger.info("Generating 3D custom items (from %d customs_1d)", len(self.osm.customs_1d.children))

        for custom_2d in self.osm.customs_1d.children:
            #if custom_2d.geom.empty: continue
            custom_3d = self.generate_custom_3d(custom_2d)
            if custom_3d:
                custom_3d.name = custom_3d.name if custom_3d.name else custom_2d.name
                logger.debug("Generated custom item: %s", custom_3d)
                self.osm.customs_3d.children.append(custom_3d)

        # FIXME: Do not alter every vertex, move the entire object instead
        self.osm.customs_3d = terrain.terrain_geotiff_elevation_apply(self.osm.customs_3d, self.osm.ddd_proj)
        #self.osm.customs_3d = self.osm.customs_3d.translate([0, 0, -0.20])  # temporary fix snapping

    def generate_custom_3d(self, custom_2d):
        custom_3d = None
        if custom_2d.extra.get('type') == 'checkpoint':
            custom_3d = self.generate_custom_3d_checkpoint(custom_2d)
        else:
            logger.warn("Unknown custom feature: %s", custom_2d)
            return

        return custom_3d

    def generate_custom_3d_checkpoint(self, custom_2d):
        pass

