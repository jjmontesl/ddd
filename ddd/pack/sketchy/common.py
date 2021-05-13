# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging
import math
import random

from ddd.ddd import ddd
import numpy as np


# Get instance of logger for this module
logger = logging.getLogger(__name__)

def bar_u(height, b, thick=0.20):
    """
    A u-shaped figure, like that used for handles, bycicle stands...
    """
    a = np.array(a)
    b = np.array(b)

    #path = ddd.line([a, b])
    #path_section = ddd.point(name="Cable").buffer(thick * 0.5, resolution=1, cap_style=ddd.CAP_ROUND)
    #cable = path_section.extrude_path(path)

    length = np.linalg.norm(b - a)
    cable = ddd.point(name="Cable").buffer(thick * 0.5, resolution=1, cap_style=ddd.CAP_ROUND).extrude(length + thick).translate([0, 0, -thick * 0.5])
    cable = ddd.uv.map_cylindrical(cable)

    vector_up = [0, 0, 1]
    vector_dir = (b - a) / length
    rot_axis = np.cross(vector_up, vector_dir)
    rot_angle = math.asin(np.linalg.norm(rot_axis))
    if rot_angle > 0.00001:
        rotation = transformations.quaternion_about_axis(rot_angle, rot_axis / np.linalg.norm(rot_axis))
        cable = cable.rotate_quaternion(rotation)
    cable = cable.translate(a)

    return cable
