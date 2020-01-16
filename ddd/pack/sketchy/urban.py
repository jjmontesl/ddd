# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import math
import random

from csg import geom as csggeom
from csg.core import CSG
import noise
from shapely import geometry
from trimesh import creation, primitives, boolean
import trimesh
from trimesh.base import Trimesh
from trimesh.path import segments
from trimesh.path.path import Path
from trimesh.scene.scene import Scene, append_scenes
from trimesh.visual.material import SimpleMaterial

from ddd.ddd import ddd
from ddd.pack.sketchy import filters


mat_paint_green = ddd.material('#265e13')
mat_trafficlight_green = ddd.material('#00ff00')
mat_trafficlight_orange = ddd.material('#ffff00')
mat_trafficlight_red = ddd.material('#ff0000')


def post(height=2.00, r=0.075, top=None):
    """
    A round (or squared) post.
    """
    col = ddd.point([0, 0]).buffer(r, resolution=1, cap_style=ddd.CAP_ROUND).extrude(height)
    if top:
        top = top.translate([0, 0, height])
        col = ddd.group([col, top])
    return col

def curvedpost(height=4.2, arm_length=4.5, r=0.1, corner_radius=0.75, arm_items=None, arm_side='left'):
    """
    A curved post, sitting on the center of its vertical post, with an arm extending to
    the defined side. Items are stacked centered on the arm front side.
    """
    side = -1 if arm_side == "left" else 1
    line = ddd.point([0, 0]).line_to([0, height - corner_radius])
    line = line.line_to([side * corner_radius, height])
    line = line.line_to([side * arm_length, height])
    post = line.buffer(r, cap_style=ddd.CAP_FLAT).extrude(r * 2, center=True)
    post = post.rotate([math.pi / 2.0, 0, 0]).material(mat_paint_green)

    items = []
    for idx, item in enumerate(arm_items):
        positem = item.translate([side * (arm_length - (idx + 1) * 0.4), -r, height])
        items.append(positem)

    post = ddd.group([post] + items)
    return post

def lamppost(height=2.80):
    lamp = ddd.sphere(r=0.25, subdivisions=1)
    col = post(height=height, top=lamp)
    #ped = pedestal(top=col)
    return col

def lamppost_arm(length, lamp_pos='over'):
    pass

def lamppost_with_arms(height, arms=2, degrees=360):
    pass

def trafficlights_head(height=0.8, depth=0.3):

    head = ddd.rect([-0.15, 0, 0.15, height]).material(mat_paint_green).extrude(depth)
    disc_green = ddd.disc(ddd.point([0, 0.2]), r=0.09).material(mat_trafficlight_green).extrude(0.05)
    disc_orange = ddd.disc(ddd.point([0, 0.4]), r=0.09).material(mat_trafficlight_orange).extrude(0.05)
    disc_red = ddd.disc(ddd.point([0, 0.6]), r=0.09).material(mat_trafficlight_red).extrude(0.05)

    discs = ddd.group([disc_green, disc_orange, disc_red]).translate([0, 0, depth])  # Put discs over head
    head = ddd.group([head, discs]).translate([0, -height / 2.0, 0])  # Center vertically
    head = head.rotate([math.pi / 2.0, 0, 0])
    return head

def trafficlights():
    head = trafficlights_head()
    post = curvedpost(arm_items=[head])
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


def sign_pharmacy(size=1.0, depth=0.3):
    '''
    A pharmacy sign (cross). Sits centered on its back (vertical plane).
    '''
    l1 = ddd.line([[-size / 2, 0], [size / 2, 0]]).buffer(size / 3.0, cap_style=3)
    l2 = ddd.line([[0, -size / 2], [0, size / 2]]).buffer(size / 3.0, cap_style=3)
    sign = l1.union(l2)
    sign = sign.extrude(depth)
    sign = sign.rotate([math.pi / 2.0, 0, 0])
    sign = sign.material(ddd.material('#00ff00'))
    sign.name = "Pharmacy Sign"
    return sign

