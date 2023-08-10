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
Generates roofs, given a footprint shape.
"""


def roof_gabled(obj, roof_buffer=0.0):
    """
    Creates a gabled roof for the given footprint.

    The base of the gabled roof keeps the footprint shape, even if irregular.
    """

    base = obj
    
    if roof_buffer:
        base = base.buffer(roof_buffer)
    
    roof_height = 1.2  # default_height = random.uniform(3.0, 4.0)
    #roof_height = roof_height if roof_height else default_height
    roof_thick = 0.2
    orientation = "major"
    #if part.extra.get("osm:roof:orientation", "along") == "across": orientation = "minor"

    (axis_major, axis_minor, axis_rot) = ddd.geomops.oriented_axis(base)
    axis_line = axis_major if orientation == "major" else axis_minor

    #half_profile = ddd.polygon(([])
    
    roof = base.extrude_step(axis_line, roof_height)  #.material(roof_material)
    roof = roof.subtract(roof.translate([0, 0, -roof_thick]))
    roof = roof.clean()

    roof = roof.smooth(ddd.PI_OVER_8)
    roof = ddd.uv.map_cubic(roof)

    return roof