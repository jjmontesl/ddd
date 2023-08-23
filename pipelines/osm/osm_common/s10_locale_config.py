# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020-2023

from ddd.ddd import ddd
from ddd.pipeline.decorators import dddtask


#@dddgroupgeocondition(select='osm.center [contains()')
@dddtask(order="10.10.10.+")  # [!contains(["natural"="tree"])]
def osm_config_locale(root, osm, pipeline):
    pipeline.data['ddd:config:items'] = ddd.group2()
    pass

@dddtask()
def osm_config_locale_es_salamanca(root, osm, pipeline):
    config = ddd.point([-5.664, 40.965], name="Salamanca Config")
    config.extra['osm:tree:type'] = {'default': 1, 'fir': 0.5}
    #config.extra['ddd:aug:itemfill:types'] = {'default': 1, 'fir': 1}

    pipeline.data['ddd:config:items'].append(config)

@dddtask()
def osm_config_locale_es_vigo(root, osm, pipeline):
    config = ddd.point([-8.723, 42.238], name="Vigo Config")
    config.extra['osm:tree:type'] = {'default': 1.9, 'fir': 0.1 }  #, 'fir': 1, 'palm': 0.25}
    #config.extra['ddd:aug:itemfill:types'] = {'default': 1, 'fir': 1}

    pipeline.data['ddd:config:items'].append(config)

@dddtask()
def osm_config_locale_es_huesca(root, osm, pipeline):
    config = ddd.point([-0.4116850, 42.1367415], name="Huesca Config")
    config.extra['osm:tree:type'] = {'default': 1, 'fir': 0.1 }  #, 'fir': 1, 'palm': 0.25}
    #config.extra['ddd:aug:itemfill:types'] = {'default': 1, 'fir': 1}

    pipeline.data['ddd:config:items'].append(config)

@dddtask()
def osm_config_locale_es_vilanovailageltru(root, osm, pipeline):
    config = ddd.point([1.725,41.224], name="Vilanova i la Geltrú Config")
    config.extra['osm:tree:type'] = {'default': 0.5, 'fir': 0.25, 'palm': 1}
    #config.extra['ddd:aug:itemfill:types'] = {'default': 1, 'fir': 1}

    pipeline.data['ddd:config:items'].append(config)


@dddtask(order="10.10.90.+")  # [!contains(["natural"="tree"])]
def osm_config_locale_apply(logger, root, osm, pipeline):
    # Find closest config point
    center = osm.area_crop2.centroid()

    items = pipeline.data['ddd:config:items']
    items = osm.project_coordinates(items, osm.osm_proj, osm.ddd_proj)

    (closest_object, closest_distance) = items.closest(center)
    logger.info("Config selected: %s (%s m)", closest_object, closest_distance)

    # Apply config to pipeline
    pipeline.data.update(closest_object.extra)
    logger.info("Pipeline data: %s", pipeline.data)

