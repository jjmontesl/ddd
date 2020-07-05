# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging
from ddd.ddd import ddd
import math

# Get instance of logger for this module
logger = logging.getLogger(__name__)


class DDDMeshOps():

    def reduce(self, obj):
        result = obj.copy()
        # Currently reducing very simply
        if not result.children:
            try:
                result = result.convex_hull()
            except Exception as e:
                logger.error("Could not calculate convex hull for: %s", result)
        result.children = [self.reduce(c) for c in result.children]
        return result

    def reduce_bounds(self, obj):
        result = obj.copy()
        if not result.children:
            try:
                bounds = result.bounds()
                bounds = list(bounds[0]) + list(bounds[1])
                result.mesh = ddd.box(bounds).mesh
            except Exception as e:
                logger.error("Could not calculate bounding box for: %s", result)
                result.mesh = None
        result.children = [self.reduce_bounds(c) for c in result.children]
        return result

    def reduce_billboard(self, obj):
        raise NotImplementedError()

