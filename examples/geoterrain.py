# ddd - DDD123
# Library for simple scene modelling.
# Jose Juan Montes and Contributors 2019-2021

import math

import pyproj

from ddd.ddd import ddd
from ddd.geo import terrain
from ddd.pipeline.decorators import dddtask


@dddtask(order="10")
def pipeline_start(pipeline, root):
    """
    Generate a terrain mesh from a DEM.
    """

    coords_latlon = [42.232606, -8.726203]
    ddd_proj = pyproj.Proj(proj="tmerc",
                           lon_0=coords_latlon[1], lat_0=coords_latlon[0],
                           k=1,
                           x_0=0., y_0=0.,
                           units="m", datum="WGS84", ellps="WGS84",
                           towgs84="0,0,0,0,0,0,0",
                           no_defs=True)

    item = terrain.terrain_geotiff([-200, -200, 200, 200], ddd_proj, detail=15.0)
    item = item.material(ddd.mats.terrain)
    item = item.smooth(angle=math.pi/12)
    item = ddd.uv.map_cubic(item)
    item.show()

    root.append(item)

