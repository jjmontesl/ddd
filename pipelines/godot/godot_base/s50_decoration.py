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
                 "blockGreen", "blockGreen_puzzle",
                 "blockGrey", "blockGrey_broken",
                 "blockRed", "blockRed_puzzle",
                 ]

sprites_bg_rc = ["outlineCowbell", "outlineCowbell_solid",
                 "outlineHappyMilk", "outlineHappyMilk_solid"]

sprites_solid_rc = ["blockBrown_cowbell", "blockBrown_happymilk",
                    "blockGreen_cowbell", "blockGreen_happymilk",
                    "blockGrey_cowbell", "blockGrey_happymilk", "blockGrey_broken_happymilk",
                    "blockRed_cowbell", "blockRed_happymilk",]


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


#@dddtask(path="/Features/*", select='[ddd:polygon:type="hollow"]', log=True)
@dddtask(path="/Features", log=True)
def room_decoration(root, pipeline, obj):

    obj = pipeline.data['rooms:background_union']

    points = obj.random_points(50)
    for p in points:
        pos = [p[0], p[1]]
        sprite_key = random.choice(sprites_bg + sprites_solid + sprites_bg_rc + sprites_solid_rc)
        item = TextureAtlasUtils().create_sprite_rect(pipeline.data['spritesheet'], sprite_key + ".png")
        #item.extra['godot:instance'] = "res://scenes/items/ItemGeneric.tscn"
        item = item.material(pipeline.data['spritesheet'])

        # TODO: Scale to sprite dimensions
        item = item.scale([64.0, 64.0])

        rndscale = random.uniform(0.7, 3)
        item.extra['godot:scale'] = [rndscale, rndscale]
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

    pos = [p[0], p[1] - 20.0]
    item = ddd.point(pos, "Light")
    item = ddd.snap.project(item, line)
    item.extra['ddd:angle'] = item.extra['ddd:angle'] - math.pi / 2.0
    item.extra['godot:instance'] = "res://scenes/items/lamps/LampGrid.tscn"
    #item.geom.coords = [p[0], p[1]]
    root.find("/Items").append(item)


@dddtask(path="/Rooms/*", select='[ceiling_line]', log=True)
def ceiling_decoration_items(root, pipeline, obj):

    line = obj.extra['ceiling_line']
    l = line.geom.length

    for d in (l/3, 2*l/3):
        p, segment_idx, segment_coords_a, segment_coords_b = line.interpolate_segment(d)

        pos = [p[0], p[1] - 20.0]
        rndscale = random.uniform(1.0, 2.5)

        itempos = ddd.point(pos, "Ceiling Deco")
        itempos = ddd.snap.project(itempos, line, 16.0 * rndscale)

        sprites_ceiling = sprites_flags + sprites_plants + sprites_vine + sprites_vine
        sprite_key = random.choice(sprites_ceiling)

        item = TextureAtlasUtils().create_sprite_rect(pipeline.data['spritesheet'], sprite_key + ".png")
        item = item.material(pipeline.data['spritesheet'])

        # TODO: Scale to sprite dimensions
        item = item.scale([32.0, -32.0])

        item.extra['godot:scale'] = [1.0, rndscale]
        item = item.scale([rndscale, rndscale])

        item = item.translate(itempos.centroid())
        item.extra['ddd:angle'] = itempos.extra['ddd:angle'] + math.pi / 2.0
        item.extra['ddd:z_index'] = -2

        root.find("/Rooms/").append(item)

@dddtask(path="/Rooms/*", select='[ceiling_line][geom:type="Polygon"]', log=True)
def ceiling_line_remove(root, pipeline, obj):
    return False


@dddtask(path="/Rooms/*", select='[floor_line]', log=True)
def floor_decoration_items(root, pipeline, obj):

    line = obj.extra['floor_line']
    l = line.geom.length

    for d in (l/3, 2*l/3):
        p, segment_idx, segment_coords_a, segment_coords_b = line.interpolate_segment(d)

        pos = [p[0], p[1] - 20.0]
        rndscale = random.uniform(0.8, 1.3)

        itempos = ddd.point(pos, "Floor Deco")
        itempos = ddd.snap.project(itempos, line, -16.0 * rndscale)

        sprites_floor = sprites_flags + sprites_plants + sprites_signs
        sprite_key = random.choice(sprites_floor)

        item = TextureAtlasUtils().create_sprite_rect(pipeline.data['spritesheet'], sprite_key + ".png")
        item = item.material(pipeline.data['spritesheet'])

        # TODO: Scale to sprite dimensions
        item = item.scale([32.0, -32.0])

        item.extra['godot:scale'] = [rndscale, rndscale]
        item = item.scale([rndscale, rndscale])

        item = item.translate(itempos.centroid())
        item.extra['ddd:angle'] = itempos.extra['ddd:angle'] - math.pi / 2.0
        item.extra['ddd:z_index'] = -2

        root.find("/Rooms/").append(item)


@dddtask(path="/Rooms/*", log=True)
def outside_decoration_remove(root, pipeline, obj):
    if not obj.buffer(2.0).intersects(pipeline.data['rooms:background_union']):
        return False

@dddtask(path="/Rooms/Floors/*", log=True)
def outside_floors_remove(root, pipeline, obj):
    if not obj.buffer(2.0).intersects(pipeline.data['rooms:background_union']):
        return False

@dddtask(path="/Items/*", log=True)
def outside_items_remove(root, pipeline, obj):
    if not obj.buffer(2.0).intersects(pipeline.data['rooms:background_union']):
        return False

    '''
    item = ddd.point(pos, "Light")
    item = ddd.snap.project(item, obj)
    item.extra['ddd:angle'] = item.extra['ddd:angle'] + math.pi / 2
    item.extra['godot:instance'] = "res://scenes/items/lamps/LampGrid.tscn"
    item.geom.coords = [p[0], p[1]]
    '''



