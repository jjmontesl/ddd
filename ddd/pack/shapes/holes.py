# DDD(123) - Library for procedural generation of 2D and 3D geometries and scenes
# Copyright (C) 2021 Jose Juan Montes
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import logging
import math
import random
import re

from pycatenary.cable import MooringLine
import numpy as np
from trimesh import transformations

from ddd.ddd import ddd
from ddd.lighting.lights import PointLight
from ddd.materials.atlas import TextureAtlasUtils
from ddd.ops import filters, extrusion
from ddd.ops.extrusion import extrude_step_multi, extrude_dome
from ddd.pack.sketchy import interior, vehicles
from ddd.text.text3d import Text3D


# Get instance of logger for this module
logger = logging.getLogger(__name__)

def hole_broken(width=0.7, height=1.8, noise_scale = 0.1):

    noise_subdivision = noise_scale * 2.1

    shape = ddd.rect([width, height], name="Hole Broken")
    shape = ddd.geomops.subdivide_to_size(shape, max_edge=noise_subdivision)
    shape = filters.noise_random(shape, scale=noise_scale)
    shape = shape.clean(eps=0.02)

    return shape

def hole_bricks_missing():
    pass