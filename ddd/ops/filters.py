'''
'''
import math

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


#def log(height=3.60, r=0.05):
#    pass


def wobbly():
    pass


def noise_random(obj, scale=1.0):
    func = lambda x, y, z, i: [x + random.uniform(-1.0, 1.0) * scale, 
                               y + random.uniform(-1.0, 1.0) * scale, 
                               z + random.uniform(-1.0, 1.0) * scale]
    obj = obj.vertex_func(func)
    return obj


