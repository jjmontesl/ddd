# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging
import math

import numpy as np
from ddd.ddd import ddd


# Get instance of logger for this module
logger = logging.getLogger(__name__)

class DDDAlign():

    def grid(self, obj, space=5.0, width=None):
        """
        Distribute children in a grid.
        """

        if width is None:
            width = int(math.ceil(math.sqrt(len(obj.children))))

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
                if isinstance(newc, ddd.DDDObject3):
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

        TODO: Should be using polar, and copies made by clone_* methods.
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

    def anchor(self, obj, anchor):
        """
        TODO: Rename to 'reanchor'

        Recenters an object around a given anchor.
        Anchor is a normalized vector relative to the object's bounding box.
        """
        (xmin, ymin, _), (xmax, ymax, _) = obj.bounds()
        center = (xmin + (xmax - xmin) * anchor[0], ymin + (ymax - ymin) * anchor[1])
        result = obj.translate([-center[0], -center[1], 0])
        return result


    def along(self, obj, reference, endpoint=True):
        """
        Distributes children along a linear geometry reference.

        This method modifies the object chilren in place, returning the same object.
        """
        length = reference.length()
        numitems = len(obj.children)
        idx = 0
        for distance in np.linspace(0.0, length, numitems, endpoint=endpoint):
            (coords_p, segment_idx, segment_coords_a, segment_coords_b) = reference.interpolate_segment(distance)
            child = obj.children[idx]
            child.replace(child.translate(coords_p))
            idx += 1

        return obj

    def clone_on_coords(self, source, target):
        """
        Clone source over target.

        Source can be any DDDObject (2D, 3D or instances).

        If target is a geometry, uses its coordinates.
        """

        result = source.grouptyped(name="Group: %s" % source.name)
        #result.mesh = None
        #result.children = []

        # Note: it's called vertex_iterator for 3D objects
        for c in set(target.coords_iterator()):
            obj = source.copy()
            obj = obj.translate(c)
            result.append(obj)

        return result

