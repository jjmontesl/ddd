# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import math

from ddd.ddd import ddd
from ddd.ops import filters
import logging
from ddd.text import fonts
from ddd.lighting.lights import PointLight
import sys
import re
import random
from trimesh import transformations
import numpy as np
from ddd.ops.extrusion import extrude_step_multi, extrude_dome


# Get instance of logger for this module
logger = logging.getLogger(__name__)


def tap_push(r=0.01, height=0.1, length=0.15):
    base = ddd.point(name="Tap").buffer(r, resolution=2)
    path = ddd.point().line_to([0, height]).line_to([length, height]).line_to([length, height * 0.5])
    item = base.extrude_along(path)
    item = item.rotate(ddd.ROT_FLOOR_TO_FRONT).rotate(ddd.ROT_TOP_CW)
    item = item.material(ddd.mats.steel)
    item = ddd.uv.map_cubic(item)
    return item

def tap():
    return tap_push()
