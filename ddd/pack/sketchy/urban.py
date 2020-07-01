# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import math

from ddd.ddd import ddd
from ddd.ops import filters
import logging
from ddd.text import fonts
from ddd.lighting.lights import PointLight
import sys
import re
import random
from trimesh import transformations
import numpy as np
from ddd.ops.extrusion import extrude_step_multi, extrude_dome


# Get instance of logger for this module
logger = logging.getLogger(__name__)


def cable(a, b, thick=0.20):
    a = np.array(a)
    b = np.array(b)

    #path = ddd.line([a, b])
    #path_section = ddd.point(name="Cable").buffer(thick * 0.5, resolution=1, cap_style=ddd.CAP_ROUND)
    #cable = path_section.extrude_path(path)

    length = np.linalg.norm(b - a)
    cable = ddd.point(name="Cable").buffer(thick * 0.5, resolution=1, cap_style=ddd.CAP_ROUND).extrude(length + thick).translate([0, 0, -thick * 0.5])
    cable = ddd.uv.map_cylindrical(cable)

    vector_up = [0, 0, 1]
    vector_dir = (b - a) / length
    rot_axis = np.cross(vector_up, vector_dir)
    rot_angle = math.asin(np.linalg.norm(rot_axis))
    if rot_angle > 0.00001:
        rotation = transformations.quaternion_about_axis(rot_angle, rot_axis / np.linalg.norm(rot_axis))
        cable = cable.rotate_quaternion(rotation)
    cable = cable.translate(a)

    return cable

def post(height=2.00, r=0.075, top=None, side=None, mat_post=None):
    """
    A round (or squared) post.
    """
    col = ddd.point([0, 0], name="Post").buffer(r, resolution=0, cap_style=ddd.CAP_SQUARE).extrude(height)
    if mat_post: col = col.material(mat_post)
    col = ddd.uv.map_cylindrical(col)
    col = ddd.collision.aabox_from_aabb(col)

    col = ddd.group3([col])
    if top:
        top = top.translate([0, 0, height])
        col.append(top)
    if side:
        side = side.translate([0, -r, height - 0.2])
        col.append(side)

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
    post = post.rotate([math.pi / 2.0, 0, 0]).material(ddd.mats.metal_paint_green)
    post = ddd.uv.map_cubic(post)
    post.name = "Post Curved"

    items = []
    if arm_items:
        for idx, item in enumerate(arm_items):
            positem = item.translate([side * (arm_length - (idx + 1) * 0.4), -r, height])
            items.append(positem)

    post = ddd.group([post] + items)
    return post

def lamppost(height=2.80, r=0.25, lamp=None, mat_post=None):
    if lamp is None:
        #lamp = ddd.sphere(r=r, subdivisions=1).scale([1.0, 1.0, 1.2]).material(self.osm.mat_lightbulb)
        lamp = lamp_case(height=0.8, r=r)
    col = post(height=height, top=lamp, mat_post=mat_post or ddd.mats.metal_paint_green)  # FIXME: materials shall be assigned by styling, not passing args
    col.name = "Lamppost"
    return col

def lamp_case(height=0.5, r=0.25):
    lamp_shape = ddd.point(name="Lamp Case").buffer(r - 0.10, resolution=1)
    lamp = lamp_shape.extrude_step(lamp_shape.buffer(0.10, cap_style=ddd.CAP_SQUARE, join_style=ddd.JOIN_BEVEL), height * 0.8)
    lamp = lamp.extrude_step(lamp_shape.buffer(-0.10), height * 0.2)
    lamp = lamp.material(ddd.mats.lightbulb)
    lamp = ddd.collision.aabox_from_aabb(lamp)
    lamp = ddd.uv.map_cubic(lamp)

    # TODO: Possibly add this with styling too, although lights are first class citizens (used for render)
    light = PointLight([0, 0, height * 0.8], name="Lamp Light", color="#e4e520", radius=18, intensity=1.25, enabled=False)

    lamp_case = ddd.group([lamp, light], name="Lamp Case and Light")

    return lamp_case

def lamp_ball(r=0.25):
    lamp = ddd.sphere(r=r, subdivisions=1)  # .scale([1.0, 1.0, 1.2])
    return lamp

def lamppost_arm(length, lamp_pos='over'):
    pass

def lamppost_with_arms(height, arms=2, degrees=360):
    pass

def trafficlights_head(height=0.8, depth=0.3):

    head = ddd.rect([-0.15, 0, 0.15, height], name="TrafficLight Box").material(ddd.mats.metal_paint_green).extrude(depth)
    disc_green = ddd.disc(ddd.point([0, 0.2]), r=0.09, name="TrafficLight Disc Green").material(ddd.mats.light_green).extrude(0.05)
    disc_orange = ddd.disc(ddd.point([0, 0.4]), r=0.09, name="TrafficLight Disc Green").material(ddd.mats.light_orange).extrude(0.05)
    disc_red = ddd.disc(ddd.point([0, 0.6]), r=0.09, name="TrafficLight Disc Green").material(ddd.mats.light_red).extrude(0.05)

    discs = ddd.group([disc_green, disc_orange, disc_red], name="TrafficLight Discs").translate([0, 0, depth])  # Put discs over head
    head = ddd.group([head, discs], name="TrafficLight Head").translate([0, -height / 2.0, 0])  # Center vertically
    head = head.rotate([math.pi / 2.0, 0, 0])
    return head

