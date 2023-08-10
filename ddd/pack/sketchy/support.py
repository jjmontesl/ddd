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
import numpy as np

from ddd.ddd import ddd
from ddd.core.exception import DDDException
from ddd.math.transform import DDDTransform


"""
"""


# Get instance of logger for this module
logger = logging.getLogger(__name__)


def fixture_round_wall(r=0.05, depth=0.02, resolution=3):
    """
    """
    obj1 = ddd.disc(r=r, resolution=resolution, name="Fixture Round Wall")
    obj2 = obj1.scale([0.9, 0.9])
    obj = obj1.extrude_step(obj2, depth)
    
    obj = obj.material(ddd.mats.steel)
    obj = ddd.uv.map_cylindrical(obj)

    obj = obj.rotate(ddd.ROT_FLOOR_TO_FRONT)

    slot_default = DDDTransform()
    slot_default.translate([0, -depth, 0])

    obj.set('ddd:slots', {
        'default': slot_default
    })

    return obj


def arm_pole_simple(length=0.4, thick=0.02):
    """
    """
    obj = ddd.rect([thick, length], name="Arm Pole").extrude(thick)
    obj = obj.translate([-thick * 0.5, -length, -thick * 0.5])
    obj = obj.material(ddd.mats.steel)
    obj = ddd.uv.map_cubic(obj)

    slot_default = DDDTransform()
    slot_default.translate([0, -length, 0])
    
    slot_below = DDDTransform()
    slot_below.translate([0, -length * 0.85, -thick * 0.5])

    obj.set('ddd:slots', {
        'default': slot_default,
        'below': slot_below
    })

    return obj


def arm_pole_forge(length=0.4):
    return arm_pole_simple(length=length)


def arm_flat_wall(length=0.4):
    """
    TODO: Create a curve with a generic shape constructor, transform to line.
    Construct a flat rect shape and extrude along the curve (other shapes can be used to construct poles). Generalize.
    """
    pass

# look into urban / lamp mast uses 3 angled arms
#def arm_angled()