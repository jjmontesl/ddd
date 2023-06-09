# ddd - DDD123
# Library for simple scene modelling.
# Jose Juan Montes 2021

import logging

#from ddd.nodes.node2 import DDDNode2
from ddd.math.vector3 import Vector3

# Get instance of logger for this module
logger = logging.getLogger(__name__)


class DDDBounds(tuple):
    """
    Stores bounds in a two element tuple (min, max).
    """

    #def __init__(self, array):
    #    super().__init__(array)

    @property
    def cmin(self) -> Vector3:
        return self[0]

    @property
    def cmax(self) -> Vector3:
        return self[1]

    def diagonal(self):  # -> DDDNode2:
        """
        Returns a DDD line representing the diagonal of this bounds.
        """
        from ddd.ddd import ddd
        return ddd.line([self[0], self[1]])

    def center(self) -> Vector3:
        """
        Returns a Vector3 representing the center of this bounds.
        """
        return Vector3((self[0] + self[1]) * 0.5)
