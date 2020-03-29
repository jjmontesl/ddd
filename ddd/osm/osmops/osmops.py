# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging
import math

from shapely import geometry, affinity, ops
from ddd.ddd import ddd


# Get instance of logger for this module
logger = logging.getLogger(__name__)


def extend_way(obj):
    # Should use joins and intersections
    return ddd.geomops.extend_line(obj, 2, 2)



