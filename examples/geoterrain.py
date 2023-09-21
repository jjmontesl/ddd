# ddd - DDD123
# Library for simple scene modelling.
# Jose Juan Montes and Contributors 2019-2021

import math

import pyproj

from ddd.ddd import ddd
from ddd.geo import terrain
from ddd.pipeline.decorators import dddtask


@dddtask()
def pipeline_start(pipeline, root):
    """
    Generate a terrain mesh from a DEM.
    """

    # Latitude and Longitude (EPSG:4326 - WGS84)
    coords_latlon = [42.232606, -8.726203]  # Vigo

    # Create a UTM projection centered on the target coordinates
    ddd_proj = pyproj.Proj(proj="tmerc",
                           lon_0=coords_latlon[1], lat_0=coords_latlon[0],
                           k=1,
                           x_0=0., y_0=0.,
                           units="m", datum="WGS84", ellps="WGS84",
                           towgs84="0,0,0,0,0,0,0",
                           no_defs=True)

    item = terrain.terrain_geotiff([[-200, -200, 0], [200, 200, 0]], ddd_proj, detail=15.0)
    #item = item.material(ddd.mats.terrain)
    item = item.material(ddd.MAT_TEST)
    item = item.smooth(angle=math.pi/12)
    item = ddd.uv.map_cubic(item, scale=[1 / 10, 1 / 10])
    item.show()


    # Rocky area
    area_2d_outline = ddd.disc(r=100)
    area_border_mask_func = lambda x, y, z, i: (ddd.point((x, y, z)).distance(area_2d_outline) < 0.2)
    noise_rocky_func = lambda x, y, z, i, o: [x + ddd.random.uniform(-2, 2), y + ddd.random.uniform(2, 2), z + ddd.random.uniform(-5.0, 20) ]
    #(terrain.terrain_noise(x, y, z, scale=0.1, octaves=3, persistence=0.5, lacunarity=2.0) - 0.5) * 0.1
    area_3d = item.merge_vertices().vertex_func(noise_rocky_func, mask=area_border_mask_func)
    area_3d = ddd.uv.map_cubic(area_3d, scale=[1 / 10, 1 / 10])
    area_3d.show()

    root.append(item)

