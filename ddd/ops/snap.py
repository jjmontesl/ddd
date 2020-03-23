# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging

from ddd.ddd import ddd
import math
from shapely.geometry.polygon import LinearRing


# Get instance of logger for this module
logger = logging.getLogger(__name__)

class DDDSnap():

    def project(self, point, obj, penetrate=0.0):

        obj = obj.individualize().linearize()
        coords_p, segment_idx, segment_coords_a, segment_coords_b, closest_obj = obj.closest_segment(point)

        dirvec_d = [coords_p[0] - point.geom.coords[0][0], coords_p[1] - point.geom.coords[0][1]]
        dirvec_l = math.sqrt(dirvec_d[0] ** 2 + dirvec_d[1] ** 2)
        dirvec = [dirvec_d[0] / dirvec_l, dirvec_d[1] / dirvec_l]

        if penetrate:
            # Find side (TODO: for linear -not rings- there is no winding direction)
            pol = LinearRing([segment_coords_a[:2], segment_coords_b[:2], (point.geom.coords[0][0], point.geom.coords[0][1], 0)])
            if pol.is_ccw == closest_obj.geom.is_ccw: penetrate = penetrate * -1
            coords_p = [coords_p[0] + dirvec[0] * penetrate, coords_p[1] + dirvec[1] * penetrate]

        result = point.copy()
        result.geom.coords = coords_p
        result.extra['ddd:angle'] = math.atan2(dirvec[1], dirvec[0])

        return result

