# Jose Juan Montes 2019-2020


from ddd.ddd import ddd
from ddd.pack.sketchy import urban, landscape, industrial, plants
from ddd.pipeline.decorators import dddtask


@dddtask(order="10")
def pipeline_start(pipeline, root):
    """
    """

    items = ddd.group3()

    heights = (3.0, 5.0, 10.0, 15.0)

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

    items_org = items.copy()

    # Original
    items = items_org.copy()
    items = ddd.align.grid(items)
    items.append(ddd.helper.all())
    items.show()

    # Simplify using convex hull
    items = ddd.meshops.reduce(items_org)
    items = ddd.align.grid(items)
    items.append(ddd.helper.all())
    items.show()

    # Simplify using bounds
    items = ddd.meshops.reduce_bounds(items_org)
    items = ddd.align.grid(items)
    items.append(ddd.helper.all())
    items.show()

    # Simplify using quadric decimation
    items = ddd.meshops.reduce_quadric_decimation(items_org, target_ratio=0.25)
    items = ddd.align.grid(items)
    items.append(ddd.helper.all())
    items.show()

    root.append(items)


