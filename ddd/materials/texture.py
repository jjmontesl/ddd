# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

from shapely import geometry
from trimesh.path import segments
from trimesh.scene.scene import Scene, append_scenes
from trimesh.base import Trimesh
from trimesh.path.path import Path
from trimesh.visual.material import SimpleMaterial
from trimesh import creation, primitives, boolean
import trimesh
from csg.core import CSG
from csg import geom as csggeom
import random
from ddd.ddd import ddd
import noise
from ddd.georaster import ElevationChunk
import pyproj
import math


def map_2d_path(obj, path):
    """
    Assigns UV coordinates to a shape for a line along a path.
    This method does not create a copy of objects, affecting the hierarchy.
    """

    def height_apply_func(x, y, z, idx):
        # Find nearest point in path, and return its height
        d = path.geom.project(ddd.point([x, y, z]).geom)
        p, segment_idx, segment_coords_a, segment_coords_b = path.interpolate_segment(d)

        dir_vec = (segment_coords_b[0] - segment_coords_a[0], segment_coords_b[1] - segment_coords_a[1])
        dir_vec_length = math.sqrt(dir_vec[0] ** 2 + dir_vec[1] ** 2)
        dir_vec = (dir_vec[0] / dir_vec_length, dir_vec[1] / dir_vec_length)
        angle = math.atan2(dir_vec[1], dir_vec[0])

        return (0.1 * random.choice([-1, 1]), d)

    result = obj
    result.extra['uv'] = [height_apply_func(v[0], v[1], 0.0, idx) for idx, v in enumerate(obj.geom.exterior.coords)]

    result.children = [map_2d_path(c, path) for c in obj.children]
    return result

def map_3d_random(obj_3d):
    """
    Assigns UV coordinates at random.
    This method does not create a copy of objects, affecting the hierarchy.
    """
    result = obj_3d
    result.extra['uv'] = [(random.uniform(0, 1), random.uniform(0, 1)) for v in result.mesh.vertices]
    result.children = [map_3d_random(c) for c in result.children]
    return result


def map_3d_from_2d(obj_3d, obj_2d):
    """
    """
    #print(obj_2d.extra)
    path = obj_2d.extra['way_1d']

    def height_apply_func(x, y, z, idx):
        # Find nearest point in path, and return its height
        d = path.geom.project(ddd.point([x, y, z]).geom)
        closest_segment = path.interpolate_segment(d)
        #print ("%s, %s, %s => %s, %s" % ( x, y, z, 0.05 * random.choice([-1, 1]), d / 10.0))
        return (0.1 * random.choice([-1, 1]), d / 10.0)

    result = obj_3d
    result.extra['uv'] = [height_apply_func(v[0], v[1], v[2], idx) for idx, v in enumerate(obj_3d.mesh.vertices)]
    result.children = [map_3d_from_2d(c, obj_2d) for c in result.children]
    return result


