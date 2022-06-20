# ddd - DDD123
# Library for simple scene modelling.
# Jose Juan Montes 2021

import logging
import math
import numpy as np
from trimesh import transformations
import trimesh

# Get instance of logger for this module
logger = logging.getLogger(__name__)


'''
class Transform(tuple):
    """
    """

    def __init__(self):
        self.matrix = None
        #self.inverse = None
'''


class DDDTransform():
    """
    Stores position, rotation and scale.

    These can be used to form an homogeneous transformation matrix (HTM).
    """

    def __init__(self):
        self.position = [0, 0, 0]
        self.rotation = transformations.quaternion_from_euler(0, 0, 0, "sxyz")
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
