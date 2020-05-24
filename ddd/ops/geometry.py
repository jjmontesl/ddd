# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging

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
