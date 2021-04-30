# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020


import random

from ddd.ddd import ddd
from ddd.pipeline.decorators import dddtask


@dddtask(order="30.40", condition=True)
def osm_generate_buildings_condition(pipeline):
    return bool(pipeline.data.get('ddd:osm:buildings', True))


@dddtask(order="30.40.5.+")
def osm_generate_buildings_preprocess(pipeline, osm, root, logger):
    """Preprocesses buildings at OSM feature level, associating buildings and building parts."""
    features = root.find("/Features")
    osm.buildings.preprocess_buildings_features(features)

# TODO: Generate building materials before 3D, in this section. Also, this section is already structuring, should not be here.

@dddtask(order="30.40.10.+", path="/Features/*", select='["geom:type" != "Point"]', filter=lambda o: o.extra.get("osm:building", None) is not None or o.extra.get("osm:building:part", None) is not None, log=True)
def osm_generate_buildings(root, obj):
    item = obj.copy(name="Building: %s" % obj.name)
    item.extra['ddd:building:items'] = []
    if 'ddd:building:parts' not in item.extra: item.extra['ddd:building:parts'] = []
    item = item.material(random.choice([ddd.mats.building_1, ddd.mats.building_2, ddd.mats.building_3]))
    root.find("/Buildings").append(item)


@dddtask(order="30.40.20.+")
def osm_generate_buildings_postprocess(pipeline, osm, root, logger):
    pass


# Buildings attributes that can be done before structure (ways analysis, etc)

# TODO: FIXME: this will set ddd:*, so osm:* needs to be copied beforehand if it exists


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


@dddtask(path="/Buildings/*", select='["osm:man_made" = "reservoir_covered"]')
def osm_generate_buildings_man_made_reservoir_covered(pipeline, osm, root, obj):
    obj.set('ddd:building:levels', default=1)
    obj.set('ddd:building:material', default="stone")
    obj = obj.material(ddd.mats.tiles_stones)
    return obj

@dddtask(path="/Buildings/*", select='["osm:building" = "roof"]')
def osm_buildings_building_roof(pipeline, osm, root, obj):
    """
    Set defaults to sheds.
    """
    obj.set('ddd:building:levels', default=1)
    #obj.set('ddd:building:material', default="steel")
    obj.set('ddd:roof:material', default="wood")
    obj.set('ddd:roof:shape', default="hipped")
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



