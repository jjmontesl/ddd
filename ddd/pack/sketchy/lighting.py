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

import numpy as np
from trimesh import transformations

from ddd.ddd import ddd
from ddd.lighting.lights import PointLight
from ddd.ops.extrusion import extrude_step_multi, extrude_dome


# Get instance of logger for this module
logger = logging.getLogger(__name__)


def lamp_block_based(length=0.8, width=0.15, height=0.10, color="#ffffff"):
    """
    A light on a floor with an angled beam. Length along X, centered on XY, lying on Z.
    """

    # Front with hole
    margin = 0.02
    front = ddd.rect([length, width])
    hole = ddd.line([[width / 2, width / 2], [length - width / 2, width / 2]])
    hole = hole.buffer(width / 2 - margin, cap_style=ddd.CAP_ROUND, resolution=3)
    front_hole = front.subtract(hole)
    #front_hole.show()

    obj = front.extrude_step(front.scale([1, 1]), height, base=False)
    #obj = obj.extrude_step(front_hole, 0, method=ddd.EXTRUSION_METHOD_SUBTRACT, cap=False)
    obj = obj.extrude_step(hole, 0, method=ddd.EXTRUSION_METHOD_SUBTRACT)
    obj = obj.extrude_step(hole, -margin, method=ddd.EXTRUSION_METHOD_SUBTRACT, cap=False)
    obj.fix_normals()
    obj = obj.smooth()

    #obj = obj.flip_faces()
    obj = obj.material(ddd.mats.metal)
    obj = ddd.uv.map_cubic(obj)

    lightpanel = hole.triangulate().translate([0, 0, height - margin * 0.95])
    lightpanel = lightpanel.material(ddd.mats.light_yellow)
    lightpanel = ddd.uv.map_cubic(lightpanel)

    lightpos = [length / 2, width / 2, height + width]  # light is positioned 2 * width above top
    light = PointLight(lightpos, name="Lamp Floor Light", color=color, radius=length * 4, intensity=1.25, enabled=True)

    lamp = ddd.group3([obj, lightpanel, light], name="Lamp Floor")
    lamp = lamp.recenter(onplane=True)

    return lamp

def lamp_block_based_bevel(length=0.8, width=0.15, bevel=[0.025, 0.025], height=0.10, color=[1.0, 1.0, 1.0]):

    if isinstance(bevel, (float, int)):
        bevel = [bevel, bevel]

    lamp = lamp_block_based(length - bevel[0] * 2, width - bevel[1] * 2, height, color)

    def remap_vertices_to_corner(x, y, z, idx):
        if z == 0:
            if y < 0:
                y = y - bevel[1]
            elif y > 0:
                y = y + bevel[1]
            if x < 0:
                x = x - bevel[0]
            elif x > 0:
                x = x + bevel[0]
        return (x, y, z)

    lamp = lamp.vertex_func(remap_vertices_to_corner)
    lamp = lamp.recenter(onplane=True)

    #lamp.show()
    return lamp

def lamp_block_based_angled_corner(length=0.8, width=0.15, bevel=[0.10, 0.10], color=[1.0, 1.0, 1.0]):
    raise NotImplementedError()

