# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020


from ddd.ddd import ddd
from ddd.pipeline.decorators import dddtask



@dddtask(path="/Features/*", select='["osm:barrier" = "fence"]')
def osm_select_items_ways_barrier_fence(root, osm, obj):
    """Define item data. Works on polygon (uses boundary)."""
    obj.name = "Fence: %s" % obj.name
    #obj.extra['ddd:way:weight'] = 100
    #obj.extra['ddd:way:lanes'] = None
    obj.extra['ddd:width'] = 0.0
    obj.extra['ddd:height'] = float(obj.extra.get('osm:height', 1.2))
    obj.extra['ddd:min_height'] = float(obj.extra.get('osm:min_height', 0.0))
    obj.extra['ddd:subtract_buildings'] = True
    obj = obj.material(ddd.mats.fence)
    obj = obj.outline()  #.buffer(0.05)
    root.find("/ItemsWays").append(obj)

@dddtask(path="/Features/*", select='["geom:type"="LineString"]["osm:barrier" = "hedge"]')
def osm_select_items_ways_barrier_hedge(root, osm, obj):
    """Define item data."""
    obj.name = "Hedge: %s" % obj.name
    #obj.extra['ddd:way:weight'] = 100
    #obj.extra['ddd:way:lanes'] = None
    obj.extra['ddd:width'] = 0.6
    obj.extra['ddd:height'] = float(obj.extra.get('osm:height', 1.2))
    obj.extra['ddd:min_height'] = float(obj.extra.get('osm:min_height', 0.0))
    obj.extra['ddd:subtract_buildings'] = True
    obj = obj.material(ddd.mats.treetop)

    root.find("/ItemsWays").append(obj)


'''
@dddtask(order="30.50.20.+", log=True)
def osm_groups_areaitems(root, osm):

    # Split and junctions first?
    # Possibly: metadata can depend on that, and it needs to be done if it will be done anyway

    # Otherwise: do a pre and post step, and do most things in post (everything not needed for splitting)

    pass

@dddtask(path="/Areas/*")
def osm_groups_areas_default_name(obj, osm):
    """Set default name."""
    name = "Area: " + (obj.extra.get('osm:name', obj.extra.get('osm:id')))
    obj.name = name
    #obj.extra['ddd:ignore'] = True

@dddtask(path="/Areas/*")
def osm_groups_areas_default_material(obj, osm):
    """Assign default material."""
    obj = obj.material(ddd.mats.terrain)
    return obj

@dddtask(path="/Areas/*")
def osm_groups_areas_default_data(obj, osm):
    """Sets default data."""
    obj.extra['ddd:area:weight'] = 100  # Lowest
    obj.extra['ddd:area:height'] = 0  # Lowest
'''


