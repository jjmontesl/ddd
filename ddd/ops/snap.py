# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging

from ddd.ddd import ddd
import math
from shapely.geometry.polygon import LinearRing
from shapely.geometry.point import Point
from ddd.core.exception import DDDException


# Get instance of logger for this module
logger = logging.getLogger(__name__)

class DDDSnap():

    def __init__(self):
        self._last_obj = None
        self._last_linearized = None

    def project(self, point, obj, penetrate=0.0):
        """
        Projects a point to another object outline, also calculating the normal angle for alignment.

        Angle is stored in ddd:angle:calculated, and also in ddd:angle if it wasn't set previously.

        See examples/snap.py for several examples of usage.
        """

        # Cache last object
        if obj != self._last_obj:
            self._last_obj = obj
            obj = obj.individualize().linearize()
            self._last_linearized = obj
        else:
            obj = self._last_linearized

        result = point.copy()

        try:
            coords_p, segment_idx, segment_coords_a, segment_coords_b, closest_obj, closest_d = obj.closest_segment(point)
        except DDDException as e:
            logger.warn("Could not snap project point %s onto %s", point, obj)
            return result


        dirvec_d = [coords_p[0] - point.geom.coords[0][0], coords_p[1] - point.geom.coords[0][1]]
        dirvec_l = math.sqrt(dirvec_d[0] ** 2 + dirvec_d[1] ** 2)
        if dirvec_l > 0:
            dirvec = [dirvec_d[0] / dirvec_l, dirvec_d[1] / dirvec_l]
        else:
            logger.warn("Could not calculate closest segment director vector for align project point %s onto %s", point, obj)
            dirvec = [0, 0]

        # Find side (TODO: for linear -not rings- there is no winding direction)
        exterior = 1
        pol = LinearRing([segment_coords_a[:2], segment_coords_b[:2], (point.geom.coords[0][0], point.geom.coords[0][1], 0)])
        if closest_obj.geom.type != "LineString":
            if pol.is_ccw == closest_obj.geom.is_ccw:
                exterior = -1

        if penetrate:
            coords_p = [coords_p[0] + dirvec[0] * penetrate * exterior, coords_p[1] + dirvec[1] * penetrate * exterior]

        result.geom = Point(coords_p)
        result.extra['ddd:angle:calculated'] = math.atan2(dirvec[1], dirvec[0]) + (math.pi if exterior < 0 else 0)
        result.extra['ddd:angle'] = result.extra['ddd:angle'] if result.extra.get('ddd:angle', None) is not None else result.extra['ddd:angle:calculated']

        return result


    # for snap3, check https://github.com/mikedh/trimesh/blob/master/trimesh/proximity.py
