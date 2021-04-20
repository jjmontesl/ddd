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



@dddtask(path="/Buildings/*", select='["osm:building" = "shed"]')
def osm_buildings_(pipeline, osm, root, obj):
    """
    Set defaults to sheds.
    """
    obj.set('ddd:building:levels', default=1)
    obj.set('ddd:building:material', default="wood")
    obj.set('ddd:roof:material', default="wood")
    obj.set('ddd:roof:shape', default="flat")
    obj = obj.material(ddd.mats.wood)
    return obj



