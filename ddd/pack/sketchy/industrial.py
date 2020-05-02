# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging
import random
import numpy as np

from ddd.ddd import ddd
from ddd.pack.sketchy.urban import post, lamp_ball

def crane_vertical():

    base_width = 7
    base_length = 6

    # Piers
    pier_height = 2.0
    pier_width = 1.5
    pier_length = base_length + 2
    pier = ddd.rect([-pier_width / 2, -pier_length / 2, pier_width / 2, pier_length / 2], name="Crane Pier")
    pier = pier.extrude(pier_height).material(ddd.mats.metal_paint_red)
    pier = ddd.uv.map_cubic(pier)

    pier_l = pier.translate([-base_width * (2/6), 0, 0])
    pier_r = pier.translate([base_width * (2/6), 0, 0])
    piers = ddd.group3([pier_l, pier_r], name="Crane Piers")

    # Base
    base_height = 1.5
    base = ddd.rect([0, 0, base_width, base_length], name="Crane Base").recenter()
    base = base.extrude(base_height).translate([0, 0, pier_height])
    base = base.material(ddd.mats.cement)
    base = ddd.uv.map_cubic(base)

    # Base Tower
    column_height = 8
    column_radius_base = base_width * 0.85 * 0.5
    column_radius = column_radius_base * 0.5
    column_shape_base = ddd.regularpolygon(4, column_radius_base)
    column_shape_middle = ddd.regularpolygon(12, column_radius)
    column = column_shape_base.extrude_step(column_shape_middle, 1, base=False)
    column = column.extrude_step(column_shape_middle, column_height - 1, cap=False)
    column = column.translate([0, 0, pier_height + base_height]).material(ddd.mats.metal_paint_red)
    column = ddd.uv.map_cubic(column)
    column.name = "Crane column"

    # Platform and railing
    platform_radius = column_radius + 0.85
    platform_base_height = pier_height + base_height + column_height - 2.0
    platform_shape = ddd.point(name="Crane platform").buffer(platform_radius, cap_style=ddd.CAP_ROUND)
    platform = platform_shape.triangulate(twosided=True)
    platform = platform.material(ddd.mats.metallic_grid)
    platform_fence = platform_shape.outline().extrude(1.2).material(ddd.mats.fence)
    platform = ddd.group([platform, platform_fence], name="Crane platform")
    platform = ddd.uv.map_cylindrical(platform)
    platform = platform.translate([0, 0, platform_base_height])

    # WeightBlock
    block_width = base_width * 0.6
    block_length = base_length * 1.25
    block_base_height = pier_height + base_height + column_height
    block_height = 2.2
    block = ddd.rect([-block_width / 2, 0, block_width / 2, block_length], name="Crane Weight")
    block = block.extrude(block_height).translate([0, -2.5, block_base_height]).material(ddd.mats.cement)
    block = ddd.uv.map_cubic(block)

    # Cabin
    cabin_width = block_width * 0.6
    cabin_length = 4
    cabin_height = block_height
    cabin_shape = ddd.rect([-block_width * 0.5, 0, block_width * 0.5, cabin_length])
    cabin_shape_top = ddd.rect([-block_width * 0.5, 1, block_width * 0.5, cabin_length])
    cabin = cabin_shape.extrude_step(cabin_shape, 1)
    cabin = cabin.extrude_step(cabin_shape_top, cabin_height - 1)
    cabin = cabin.extrude_step(cabin_shape_top.buffer(-0.4), 0.4)
    cabin = cabin.material(ddd.mats.metal_paint_yellow)
    cabin = cabin.translate([0, -2.5 - cabin_length, block_base_height])
    cabin = ddd.uv.map_cubic(cabin)

    mainsupport_width = 2
    mainsupport_skew = 2
    mainsupport_height = 10
    mainsupport_base_height = block_base_height + block_height
    mainsupport = ddd.rect([0, 0, mainsupport_width, mainsupport_width], name="Main Support").recenter()
    mainsupport = mainsupport.extrude_step(mainsupport.translate([0, -mainsupport_skew]), mainsupport_height, base=False)
    mainsupport = mainsupport.material(ddd.mats.metal_paint_red)
    mainsupport = mainsupport.translate([0, 0, mainsupport_base_height])
    mainsupport = ddd.uv.map_cubic(mainsupport)

    secsupport_width = 1.5
    secsupport_skew = 11
    secsupport_height = 18
    secsupport_base_height = block_base_height + block_height
    secsupport = ddd.rect([0, 0, secsupport_width, secsupport_width], name="Sec Support").recenter()
    secsupport = secsupport.extrude_step(secsupport.scale([0.8, 0.7]).translate([0, -secsupport_skew]), secsupport_height, base=False)
    secsupport = secsupport.material(ddd.mats.metal_paint_red)
    secsupport = secsupport.translate([0, -1.5, secsupport_base_height])
    secsupport = ddd.uv.map_cubic(secsupport)

    def cable(a, b, thick=0.20):
        a = np.array(a)
        b = np.array(b)
        length = np.linalg.norm(a-b)
        cable = ddd.point(name="Cable").buffer(thick * 0.5, resolution=1, cap_style=ddd.CAP_ROUND).extrude(length + thick).translate([0, 0, -thick * 0.5])
        cable = ddd.uv.map_cylindrical(cable)
        cable = cable.translate(a)
        return cable

    maincable1 = cable([0, block_length - 3, mainsupport_base_height], [0, -mainsupport_skew, mainsupport_base_height + mainsupport_height - 0.2])
    maincable1 = maincable1.material(ddd.mats.cable_metal)

    item = ddd.group3([piers, base, column, platform,
                       block, cabin,
                       mainsupport, maincable1,
                       secsupport], name="Crane Vertical")
    return item



