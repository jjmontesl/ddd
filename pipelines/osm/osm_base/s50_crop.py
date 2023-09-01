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
from ddd.core.exception import DDDException

"""
"""


@dddtask(order="50.80.10.+", log=True)
def osm_crop(pipeline, osm, root, logger):
    """Crops features in different ways."""
    osm.area_crop2.index_clear()


@dddtask(path="/Areas/*")
def osm_crop_areas(obj, osm, root, logger):
    obj.set('ddd:crop', default='area')

@dddtask(path="/Ways/*")
def osm_crop_ways(obj, osm, root, logger):
    obj.set('ddd:crop', default='area')

@dddtask(path="/Structures2/*")
def osm_crop_structures(obj, osm, root, logger):
    obj.set('ddd:crop', default='area')

@dddtask(path="/ItemsAreas/*")
def osm_crop_items_areas(obj, osm, root, logger):
    obj.set('ddd:crop', default='centroid')

@dddtask(path="/ItemsWays/*")
def osm_crop_items_ways(obj, osm, root, logger):
    obj.set('ddd:crop', default='centroid')

@dddtask(path="/ItemsNodes/*")
def osm_crop_items_nodes(obj, osm, root, logger):
    obj.set('ddd:crop', default='centroid')


@dddtask(path="/Buildings/*")
def osm_crop_buildings(obj, osm, root, logger):
    obj.set('ddd:crop', default='centroid')


@dddtask(order="50.80.90.+", log=True)
def osm_crop_apply(obj, osm, root, logger):
    pass

@dddtask(select='["ddd:crop" = "area"]')
def osm_crop_apply_area(obj, osm, root, logger):
    obj.extra['ddd:crop:original'] = obj.copy()
    obj = obj.intersection(osm.area_crop2)
    return obj

@dddtask(select='["ddd:crop" = "centroid"]')
def osm_crop_apply_centroid(obj, osm, root, logger):
    try:
        point = obj.centroid()
    except DDDException as e:
        logger.warn("Could not find centroid for cropping for: %s", obj)
        return False

    contained = osm.area_crop2.contains(point)
    if not contained:
        return False


@dddtask()
def osm_crop_cleanup(root, logger):
    """
    Remove empty geometries.
    """
    for c in root.children:
        c.clean_replace()

