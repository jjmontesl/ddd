# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging
import math
import random

from ddd.ddd import ddd


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class DDDRandom:

    def angle(self, factor=1.0):
        """
        Random angle in radians, between 0 and 2pi (or factor * 2pi).
        """
        return random.uniform(0, math.pi * 2.0 * factor)

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
        assert False, "Incorrect weighted choice."


'''
def weighted_choice(options):
    """
    """
    total = sum([o for o in options.values()])
    rand = random.uniform(0, total)
    accum = 0.0
    for k, v in options.items():
        if accum + v >= rand: return k
        accum += v
    assert False, "Incorrect weighted choice."
'''