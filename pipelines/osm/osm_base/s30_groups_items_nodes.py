# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020


from ddd.ddd import ddd
from ddd.pipeline.decorators import dddtask


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


@dddtask(path="/ItemsNodes/*", select='["osm:amenity" = "bicycle_parking"]')
def osm_select_items_nodes_amenity_bicycle_parking(root, osm, obj):
    """Define item data."""
    obj.name = "Bicycle Parking: %s" % obj.name
    capacity = int(obj.get('osm:capacity', 2))
    spacing = 0.7
    if capacity > 1:
        obj.set('ddd:array:type', "line")
        obj.set('ddd:array:length', capacity * spacing)
        obj.set('ddd:array:count', capacity)


@dddtask(order="30.20.20.+", log=True)  #  , select='[geom:type="Point"]'  , parent="stage_30_generate_items_node")
def osm_generate_items_process(root, osm, obj):
    """Generate items for point features."""
    #root.save("/tmp/osm-31-items.svg")
    pass