def trafficlights():
    head = trafficlights_head()
    post = curvedpost(arm_items=[head])
    post.name = "TrafficLight"
    return post


def traffic_sign(signtype):
    head = None
    if signtype == 'give_way':
        head = traffic_sign_triangle()
    elif signtype == 'stop':
        head = traffic_sign_octagon()
    else:
        try:
            head = traffic_sign_code(signtype)
        except Exception as e:
            logger.warn("Cannot generate traffic sign of type %s: %s", signtype, e)
            return None

    item = post(2.2, r=0.04, top=head, mat_post=ddd.mats.steel)
    return item

def traffic_sign_code(signtype, thick=0.1):

    countrycode, signcode = signtype.split(":")
    head = None

    if countrycode == 'es':

        # From: https://es.wikipedia.org/wiki/Anexo:Se%C3%B1ales_de_tr%C3%A1fico_de_reglamentaci%C3%B3n_de_Espa%C3%B1a#Se%C3%B1ales_de_Prioridad
        #       https://commons.wikimedia.org/wiki/Road_signs_of_Spain
        #print(signcode)
        sign_shape = signcode[0]
        sign_mat = None
        if signcode == "r1": sign_shape = "i"
        if signcode == "r2": sign_shape = "o"
        if signcode in ("r3", "r4"): sign_shape = "v"
        if signcode == "r6": sign_shape = "s"
        if signcode == "r309": sign_shape = "s"
        if re.match(r"r4[0-9]{2}.*", signcode):
            sign_mat = ddd.mats.metal_paint_blue
        if re.match(r"r5[0-9]{2}.*", signcode):
            sign_mat = ddd.mats.metal_paint_white
        if signcode == "r504": sign_shape = "s"
        if signcode in ("r505", "r506"):
            sign_mat = ddd.mats.metal_paint_blue

        if sign_shape == 'p':
            if sign_mat is None: sign_mat = ddd.mats.metal_paint_red
            head = traffic_sign_triangle(thick=thick)
        elif sign_shape == 'i':
            if sign_mat is None: sign_mat = ddd.mats.metal_paint_red
            head = traffic_sign_triangle_inverted(thick=thick)
        elif sign_shape == 'r':
            if sign_mat is None: sign_mat = ddd.mats.metal_paint_red
            head = traffic_sign_circle(thick=thick)
        elif sign_shape == 's':
            if sign_mat is None: sign_mat = ddd.mats.metal_paint_blue
            head = traffic_sign_rect(thick=thick)
        elif sign_shape == 'e':
            if sign_mat is None: sign_mat = ddd.mats.metal_paint_white
            head = traffic_sign_rect(thick=thick)
        elif sign_shape == 'v':
            if sign_mat is None: sign_mat = ddd.mats.metal_paint_white
            head = traffic_sign_rect_rotated(thick=thick)
        elif sign_shape == 'o':
            if sign_mat is None: sign_mat = ddd.mats.metal_paint_red
            head = traffic_sign_octagon(thick=thick)
        else:
            logger.warn("Sign shape unknown: %s", signtype)
            raise NotImplementedError()

        if sign_mat:
            head = head.material(sign_mat)

        # Force steel material
        # TODO: correctly separate back (metal), side (color) and front, replace front with decal
        #head = head.material(ddd.mats.steel)

        # Get sprite
        sprite = ddd.mats.traffic_signs.atlas.sprite(signtype.replace(":", "_") + ".png")
        #print(sprite)

        head_bounds = head.bounds()
        head_width = head_bounds[1][0] - head_bounds[0][0]
        head_height = head_bounds[1][2] - head_bounds[0][2]

        # Create decal (TODO: should replace sign, creating shape and extruding, with single bbox
        decal = ddd.rect(name="Traffic Sign Decal")
        # TODO: move atlas decal mapping and rotation to atlas/uvmapping libs

        # Cut decal (original extruded shape shall be centered at 0)
        shape_aligned = head.extra['extruded_shape']
        shape_bounds = shape_aligned.bounds()
        shape_aligned = shape_aligned.translate([shape_bounds[0] * -1, shape_bounds[1] * -1])
        shape_aligned = shape_aligned.scale([1 / (shape_bounds[2] - shape_bounds[0]), 1 / (shape_bounds[3] - shape_bounds[1])])
        decal_shape = decal.intersection(shape_aligned)
        decal = decal_shape.triangulate().material(ddd.mats.traffic_signs)
        decal = ddd.uv.map_cubic(decal)

        if sprite.rot:
            decal.extra['uv'] = [(sprite.bounds_norm[0] + (sprite.bounds_norm[3] - sprite.bounds_norm[1]) * v[1],
                                  1.0 - (sprite.bounds_norm[1] + (sprite.bounds_norm[2] - sprite.bounds_norm[0]) * v[0]))
                                  for v in decal.extra['uv']]
        else:
            decal.extra['uv'] = [(sprite.bounds_norm[0] + (sprite.bounds_norm[2] - sprite.bounds_norm[0]) * v[0],
                                  1.0 - (sprite.bounds_norm[1] + (sprite.bounds_norm[3] - sprite.bounds_norm[1]) * (1 - v[1])))
                                  for v in decal.extra['uv']]

        decal = decal.translate([-0.5, -0.5, 0]).scale([head_width, head_height, 1]).translate([0, head_height / 2, 0])
        decal = decal.rotate(ddd.ROT_FLOOR_TO_FRONT).translate([0, -thick / 2 - 0.005, 0])
        decal.extra['ddd:shadows'] = False
        decal.extra['ddd:collider'] = False

        # TODO: correctly separate back (metal), side (color) and front, replace front with decal
        decal2 = decal.rotate(ddd.ROT_TOP_HALFTURN).material(ddd.mats.steel)

        # Combine
        head = ddd.group3([head, decal, decal2], name="Traffic Sign Textured")

        if sign_shape in ('s', 'e'):
            # Adapt panel size for rectangular signs
            square_ratio = (sprite.bounds_pixel[2] - sprite.bounds_pixel[0] ) / (sprite.bounds_pixel[3] - sprite.bounds_pixel[1])
            #if sprite.rot: square_ratio = 1 / square_ratio
            head = head.scale([max(square_ratio, 1), 1, max(1 / square_ratio, 1)])
        if sign_shape in ('i', 'v'):
            # FIXME: hack for inverted triangles and squares
            # Move slightly down for pointy shapes, so they penetrate post (avoid, make post move signal)
            head = head.translate([0, 0, -thick])

    else:
        raise NotImplementedError()

    return head


