# ddd - DDD123
# Library for simple scene modelling.
# Jose Juan Montes 2021

import logging
import math

# Get instance of logger for this module
logger = logging.getLogger(__name__)


class Transform(tuple):
    """
    """

    def __init__(self):
        self.matrix = None
        self.inverse = None


