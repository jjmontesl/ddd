# ddd - DDD123
# Library for simple scene modelling.
# Jose Juan Montes 2021

from collections import namedtuple
import logging
import math

# Get instance of logger for this module
logger = logging.getLogger(__name__)


class Vector2(tuple):
    """
    """
    #def __init__(self, array):
    #    super().__init__(array)

    @property
    def x(self):
        return self[0]

    @property
    def y(self):
        return self[1]

    #@property
    #def z(self):
    #    return self[2]

    @staticmethod
    def distance(a, b):
        return math.sqrt( ((b[0] - a[0]) ** 2) + ((b[1] - a[1]) ** 2) )

    @staticmethod
    def distance_sqr(a, b):
        return ((b[0] - a[0]) ** 2) + ((b[1] - a[1]) ** 2)

    def length(self):
        return math.sqrt(self[0] ** 2 + self[1] ** 2)

    def normalized(self):
        return self / self.length()

    def __add__(self, other):
        return Vector2(self[0] + other[0], self[1] + other[1])

    def __mul__(self, other):
        return Vector2(self[0] * other, self[1] * other)

    def __truediv__(self, other):
        return Vector2(self[0] / other, self[1] / other)

    def distance_to(self, b):
        return math.sqrt( ((b[0] - self[0]) ** 2) + ((b[1] - self[1]) ** 2) )

