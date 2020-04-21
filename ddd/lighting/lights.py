# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging
from ddd.ddd import DDDMaterial, DDDObject3, ddd


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class Light(DDDObject3):
    """
    Base class for light components.
    """

    def __init__(self):
        self.color = '#ffffff'  # ddd.color('#ffffff')
        self.radius = 10.0
        self.intensity = 1.0


class PointLight(Light):
    """
    """
    pass


class DirectionalLight(Light):
    """
    """
    pass

