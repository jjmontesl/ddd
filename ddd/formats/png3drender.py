# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import json
import logging
import math

from shapely import geometry, affinity, ops
from trimesh import transformations

from ddd.core.exception import DDDException
from ddd.core.cli import D1D2D3Bootstrap
from builtins import staticmethod
from abc import abstractstaticmethod
from shapely.geometry.base import BaseMultipartGeometry
import base64
from ddd.render.rendering import DDD3DRenderer


# Get instance of logger for this module
logger = logging.getLogger(__name__)

class DDDPNG3DRenderFormat():

    @staticmethod
    def export_png_3d_render(obj, instance_mesh=True, instance_marker=False, size=(1280, 720)):
        """
        Saves a rendered image to PNG.
        """

        image = DDD3DRenderer.render(obj, instance_mesh=True, instance_marker=False, size=(1280, 720))
        return image

