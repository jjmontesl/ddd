# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020

import sys


from ddd.pipeline.decorators import dddtask




@dddtask(order="20.1", log=True)
def osm_features_load(pipeline, osm):
    osm.load_geojson(pipeline.data['osmfiles'])
    pass

@dddtask(log=True)
def osm_features_preprocess(pipeline, osm):
    #pipeline.data['osm'].preprocess_features()
    osm.preprocess_features()
    pipeline.root.append(osm.features_2d)



# Filter to only features if specified
@dddtask(log=True)
def osm_features_filter_custom(pipeline, osm, root, logger):
    selector = pipeline.data.get('ddd:osm:filter', None)
    if selector:
        filtered = root.find("/Features").select(selector=selector)
        logger.info("Filtering to only custom selected features: %s (%d items)", selector, len(filtered.children))
        root.find("/Features").children = filtered.children


@dddtask(path="/Features/*", log=True)  # and o.geom.type in ('Point', 'Polygon', 'MultiPolygon') .. and o.geom.type == 'Polygon' |  ... path="/Features", select=r'["geom:type"="Polygon"]'
def osm_features_crop_extended_area(pipeline, osm, root, obj):
    """Crops to extended area size to avoid working with huge areas."""

    # TODO: Crop centroids of buildings and lines and entire areas...
    #pipeline.data['osm'].preprocess_features()
    #osm.preprocess_features()
    obj.extra['osm:original'] = obj.copy()
    obj = obj.intersection(osm.area_filter2)
    return obj


# Filtering for non-represented features

@dddtask(path="/Features/*", select='["osm:route:bus"]')
def osm_select_ways_routes_remove(obj, root):
    """Remove routes."""
    return False



'''
@dddtask(select='[osm:element="relation"]')
def osm_load_remove_relations():
    # TEMPORARY ? they shall be simmply not picked
    #obj = obj.material(ddd.mats.outline)
    #obj.extra['ddd:enabled'] = False
    #return False  # TODO: return... ddd.REMOVE APPLY:REMOVE ?... (depends on final api for this)
    pass
'''


'''
@dddtask(select='[osm:boundary]')
def stage_11_hide_relations(obj):
    obj = obj.material(ddd.mats.outline)
    #obj.data['ddd:visible': False]
    return False

@dddtask(select='[osm:boundary]')
def stage_11_hide_boundaries(obj):
    obj = obj.material(ddd.mats.outline)
    #obj.data['ddd:visible': False]
    return False
'''

@dddtask(order="20.95.+", cache=True)
def osm_features_cache(pipeline, osm, root, logger):
    """
    Caches current state to allow for faster reruns.
    """
    return pipeline.data['filenamebase'] + ".s20.cache"

