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

"""
Framework and functions for height mapping of different accidents or strategies, e.g. for terrain or meshes, or points.

These functions are based on mapping XY coordinates to height, in a manner that can be combined with other
mapping functions to generate a complete height map. They shall fade to 0 beyond their respective range.

These include support for bumps, and mapping of heights across Paths / LineStrings (see pathheight).

Geometry needs to be prepared for, or subdivided before applying these functions.
"""

# Get instance of logger for this module
logger = logging.getLogger(__name__)



class HeightFunction():
    """
    Base class for height functions (or, more precisely, '1d value' functions), that map XY(Z) coordinates to a value.
    """

    def value(self, x, y, z, idx=None, o=None) -> float:
        """
        Returns the function value for the given coordinates.
        """
        raise NotImplementedError()

    def vertex_function(self, x, y, z, idx=None, obj=None):
        """
        Default vertex function implementation, which calls value and ADDS height to Z.
        """
        height_val = self.value(x, y, z, idx, obj)
        return (x, y, z + height_val)


class ConstantHeightFunction(HeightFunction):
    """
    A height function that combines several height functions (adding their results).
    """

    def __init__(self, value=0):
        self.constant_value = value
    
    def value(self, x, y, z, idx=None, o=None):
        return self.constant_value


class CompositeHeightFunction(HeightFunction):
    """
    A height function that combines several height functions (adding their results).
    """

    def __init__(self, functions):
        self.functions = functions
    
    def value(self, x, y, z, idx=None, o=None):
        result = 0
        for function in self.functions:
            result = result + function.value(x, y, result, idx, o)
        return result


def height_func_bump(coords, center, r, h):
    dif = (coords[0] - center[0], coords[1] - center[1])
    d = math.sqrt(dif[0] * dif[0] + dif[1] * dif[1])
    d = DDDMath.clamp(d, 0, r)
    return h * (1.0 - d / r)

def height_func_bump_smooth(coords, center, r, h):
    dif = (coords[0] - center[0], coords[1] - center[1])
    d = math.sqrt(dif[0] * dif[0] + dif[1] * dif[1])
    f = DDDMath.smoothstep(0.1, 0.9, d / r)
    return h * (1.0 - f)
