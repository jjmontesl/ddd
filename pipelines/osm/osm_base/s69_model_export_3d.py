# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020


from ddd.pipeline.decorators import dddtask
from ddd.ddd import ddd
from ddd.util.common import parse_bool


@dddtask(order="69.90.+")
def osm_model_export_3d(root, osm, pipeline, logger):

    #root = root.copy()
    #root.find("/Areas").replace(root.find("/Areas").material(ddd.mats.park).prop_set('svg:fill-opacity', 0.6, True))
    #root.find("/Ways").replace(root.find("/Ways").buffer(1.0).material(ddd.mats.asphalt).prop_set('svg:fill-opacity', 0.8, True))
    #root.find("/Buildings").replace(root.find("/Buildings").material(ddd.mats.stone).prop_set('svg:fill-opacity', 0.7, True))
    #root.find("/Items").replace(root.find("/Items").buffer(1.0).material(ddd.mats.highlight))

    if parse_bool(pipeline.data.get('ddd:osm:output:json', False)):
        root.save("/tmp/osm-model.json")

    #if bool(pipeline.data.get('ddd:osm:output:intermediate', False)):
    #root.save("/tmp/osm-model.glb")


    #root.dump()
    #root = root.clean()  # Test (issues with Babylon picking - meshes with no or invalid indices or vertices)
    root.save(pipeline.data['filenamebase'] + ".glb")

    # PNG
    #root.rotate(ddd.ROT_FLOOR_TO_FRONT).save(pipeline.data['filenamebase'] + ".render.png", size=(512, 512))
    #root.rotate(ddd.ROT_FLOOR_TO_FRONT).show()

    # Reduction tests
    #lod1 = root.copy()
    #lod1.show()
    #logger.info("Reducing model: %s", lod1)
    #lod1 = lod1.combine()
    #lod1 = ddd.meshops.reduce_quadric_decimation(lod1, target_ratio=0.25)
    #del(lod1.extra['uv'])
    #lod1 = lod1.material(ddd.mats.highlight)
    #lod1.dump()
    #lod1.show()
    #lod1.save(pipeline.data['filenamebase'] + ".lod-onemesh.glb")

    #scene.dump()


