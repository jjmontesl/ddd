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


obj = ddd.line([(0, 0), (4, 0)])
obj2 = obj.line_substring(1.0, -1.0)

ddd.group([obj.buffer(0.1, cap_style=ddd.CAP_FLAT),
           obj2.buffer(0.1, cap_style=ddd.CAP_FLAT).material(ddd.MAT_HIGHLIGHT)]).show()


coords = [[10, 10], [5, 9], [3, 12], [1, 5], [-8, 0], [10, 0]]
obj = ddd.polygon(coords).subtract(ddd.rect([1,1,2,2]))
ref = obj.convex_hull().material(ddd.MAT_HIGHLIGHT)

#ddd.group([obj, ref,
#           ddd.point(obj.geom.exterior.coords[0]).buffer(0.1),
#           ddd.point(ref.geom.exterior.coords[0]).buffer(0.2).material(ddd.MAT_HIGHLIGHT),]).show()

# Test vertex reordering
obj = ddd.geomops.vertex_order_align_snap(obj, ref)

ddd.group([obj, ref,
           ddd.point(obj.geom.exterior.coords[0]).buffer(0.1),
           ddd.point(ref.geom.exterior.coords[0]).buffer(0.2).material(ddd.MAT_HIGHLIGHT),]).show()


