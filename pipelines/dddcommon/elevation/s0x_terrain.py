# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020


import math
import random

import noise
import pyproj

from ddd.core.exception import DDDException
from ddd.ddd import ddd
from ddd.geo import terrain
from ddd.pipeline.decorators import dddtask
from ddd.util.common import parse_bool
from ddd.geo.elevation import ElevationModel

"""
Manages elevation (terrain) projection initialization.

TODO: check similar module in ddd/terrain
"""

# ddd:elevation = "terrain"

@dddtask()
def ddd_common_elevation_terrain_init(root, pipeline, logger):
    """
    Initialize terrain elevation.
    """
    pass
    

@dddtask(params={'geo:center_wgs84': [-8.726203, 42.232606]})
def ddd_common_init_geo_projection(root, pipeline, logger):
    """
    Initializes the pyproj projection used to project any coordinates to the local area.
    """
    logger.info("Initializing VRS geo projection.")

    center_wgs84 = pipeline.data.get('geo:center_wgs84')

    ddd_proj = pyproj.Proj(proj="tmerc",
                           lon_0=center_wgs84[0], lat_0=center_wgs84[1],
                           k=1,
                           x_0=0., y_0=0.,
                           units="m", datum="WGS84", ellps="WGS84",
                           towgs84="0,0,0,0,0,0,0",
                           no_defs=True)

    pipeline.data['geo:proj:local'] = ddd_proj


@dddtask(params={'geo:center_wgs84': [-8.726203, 42.232606]})
def ddd_common_init_terrain_offset(root, pipeline, logger):

    ddd_proj = pipeline.data['geo:proj:local']
    elevation = ElevationModel.instance()
    terrain_offset = -elevation.value(terrain.transform_ddd_to_geo(ddd_proj, [0, 0]))
    pipeline.data['geo:terrain:origin:height:offset'] = terrain_offset

