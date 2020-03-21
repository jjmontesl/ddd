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
from trimesh.path.path import Path
from trimesh.scene.scene import Scene, append_scenes
from trimesh.visual.material import SimpleMaterial
from trimesh.scene.transforms import TransformForest
import copy
from trimesh.visual.texture import TextureVisuals
from matplotlib import colors
import json
import base64
from shapely.geometry.polygon import orient


# Get instance of logger for this module
logger = logging.getLogger(__name__)

class DDDDistribute():

    def grid(self, obj, space=5.0, width=None):

        if width is None:
            width = int(math.sqrt(len(obj.children)))

        result = []
        for idx, c in enumerate(obj.children):
            col = idx % width
            row = int(idx / width)
            pos = [col * space, row * space, 0.0]
            result.append(c.translate(pos))
            col += 1

        obj.children = result

        return obj




