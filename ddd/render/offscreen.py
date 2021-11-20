# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import json
import logging
import math

from shapely import geometry, affinity, ops
from trimesh import transformations
import trimesh
import numpy as np

from ddd.core.exception import DDDException
from ddd.core.cli import D1D2D3Bootstrap
from builtins import staticmethod
from abc import abstractstaticmethod
from shapely.geometry.base import BaseMultipartGeometry
import base64


# Get instance of logger for this module
logger = logging.getLogger(__name__)

class Offscreen3DRenderer():
    """

    """

    @staticmethod
    def render(obj, instance_mesh=True, instance_marker=False, size=(1280, 720)):
        """
        Renders an image (offscreen).
        """

        obj = obj.rotate([-math.pi / 2.0, 0, 0])
        scene = obj._recurse_scene_tree("", "", instance_mesh=instance_mesh, instance_marker=instance_marker, include_metadata=False)

        # a 45 degree homogeneous rotation matrix around
        # the Y axis at the scene centroid
        rotate = trimesh.transformations.rotation_matrix(
            angle=np.radians(0.0),
            direction=[0, 1, 0],
            point=scene.centroid)

        for i in range(4):
            # rotate the camera view transform
            camera_old, _geometry = scene.graph[scene.camera.name]
            camera_new = np.dot(rotate, camera_old)

            # apply the new transform
            scene.graph[scene.camera.name] = camera_new

            png = scene.save_image(resolution=size, visible=True)  # Seems we get a black image with visible=False ?

            return png


