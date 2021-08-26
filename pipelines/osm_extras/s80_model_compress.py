# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020


from ddd.pipeline.decorators import dddtask
from ddd.ddd import ddd
from ddd.util.common import parse_bool


@dddtask(order="80.10.10.+")
def osm_model_3d_compress_draco(root, osm, pipeline, logger):
    """
    Compresses the pipeline GLB output using draco
    (leaves the original file in place).
    """
    if not parse_bool(pipeline.data.get('ddd:osm:output:compress', True)):
        return

    source_file = pipeline.data['filenamebase'] + ".glb"
    target_file = pipeline.data['filenamebase'] + ".compressed.glb"

    logger.info("Compressing GLB file to: %s", target_file)

    # TODO:

