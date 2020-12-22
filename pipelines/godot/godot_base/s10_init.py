# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020

import sys

import pyproj

from ddd.ddd import ddd
from ddd.pipeline.decorators import dddtask



@dddtask(order="10")
def godot_init(pipeline, root):
    """
    Pipeline initialization (variables, etc).
    """
    pass

@dddtask()
def godot_materials(pipeline, root):

    pipeline.data['spritesheet'] = ddd.material(name="SpriteSheet", color="#ffffff", #color="#e01010",
                                                texture_path="spritesheets/sprites_0.png",
                                                atlas_path="spritesheets/sprites_0.plist")




