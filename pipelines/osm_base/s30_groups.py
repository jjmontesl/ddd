# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020

from ddd.ddd import ddd
from ddd.pipeline.decorators import dddtask
from ddd.core.exception import DDDException

"""
The "grouping" stage of the build process **selects** features from the /Features node
and adds the necessary data to other different subnodes (Areas, Ways, Buildings...).

OSM features are not removed from the /Features node. Rather, new objects / copies of the
features are added to the graph. These are based off the feature so OSM metadata is
conserved.

Selection is done in the default pipeline order (irrespective of the original OSM object type,
but often related to ways / polygons / nodes).

1. Ways
2. Areas
3. Items
"""

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

@dddtask(order="30.20.10", log=True)  #  , select='[geom:type="Point"]'  , parent="stage_30_generate_items_node")
def osm_generate_items_nodes(root, osm):
    """
    Generate items.
    See groups items nodes generation
    """
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
    """Remove not selected areas."""
    return False


@dddtask(order="30.60.+")
def osm_generate_areas_coastline_2d(osm, root, logger):
    #osm.areas.generate_coastline_2d(osm.area_crop if osm.area_crop else osm.area_filter)  # must come before ground
    water_2d = osm.areas2.generate_coastline_2d(osm.area_filter)  # must come before ground
    logger.info("Coastline 2D areas generated: %s", water_2d)
    if water_2d:
        root.find("/Areas").children.extend(water_2d.children)


@dddtask(order="30.65.+")
def osm_groups_items_ways(osm, root, logger):
    # In separate file
    pass


@dddtask(order="30.70.+")
def osm_groups_items_areas(osm, root, logger):
    # In separate file
    pass


@dddtask(order="30.80.+")
def osm_groups_common(osm, root, logger):
    # In separate file
    pass

# Area and ways attributes
# TODO: Move 30_80_groups_common  to a separate file
# Ensure this applies to areas and ways at an appropriate time (now is applying to everything)

@dddtask(select='["osm:surface" = "compacted"]')  # path="/Areas/*",
def osm_groups_areas_surface_compacted(obj, root):
    """Applies osm:surface=compacted material."""
    #obj.extra['ddd:height'] = 0.0
    obj = obj.material(ddd.mats.dirt)
    return obj

@dddtask(select='["osm:surface" = "asphalt"]')
def osm_groups_areas_surface_asphalt(obj, root):
    """Applies osm:surface=compacted material."""
    #obj.extra['ddd:height'] = 0.0
    obj = obj.material(ddd.mats.asphalt)
    return obj

@dddtask(select='["osm:surface" = "concrete"]')
def osm_groups_areas_surface_concrete(obj, root):
    """"""
    #obj.extra['ddd:height'] = 0.0
    obj = obj.material(ddd.mats.concrete)
    return obj

@dddtask(select='["osm:surface" = "grass"]')
def osm_groups_areas_surface_grass(obj, root):
    """"""
    #obj.extra['ddd:height'] = 0.0
    obj = obj.material(ddd.mats.grass)
    return obj

@dddtask(select='["osm:surface" = "sand"]')
def osm_groups_areas_surface_sand(obj, root):
    """"""
    #obj.extra['ddd:height'] = 0.0
    obj = obj.material(ddd.mats.sand)
    return obj




@dddtask(order="30.90")
def osm_groups_finished(pipeline, osm, root, logger):
    pass



@dddtask(order="39.95.+", cache=True)
def osm_groups_cache(pipeline, osm, root, logger):
    """
    Caches current state to allow for faster reruns.
    """
    return pipeline.data['filenamebase'] + ".s30.cache"