def traffic_sign_triangle(r=0.6, thick=0.1):
    item = ddd.regularpolygon(3, r, name="Sign triangle").material(ddd.mats.metal_paint_red)
    item = item.rotate(math.pi / 2 + math.pi).rotate(math.pi).extrude(thick)
    item = item.rotate(ddd.ROT_FLOOR_TO_FRONT).translate([0, thick / 2, r - r * math.cos(math.pi / 3)])
    item = ddd.uv.map_cubic(item)
    return item

def traffic_sign_triangle_inverted(r=0.6, thick=0.1):
    item = ddd.regularpolygon(3, r, name="Sign triangle inverted").material(ddd.mats.metal_paint_red)
    item = item.rotate(math.pi / 2 + math.pi).extrude(thick)
    item = item.rotate(ddd.ROT_FLOOR_TO_FRONT).translate([0, thick / 2, r])
    item = ddd.uv.map_cubic(item)
    return item

def traffic_sign_octagon(r=0.5, thick=0.1):
    item = ddd.regularpolygon(8, r, name="Sign triangle").material(ddd.mats.metal_paint_red)
    item = item.rotate(math.pi / 8).extrude(thick)
    item = item.rotate(ddd.ROT_FLOOR_TO_FRONT).translate([0, thick / 2, r * math.cos(math.pi / 8)])
    item = ddd.uv.map_cubic(item)
    return item

def traffic_sign_rect(width=0.8, height=0.8, thick=0.1):
    item = ddd.rect([-width/2, -height/2, width/2, height/2], name="Sign rect").material(ddd.mats.metal_paint_blue)
    item = item.extrude(thick)
    item = item.rotate(ddd.ROT_FLOOR_TO_FRONT).translate([0, thick / 2, height / 2])
    item = ddd.uv.map_cubic(item)
    return item

def traffic_sign_rect_rotated(r=0.5, thick=0.1):
    item = ddd.regularpolygon(4, r, name="Sign square angled").material(ddd.mats.metal_paint_white)
    item = item.extrude(thick)
    item = item.rotate(ddd.ROT_FLOOR_TO_FRONT).translate([0, thick / 2, r])
    item = ddd.uv.map_cubic(item)
    return item

def traffic_sign_circle(r=0.5, thick=0.1):
    sides = 16
    item = ddd.regularpolygon(sides, r, name="Sign circle").material(ddd.mats.metal_paint_red)
    item = item.rotate(math.pi / sides).extrude(thick)
    item = item.rotate(ddd.ROT_FLOOR_TO_FRONT).translate([0, thick / 2, r * math.cos(math.pi / sides)])
    item = ddd.uv.map_cubic(item)
    return item


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
    sign = sign.material(ddd.material(color='#00ff00'))
    sign = ddd.uv.map_cubic(sign)
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
    arm = arm.material(ddd.material(color='#888888'))
    arm = ddd.uv.map_cubic(arm)
    sign = sign.rotate([0, 0, -math.pi / 2.0]).translate([depth / 2, 0, 0])
    sign = sign.translate([0, -(arm_length + size * 0.66), 0])
    return ddd.group([sign, arm], name="Pharmacy Side Sign with Arm")

