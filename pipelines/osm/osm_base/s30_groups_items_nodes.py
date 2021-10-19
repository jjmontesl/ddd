# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020


from ddd.ddd import ddd
from ddd.pipeline.decorators import dddtask


# Generate items (also see groups_items_nodes)
@dddtask(order="30.20.10.10.+", path="/Features/*", select='[geom:type="Point"]', log=True)  #  , select='[geom:type="Point"]'  , parent="stage_30_generate_items_node")
def osm_generate_items_nodes_entry(root, osm, obj):
    """Entry point for items nodes generation (30.20.*)."""
    pass

@dddtask(path="/Features/*", select='[geom:type="Point"]', log=True)  #  , select='[geom:type="Point"]'  , parent="stage_30_generate_items_node")
def osm_generate_items_nodes_point(root, osm, obj):
    """Generate items for point features."""
    item = obj.copy(name="Item: %s" % obj.name)
    item = item.material(ddd.mats.red)
    if item.geom:
        root.find("/ItemsNodes").append(item)


@dddtask(order="30.20.20.+", log=True)  #  , select='[geom:type="Point"]'  , parent="stage_30_generate_items_node")
def osm_generate_items_process(root, osm, obj):
    """Generate items for point features."""
    #root.save("/tmp/osm-31-items.svg")
    pass
