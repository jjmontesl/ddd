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
from ddd.pack.sketchy import common


# Get instance of logger for this module
logger = logging.getLogger(__name__)



def lamp_case(height=0.5, r=0.30):
    lamp_shape = ddd.point(name="Lamp Case").buffer(r - 0.10, resolution=1)
    lamp = lamp_shape.extrude_step(lamp_shape.buffer(0.10, cap_style=ddd.CAP_SQUARE, join_style=ddd.JOIN_BEVEL), height * 0.8)
    lamp = lamp.extrude_step(lamp_shape.buffer(-0.10), height * 0.2)
    lamp = lamp.merge_vertices().smooth()
    lamp = lamp.material(ddd.mats.lightbulb)
    lamp = ddd.collision.aabox_from_aabb(lamp)
    lamp = ddd.uv.map_spherical(lamp, split=True)

    # TODO: Possibly add this with styling too, although lights are first class citizens (used for render)
    light = PointLight([0, 0, height * 0.8], name="Lamp Light", color="#e4e520", radius=18, intensity=1.25, enabled=False)

    lamp_case = ddd.group([lamp, light], name="Lamp Case and Light")

    return lamp_case


def lamp_ball(r=0.25):
    lamp = ddd.sphere(r=r, subdivisions=1)  # .scale([1.0, 1.0, 1.2])
    lamp = lamp.material(ddd.mats.lightbulb)
    return lamp



def lamp_block_based(length=0.8, width=0.15, height=0.10, color="#ffffff", empty=False):
    """
    A light on a floor with an angled beam. Length along X, centered on XY, lying on Z.
    """

    # Front with hole
    margin = 0.02
    front = ddd.rect([length, width])
    hole = ddd.line([[width / 2, width / 2], [length - width / 2, width / 2]])
    hole = hole.buffer(width / 2 - margin, cap_style=ddd.CAP_ROUND, resolution=3)
    #front_hole = front.subtract(hole)
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

    if not empty:
        lightpanel = hole.triangulate().translate([0, 0, height - margin * 0.95])
        lightpanel = lightpanel.material(ddd.mats.light_yellow)
        lightpanel = ddd.uv.map_cubic(lightpanel)

        lightpos = [length / 2, width / 2, height - margin / 2]
        light = PointLight(lightpos, name="Lamp Floor Light", color=color, radius=length * 4, intensity=1.0, enabled=True)
        lamp = ddd.group3([obj, lightpanel, light], name="Lamp Floor")
    else:
        lamp = ddd.group([obj], name="Lamp Floor Empty")

    lamp = lamp.recenter(onplane=True)

    return lamp

def lamp_block_based_bevel(length=0.8, width=0.15, bevel=[0.025, 0.025], height=0.10, color=[1.0, 1.0, 1.0], empty=False):

    if isinstance(bevel, (float, int)):
        bevel = [bevel, bevel]

    lamp = lamp_block_based(length - bevel[0] * 2, width - bevel[1] * 2, height, color, empty=empty)

    def remap_vertices_to_corner(x, y, z, idx, o):
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


def lamp_lantern_cap(height=0.2):
    """
    A lantern top cap, to reflect light downwards and provide a support from above (for ceiling or side mounts).
    """

    # Cap revolution profile is constructed with an arbitrary ~4 x 2.9 shape, then scaled to desired height
    larger_radius = 3.5  # Ref: 4.0
    lamp_cap_profile = (
        ddd.point().arc_to([1, -1], [0, -1], False).line_to([1.1, -1.0]).line_to([1.1, -1.1]).
        line_to([1.2, -1.1]).line_to([1.2, -1.2]).
        line_to([2.0, -2.0]).line_to([2.0, -2.2]).
        line_to([2.2, -2.3]).line_to([larger_radius, -2.9]).

        line_to([larger_radius - 0.01, -2.91]).line_to([2.19, -2.31]).
        line_to([2.0, -2.21]).line_to([1.99, -2.01]).
        line_to([0, -2.01]).line_to([0, 0])
    )

    # Rescale to unit height, and then back
    factor = 1 / 2.9 * height
    lamp_cap_profile = lamp_cap_profile.scale([factor, factor])
    
    lamp_cap = lamp_cap_profile.revolve()

    lamp_cap = lamp_cap.smooth(ddd.PI_OVER_3)
    #lamp_cap = lamp_cap.flip_faces()
    lamp_cap = lamp_cap.material(ddd.mats.metal)
    lamp_cap = ddd.uv.map_cubic(lamp_cap)


    return lamp_cap

