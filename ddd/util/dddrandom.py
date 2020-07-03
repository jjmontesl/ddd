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


def weighted_choice(options):
    """
    TODO: Move to a generic utils module (or ddd.random, and account for seeding and hashing etc).
    """
    total = sum([o for o in options.values()])
    rand = random.uniform(0, total)
    accum = 0.0
    for k, v in options.items():
        if accum + v >= rand: return k
        accum += v
    assert False, "Incorrect weighted choice."
