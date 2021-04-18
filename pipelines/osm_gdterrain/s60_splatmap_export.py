# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020

import sys

import pyproj
import numpy as np

from ddd.ddd import ddd
from ddd.geo import terrain
from ddd.osm import osm
from ddd.osm.osm import project_coordinates
from ddd.pipeline.decorators import dddtask
from ddd.geo.elevation import ElevationModel
from PIL import Image
import math
from shapely.strtree import STRtree
import hashlib
import noise



# TODO: This is required by s70 descriptor export, but should not
@dddtask(order="59.89.+.10")
def osm_gdterrain_export_splatmap_init(root, pipeline, osm, logger):
    splatmap = ddd.group2(name="Splatmap")
    root.append(splatmap)

    # TODO: This is copied in osm_materials pipeline for export, keep here in a task as metadata (and add to descriptor)
    pipeline.data['splatmap:channels_materials'] = [
        ddd.mats.terrain,
        ddd.mats.dirt,
        ddd.mats.asphalt,
        ddd.mats.pavement,

        ddd.mats.sidewalk,
        ddd.mats.pathwalk,
        None,
        None,

        ddd.mats.grass,
        ddd.mats.garden,
        ddd.mats.park,
        ddd.mats.forest,

        ddd.mats.sand,
        ddd.mats.rock,
        None,
        None
        ]

    pipeline.data['splatmap:channels_num'] = 16

    pipeline.data['splatmap:channels:collapse_map'] = [
        [0, 2, 12],     # Terrain, asphalt, pavement, sand
        [1, 13],        # Paths, dirt, rock
        [8, 9, 10, 11], # Grass
        [3, 4, 5]       # Pedestrian, tiles
    ]

# 0 - Ground / Terrain
# 1 - Dirt (some wild pathways, terrain)
# 2 - Rock
# 3 - Forest/dense park terrain
# 4 - Sand
# 5 - UNUSED (?)
# 6 - Pedestrian area / castle interior / paved tiles
# 7 - Grass


# TODO: Doing this on stage 59 as buildings are deleted (keep 2D and 3D versions in the tree for late usage, also for terrain_export)
@dddtask(order="59.89.+.10", condition=True)
def osm_gdterrain_export_splatmap_condition(pipeline):
    return bool(pipeline.data.get('ddd:gdterrain:splatmap', False))



@dddtask(order="*.10.+")
def osm_gdterrain_export_splatmap_channels_all(root, pipeline, osm, logger):
    for i in range(pipeline.data['splatmap:channels_num']):
        mat = pipeline.data['splatmap:channels_materials'][i]
        if mat:
            objs = root.select('["ddd:material" = "%s"]' % mat.name)
        else:
            objs = ddd.group2()
        objs.name = 'Channel' + str(i)
        root.find("/Splatmap").append(objs)

'''
@dddtask()
def osm_gdterrain_export_splatmap_channel_0_terrain(root, pipeline, osm, logger):
    objs = root.select('["ddd:material" = "Ground"]')
    objs.name = 'Channel0'
    root.find("/Splatmap").append(objs)

@dddtask()
def osm_gdterrain_export_splatmap_channel_1_dirt(root, pipeline, osm, logger):
    objs = root.select('["ddd:material" = "Dirt"]')
    objs.name = 'Channel1'
    root.find("/Splatmap").append(objs)

@dddtask()
def osm_gdterrain_export_splatmap_channel_2_rock(root, pipeline, osm, logger):
    objs = root.select('["ddd:material" = "Rock"]')
    objs.name = 'Channel2'
    root.find("/Splatmap").append(objs)

@dddtask()
def osm_gdterrain_export_splatmap_channel_3_park(root, pipeline, osm, logger):
    objs = root.select('["ddd:material" ~ "Park|Forest"]')
    objs.name = 'Channel3'
    root.find("/Splatmap").append(objs)

@dddtask()
def osm_gdterrain_export_splatmap_channel_4_sand(root, pipeline, osm, logger):
    objs = root.select('["ddd:material" = "Sand"]')
    objs.name = 'Channel4'
    root.find("/Splatmap").append(objs)

@dddtask()
def osm_gdterrain_export_splatmap_channel_5(root, pipeline, osm, logger):
    objs = root.select('["ddd:material" = "NONE"]')
    objs.name = 'Channel5'
    root.find("/Splatmap").append(objs)

@dddtask()
def osm_gdterrain_export_splatmap_channel_6_pedestrian(root, pipeline, osm, logger):
    objs = root.select('["ddd:material" = "WayPedestrian"]')
    objs.name = 'Channel6'
    root.find("/Splatmap").append(objs)

@dddtask()
def osm_gdterrain_export_splatmap_channel_7_grass(root, pipeline, osm, logger):
    objs = root.select('["ddd:material" ~ "Grass|Garden"]')
    objs.name = 'Channel7'
    root.find("/Splatmap").append(objs)
'''


