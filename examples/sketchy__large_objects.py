# Jose Juan Montes 2019-2020

from ddd.ddd import ddd
from ddd.pack.sketchy import urban, landscape, industrial
from ddd.pipeline.decorators import dddtask


@dddtask()
def pipeline_start(pipeline, root):

    items = ddd.group3()

    item = industrial.crane_vertical()
    items.append(item)

    item = landscape.powertower()
    items.append(item)

    item = landscape.lighthouse()
    items.append(item)
    #item.show()

    item = landscape.comm_tower()
    items.append(item)


    items = ddd.align.grid(items, 10.0)
    items.append(ddd.helper.all())
    items.show()

    pipeline.root = items

