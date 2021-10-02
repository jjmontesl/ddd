# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020


from ddd.pipeline.decorators import dddtask
from ddd.ddd import ddd
from ddd.util.common import parse_bool
import subprocess
import os


@dddtask(order="80.10.10.+")
def osm_model_3d_compress_draco(root, osm, pipeline, logger):
    """
    Compresses the pipeline GLB output using draco.
    """
    if not parse_bool(pipeline.data.get('ddd:osm:output:compress', True)):
        return

    input_file = pipeline.data['filenamebase'] + ".glb"
    output_file = pipeline.data['filenamebase'] + ".compressed.glb"

    draco_home = "/home/jjmontes/git/ddd-gltf-draco/"
    draco_script = draco_home + "node_modules/gltf-pipeline/bin/gltf-pipeline.js"
    node_bin = "node"

    input_file_abs = os.path.abspath(input_file)
    output_file_abs = os.path.abspath(output_file)

    logger.info("Compressing GLB file to: %s", output_file_abs)

    #command = f'{node_bin} {draco_script} -d --draco.compressionLevel=0 --draco.unifiedQuantization=true --draco.quantizePositionBits=11 -i {input_file_abs} -o {output_file_abs}'
    command = f'{node_bin} {draco_script} -d --draco.compressionLevel=0 --draco.unifiedQuantization=true --draco.quantizePositionBits=12 -i {input_file_abs} -o {output_file_abs}'
    subprocess.run(command, cwd=draco_home, shell=True, check=True)  # requires Python 3.5

    # Compare sizes
    input_size = os.path.getsize(input_file)
    output_size = os.path.getsize(output_file)
    logger.info("  Input:  %s B", input_size)
    logger.info("  Output: %s B (%.2f %%, %s B)", output_size, output_size / input_size, output_size - input_size)



    # Exchange files
    original_file = pipeline.data['filenamebase'] + ".uncompressed.glb"
    os.rename(input_file, original_file)
    os.rename(output_file, input_file)
