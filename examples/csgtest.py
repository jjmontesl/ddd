# ddd - D1D2D3
# Library for simple scene modelling.

import math

from ddd.ddd import ddd
from ddd.pipeline.decorators import dddtask

import numpy as np

@dddtask()
def example_csg(pipeline, root):
    """
    """

    items = ddd.DDDNode3("Items")

    box = ddd.box().recenter(onplane=True)
    sphere = ddd.sphere(r=0.2).translate([0, 0, 1])

    obj1 = box.subtract(sphere)
    obj1 = obj1.material(ddd.MAT_TEST)
    obj1 = ddd.uv.map_cubic(obj1)
    items.append(obj1)

    obj2 = box.union(sphere)
    obj2 = obj2.material(ddd.MAT_TEST)
    obj2 = ddd.uv.map_cubic(obj2)
    items.append(obj2)

    items = ddd.align.grid(items, space=3)
    items.append(ddd.helper.grid_xy(size=10).recenter())

    #items = ddd.meshops.batch_by_material(items)
    #items.dump()
    root.append(items)
    root.show()
    #items.save("/tmp/test.json")
    #items.save("/tmp/test.glb")