# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020


from ddd.ddd import ddd
from ddd.geo import terrain
from ddd.osm import osm
from ddd.pipeline.decorators import dddtask
import math
import random
from ddd.geo.sources.population import PopulationModel


"""
Assigns building floors where not available.
"""

#@dddtask(order="45.20.+.+")
@dddtask(order="55.70.+.+")
def osm_augment_building_levels(root, osm, pipeline, logger):
    """
    Assigns building floors where not available.
    """
    pipeline.data['_lamps'] = root.select('["osm:highway" = "street_lamp"]')

@dddtask(path="/Buildings/*", select='[ ! "osm:building:levels"][! "osm:building:height"]["osm:type" != "multipolygon"]')
def osm_augment_building_levels_select(root, osm, pipeline, logger, obj):
    """
    """
    obj.prop_set('ddd:augment:building:levels', default=True)


@dddtask(path="/Buildings/*", select='["ddd:augment:building:levels"]')
def osm_augment_building_levels_apply(root, osm, pipeline, logger, obj):
    """
    """

    coords_ddd = obj.centroid().geom.coords[0]
    coords_wgs84 = terrain.transform_ddd_to_geo(osm.ddd_proj, coords_ddd)

    try:
        population = PopulationModel.instance().population_km2(coords_wgs84)
    except Exception as e:
        logger.error("Error calculating population for point %s: %s", coords_wgs84, e)
        return

    levels = max(int(1 + (population / 750) + random.gauss(0, 2)), 1)

    logger.debug("Population %s: %s (%s levels)", coords_wgs84, population, levels)

    obj.set('ddd:building:levels', levels)





