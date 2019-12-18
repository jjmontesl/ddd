'''
'''

'''
'''

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
