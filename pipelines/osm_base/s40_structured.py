# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020

from ddd.osm import osm
from ddd.pipeline.decorators import dddtask


@dddtask(order="40.10.+", log=True)
def osm_structured_init(root, osm):
    #osm.ways_1d = root.find("/Ways")
    pass


@dddtask()
def osm_structured_split_ways(osm, root):
    osm.ways1.split_ways_1d(root.find("/Ways"))  # Where to put?

@dddtask()
def osm_structured_link_ways_items(osm, root):
    osm.ways1.ways_1d_link_items(root.find("/Ways"), root.find("/Items"))


@dddtask()
def osm_structured_buildings(osm, root):
    # dependencies? (document)
    osm.buildings.preprocess_buildings_2d()

    root.find("/Buildings").children = []  # Remove as they will be generated from features: TODO: change this
    osm.buildings.generate_buildings_2d(root.find("/Buildings"))

@dddtask()
def osm_structured_generate_ways_2d(osm, root):
    """Generates ways 2D (areas) from ways 1D (lines), replacing the /Ways node in the hierarchy."""
    ways1 = root.find("/Ways")
    root.remove(ways1)

    ways2 = osm.ways2.generate_ways_2d(ways1)
    root.append(ways2)


@dddtask()
def osm_structured_areas_processed(osm, root):
    areas_2d = root.find("/Areas")
    subtract = root.find("/Ways").select('["ddd:layer" ~ "0|-1a"]')
    osm.areas2.generate_areas_2d_process(areas_2d, subtract)  # Where to put?

@dddtask()
def osm_generate_areas_interways(pipeline, osm, root, logger):
    osm.areas2.generate_areas_2d_interways()

@dddtask()
def osm_generate_areas_ground_2d(osm, root):
    """Ground must come after every other area (interways, etc), as it is used to "fill" missing gaps. It requires Ways2 to have been generated."""
    #osm.areas.generate_coastline_2d(osm.area_crop if osm.area_crop else osm.area_filter)  # must come before ground
    osm.areas2.generate_ground_2d(osm.area_filter)  # must come before ground
    for a in osm.ground_2d.children:
        root.find("/Areas").append(a)

@dddtask(log=True)
def osm_structured_rest(root, osm):

    #root.find("/Ways").replace(osm.ways_1d)

    osm.areas2.generate_areas_2d_postprocess()
    osm.areas2.generate_areas_2d_postprocess_water()

    # Associate features (amenities, etc) to 2D objects (buildings, etc)
    osm.buildings.link_features_2d()


@dddtask(order="40.90")
def osm_structured_finished(pipeline, osm, root, logger):
    pass