def panel(height=1.0, width=2.0, depth=0.2, text=None, text_back=None, texture=None, center=False):
    '''
    A panel, like what commerces have either sideways or sitting on the facade. Also
    road panels.
    '''
    panel = ddd.rect([-width / 2.0, -height / 2.0, width / 2.0, height / 2.0]).extrude(depth, center=True)
    panel = panel.rotate(ddd.ROT_FLOOR_TO_FRONT)
    panel = panel.material(ddd.material(color='#f0f0ff'))
    panel = ddd.uv.map_cubic(panel)
    panel.name = "Panel"

    if text:
        textobj = ddd.marker(name="Panel Text Marker").translate([0, -depth * 0.5 - 0.02, 0])
        textobj.extra['ddd:text'] = text
        textobj.extra['ddd:text:width'] = width * 0.9
        textobj.extra['ddd:text:height'] = height * 0.9
        textobj.extra['ddd:collider'] = False
        textobj.extra['ddd:shadows'] = False
        textobj.extra['ddd:occluder'] = False
        #textobj.extra['ddd:layer'] = "Texts"
    if text_back:
        textbackobj = ddd.marker(name="Panel Text Marker").rotate([0, 0, math.pi]).translate([0, +depth * 0.5 + 0.02, 0])
        textbackobj.extra['ddd:text'] = text
        textbackobj.extra['ddd:text:width'] = width * 0.9
        textbackobj.extra['ddd:text:height'] = height * 0.9
        textbackobj.extra['ddd:collider'] = False
        textbackobj.extra['ddd:shadows'] = False
        textbackobj.extra['ddd:occluder'] = False

    panel = ddd.group3([panel])
    if text: panel.append(textobj)
    if text_back: panel.append(textbackobj)

    if not center:
        panel = panel.translate([0, - depth * 0.5, 0])

    return panel


def busstop_small(height=2.50, panel_height=1.4, panel_width=0.45, text=None):
    obj_post = post(height=height).material(ddd.mats.metal_paint_green)
    obj_panel = panel(height=panel_width, width=panel_height, depth=0.05, text=text, text_back=text, center=True)
    obj_panel = obj_panel.rotate([0, math.pi / 2, 0]).translate([panel_width / 2 + 0.075, 0, height - 0.20 - panel_height / 2])
    obj = ddd.group([obj_post, obj_panel])
    return obj

def busstop_covered():
    pass

def post_box(height=1.10, r=0.35):
    circle = ddd.point([0, 0]).buffer(r, resolution=3, cap_style=ddd.CAP_ROUND)
    obj = circle.extrude_step(circle, 0.35)
    obj = obj.extrude_step(circle.scale([0.9, 0.9, 1]), 0.02)
    obj = obj.extrude_step(circle.scale([0.9, 0.9, 1]), height - 0.4)
    obj = obj.extrude_step(circle.scale([1.0, 1.0, 1]), 0.05)
    obj = obj.extrude_step(circle.scale([1.0, 1.0, 1]), 0.10)
    obj = obj.extrude_step(circle.scale([0.6, 0.6, 1]), 0.05)
    obj = obj.material(ddd.mats.metal_paint_yellow)
    obj = ddd.uv.map_cylindrical(obj)
    obj.name = "Post Box"
    logger.warn("Post Box collider should be a cylinder.")
    return obj


def fire_hydrant(height=0.90, r=0.25):
    """
    Ref: https://upload.wikimedia.org/wikipedia/commons/5/5a/Downtown_Charlottesville_fire_hydrant.jpg
    """
    circle = ddd.point([0, 0]).buffer(r, resolution=3, cap_style=ddd.CAP_ROUND)
    obj = circle.scale([0.85, 0.85, 1]).extrude_step(circle.scale([0.85, 0.85, 1]), 0.10)
    obj = obj.extrude_step(circle.scale([0.6, 0.6, 1]), 0.01)
    obj = obj.extrude_step(circle.scale([0.6, 0.6, 1]), height - 0.3)
    obj = obj.extrude_step(circle.scale([0.82, 0.82, 1]), 0.01)
    obj = obj.extrude_step(circle.scale([0.85, 0.85, 1]), 0.035)
    obj = obj.extrude_step(circle.scale([0.82, 0.82, 1]), 0.035)
    obj = obj.extrude_step(circle.scale([0.6, 0.6, 1]), 0.01)
    obj = obj.extrude_step(circle.scale([0.55, 0.55, 1]), 0.05)
    obj = obj.extrude_step(circle.scale([0.45, 0.45, 1]), 0.05)
    obj = obj.extrude_step(circle.scale([0.3, 0.3, 1]), 0.05)
    obj = obj.extrude_step(circle.scale([0.1, 0.1, 1]), 0.02)

    obj = obj.material(ddd.mats.metal_paint_red)
    obj = ddd.uv.map_cylindrical(obj)

    barh = ddd.cylinder(height=r * 1.8, r=r * 0.6 * 0.5, center=True, name="Fire hydrant taps")
    barh = barh .material(ddd.mats.metal_paint_red)
    barh = ddd.uv.map_cylindrical(barh)
    barh = barh.rotate(ddd.ROT_FLOOR_TO_FRONT).rotate(ddd.ROT_TOP_CCW)
    barh = barh.translate([0, 0, height * 0.65])

    barf = ddd.cylinder(height=r * 0.8, r=r * 0.6 * 0.7, center=False, name="Fire hydrant front")
    barf = barf .material(ddd.mats.metal_paint_red)
    barf = ddd.uv.map_cylindrical(barf)
    barf = barf.rotate(ddd.ROT_FLOOR_TO_FRONT)
    barf = barf.translate([0, 0, height * 0.5])

    obj = ddd.group3([obj, barh, barf])
    obj = obj.combine()

    obj.name = "Fire Hydrant"
    return obj


