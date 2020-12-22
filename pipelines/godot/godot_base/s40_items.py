# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020

from ddd.ddd import ddd, DDDObject2
from ddd.pipeline.decorators import dddtask
from ddd.core.exception import DDDException
import random
import sys
import math
from shapely.ops import linemerge
from ddd.ops import filters, uvmapping


@dddtask(path="/Features/*", select='[ddd:polygon:type="hollow"]', log=True)
def room_items(root, pipeline, obj):

    points = obj.random_points(5)
    for p in points:
        pos = [p[0], p[1]]
        item = ddd.point(pos, "ItemRandom")
        item.extra['godot:instance'] = "res://scenes/items/ItemGeneric.tscn"
        root.find("/Items").append(item)

