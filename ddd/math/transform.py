# ddd - DDD123
# Library for simple scene modelling.
# Jose Juan Montes 2021

import logging
import math
import numpy as np
from trimesh import transformations
import trimesh

from ddd.math.vector3 import Vector3

# Get instance of logger for this module
logger = logging.getLogger(__name__)



class DDDTransform():
    """
    Stores position, rotation and scale.

    These can be used to form an homogeneous transformation matrix (HTM).
    """

    _quaternion_identity = transformations.quaternion_from_euler(0, 0, 0, "sxyz")

    def __init__(self):
        self.position = [0, 0, 0]
        self.rotation = DDDTransform._quaternion_identity
        self.scale = [1, 1, 1]

    def __str__(self):
        return "DDDTransform(pos=%s, rot=%s, s=%s)" % (self.position, self.rotation, self.scale)

    def copy(self):
        result = DDDTransform()
        result.position = list(self.position)
        result.rotation = list(self.rotation)
        result.scale = list(self.scale)
        return result

    def export(self):
        """
        TODO: Rename to 'to_dict()'
        """
        result = {'position': self.position,
                  'rotation': self.rotation,
                  'scale': self.scale}
        return result

    def transform_vertices(self, vertices):
        node_transform = transformations.concatenate_matrices(
            transformations.translation_matrix(self.position),
            transformations.quaternion_matrix(self.rotation)
        )
        return trimesh.transform_points(vertices, node_transform)

    def transform_point(self, point):
        points = self.transform_vertices([point])
        return points[0]

    def forward(self):
        return Vector3(np.dot(self.to_matrix(), [0, 1, 0, 1])[:3])  # Hack: use matrices

    def to_matrix(self):
        """
        Returns a HTM for the translation, rotation and scale represented by this Transform.

        NOTE: This method was created to export Babylon instance lists, the fixed for DDD transforms. The fix for Babylon should go elsewhere.
        NOTE: The copy in ddd.py still has the old method, should be removed from there.
        """

        # For babylon
        #rot = transformations.quaternion_from_euler(-math.pi / 2, math.pi, 0, "sxyz")
        #rotation_matrix = transformations.quaternion_matrix(rot)
        '''
        scale_matrix = np.array(((1.0,   0.0,  0.0,    0.0),
                                 (0.0,    -1.0,  0.0,    0.0),
                                 (0.0,    0.0, 1.0,    0.0),
                                 (0.0,    0.0,  0.0,    1.0)), dtype=np.float64)
        '''

        node_transform = transformations.concatenate_matrices(
            #rotation_matrix,  # For babylon
            #scale_matrix,   # For babylon
            transformations.translation_matrix(self.position),
            #transformations.scale_matrix(self.scale),
            transformations.quaternion_matrix(self.rotation),
        )

        return node_transform

    '''
    def to_array(self):
        return self.to_matrix().flatten()
    '''

    def translate(self, v):
        """Modifies the transform in place."""
        self.position = [self.position[0] + v[0], self.position[1] + v[1], self.position[2] + v[2] if len(v) > 2 else self.position[2]]

    def rotate(self, v, origin=None):

        center_coords = None
        if origin == 'local':
            center_coords = None
        elif origin:
            center_coords = origin

        rot = transformations.quaternion_from_euler(v[0], v[1], v[2], "sxyz")

        #rotation_matrix = transformations.quaternion_matrix(rot)

        if center_coords:
            raise NotImplementedError()
        '''
            translate_before = transformations.translation_matrix(np.array(center_coords) * -1)
            translate_after = transformations.translation_matrix(np.array(center_coords))
            self.position = np.dot(translate_before, self.position + [1])[:3]
            self.position = np.dot(rotation_matrix, self.position + [1])[:3]
            self.position = np.dot(translate_after, self.position + [1])[:3]
        else:
            self.position = np.dot(rotation_matrix, self.position + [1])[:3]
        '''

        self.rotation = transformations.quaternion_multiply(rot, self.rotation)  # order matters!


'''

# Former DDDTransform in DDD (backup, this ione included rotation and scale matrix for babylon :?)

class DDDTransform():
    """
    Stores position, rotation and scale.

    These can be used to form an homogeneous transformation matrix.
    """

    def __init__(self):
        self.position = [0, 0, 0]
        self.rotation = quaternion_from_euler(0, 0, 0, "sxyz")
        self.scale = [1, 1, 1]

    def copy(self):
        result = DDDTransform()
        result.position = list(self.position)
        result.rotation = list(self.rotation)
        result.scale = list(self.scale)
        return result

    def export(self):
        """
        TODO: Rename to 'to_dict()'
        """
        result = {'position': self.position,
                  'rotation': self.rotation,
                  'scale': self.scale}
        return result

    def transform_vertices(self, vertices):
        node_transform = transformations.concatenate_matrices(
            transformations.translation_matrix(self.position),
            transformations.quaternion_matrix(self.rotation)
        )
        return trimesh.transform_points(vertices, node_transform)

    def to_matrix(self):
        """
        Returns a HTM for the translation, rotation and scale represented by this Transform.

        NOTE: This method was created to export Babylon instance lists, and seems to not work for DDD transforms. Rename accordingly?
        """

        #rot = quaternion_from_euler(-math.pi / 2, 0, 0, "sxyz")
        rot = quaternion_from_euler(-math.pi / 2, math.pi, 0, "sxyz")
        rotation_matrix = transformations.quaternion_matrix(rot)

        scale_matrix = np.array(((1.0,   0.0,  0.0,    0.0),
                                 (0.0,    -1.0,  0.0,    0.0),
                                 (0.0,    0.0, 1.0,    0.0),
                                 (0.0,    0.0,  0.0,    1.0)), dtype=np.float64)

        node_transform = transformations.concatenate_matrices(
            rotation_matrix,  # For babylon
            scale_matrix,   # For babylon
            transformations.translation_matrix(self.position),
            #transformations.scale_matrix(self.scale),
            transformations.quaternion_matrix(self.rotation),
        )

        return node_transform

'''
