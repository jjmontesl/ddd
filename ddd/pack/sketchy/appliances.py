# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging

from ddd.ddd import ddd
from trimesh import transformations
from ddd.math.vector3 import Vector3

from ddd.ops.layout import DDDLayout, VerticalDDDLayout
from ddd.pack.shapes.holes import hole_broken


# Get instance of logger for this module
logger = logging.getLogger(__name__)


def clock_wall_round(radius=0.24, depth=0.02):
    """
    Clock is upright, centered on XZ, and facing -Y.
    """
    
    resolution = 4
    
    item = ddd.disc(r=radius, resolution=resolution, name="Clock")
    
    if depth:
        #item = item.extrude_step(item, disc_depth, base=False)
        item = item.extrude(depth, base=False)
    else:
        item.set('_extruded_shape', item.copy())
        item = item.triangulate()
    

    angle_second = 0
    angle_minute = - 5 * ddd.PI_OVER_4
    angle_hour = - 2 *  ddd.PI_OVER_4

    item = item.material(ddd.mats.plastic_white)
    #item = item.clean()
    #item = item.smooth(0)
    item = ddd.uv.map_cubic(item, split=True)  # , scale=[1 / width, 1 / height])

    for handle_idx, handle in enumerate((
        ('Second', radius * 0.9, 0.01, angle_second),
        ('Minute', radius * 0.75, 0.02, angle_minute),
        ('Hour', radius * 0.6, 0.02, angle_hour)) ):
        
        handle_item = ddd.rect([[-handle[2] / 2, -handle[2]], [handle[2] / 2, handle[1]]], name="ClockHandle " + handle[0])
        handle_item = handle_item.triangulate()  #.twosided()
        handle_item = handle_item.material(ddd.mats.plastic_black)
        handle_item = handle_item.rotate([0, 0, handle[3]])
        handle_item = handle_item.translate([0, 0, depth + 0.001 * (handle_idx + 1.5)])
        
        item = item.append(handle_item)

    item = item.rotate(ddd.ROT_FLOOR_TO_FRONT)
    
    return item

def clock_wall_round_framed(radius=0.24, frame_width=0.03):
    """
    """
    
    frame_depth = 0.03
    clock_depth = 0.02

    clock = clock_wall_round(radius=radius - frame_width, depth=0).translate([0, -clock_depth, 0])
    
    clock_shape = clock.get('_extruded_shape')
    #clock = ddd.meshops.remove_faces_pointing(clock, ddd.VECTOR_BACKWARD, 1.0)

    resolution = 4
    clock_frame = ddd.disc(r=radius, resolution=resolution, name="ClockFrame")
    clock_frame = clock_frame.subtract(clock_shape)
    #clock_frame = clock_frame.extrude_step(clock_frame, frame_depth, base=False)
    clock_frame = clock_frame.extrude(frame_depth, base=False)
    clock_frame = clock_frame.material(ddd.mats.plastic_black)
    clock_frame = ddd.uv.map_cubic(clock_frame)  # , scale=[1 / width, 1 / height])

    clock_frame = clock_frame.rotate(ddd.ROT_FLOOR_TO_FRONT)
    clock_frame.append(clock)
    
    return clock_frame


"""
TODO:

- Microwave Oven
- Fridge (solid or hollow)

- TV Flat
- TV CRT 
- TV Retro (+ w/base)
- Radio Analog 80s
- Radio Analog 90s

- Phone Dial Classic
- Phone Wireless Modern (wall + w/base for desktop)

- PC
- Laptop

- Tablet
- Cellphone Smartphone
- Cellphone Analog (w antenna)


"""