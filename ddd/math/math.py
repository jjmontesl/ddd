# ddd - DDD123
# Library for simple scene modelling.
# Jose Juan Montes 2021

import logging
import math

# Get instance of logger for this module
logger = logging.getLogger(__name__)

class DDDMath():
    """
    """

    @staticmethod
    def clamp(v, vmin, vmax):
        return min(max(v, vmin), vmax)

    @staticmethod
    def smoothstep(edge0, edge1, x):
        x = DDDMath.clamp((x - edge0) / (edge1 - edge0), 0.0, 1.0)
        return x * x * (3.0 - 2.0 * x)

    @staticmethod
    def smoothstep_pulse(x, edgei0, edgei1, edgeo0, edgeo1):
        if x < edgeo0:
            return DDDMath.smoothstep(edgei0, edgei1, x)
        else:
            return 1.0 - DDDMath.smoothstep(edgeo0, edgeo1, x)

    @staticmethod
    def sign(v):
        return math.copysign(1, v)
