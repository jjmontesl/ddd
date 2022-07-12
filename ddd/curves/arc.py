# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging

from ddd.core.exception import DDDException
from ddd.curves.path import DDDCurve
from ddd.math.vector2 import Vector2
from trimesh.path.arc import arc_center
from trimesh import util


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class DDDArcCurve(DDDCurve):
    """
    """

    def __init__(self):
        self.center = None
        self.radius = None
        self.normal = None
        self.angle = None

    @staticmethod
    def from_points(points):
        curve = DDDArcCurve()
        center_info = arc_center(points)

        curve.center = center_info['center']
        curve.radius = center_info['radius']
        curve.normal = center_info['normal']
        curve.angle = center_info['span']

        return curve

    def evaluate(self, t):

        V1 = util.unitize(points[0] - center)
        V2 = util.unitize(np.cross(-N, V1))
        t = np.linspace(0, angle, count)

        discrete = np.tile(center, (count, 1))
        discrete += R * np.cos(t).reshape((-1, 1)) * V1
        discrete += R * np.sin(t).reshape((-1, 1)) * V2

        # do an in-process check to make sure result endpoints
        # match the endpoints of the source arc
        if not close:
            arc_dist = util.row_norm(points[[0, -1]] - discrete[[0, -1]])
            arc_ok = (arc_dist < tol.merge).all()
            if not arc_ok:
                log.warning(
                    'failed to discretize arc (endpoint_distance=%s R=%s)',
                    str(arc_dist), R)
                log.warning('Failed arc points: %s', str(points))
                raise ValueError('Arc endpoints diverging!')
        discrete = discrete[:, :(3 - is_2D)]

        return discrete

