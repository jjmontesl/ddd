# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

from shapely import geometry
from trimesh.path import segments
from trimesh.scene.scene import Scene, append_scenes
from trimesh.base import Trimesh
from trimesh.path.path import Path
from trimesh.visual.material import SimpleMaterial
from trimesh import creation, primitives, boolean
import trimesh
from csg.core import CSG
from csg import geom as csggeom
import random
from ddd import ddd
import noise

from ddd.ddd import ddd
from ddd.pack.sketchy import filters
import logging
from ddd.text import fonts


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


def lighthouse(height=8.5, r=1.5):
    obj = ddd.point([0, 0]).buffer(r, resolution=4, cap_style=ddd.CAP_ROUND).extrude(height)
    obj.name = "Lighthouse"
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


