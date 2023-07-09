# Jose Juan Montes 2019-2020

from ddd.ddd import ddd
from ddd.pack.sketchy import urban, landscape, industrial
from ddd.pipeline.decorators import dddtask


@dddtask()
def pipeline_start(pipeline, root):

    items = ddd.group3()

    item = industrial.barrel_metal()
    items.append(item)

    pipe_segment_height = 2.0
    item = industrial.pipe_segment(height=pipe_segment_height)
    item.append(item.copy().translate([0, 0, pipe_segment_height]))
    items.append(item)


    items = ddd.align.grid(items, 10.0)
    items.append(ddd.helper.all())
    items.show()

    pipeline.root = items