def lamp_lantern_case_grid_top(height=0.5, r=0.30):
    """
    A cylindrical grid (rounded on the bottom) to cover a light source.
    """

    ubar = common.bar_u(height=0.34, width=0.2, r=0.08, thick=0.0225)
    ubar2 = ubar.copy().rotate([0, 0, ddd.PI_OVER_2])
    ubar = ubar.append(ubar2).combine().rotate([0, ddd.PI, 0])
    ubar = ubar.translate([0, 0, -0.135])

    #ubar.show()

    ring = common.ring(0.1, 0.02)
    ring1 = ring.copy().translate([0, 0, -0.2])
    ring2 = ring.copy().translate([0, 0, -0.3])
    ring3 = ring.copy().translate([0, 0, -0.4])
    ubar.append([ring1, ring2, ring3])

    #lamp = lamp.extrude_step(lamp_shape.buffer(-0.10), height * 0.2)
    #lamp = lamp.merge_vertices().smooth()
    #lamp = lamp.material(ddd.mats.lightbulb)
    #lamp = ddd.collision.aabox_from_aabb(lamp)
    #lamp = ddd.uv.map_spherical(lamp, split=True)

    # TODO: Possibly add this with styling too, although lights are first class citizens (used for render)
    #light = PointLight([0, 0, height * 0.8], name="Lamp Light", color="#e4e520", radius=18, intensity=1.25, enabled=False)

    #lamp_case = ddd.group([lamp, light], name="Lamp Case and Light")
    lamp_case = ubar
    lamp_case.setname('Lantern Case')

    return lamp_case

def lamp_lantern_case_grid_front(height=0.40, width=0.20, thick=0.18):
    
    bar_margin = 0.03

    ubarv1 = common.bar_u(height=thick, width=height, r=0.03, thick=0.0225).rotate([0, 0, ddd.PI_OVER_2]).translate([-width / 2 + bar_margin, 0, 0])
    ubarv2 = ubarv1.copy().translate([width - 2 * bar_margin, 0, 0])
    
    ubarh1 = common.bar_u(height=thick, width=width, r=0.03, thick=0.0225).translate([0, -height / 2 + bar_margin, 0])
    ubarh2 = ubarh1.copy().translate([0, height - 2 * bar_margin, 0])

    grid = ubarv1.append([ubarv2, ubarh1, ubarh2]).combine()
    grid = grid.material(ddd.mats.metal)
    grid = ddd.uv.map_cubic(grid)

    return grid


def lamp_bulb_capsule(height=0.2, r=0.05):
    obj = ddd.point().arc_to([r, r], [0, r], True).line_to([r, height]).line_to([0, height]).translate([0, -height])
    obj = obj.revolve().flip_faces()
    obj = obj.material(ddd.mats.light_yellow)  # ddd.mats.lightbulb
    obj = ddd.uv.map_spherical(obj, split=False)
    return obj


