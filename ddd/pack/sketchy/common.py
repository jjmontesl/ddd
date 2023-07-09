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


# Get instance of logger for this module
logger = logging.getLogger(__name__)


"""
Partial general purpose shapes and parts of other objects.
"""

def bar_u(height=0.8, width=0.4, r=0.15, thick=0.1):
    """
    A U-shaped figure, like that used for handles, bycicle stands...

    Oriented with arc up, like a bike parking.
    """

    if r >= width / 2:
        raise DDDException("Radius is too big for width")

    vertical_height = height - r

    base = ddd.regularpolygon(6, r=thick * 0.5, name="U-Shape")

    path = ddd.point().line_to([0, vertical_height]).arc_to([r, height], [r, vertical_height], True, resolution=1)
    path = path.line_to([width - r, height]).arc_to([width, vertical_height], [width-r, vertical_height], True, resolution=1)
    path = path.line_to([width, 0])

    item = base.extrude_along(path)
    item = item.rotate(ddd.ROT_FLOOR_TO_FRONT)  #.rotate(ddd.ROT_TOP_CW)
    item = item.translate([-width*0.5, 0, 0])
    item = item.material(ddd.mats.steel)
    item = ddd.uv.map_cubic(item)
    return item


def planks_crossed(width, height, beam_thick=0.05, beam_width = 0.075):

    beams = ddd.group2()

    face = ddd.rect([0, 0, width, height])

    beams.append(ddd.rect([beam_width / 2, beam_width / 2, width - beam_width / 2, height - beam_width / 2]).outline())
    beams.append(ddd.line([[beam_width / 2, beam_width / 2], [width - beam_width / 2, height - beam_width / 2]]))
    beams.append(ddd.line([[beam_width / 2, height - beam_width / 2], [width - beam_width / 2, beam_width / 2]]))
    beams = beams.buffer(beam_width).union().intersection(face)
    beams = beams.extrude(beam_thick)

    return beams


def ring(r=1.0, thick_r=0.1, height_flatten=0.5, sides=6):

    shape = ddd.regularpolygon(sides, r=thick_r)
    shape = shape.scale([1, height_flatten])
    shape = shape.translate([r, 0])

    ring = shape.revolve()

    return ring

