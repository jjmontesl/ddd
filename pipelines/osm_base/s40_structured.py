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


@dddtask(order="40.10.+", log=True)
def osm_structured_init(root, osm):
    pass

@dddtask(log=True)
def osm_structured_rest(root, osm):
    osm.ways.generate_ways_2d()

    osm.areas.generate_areas_2d()
    osm.areas.generate_areas_2d_interways()  # and assign types

    osm.areas.generate_areas_2d_postprocess()
    osm.areas.generate_areas_2d_postprocess_water()

    # Associate features (amenities, etc) to 2D objects (buildings, etc)
    osm.buildings.link_features_2d()



@dddtask(order="40.90")
def osm_structured_finished(pipeline, osm, root, logger):
    pass
