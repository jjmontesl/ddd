# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020

import sys

import pyproj

from ddd.ddd import ddd
from ddd.geo import terrain
from ddd.osm import osm
from ddd.osm.osm import project_coordinates
from ddd.pipeline.decorators import dddtask


# TODO: bear in mind that elevation/height fine-calculation shall come before this possibly


@dddtask(order="50.30", condition=True)
def osm_stairs_condition(pipeline):
    return bool(pipeline.data.get('ddd:osm:stairs', True))


@dddtask(order="50.30.10.+", path="/Ways", select='["ddd:way:stairs"][!"intersection"]')
def osm_stairs_split(pipeline, osm, root, logger, obj):
    """
    TODO: Use an algorithm based on projection from interior vertex corners.
    """
    #osm.ways2.generate_stairs_simple(pipeline, obj)
    obj = osm.ways2.generate_stairs_simple(pipeline, obj)
    return obj






