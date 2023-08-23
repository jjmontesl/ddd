# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging

from ddd.ddd import ddd
from trimesh import transformations
from ddd.math.vector3 import Vector3
from ddd.ops import grid
from ddd.math.transform import DDDTransform

from ddd.ops.layout import DDDLayout, VerticalDDDLayout


# Get instance of logger for this module
logger = logging.getLogger(__name__)


def paper_airplane_dart():
    '''
    base = ddd.point(name="Tap").buffer(r, resolution=2)
    path = ddd.point().line_to([0, height]).line_to([length, height]).line_to([length, height * 0.5])
    item = base.extrude_along(path)
    item = item.rotate(ddd.ROT_FLOOR_TO_FRONT).rotate(ddd.ROT_TOP_CW)
    item = item.material(ddd.mats.steel)
    item = ddd.uv.map_cubic(item)
    return item
    '''
    raise NotImplementedError()



def frisbee():
    raise NotImplementedError()


def jenga():
    raise NotImplementedError()


def ball_soccer():
    raise NotImplementedError()

def ball_basketball():
    raise NotImplementedError()

def ball_beach():
    raise NotImplementedError()

def ball_golf():
    # Link / refer / deduplicate with 'sports_props.golf_*' module
    raise NotImplementedError()


def cube_symbols_relief(size=0.1, bevel=0.01, bevel_style=ddd.JOIN_BEVEL, symbols=['1', '2', '3', '4', '5', '6'], symbol_height=0.01):
    """
    """
    #common.face_relief...  / triangles relief...
    raise NotImplementedError()

def cube_symbol_engraved():
    raise NotImplementedError()


def dice_d4():
    raise NotImplementedError()

def dice_d6():
    raise NotImplementedError()

def dice_d6_dots():
    raise NotImplementedError()

def dice_d20():
    raise NotImplementedError()


def bowling_pin():
    raise NotImplementedError()

def bowling_ball():
    raise NotImplementedError()




'''
def balloon():
    raise NotImplementedError()

def balloon_pack():
    raise NotImplementedError()
'''


