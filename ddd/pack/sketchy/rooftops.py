# DDD(123) - Library for procedural generation of 2D and 3D geometries and scenes
# Copyright (C) 2021 Jose Juan Montes
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import logging
import math
import random
import numpy as np

from ddd.ddd import ddd
from ddd.core.exception import DDDException


# Get instance of logger for this module
logger = logging.getLogger(__name__)


"""
Rooftop-specific items (chimneys, antennas, ventilation, A/C, skylights)
"""

def chimney_round_turbine(obj, height=1.0, radius=0.1):
    """
    Creates a modern chimeney, thin, tall, typically metallic and with a rotatin fan/turbine on top.
    """
    pass

def chimney_open_shape(obj, height=1.0, radius=0.1):
    """
    Creates a round chimeney, thin, tall, typically metallic.

    Uses the given shape, this is used by chimney round and chimney rect.
    """
    pass

def chimney_open_round():
    pass

def chimney_open_rect():
    pass

def chimney_capped_rect():
    pass

def chimney_capped_round():
    pass



def roof_antenna_tv():
    pass

def roof_antena_satellite_dish():
    pass

def roof_antenna_cell():
    pass

def roof_antenna_radio_station():
    pass

def roof_antenna_radio_amateur():
    pass


def large_ac_unit():
    pass


def roof_skylight():
    pass

