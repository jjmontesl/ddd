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
import random
from ddd.util.common import parse_bool
from scipy.ndimage.filters import gaussian_filter



# TODO: This is required by s70 descriptor export, but should not
@dddtask(order="59.89.+.10")
def osm_terrain_export_splatmap_init(root, pipeline, osm, logger):
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
        ddd.mats.terrain_rock,
        ddd.mats.terrain_ground,
        ]

    pipeline.data['splatmap:channels_num'] = 16

    pipeline.data['splatmap:channels:collapse_map'] = None
    #pipeline.data['splatmap:channels:collapse_map'] = [
    #    [0, 2, 12],     # Terrain, asphalt, pavement, sand
    #    [1, 13],        # Paths, dirt, rock
    #    [8, 9, 10, 11], # Grass, garden, pàrk, forest
    #    [3, 4, 5]       # Pedestrian, tiles
    #]

    pipeline.data['splatmap:ids'] = {}

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
def osm_terrain_export_splatmap_condition(pipeline):
    return parse_bool(pipeline.data.get('ddd:terrain:splatmap', False))



@dddtask(order="*.10.+")
def osm_terrain_export_splatmap_channels_all(root, pipeline, osm, logger):
    for i in range(pipeline.data['splatmap:channels_num']):
        mat = pipeline.data['splatmap:channels_materials'][i]
        objs = ddd.group2()
        if mat:
            sel = root.find("/Areas").select('["ddd:material" = "%s"]["ddd:layer" = "0"]["ddd:material:splatmap" = True]' % mat.name)
            objs.append(sel.children)
            sel = root.find("/Ways").select('["ddd:material" = "%s"]["ddd:layer" = "0"]["ddd:material:splatmap" = True]' % mat.name)
            objs.append(sel.children)
        objs.name = 'Channel' + str(i)
        root.find("/Splatmap").append(objs)

'''
@dddtask()
def osm_terrain_export_splatmap_channel_0_terrain(root, pipeline, osm, logger):
    objs = root.select('["ddd:material" = "Ground"]')
    objs.name = 'Channel0'
    root.find("/Splatmap").append(objs)

@dddtask()
def osm_terrain_export_splatmap_channel_1_dirt(root, pipeline, osm, logger):
    objs = root.select('["ddd:material" = "Dirt"]')
    objs.name = 'Channel1'
    root.find("/Splatmap").append(objs)

@dddtask()
def osm_terrain_export_splatmap_channel_2_rock(root, pipeline, osm, logger):
    objs = root.select('["ddd:material" = "Rock"]')
    objs.name = 'Channel2'
    root.find("/Splatmap").append(objs)

@dddtask()
def osm_terrain_export_splatmap_channel_3_park(root, pipeline, osm, logger):
    objs = root.select('["ddd:material" ~ "Park|Forest"]')
    objs.name = 'Channel3'
    root.find("/Splatmap").append(objs)

@dddtask()
def osm_terrain_export_splatmap_channel_4_sand(root, pipeline, osm, logger):
    objs = root.select('["ddd:material" = "Sand"]')
    objs.name = 'Channel4'
    root.find("/Splatmap").append(objs)

@dddtask()
def osm_terrain_export_splatmap_channel_5(root, pipeline, osm, logger):
    objs = root.select('["ddd:material" = "NONE"]')
    objs.name = 'Channel5'
    root.find("/Splatmap").append(objs)

@dddtask()
def osm_terrain_export_splatmap_channel_6_pedestrian(root, pipeline, osm, logger):
    objs = root.select('["ddd:material" = "WayPedestrian"]')
    objs.name = 'Channel6'
    root.find("/Splatmap").append(objs)

@dddtask()
def osm_terrain_export_splatmap_channel_7_grass(root, pipeline, osm, logger):
    objs = root.select('["ddd:material" ~ "Grass|Garden"]')
    objs.name = 'Channel7'
    root.find("/Splatmap").append(objs)
'''




