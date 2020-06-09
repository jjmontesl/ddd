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
    osm.ways_1d = root.find("/Ways")
    pass

@dddtask()
def osm_structured_split_ways(osm, root):
    osm.ways1.split_ways_1d()  # Where to put?

@dddtask()
def osm_generate_areas_interways(pipeline, osm, root, logger):
    osm.areas2.generate_areas_2d_interways()

@dddtask(log=True)
def osm_structured_rest(root, osm):

    root.find("/Ways").replace(osm.ways_1d)

    #osm.buildings_2d =
    osm.buildings.preprocess_buildings_2d()
    osm.buildings.generate_buildings_2d()

    osm.ways2.generate_ways_2d()

    #osm.areas2.generate_areas_2d()
    #osm.areas2.generate_areas_2d_interways()  # and assign types

    osm.areas2.generate_areas_2d_postprocess()
    osm.areas2.generate_areas_2d_postprocess_water()

    # Associate features (amenities, etc) to 2D objects (buildings, etc)
    osm.buildings.link_features_2d()

    # Coastline and ground
    osm.areas3.generate_coastline_3d(osm.area_crop if osm.area_crop else osm.area_filter)  # must come before ground
    #osm.areas3.generate_ground_3d(osm.area_crop if osm.area_crop else osm.area_filter) # separate in 2d + 3d, also subdivide (calculation is huge - core dump-)


@dddtask(order="40.90")
def osm_structured_finished(pipeline, osm, root, logger):
    pass
