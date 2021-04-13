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



# TODO: Doing this on stage 59 as buildings are deleted (keep 2D and 3D versions in the tree for late usage, also for terrain_export)

@dddtask(order="59.89.+.10", condition=True)
def osm_gdterrain_export_splatmap_condition(pipeline):
    return bool(pipeline.data.get('ddd:gdterrain:splatmap', False))


@dddtask(order="*.10.+")
def osm_gdterrain_export_splatmap_init(root, pipeline, osm, logger):
    splatmap = ddd.group2(name="Splatmap")
    root.append(splatmap)

# Layering and ordering
# Output values are normalized to to sum 1 across all channels
# If only 4 channels are used, channels are collapsed (0+4, 1+5, 2+6, 3+7)

# 0 - Ground / Terrain
# 1 - Dirt (some wild pathways, terrain)
# 2 - Rock
# 3 - Forest/dense park terrain

# 4 - Sand
# 5 - UNUSED (?)
# 6 - Pedestrian area / castle interior / paved tiles
# 7 - Grass

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


@dddtask()
def osm_gdterrain_export_splatmap(root, pipeline, osm, logger):

    ddd_bounds = osm.area_crop.bounds
    wgs84_min = terrain.transform_ddd_to_geo(osm.ddd_proj, ddd_bounds[:2])
    wgs84_max = terrain.transform_ddd_to_geo(osm.ddd_proj, ddd_bounds[2:])
    wgs84_bounds = wgs84_min + wgs84_max

    splatmap_size = 256
    logger.info("Generating splatmap for area: ddd_bounds=%s, wgs84_bounds=%s, size=%s", ddd_bounds, wgs84_bounds, splatmap_size)

    splatmap = root.find("/Splatmap")

    # Sample each channel pixel, calculating the area covered by the surface
    splat_matrix = np.zeros([splatmap_size, splatmap_size, 8])

    # Interpolate over DDD coordinates
    for chan_idx in range(8):

        channel_items = splatmap.find("/Channel%s" % chan_idx)
        logger.info("Calculating splatmap coverage for channel: %s (%d items)" % (chan_idx, len(channel_items.children)))

        # Spatial index
        rtree = STRtree(splatmap.geom_recursive())

        points_x = np.linspace(ddd_bounds[0], ddd_bounds[2], splatmap_size + 1, endpoint=True)
        for xi, (x, xp) in enumerate(zip(points_x, points_x[1:])):
            points_y = list(reversed(np.linspace(ddd_bounds[1], ddd_bounds[3], splatmap_size + 1, endpoint=True)))
            for yi, (y, yp) in enumerate(zip(points_y, points_y[1:])):

                pixel_rect = ddd.rect([x, y, xp, yp])
                pixel_area = pixel_rect.area()

                cand_items = rtree.query(pixel_rect.geom)
                items = [c._ddd_obj for c in cand_items if c.intersects(pixel_rect.geom) and c._ddd_obj in channel_items.children]

                pixel_items = ddd.group2(items).intersection(pixel_rect).union()
                items_area = pixel_items.area()

                cover_factor = items_area / pixel_area

                splat_matrix[yi, xi, chan_idx] = cover_factor


    '''
    # Normalize across 8 channels and set a default for channel 0
    row_sums = splat_matrix.sum(axis=2)

    # Sums that don't add up to at least this coverage will be filled with the default
    default_min_threshold = 1.0

    add_matrix = np.maximum(default_min_threshold - row_sums, 0)

    topped_matrix = np.copy(splat_matrix)
    topped_matrix[:,:,0] += add_matrix

    row_sums = topped_matrix.sum(axis=2)
    splat_matrix = topped_matrix[:,:] / row_sums[:, :, np.newaxis]
    '''


    # Save
    #print(splat_matrix)

    #splat2_0_3_matrix = splat_matrix[:,:,:4] * 255
    #im = Image.fromarray(np.uint8(splat2_0_3_matrix), "RGBA")
    #im.save("/tmp/osm-splatmap-8chan-0_3-" + str(splatmap_size) + ".png", "PNG")

    #splat2_4_7_matrix = splat_matrix[:,:,4:] * 255
    #im = Image.fromarray(np.uint8(splat2_4_7_matrix), "RGBA")
    #im.save("/tmp/osm-splatmap-8chan-4_7-" + str(splatmap_size) + ".png", "PNG")

    # Collapse into 1 splatmap
    splat_matrix_collapsed = splat_matrix[:,:,:4] + splat_matrix[:,:,4:]
    splat_matrix_collapsed = splat_matrix_collapsed * (0.5 * 255)


    #im = Image.fromarray(np.uint8(splat_matrix_collapsed), "RGBA")
    #im.save("/tmp/osm-splatmap-1chan-0_3.png", "PNG")
    #im.save(pipeline.data['filenamebase'] + ".splatmap-4chan-0_3-" + str(splatmap_size) + ".png", "PNG")

    # Splatmap smoothed pixels correction
    # TODO: If using 8 channels we may wish to do this before exporting those (but careful as many pixels may appear as 1.0 if area subtraction was incorrect during generation).
    splat_matrix_corrected = np.copy(splat_matrix_collapsed)
    # Channels 1 and 2
    splat_matrix_corrected[:,:,0] = splat_matrix_corrected[:,:,0] * 2.0
    splat_matrix_corrected[:,:,1] = splat_matrix_corrected[:,:,1] * 255.0 / 50.0
    splat_matrix_corrected[:,:,2] = splat_matrix_corrected[:,:,2] * 255.0 / 50.0
    splat_matrix_corrected[:,:,3] = splat_matrix_corrected[:,:,3] * 2.0
    splat_matrix_corrected = np.minimum(splat_matrix_corrected, 255)

    im = Image.fromarray(np.uint8(splat_matrix_corrected), "RGBA")
    #im.save("/tmp/osm-splatmap-1chan-0_3-processed.png", "PNG")
    im.save(pipeline.data['filenamebase'] + ".splatmap-4chan-0_3-" + str(splatmap_size) + ".png", "PNG")

    # Metadata (to be saved later to descriptor)
    pipeline.data['splatmap:channels'] = None

