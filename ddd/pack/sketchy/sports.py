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


def football_field_lines(area, line_width=0.10):
    # TODO: Receive size or aspect ratio and create centered so it's more reusable, and we can enforce size.

    item = ddd.group3(name="Football lines")

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
    width2_seg = ddd.line([coords[2], coords[3]])
    length2_seg = ddd.line([coords[3], coords[0]])

    width_l = width_seg.geom.length
    length_l = length_seg.geom.length

    exterior = rectangle.outline().buffer(line_width, cap_style=ddd.CAP_SQUARE).triangulate().material(ddd.material(color='#ffffff'))
    exterior.name = "Bounds line"
    exterior.extra['ddd:collider'] = False
    exterior.extra['ddd:shadows'] = False

    midline = ddd.line([length_seg.geom.centroid, length2_seg.geom.centroid], name="Mid line")
    midline = midline.buffer(line_width, cap_style=ddd.CAP_SQUARE).triangulate().material(ddd.material(color='#ffffff'))
    midline.extra['ddd:collider'] = False
    midline.extra['ddd:shadows'] = False

    #midcircle = ddd.disc().subtract(ddd.disc())

    item.append(exterior)
    item.append(midline)

    item = ddd.uv.map_cubic(item)

    return item

def football_goal11():
    return football_goal(width=7.2, height=2.44)

def football_goal9():
    return football_goal(width=4.88, height=1.83)

def football_goal7():
    return football_goal(width=3.66, height=1.83)

def football_goal(width=4.88, height=1.83, thick=0.10):
    line = ddd.point().line_to([0, height]).line_to([width, height]).line_to([width, 0]).translate([-width/2, 0])
    line = line.extrude(-thick)
    line = line.rotate([math.pi / 2.0, 0, 0]).material(ddd.mats.metal_paint_green)
    return line

