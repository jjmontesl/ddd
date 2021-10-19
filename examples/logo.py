# ddd - DDD123
# Library for simple scene modelling.
# Jose Juan Montes and Contributors 2019-2021

import logging

from ddd.ddd import ddd
from ddd.pipeline.decorators import dddtask
import math


@dddtask()
def pipeline_logo(pipeline, root):
    """
    """

    logo = ddd.group3()

    thick = 0.125
    margin = 0.4

    line_out = ddd.line([
        (1.0, 0.0, 0.4),
        (1.0, 0.0, 0.0),
        (0.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
        (0.0, 1.0, 1.0),
        (1.0, 1.0, 1.0),
        (1.0, 0.0, 1.0),
        (1.0, 0.0, 0.6),
        ])

    base = ddd.rect([thick, thick], name="Logo exterior").recenter()

    item = base.extrude_along(line_out)
    item = item.material(ddd.mats.steel)
    #item = item.rotate([0, 0, 0.2])
    item = ddd.uv.map_cubic(item)  # FIXME: One of the corner vertices are not being split (but they are if slightly rotated)
    logo.append(item)

    line_in = ddd.line([
        (1.0 - margin, 1.0 - margin - 0.1, 1),
        (1.0 - margin, 1.0 - margin, 1),
        (0.0, 1.0 - margin, 1),
        (0.0, 0.0, 1),
        (1.0 - margin, 0.0, 1),
        (1.0 - margin, 0.0, margin),
        (0.0, 0.0, margin),
        (0.0, 1.0 - margin, margin),
        (0.0, 1.0 - margin, 1.0 - margin),
        (0.0, 1.0 - margin - 0.1, 1.0 - margin),
        ])

    item = base.extrude_along(line_in)
    item = item.material(ddd.mats.green)
    item = ddd.uv.map_cubic(item)
    logo.append(item)

    #logo = logo.scale([2, 2, 2])

    logo.show()

    root.append(logo)

    root.append(ddd.helper.all(center=[10, 10, 1]))


    #root.append(items)

'''
@dddtask()
def pipeline_logo_old(pipeline, root):
    """
    """

    items = ddd.group3()

    # Extrusion with optional caps
    dext_line = ddd.point().line_to([0, 10]).line_to([2, 10]).arc_to([2, 0], [2, 5], False).line_to([0, 0])
    dint_line = ddd.point([2, 2]).line_to([2, 8]).arc_to([2, 2], [2, 5], False)
    dext = ddd.polygon(dext_line.geom.coords)
    dint = ddd.polygon(dint_line.geom.coords)
    dchar = dext.subtract(dint)

    dchar_base = dchar.extrude(1)
    dchar = dchar_base.rotate(ddd.ROT_FLOOR_TO_FRONT)

    dchar_r = dchar.copy().material(ddd.mats.red)
    dchar_l = dchar.rotate(ddd.ROT_TOP_HALFTURN).translate([1, 0, -1]).material(ddd.mats.green)
    dchar_b = dchar_base.rotate(ddd.ROT_TOP_CW).translate([-5, 1, -1]).material(ddd.mats.blue)

    items.append([dchar_r, dchar_l, dchar_b])

    # All items
    #items = ddd.align.grid(items, space=10.0)
    #items.append(ddd.helper.all())

    #root.append(items)
'''