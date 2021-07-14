# Jose Juan Montes 2019-2021

"""
Tests several 2D and 3D geometry operations.
"""

from ddd.pack.sketchy import urban, landscape
from ddd.ddd import ddd
import math
import sys
from ddd.text import fonts
import logging

items = ddd.group3()

# Get instance of logger for this module
logger = logging.getLogger(__name__)


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
items.show()


