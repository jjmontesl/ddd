# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020-2023

import logging
import math
import random

from ddd.core.exception import DDDException
from ddd.ddd import ddd

# Get instance of logger for this module
logger = logging.getLogger(__name__)


class DDDExpressions:
    """
    """

    def __init__(self):
        """
        """
        self.functions = {}

    def register_func(self, func_name, func):
        """
        """
        self.functions[func_name] = func

    