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

"""
"""


@dddtask(order="10")
def osm_init(pipeline, root):
    """
    Pipeline initialization (variables, etc).
    """
    pass



@dddtask(order="50.999999", log=True)
def osm_finish_rest_before_3d(pipeline, osm, root, logger):

    # Generate items for point features
    ##osm.items.generate_items_1d()

    pass

