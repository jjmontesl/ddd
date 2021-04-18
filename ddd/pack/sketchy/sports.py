# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import math

from ddd.ddd import ddd
from ddd.ops import filters
import logging
from ddd.text import fonts
from ddd.pack.sketchy import urban
from ddd.pack.sketchy.urban import post, curvedpost


# Get instance of logger for this module
logger = logging.getLogger(__name__)


'''
def football_field_lines_area(area, line_width=0.10):
    # TODO: Receive size or aspect ratio and create centered so it's more reusable, and we can enforce size.

    rectangle = ddd.geomops.inscribed_rectangle(area, padding=0.5)

    if not rectangle.geom or not rectangle.geom.exterior:
        return

    coords = rectangle.geom.exterior.coords

    #seg1 = ([coords[1][0] - coords[0][0], coords[1][1] - coords[0][1]])
    #seg2 = ([coords[2][0] - coords[1][0], coords[2][1] - coords[1][1]])
    #l1 = (seg1[0] ** 2)[0] + (seg1[1] ** 2)
    #l2 = (seg2[0] ** 2)[0] + (seg2[1] ** 2)

    width_seg = ddd.line([coords[0], coords[1]])
    length_seg = ddd.line([coords[1], coords[2]])
    #width2_seg = ddd.line([coords[2], coords[3]])
    #length2_seg = ddd.line([coords[3], coords[0]])

    width_l = width_seg.geom.length
    length_l = length_seg.geom.length

    if width_l > length_l:
        (width_l, length_l) = (length_l, width_l)
        (width_seg, length_seg) = (length_seg, width_seg)
        #(width2_seg, length2_seg) = (length2_seg, width2_seg)

    # Generate lines, rotate and translate to area
    lines = football_field_lines(length_l, width_l, line_width)
    angle = math.atan2(length_seg.geom.coords[1][1] - length_seg.geom.coords[0][1],
                       length_seg.geom.coords[1][0] - length_seg.geom.coords[0][0])
    lines = lines.rotate([0, 0, angle]).translate([rectangle.geom.centroid.coords[0][0], rectangle.geom.centroid.coords[0][1], 0])

    return lines
'''

def field_lines_area(area, lines_method, padding=0.5, **kwargs):
    """
    Playground fields are seen x: length, y: width
    """

    rectangle = ddd.geomops.inscribed_rectangle(area, padding=padding)
    if not rectangle.geom or not rectangle.geom.exterior: return

    coords = rectangle.geom.exterior.coords
    width_seg = ddd.line([coords[0], coords[1]])
    length_seg = ddd.line([coords[1], coords[2]])
    width_l = width_seg.geom.length
    length_l = length_seg.geom.length

    if width_l > length_l:
        (width_l, length_l) = (length_l, width_l)
        (width_seg, length_seg) = (length_seg, width_seg)

    # Generate lines, rotate and translate to area
    lines = lines_method(length_l, width_l, **kwargs)
    angle = math.atan2(length_seg.geom.coords[1][1] - length_seg.geom.coords[0][1],
                       length_seg.geom.coords[1][0] - length_seg.geom.coords[0][0])
    lines = lines.rotate([0, 0, angle]).translate([rectangle.geom.centroid.coords[0][0], rectangle.geom.centroid.coords[0][1], 0])

    return lines

