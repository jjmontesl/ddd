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
import sys
import numpy as np

from ddd.ddd import DDDNode2, DDDNode3
from ddd.ddd import ddd
from ddd.pack.sketchy import plants, urban
from ddd.geo import terrain
from ddd.core.exception import DDDException
from ddd.pack.sketchy.buildings import window_with_border, door
from ddd.util import common


# Get instance of logger for this module
logger = logging.getLogger(__name__)


from pint import UnitRegistry
ureg = UnitRegistry()


def parse_material(name, color):
    """
    Note: materials mapping shall rather be done by pipeline rules.

    Alternatively or in addition, a customizable materials mapping table shall be used by this method,
    instead of hard coding materials and names.

    TODO: Also search materials by name and ignoring dash/spaces/case.
    """
    material = None
    if hasattr(ddd.mats, name):
        material = getattr(ddd.mats, name)
    else:
        material = ddd.material(name, color)
    return material

