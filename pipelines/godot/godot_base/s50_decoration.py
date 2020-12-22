# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020

from ddd.ddd import ddd, DDDObject2
from ddd.pipeline.decorators import dddtask
from ddd.core.exception import DDDException
import random
import sys
import math
from shapely.ops import linemerge
from ddd.ops import filters, uvmapping
from ddd.materials import atlas
from ddd.materials.atlas import TextureAtlasUtils

sprites_bg = ["outlineDisc", "outlineDisc_alt", "outlineCrystal", "outlineGem", "outlineJewel",
              "outlinePuzzle", ]

sprites_solid = ["blockBrown", "blockBrown_broken",
                 "blockGreen",
                 "blockGrey", "blockGrey_broken",
                 "blockRed", "blockRed_puzzle",
                 ]

sprites_fence = ["fence", "fenceBroken", "fenceLeft", "fenceMid", "fenceRight", "fenceOpen"]
sprites_ladder = ["ladderNarrow_mid", "ladderNarrow_top",
                  "ladderWide_mid", "ladderWide_top",]

sprites_flags = ["flagGreen_down", "flagGreen_up",
                 "flagRed_down", "flagRed_up"]
sprites_plants = ["plantBlue_1", "plantBlue_2", "plantBlue_3", "plantBlue_4", "plantBlue_5", "plantBlue_6",
                  "plantDark_1", "plantDark_2", "plantDark_3", "plantDark_4", "plantDark_5", "plantDark_6",
                  "plantGreen_1", "plantGreen_2", "plantGreen_3", "plantGreen_4", "plantGreen_5", "plantGreen_6",
                  "plantRed_1", "plantRed_2", "plantRed_3", "plantRed_4", "plantRed_5", "plantRed_6",]
'''
sprites_plants_bottom = ["plantBottom_1", "plantBottom_2"]
sprites_plants_leaves = ["plantLeaves_1", "plantLeaves_2"]
sprites_plants_stem = ["plantLeaves_1", "plantLeaves_2"]
sprites_plants_thorns = ["plantLeaves_1", "plantLeaves_2"]
sprites_plants_top = ["plantLeaves_1", "plantLeaves_2"]
'''

sprites_vine = ["vine", "vine_bottom", "vine_bottomAlt"]

sprites_signs = ["signArrow_BL", "signArrow_BR", "signArrow_TL", "signArrow_TR",
                 "signArrow_down", "signArrow_up", "signArrow_left", "signArrow_right",
                 "signLarge", "signpost", "signSmall", ]

sprites_spikes = ["spikesHigh", "spikesLow", ]


@dddtask(path="/Features/*", select='[ddd:polygon:type="hollow"]', log=True)
def room_decoration(root, pipeline, obj):

    points = obj.random_points(5)
    for p in points:
        pos = [p[0], p[1]]
        sprite_key = random.choice(sprites_bg + sprites_solid)
        item = TextureAtlasUtils().create_sprite_rect(pipeline.data['spritesheet'], sprite_key + ".png")
        #item.extra['godot:instance'] = "res://scenes/items/ItemGeneric.tscn"
        item = item.material(pipeline.data['spritesheet'])
        item = item.scale([64.0, 64.0])

        rndscale = random.uniform(0.7, 3)
        item = item.scale([rndscale, rndscale])

        item = item.translate(pos)
        item.extra['ddd:z_index'] = -2

        root.find("/Rooms/").append(item)


@dddtask(path="/Rooms/*", select='[ceiling_line]', log=True)
def ceiling_lamps(root, pipeline, obj):

    line = obj.extra['ceiling_line']
    l = line.geom.length
    d = l / 2
    p, segment_idx, segment_coords_a, segment_coords_b = line.interpolate_segment(d)

    pos = [p[0], p[1] + 20.0]
    item = ddd.point(pos, "Light")
    item = ddd.snap.project(item, obj)
    item.extra['ddd:angle'] = item.extra['ddd:angle'] + math.pi / 2
    item.extra['godot:instance'] = "res://scenes/items/lamps/LampGrid.tscn"
    item.geom.coords = [p[0], p[1]]
    root.find("/Items").append(item)


@dddtask(path="/Rooms/*", select='[floor_line]', log=True)
def floor_decoration_items(root, pipeline, obj):


    line = obj.extra['floor_line']
    l = line.geom.length
    d = l / 2
    p, segment_idx, segment_coords_a, segment_coords_b = line.interpolate_segment(d)

    pos = [p[0], p[1] - 20.0]

    sprites_floor = sprites_flags + sprites_plants + sprites_signs
    sprite_key = random.choice(sprites_floor)

    item = TextureAtlasUtils().create_sprite_rect(pipeline.data['spritesheet'], sprite_key + ".png")
    item = item.material(pipeline.data['spritesheet'])
    item = item.scale([32.0, -32.0])

    rndscale = random.uniform(0.8, 1.3)
    item = item.scale([rndscale, rndscale])

    item = item.translate(pos)
    item.extra['ddd:z_index'] = -2

    root.find("/Rooms/").append(item)


    '''
    item = ddd.point(pos, "Light")
    item = ddd.snap.project(item, obj)
    item.extra['ddd:angle'] = item.extra['ddd:angle'] + math.pi / 2
    item.extra['godot:instance'] = "res://scenes/items/lamps/LampGrid.tscn"
    item.geom.coords = [p[0], p[1]]
    '''



