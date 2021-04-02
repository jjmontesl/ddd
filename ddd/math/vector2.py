# ddd - DDD123
# Library for simple scene modelling.
# Jose Juan Montes 2021

import logging
import math

# Get instance of logger for this module
logger = logging.getLogger(__name__)


class Vector2(tuple):
    """
    """
    # TODO: Use numpy?

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
        return math.sqrt( ((b[0] - a[0]) ** 2) + ((b[1] - a[1]) ** 2) )

    @staticmethod
    def distance_sqr(a, b):
        return ((b[0] - a[0]) ** 2) + ((b[1] - a[1]) ** 2)

    #def distance_to(a, b):
    #    return sqrt( ((b[0] - a[0]) ** 2) + ((b[1] - a[1]) ** 2) )


