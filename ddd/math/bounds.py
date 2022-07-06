# ddd - DDD123
# Library for simple scene modelling.
# Jose Juan Montes 2021

from collections import namedtuple
import logging
import math

from ddd.ddd import D1D2D3
from ddd.math.vector3 import Vector3

# Get instance of logger for this module
logger = logging.getLogger(__name__)


class DDDBounds(tuple):

    #def __init__(self, array):
    #    super().__init__(array)

    @property
    def cmin(self):
        return self[0]

    @property
    def cmax(self):
        return self[1]

    def diagonal(self):
        return D1D2D3.line([self[0], self[1]])

    def center(self):
        return Vector3((self[0] + self[1]) * 0.5)