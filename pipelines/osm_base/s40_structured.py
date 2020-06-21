# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020

from ddd.osm import osm
from ddd.pipeline.decorators import dddtask
from ddd.ddd import ddd


@dddtask(order="40.10.+", log=True)
def osm_structured_init(root, osm):
    #osm.ways_1d = root.find("/Ways")
    pass


@dddtask()
def osm_structured_split_ways(osm, root):
    osm.ways1.split_ways_1d(root.find("/Ways"))  # Where to put?

@dddtask()
def osm_structured_link_ways_items(osm, root):
    osm.ways1.ways_1d_link_items(root.find("/Ways"), root.find("/ItemsNodes"))


@dddtask()
def osm_structured_buildings(osm, root):
    # dependencies? (document)
    features = root.find("/Features")
    #osm.buildings.preprocess_buildings_features(features)
    #root.find("/Buildings").children = []  # Remove as they will be generated from features: TODO: change this
    #osm.buildings.generate_buildings_2d(root.find("/Buildings"))


@dddtask(path="/ItemsWays/*", select='["ddd:width"]')
def osm_structured_process_items_ways(osm, root, obj):
    """Generates items from Items Ways (lines)."""
    width = float(obj.extra.get('ddd:width', 0))
    if width > 0:
        obj = obj.buffer(width, cap_style=ddd.CAP_FLAT)
    return obj


@dddtask()
def osm_structured_generate_ways_2d(osm, root):
    """Generates ways 2D (areas) from ways 1D (lines), replacing the /Ways node in the hierarchy."""
    ways1 = root.find("/Ways")
    root.remove(ways1)

    ways2 = osm.ways2.generate_ways_2d(ways1)
    root.append(ways2)


@dddtask()
def osm_structured_subtract_buildings_calculate(pipeline, root, logger):

    buildings = root.find("/Buildings").union()
    pipeline.data['buildings'] = buildings

@dddtask(path="/Ways/*", select='["ddd:subtract_buildings" = True]')
def osm_structured_subtract_buildings(pipeline, root, logger, obj):
    """Subtract buildings from objects that cannot overlap them."""
    #buildings_2d_union = self.osm.buildings_2d.union()
    #way_2d = way_2d.subtract(self.osm.buildings_2d_union)
    obj = obj.clean(eps=0.05)
    buildings = pipeline.data['buildings']
    try:
        obj = obj.subtract(buildings)
    except Exception as e:
        logger.error("Could not subtract buildings %s from way %s: %s", buildings, obj, e)
    return obj


@dddtask(log=True)
def osm_structured_areas_postprocess(root, osm):
    areas_2d = root.find("/Areas")
    ways_2d = root.find("/Ways")
    #osm.areas2.generate_areas_2d_postprocess()
    osm.areas2.generate_areas_2d_postprocess_water(areas_2d, ways_2d)


@dddtask()
def osm_structured_generate_areas_interways(pipeline, osm, root, logger):
    """Generates interior areas between ways."""

    #osm.areas2.generate_areas_2d_interways()

    union = ddd.group2([root.find("/Ways").select('["ddd:layer" ~ "0|-1a"]'),
                        root.find("/Areas")])
    union = osm.areas2.generate_union_safe(union)

    interiors = osm.areas2.generate_areas_2d_ways_interiors(union)
    interiors = interiors.material(ddd.mats.pavement)
    interiors.extra['ddd:area:type'] = 'sidewalk'

    root.find("/Areas").append(interiors.children)

@dddtask()
def osm_structured_generate_areas_ground_fill(osm, root, logger):
    """
    Generates (fills) remaining ground areas (not between ways or otherwise occupied by other areas).
    Ground must come after every other area (interways, etc), as it is used to "fill" missing gaps.
    """

    area_crop = osm.area_filter
    logger.info("Generating terrain (bounds: %s)", area_crop.bounds)

    union = ddd.group2([root.find("/Ways").select('["ddd:layer" ~ "^(0|-1a)$"]'),
                        root.find("/Areas"),
                        #root.find("/Water")
                        ])
    union = osm.areas2.generate_union_safe(union)

    terr = ddd.rect(area_crop.bounds, name="Ground")
    terr = terr.material(ddd.mats.terrain)

    try:
        terr = terr.subtract(union)
        terr = terr.clean(eps=0.01)
    except Exception as e:
        logger.error("Could not subtract areas_2d from terrain.")
        return

    root.find("/Areas").append(terr)

@dddtask()
def osm_structured_areas_processed(osm, root):
    areas_2d = root.find("/Areas")

    subtract = root.find("/Ways").select('["ddd:layer" ~ "0|-1a"]')
    subtract = osm.areas2.generate_union_safe(subtract)

    osm.areas2.generate_areas_2d_process(areas_2d, subtract)


@dddtask(log=True)
def osm_structured_building_link_items_nodes(root, osm):
    """Associate features (amenities, etc) to buildings."""
    # TODO: There is some logic for specific items inside: use tagging for linkable items.
    items = root.find("/ItemsNodes")
    buildings = root.find("/Buildings")
    osm.buildings.link_items_to_buildings(buildings, items)


@dddtask(log=True)
def osm_structured_building_link_items_ways(root, osm):
    """Associate features (amenities, etc) to buildings."""
    items = root.find("/ItemsWays")
    buildings = root.find("/Buildings")
    osm.buildings.link_items_ways_to_buildings(buildings, items)


@dddtask(path="/ItemsWays/*", select='["ddd:building:parent"]')  # filter=lambda o: "ddd:building:parent" in o.extra)  #
def osm_structured_building_link_items_ways_elevation(root, osm, obj):
    obj.extra['ddd:elevation'] = 'building'
    obj.extra['_height_mapping'] = 'none'


@dddtask()
def osm_structured_items_2d_generate(root, osm):
    # Generates items defined as areas (area fountains, football fields...)
    #osm.items2.generate_items_2d()  # Objects related to areas (fountains, playgrounds...)
    pass

@dddtask(order="40.80.+.+")
def osm_structured_ways_2d_generate_roadlines(root, osm, pipeline, logger):
    # TODO: Except roadline,s the rest shall be moved to augmentation, etc... and not pass root around
    # Separate different things: roadlines, etc...
    # Road props (traffic lights, lampposts, fountains, football fields...) - needs. roads, areas, coastline, etc... and buildings
    logger.warn("Separate Roadlines 2D and 3D creation.")
    root.append(ddd.group2(name="Roadlines2"))
    pipeline.data["Roadlines3"] = ddd.group3(name="Roadlines3")
    osm.ways2.generate_props_2d(root.find("/Ways"), pipeline)  # Objects related to ways


@dddtask(order="40.80")
def osm_structured_rest(root, osm):
    pass


@dddtask(order="40.90")
def osm_structured_finished(pipeline, osm, root, logger):
    pass
