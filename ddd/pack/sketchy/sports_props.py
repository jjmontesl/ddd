# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import math

from ddd.ddd import ddd
import logging
from ddd.pack.sketchy import urban
from ddd.pack.sketchy.urban import post, curvedpost


# Get instance of logger for this module
logger = logging.getLogger(__name__)




def golf_club(length=1.2):
    """
    """
    
    flag = ddd.rect([0, 0, flag_width, flag_height])
    flag = flag.material(ddd.mats.red)
    flag = flag.triangulate()  # twosided=True)
    flag = flag.rotate(ddd.ROT_FLOOR_TO_FRONT).twosided()
    flag = ddd.uv.map_cubic(flag)

    flag = flag.translate([0.025, 0, -0.02 - flag_height])

    item_post = post(height=pole_height, r=0.025, top=flag, mat_post=ddd.mats.metal_paint_yellow)

    return item_post


def tennis_racket():
    pass

def paddletennis_racket():
    pass

def tabletennis_bat():
    pass

def baseball_bat():
    pass

