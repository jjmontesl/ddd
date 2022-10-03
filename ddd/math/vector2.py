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

    @staticmethod
    def array(array):
        return Vector2((array[0], array[1]))

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
        if isinstance(other, (int, float)):
            return Vector2((self[0] + other, self[1] + other))
        return Vector2((self[0] + other[0], self[1] + other[1]))

    def __sub__(self, other):
        if isinstance(other, (int, float)):
            return Vector2((self[0] - other, self[1] - other))
        return Vector2((self[0] - other[0], self[1] - other[1]))

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return Vector2((self[0] * other, self[1] * other))
        else:
            raise ValueError()
        #return Vector2((self[0] * other, self[1] * other))

    def __truediv__(self, other):
        if isinstance(other, (int, float)):
            return Vector2((self[0] / other, self[1] / other))
        else:
            raise ValueError()

    def scale(self, other):
        return Vector2((self[0] * other[0], self[1] * other[1]))

    def abs(self):
        return Vector2((abs(self[0]), abs(self[1])))

    def distance_to(self, b):
        return math.sqrt( ((b[0] - self[0]) ** 2) + ((b[1] - self[1]) ** 2) )

    def rotate(self, angle):
        """Angle is in radians."""
        c = math.cos(angle)
        s = math.sin(angle)
        return Vector2((self[0] * c - self[1] * s, self[0] * s + self[1] * c))

    def angle(self):
        return math.atan2(self[1], self[0])


Vector2.zero = Vector2((0, 0))
Vector2.one = Vector2((1, 1))
Vector2.right = Vector2((1, 0))
Vector2.up = Vector2((0, 1))

