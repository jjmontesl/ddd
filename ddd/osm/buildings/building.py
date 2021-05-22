# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging
import math
import random
import sys

from ddd.ddd import DDDObject2, DDDObject3
from ddd.ddd import ddd
from ddd.pack.sketchy import plants, urban
from ddd.geo import terrain
from ddd.core.exception import DDDException
from ddd.util.dddrandom import weighted_choice
from collections import namedtuple


# Get instance of logger for this module
logger = logging.getLogger(__name__)


from pint import UnitRegistry
ureg = UnitRegistry()


"""
"""
BuildingContact = namedtuple("BuildingContact", "other self_idx other_idx")

"""
"""
class BuildingSegment:

    __slots__ = ('building', 'seg_idx', 'p1', 'p2',
                 'seg_convex_idx',
                 'closest_way')

    def __init__(self, building, seg_idx, p1, p2):
        self.building = building
        self.seg_idx = seg_idx
        self.p1 = p1
        self.p2 = p2

        self.seg_convex_idx = None

        self.closest_way = None

    def __repr__(self):
        return "%s (convex=%s, closest_way=%s)" % (self.seg_idx, self.seg_convex_idx, self.closest_way)

class Building():  # DDDObject3, DDDDataObject

    def __init__(self, obj):  # extend or wrap?
        self.obj = obj


