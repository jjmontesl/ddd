# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import math

from ddd.ddd import ddd
from ddd.ops import filters
import logging
from ddd.text import fonts


# Get instance of logger for this module
logger = logging.getLogger(__name__)


def post(height=2.00, r=0.075, top=None, side=None, mat_post=None):
    """
    A round (or squared) post.
    """
    col = ddd.point([0, 0]).buffer(r, resolution=0, cap_style=ddd.CAP_SQUARE).extrude(height)
    if mat_post: col = col.material(mat_post)
    col = ddd.uv.map_cylindrical(col)

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
    for idx, item in enumerate(arm_items):
        positem = item.translate([side * (arm_length - (idx + 1) * 0.4), -r, height])
        items.append(positem)

    post = ddd.group([post] + items)
    return post

def lamppost(height=2.80, r=0.25, lamp=None, mat_post=None):
    if lamp is None:
        #lamp = ddd.sphere(r=r, subdivisions=1).scale([1.0, 1.0, 1.2]).material(self.osm.mat_lightbulb)
        lamp = lamp_case(height=0.8, r=r)
    col = post(height=height, top=lamp, mat_post=mat_post or ddd.mats.metal_paint_green)
    col.name = "Lamppost"
    return col

def lamp_case(height=0.5, r=0.25):
    lamp_shape = ddd.point(name="Lamp Case").buffer(r - 0.10, resolution=1)
    lamp = lamp_shape.extrude_step(lamp_shape.buffer(0.10, cap_style=ddd.CAP_SQUARE, join_style=ddd.JOIN_BEVEL), height * 0.8)
    lamp = lamp.extrude_step(lamp_shape.buffer(-0.10), height * 0.2)
    lamp = lamp.material(ddd.mats.lightbulb)
    return lamp

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

def panel(height=1.0, width=2.0, depth=0.2, text=None, texture=None):
    '''
    A panel, like what commerces have either sideways or sitting on the facade. Also
    road panels.
    '''
    panel = ddd.rect([-width / 2.0, -height / 2.0, width / 2.0, height / 2.0]).extrude(depth)
    panel = panel.rotate([math.pi / 2.0, 0, 0])
    panel = panel.material(ddd.material(color='#f0f0ff'))
    panel = ddd.uv.map_cubic(panel)
    panel.name = "Panel"

    if text:
        textobj = ddd.marker(name="Panel Text Marker").translate([0, - depth - 0.02, 0])
        textobj.extra['ddd:text'] = text
        textobj.extra['ddd:text:width'] = width * 0.9
        textobj.extra['ddd:text:height'] = height * 0.9
        textobj.extra['ddd:collider'] = False
        #textobj.extra['ddd:layer'] = "Texts"

    panel = ddd.group([panel, textobj]) if text else panel

    return panel


def busstop_small(height=2.50, panel_height=1.4, panel_width=0.45, text=None):
    obj_post = post(height=height).material(ddd.mats.metal_paint_green)
    obj_panel = panel(height=panel_width, width=panel_height, depth=0.05, text=text)
    obj_panel = obj_panel.rotate([0, -math.pi / 2, 0]).translate([panel_width / 2 + 0.075, 0, height - 0.20 - panel_height / 2])
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


def statue():
    pass

def sculpture(d=1.0, height=4.0):
    """
    An urban sculpture, sitting centered on the XY plane.
    """
    pedestal = ddd.cube(d=d / 2.0)
    pedestal = ddd.uv.map_cubic(pedestal)

    item = ddd.sphere(r=1, subdivisions=2)
    item = item.scale([d, d, height / 2])
    item = filters.noise_random(item, scale=0.2)
    item = item.translate([0, 0, height / 2 + d])
    item = ddd.uv.map_spherical(item)

    item = ddd.group([pedestal, item], name="Urban sculpture")

    return item

def sculpture_text(text, d=1.0, height=4.0):
    """
    An urban sculpture, sitting centered on the XY plane.
    """
    pedestal = ddd.cube(d=d / 2.0)
    pedestal = ddd.uv.map_cubic(pedestal)

    logger.debug("Generating text for: %s", text)
    item = fonts.text(text)
    item = item.extrude(0.5).material(ddd.mats.bronze)
    item = item.rotate([math.pi / 2.0, 0, 0])

    item = filters.noise_random(item, scale=0.03)

    item = item.translate([-0.25, 0.25, 0.0])
    item = item.scale([d, d, height - d])
    item = item.translate([0, 0, height / 2 + d])
    item = ddd.uv.map_cubic(item)

    item = ddd.group([pedestal, item], name="Urban sculpture")

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


def bench(length=1.40, height=1.00, width=0.8, seat_height=0.50,
          legs=2, hangout=0.20):

    seat_thick = 0.10
    leg_thick = 0.2
    leg_padding = 0.3
    leg_width = width - leg_padding
    leg_height = seat_height - seat_thick

    seat = ddd.rect([-length/ 2.0, -width / 2.0, length / 2.0, width / 2.0]).extrude(-seat_thick).translate([0, 0, seat_height])
    legs_objs = []
    leg_spacing = (length - leg_padding * 2) / (legs - 1)
    for leg_idx in range(legs):
        leg = ddd.rect([-leg_thick / 2, -leg_width / 2.0, leg_thick / 2, leg_width / 2]).extrude(leg_height)
        leg = leg.translate([-(length / 2) + leg_padding + leg_spacing * leg_idx, 0, 0])
        legs_objs.append(leg)

    bench = ddd.group([seat] + legs_objs)
    bench.name = "Bench"
    return bench

def bank(length=1.40, height=1.00, seat_height=0.40,
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
    item.material(ddd.mats.steel)
    return item

def trash_bin_hung(height=0.70, r=0.25):
    base = ddd.disc(r=r - 0.05, resolution=3)
    item = base.extrude_step(base, 0.10)
    item = item.extrude_step(base.buffer(0.05, join_style=ddd.JOIN_MITRE), height)
    item = item.extrude_step(base.buffer(0.03, join_style=ddd.JOIN_MITRE), 0.0)
    item = item.extrude_step(base, -(height - 0.2))
    item = item.translate([0, -r, -height + 0.05])
    item.material(ddd.mats.steel)
    return item

def trash_bin_post(height = 1.30):
    item = trash_bin_hung()
    item_post = post(height=height, side=item, mat_post=ddd.mats.steel)
    return item_post
