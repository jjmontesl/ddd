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

from ddd.pipeline.decorators import dddtask


@dddtask()
def pipeline_test_line_substring(pipeline, root):
    """
    Tests geometric operations.
    """

    items = ddd.group3()

    # Get instance of logger for this module
    logger = logging.getLogger(__name__)

    # Test substrings
    obj = ddd.line([(0, 0), (4, 0)])
    obj2 = obj.line_substring(1.0, -1.0)

    result = ddd.group([obj.buffer(0.1, cap_style=ddd.CAP_FLAT),
               obj2.buffer(0.1, cap_style=ddd.CAP_FLAT).material(ddd.MAT_HIGHLIGHT)])
    result.show()

@dddtask()
def pipeline_test_vertex_order_align_snap(pipeline, root):
    """
    Tests geometric operations.
    """

    # Test polygon subtract, and 2D convex hull
    coords = [[10, 10], [5, 9], [3, 12], [1, 5], [-8, 0], [10, 0]]
    obj = ddd.polygon(coords).subtract(ddd.rect([1,1,2,2]))
    ref = obj.convex_hull().material(ddd.MAT_HIGHLIGHT)

    # Test vertex reordering
    obj = ddd.geomops.vertex_order_align_snap(obj, ref)

    result = ddd.group([
        obj, ref,
        ddd.point(obj.geom.exterior.coords[0]).buffer(0.1),
        ddd.point(ref.geom.exterior.coords[0]).buffer(0.2).material(ddd.MAT_HIGHLIGHT),])

    result.show()

    root.append(result)

