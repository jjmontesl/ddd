# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import math
import random

from csg import geom as csggeom
from csg.core import CSG
import noise
import pyproj
from shapely import geometry
from shapely.geometry.polygon import LinearRing
from trimesh import creation, primitives, boolean
import trimesh
from trimesh.base import Trimesh
from trimesh.path import segments
from trimesh.path.path import Path
from trimesh.scene.scene import Scene, append_scenes
from trimesh.visual.material import SimpleMaterial

from ddd.ddd import ddd
from ddd.georaster import ElevationChunk


def map_2d_path(obj, path):
    """
    Assigns UV coordinates to a shape for a line along a path.
    This method does not create a copy of objects, affecting the hierarchy.
    """

    def uv_apply_func(x, y, z, idx):
        # Find nearest point in path
        d = path.geom.project(ddd.point([x, y, z]).geom)
        #print(x, y, z, idx, d, path)
        p, segment_idx, segment_coords_a, segment_coords_b = path.interpolate_segment(d)
        pol = LinearRing([segment_coords_a, segment_coords_b, [x, y, z]])
        return (0.1 * (-1 if pol.is_ccw else 1), d)

    result = obj
    if obj.geom:
        result.extra['uv'] = [uv_apply_func(v[0], v[1], 0.0, idx) for idx, v in enumerate(obj.geom.exterior.coords)]

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
    Apply 2D UV coordinates to 3D shapes (using UV from closest point in 2D space).
    This method does not create a copy of objects.
    """

    def uv_apply_func(x, y, z, idx):
        # Find nearest point in shape, and return its height
        closest_uv = obj_2d.extra['uv'][0]
        closest_distsqr = float('inf')
        for idx, v in enumerate(obj_2d.geom.exterior.coords):
            point_2d = [v[0], v[1], 0]
            diff = [point_2d[0] - x, point_2d[1] - y]
            distsqr = (diff[0] ** 2) + (diff[1] ** 2)
            if (distsqr < closest_distsqr):
                closest_uv = obj_2d.extra['uv'][idx]
                closest_distsqr = distsqr
        #print (closest_uv)
        return closest_uv

    result = obj_3d
    if obj_3d.mesh:
        result.extra['uv'] = [uv_apply_func(v[0], v[1], v[2], idx) for idx, v in enumerate(obj_3d.mesh.vertices)]
    result.children = [map_3d_from_2d(c, obj_2d) for c in result.children]
    return result
