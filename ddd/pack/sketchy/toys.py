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


def ball_soccer(r=0.11):
    item = ddd.sphere(r=r)
    item = item.material(ddd.mats.ball_soccer)
    return item

def ball_basketball(r=0.12):
    item = ddd.sphere(r=r)
    item = item.material(ddd.mats.ball_basketball)
    return item

def ball_beach():
    raise NotImplementedError()

def ball_golf(r=0.043 / 2):
    item = ddd.sphere(r=r)
    item = item.material(ddd.mats.plastic_white)
    item.set('ddd:weight', 0.045)
    return item

def ball_american_football(length=0.28, radius=0.16 / 2):
    ball = ddd.point([0, -length / 2]).arc_quarter_to([radius, 0], True, resolution=2).arc_quarter_to([0, length / 2], True, resolution=2)
    ball = ball.revolve().merge_vertices().flip_faces()
    ball = ball.smooth(ddd.PI_OVER_4)
    ball = ball.material(ddd.mats.rubber_orange)
    return ball

def ball_table_tennis(r=0.02):
    """
    Official balls: 4cm diameter, mass: 2.7g (bounce restoration energy: ~77%)
    """
    item = ddd.sphere(r=r)
    item = item.material(ddd.mats.plastic_white)
    return item


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




