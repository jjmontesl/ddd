# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging
from ddd.ddd import ddd
import math

# Get instance of logger for this module
logger = logging.getLogger(__name__)

class DDDGeometry():

    def inscribed_rectangle(self, obj, padding=0.5, search_erode=1.5):
        """
        Generates an inscribed rectangle from the oriented bounding box of the shape,
        searching an downscaled inscribed rectangle from it. Note that
        this is nt guaranteed to be the largest inscribed rectangle possible.
        """

        rect = obj.copy()
        rect.geom = obj.geom.minimum_rotated_rectangle

        iters = 60
        candidate_rect = rect.copy()
        # TODO: do this by bipartition
        for i in range(iters):
            #scale = 1.0 - (1.0 / iters) * i
            candidate_rect = rect.buffer(-search_erode * i)
            if obj.contains(candidate_rect.buffer(padding)):
                break

        return candidate_rect

    def oriented_axis(self, obj):
        """
        Returns (major, minor, rotation)
        """

        rectangle = obj.geom.minimum_rotated_rectangle

        coords = rectangle.exterior.coords[:-1]

        min_point = 0
        for i in range(len(coords)):
            if (coords[i][0] + coords[i][1]) < (coords[min_point][0] + coords[min_point][1]):
                min_point = i
        coords = coords[i:] + coords[:i]

        width_seg = ddd.line([coords[0], coords[1]])
        length_seg = ddd.line([coords[0], coords[-1]])

        width_l = width_seg.geom.length
        length_l = length_seg.geom.length

        if width_l > length_l:
            (width_l, length_l) = (length_l, width_l)
            (width_seg, length_seg) = (length_seg, width_seg)

        vec_dir_major = (length_seg.geom.coords[1][0] - length_seg.geom.coords[0][0], length_seg.geom.coords[1][1] - length_seg.geom.coords[0][1])
        vec_dir_minor = (width_seg.geom.coords[1][0] - width_seg.geom.coords[0][0], width_seg.geom.coords[1][1] - width_seg.geom.coords[0][1])
        midpoint_major = length_seg.centroid().geom.coords[0]
        midpoint_minor = width_seg.centroid().geom.coords[0]
        major_seg = ddd.line([midpoint_minor, [midpoint_minor[0] + vec_dir_major[0], midpoint_minor[1] + vec_dir_major[1]]])
        minor_seg = ddd.line([midpoint_major, [midpoint_major[0] + vec_dir_minor[0], midpoint_major[1] + vec_dir_minor[1]]])

        # Generate lines, rotate and translate to area
        angle = math.atan2(length_seg.geom.coords[1][1] - length_seg.geom.coords[0][1],
                           length_seg.geom.coords[1][0] - length_seg.geom.coords[0][0])

        return (major_seg, minor_seg, angle)  #, length_seg, width_seg)


