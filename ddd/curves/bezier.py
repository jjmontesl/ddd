# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging
import math
import shapely
import numpy as np

from ddd.core.exception import DDDException
from ddd.curves.path import DDDCurve
from ddd.math.vector2 import Vector2
from ddd.ddd import ddd, DDDObject2, Node
from trimesh.path.curve import binomial


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class DDDBezierCurve(DDDCurve):
    """
    """

    def __init__(self, vertices):
        self.vertices = vertices

    def evaluate(self, t):
        return self.discretize_bezier(t)

    def discretize_bezier(self, t, scale=1.0):
        """
        """
        # make sure we have a numpy array
        #print(t)

        points = self.vertices
        points = np.asanyarray(points, dtype=np.float64)

        # decrementing 1.0-0.0
        t_d = 1.0 - t
        n = len(points) - 1
        # binomial coefficients, i, and each point
        iterable = zip(binomial(n), np.arange(len(points)), points)
        # run the actual interpolation
        stacked = [((t**i) * (t_d**(n - i))).reshape((-1, 1))
                * p * c for c, i, p in iterable]
        result = np.sum(stacked, axis=0)

        # test to make sure end points are correct
        #test = np.sum((result[[0, -1]] - points[[0, -1]])**2, axis=1)
        #tol_merge = 1e-5
        #assert (test < tol_merge).all()
        #assert len(result) >= 2

        return result

