# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020-2023

import logging
import math
import random

from ddd.core.exception import DDDException
from ddd.ddd import ddd

# Get instance of logger for this module
logger = logging.getLogger(__name__)


class DDDRandom:
    """
    Class to generate random values.

    Can be accessed as 'ddd.random'.
    """

    def angle(self, factor=1.0):
        """
        Random angle in radians, between 0 and 2pi (scaled by factor).
        """
        return random.uniform(0, ddd.TWO_PI * factor)
    
    def uniform(self, a, b):
        """
        Random float between a and b.
        """
        return random.uniform(a, b)

    def weighted_choice(self, options):
        """
        Return a random choice between a dictionary of weighted entries.
        """
        total = sum([o for o in options.values()])
        rand = random.uniform(0, total)
        accum = 0.0
        for k, v in options.items():
            if accum + v >= rand: return k
            accum += v

        raise DDDException(False, "Incorrect weighted choice.")
