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
import numpy as np

from ddd.math.math import DDDMath
from ddd.ops.height.height import HeightFunction
from ddd.geo.elevation import ElevationModel
from ddd.geo import terrain

"""
Framework and functions for height mapping of different accidents or strategies, e.g. for terrain or meshes, or points.

These functions are based on mapping XY coordinates to height, in a manner that can be combined with other
mapping functions to generate a complete height map. They shall fade to 0 beyond their respective range.

These include support for bumps, and mapping of heights across Paths / LineStrings (see pathheight).

Geometry needs to be prepared for, or subdivided before applying these functions.
"""

# Get instance of logger for this module
logger = logging.getLogger(__name__)



class ElevationModelHeightFunction(HeightFunction):
    """
    A height function that returns elevation data from elevation model.
    """

    def __init__(self, ddd_proj, terrain_offset=0.0):
        self.ddd_proj = ddd_proj
        self.terrain_offset = terrain_offset

    def value(self, x, y, z, idx=None, o=None):
        elevation = ElevationModel.instance()
        world_xyz = x, y, z
        height_val = elevation.value(terrain.transform_ddd_to_geo(self.ddd_proj, [world_xyz[0], world_xyz[1]])) + self.terrain_offset
        return height_val


