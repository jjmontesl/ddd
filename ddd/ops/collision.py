# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging
import math
import sys

from shapely.geometry.polygon import LinearRing

#from ddd.ddd import ddd, DDDObject3, DDDObject
import numpy as np
from trimesh.transformations import quaternion_from_euler
from trimesh import transformations

from ddd.nodes.node3 import DDDNode3


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class AABox(DDDNode3):
    """
    Axis-aligned box.

    TODO: Separate from Node3 (should be only "trimesh mesh" if anything, or a primitive) Move to primitives (check Trimesh primitives)
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

    def rotate(self, v, origin="local"):
        obj = self.copy()

        rot = quaternion_from_euler(v[0], v[1], v[2], "sxyz")
        rotation_matrix = transformations.quaternion_matrix(rot)
        #rot = transformations.euler_matrix(v[0], v[1], v[2], 'sxyz')

        center_coords = None
        if origin == 'local':
            center_coords = None
        elif origin == 'bounds_center':  # group_centroid, use for children
            ((xmin, ymin, zmin), (xmax, ymax, zmax)) = self.bounds()
            center_coords = [(xmin + xmax) / 2, (ymin + ymax) / 2, (zmin + zmax) / 2]
        elif origin:
            center_coords = origin

        if center_coords:
            #translate_before = transformations.translation_matrix(np.array(center_coords) * -1)
            #translate_after = transformations.translation_matrix(np.array(center_coords))
            #transf = translate_before * rot # * rot * translate_after  # doesn't work, these matrifes are 4x3, not 4x4 HTM

            obj.center = obj.center - np.array(center_coords)
            obj.center = np.dot(rotation_matrix, list(obj.center) + [1])[:3]  # Hack: use matrices
            obj.center = obj.center + np.array(center_coords)

            obj.size = np.abs(np.dot(rotation_matrix, list(obj.size) + [1])[:3])  # Hack: use matrices
        else:
            #transf = rot
            obj.center = np.dot(rotation_matrix, list(obj.center) + [1])[:3]  # Hack: use matrices
            obj.size = np.abs(np.dot(rotation_matrix, list(obj.size) + [1])[:3])  # Hack: use matrices

        return obj


class DDDCollision():

    def aabox_from_aabb(self, obj):
        """
        Adds a box collider to the object, using object AABB for dimensions.
        """

        #logger.debug("Adding AABox collider to object: %s", obj)
        bounds = obj.bounds()
        collider = AABox.from_bounds(bounds)

        obj.prop_set('ddd:collider:primitive', collider)

        return obj