def football_field_lines(length=105.0, width=67.5, line_width=0.10):
    """
    Playground fields are seen x: length, y: width
    """

    item = ddd.group3(name="Football lines")

    rectangle = ddd.rect([-length / 2, -width / 2, length / 2, width / 2])

    coords = rectangle.geom.exterior.coords
    width_seg = ddd.line([coords[0], coords[1]])
    length_seg = ddd.line([coords[1], coords[2]])
    width2_seg = ddd.line([coords[2], coords[3]])
    length2_seg = ddd.line([coords[3], coords[0]])
    width_l = width_seg.geom.length
    length_l = length_seg.geom.length

    exterior = rectangle.outline().buffer(line_width, cap_style=ddd.CAP_SQUARE).triangulate().material(ddd.material(color='#ffffff'))
    exterior.name = "Bounds line"
    exterior.extra['ddd:collider'] = False
    exterior.extra['ddd:shadows'] = False

    midline_2d = ddd.line([length_seg.geom.centroid, length2_seg.geom.centroid], name="Mid line")
    midline = midline_2d.buffer(line_width, cap_style=ddd.CAP_SQUARE).triangulate().material(ddd.material(color='#ffffff'))
    midline.extra['ddd:collider'] = False
    midline.extra['ddd:shadows'] = False

    midcircle_radius_ratio = 9.15 / 67.5
    midcircle = ddd.disc(center=midline_2d.geom.centroid.coords, r=width_l * midcircle_radius_ratio).outline()
    midcircle = midcircle.buffer(line_width, cap_style=ddd.CAP_SQUARE).triangulate().material(ddd.material(color='#ffffff'))
    midcircle.extra['ddd:collider'] = False
    midcircle.extra['ddd:shadows'] = False

    item.append(exterior)
    item.append(midline)
    item.append(midcircle)

    centralline_2d = ddd.line([width_seg.geom.centroid, width2_seg.geom.centroid], name="Central line")
    goal_width = 7.2

    smallarea_width_ratio = (goal_width + 5.5 * 2) / 67.5
    smallarea_length_ratio = 5.5 / 67.5
    largearea_width_ratio = 40.3 / 67.5
    largearea_length_ratio = 16.5 / 105.5

    for side in (-1, 1):
        smallarea = ddd.line([[0, -1], [1, -1], [1, 1], [0, 1]])
        smallarea = smallarea.scale([smallarea_length_ratio * length, smallarea_width_ratio * width * 0.5])
        if side == 1: smallarea = smallarea.rotate(math.pi)
        smallarea = smallarea.translate([side * length_l / 2, 0])
        smallarea = smallarea.buffer(line_width, cap_style=ddd.CAP_SQUARE).triangulate().material(ddd.material(color='#ffffff'))
        smallarea.extra['ddd:collider'] = False
        smallarea.extra['ddd:shadows'] = False
        item.append(smallarea)

        largearea = ddd.line([[0, -1], [1, -1], [1, 1], [0, 1]])
        largearea = largearea.scale([largearea_length_ratio * length, largearea_width_ratio * width * 0.5])
        if side == 1: largearea = largearea.rotate(math.pi)
        largearea = largearea.translate([side * length_l / 2, 0])
        largearea = largearea.buffer(line_width, cap_style=ddd.CAP_SQUARE).triangulate().material(ddd.material(color='#ffffff'))
        largearea.extra['ddd:collider'] = False
        largearea.extra['ddd:shadows'] = False
        item.append(largearea)

        # TIODO: shall depend on the football type, assign earlier maybe
        if width > 30: goal = football_goal11()
        elif width > 15: goal = football_goal9()
        elif width > 9: goal = football_goal7()
        else: goal = football_goal_small()


        goal = goal.rotate(ddd.ROT_TOP_CCW)
        if side == 1: goal = goal.rotate(ddd.ROT_TOP_HALFTURN)
        goal = goal.translate([side * length_l / 2, 0, 0])
        item.append(goal)

    item = ddd.uv.map_cubic(item)

    return item

def football_goal11():
    return football_goal(width=7.2, height=2.44)

def football_goal9():
    return football_goal(width=4.88, height=1.83)

def football_goal7():
    return football_goal(width=3.66, height=1.83)

def football_goal_small():
    return football_goal(width=2.8, height=1.6)

def football_goal(width=4.88, height=1.83, thick=0.20):
    line = ddd.point().line_to([0, height]).line_to([width, height]).line_to([width, 0]).translate([-width/2, 0])
    line = line.buffer(thick * 0.5).extrude(-thick)
    line = line.rotate(ddd.ROT_FLOOR_TO_FRONT).material(ddd.mats.steel)
    return line


