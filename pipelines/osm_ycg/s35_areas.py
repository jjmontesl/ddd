# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020

import sys

import pyproj

from ddd.ddd import ddd
from ddd.geo import terrain
from ddd.osm import osm
from ddd.osm.augment.mapillary import MapillaryClient
from ddd.osm.osm import project_coordinates
from ddd.pipeline.decorators import dddtask



# Add fences to schools
def generate_area_2d_school(self, area):
    feature = area.extra['osm:feature']
    area.name = "School: %s" % feature['properties'].get('name', None)
    area = area.material(ddd.mats.dirt)
    area.extra['ddd:height'] = 0.0

    # TODO: Generate only if no borders or other wall/fence/barriers present
    area = self.generate_wallfence_2d(area, doors=2)

    return area