@dddtask()
def osm_gdterrain_export_splatmap(root, pipeline, osm, logger):

    ddd_bounds = osm.area_crop.bounds
    wgs84_min = terrain.transform_ddd_to_geo(osm.ddd_proj, ddd_bounds[:2])
    wgs84_max = terrain.transform_ddd_to_geo(osm.ddd_proj, ddd_bounds[2:])
    wgs84_bounds = wgs84_min + wgs84_max

    splatmap_size = pipeline.data.get('ddd:gdterrain:splatmap:size', 128)

    logger.info("Generating splatmap for area: ddd_bounds=%s, wgs84_bounds=%s, size=%s", ddd_bounds, wgs84_bounds, splatmap_size)

    splatmap = root.find("/Splatmap")

    # Sample each channel pixel, calculating the area covered by the surface
    splat_matrix = np.zeros([splatmap_size, splatmap_size, pipeline.data['splatmap:channels_num']])

    # Interpolate over DDD coordinates
    for chan_idx in range(pipeline.data['splatmap:channels_num']):

        channel_items = splatmap.find("/Channel%s" % chan_idx)
        logger.info("Calculating splatmap coverage for channel %s %s (%d items)" % (chan_idx,  pipeline.data['splatmap:channels_materials'][chan_idx], len(channel_items.children)))

        if len(channel_items.children) == 0:
            continue

        # Spatial index
        rtree = STRtree(splatmap.geom_recursive())

        # Channel union
        channel_items_union = None
        if chan_idx == 12:
            channel_items_union = channel_items.union()

        pixel_width_x = (ddd_bounds[2] - ddd_bounds[0]) / splatmap_size
        pixel_width_y = (ddd_bounds[3] - ddd_bounds[1]) / splatmap_size
        pixel_area = pixel_width_x * pixel_width_y
        points_x = np.linspace(ddd_bounds[0] - pixel_width_x * 0.5, ddd_bounds[2] + pixel_width_x * 0.5, splatmap_size + 1, endpoint=True)
        for xi, (x, xp) in enumerate(zip(points_x, points_x[1:])):
            points_y = list(reversed(np.linspace(ddd_bounds[1] - pixel_width_y * 0.5, ddd_bounds[3] + pixel_width_y * 0.5, splatmap_size + 1, endpoint=True)))
            for yi, (y, yp) in enumerate(zip(points_y, points_y[1:])):

                pixel_rect = ddd.rect([x, y, xp, yp])
                #pixel_area = pixel_rect.area()

                cand_items = rtree.query(pixel_rect.geom)
                items = [c._ddd_obj for c in cand_items if c.intersects(pixel_rect.geom) and c._ddd_obj in channel_items.children]

                pixel_items = ddd.group2(items).intersection(pixel_rect).union()
                items_area = pixel_items.area()

                cover_factor = items_area / pixel_area
                if (xi in (0, splatmap_size - 1)):
                    cover_factor *= 2
                if (yi in (0, splatmap_size - 1)):
                    cover_factor *= 2


                # Augmentation tests: sand (12)
                if chan_idx == 12:
                    if cover_factor < 0.99:
                        distance = channel_items_union.distance(ddd.point([x, y]))
                        distance_reach = 10.0
                        #extend_ratio *= noise.pnoise2(coords[0] * 0.1, coords[1] * 0.1, octaves=2, persistence=0.5, lacunarity=2, repeatx=1024, repeaty=1024, base=0)  # Randomize reach
                        aug_factor = max(0, 1.0 - distance / distance_reach)
                        aug_factor *= noise.pnoise2(x * 0.1, y * 0.1, octaves=3, persistence=0.5, lacunarity=2, repeatx=1024, repeaty=1024, base=0)  # Randomize reach
                        aug_factor = max(aug_factor, 0.0) * 0.55

                        cover_factor = max(aug_factor, cover_factor)
                        splat_matrix[yi, xi, :] -= cover_factor  # Reduce others


                # Augmentation tests: park (10)
                if chan_idx == 10 or chan_idx == 11:
                    if cover_factor > 0.95:
                        #extend_ratio *= noise.pnoise2(coords[0] * 0.1, coords[1] * 0.1, octaves=2, persistence=0.5, lacunarity=2, repeatx=1024, repeaty=1024, base=0)  # Randomize reach
                        reduce_factor = noise.pnoise2(x * 0.1, y * 0.1, octaves=3, persistence=0.5, lacunarity=2, repeatx=1024, repeaty=1024, base=0) * 0.5 + 0.5  # Randomize reach
                        reduce_factor = ddd.math.clamp((reduce_factor - 0.5) * 4.0, 0.0, 1.0)  #  * (0.15 if chan_idx == 10 else 0.3)
                        cover_factor = cover_factor - reduce_factor
                        splat_matrix[yi, xi, 0] += reduce_factor  # Increase terrain

                splat_matrix[yi, xi, chan_idx] = cover_factor


    # Clamp to 0..1
    splat_matrix = np.maximum(splat_matrix, 0.0)
    splat_matrix = np.minimum(splat_matrix, 1.0)

    # Sums that don't add up to at least this coverage will be filled with the default
    #default_min_threshold = 1.0
    #add_matrix = np.maximum(default_min_threshold - row_sums, 0)
    #topped_matrix = np.copy(splat_matrix)
    #topped_matrix[:,:,0] += add_matrix
    #row_sums = topped_matrix.sum(axis=2)

    # Normalize across all channels
    #row_sums = splat_matrix.sum(axis=2)
    #splat_matrix = splat_matrix[:,:] / row_sums[:, :, np.newaxis]

    # Clamp to 0..1
    #splat_matrix = np.maximum(np.copy(splat_matrix), 0.0)
    #splat_matrix = np.minimum(np.copy(splat_matrix), 1.0)

    # Splatmap smoothed pixels correction
    # TODO: If using 8 channels we may wish to do this before exporting those (but careful as many pixels may appear as 1.0 if area subtraction was incorrect during generation).
    splat_matrix_corrected = np.copy(splat_matrix)
    # Channels 1 and 2
    splat_matrix_corrected[:,:,1] = splat_matrix_corrected[:,:,1] * 4.0
    splat_matrix_corrected = np.minimum(splat_matrix_corrected, 1.0)

    splat_matrix = splat_matrix_corrected


    # Save
    #print(splat_matrix)

    #splat2_0_3_matrix = splat_matrix[:,:,:4] * 255
    #im = Image.fromarray(np.uint8(splat2_0_3_matrix), "RGBA")
    #im.save("/tmp/osm-splatmap-8chan-0_3-" + str(splatmap_size) + ".png", "PNG")

    #splat2_4_7_matrix = splat_matrix[:,:,4:] * 255
    #im = Image.fromarray(np.uint8(splat2_4_7_matrix), "RGBA")
    #im.save("/tmp/osm-splatmap-8chan-4_7-" + str(splatmap_size) + ".png", "PNG")

    # Collapse into N channels
    collapse_map = pipeline.data.get('splatmap:channels:collapse_map', None)
    if collapse_map:
        splat_matrix_collapsed = np.zeros([splatmap_size, splatmap_size, len(collapse_map)])
        for collapse_idx in range(len(collapse_map)):
            collapse_source_weight = (1.0 / len(collapse_map[collapse_idx]))
            for collapse_source in collapse_map[collapse_idx]:
                splat_matrix_collapsed[:,:,collapse_idx] += (splat_matrix[:,:,collapse_source])
    splat_matrix_collapsed = np.minimum(splat_matrix_collapsed, 1.0)

    #splat_matrix_collapsed = splat_matrix[:,:,0:4] + splat_matrix[:,:,4:8]
    #splat_matrix_collapsed = splat_matrix_collapsed * (0.5 * 255)

    #im = Image.fromarray(np.uint8(splat_matrix_collapsed), "RGBA")
    #im.save("/tmp/osm-splatmap-1chan-0_3.png", "PNG")
    #im.save(pipeline.data['filenamebase'] + ".splatmap-4chan-0_3-" + str(splatmap_size) + ".png", "PNG")

    im = Image.fromarray(np.uint8(splat_matrix_collapsed * 255), "RGBA")
    #im.save("/tmp/osm-splatmap-1chan-0_3-processed.png", "PNG")
    im.save(pipeline.data['filenamebase'] + ".splatmap-4chan-0_3-" + str(splatmap_size) + ".png", "PNG")


    # Collage into 1 splatmap atlas
    splatmap_atlas_rows = 2
    splatmap_atlas_cols = 2
    splat_matrix_atlas = np.zeros([splatmap_size * splatmap_atlas_rows, splatmap_size * splatmap_atlas_cols, 4])

    chan_idx = 0
    for row in range(splatmap_atlas_rows):
        for col in range(splatmap_atlas_cols):
            rowpos = row * splatmap_size
            colpos = col * splatmap_size
            splat_matrix_atlas[rowpos:rowpos+splatmap_size, colpos:colpos+splatmap_size, 0:4] = splat_matrix[:, :, chan_idx:chan_idx+4]
            chan_idx += 4

    im = Image.fromarray(np.uint8(splat_matrix_atlas * 255), "RGBA")
    #im.save("/tmp/osm-splatmap-1chan-0_3-processed.png", "PNG")
    im.save(pipeline.data['filenamebase'] + ".splatmap-" + str(pipeline.data['splatmap:channels_num']) +
            "chan-0_" + str(pipeline.data['splatmap:channels_num'] - 1) + "-" + str(splatmap_size) + ".png", "PNG")

    # Metadata (to be saved later to descriptor)
    pipeline.data['splatmap:channels'] = "TO-DO"

