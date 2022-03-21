# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging
import math
import random

from csg import geom as csggeom
from csg.core import CSG
import numpy as np
from shapely import geometry, affinity, ops
from shapely.geometry import shape
from trimesh import creation, primitives, boolean, transformations
import trimesh
from trimesh.base import Trimesh
from trimesh.path import segments
from trimesh.path.path import Path, Path3D
from trimesh.scene.scene import Scene, append_scenes
from trimesh.visual.material import SimpleMaterial
import copy
from trimesh.visual.texture import TextureVisuals
from matplotlib import colors
import json
import base64
from shapely.geometry.polygon import orient
from ddd.ddd import ddd, DDDObject3


# Get instance of logger for this module
logger = logging.getLogger(__name__)

class DDDHelper():

    def all(self, size=20.0, plane_xy=True, grid_yz=True, grid_xz=True, grid_space=2.0, center=None, around_center=False):

        objs = ddd.group3(name="Helper grid")

        if plane_xy:
            objs.append(self.plane_xy(size))
        if grid_yz:
            objs.append(self.grid_yz(size, grid_space))
        if grid_xz:
            objs.append(self.grid_xz(size, grid_space))

        objs = objs.combine()

        if center is None:
            center = [0, 0, 0]
        objs = objs.translate([-center[0], -center[1], -center[2] if len(center) > 2 else 0])

        if around_center:
            objs = objs.translate([-size / 2, -size / 2, 0])

        return objs

    def plane_xy(self, size=10.0):
        obj = ddd.rect([0, 0, size, size], name="Helper plane XY").triangulate()
        return obj

    def grid_yz(self, size=10.0, grid_space=1.0):
        gw = 0.05
        grid = ddd.group3(name="Helper grid YZ")
        for i in range(int(size / grid_space) + 1):
            line1 = ddd.box([0, i * grid_space, 0, 0 + gw, i * grid_space + gw, size])
            grid.append(line1)
        for j in range(int(size / grid_space) + 1):
            line2 = ddd.box([0, 0, j * grid_space, 0 + gw, size, j * grid_space + gw])
            grid.append(line2)
        grid = grid.combine()
        return grid

    def grid_xz(self, size=10.0, grid_space=1.0):
        gw = 0.05
        grid = ddd.group3(name="Helper grid XZ")
        for i in range(int(size / grid_space) + 1):
            line1 = ddd.box([i * grid_space, 0, 0, i * grid_space + gw, 0 + gw, size])
            grid.append(line1)
        for j in range(int(size / grid_space) + 1):
            line2 = ddd.box([0, 0, j * grid_space, size, 0 + gw, j * grid_space + gw])
            grid.append(line2)
        grid = grid.combine()
        return grid