def lamp_lantern():  # length=0.8, width=0.15, bevel=[0.10, 0.10], color=[1.0, 1.0, 1.0]):
    # Ref: https://www.artstation.com/artwork/QzDmo3
    
    lamp_cap = lamp_lantern_cap()
    lamp_grid = lamp_lantern_case_grid_top()
    
    lamp = lamp_grid.append(lamp_cap)
    lamp = lamp.combine()
    lamp = lamp.material(ddd.mats.metal)
    lamp = lamp.merge_vertices().smooth(ddd.PI_OVER_3)
    #lamp = ddd.uv.map_cubic(lamp)

    lamp_bulb = lamp_bulb_capsule(height=0.25)
    lamp_bulb = lamp_bulb.translate([0, 0, -0.135])
    lamp = lamp.append(lamp_bulb)

    lamp_glass_cover = lamp_bulb_capsule(height=0.30, r=0.075)
    lamp_glass_cover = lamp_glass_cover.translate([0, 0, -0.135])
    lamp_glass_cover = lamp_glass_cover.material(ddd.mats.glass)
    lamp = lamp.append(lamp_glass_cover)

    lamp = lamp.translate([0, 0, 0.03])  # center on the inside of the top dome

    #lamp.show()
    return lamp


def lamp_lantern_wall(length=0.8, width=0.15, bevel=[0.10, 0.10], color=[1.0, 1.0, 1.0]):
    # TODO: do not create specific wall arm, use slots/connectors instead
    obj = lamp_lantern(length=length, width=width, bevel=bevel, color=color)
    return obj


def lamp_lantern_grid(height=0.40, width=0.20, thick=0.16, color=[1.0, 1.0, 1.0]):
    
    round = 0.05
    margin = 0.025
    base = ddd.rect(([-width / 2, -height / 2], [width / 2, height / 2]))
    base = base.buffer(-round).buffer(round, join_style=ddd.JOIN_ROUND)
    base = base.extrude(0.02)

    grid = lamp_lantern_case_grid_front(height=height - margin * 2, width=width - margin * 2, thick=thick)

    obj = base.append(grid)
    obj = obj.rotate(ddd.ROT_FLOOR_TO_FRONT)
    obj = obj.combine().material(ddd.mats.metal)
    base = ddd.uv.map_cubic(base)

    support = ddd.box([0, 0, 0, 0.10, 0.125, 0.02]).translate([-0.05, -0.02 - 0.125, 0.11])
    obj.append(support)

    lamp_bulb = lamp_bulb_capsule(height=0.22)
    lamp_bulb = lamp_bulb.translate([0, -0.09, 0.11])
    obj.append(lamp_bulb)
    
    #obj.show()
    return obj


def skylight_grid(length=0.60, width=0.40, thick=0.05, round=0.05, color=[1.0, 1.0, 1.0]):
    """
    A simple square skylight "box" with a tight grid on top of a glass / light plane, for diffuse lighting.
    """
    margin = 0.025
    border_width = 0.03
    grid_width = 0.02
    grid_spacing = 0.05

    base = ddd.rect(([-width / 2, -length / 2], [width / 2, length / 2]))
    if round:
        base = base.buffer(-round).buffer(round, join_style=ddd.JOIN_ROUND)
        
    interior = base.buffer(-border_width)
    
    base = base.subtract(interior)
    base = base.extrude(thick)

    #grid_over = lamp_lantern_case_grid_front(height=height - margin * 2, width=width - margin * 2, thick=thick)

    grid = ddd.grid2(interior.bounds(), detail=grid_spacing, adjust=True)
    grid = grid.outline().buffer(grid_width / 2).union().intersection(interior).clean(eps=-0.001)
    grid = grid.extrude(thick / 4).translate([0, 0, thick / 4])

    obj = base.append(grid)
    #obj = obj.rotate(ddd.ROT_FLOOR_TO_FRONT)
    obj = obj.combine().material(ddd.mats.metal)
    base = ddd.uv.map_cubic(base)

    light_box = interior.extrude(thick / 4)
    light_box = light_box.material(ddd.mats.lightbulb)
    #light_box = lamp_bulb.translate([0, -0.09, 0.11])
    obj.append(light_box)

    obj = obj.rotate([ddd.PI, 0, 0])

    #obj.show()
    return obj
