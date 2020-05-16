# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging
import random
import numpy as np

from ddd.ddd import ddd
from ddd.pack.sketchy.urban import post, lamp_ball
import math
from trimesh import transformations


def crane_vertical():
    """
    Large vertical crane (such as those seen in cargo ports).
    Inspired by: https://commons.wikimedia.org/wiki/File:Port_crane_of_Mammoet,_Schiedam-8054.jpg
    """

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
    cabin_length = 3
    cabin_height = block_height
    cabin_shape = ddd.rect([-block_width * 0.5, 0, block_width * 0.5, cabin_length])
    cabin_shape_top = ddd.rect([-block_width * 0.5, 1, block_width * 0.5, cabin_length])
    cabin = cabin_shape.extrude_step(cabin_shape, 1)
    cabin = cabin.extrude_step(cabin_shape_top, cabin_height - 1)
    cabin = cabin.extrude_step(cabin_shape_top.buffer(-0.4), 0.3)
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

    maincable1 = cable([-block_width * 0.4, block_length - 3, mainsupport_base_height], [-mainsupport_width * 0.2, -mainsupport_skew, mainsupport_base_height + mainsupport_height - 0.2])
    maincable1 = maincable1.material(ddd.mats.cable_metal)
    maincable2 = cable([block_width * 0.4, block_length - 3, mainsupport_base_height], [mainsupport_width * 0.2, -mainsupport_skew, mainsupport_base_height + mainsupport_height - 0.2])
    maincable2 = maincable2.material(ddd.mats.cable_metal)

    seccable1 = cable([0, -mainsupport_skew, mainsupport_base_height + mainsupport_height], [0, -1.5 - secsupport_skew, mainsupport_base_height + secsupport_height - 0.2])
    seccable1 = seccable1.material(ddd.mats.cable_metal)

    # Drag cable
    dragcable_length = 20
    dragcable_point = [0, -1.5 - secsupport_skew, mainsupport_base_height + secsupport_height - 0.2]
    dragcable_endpoint = [0, -1.5 - secsupport_skew, mainsupport_base_height + secsupport_height - 0.2 - dragcable_length]
    dragcable = cable(dragcable_endpoint, dragcable_point)
    dragcable = dragcable.material(ddd.mats.cable_metal)

    # Pulley block
    pulley_block_width = 0.5
    pulley_block_thick = 0.3
    pulley_block_height = 0.8
    pulley_block_profile = ddd.polygon([[-pulley_block_width * 0.25, 0],
                                        [pulley_block_width * 0.25, 0],
                                        [pulley_block_width / 2, pulley_block_height],
                                        [-pulley_block_width / 2, pulley_block_height]], name="Pulley block")
    pulley_block_profile = pulley_block_profile.buffer(0.2, resolution=3, join_style=ddd.JOIN_ROUND)

    pulley_block = pulley_block_profile.extrude(pulley_block_thick).translate([0, 0, -pulley_block_thick / 2])
    pulley_block = pulley_block.rotate(ddd.ROT_FLOOR_TO_FRONT).rotate(ddd.ROT_TOP_CW)
    pulley_block = pulley_block.material(ddd.mats.metal_paint_yellow)
    pulley_block = ddd.uv.map_cubic(pulley_block)
    pulley_block = pulley_block.translate(dragcable_endpoint)

    # Hook
    hook_radius = 0.6
    hook_radius_inner = 0.35
    hook = ddd.sphere(r=hook_radius, name="Hook")
    hook = hook.scale([0.2, 1.0, 1.0])

    hole = ddd.point().buffer(hook_radius_inner, resolution=3, cap_style=ddd.CAP_ROUND).extrude(4.0).translate([0, 0, -2])
    hole = hole.rotate(ddd.ROT_FLOOR_TO_FRONT).rotate(ddd.ROT_TOP_CW)
    hook = hook.subtract(hole)
    hook = hook.material(ddd.mats.steel)
    #hook = ddd.uv.map_cubic(hook)
    hook = hook.translate(dragcable_endpoint)


    item = ddd.group3([piers, base, column, platform,
                       block, cabin,
                       mainsupport, maincable1, maincable2,
                       secsupport, seccable1,
                       dragcable, pulley_block, hook], name="Crane Vertical")
    return item



