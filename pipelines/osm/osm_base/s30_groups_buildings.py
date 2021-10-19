# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020


import random

from ddd.ddd import ddd
from ddd.pipeline.decorators import dddtask
from ddd.util.common import parse_bool

"""
Buildings are preprocessed and selected in this stage. Then metadata is assigned.

Preprocessing involves:

- Assigning each building part to a building, or transforming it into a building if needed.


"""


@dddtask(order="30.40", condition=True)
def osm_generate_buildings_condition(pipeline):
    return parse_bool(pipeline.data.get('ddd:osm:buildings', True))


@dddtask(order="30.40.5.+", path="/Features/*", select='["geom:type" != "Point"]["geom:type" != "MultiLineString"]',
         filter=lambda o: o.extra.get("osm:building", None) is not None or o.extra.get("osm:building:part", None) is not None, log=True)
def osm_generate_buildings_select_features(root, obj):
    item = obj.copy(name="Building: %s" % obj.name)

    # TODO: Initialization of technical metadata shall be left to preprocess_, which actually manages it
    #item.extra['ddd:building:items'] = []
    if 'ddd:building:parts' not in item.extra: item.extra['ddd:building:parts'] = []

    item = item.material(random.choice([ddd.mats.building_1, ddd.mats.building_2, ddd.mats.building_3, ddd.mats.building_4, ddd.mats.building_5]))
    root.find("/Buildings").append(item)


@dddtask(order="30.40.10.+")
def osm_generate_buildings_parenting(pipeline, osm, root, logger):
    """
    Preprocesses buildings at OSM feature level, associating buildings and building parts.

    """
    buildings = root.find("/Buildings")

    buildings = osm.buildings2.preprocess_buildings_individualize(buildings)
    root.find("/Buildings").replace(buildings)

    osm.buildings2.preprocess_buildings_parenting(buildings)


@dddtask(order="30.40.20.+")
def osm_generate_buildings_postprocess(pipeline, osm, root, logger):
    pass


# Buildings attributes that can be done before structure (ways analysis, etc)
# TODO: FIXME: this will set ddd:*, so osm:* needs to be copied beforehand if it exists


# Settings per building attributes (bieng more specific, here we apply defaults first)

@dddtask(path="/Buildings/*", select='["osm:historic:civilization" = "ancient_roman"]')
def osm_buildings_historic_civilization_ancient_roman(pipeline, osm, root, obj):
    """
    Set defaults to parking_entrance.
    """
    obj.set('ddd:building:material', default="tiles_stones_veg_sparse")
    obj = obj.material(ddd.mats.tiles_stones_veg_sparse)
    return obj


# Settings per building type

@dddtask(path="/Buildings/*", select='["osm:amenity" = "cafe"]')
def osm_buildings_amenity_cafe(pipeline, osm, root, obj):
    """
    Set defaults to cafe buildings.
    """
    obj.set('ddd:building:levels', default=1)
    obj.set('ddd:building:material', default="stone_white")
    obj.set('ddd:roof:shape', default="hipped")
    obj = obj.material(ddd.mats.stones_white)
    return obj

@dddtask(path="/Buildings/*", select='["osm:amenity" = "parking_entrance"]')
def osm_buildings_amenity_parking_entrance(pipeline, osm, root, obj):
    """
    Set defaults to parking_entrance.
    """
    obj.set('ddd:building:levels', default=1)
    obj.set('ddd:building:material', default="glass")
    obj.set('ddd:roof:shape', default="flat")
    obj = obj.material(ddd.mats.glass)
    return obj

@dddtask(path="/Buildings/*", select='["osm:man_made" = "lighthouse"]')
def osm_generate_buildings_man_made_lighthouse(pipeline, osm, root, obj):
    #obj.set('ddd:building:levels', default=1)
    #obj.set('ddd:building:material', default="stone")
    obj.set('ddd:building:windows', default='no')
    return obj

@dddtask(path="/Buildings/*", select='["osm:man_made" = "reservoir_covered"]')
def osm_generate_buildings_man_made_reservoir_covered(pipeline, osm, root, obj):
    obj.set('ddd:building:levels', default=1)

    # Do not adjust floor 0 height so building can stay half-buried
    # Should also look at "location=*" (surfacem, underground) here and in buildings to arrange floor 0
    #obj.set('ddd:building:levels:0:elevation-height', default=False)

    obj.set('ddd:building:material', default="stone")
    obj = obj.material(ddd.mats.tiles_stones)
    return obj


@dddtask(path="/Buildings/*", select='["osm:building" = "roof"]["osm:amenity" = "fuel"]')
def osm_buildings_building_roof_fuel(pipeline, osm, root, obj):
    """
    Set defaults to sheds.
    """
    obj.set('ddd:building:levels', default=3)  # TODO: use height, not levels
    obj.set('ddd:building:levels:0:height', default=8.5)  # TODO: use height, not levels
    #obj.set('ddd:building:material', default="steel")
    obj.set('ddd:roof:material', default="metal")
    obj.set('ddd:roof:shape', default=random.choice(["skillion", "flat"]))
    #obj = obj.material(ddd.mats.steel)
    return obj

@dddtask(path="/Buildings/*", select='["osm:building" = "roof"]')
def osm_buildings_building_roof(pipeline, osm, root, obj):
    """
    Set defaults to sheds.
    """
    obj.set('ddd:building:levels', default=1)
    #obj.set('ddd:building:material', default="steel")
    obj.set('ddd:roof:material', default="wood")
    obj.set('ddd:roof:shape', default=random.choice(["gabled", "skillion"]))
    #obj = obj.material(ddd.mats.steel)
    return obj


@dddtask(path="/Buildings/*", select='["osm:building" = "shed"]')
def osm_buildings_building_shed(pipeline, osm, root, obj):
    """
    Set defaults to sheds.
    """
    obj.set('ddd:building:levels', default=1)
    obj.set('ddd:building:material', default="wood")
    obj.set('ddd:roof:material', default="wood")
    obj.set('ddd:roof:shape', default="flat")
    obj = obj.material(ddd.mats.wood)
    return obj

# Materials

@dddtask(path="/Buildings/*", select='["osm:building:material" = "timber_framing"]')
def osm_buildings_building_material_timber_framing(pipeline, osm, root, obj):
    obj.set('ddd:building:material', "wood")

@dddtask(path="/Buildings/*", select='["osm:roof:material" = "timber_framing"]')
def osm_buildings_roof_material_timber_framing(pipeline, osm, root, obj):
    obj.set('ddd:roof:material', "wood")

