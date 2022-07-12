# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging
import math
import shapely
import numpy

from ddd.core.exception import DDDException
from ddd.math.vector2 import Vector2
from ddd.ddd import ddd
from ddd.nodes.node2 import DDDNode2


# Get instance of logger for this module
logger = logging.getLogger(__name__)

class DDDCurve():
    """
    Curves are mathematically defined and can be evaluated at any point inside their domain.

    Note: curves are not nodes, use a Path node to represent a curve in space.
    """
    pass


class ParabollaCurve(DDDCurve):
    """
    A parabolla on the the XY plane.
    """

    def __init__(self):
        self.a = None
        self.b = None
        self.c = None

    @staticmethod
    def from_points(a, b, c):
        '''
        Adapted and modifed to get the unknowns for defining a parabola:
        http://stackoverflow.com/questions/717762/how-to-calculate-the-vertex-of-a-parabola-given-three-points
        '''
        x1, y1 = a[:2]
        x2, y2 = b[:2]
        x3, y3 = c[:2]
        denom = (x1-x2) * (x1-x3) * (x2-x3);
        A     = (x3 * (y2-y1) + x2 * (y1-y3) + x1 * (y3-y2)) / denom;
        B     = (x3*x3 * (y1-y2) + x2*x2 * (y3-y1) + x1*x1 * (y2-y3)) / denom;
        C     = (x2 * x3 * (x2-x3) * y1+x3 * x1 * (x3-x1) * y2+x1 * x2 * (x1-x2) * y3) / denom;

        curve = ParabollaCurve()
        curve.a = A
        curve.b = B
        curve.c = C
        return curve

    def evaluate_y(self, x):
        return self.a * x * x + self.b * x + self.c

    #def evaluate(self, t):
    #    return self.a * x * x + self.b * x + self.c


class Path2(DDDNode2):

    def __init__(self, name=None, children=None, extra=None, material=None):
        super().__init__(name, children, extra, material)
        self.curve = None
        self.start = None
        self.end = None

    @staticmethod
    def parabolla_from_geom(obj):
        points = obj.vertex_list()
        if len(points) != 3:
            raise DDDException("Cannot create parabolla from geometry with other than 3 vertices: %s" % obj)
        if obj.children:
            raise DDDException("Cannot create parabolla from geometry with children nodes: %s" % obj)
        path = Path2.parabolla_from_points(points[0], points[2], points[1])
        path.copy_from(obj, copy_material=True, copy_children=True)
        return path

    @staticmethod
    def parabolla_from_points(start, end, other, name=None):
        path = Path2(name=name)
        path.curve = ParabollaCurve.from_points(start, end, other)
        path.start = start
        path.end = end
        return path

    def to_geom(self, resolution):
        """
        Currently, resolution is interpolated on the x axis. Returns a linestring.
        """
        length = Vector2.distance(self.start, self.end)
        numpoints = length / resolution
        coords = []
        for x in numpy.linspace(self.start[0], self.end[0], numpoints, endpoint=True):
            coords.append((x, self.curve.evaluate_y(x)))
        obj = ddd.line(coords)
        obj.copy_from(self, copy_material=True, copy_children=True)
        return obj


ddd.path = Path2