def bollard(height=1.2, r=0.2, sides=6):
    """
    A bollard. Sits centered on its base.
    """
    bollard = ddd.regularpolygon(6, r, name="Bollard")
    extrude_steps = ((2.0, 0), (2.0, 0.75), (1.0, 1), (1.0, 6.75), (2.0, 7), (2.0, 7.75), (1.0, 8))
    bollard = extrude_step_multi(bollard, extrude_steps, base=False, cap=True, scale_y=height / 8)
    bollard = bollard.material(ddd.mats.bronze)
    bollard = ddd.uv.map_cylindrical(bollard)
    return bollard


def pedestal(obj=None, d=1.0):
    """
    A pedestal with an optional object on top.
    Sits centered on its base.
    """

    pedestal = ddd.cube(d=d / 2.0).material(ddd.mats.bronze)
    pedestal = ddd.uv.map_cubic(pedestal)

    obj = obj.translate([0, 0, d])

    item = ddd.group([pedestal, obj], name="Pedestal: %s" % obj.name)
    return item

def statue():
    pass

def sculpture(d=1.0, height=4.0):
    """
    An urban sculpture, sitting centered on the XY plane.
    """
    #pedestal = ddd.cube(d=d / 2.0)
    #pedestal = ddd.uv.map_cubic(pedestal)

    item = ddd.sphere(r=1, subdivisions=2, name="Sculpture")
    item = item.scale([d, d, height / 2])
    item = filters.noise_random(item, scale=0.2)
    item = item.translate([0, 0, height / 2])  # + d
    item = ddd.uv.map_spherical(item)

    return item

def sculpture_text(text, d=1.0, height=4.0, vertical=False):
    """
    An urban sculpture, sitting centered on the XY plane.
    """
    #pedestal = ddd.cube(d=d / 2.0)
    #pedestal = ddd.uv.map_cubic(pedestal)

    logger.debug("Generating text for: %s", text)
    item = fonts.text(text)
    item = item.extrude(0.5).material(ddd.mats.bronze).recenter()

    if vertical:
        item = item.rotate(ddd.ROT_TOP_CCW)
    item = item.rotate(ddd.ROT_FLOOR_TO_FRONT)

    item = filters.noise_random(item, scale=0.03)

    bounds = item.bounds()
    item = item.scale([d, d, (height) / (bounds[1][2] - bounds[0][2])]).recenter(onplane=True)
    #item = item.translate([0, 0, d])
    item = ddd.uv.map_cubic(item)

    #item = ddd.group([pedestal, item], name="Urban sculpture: %s" % text)
    item.name = "Urban sculpture: %s" % text

    return item


def fountain(r=1.5):
    # Base
    base = ddd.disc(r=r, resolution=2).extrude(0.30).material(ddd.mats.stone)
    base = ddd.uv.map_cylindrical(base)

    # Fountain
    fountain = ddd.sphere(r=r, subdivisions=1).subtract(ddd.cube(d=r * 1.2)).subtract(ddd.sphere(r=r - 0.2, subdivisions=1))
    fountain = fountain.translate([0, 0, 1.2])  # TODO: align
    fountain = fountain.material(ddd.mats.stone)
    fountain = ddd.uv.map_spherical(fountain)
    #.subtract(base)
    # Water
    water = ddd.disc(r=r-0.2, resolution=2).triangulate().translate([0, 0, 1.1]).material(ddd.mats.water)
    water.extra['ddd:collider'] = False
    water.extra['ddd:occluder'] = False
    water.extra['ddd:shadows'] = False

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
    sign = ddd.uv.map_cubic(sign)
    sign.name = "Cross"
    return sign

def column(r=0.1, height=2.0, top=None):
    col = ddd.point([0, 0]).buffer(r, resolution =1).extrude(height)
    col = ddd.uv.map_cubic(col)
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

