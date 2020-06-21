# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging

from ddd.ddd import ddd
import math
from shapely.geometry.polygon import LinearRing
import random


# Get instance of logger for this module
logger = logging.getLogger(__name__)


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