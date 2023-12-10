# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging
from ddd.ddd import ddd
from ddd.nodes.instance import DDDInstance
from ddd.nodes.node3 import DDDNode3


# Get instance of logger for this module
logger = logging.getLogger(__name__)


#class Light(DDDInstance):  # formerly lights were instances, but there are issues on export and... they should not be anyway
class Light(DDDNode3):
    """
    Base class for light nodes.
    """

    def material(self, material):
        # Assigning materials to lights is ignored
        logger.debug("Assigning material to light (ignoring): %s", self)
        return self


class PointLight(Light):
    """
    """

    def __init__(self, pos=None, name="Light", color="#ffffff", radius=5, intensity=1.05, enabled=True, shadows=False):
        """
        Shadows can currently be: False, True (hard), 'hard', 'soft', 'none'
        """

        super(PointLight, self).__init__(name=name)

        if pos:
            self.transform.position = pos

        self.extra['ddd:light'] = True
        self.extra['ddd:light:color'] = color
        self.extra['ddd:light:radius'] = radius
        self.extra['ddd:light:intensity'] = intensity
        self.extra['ddd:light:enabled'] = enabled
        if shadows:
            shadows_type = 'hard' if shadows is True else shadows
            self.extra['ddd:light:shadows'] = shadows_type


class DirectionalLight(Light):
    """
    """
    pass

