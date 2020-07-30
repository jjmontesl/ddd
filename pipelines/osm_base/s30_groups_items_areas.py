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
    obj.name = "Fountain: %s" % obj.name
    #obj.extra['ddd:item:type'] = "area"
    root.find("/ItemsAreas").append(obj)

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
    """Define area data."""
    obj.extra['ddd:elevation:base_ref'] = "container"
    #print(obj.geom)
    items = osm.items2.generate_item_2d_childrens_playground(obj)
    root.find("/ItemsNodes").children.extend([i for i in items.flatten().children if i.geom])

    obj = obj.material(ddd.mats.pitch_blue)
    obj.name = "Playground: %s" % obj.name
    obj.extra['ddd:area:type'] = "default"
    obj.extra['ddd:height'] = 0.2
    root.find("/Areas").append(obj)


