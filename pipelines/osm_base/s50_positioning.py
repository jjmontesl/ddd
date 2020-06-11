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


@dddtask(order="50.05.10.+", log=True)
def osm_positioning(pipeline, osm, root, logger):
    """Repositions features in different ways."""
    pass

@dddtask(order="50.05.20.+", log=True)
def osm_positioning_init(pipeline, osm, root, logger):
    """Repositions features in different ways."""

    pipeline.data['positioning_ways_2d_0'] = root.select(path="/Ways/*", selector='["osm:layer" = "0"]', recurse=False)

    pipeline.data['positioning_ways_2d_0_major'] = root.select(path="/Ways/*", selector='["osm:layer" = "0"]', recurse=False).flatten().filter(lambda i: i.extra.get('osm:highway', None) not in ('path', 'track', 'footway', None))


# TODO: Tag earlier
@dddtask(order="50.05.30.+", log=True)
def osm_positioning_select(pipeline, osm, root, logger):
    pass

@dddtask(path="/Items/*", select='["osm:amenity" = "post_box"]')
def osm_positioning_select_postbox (obj, osm, root, logger):
    obj.extra['ddd:positioning:type'] = 'snap-project'
    obj.extra['ddd:positioning:ref'] = 'positioning_ways_2d_0'
    obj.extra['ddd:positioning:penetrate'] = -1.0

@dddtask(path="/Items/*", select='["osm:highway" = "bus_stop"]')
def osm_positioning_select_bus_stop(obj, osm, root, logger):
    obj.extra['ddd:positioning:type'] = 'snap-project'
    obj.extra['ddd:positioning:ref'] = 'positioning_ways_2d_0_major'
    obj.extra['ddd:positioning:penetrate'] = -0.5


# Apply
@dddtask(order="50.05.50.+", log=True)
def osm_positioning_apply(pipeline, osm, root, logger):
    """Apply positioning tagging (ddd:positioning)."""
    pass

@dddtask(select='["ddd:positioning:type" = "snap-project"]')
def osm_positioning_apply_snap_project(obj, pipeline, osm, root, logger):
    obj = ddd.snap.project(obj, pipeline.data[obj.extra['ddd:positioning:ref']], penetrate=obj.extra.get('ddd:positioning:penetrate', None))
    return obj

