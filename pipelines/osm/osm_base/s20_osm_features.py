# ddd - DDD123
# Library for simple scene modelling.
# Jose Juan Montes and Contributors 2019-2023

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


@dddtask(path="/Features/*")
def osm_features_crop_extended_area(pipeline, osm, root, obj, logger):
    """Crops to extended area size to avoid working with huge areas."""

    # TODO: Crop centroids of buildings and lines and entire areas...
    #pipeline.data['osm'].preprocess_features()
    #osm.preprocess_features()
    #logger.info(obj)
    obj.extra['osm:original'] = obj.copy()

    #obj = obj.intersection(osm.area_filter2)  # old method
    if not obj.intersects(osm.area_filter2):
        return False

    # This is CRITICAL, but poorly justified... walls and others need to keep orientation (left vs side)
    # Formerly, the (incorrect) intersection with area_filter2 caused the reordering :o
    # If there shoudl be a preferred orientation for polygons/multipol, should it be OSM, GeoJSON's, Shapely?
    # Reordering of polygons is done here as otherwise buildings are analyzed incorrectly (and windows and other features are reversed inside)
    # Perhaps, if orientation is needed, it can/must be enforced later: e.g. before analyzing buildings

    # This is possibly incorrect (rivers, coastlines...)
    if obj.get('osm:building', None) or obj.get('osm:building:part', None):
        obj = obj.orient(ccw=False)

    #obj = obj.clean(eps=0.0)
    #obj.validate()

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
def osm_features_cache(pipeline, root, logger):
    """
    Caches current state to allow for faster reruns.
    """
    return pipeline.data['filenamebase'] + ".s20.cache"

