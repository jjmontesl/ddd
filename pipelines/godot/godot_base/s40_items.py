# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020

from ddd.ddd import ddd, DDDObject2
from ddd.math.curves import path
from ddd.pipeline.decorators import dddtask
from ddd.core.exception import DDDException
import random
import sys
import math
from shapely.ops import linemerge
from ddd.ops import filters, uvmapping
import numpy


@dddtask(path="/Features", log=True)
def room_items(root, pipeline, obj):

    obj = pipeline.data['rooms:background_union']

    points = obj.random_points(5)  #50

    return  # No random objects

    for p in points:
        pos = [p[0], p[1]]
        item = ddd.point(pos, "ItemRandom")
        item.extra['gdc:item'] = True
        item.extra['godot:instance'] = "res://scenes/items/ItemGeneric.tscn"
        root.find("/Items").append(item)


@dddtask(path="/Features/*", select='[geom:type="LineString"]', log=True)
def lines_to_parabollas(root, pipeline, obj):
    print(obj)
    if obj.vertex_count() == 3:
        path = ddd.path.parabolla_from_geom(obj)
        path = path.to_geom(resolution=10.0)
        return path

@dddtask(path="/Features/*", select='[geom:type="LineString"]', log=True)
def room_items_line(root, pipeline, obj):
    """
    Creates items along a line.
    """
    # Sample line
    length = obj.length()
    itemdensity = 150.0
    numpoints = length / itemdensity

    for d in numpy.linspace(0.0, length, numpoints, endpoint=True):
        p, segment_idx, segment_coords_a, segment_coords_b = obj.interpolate_segment(d)
        pos = [p[0], p[1]]
        item = ddd.point(pos, "ItemLine")
        item.extra['gdc:item'] = True
        item.extra['godot:instance'] = "res://scenes/items/ItemGeneric.tscn"
        root.find("/Items").append(item)

