# DDD(123) - Library for procedural generation of 2D and 3D geometries and scenes
# Copyright (C) 2021 Jose Juan Montes
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import logging
import math
import random
import numpy as np

from ddd.ddd import ddd
from ddd.core.exception import DDDException


# Get instance of logger for this module
logger = logging.getLogger(__name__)


"""
Rooftop-specific items (chimneys, antennas, ventilation, A/C, skylights)
"""

# TODO: Use items and item-builders to create various chimneys (e.g. adding caps)

def chimney_round_turbine(obj, height=1.0, radius=0.1):
    """
    Creates a modern chimeney, thin, tall, typically metallic and with a rotatin fan/turbine on top.
    """
    pass

def chimney_shape(obj, height=1.0, thickness=None):
    """
    Creates a chimeney. Uses the given shape.
    """
    if thickness:
        obj = obj.subtract(obj.buffer(-thickness))
    obj = obj.extrude(height, base=False)
    obj = obj.material(ddd.mats.bricks)
    obj = ddd.uv.map_cubic(obj)
    return obj

def chimney_open_round(radius=0.2, height=0.8, thickness=0.075):
    obj = ddd.disc(r=radius, resolution=3, name="ChimneyCO")
    obj = chimney_shape(obj, height, thickness)
    return obj

def chimney_closed_round(radius=0.2, height=0.8):
    obj = ddd.disc(r=radius, resolution=3, name="ChimneyCO")
    obj = chimney_shape(obj, height)
    return obj

def chimney_open_rect(height=1.2, width=0.5, length=0.4, thickness=0.075):
    obj = ddd.rect([width, length], name="ChimneyCR").recenter()
    obj = chimney_shape(obj, height, thickness)
    return obj

def chimney_closed_rect(height=1.2, width=0.5, length=0.4):
    obj = ddd.rect([width, length], name="ChimneyCR").recenter()
    obj = chimney_shape(obj, height)
    return obj


ROOF_ANTENA_TV_FRONT = [(0.1, 1.0), (0.2, None), (0.3, 0.85), (0.6, 0.5), (0.8, 0.5), (1.0, 0.5) ]  # ratio: 1.25/0.43
ROOF_ANTENA_TV_MID = [(0.0, 0.9), (0.3, 1.0), (0.4, None), (0.5, 0.5), (0.7, 0.3), (0.9, 0.2), (0.9, 0.2), (1.0, 0.2)]  # ratio? 1.25/0.8

def roof_antenna_tv(length=1.25, width=0.43, thick_main=0.05, thick_sec=0.02, segments=None):
    """
    A UFH/VFH outdoor antenna piece (without mast).

    Segments are both normalized along length and width.

    Lying on XY, pointing towards -Y, centered on its mount point.
    """

    if segments is None:
        segments = ROOF_ANTENA_TV_FRONT
    
    frontpole = ddd.rect([thick_main, length]).translate([-thick_main * 0.5, -length])
    frontpole = frontpole.extrude(thick_main)
    frontpole = frontpole.material(ddd.mats.steel)

    antenna = ddd.group([frontpole], "AntennaTV")

    mount_point_d = None
    for sd in segments:
        
        if sd[1] is None:
            mount_point_d = sd[0]
            continue
        
        segmentpole = ddd.rect([width * sd[1], thick_sec]).recenter()
        segmentpole = segmentpole.extrude(thick_sec)
        segmentpole = segmentpole.material(ddd.mats.steel)
        segmentpole = segmentpole.translate([0, -length * sd[0], thick_main])
        antenna.append(segmentpole)

    antenna = antenna.translate([0, length * mount_point_d, 0])
    
    antenna = antenna.combine()
    antenna = ddd.uv.map_cubic(antenna)
    
    return antenna


def antenna_mast():

    mast_radius = 0.03 
    mast = ddd.cylinder(height=2.5, r=mast_radius, center=False, resolution=2)
    mast = mast.material(ddd.mats.steel)
    mast = ddd.uv.map_cylindrical(mast)

    antenna = roof_antenna_tv()
    antenna.transform.translate([-mast_radius, 0, 2.3])

    obj = ddd.group([mast, antenna], "Antenna Mast")

    return obj


def satellite_dish(radius=0.5, height=0.16, dish_resolution_arc=3, dish_resolution_r=4):
    """
    Dish is presented looking towards -Y, centered on its central base point.
    """

    intervals = np.linspace(0.05, 1, dish_resolution_r, endpoint=False)
    interval_scales = [(p, (p ** 2) * height) for p in intervals]
    
    disc_shape = ddd.disc(r=radius, resolution=dish_resolution_arc, name="Sat Dish")
    disc = disc_shape.buffer(0.005).extrude_step(disc_shape, 0.02, method=ddd.EXTRUSION_METHOD_SUBTRACT, base=False)
    prev_h = height
    for p in list(reversed(interval_scales)):
        disc = disc.extrude_step(disc_shape.scale([p[0], p[0]]), (p[1] - prev_h), method=ddd.EXTRUSION_METHOD_SUBTRACT, base=False)
        prev_h = p[1]
    
    disc = disc.translate([0, 0, height - 0.02])
    
    disc = disc.material(ddd.mats.metal_paint_white)
    disc = disc.merge_vertices().smooth(ddd.PI_OVER_8)
    disc = disc.twosided()
    disc = ddd.uv.map_cubic(disc)

    disc= disc.rotate(ddd.ROT_FLOOR_TO_FRONT)

    return disc


def satellite_dish_antenna_simple(length=0.5):
    """
    Presented growing towards -Y, centered on its central base point.
    """

    pole = ddd.box([0, 0, 0, 0.04, -length, 0.02]).translate([-0.02, 0, -0.01])
    pole = ddd.uv.map_cubic(pole)
    pole = pole.material(ddd.mats.metal)
    
    feed_horn_shape = ddd.disc(r=0.02, resolution=2)
    feed_horn = feed_horn_shape.extrude_step(feed_horn_shape.buffer(0.02), 0.06)
    #feed_horn = feed_horn.rotate(ddd.ROT_FLOOR_TO_BACK)
    feed_horn = feed_horn.material(ddd.mats.plastic_black)
    feed_horn = feed_horn.rotate([-ddd.PI * 0.15, 0, 0])
    feed_horn = feed_horn.translate([0, -length, 0])

    dish_antenna = ddd.group([pole, feed_horn], "Sat Dish Antenna")
    return dish_antenna
    

def roof_antena_satellite_dish(radius=0.5, height=0.16):
    dish = satellite_dish(radius=radius, height=height)
    antenna = satellite_dish_antenna_simple()
    antenna.transform.translate([0, -height, -(radius - 0.02)])
    antenna.transform.rotate([-ddd.PI * 0.15, 0, 0])
    obj = ddd.group([dish, antenna], "Sat Dish")
    return obj


def roof_antenna_radio_amateur():
    pass

def roof_antenna_cell_bts():
    pass

def roof_antenna_radio_station():
    pass




def ac_unit():
    pass


def roof_skylight():
    pass

