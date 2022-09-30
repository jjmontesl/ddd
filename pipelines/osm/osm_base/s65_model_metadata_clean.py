# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020


import numpy as np

from ddd.ddd import ddd
from ddd.pipeline.decorators import dddtask
from ddd.geo import terrain
from ddd.core.exception import DDDException
import datetime
from ddd.util.common import parse_bool


"""
"""


@dddtask(order="64.10.10", condition=True)
def osm_model_metadata_clean_condition(pipeline):
    """
    Combine meshes by material condition (default is True).
    """
    return parse_bool(pipeline.data.get('ddd:osm:model:metadata_clean', True))


@dddtask(order="64.10.10.+")
def osm_model_metadata_clean(pipeline):
    """
    Clears unused metadata (this depends on the target model usage), in order to prevent
    unnecessary metadata to increase file size (some of the metadata, while useful for
    debugging, is too verbose for many practical purposes).
    """
    pass

'''

@dddtask(path="/", recurse=True)
def osm_metadata_clean_osm(pipeline, osm, root, obj):
    """
    Removes all OSM metadata.
    """
    obj.extra = { k: v for k, v in obj.extra.items() if not k.startswith("osm:") }

'''

@dddtask(path="/", recurse=True)
def osm_metadata_clean_ddd_verbose(pipeline, osm, root, obj):
    """
    Removes verbose DDD metadata.
    """
    keys = [
        'ddd:building:contacts',
        'ddd:building:segments',
        'ddd:building:convex',
        'ddd:building:convex:segments',

        #'_extruded_shape',
        'tags',
    ]

    obj.extra = { k: v for k, v in obj.extra.items() if k not in keys }

'''
@dddtask(path="/", recurse=True)
def osm_metadata_clean_ddd_minimal(pipeline, osm, root, obj):
    """
    Clears all DDD metadata except the minimal metadata needed for representation,
    as per DDD Geo Tile format (materials, instances, collapsed indices, and others)
    """
    keep_keys = [
        'uv',
        'uv:scale',

        'ddd:path',
        'ddd:rpath',
        'ddd:material',
        'ddd:material:color',
        'ddd:material:splatmap',
        'ddd:layer',

        'ddd:text',
        'ddd:text:width',
        'ddd:text:height',

        'ddd:light:color',

        'ddd:instance:key',
        'ddd:instance:buffer:matrices',

        'ddd:batch:indices',
    ]

    obj.extra = { k: v for k, v in obj.extra.items() if not k.startswith('ddd:') or k in keep_keys }

'''