def tennis_field_lines(length=23.77, width=10.97, square_length_ratio=6.40 / 23.77, net_height_center=0.914, net_height_post=1.07, line_width=0.10):
    """
    Playground fields are seen x: length, y: width

    doubles_width_official = 10.97
    singles_width_official = 8.23
    extra_width = 3.65 (/2?)
    extra_length = 6.50 (/2?)
    """

    length = min(length, 23.77)
    width = min(width, 10.97)
    (length, width) = enforce_aspect_ratio(length, width, 23.77 / 10.97)

    item = ddd.group3(name="Tennis lines")

    rectangle = ddd.rect([-length / 2, -width / 2, length / 2, width / 2])
    coords = rectangle.geom.exterior.coords
    width_seg = ddd.line([coords[0], coords[1]])
    length_seg = ddd.line([coords[1], coords[2]])
    width2_seg = ddd.line([coords[2], coords[3]])
    length2_seg = ddd.line([coords[3], coords[0]])
    width_l = width_seg.geom.length
    length_l = length_seg.geom.length

    exterior = rectangle.outline().buffer(line_width, cap_style=ddd.CAP_SQUARE).triangulate().material(ddd.material(color='#ffffff'))
    exterior.name = "Bounds line"
    exterior.extra['ddd:collider'] = False
    exterior.extra['ddd:shadows'] = False

    item.append(exterior)

    centralline_2d = ddd.line([width_seg.geom.centroid, width2_seg.geom.centroid], name="Central line")
    goal_width = 4.88

    # Sideline
    sideline_pos_ratio = 8.23 / 10.97
    for side in (-1, 1):
        sideline = centralline_2d.translate([0, side * width * sideline_pos_ratio * 0.5])
        sideline = sideline.buffer(line_width, cap_style=ddd.CAP_SQUARE).triangulate().material(ddd.material(color='#ffffff'))
        sideline.extra['ddd:collider'] = False
        sideline.extra['ddd:shadows'] = False
        item.append(sideline)

    for side in (-1, 1):
        midline = ddd.line([[side * length * square_length_ratio, -width * sideline_pos_ratio * 0.5], [side * length * square_length_ratio, width * sideline_pos_ratio * 0.5]])
        midline = midline.buffer(line_width, cap_style=ddd.CAP_SQUARE).triangulate().material(ddd.material(color='#ffffff'))
        midline.extra['ddd:collider'] = False
        midline.extra['ddd:shadows'] = False
        item.append(midline)

    item = ddd.uv.map_cubic(item)

    net = tennis_net(width=width + 0.5, net_height_center=net_height_center, net_height_post=net_height_post)
    item.append(net)

    return item

def tennis_net(width, net_height_center=0.914, net_height_post=1.07):
    """
    Tennis net, on XY along the Y axis (since playground fields are seen x: length, y: width).
    """
    post1 = urban.post(net_height_post + 0.15).translate([0, -width * 0.5, 0]).material(ddd.mats.steel)
    post2 = urban.post(net_height_post + 0.15).translate([0, +width * 0.5, 0]).material(ddd.mats.steel)

    net = ddd.polygon([[-width * 0.5, 0], [width * 0.5, 0],
                       [width * 0.5, net_height_post], [0, net_height_center], [-width * 0.5, net_height_post]],
                      name="Tennis net")
    net = net.triangulate(twosided=True).material(ddd.mats.fence)
    net = net.rotate(ddd.ROT_FLOOR_TO_FRONT).rotate(ddd.ROT_TOP_CCW)
    net = ddd.uv.map_cubic(net)

    item = ddd.group3([post1, post2, net])
    return item


def basketball_hoop():
    """
    """

    ring_r = 0.45 / 2
    ring = ddd.disc(r=ring_r, name="Basketball hoop ring").outline().buffer(0.015).extrude(-0.03)
    ring = ring.material(ddd.mats.steel)
    #ring = ddd.uv.map_cubic(ring)

    board_w = 1.80
    board_h = 1.20
    board_ring_h = 0.30
    board_shape = ddd.rect([board_w, board_h], name="Basketball hoop board").recenter().extrude(-0.05)
    board_shape = board_shape.material(ddd.mats.plastic_transparent)
    #board_shape = ddd.uv.map_cubic(board_shape)
    board_shape = board_shape.rotate(ddd.ROT_FLOOR_TO_FRONT)
    board_shape = board_shape.translate([0, ring_r + 0.15, board_h / 2 - board_ring_h])

    board = ddd.group3([ring, board_shape], name="Basketball hoop")
    board = board.translate([0, 0, 3.05])

    pole = curvedpost(3.25, arm_length=1.5, corner_radius=0.4).rotate(ddd.ROT_TOP_CCW)
    pole = pole.material(ddd.mats.metal_paint_red)
    pole.prop_set('uv', None, True)
    pole = pole.translate([0, ring_r + 0.15 + 0.05 + 1.5, 0])

    hoop = ddd.group3([pole, board], name="Basketball hoop with pole")

    return hoop


def enforce_aspect_ratio(length, width, ratio):
    current_ratio = length / width
    if current_ratio > ratio:
        length = length / (current_ratio / ratio)
    else:
        width = width * (current_ratio / ratio)
    return length, width


