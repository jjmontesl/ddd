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

def road_way(path):
    """
    This shall serve for asphalt but also dirt roads, country walks, etc.
    """
    pass

def road_lines():
    pass

def road_crosswalk():
    pass

def road_lined():
    # Lined islands (with perimeter lines)
    pass

def road_sidewalk():
    # How to conjugate this with squareas and buildings
    # This can also be used for islands
    pass

def road_rail():
    pass

def road(path):
    pass

def bridge(path):
    pass
