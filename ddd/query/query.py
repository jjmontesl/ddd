# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging
from ddd.ddd import DDDMaterial, DDDObject3, ddd


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class Query():
    """
    Represents a scenegraph query.

    NOTE: See selectors/selection, as it overlaps with the intent of this class. Description of that class is better as of today.
    """

    def __init__(self):
        pass

    def query(self, *args, **kwargs):
        """
        """
        pass
