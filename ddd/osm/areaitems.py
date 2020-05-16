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
from ddd.pack.sketchy import plants, urban
from trimesh import creation, primitives, boolean
import trimesh
from trimesh.base import Trimesh
from trimesh.path import segments
from trimesh.path.path import Path
from trimesh.scene.scene import Scene, append_scenes
from trimesh.visual.material import SimpleMaterial
from shapely.geometry.linestring import LineString
from ddd.geo import terrain
from ddd.pack.sketchy.urban import childrens_playground_swingset,\
    childrens_playground_sandbox, childrens_playground_slide,\
    childrens_playground_arc


# Get instance of logger for this module
logger = logging.getLogger(__name__)

class AreaItemsOSMBuilder():

    def __init__(self, osmbuilder):
        self.osm = osmbuilder

    def generate_items_2d(self):
        logger.info("Generating 2D area items (fountains, playgrounds...)")


        for feature in self.osm.features_2d.children:

            if feature.geom.type == 'Point': continue

            area = None

            if feature.extra.get('osm:amenity', None) in ('fountain', ):
                area = self.generate_item_2d_fountain(feature)
            elif feature.extra.get('osm:water', None) in ('pond', ):
                area = self.generate_item_2d_pond(feature)

            elif feature.extra.get('osm:leisure', None) == 'outdoor_seating':
                area = self.generate_item_2d_outdoor_seating(feature)
            elif feature.extra.get('osm:leisure', None) == 'playground':
                area = self.generate_item_2d_childrens_playground(feature)

            if area:
                #union = union.union(area)
                self.osm.items_2d.children.append(area)
                logger.debug("Area Object: %s", area)

    def generate_item_2d_fountain(self, feature):
        area = feature.copy(name="Area Fountain: %s" % feature.extra.get('name', None))
        return area

    def generate_item_2d_pond(self, feature):
        area = feature.copy(name="Pond: %s" % feature.extra.get('name', None))
        return area

    def generate_item_2d_outdoor_seating(self, feature):

        # Distribute centers for seating (ideally, grid if shape is almost square, sampled if not)
        # For now, using center:

        center = feature.centroid()

        table = center.copy(name="Outdoor seating table: %s" % feature.name)
        table.extra['osm:amenity'] = 'table'
        table.extra['osm:seats'] = random.randint(0, 4)

        umbrella = ddd.group2()
        if random.uniform(0, 1) < 0.8:
            umbrella = center.copy(name="Outdoor seating umbrella: %s" % feature.name)
            umbrella.extra['osmext:amenity'] = 'umbrella'

        chairs = ddd.group2(name="Outdoor seating seats")
        ang_offset = random.choice([0, math.pi / 2, math.pi, math.pi * 3/4])
        for i in range(table.extra['osm:seats']):
            ang = ang_offset + (2 * math.pi / table.extra['osm:seats']) * i + random.uniform(-0.1, 0.1)
            chair = ddd.point([0, random.uniform(0.7, 1.1)], name="Outdoor seating seat %d: %s" % (i, feature.name))
            chair = chair.rotate(ang).translate(center.geom.coords[0])
            chair.extra['osm:amenity'] = 'seat'
            chair.extra['ddd:angle'] = ang + random.uniform(-0.1, 0.1) # * (180 / math.pi)
            chairs.append(chair)

        item = ddd.group2([table, umbrella, chairs], "Outdoor seating: %s" % feature.name)

        for i in item.flatten().children:
            if i.geom: self.osm.items_1d.append(i)

        return None

    def generate_item_2d_childrens_playground(self, feature):

        # Distribute centers for seating (ideally, grid if shape is almost square, sampled if not)
        # For now, using center:

        center = feature.centroid()

        items = [ddd.point(name="Swingset", extra={'osm:playground': 'swing'}),
                 ddd.point(name="Swingset", extra={'osm:playground': 'sandbox'}),
                 ddd.point(name="Swingset", extra={'osm:playground': 'slide'}),
                 ddd.point(name="Swingset", extra={'osm:playground': 'monkey_bar'})]
        items = ddd.group2(items, name="Childrens Playground")

        items = ddd.align.polar(items, 2)
        items.translate(center)

        for i in items.flatten().children:
            self.osm.items_1d.append(i)

        return None

    def generate_items_3d(self):
        logger.info("Generating 3D area items")

        for item_2d in self.osm.items_2d.children:
            item_3d = self.generate_item_3d(item_2d)
            if item_3d:
                item_3d.name = item_2d.name
                item_3d = terrain.terrain_geotiff_elevation_apply(item_3d, self.osm.ddd_proj)
                self.osm.items_3d.children.append(item_3d)
                logger.debug("Generated area item: %s", item_3d)

        # FIXME: Do not alter every vertex, move the entire object instead
        #self.osm.items_3d = self.osm.items_3d.translate([0, 0, -0.20])  # temporary fix snapping

    def generate_item_3d(self, item_2d):
        item_3d = None
        if item_2d.extra.get('osm:amenity', None) == 'fountain':
            item_3d = self.generate_item_3d_fountain(item_2d)
        if item_2d.extra.get('osm:water', None) == 'pond':
            item_3d = self.generate_item_3d_pond(item_2d)

        return item_3d

    def generate_item_3d_fountain(self, item_2d):
        # Todo: Use fountain shape if available, instead of centroid
        exterior = item_2d.subtract(item_2d.buffer(-0.3)).extrude(1.0).material(ddd.mats.stone)
        exterior = ddd.uv.map_cylindrical(exterior)

        water =  item_2d.buffer(-0.20).triangulate().material(ddd.mats.water).translate([0, 0, .7])

        #coords = item_2d.geom.centroid.coords[0]
        #insidefountain = urban.fountain(r=item_2d.geom).translate([coords[0], coords[1], 0.0])

        item_3d = ddd.group([exterior, water])

        item_3d.name = 'Fountain: %s' % item_2d.name
        return item_3d

    def generate_item_3d_pond(self, item_2d):
        # Todo: Use fountain shape if available, instead of centroid
        exterior = item_2d.subtract(item_2d.buffer(-0.4)).extrude(0.4).material(ddd.mats.dirt)
        exterior = ddd.uv.map_cylindrical(exterior)

        water = item_2d.buffer(-0.2).triangulate().material(ddd.mats.water)

        #coords = item_2d.geom.centroid.coords[0]
        #insidefountain = urban.fountain(r=item_2d.geom).translate([coords[0], coords[1], 0.0])

        item_3d = ddd.group([exterior, water])  # .translate([0, 0, 0.3])

        item_3d.name = 'Pond: %s' % item_2d.name
        return item_3d
