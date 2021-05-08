# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020


from ddd.ddd import ddd
from ddd.pipeline.decorators import dddtask


@dddtask(order="30.65.10.+")
def osm_groups_items_ways_entry(osm, root, logger):
    # In separate file
    pass


@dddtask(path="/Features/*", select='["geom:type"="LineString"]["osm:natural" = "tree_row"]')
def osm_groups_items_ways_natural_tree_row(root, osm, obj):
    """
    Generate tree node items for tree row ways.
    """

    trees = ddd.group2(name="Tree Row: %s" % obj.name)
    trees.copy_from(obj)

    length = obj.length()
    density = 1 / 12.0  # tree every 10 m
    count = int(length * density) + 1

    for i in range(count):
        tree = ddd.point(name="Tree %d" % (i + 1))
        tree.copy_from(trees)
        tree.set('osm:natural', 'tree')
        trees.append(tree)

    ddd.align.along(trees, obj)

    root.find("/ItemsNodes").children.extend(trees.children)


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
    obj.extra['ddd:width'] = 0.55
    obj.extra['ddd:height'] = float(obj.extra.get('osm:height', 1.2))
    obj.extra['ddd:min_height'] = float(obj.extra.get('osm:min_height', 0.0))
    obj.extra['ddd:subtract_buildings'] = True
    obj = obj.material(ddd.mats.hedge)

    root.find("/ItemsWays").append(obj)



@dddtask(path="/Features/*", select='["geom:type"="LineString"]["osm:power" ~ "line|minor_line"]')
def osm_select_items_ways_power_line(root, osm, obj):
    """Define item data."""
    obj = obj.copy()
    obj.name = "Power line: %s" % obj.name
    obj.extra['ddd:width'] = 0.1
    obj.extra['ddd:height'] = 0.1
    obj.extra['ddd:min_height'] = float(obj.extra.get('osm:min_height', 11.0))
    obj.extra['ddd:layer'] = 2
    #obj.extra['ddd:way:weight'] = 100
    #obj.extra['ddd:way:lanes'] = None
    #obj.extra['ddd:base_height'] = 10.0
    obj = obj.material(ddd.mats.cable_metal)
    # TODO: Resolve tower/posts/building + connectors
    numcables = int(obj.get('osm:cables', 2))
    for i in range(numcables):
        cable = obj.copy()
        cable.geom = cable.geom.parallel_offset(-(numcables - 1 ) / 2.0 + 1.0 * i, "left")
        root.find("/ItemsWays").append(cable)


'''
###@dddtask(order="30.50.20.+", log=True)
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


