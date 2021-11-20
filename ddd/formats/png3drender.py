# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

from builtins import staticmethod
import logging

from ddd.render.offscreen import Offscreen3DRenderer
from trimesh import transformations


# Get instance of logger for this module
logger = logging.getLogger(__name__)

class DDDPNG3DRenderFormat():

    @staticmethod
    def export_png_3d_render(obj, instance_mesh=True, instance_marker=False, size=None):
        """
        Saves a rendered image to PNG.
        """

        if size is None:
            size = (1280, 720)

        image = Offscreen3DRenderer.render(obj, instance_mesh=True, instance_marker=False, size=size)
        return image