def basketball_field_lines(length=28, width=15, line_width=0.075):
    """
    Note that an additional 2m around the field shall be granted.

    Playground fields are seen x: length, y: width
    """

    item = ddd.group3(name="Basketball lines")

    length = min(length, 28)
    width = min(width, 15)
    (length, width) = enforce_aspect_ratio(length, width, 28 / 15)

    rectangle = ddd.rect([-length / 2, -width / 2, length / 2, width / 2])
    coords = rectangle.geom.exterior.coords
    width_seg = ddd.line([coords[0], coords[1]])
    length_seg = ddd.line([coords[1], coords[2]])
    width2_seg = ddd.line([coords[2], coords[3]])
    length2_seg = ddd.line([coords[3], coords[0]])
    width_l = width_seg.geom.length
    length_l = length_seg.geom.length

    exterior = rectangle.outline().buffer(line_width, cap_style=ddd.CAP_SQUARE).triangulate().material(ddd.material(color='#ffffff'))
    exterior.name = "Bounds line"
    exterior.extra['ddd:collider'] = False
    exterior.extra['ddd:shadows'] = False

    midline_2d = ddd.line([length_seg.geom.centroid, length2_seg.geom.centroid], name="Mid line")
    midline = midline_2d.buffer(line_width, cap_style=ddd.CAP_SQUARE).triangulate().material(ddd.material(color='#ffffff'))
    midline.extra['ddd:collider'] = False
    midline.extra['ddd:shadows'] = False

    midcircle_radius_ratio = (3.60 / 2) / 15
    midcircle = ddd.disc(center=midline_2d.geom.centroid.coords, r=width_l * midcircle_radius_ratio).outline()
    midcircle = midcircle.buffer(line_width, cap_style=ddd.CAP_SQUARE).triangulate().material(ddd.material(color='#ffffff'))
    midcircle.extra['ddd:collider'] = False
    midcircle.extra['ddd:shadows'] = False

    item.append(exterior)
    item.append(midline)
    item.append(midcircle)

    centralline_2d = ddd.line([width_seg.geom.centroid, width2_seg.geom.centroid], name="Central line")

    # Sides
    for side in (-1, 1):
        if width > 12.0:
            smallarea = ddd.line([[0, -3], [5.80, -(3 - 1.80)]]).arc_to([5.80, 3 - 1.80], center=[5.80, 0], ccw=True).line_to([0, 3])
            #smallarea = smallarea.scale([smallarea_length_ratio * length, smallarea_width_ratio * width * 0.5])
            if side == 1: smallarea = smallarea.rotate(math.pi)
            smallarea = smallarea.translate([side * length_l / 2, 0])
            smallarea = smallarea.buffer(line_width, cap_style=ddd.CAP_SQUARE).triangulate().material(ddd.material(color='#ffffff'))
            smallarea.extra['ddd:collider'] = False
            smallarea.extra['ddd:shadows'] = False
            item.append(smallarea)

            smallline = ddd.line([[5.80, -(3 - 1.80)], [5.80, 3 - 1.80]])
            if side == 1: smallline = smallline.rotate(math.pi)
            smallline = smallline.translate([side * length_l / 2, 0])
            smallline = smallline.buffer(line_width, cap_style=ddd.CAP_SQUARE).triangulate().material(ddd.material(color='#ffffff'))
            smallline.extra['ddd:collider'] = False
            smallline.extra['ddd:shadows'] = False
            item.append(smallline)

        if width > 14.0:
            largearea = ddd.line([[0, -6.75], [1.575, -6.75]]).arc_to([1.575, 6.75], center=[1.575, 0], ccw=True).line_to([0, 6.75])
            if side == 1: largearea = largearea.rotate(math.pi)
            largearea = largearea.translate([side * length_l / 2, 0])
            largearea = largearea.buffer(line_width, cap_style=ddd.CAP_SQUARE).triangulate().material(ddd.material(color='#ffffff'))
            largearea.extra['ddd:collider'] = False
            largearea.extra['ddd:shadows'] = False
            item.append(largearea)

        goal = basketball_hoop().rotate(ddd.ROT_TOP_CCW)
        if side == 1: goal = goal.rotate(ddd.ROT_TOP_HALFTURN)
        goal = goal.translate([side * (length_l / 2 - 1.22 - 0.15), 0, 0])
        item.append(goal)


    item = ddd.uv.map_cubic(item)

    #hoop = basketball_hoop(width=width + 0.5, net_height_center=net_height_center, net_height_post=net_height_post)
    #item.append(hoop)

    return item


def golf_flag(pole_height=2.1336, flag_width=20*0.0254, flag_height=14*0.0254):
    """
    The USGA recommends a golf flagstick height should be at least 7 feet tall, measured from the bottom of the flagstick in the ground to the top of the stick.
    The standard 14”x20” golf flags are the official size used at golf courses.
    """
    flag = ddd.rect([0, 0, flag_width, flag_height])
    flag = flag.material(ddd.mats.red)
    flag = flag.triangulate(twosided=True)
    flag = flag.rotate(ddd.ROT_FLOOR_TO_FRONT)

    flag = flag.translate([0.025, 0, -0.02 - flag_height])

    item_post = post(height=pole_height, r=0.025, top=flag, mat_post=ddd.mats.metal_paint_yellow)

    return item_post
