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


@dddtask(path="/Features/*", log=True)  # and o.geom.type in ('Point', 'Polygon', 'MultiPolygon') .. and o.geom.type == 'Polygon' |  ... path="/Features", select=r'["geom:type"="Polygon"]'
def osm_features_crop_extended_area(pipeline, osm, root, obj):
    """Crops to extended area size to avoid working with huge areas."""

    # TODO: Crop centroids of buildings and lines and entire areas...

    #pipeline.data['osm'].preprocess_features()
    #osm.preprocess_features()
    obj = obj.intersection(osm.area_filter2)
    return obj


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
