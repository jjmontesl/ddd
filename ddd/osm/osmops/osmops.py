# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging
import math

from shapely import geometry, affinity, ops
from ddd.ddd import ddd


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class OSMBuilderOps():

    def __init__(self, osm):

        self.osm = osm

    def extend_way(self, obj):
        # Should use joins and intersections
        #return ddd.geomops.extend_line(obj, 2, 2)
        pass

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
        Consider other objects (eg. do not place on fountains or trees)
        """

        # options = [{'valid': if distance &...}]

        pass