def sign_pharmacy_side(size=1.0, depth=0.3, arm_length=1.0):
    '''
    A pharmacy sign, attached sideways to a post arm. The post attaches centered
    (on the vertical plane).
    '''
    arm_thick = depth / 2
    sign = sign_pharmacy(size, depth)
    arm = ddd.rect([-arm_thick / 2, -arm_thick / 2, arm_thick / 2, arm_thick / 2]).extrude(arm_length)
    arm = arm.rotate([math.pi / 2.0, 0, 0])
    arm = arm.material(ddd.material('#888888'))
    sign = sign.rotate([0, 0, -math.pi / 2.0]).translate([depth / 2, 0, 0])
    sign = sign.translate([0, -(arm_length + size * 0.66), 0])
    return ddd.group([sign, arm], name="Pharmacy Side Sign with Arm")

def panel(height=1.0, width=2.0, depth=0.2):
    '''
    A panel, like what commerces have either sideways or sitting on the facade. Also
    road panels.
    '''
    panel = ddd.rect([-width / 2.0, -height / 2.0, width / 2.0, height / 2.0]).extrude(depth)
    panel = panel.rotate([math.pi / 2.0, 0, 0])
    panel = panel.material(ddd.material('#f0f0ff'))
    panel.name = "Panel"
    return panel

def panel_texture(height=1.0, width=2.0, depth=0.3):
    '''
    A panel, like what commerces have either sideways or sitting on the facade. Also
    road panels.
    '''
    pass

def panel_texture_text(text, height=1.0, width=2.0, depth=0.3):
    pass





def busstop_small():
    pass

def busstop_covered():
    pass

def mailbox():
    pass


def statue():
    pass

def sculpture(d=1.0, height=4.0):
    """
    An urban sculpture, sitting centered on the XY plane.
    """
    pedestal = ddd.cube(d=d / 2.0)

    item = ddd.sphere(r=1, subdivisions=2)
    item = item.scale([d, d, height / 2])
    item = filters.noise_random(item, scale=0.50)
    item = item.translate([0, 0, height / 2 + d])

    item = ddd.group([pedestal, item], name="Urban sculpture")

    return item

def fountain(r=1.5):

    # Base
    base = ddd.disc(r=r, resolution=2).extrude(0.30)

    fountain = ddd.sphere(r=r, subdivisions=1).subtract(ddd.cube(d=r * 1.2)).subtract(ddd.sphere(r=r - 0.2, subdivisions=1))
    fountain = fountain.translate([0, 0, 1.2])  # TODO: align
    #.subtract(base)

    water = ddd.disc(r=r-0.2, resolution=2).triangulate().translate([0, 0, 1.1])

    # Fountain
    item = ddd.group([base, fountain, water])
    return item

def religion_cross(width=1, height=1.5):
    """
    Religion cross.
    """
    l1 = ddd.line([[-width / 2, height - width], [width / 2, height - width]]).buffer(width / 8.0, cap_style=2)
    l2 = ddd.line([[0, 0], [0, height]]).buffer(width / 8.0, cap_style=2)
    sign = l1.union(l2)
    sign = sign.extrude(width / 4.0)
    sign = sign.translate([0, 0, -width / 8.0]).rotate([-math.pi / 2.0, 0, 0])
    sign = sign.translate([0, 0, height])
    sign.name = "Cross"
    return sign

def column(r=0.1, height=2.0, top=None):
    col = ddd.point([0, 0]).buffer(r, resolution =1).extrude(height)
    if top:
        top = top.translate([0, 0, height])
        col = ddd.group([col, top])
    return col

def wayside_cross():
    """
    A wayside cross. A cross on a pole on a pedestal.
    """
    cross = religion_cross()
    col = column(height=2.0, top=cross)
    #ped = pedestal(top=col)
    return col

def plaque():
    '''
    A plaque, just the square form with text.
    Lays centered with its back on the vertical plane.
    '''
    pass

def pedestal():
    '''
    A pedestal with an optional plaque position, and an optional object on top.
    Sits centered on its base.
    '''
    pass


def hedge(length=2.0):
    '''
    A hedge line. Centered on its base.
    '''
    pass

def pot():
    pass

def pot_tree():
    pass

def pot_flower():
    pass

def gardener(length=2.0):
    pass


def bench(length=1.40, height=1.00, seat_height=0.40,
          legs=2, hangout=0.20):
    pass

def bank(length=1.40, height=1.00, seat_height=0.40,
          legs=2, hangout=0.20, angle=100.0, arms=0):
    #bench =
    pass


