# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging
import math

from shapely import geometry, affinity, ops
from ddd.ddd import ddd, DDDObject3
import numpy as np


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

    def polar(self, obj, d, offset=0, rotate=False):
        """
        Distribute children around center with distance d.
        """
        for idx, c in enumerate(obj.children):
            angle = offset + (2 * math.pi) / len(obj.children) * idx
            posx, posy = math.cos(angle) * d, math.sin(angle) * d
            newc = c.copy()
            if rotate:
                if isinstance(newc, DDDObject3):
                    newc = newc.rotate([0, 0, angle + (math.pi / 2)])
                else:
                    newc = newc.rotate(angle)
            newc = newc.translate([posx, posy, 0])
            newc.extra['ddd:angle'] = angle - (math.pi / 2)
            c.replace(newc)
        return obj

    def matrix_polar(self, obj, count=None, angle_interval=None, span=math.pi * 2):
        """
        Clones the object and positions it radially.

        TODO: Should be using polar, and copies made by matrix methods.
        """

        result = ddd.group3(name="Matrix of: %s" % obj.name)

        if count is None:
            count = span / angle_interval

        idx = 0
        for angle in np.linspace(0, span, count, endpoint=False):
            oc = obj.copy().rotate([0, 0, angle])
            oc.name = oc.name + (" (%d)" % idx)
            result.append(oc)
            idx += 1

        return result

