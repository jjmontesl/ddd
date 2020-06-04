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


@dddtask(order="30.9.+")
def osm_generate_export_2d(root):

    root = root.copy()
    root = root.remove(root.find("/Features"))  # !Altering
    root.find("/Areas").replace(root.find("/Areas").material(ddd.mats.park).prop_set('svg:fill-opacity', 0.6, True))
    root.find("/Ways").replace(root.find("/Ways").buffer(1.0).material(ddd.mats.asphalt).prop_set('svg:fill-opacity', 0.8, True))
    root.find("/Buildings").replace(root.find("/Buildings").material(ddd.mats.stone).prop_set('svg:fill-opacity', 0.7, True))
    root.find("/Items").replace(root.find("/Items").buffer(1.0).material(ddd.mats.highlight))
    root.save("/tmp/osm-10-main.json")
    root.save("/tmp/osm-10-main.svg")

