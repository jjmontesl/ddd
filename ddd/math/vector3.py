# ddd - DDD123
# Library for simple scene modelling.
# Jose Juan Montes 2021

from collections import namedtuple
import logging
import math

# Get instance of logger for this module
logger = logging.getLogger(__name__)


class Vector3(tuple):

    '''
    def __init__(self, array):
        if len(array) == 2:
            super().__init__((array[0], array[1], 0.0))
        else:
            super().__init__(array)
    '''

    @staticmethod
    def array(array):
        return Vector3((array[0], array[1], array[2] if len(array) >= 3 else 0))

    @property
    def x(self):
        return self[0]

    @property
    def y(self):
        return self[1]

    @property
    def z(self):
        return self[2]

    @staticmethod
    def distance(a, b):
        return math.sqrt( ((b[0] - a[0]) ** 2) + ((b[1] - a[1]) ** 2) + ((b[2] - a[2]) ** 2) )

    @staticmethod
    def distance_sqr(a, b):
        return ((b[0] - a[0]) ** 2) + ((b[1] - a[1]) ** 2) + ((b[2] - a[2]) ** 2)

    def length(self):
        return math.sqrt(self[0] ** 2 + self[1] ** 2 + self[2] ** 2)

    def normalized(self):
        l = self.length()
        if l == 0:
            return self
        return self / l

    def __add__(self, other):
        if isinstance(other, (int, float)):
            return Vector3((self[0] + other, self[1] + other, self[2] + other))
        return Vector3((self[0] + other[0], self[1] + other[1], (self[2] if len(self) > 2 else 0) + (other[2] if len(other) > 2 else 0)))

    def __sub__(self, other):
        if isinstance(other, (int, float)):
            return Vector3((self[0] - other, self[1] - other, self[2] - other))
        return Vector3((self[0] - other[0], self[1] - other[1], (self[2] if len(self) > 2 else 0) - (other[2] if len(other) > 2 else 0)))

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return Vector3((self[0] * other, self[1] * other, self[2] * other))
        return Vector3((self[0] * other[0], self[1] * other[1], self[2] * (other[2] if len(other) > 2 else 0)))

    def __truediv__(self, other):
        if isinstance(other, (int, float)):
            return Vector3((self[0] / other, self[1] / other, self[2] / other))
        return Vector3((self[0] / other[0], self[1] / other[1], self[2] / other[2]))

    def distance_to(self, b):
        return math.sqrt( ((b[0] - self[0]) ** 2) + ((b[1] - self[1]) ** 2) + ((b[2] - self[2]) ** 2) )

    def dot(self, other):
        return self[0] * other[0] + self[1] * other[1] + self[2] * other[2]
        #return self[0] * other[0] + self[1] * other[1] + (self[2] * other[2] if len(self) >= len(other) >= 3 else 0)

    def angle(self, other):
        dp = self.normalized().dot(other.normalized())
        a = math.acos(dp)
        return a


Vector3.zero = Vector3((0, 0, 0))
Vector3.one = Vector3((1, 1, 1))

Vector3.right = Vector3((1, 0, 0))
Vector3.forward = Vector3((0, 1, 0))
Vector3.up = Vector3((0, 0, 1))
