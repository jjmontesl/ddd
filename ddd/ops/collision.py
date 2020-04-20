# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging
import math
import sys

from shapely.geometry.polygon import LinearRing

from ddd.ddd import ddd, DDDObject3, DDDObject
import numpy as np
from trimesh.transformations import quaternion_from_euler
from trimesh import transformations


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class AABox(DDDObject):
    """
    Axis-aligned box.

    TODO: Move to primitives
    """

    @staticmethod
    def from_bounds(bounds):
        result = AABox()
        # result.bounds = bounds
        result.center = np.average(bounds, axis=0)
        result.size = bounds[1] - bounds[0]
        #print(result)
        #print(result.export())
        return result

    def copy(self):
        result = AABox()
        result.center = self.center
        result.size = self.size
        return result

    def export(self):
        return {"type": "BoxCollider",
                "center": list(self.center),
                "size": list(self.size)}

    def translate(self, v):
        obj = self.copy()
        obj.center = obj.center + v  # Hack: use matrices
        return obj

    def rotate(self, v):
        obj = self.copy()
        rot = quaternion_from_euler(v[0], v[1], v[2], "sxyz")
        rotation_matrix = transformations.quaternion_matrix(rot)
        obj.center = np.dot(rotation_matrix, list(obj.center) + [1])[:3]  # Hack: use matrices
        obj.size = np.abs(np.dot(rotation_matrix, list(obj.size) + [1])[:3])  # Hack: use matrices
        return obj


class DDDCollision():

    def aabox_from_aabb(self, obj):
        """
        Adds a box collider to the object, using object AABB for dimensions.
        """

        logger.info("Adding AABox collider to object: %s", obj)
        bounds = obj.bounds()
        collider = AABox.from_bounds(bounds)

        obj.prop_set('ddd:collider:primitive', collider)

        return obj


