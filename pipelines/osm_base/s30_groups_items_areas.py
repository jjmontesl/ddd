# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020


from ddd.ddd import ddd
from ddd.pipeline.decorators import dddtask



@dddtask(order="30.70.30.+")
def osm_groups_items_areas(osm, root, logger):
    # In separate file
    pass

@dddtask(path="/Features/*", select='["osm:amenity" = "fountain"]["geom:type" ~ "Polygon|MultiPolygon|GeometryCollection"]')
def osm_groups_items_areas_amenity_fountain(obj, root):
    """Define area data."""
    obj = obj.material(ddd.mats.water)
    #obj = obj.material(ddd.mats.pavement)
    obj.name = "AreaFountain: %s" % obj.name
    #obj.extra['ddd:area:water'] = 'ignore'  # Water is created by the fountain object, but the riverbank still requires
    #obj.extra['ddd:item:type'] = "area"
    #obj.extra['osm:natural']
    obj.extra["ddd:elevation"] = "min"
    root.find("/ItemsAreas").append(obj)
    return False  # Remove the feature so it is not processed as water

@dddtask(path="/Features/*", select='["osm:water" = "pond"]["geom:type" ~ "Polygon|MultiPolygon|GeometryCollection"]')
def osm_groups_items_areas_water_pond(obj, root):
    """Define area data."""
    obj = obj.material(ddd.mats.water)
    obj.name = "Pond: %s" % obj.name
    #obj.extra['ddd:item:type'] = "area"
    root.find("/ItemsAreas").append(obj)


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

