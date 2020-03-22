# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging
import math

from shapely import geometry, affinity, ops


# Get instance of logger for this module
logger = logging.getLogger(__name__)

class DDDAlign():

    def grid(self, obj, space=5.0, width=None):

        if width is None:
            width = int(math.sqrt(len(obj.children)))

        result = []
        for idx, c in enumerate(obj.children):
            col = idx % width
            row = int(idx / width)
            pos = [col * space, row * space, 0.0]
            result.append(c.translate(pos))
            col += 1

        obj.children = result

        return obj


