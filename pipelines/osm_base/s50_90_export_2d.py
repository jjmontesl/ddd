# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020


from ddd.pipeline.decorators import dddtask
from ddd.ddd import ddd


@dddtask(order="59.90", condition=True)
def osm_processed_export_2d_condition(pipeline):
    return bool(pipeline.data.get('ddd:osm:output:intermediate', False))


@dddtask(order="59.90.+")
def osm_processed_export_2d(root, osm):


    root = root.copy()
    root = root.remove(root.find("/Features"))  # !Altering
    root.prop_set('svg:stroke-width', 0.1, children=True)
    #root.prop_set('svg:fill-opacity', 0.7, children=True)

    #root.find("/Areas").replace(root.find("/Areas").material(ddd.mats.park).prop_set('svg:fill-opacity', 0.6, True))
    #root.find("/Ways").replace(root.find("/Ways").buffer(1.0).material(ddd.mats.asphalt).prop_set('svg:fill-opacity', 0.8, True))
    #root.find("/Buildings").replace(root.find("/Buildings").material(ddd.mats.stone).prop_set('svg:fill-opacity', 0.7, True))
    #root.find("/Items").replace(root.find("/Items").buffer(1.0).material(ddd.mats.highlight))

    root.save("/tmp/osm-processed.json")
    root.save("/tmp/osm-processed.svg")


@dddtask(order="59.95.+", cache=True)
def osm_processed_cache(pipeline, osm, root, logger):
    """
    Caches current state to allow for faster reruns.
    """
    return pipeline.data['filenamebase'] + ".s50.cache"

