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

    ddd.mats.spritesheet = ddd.material(name="SpriteSheet", color="#ffffff", #color="#e01010",
                                        texture_path="assets/spritesheets/ropecow/spritesheet_0.png",
                                        texture_normal_path="assets/spritesheets/ropecow/spritesheet_0_n.png",
                                        atlas_path="/home/jjmontes/git/NinjaCow/assets/spritesheets/ropecow/spritesheet_0.plist")

    ddd.mats.grass = ddd.material(name="Grass", color='#2dd355',
                                  texture_path="assets/scene/props/grass-texture-tiled.png",
                                  #alpha_cutoff=0.05,
                                  #extra={'ddd:collider': False, 'ddd:shadows': False, 'uv:scale': 0.05}
                                  )

    ddd.mats.grass_fore = ddd.material(name="GrassFore", color='#7f8d83',
                                       texture_path="assets/scene/props/grass-texture-tiled.png",
                                       #alpha_cutoff=0.05,
                                       extra={'godot:light_mask': 1 << 15}
                                       )

    ddd.mats.bricks = ddd.material(name="Bricks", color='#89796a',  # #d49156',
                                   texture_path="assets/textures/Bricks37_col.jpg",
                                   extra={'godot:texture_scale': [8.0, 8.0],
                                          'godot:texture_rotation': math.pi / 2.0,
                                          'godot:material:resource': 'res://assets/materials/textures/material-brick-normal.tres'
                                   })

    ddd.mats.paintedplaster = ddd.material(name="Bricks", color='#89796a',  # #d49156',
                                   texture_path="assets/textures/PaintedPlaster006_2K_Color.jpg",
                                   texture_normal_path="assets/textures/PaintedPlaster006_2K_Normal.jpg",
                                   extra={'godot:texture_scale': [8.0, 8.0],
                                          'godot:texture_rotation': math.pi / 2.0,
                                          'godot:material:resource': 'res://assets/materials/textures/material-brick-normal.tres'
                                   })


    ddd.mats.rock = ddd.material(name="Rock", color='#5f5f4d',
                                 texture_path="assets/textures/Rock22_col.jpg",
                                 #extra={'ddd:collider': False, 'ddd:shadows': False, 'uv:scale': 0.05}
                                 extra={#'godot:texture_scale': [8.0, 8.0],
                                        'godot:texture_rotation': math.pi / 2.0,
                                        'godot:material:resource': 'res://assets/materials/textures/material-rock-normal.tres'
                                 })
    ddd.mats.rock2 = ddd.material(name="Rock2(Background)(flat,grey,rock,smooth,wet)", color='#a0a0a0',
                                 texture_path="assets/textures/Rock020_2K_Color.jpg",
                                 texture_normal_path="assets/textures/Rock020_2K_Normal.jpg",
                                 #extra={'ddd:collider': False, 'ddd:shadows': False, 'uv:scale': 0.05}
                                 extra={'godot:texture_scale': [4.0, 4.0],
                                        'godot:texture_rotation': math.pi / 2.0,
                                        #'godot:material:resource': 'res://assets/materials/textures/material-rock-normal.tres'
                                 })

    ddd.mats.wood = ddd.material(name="Wood", color='#5f5f4d',
                                 texture_path="assets/textures/Planks16_col.jpg",
                                 #extra={'ddd:collider': False, 'ddd:shadows': False, 'uv:scale': 0.05}
                                 extra={'godot:texture_scale': [8.0, 8.0],
                                        'godot:texture_rotation': math.pi / 2.0,
                                        'godot:material:resource': 'res://assets/materials/textures/material-wood-normal.tres'
                                 })

    # Concrete with Moss
    ddd.mats.concrete_moss = ddd.material(name="ConcreteMoss", color='#b0b0b0',
                                 texture_path="assets/textures/Concrete026_2K_Color.jpg",
                                 texture_normal_path="assets/textures/Concrete026_2K_Normal.jpg",
                                 extra={'godot:texture_scale': [6.0, 6.0],
                                        'godot:texture_rotation': math.pi / 2.0,
                                        'godot:material:resource': 'res://assets/materials/textures/material-concrete_moss-normal.tres'
                                 })

    ddd.mats.tiles_checker = ddd.material(name="ConcreteMoss", color='#474747',
                                 texture_path="assets/textures/Tiles012_2K_Color.jpg",
                                 texture_normal_path="assets/textures/Tiles012_2K_Normal.jpg",
                                 extra={'godot:texture_scale': [12.0, 12.0],
                                        'godot:texture_rotation': math.pi / 2.0,
                                        #'godot:material:resource': 'res://assets/materials/textures/material-concrete_moss-normal.tres'
                                 })


    ddd.mats.obj_bush_def = ddd.material(name="Bush Def", texture_path="assets/scene/props/bush-def.png", texture_normal_path="assets/scene/props/bush-def_n.png" )
    ddd.mats.obj_bush_wide= ddd.material(name="Bush Wide", texture_path="assets/scene/props/bush-wide.png", texture_normal_path="assets/scene/props/bush-wide_n.png" )
    ddd.mats.obj_tree1 = ddd.material(name="Tree1", texture_path="assets/scene/props/tree1.png", texture_normal_path="assets/scene/props/tree1_n.png" )
    ddd.mats.obj_tree2 = ddd.material(name="Tree2", texture_path="assets/scene/props/tree2.png", texture_normal_path="assets/scene/props/tree2_n.png" )
    ddd.mats.obj_tree3 = ddd.material(name="Tree3", texture_path="assets/scene/props/tree3.png", texture_normal_path="assets/scene/props/tree3_n.png" )
    ddd.mats.obj_tree4 = ddd.material(name="Tree4", texture_path="assets/scene/props/tree4.png", texture_normal_path="assets/scene/props/tree4_n.png" )
    #ddd.mats.obj_tree_intro = ddd.material(name="TreeIntro", texture_path="assets/scene/truck/intro-hill-tree.png" )
    ddd.mats.obj_barsx4 = ddd.material(name="BarsX4", texture_path="assets/scene/props/bars-4-vert.png")
    ddd.mats.obj_pipes = ddd.material(name="Pipes", texture_path="assets/scene/props/pipes.png", texture_normal_path="assets/scene/props/pipes_n.png", extra={'godot:obj:scale': 0.25})
    ddd.mats.obj_plant = ddd.material(name="Plant", texture_path="assets/scene/props/plant.png" )

    ddd.mats.obj_plantsx1 = ddd.material(name="PlantsX1", texture_path="assets/scene/props/city-props-plantsx1.png", texture_normal_path="assets/scene/props/city-props-plantsx1_n.png", extra={'godot:obj:scale': 0.2} )
    ddd.mats.obj_plantsx3 = ddd.material(name="PlantsX3", texture_path="assets/scene/props/city-props-plantsx3.png", texture_normal_path="assets/scene/props/city-props-plantsx3_n.png", extra={'godot:obj:scale': 0.2} )
    ddd.mats.obj_flowerpot = ddd.material(name="FlowerPot", texture_path="assets/scene/props/city-props-flowerpot.png", texture_normal_path="assets/scene/props/city-props-flowerpot_n.png", extra={'godot:obj:scale': 0.25} )
    ddd.mats.obj_flowers1 = ddd.material(name="Flowers1", texture_path="assets/scene/props/city-props-flowers-1.png", texture_normal_path="assets/scene/props/city-props-flowers-1_n.png", extra={'godot:obj:scale': 0.25} )
    ddd.mats.obj_flowers2 = ddd.material(name="Flowers2", texture_path="assets/scene/props/city-props-flowers-2.png", texture_normal_path="assets/scene/props/city-props-flowers-2_n.png", extra={'godot:obj:scale': 0.25} )

    ddd.mats.obj_mailbox = ddd.material(name="Mailbox", texture_path="assets/scene/props/city-props-mailbox.png", texture_normal_path="assets/scene/props/city-props-mailbox_n.png", extra={'godot:obj:scale': 0.2} )
    ddd.mats.obj_bin = ddd.material(name="Bin", texture_path="assets/scene/props/cityprops-bin.png", texture_normal_path="assets/scene/props/cityprops-bin_n.png", extra={'godot:obj:scale': 0.25} )
    ddd.mats.obj_bench = ddd.material(name="Bench", texture_path="assets/scene/props/city-props-bench.png", texture_normal_path="assets/scene/props/city-props-bench_n.png", extra={'godot:obj:scale': 0.2} )


    ddd.mats.obj_grid_panel = ddd.material(name="Grid Panel", texture_path="assets/scene/props/gridpanel.png", texture_normal_path="assets/scene/props/gridpanel_n.png" )
    ddd.mats.obj_grid_panel_broken = ddd.material(name="Grid Panel Broken", texture_path="assets/scene/props/gridpanel_broken.png", texture_normal_path="assets/scene/props/gridpanel_broken_n.png" )

    ddd.mats.obj_lamp_fluor = ddd.material(name="Fluor Lamp", texture_path="assets/scene/props/lamp-office-fluor.png" )
    ddd.mats.obj_vines1 = ddd.material(name="Vines1", texture_path="assets/scene/props/vines1.png", texture_normal_path="assets/scene/props/vines1_n.png" )
    ddd.mats.obj_vines2 = ddd.material(name="Vines2", texture_path="assets/scene/props/vines2.png", texture_normal_path="assets/scene/props/vines2_n.png" )

    ddd.mats.obj_vines_h1 = ddd.material(name="Vines Hor1", texture_path="assets/scene/props/vines-h1.png", texture_normal_path="assets/scene/props/vines-h1_n.png" )
    ddd.mats.obj_vines_h2 = ddd.material(name="Vines Hor2", texture_path="assets/scene/props/vines-h2.png", texture_normal_path="assets/scene/props/vines-h2_n.png" )
    ddd.mats.obj_cables_h = ddd.material(name="Cables", texture_path="assets/scene/props/cables-h.png", texture_normal_path="assets/scene/props/cables-h_n.png" )
    ddd.mats.obj_beam1 = ddd.material(name="Beam1", texture_path="assets/scene/props/beam1.png", texture_normal_path="assets/scene/props/beam1_n.png" )
    ddd.mats.obj_beam2 = ddd.material(name="Beam2", texture_path="assets/scene/props/beam2.png", texture_normal_path="assets/scene/props/beam2_n.png" )
    ddd.mats.obj_cables2 = ddd.material(name="Cable2", texture_path="assets/scene/props/cables2.png", texture_normal_path="assets/scene/props/cables2_n.png" )

