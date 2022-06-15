# ddd - DDD123
# Library for simple scene modelling.
# Jose Juan Montes and Contributors 2019-2021

import logging

from ddd.ddd import ddd
from ddd.pack.symbols.dddlogo import dddlogo
from ddd.pipeline.decorators import dddtask
import math


@dddtask()
def pipeline_logo(pipeline, root):
    """
    """
    logo = dddlogo()
    #logo.append(ddd.helper.all(center=[10, 10, 1]))
    logo.show()


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