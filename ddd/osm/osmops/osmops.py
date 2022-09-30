# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging
import math

from shapely import geometry, affinity, ops
from ddd.ddd import ddd
import sys


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class OSMBuilderOps():

    def __init__(self, osm):
        self.osm = osm

    def position_along_way(self, obj, way_1d, penetrate=-0.5, offset=0):
        """
        Positions an item in a way, according to item and way direction,
        and according to way width.
        """

        logger.info("Positioning %s along way %s", obj, way_1d)

        closest_seg = way_1d.closest_segment(obj)
        (coords_p, segment_idx, segment_coords_a, segment_coords_b, closest_object, closest_object_d) = closest_seg
        #dist = ddd.point(coords_p).distance(ddd.point(intersection_shape.geom.centroid.coords))

        dir_vec = (segment_coords_b[0] - segment_coords_a[0], segment_coords_b[1] - segment_coords_a[1])
        dir_vec_length = math.sqrt(dir_vec[0] ** 2 + dir_vec[1] ** 2)
        dir_vec = (dir_vec[0] / dir_vec_length, dir_vec[1] / dir_vec_length)

        direction_mult = -1 if obj.extra.get('osm:direction', 'forward') != 'forward' else 1
        if offset:
            coords_p  = [coords_p[0] + dir_vec[0] * offset * direction_mult, coords_p[1] + dir_vec[1] * offset * direction_mult]

        perpendicular_vec = (-dir_vec[1], dir_vec[0])

        item_dist = way_1d.extra['ddd:way:width'] * 0.5 - penetrate
        right = (coords_p[0] - perpendicular_vec[0] * item_dist, coords_p[1] - perpendicular_vec[1] * item_dist)
        left = (coords_p[0] + perpendicular_vec[0] * item_dist, coords_p[1] + perpendicular_vec[1] * item_dist)

        angle = math.atan2(dir_vec[1], dir_vec[0])
        obj.geom.coords = right if obj.extra.get('osm:direction', 'forward') == 'forward' else left
        obj.extra['ddd:angle'] = (angle) if obj.extra.get('osm:direction', 'forward') == 'forward' else (angle + math.pi)
        #print (obj.extra)

        return obj


    def placement_valid(self, obj, valid=None, invalid=None):

        currently_valid = None

        if valid:
            if valid.intersects(obj):
                currently_valid = True
            else:
                currently_valid = False
        else:
            currently_valid = True

        if invalid and currently_valid:
            if invalid.intersects(obj):
                currently_valid = False

        #print(obj)
        #print("Valid: %s" % currently_valid)
        #if obj.name and 'Luis' in obj.name:
        #    ddd.group3([obj.material(ddd.mats.highlight), invalid]).show()

        return currently_valid

    def placement_smart(self, obj, options):
        """
        Consider other objects (eg. do not place on fountains or trees).
        """
        # options = [{'valid': if distance &...}]

        pass

