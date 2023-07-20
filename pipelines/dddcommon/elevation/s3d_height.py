# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020


import math
import random

import pyproj
import noise

from ddd.core.exception import DDDException
from ddd.ddd import ddd
from ddd.geo import terrain
from ddd.pipeline.decorators import dddtask
from ddd.util.common import parse_bool

"""
Manages elevation functions (terrain, other...), and applies different elevation
methods to objects.

TODO: check similar module in ddd/ops/height and relation to terrain in pipelines and ddd
TODO: elevation or height? base_height is used? ddd.ops.height uses height... -> height?
"""

# ddd:elevation = "terrain"


@dddtask(path="/", select='["ddd:height" = "terrain"]', recurse=False)
def common_height_apply_terrain(obj, pipeline, root):
    ddd_proj = pipeline.data['geo:proj:local']
    terrain_offset = pipeline.data.get('geo:terrain:origin:height:offset', 0)
    obj = terrain.terrain_geotiff_elevation_apply(obj, ddd_proj, offset=terrain_offset)
    return obj


@dddtask(path="/", select='["ddd:height" = "min"]', recurse=False)
def common_height_apply_terrain_min(root, pipeline, obj):
    ddd_proj = pipeline.data['geo:proj:local']
    obj = terrain.terrain_geotiff_min_elevation_apply(obj, ddd_proj)
    terrain_offset = pipeline.data.get('geo:terrain:origin:height:offset', 0)
    if terrain_offset: 
        #obj = obj.translate([0, 0, terrain_offset])
        obj.transform.translate([0, 0, terrain_offset])
    return obj


@dddtask(path="/", select='["ddd:height" = "max"]', recurse=False)
def common_height_apply_terrain_max(root, pipeline, obj):
    ddd_proj = pipeline.data['geo:proj:local']
    obj = terrain.terrain_geotiff_max_elevation_apply(obj, ddd_proj)
    return obj

