# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging
import math
import random
from ddd.core.exception import DDDException


# Get instance of logger for this module
logger = logging.getLogger(__name__)


def parse_bool(value):

    if value in (True, "True", "true", "Yes", "yes", "1", 1):
        return True
    if value in (False, "False", "false", "No", "no", "0", 0):
        return False
    raise DDDException("Could not parse boolean value: %r", value)
