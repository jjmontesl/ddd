# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging
import random

from ddd.ddd import ddd
from ddd.pack.sketchy.urban import post, lamp_ball


def cloud():
    raise NotImplementedError()

def clouds():
    """
    High-level clouds (5-13 km): cirrocumulus, cirrus, and cirrostratus.
    Mid-level clouds (2-7 km): altocumulus, altostratus, and nimbostratus.
    Low-level clouds (0-2 km): stratus, cumulus, cumulonimbus, and stratocumulus.
    """
    raise NotImplementedError()


def rock():
    raise NotImplementedError()

def rocks():
    raise NotImplementedError()


def river():
    raise NotImplementedError()


def well(terrain, subtract=True):
    raise NotImplementedError()

def cave(terrain):
    raise NotImplementedError()


def lighthouse(height=10, r=1.5):

    mat = random.choice([ddd.mats.metal_paint_green, ddd.mats.metal_paint_red])

    disc = ddd.point([0, 0]).buffer(r, resolution=3, cap_style=ddd.CAP_ROUND)
    obj = disc.extrude_step(disc, height * 0.3)
    obj = obj.extrude_step(disc.scale(0.7), height * 0.5)
    obj = obj.extrude_step(disc.scale(1.0), height * 0.18)
    obj = obj.extrude_step(disc.scale(1.2), height * 0.02)
    obj = obj.material(mat)
    obj = ddd.uv.map_cylindrical(obj)
    obj.name = "Lighthouse"

    lamp = lamp_ball(r=0.2).material(mat)
    lamp = ddd.uv.map_spherical(lamp)

    top = post(top=lamp).translate([0, 0, height])

    rail = disc.scale(1.2).extrude_step(disc.scale(1.2), 1.0, base=False, cap=False).translate([0, 0, height]).material(ddd.mats.railing)
    rail = ddd.uv.map_cylindrical(rail)

    obj = ddd.group([obj, top, rail], name="Lighthouse Small")

    return obj

# TODO: Move to industrial
def crane():
    raise NotImplementedError()


def powertower(height=14.0):
    obj_pole = ddd.rect([-0.5, -0.5, 0.5, 0.5]).extrude(height)
    obj_horz1 = ddd.rect([-2.5, -0.3, 2.5, 0.3]).extrude(0.6).translate([0, 0, height - 2])
    obj_horz2 = ddd.rect([-3, -0.3, 3, 0.3]).extrude(0.6).translate([0, 0, height - 4])
    obj = ddd.group([obj_pole, obj_horz1, obj_horz2])
    return obj