def osm_terrain_splatmap_detail_id(pipeline, obj):
    """
    """
    idmap = pipeline.data['splatmap:ids']
    ignore_keys = ('osm:user', 'osm:feature', 'osm:feature_2d', 'osm:timestamp', 'osm:name', 'osm:alt_name', 'osm:source', 'osm:version', 'osm:changeset', 'osm:uid', 'osm:id', 'osm:layer', 'osm:original', 'osm:way', 'osm:oneway', 'osm:element',
                   'osm:cycleway', 'osm:maxspeed')
    #include_keys = ('osm:highway', 'osm:leisure', 'osm:surface', 'osm:amenity')

    detail_data = {}
    for k, v in obj.extra.items():
        if not k.startswith('osm:') or any([k.startswith(v) for v in ignore_keys]): continue
        #if k not in include_keys: continue
        detail_data[k] = v
    if obj.mat:
        detail_data['ddd:material'] = obj.mat.name
    detail_data['ddd:area:type'] = obj.get('ddd:area:type', None)

    code = ";".join(sorted(['%s=%s' % (k, v) for k, v in detail_data.items()]))
    if code not in idmap:
        idmap[code] = max(list(idmap.values()) + [0]) + 1
    code_id = idmap[code]
    return code_id


@dddtask()
def osm_terrain_export_splatmap(root, pipeline, osm, logger):
    """
    Exports
    """

    ddd_bounds = osm.area_crop.bounds
    wgs84_min = terrain.transform_ddd_to_geo(osm.ddd_proj, ddd_bounds[:2])
    wgs84_max = terrain.transform_ddd_to_geo(osm.ddd_proj, ddd_bounds[2:])
    wgs84_bounds = wgs84_min + wgs84_max

    splatmap_size = pipeline.data.get('ddd:terrain:splatmap:size', 128)
    use_detailmap = pipeline.data.get('ddd:terrain:splatmap:detailmap', False)

    logger.info("Generating splatmap for area: ddd_bounds=%s, wgs84_bounds=%s, size=%s", ddd_bounds, wgs84_bounds, splatmap_size)

    channel_indexes = range(pipeline.data['splatmap:channels_num'])
    splatmap = root.find("/Splatmap")

    # Result matrices
    splat_matrix = np.zeros([splatmap_size, splatmap_size, pipeline.data['splatmap:channels_num']])
    id_matrix = np.zeros([splatmap_size, splatmap_size, pipeline.data['splatmap:channels_num']])

    logger.info("Calculating splatmap coverage for %s channels (%d items)", len(channel_indexes),  len(splatmap.geom_recursive()))

    # Spatial index and cached groups
    channel_items_all = {chan_idx: splatmap.find("/Channel%s" % chan_idx) for chan_idx in channel_indexes}

    #channel_items_index = {chan_idx: STRtree(channel_items_all[chan_idx].geom_recursive()) for chan_idx in channel_indexes}
    channel_items_index = {chan_idx: channel_items_all[chan_idx] for chan_idx in channel_indexes}
    for ci, cia in channel_items_index.items(): cia.index_create()

    #channel_items_all_union = {chan_idx: chan.union() for chan_idx, chan in channel_items_all.items()}
    channel_items_sand_spread_union = splatmap.select('["ddd:material" = "Sand"]["osm:natural" = "beach"]').union()

    transformer = pyproj.Transformer.from_proj(osm.ddd_proj, 'epsg:3857', always_xy=True)

    # Interpolate over DDD coordinates
    pixel_width_x = (ddd_bounds[2] - ddd_bounds[0]) / splatmap_size
    pixel_width_y = (ddd_bounds[3] - ddd_bounds[1]) / splatmap_size
    pixel_area = pixel_width_x * pixel_width_y
    points_x = np.linspace(ddd_bounds[0] - pixel_width_x * 0.5, ddd_bounds[2] + pixel_width_x * 0.5, splatmap_size + 1, endpoint=True)
    for xi, (x, xp) in enumerate(zip(points_x, points_x[1:])):
        points_y = list(reversed(np.linspace(ddd_bounds[1] - pixel_width_y * 0.5, ddd_bounds[3] + pixel_width_y * 0.5, splatmap_size + 1, endpoint=True)))
        for yi, (y, yp) in enumerate(zip(points_y, points_y[1:])):

            x_utm, y_utm = transformer.transform(x, y)
            x_utm, y_utm = (x_utm % 4096, y_utm % 4096)

            pixel_rect = ddd.rect([x, y, xp, yp])

            # Assign values to matrices
            for chan_idx in channel_indexes:

                channel_items = channel_items_all[chan_idx]

                cand_geoms = channel_items_index[chan_idx].index_query(pixel_rect)  # .geom)
                cand_items = [c for c in cand_geoms.children if c.intersects(pixel_rect) and c in channel_items.children]

                # Check if intersects and percentage
                pixel_item = ddd.group2(cand_items).intersection(pixel_rect).union()

                item_area = pixel_item.area()

                # Calculate cover factor (pixels in the border account for half/quarter the surface due to previous tile clipping (should be avoided)
                cover_factor = item_area / pixel_area
                if (xi in (0, splatmap_size - 1)):
                    cover_factor *= 2
                if (yi in (0, splatmap_size - 1)):
                    cover_factor *= 2

                # Augmentation tests: sand (12) - extend sand around
                if chan_idx == 12 and not channel_items_sand_spread_union.is_empty():
                    if cover_factor < 0.99:
                        distance = channel_items_sand_spread_union.distance(ddd.point([x, y]))
                        distance_reach = 8.0
                        #extend_ratio *= noise.pnoise2(coords[0] * 0.1, coords[1] * 0.1, octaves=2, persistence=0.5, lacunarity=2, repeatx=1024, repeaty=1024, base=0)  # Randomize reach
                        aug_factor = max(0, 1.0 - distance / distance_reach)
                        noise_factor = noise.pnoise2(x_utm * 0.03, y_utm * 0.03, octaves=3, persistence=0.2, lacunarity=0.7, repeatx=4096, repeaty=4096, base=0)
                        noise_factor = ddd.math.clamp((noise_factor - 0.5) * 2.0, 0.0, 1.0)  #  * (0.15 if chan_idx == 10 else 0.3)
                        aug_factor = max(aug_factor * noise_factor, 0.0) * 0.75

                        cover_factor = max(aug_factor, cover_factor)
                        splat_matrix[yi, xi, :] -= cover_factor  # Reduce others


                # Augmentation tests: park (10) - mixes ground and rock
                if chan_idx == 10 or chan_idx == 11:
                    if cover_factor > 0.95:
                        reduce_factor = noise.pnoise2(x_utm * 0.03, y_utm * 0.03, octaves=3, persistence=2.2, lacunarity=0.7, repeatx=4096, repeaty=4096, base=0)
                        reduce_factor = ddd.math.clamp((reduce_factor - 0.1) * 4.0, 0.0, 1.0) * 0.75  #  * (0.15 if chan_idx == 10 else 0.3)
                        cover_factor = cover_factor - reduce_factor
                        splat_matrix[yi, xi, 0] += (reduce_factor * random.uniform(0, 1)) # Increase terrain
                        splat_matrix[yi, xi, 13] += (reduce_factor * random.uniform(0, 1))  # Increase rock

                splat_matrix[yi, xi, chan_idx] += cover_factor

                # Detail map (IDs)
                if use_detailmap:
                    for cand_item in cand_items:

                        if not pixel_item.intersects(pixel_rect): continue

                        detail_id = osm_terrain_splatmap_detail_id(pipeline, cand_item)
                        id_matrix[yi, xi, chan_idx] = detail_id


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

    splat_matrix_corrected = np.copy(splat_matrix)
    # Channels 1 and 2
    #splat_matrix_corrected[:,:,1] = splat_matrix_corrected[:,:,1] * 4.0
    #splat_matrix_corrected = np.minimum(splat_matrix_corrected, 1.0)

    # TODO: Use attributes for all this (different areas spread differently and get dirty differently)
    diffuse = (1, 12)  #  , 13, 14, 15)
    preserve = (2, 3, 4, 5)
    preserve_sum = np.zeros([splatmap_size, splatmap_size])
    for p in preserve:
        preserve_sum = np.maximum(preserve_sum, splat_matrix[:,:,p])
    for i in diffuse:
        splat_matrix_corrected[:,:,i] = gaussian_filter(splat_matrix_corrected[:,:,i], sigma=2)
        splat_matrix_corrected[:,:,i] -= preserve_sum

    splat_matrix = splat_matrix_corrected

    # Clamp to 0..1
    splat_matrix = np.maximum(splat_matrix, 0.0)
    splat_matrix = np.minimum(splat_matrix, 1.0)



    # Save
    #print(splat_matrix)

    #splat2_0_3_matrix = splat_matrix[:,:,:4] * 255
    #im = Image.fromarray(np.uint8(splat2_0_3_matrix), "RGBA")
    #im.save("/tmp/osm-splatmap-8chan-0_3-" + str(splatmap_size) + ".png", "PNG")

    #splat2_4_7_matrix = splat_matrix[:,:,4:] * 255
    #im = Image.fromarray(np.uint8(splat2_4_7_matrix), "RGBA")
    #im.save("/tmp/osm-splatmap-8chan-4_7-" + str(splatmap_size) + ".png", "PNG")


    # Detail map
    #filename = (pipeline.data['filenamebase'] + ".detailmap-" + str(pipeline.data['splatmap:channels_num']) +
    #            "chan-0_" + str(pipeline.data['splatmap:channels_num'] - 1) + "-" + str(splatmap_size) + ".png")
    #logger.info("Saving detail map to: %s", filename)
    #im = Image.fromarray(np.uint8(id_matrix), "RGBA")
    #im.save(filename, "PNG")


    # Collapse into N channels
    splat_matrix_collapsed = None
    collapse_map = pipeline.data.get('splatmap:channels:collapse_map', None)
    if collapse_map:
        splat_matrix_collapsed = np.zeros([splatmap_size, splatmap_size, len(collapse_map)])
        id_matrix_collapsed = np.zeros([splatmap_size, splatmap_size, len(collapse_map)]) if use_detailmap else None
        for collapse_idx in range(len(collapse_map)):
            #collapse_source_weight = (1.0 / len(collapse_map[collapse_idx]))
            for collapse_source in collapse_map[collapse_idx]:
                splat_matrix_collapsed[:,:,collapse_idx] += (splat_matrix[:,:,collapse_source])
                if use_detailmap:
                    id_matrix_collapsed[:,:,collapse_idx] = np.maximum(id_matrix_collapsed[:,:,collapse_idx], id_matrix[:,:,collapse_source])

        splat_matrix_collapsed = np.minimum(splat_matrix_collapsed, 1.0)


    #splat_matrix_collapsed = splat_matrix[:,:,0:4] + splat_matrix[:,:,4:8]
    #splat_matrix_collapsed = splat_matrix_collapsed * (0.5 * 255)

    #im = Image.fromarray(np.uint8(splat_matrix_collapsed), "RGBA")
    #im.save("/tmp/osm-splatmap-1chan-0_3.png", "PNG")
    #im.save(pipeline.data['filenamebase'] + ".splatmap-4chan-0_3-" + str(splatmap_size) + ".png", "PNG")

    if collapse_map:

        filename = (pipeline.data['filenamebase'] + ".splatmap-" + str(len(collapse_map)) + "chan-0_" + str(len(collapse_map) - 1) + "-" + str(splatmap_size) + ".png")
        logger.info("Saving splatmap map to: %s", filename)
        im = Image.fromarray(np.uint8(splat_matrix_collapsed * 255), "RGBA")
        #im.save("/tmp/osm-splatmap-1chan-0_3-processed.png", "PNG")
        im.save(filename, "PNG")

        if use_detailmap:
            filename = (pipeline.data['filenamebase'] + ".detailmap-" + str(len(collapse_map)) + "chan-0_" +  str(len(collapse_map) - 1) + "-" + str(splatmap_size) + ".png")
            logger.info("Saving detail map to: %s", filename)
            im = Image.fromarray(np.uint8(id_matrix_collapsed), "RGBA")
            im.save(filename, "PNG")


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


    filename = (pipeline.data['filenamebase'] + ".splatmap-" + str(pipeline.data['splatmap:channels_num']) +
                "chan-0_" + str(pipeline.data['splatmap:channels_num'] - 1) + "-" + str(splatmap_size) + ".png")
    logger.info("Saving splatmap atlas to: %s", filename)
    im = Image.fromarray(np.uint8(splat_matrix_atlas * 255), "RGBA")
    #im.save("/tmp/osm-splatmap-1chan-0_3-processed.png", "PNG")
    im.save(filename, "PNG")

    # Metadata (to be saved later to descriptor)
    pipeline.data['splatmap:channels'] = {k: (v.name if v else None) for k, v in enumerate(pipeline.data['splatmap:channels_materials'])}

        # Correct splatmap
    pipeline.data['splatmap:ids'] = {v: k for k, v in pipeline.data['splatmap:ids'].items()}


