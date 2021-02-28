# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020


from ddd.pipeline.decorators import dddtask


@dddtask(order="69.90.+")
def osm_model_export_3d(root, osm, pipeline):

    #root = root.copy()
    #root.find("/Areas").replace(root.find("/Areas").material(ddd.mats.park).prop_set('svg:fill-opacity', 0.6, True))
    #root.find("/Ways").replace(root.find("/Ways").buffer(1.0).material(ddd.mats.asphalt).prop_set('svg:fill-opacity', 0.8, True))
    #root.find("/Buildings").replace(root.find("/Buildings").material(ddd.mats.stone).prop_set('svg:fill-opacity', 0.7, True))
    #root.find("/Items").replace(root.find("/Items").buffer(1.0).material(ddd.mats.highlight))

    if bool(pipeline.data.get('ddd:osm:output:json', False)):
        root.save("/tmp/osm-model.json")

    #if bool(pipeline.data.get('ddd:osm:output:intermediate', False)):
    #root.save("/tmp/osm-model.glb")

    root.save(pipeline.data['filenamebase'] + ".glb")

    #scene.dump()


