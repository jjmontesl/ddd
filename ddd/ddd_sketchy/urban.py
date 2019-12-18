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


def post(height=2.80, r=0.05, posttop_callback=None):
    pass

def lamppost_lamp(height=0.45, base_r=0.15, top_r=0.30, sides=4):
    pass

def lamppost_with_top_lamp(height=3.60):
    # Create lampa
    lamp = lamppost_lamp()
    
    # Create post
    
    return lamp

def lamppost_arm(length, lamp_pos='over'):
    pass

def lamppost_with_arms(height, arms=2, degrees=360):
    pass

def curvedpost(height, arm_length, items_feedback=None):
    pass

def traffic_lights():
    post = curvedpost()
    return post

def trafficsign_sign():
    pass

def trafficsign_sign_triangle():
    pass

def trafficsign_sign_rect():
    pass

def trafficsign_sign_circle():
    pass

def trafficsign_sign_octagon():
    pass
    
def signpost():
    pass
    
def trafficsign_post():
    post = signpost()
    
    
def busstop_small():
    pass

def busstop_covered():
    pass
    
def mailbox():
    pass

    
def statue():
    pass

def fountain(d=1.5):
    
    # Base
    base = ddd.disc(r=d, resolution=1).extrude(0.30)
    
    fountain = ddd.sphere(r=d, subdivisions=1).subtract(ddd.cube(d=d * 1.2)).subtract(ddd.sphere(r=d - 0.2, subdivisions=1))
    fountain = fountain.translate([0, 0, 1.1])  # TODO: align
    #.subtract(base) 
    
    # Fountain
    item = ddd.group([base, fountain])
    return item
    
    
def hedge():
    pass
    
def pot():
    pass

def pot_tree():
    pass

def pot_flower():
    pass
    
def gardener():
    pass
    
    
def bench(length=1.40, height=1.00, seat_height=0.40, 
          legs=2, hangout=0.20):
    pass

def bank(length=1.40, height=1.00, seat_height=0.40, 
          legs=2, hangout=0.20, angle=100.0, arms=0):
    #bench =
    pass

