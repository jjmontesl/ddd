# ddd - DDD123
# Library for simple scene modelling.
# Jose Juan Montes and Contributors 2019-2022

import noise
import numpy as np
import pyproj

from ddd.core.exception import DDDException
from ddd.ddd import ddd
from ddd.math.bounds import DDDBounds
from ddd.ops.height.height import HeightFunction


def polygon_from_bounds(bounds_or_obj, sides=4):
    """
    """

    if isinstance(bounds_or_obj, DDDBounds):
        bounds = bounds_or_obj
    elif isinstance(bounds_or_obj, np.ndarray):
        bounds = DDDBounds(bounds_or_obj)
    else:
        #boundsg = bounds_or_obj.flatten()
        #boundsg.children = [c for c in boundsg.children if isinstance(c, DDDObject3)]
        #bounds = boundsg.bounds()
        bounds = bounds_or_obj.bounds()

    # Get bounds (workaround as currently bounds fail as there are 2D objects mixed)

    radius = bounds.diagonal().length() / 2
    margin = 12

    polygon = ddd.regularpolygon(sides, r=radius + margin).rotate(ddd.PI_OVER_2)
    polygon = polygon.translate(bounds.center())
    return polygon

    #bounds = [bounds[0][0] - margin, bounds[0][1] - margin, bounds[1][0] + margin, bounds[1][1] + margin]
    #surroundings = grid.terrain_grid(bounds, height=3.0, detail=2.0, scale=0.1).translate([0, 0, 0.5]).material(mat_terrain)
    #surroundings = surroundings.translate([0, 0, -2])


def shape_to_grid(obj, interval=2.0, name="Shaped Grid"):
    grid = ddd.grid2(obj.bounds(), interval, name=name)
    grid = grid.individualize().intersection(obj)
    return grid

def grid_to_mesh(grid):
    grid = grid.triangulate()
    grid = grid.combine()
    grid = grid.merge_vertices()
    return grid


class PerlinTerrainRandomHeightFunction(HeightFunction):

    def __init__(self, height=1.0, scale=0.025):
        super().__init__()
        self.height = height
        self.scale = scale

    def vertex_function(self, x, y, z, idx):
        h = self.height * noise.pnoise2(x * self.scale, y * self.scale, octaves=3, persistence=0.5, lacunarity=1.0, repeatx=1024, repeaty=1024, base=0)
        return (x, y, z + h)


def terrain_height_simple_random(mesh, height=1.0, scale=0.025):

    height_func = PerlinTerrainRandomHeightFunction(height, scale)
    mesh = mesh.vertex_func(height_func.vertex_function)
    #mesh = mesh.merge_vertices()
    mesh = mesh.smooth()
    return mesh



def terrain_grid(bounds, detail=1.0, height=1.0, scale=0.025):
    '''
    If bounds is a single number, it's used as L1 distance.
    '''

    if isinstance(bounds, float):
        distance = bounds
        bounds = [-distance, -distance, distance, distance]

    mesh = ddd.grid3(bounds, detail=detail, name="Terrain grid")
    func = lambda x, y: 2.0 * noise.pnoise2(x, y, octaves=3, persistence=0.5, lacunarity=2.0, repeatx=1024, repeaty=1024)
    mesh = mesh.elevation_func(func)

    return mesh



