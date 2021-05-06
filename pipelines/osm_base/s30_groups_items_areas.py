# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020


import random

from ddd.ddd import ddd
from ddd.pipeline.decorators import dddtask
import numpy as np
import math
from shapely.geometry import polygon


@dddtask(order="30.70.30.+")
def osm_groups_items_areas(osm, root, logger):
    # In separate file
    pass


@dddtask(path="/Features/*", select='["osm:amenity" = "fountain"]["geom:type" ~ "Polygon|MultiPolygon|GeometryCollection"]')
def osm_groups_items_areas_amenity_fountain(obj, root):
    """Area fountains."""
    fountain = obj.copy()
    #obj = obj.material(ddd.mats.water)
    #obj = obj.material(ddd.mats.pavement)

    fountain.name = "AreaFountain: %s" % fountain.name
    #obj.extra['ddd:area:water'] = 'ignore'  # Water is created by the fountain object, but the riverbank still requires
    #obj.extra['ddd:item:type'] = "area"
    #obj.extra['osm:natural']
    fountain.extra["ddd:elevation"] = "min"  # Make min+raise-height
    root.find("/ItemsAreas").append(fountain)  # ItemsAreas

    # Area below fountain
    area = fountain.copy()
    area.set('ddd:area:type', 'default')  # 'void'
    area.set('ddd:area:height', 0)  # 'void'
    area.set('ddd:area:weight', 200)  # Higher than default priority (100) ?
    area.set('ddd:area:area', area.geom.area)  # Needed for area to be processed in s40
    area.set('ddd:layer', '0')
    area = area.material(ddd.mats.terrain)  # Better, use fountain:base (terrain vs base) leave void and construct fopuntain base base, get materia from surrounding possibly
    #area.set["ddd:elevation:"] = "min"  # Make min+raise-height
    root.find("/Areas").append(area)  # ItemsAreas


@dddtask(path="/Features/*", select='["osm:water" = "pond"]["geom:type" ~ "Polygon|MultiPolygon|GeometryCollection"]')
def osm_groups_items_areas_water_pond(obj, root):
    """Define area data."""
    obj = obj.material(ddd.mats.water)
    obj.name = "Pond: %s" % obj.name
    #obj.extra['ddd:item:type'] = "area"
    obj.extra['ddd:area:type'] = "water"
    #root.find("/Areas").append(obj)  # ItemsAreas
    # Currently ignoring as will be built by ddd:area:type=water

@dddtask(path="/Areas/*", select='["osm:historic" = "archaeological_site"]')
def osm_groups_items_areas_historic_archaeological_site(root, osm, obj):
    """
    Adds an archaeological site item so items are generated in archaeological site areas.
    """
    item = obj.copy()
    item.set('ddd:item:elevation', 'terrain_geotiff_elevation_apply')
    root.find("/ItemsNodes").append(item)


@dddtask(path="/Features/*", select='["osm:leisure" = "outdoor_seating"]["geom:type" ~ "Polygon|MultiPolygon|GeometryCollection"]')
def osm_groups_items_areas_leisure_outdoor_seating(obj, root, osm):
    """Define area data."""
    obj.extra['ddd:elevation:base_ref'] = "container"
    items = osm.items2.generate_item_2d_outdoor_seating(obj)
    root.find("/ItemsNodes").children.extend([i for i in items.flatten().children if i.geom])


@dddtask(path="/Features/*", select='["osm:leisure" = "playground"]["geom:type" ~ "Polygon|MultiPolygon|GeometryCollection"]')
def osm_groups_items_areas_leisure_playground(obj, root, osm):
    """
    Generates childrens objects for an area.
    TODO: As we know the area, spread objects over it instead of radially.
    TODO: Check that an equivalent node is not defined, or individual playground items.
    """
    obj = obj.copy()
    obj.extra['ddd:elevation:base_ref'] = "container"
    items = osm.items2.generate_item_2d_childrens_playground(obj)
    root.find("/ItemsNodes").children.extend([i for i in items.flatten().children if i.geom])

@dddtask(path="/Features/*", select='["osm:leisure" = "playground"]["geom:type" = "Point"]')
def osm_groups_items_areas_leisure_playground_point(obj, root, osm):
    """
    Create an area automatically for playground nodes without a defined area.
    Note that this could also be an area (see groups_areas).
    """

    obj.extra['ddd:elevation:base_ref'] = "container"
    #print(obj.geom)
    generated_area = obj.buffer(5.0)

    # Check if area conflicts with other existing playground area
    other_playgrounds = root.find("/Areas").select('["osm:leisure" = "playground"]')
    if other_playgrounds.intersects(generated_area):
        return

    items = osm.items2.generate_item_2d_childrens_playground(generated_area)
    root.find("/ItemsNodes").children.extend([i for i in items.flatten().children if i.geom])

    """
    obj = obj.material(ddd.mats.pitch_blue)
    obj.name = "Playground Point: %s" % obj.name
    obj.extra['ddd:area:type'] = "default"
    obj.extra['ddd:height'] = 0.0

    root.find("/Areas").append(obj)
    """

@dddtask(path="/Features/*", select='["osm:leisure" = "swimming_pool"]')
def osm_groups_items_areas_leisure_swimming_pool(obj, root, osm):
    """
    """

    pool = obj.copy()
    #obj = obj.material(ddd.mats.water)
    #obj = obj.material(ddd.mats.pavement)

    pool.name = "Swimming Pool: %s" % pool.name
    #obj.extra['ddd:area:water'] = 'ignore'  # Water is created by the fountain object, but the riverbank still requires
    #obj.extra['ddd:item:type'] = "area"
    #obj.extra['osm:natural']
    pool.extra["ddd:elevation"] = "max"
    root.find("/ItemsAreas").append(pool)  # ItemsAreas

    # TODO: Use normal alignment of nodes
    pool_outline = pool.copy()
    pool_outline.geom = polygon.orient(pool_outline.geom, 1)
    pool_outline = pool_outline.outline()
    ladder_pos_d = random.uniform(0, pool_outline.length())
    ladder_pos, segment_idx, segment_coords_a, segment_coords_b = pool_outline.interpolate_segment(ladder_pos_d)
    ladder = obj.copy(name="Swimming Pool Ladder")
    ladder.children = []
    ladder.geom = ddd.point(ladder_pos).geom
    angle = math.atan2(segment_coords_b[1] - segment_coords_a[1], segment_coords_b[0] - segment_coords_a[0])
    ladder.set('ddd:ladder', 'swimming_pool')
    ladder.set('ddd:angle', angle + math.pi)
    ladder.set('ddd:height:base', 0.5)
    #pool.extra["ddd:elevation"] = "max"
    root.find("/ItemsNodes").append(ladder)


    # Define terrain/area below pool as void
    area = pool.copy()
    area.set('ddd:area:type', 'void')  # 'void' # will be constructed by the pool areaitem
    area.set('ddd:area:height', -2.0)  # 'void'
    #area.set('ddd:area:weight', 200)  # Higher than default priority (100) ?
    area.set('ddd:area:area', area.geom.area)  # Needed for area to be processed in s40
    area.set('ddd:layer', '0')

    area = area.material(ddd.mats.water)  # Better, use fountain:base (terrain vs base) leave void and construct fopuntain base base, get materia from surrounding possibly
    #area.set["ddd:elevation:"] = "min"  # Make min+raise-height
    root.find("/Areas").append(area)  # ItemsAreas


