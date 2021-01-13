# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020

import sys

import pyproj

from ddd.ddd import ddd
from ddd.pipeline.decorators import dddtask
import math



@dddtask(order="10")
def godot_init(pipeline, root):
    """
    Pipeline initialization (variables, etc).
    """
    pass

@dddtask()
def godot_materials(pipeline, root):

    pipeline.data['spritesheet'] = ddd.material(name="SpriteSheet", color="#ffffff", #color="#e01010",
                                                texture_path="res://assets/spritesheets/ropecow/spritesheet_0.png",
                                                texture_normal_path="res://assets/spritesheets/ropecow/spritesheet_0_n.png",
                                                atlas_path="/home/jjmontes/git/NinjaCow/assets/spritesheets/ropecow/spritesheet_0.plist")

    ddd.mats.grass = ddd.material(name="Grass", color='#2dd355',
                                  texture_path="res://assets/scene/props/grass-texture-tiled.png",
                                  #alpha_cutoff=0.05,
                                  #extra={'ddd:collider': False, 'ddd:shadows': False, 'uv:scale': 0.05}
                                  )

    ddd.mats.grass_fore = ddd.material(name="GrassFore", color='#1dc345',
                                       texture_path="res://assets/scene/props/grass-texture-tiled.png",
                                       #alpha_cutoff=0.05,
                                       extra={'godot:light_mask': 1 << 15}
                                       )

    ddd.mats.bricks = ddd.material(name="Brikcs", color='#89796a',  # #d49156',
                                   texture_path="res://assets/textures/Bricks37_col.jpg",
                                   extra={'godot:texture_scale': [8.0, 8.0],
                                          'godot:texture_rotation': math.pi / 2.0}
                                   )

    ddd.mats.rock = ddd.material(name="Stone", color='#5f5f4d',
                                 texture_path="res://assets/textures/Rock22_col.jpg",
                                 #extra={'ddd:collider': False, 'ddd:shadows': False, 'uv:scale': 0.05}
                                 extra={#'godot:texture_scale': [8.0, 8.0],
                                        'godot:texture_rotation': math.pi / 2.0}
                                 )

