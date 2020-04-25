# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging
from ddd.ddd import DDDMaterial, DDDObject3, ddd, DDDInstance


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class Light(DDDInstance):
    """
    Base class for light components.
    """

    def material(self, material):
        logger.debug("Assigning material to light (ignoring): %s", self)
        return self


class PointLight(Light):
    """
    """

    def __init__(self, pos=None, name="Light", color="#ffffff", radius=10, intensity=1.05, enabled=True):

        super(PointLight, self).__init__(None, name=name)

        if pos: self.translate(pos)

        self.extra['ddd:light:color'] = color
        self.extra['ddd:light:radius'] = radius
        self.extra['ddd:light:intensity'] = intensity
        self.extra['ddd:light:enabled'] = enabled


class DirectionalLight(Light):
    """
    """
    pass

