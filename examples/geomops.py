# ddd - DDD123
# Library for simple scene modelling.
# Jose Juan Montes and Contributors 2019-2021

"""
Tests several 2D and 3D geometry operations.
"""

import logging

from ddd.ddd import ddd
from ddd.pipeline.decorators import dddtask


@dddtask()
def pipeline_test_line_substring(pipeline, root, logger):
    """
    Tests geometric operations.
    """

    items = ddd.group3()

    # Test substrings
    obj = ddd.line([(0, 0), (4, 0)])
    obj2 = obj.line_substring(1.0, -1.0)

    result = ddd.group([obj.buffer(0.1, cap_style=ddd.CAP_FLAT),
               obj2.buffer(0.1, cap_style=ddd.CAP_FLAT).material(ddd.MAT_HIGHLIGHT)])
    result.show()


@dddtask()
def pipeline_test_centerline(pipeline, root, logger):
    """
    Tests Node2 centerline() method.
    """

    items = ddd.group3()

    # Test substrings
    obj = ddd.line([(0, 0), (4, 0)]).buffer(0.1)

    cl = obj.centerline(0.05).highlight()

    result = ddd.group([obj, cl])
    result.show()

    cl.buffer(0.05).extrude(1.0).show()


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


@dddtask()
def pipeline_test_oriented_rect(pipeline, root):
    """
    Tests geometric operations.
    """

    # Test polygon subtract, and 2D convex hull
    coords = [[10, 10], [5, 9], [3, 12], [1, 5], [-8, 0], [10, 0]]
    obj = ddd.polygon(coords).subtract(ddd.rect([1,1,2,2]))
    #ref = obj.convex_hull().material(ddd.MAT_HIGHLIGHT)
    obj = obj.rotate(ddd.PI_OVER_3)
    ref = obj.material(ddd.MAT_HIGHLIGHT)

    # Test oriented rect
    obj = ddd.geomops.oriented_rect(ref)

    result = ddd.group([obj, ref])
    #result.show()

    root.append(result)


@dddtask()
def pipeline_test_split_bb_area_ratio(pipeline, root):
    """
    Tests geometric operations.
    """

    coords = [[0, 0], [8, 0], [8, 3]]  # , [16, 3]]
    obj = ddd.line(coords).buffer(0.5)
    #obj = obj.material(ddd.MAT_HIGHLIGHT)

    obj = ddd.group2(ddd.geomops.split_bb_area_ratio(obj))
    
    obj = ddd.helper.colorize_objects(obj)
    obj.show()

    root.append(obj)

@dddtask()
def pipeline_test_split_bb_area_ratio_2(pipeline, root):
    """
    Tests geometric operations.
    """

    coords = [[0, 0], [8, 0], [8, 3], [16, 3]]
    obj = ddd.line(coords).buffer(0.5)
    #obj = obj.material(ddd.MAT_HIGHLIGHT)

    obj = ddd.group2(ddd.geomops.split_bb_area_ratio(obj))
    
    obj = ddd.helper.colorize_objects(obj)
    obj.show()

    root.append(obj)    