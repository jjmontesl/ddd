# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020

from ddd.ddd import ddd
from ddd.pipeline.decorators import dddtask
from ddd.core.exception import DDDException
import random
import sys


@dddtask(order="30.10.+", log=True)
def osm_groups_create_root_nodes(root, osm, pipeline):
    items = ddd.group2(name="Areas")
    root.append(items)
    items = ddd.group2(name="Ways")
    root.append(items)
    items = ddd.group2(name="Buildings")
    root.append(items)
    items = ddd.group2(name="ItemsNodes")
    root.append(items)
    items = ddd.group2(name="ItemsAreas")
    root.append(items)
    items = ddd.group2(name="ItemsWays")
    root.append(items)
    items = ddd.group2(name="Meta")  # 2D meta information (boundaries, etc...)
    root.append(items)

    #root.dump(data=True)

@dddtask(order="30.20.10", path="/Features/*", select='[geom:type="Point"]', log=True)  #  , select='[geom:type="Point"]'  , parent="stage_30_generate_items_node")
def osm_generate_items(root, osm, obj):
    """Generate items for point features."""
    item = obj.copy(name="Item: %s" % obj.name)
    item = item.material(ddd.mats.red)
    if item.geom:
        root.find("/ItemsNodes").append(item)

@dddtask(order="30.20.20", log=True)  #  , select='[geom:type="Point"]'  , parent="stage_30_generate_items_node")
def osm_generate_items_process(root, osm, obj):
    """Generate items for point features."""
    #root.save("/tmp/osm-31-items.svg")
    pass



@dddtask(order="30.30.10.+", log=True)
def osm_select_ways(root):
    # Ways depend on buildings
    pass


'''
@dddtask(order="30.30.?.+", path="/Features/*", select='[geom:type="LineString"][]', log=True)
def osm_groups_ways_ignored(root, obj, logger):
    """Collect ignored ways to store, report and visualize."""
    logger.warn("Ignored ways: %s", obj)
'''


@dddtask(order="30.30.20", log=True)
def osm_groups_ways_process(pipeline, osm, root, logger):
    #osm.ways_1d = root.find("/Ways")
    #osm.ways.generate_ways_1d()
    #root.find("/Ways").replace(osm.ways_1d)
    pass



# Generate buildings (separate file)


@dddtask(order="30.50.10", path="/Features/*", select='["geom:type" ~ "Polygon|MultiPolygon|GeometryCollection"][!"osm:building"]')
def osm_groups_areas(root, osm, obj, logger):

    item = obj.copy(name="Area: %s" % obj.name)

    try:
        area = item.individualize().flatten()
        area.validate()
    except DDDException as e:
        logger.warn("Invalid geometry (cropping area) for area %s (%s): %s", area, area.extra, e)
        try:
            area = area.clean(eps=0.001).intersection(ddd.shape(osm.area_crop))
            area = area.individualize().flatten()
            area.validate()
        except DDDException as e:
            logger.warn("Invalid geometry (ignoring area) for area %s (%s): %s", area, area.extra, e)
            return

    for a in area.children:
        if a.geom:
            a.extra['ddd:area:area'] = a.geom.area
            root.find("/Areas").append(a)

    #root.find("/Areas").append(item)

@dddtask(order="30.50.20")
def osm_groups_areas_process(pipeline, osm, root, logger):
    pass


@dddtask(order="30.50.90.+", path="/Areas/*", select='[! "ddd:area:type"]')
def osm_groups_areas_remove_ignored(root, obj, logger):
    """Remove ignored areas."""
    return False


@dddtask(order="30.60.+")
def osm_generate_areas_coastline_2d(osm, root, logger):
    #osm.areas.generate_coastline_2d(osm.area_crop if osm.area_crop else osm.area_filter)  # must come before ground
    water_2d = osm.areas2.generate_coastline_2d(osm.area_filter)  # must come before ground
    logger.info("Coastline 2D areas generated: %s", water_2d)
    if water_2d:
        root.find("/Areas").children.extend(water_2d.children)


@dddtask(order="30.70.+")
def osm_groups_items_areas(osm, root, logger):
    # In separate file
    pass


@dddtask(order="30.90")
def osm_groups_finished(pipeline, osm, root, logger):
    pass



