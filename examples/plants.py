# Jose Juan Montes 2019-2020

import math

from ddd.ddd import ddd
from ddd.pack.sketchy import urban, landscape, industrial, plants
from ddd.pipeline.decorators import dddtask


@dddtask(order="10")
def pipeline_start(pipeline, root):

    items = ddd.group3()

    heights = (3.0, 5.0, 10.0, 15.0)

    for h in heights:
        item = landscape.rock([h * 0.2, h * 0.2, h * 0.1])
        items.append(item)

    for h in heights:
        item = plants.reed(height=h)
        items.append(item)

    for h in heights:
        item = plants.tree_default(height=h)
        items.append(item)

    for h in heights:
        item = plants.tree_palm(height=h)
        items.append(item)

    for h in heights:
        item = plants.tree_fir(height=h)
        items.append(item)

    for h in heights:
        item = plants.tree_bush(height=h * 0.2)
        items.append(item)

    items = ddd.align.grid(items, width=4)
    items.append( ddd.helper.all(size=40.0, center=[5, 5, 0]).twosided() )

    #items.show()
    #items.save("/tmp/test.glb")
    #items.save("/tmp/test.json")
    pipeline.root = items
    #root.append(items)

