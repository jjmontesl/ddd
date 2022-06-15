# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

from builtins import staticmethod
import logging
import subprocess

from ddd.render.offscreen import Offscreen3DRenderer
from trimesh import transformations


# Get instance of logger for this module
logger = logging.getLogger(__name__)

class DDDFBXFormat():

    @staticmethod
    def export_fbx(obj, filename):
        """
        """

        tmpscript = "/tmp/ddd-blender-fbx-convert.py"
        tmpglbfile = "/tmp/tmpfbx.glb"
        targetfbxfile = filename

        # Save temporary GLB file
        obj.save(tmpglbfile)

        # Convert through blender

        blender_convert_script = f"""
import bpy
import time
import sys

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath="{tmpglbfile}")
bpy.ops.export_scene.fbx(filepath="{targetfbxfile}")

#time.sleep(2)
#bpy.ops.wm.quit_blender()
sys.exit(0)
        """

        logger.debug("Blender convert script:\n%s", blender_convert_script)
        with open(tmpscript, "w") as f:
            f.write(blender_convert_script)

        command = f'blender --no-window-focus -noaudio -P {tmpscript}'
        logger.info("Blender convert command: %s", command)

        process = subprocess.Popen(command, shell=True)  # , stdout=subprocess.PIPE)
        process.wait()
        #print(process.returncode)

        return False


