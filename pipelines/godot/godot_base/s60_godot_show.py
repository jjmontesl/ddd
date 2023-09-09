# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020

from ddd.ddd import ddd, DDDNode2
from ddd.pipeline.decorators import dddtask
from ddd.core.exception import DDDException
import random
import sys
import math
from shapely.ops import linemerge
from ddd.ops import filters, uvmapping

@dddtask(log=True)
def rooms_test_show(root, pipeline):

    root.dump()
    items = ddd.group([root.find("/Rooms"), root.find("/Items")])
    nitems = ddd.group3()

    items = items.flatten()
    for item in items.children:
        item = item.extrude(20.0 + item.get('ddd:z_index', 0))
        item = item.translate([0, 0, -item.get('ddd:z_index', 0)])
        nitems.append(item)

    #nitems.show()

