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
from ddd.ddd import ddd
import noise



def cart_wheel(r=0.075, thick=0.03):
    """
    """
    sides = 10
    item = ddd.regularpolygon(sides, r, name="Cart Wheel").rotate(math.pi / sides)
    item = item.extrude(thick).material(ddd.mats.plastic_black)
    item = ddd.uv.map_cylindrical(item)
    item = item.rotate(ddd.ROT_FLOOR_TO_FRONT).translate([0, thick / 2, 0])
    return item


def cart_wheel_axis(height_to_axis=0.1, wheel_radius=0.075, width=0.06, thick_interior=0.032):
    """
    """
    #wheel_radius = height_to_axis * 0.75
    #height_to_axis = wheel_radius * 1.25 # 0.10

    item = ddd.point().line_to([0, -height_to_axis]).line_to([width, -height_to_axis - wheel_radius * 0.5]).line_to([width, 0])
    item = ddd.polygon(item.geom.coords)

    item = item.translate([-width * 0.5, 0]).triangulate().twosided()
    item = item.rotate(ddd.ROT_FLOOR_TO_FRONT).rotate(ddd.ROT_TOP_CW)

    side1 = item.copy().translate([-thick_interior, 0, 0])
    side2 = item.copy().translate([thick_interior, 0, 0])

    item = side1.append(side2)
    item = item.combine()
    item = item.material(ddd.mats.steel)
    item = ddd.uv.map_cubic(item)

    item.set('ddd:connector:axis', [0, 0, -height_to_axis])

    return item


def cart_wheel_and_axis():
    axis = cart_wheel_axis()
    wheel = cart_wheel().rotate(ddd.ROT_TOP_CW)
    wheel = wheel.translate(axis.extra['ddd:connector:axis'])
    axis.append(wheel)
    return axis


def rim(r=0.20):
    pass

def tyre(r=0.25, r_rim_ratio=0.8, width=0.25):
    pass

def wheel(r=0.25, r_rim_ratio=0.8, width=0.25):
    pass

def car():
    pass

def bus():
    pass

def bus_regular():
    pass

def bus_charter():
    pass

def van():
    pass

def ambulance():
    pass

def police_car():
    pass

def truck_head():
    pass


def propeller(tips=2):
    pass

def plane_airframe():
    pass

def plane1():
    pass

def plane2():
    pass

def helicopter1():
    pass


def train_head_electric():
    pass

def train_head_steam():
    pass

def train_wagon_tourist():
    pass

def train_wagon_container():
    pass

def train_wagon_pickup():
    pass

def train_wagon_vehicles():
    pass

def train(pieces):
    pass


def ship():
    pass