def bell(r=1.00, height=2.6, thick=0.10):
    """
    The bell is hung on 0, 0, 0.
    """
    base = ddd.disc(r=r, resolution=4, name="Bell").subtract(ddd.disc(r=r - thick, resolution=4))
    extrude_steps = ((4.45, 0), (4.5, 0.25), (4.3, 1), (3.7, 2), (3.0, 3), (2.5, 4), (2.3, 5), (2.4, 6), (2.6, 7))
    bell = extrude_step_multi(base, extrude_steps, base=True, cap=False, scale_y=height / 10)
    bell = bell.twosided()

    cap = extrude_dome(ddd.disc(r=r * (2.6 / 4.45), resolution=4), height=1.5 / 10)
    cap = cap.translate([0, 0, 7 / 10 * height])

    bell = ddd.group([bell, cap]).combine()
    bell = bell.material(ddd.mats.bronze)
    bell = ddd.uv.map_cylindrical(bell)
    bell = bell.translate([0, 0, -height])

    return bell



def plaque():
    '''
    A plaque, just the square form with text.
    Lays centered with its back on the vertical plane.
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


def bench(length=1.40, height=1.00, width=0.8, seat_height=0.45,
          legs=2, hangout=0.20):

    seat_thick = 0.05
    leg_thick = 0.05
    leg_padding = 0.3
    leg_width = width - leg_padding
    leg_height = seat_height - seat_thick

    seat = ddd.rect([-length/ 2.0, -width / 2.0, length / 2.0, width / 2.0], name="Bench Seat")
    seat = seat.extrude(-seat_thick).translate([0, 0, seat_height])

    legs_objs = []
    leg_spacing = (length - leg_padding * 2) / (legs - 1)
    for leg_idx in range(legs):
        leg = ddd.rect([-leg_thick / 2, -leg_width / 2.0, leg_thick / 2, leg_width / 2], name="Bench Leg").extrude(leg_height)
        leg = leg.translate([-(length / 2) + leg_padding + leg_spacing * leg_idx, 0, 0])
        legs_objs.append(leg)

    bench = ddd.group([seat] + legs_objs, name="Bench")
    bench = bench.material(ddd.mats.stone)
    bench = ddd.uv.map_cubic(bench)
    bench.name = "Bench"
    return bench

def bank(length=1.40, height=1.00, seat_height=0.45,
          legs=2, hangout=0.20, angle=100.0, arms=0):
    #bench =
    pass

def trash_bin(height=1.20, r=0.35):
    base = ddd.disc(r=r - 0.05, resolution=3)
    item = base.extrude_step(base, 0.10)
    item = item.extrude_step(base.buffer(0.05, join_style=ddd.JOIN_MITRE), 0.0)
    item = item.extrude_step(base.buffer(0.05, join_style=ddd.JOIN_MITRE), height - 0.15)
    item = item.extrude_step(base, 0.05)
    item = item.extrude_step(base.buffer(-0.05), 0.0)
    item = item.extrude_step(base.buffer(-0.05), -(height - 0.4))
    item = item.material(ddd.mats.steel)
    return item

def trash_bin_hung(height=0.70, r=0.25):
    base = ddd.disc(r=r - 0.05, resolution=3)
    item = base.extrude_step(base, 0.10)
    item = item.extrude_step(base.buffer(0.05, join_style=ddd.JOIN_MITRE), height)
    item = item.extrude_step(base.buffer(0.03, join_style=ddd.JOIN_MITRE), 0.0)
    item = item.extrude_step(base, -(height - 0.2))
    item = item.translate([0, -r, -height + 0.05])
    item = item.material(ddd.mats.steel)
    return item

def trash_bin_post(height = 1.30):
    item = trash_bin_hung()
    item_post = post(height=height, side=item, mat_post=ddd.mats.steel)
    return item_post


def patio_table(width=0.8, length=0.8, height=0.73):
    table_thick = 0.05
    tabletop = ddd.rect([0, 0, width, length], name="Table top").recenter().extrude(table_thick)
    tabletop = ddd.uv.map_cubic(tabletop)
    tabletop = tabletop.translate([0, 0, height-table_thick])

    table = ddd.group3([tabletop], name="Table")

    leg_thick = 0.05
    leg_padding = 0.1
    for c in [(1, 1), (-1, 1), (-1, -1), (1, -1)]:
        leg = ddd.point([c[0] * (width / 2 - leg_padding), c[1] * (length / 2 - leg_padding)]).buffer(leg_thick / 2).extrude(height - table_thick)
        leg = ddd.uv.map_cylindrical(leg)
        table.append(leg)

    table = table.material(ddd.mats.steel)
    table = ddd.collision.aabox_from_aabb(table)
    table.extra['ddd:mass'] = 5.0
    return table

def patio_chair(width=0.45, length=0.45, seat_height=0.40):
    seat_thick = 0.05
    seat = ddd.rect([0, 0, width, length], name="Chair seat").recenter().extrude(seat_thick)
    seat = ddd.uv.map_cubic(seat)
    seat = seat.translate([0, 0, seat_height - seat_thick])

    stool = ddd.group3([seat], name="Chair stool")

    leg_thick = 0.05
    leg_padding = leg_thick
    for c in [(1, 1), (-1, 1), (-1, -1), (1, -1)]:
        leg = ddd.point([c[0] * (width / 2 - leg_padding), c[1] * (length / 2 - leg_padding)]).buffer(leg_thick / 2).extrude(seat_height - seat_thick)
        leg = ddd.uv.map_cylindrical(leg)
        stool.append(leg)

    stool = stool.material(ddd.mats.steel)
    stool = ddd.collision.aabox_from_aabb(stool)

    back_height = 0.3
    back = ddd.rect([width, seat_thick], name="Chair Back").recenter().extrude(back_height)
    back = back.material(ddd.mats.steel)
    back = ddd.uv.map_cubic(back)
    back = back.translate([0, length / 2 - seat_thick, seat_height])
    back = ddd.collision.aabox_from_aabb(back)

    chair = ddd.group3([stool, back], name="Chair")
    chair.extra['ddd:mass'] = 2.5
    return chair

def patio_umbrella(side=2.5, height=2.5):
    base_height = 0.04
    base_side = 0.4
    base_weight = ddd.rect([base_side, base_side], name="Base weight").recenter()
    base_weight = base_weight.extrude(base_height).material(ddd.mats.metal_paint_white)
    base_weight = ddd.uv.map_cubic(base_weight)

    pole_r = 0.04
    pole = ddd.point(name="Pole").buffer(pole_r).extrude(height - base_height).translate([0, 0, base_height])
    pole = pole.material(ddd.mats.metal_paint_white)
    pole = ddd.uv.map_cylindrical(pole)

    umbrella_height = height - 1.8
    umbrella = ddd.rect([side, side], name="Umbrella").recenter().material(ddd.mats.rope)
    umbrella = umbrella.extrude_step(ddd.point(), umbrella_height, base=False, cap=False)
    umbrella = umbrella.twosided().translate([0, 0, height - umbrella_height - 0.02])
    umbrella = ddd.uv.map_cubic(umbrella)

    item = ddd.group([base_weight, pole, umbrella])
    return item


# Childrens playground
# See: https://wiki.openstreetmap.org/wiki/Key:playground

def childrens_playground_arc(length=3.25, width=1.0, sides=7, height=None):

    arc_thick = 0.08
    bar_thick = 0.05
    if height is None:
        height = length / 2 * 0.9

    circleline = ddd.regularpolygon(sides * 2, name="Childrens Playground Arc Side Arc").rotate(-math.pi / 2).outline().scale([length / 2, height])
    arcline = circleline.intersection(ddd.rect([-length, 0.1, length, height * 2]))
    arc = circleline.buffer(arc_thick / 2).intersection(ddd.rect([-length, 0, length, height * 2]))
    arc = arc.extrude(arc_thick, center=True).material(ddd.mats.metal_paint_red)
    arc = arc.rotate(ddd.ROT_FLOOR_TO_FRONT)
    arc = ddd.uv.map_cubic(arc)

    arc1 = arc.copy().translate([0, -width / 2, 0])
    arc2 = arc.copy().translate([0, +width / 2, 0])
    item = ddd.group([arc1, arc2])

    bar = ddd.point(name="Childrens Playground Arc Bar").buffer(bar_thick / 2).extrude(width - arc_thick, center=True).rotate(ddd.ROT_FLOOR_TO_FRONT)
    bar = ddd.uv.map_cubic(bar)
    mats = [ddd.mats.metal_paint_white, ddd.mats.metal_paint_red]
    for idx, p in enumerate(arcline.geom.coords[1:-1]):
        pbar = bar.copy().translate([p[0], 0, p[1]])
        pbar = pbar.material(mats[idx % 2])
        item.append(pbar)

    return item

def childrens_playground_slide(length=4.5, height=None, width=0.5):

    slide_thick = 0.03
    side_thick = 0.06
    if height is None:
        height = length * 0.45

    side_mat = random.choice([ddd.mats.metal_paint_red, ddd.mats.metal_paint_green, ddd.mats.metal_paint_yellow])

    slideline = ddd.point([0, 0], name="Slide").line_to([0.5, 0]).line_to([3, 1.5]).line_to([3.5, 1.5])
    # TODO: slideline.interpolate_cubic(), or slideline.smooth() or similar
    slideprofile = slideline.buffer(slide_thick / 2, cap_style=ddd.CAP_FLAT)
    slide = slideprofile.scale([1 / 4.5 * length, 1 / 2.0 * height])
    slide = slide.extrude(width - side_thick, center=True).rotate(ddd.ROT_FLOOR_TO_FRONT)
    slide = slide.material(ddd.mats.steel)
    slide = ddd.uv.map_cubic(slide)

    slidesideprofile = slideline.line_to([3.5, 1.7]).line_to([3, 1.7]).line_to([0.5, 0.2]).line_to([0, 0.2])
    slidesideprofile = ddd.polygon(list(slidesideprofile.geom.coords), name="Slide profile")
    stairssideprofile = ddd.polygon([[3.5, 1.5], [3.5, 2], [4, 2], [4, 1.5], [4.5, 0], [4.0, 0], [3.5, 1.5]])
    stairssideprofile = stairssideprofile.union(ddd.point([3.75, 2]).buffer(0.25, cap_style=ddd.CAP_ROUND))
    stairssideprofile = stairssideprofile.subtract(ddd.point([3.75, 2]).buffer(0.15, cap_style=ddd.CAP_ROUND, resolution=2))  # Hole
    stairssideprofile = stairssideprofile.translate([-0.25, 0])
    slidesideprofile = slidesideprofile.union(stairssideprofile)

    slidesideprofile = slidesideprofile.scale([1 / 4.5 * length, 1 / 2.0 * height])
    slidesideprofile = slidesideprofile.extrude(side_thick, center=True).rotate(ddd.ROT_FLOOR_TO_FRONT)
    slidesideprofile = slidesideprofile.material(side_mat)
    slidesideprofile = ddd.uv.map_cubic(slidesideprofile)

    slidesideprofile1 = slidesideprofile.translate([0, width / 2, 0])
    slidesideprofile2 = slidesideprofile.translate([0, -width / 2, 0])

    item = ddd.group([slide, slidesideprofile1, slidesideprofile2])

    numsteps = int((height - 1) / 0.3) + 1
    for i in range(numsteps):
        step = ddd.box([-0.1, -((width - side_thick) / 2), 0, 0.1, ((width - side_thick) / 2), 0.05], name="Slide Step")
        step = step.translate([4 - (i + 1) * (0.5 / (numsteps + 1)), 0, (i + 1) * 0.3]).material(ddd.mats.steel)
        step = ddd.uv.map_cubic(step)
        item.append(step)

    item = item.translate([-4.5/2, 0, 0]).rotate(ddd.ROT_TOP_CCW)

    return item

def childrens_playground_swingset(length=2.2, num=2, height=2.1, width=1.6):
    """
    """
    frame_thick = 0.06
    path = ddd.point([-width / 2, 0], name="Swing path").line_to([-width*2/6, height - width*2/6])
    path = path.arc_to([width*2/6, height - width *2/6], [0, height - width*2/6], ccw=False)
    path = path.line_to([width / 2, 0])

    side_mat = random.choice([ddd.mats.metal_paint_red, ddd.mats.metal_paint_green, ddd.mats.metal_paint_yellow])
    frameside = path.buffer(frame_thick / 2).material(side_mat)
    frameside = frameside.extrude(frame_thick, center=True).rotate(ddd.ROT_FLOOR_TO_FRONT).rotate(ddd.ROT_TOP_CCW)
    frameside = frameside.material(ddd.mats.steel)
    frameside = ddd.uv.map_cubic(frameside)

    frameside1 = frameside.translate([-length/2, 0, 0])
    frameside2 = frameside.translate([length/2, 0, 0])

    topbar = ddd.point([(-length + frame_thick) / 2, 0], name="Swing top bar").line_to([(length - frame_thick) / 2, 0])
    topbar = topbar.buffer(frame_thick / 2).extrude(frame_thick, center=True).translate([0, 0, height])
    topbar = topbar.material(ddd.mats.steel)
    topbar = ddd.uv.map_cubic(topbar)

    swingset = ddd.group3([frameside1, frameside2, topbar], name="Playground swingset")

    for i in range(num):
        posx = -length / 2 + (i + 0.5) * (length / (num))
        swing = childrens_playground_swing(height=height - 0.4)
        swing = swing.translate([posx, 0, height])
        swingset.append(swing)

    return swingset

def childrens_playground_swing(width=0.45, height=1.6, depth=0.2, width_top=None):

    if width_top is None:
        width_top = width * 1.1

    seat_thick = 0.05
    seat = ddd.rect([width, depth], name="Playground Swing Seat").recenter().extrude(seat_thick, center=True)
    seat = ddd.uv.map_cubic(seat)
    seat = seat.material(ddd.mats.plastic_black)

    chain_thick = 0.02
    #chain = ddd.point(name="Playground Swing Chain").buffer(chain_thick / 2).extrude(height)
    #chain.translate([0, ])
    chain1 = cable([-width / 2, 0, 0], [-width_top / 2, 0, height], thick=chain_thick)
    chain1 = chain1.material(ddd.mats.chain)
    chain2 = cable([width / 2, 0, 0], [width_top / 2, 0, height], thick=chain_thick)
    chain2 = chain2.material(ddd.mats.chain)

    swing = ddd.group3([seat, chain1, chain2], name="Swing")
    swing = swing.translate([0, 0, -height])
    return swing


def childrens_playground_sandbox(r=1.5, sides=5, height=0.4, thick=0.1):
    """
    """
    area = ddd.regularpolygon(sides, r, name="Playground Sand")
    item = area.material(ddd.mats.wood)
    item = item.outline().buffer(thick / 2).extrude(height)
    item = ddd.uv.map_cubic(item)
    item.name = "Playground sandbox border"

    area = area.triangulate().material(ddd.mats.sand).translate([0, 0, height / 3])
    area = ddd.uv.map_cubic(area)

    item = ddd.group([area, item], name="Playground Sandbox")

    return item




