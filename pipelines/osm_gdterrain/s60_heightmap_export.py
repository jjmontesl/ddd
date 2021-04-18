# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020

import sys

import png
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


@dddtask(order="69.89.+.10", condition=True)
def osm_gdterrain_export_heightmap_condition(pipeline):
    return bool(pipeline.data.get('ddd:gdterrain:heightmap', False))


@dddtask(order="*.10.+")
def osm_gdterrain_export_heightmap(root, osm, pipeline, logger):

    # Get chunk heightmap from elevation engine

    # TODO: Correct heightmap with calculated alterations (ponds, riverbanks, elevation augmentation...)

    #terrain.terrain_geotiff_elevation_apply(ceilings_3d, osm.ddd_proj)
    elevation = ElevationModel.instance()
    ddd_bounds = osm.area_crop.bounds
    wgs84_min = terrain.transform_ddd_to_geo(osm.ddd_proj, ddd_bounds[:2])
    wgs84_max = terrain.transform_ddd_to_geo(osm.ddd_proj, ddd_bounds[2:])
    wgs84_bounds = wgs84_min + wgs84_max

    heightmap_size = pipeline.data.get('ddd:gdterrain:heightmap:size', 128)

    logger.info("Generating heightmap for area: ddd_bounds=%s, wgs84_bounds=%s, size=%s", ddd_bounds, wgs84_bounds, heightmap_size)

    #height_matrix = elevation.dem.area(wgs84_bounds)
    #print(height_matrix)

    water = root.select(path="/Areas", selector='["ddd:area:type" = "sea"]["ddd:crop:original"]')

    # Interpolate over DDD coordinates and resolve height
    height_matrix = np.zeros([heightmap_size, heightmap_size])
    for xi, x in enumerate(np.linspace(ddd_bounds[0], ddd_bounds[2], heightmap_size, endpoint=True)):
        for yi, y in enumerate(reversed(np.linspace(ddd_bounds[1], ddd_bounds[3], heightmap_size, endpoint=True))):
            wgs84_point = terrain.transform_ddd_to_geo(osm.ddd_proj, [x, y]) # Arbitrary offset tests
            height = elevation.value(wgs84_point)
            if height < 0: height = 0

            # Temporarily enhance with areas (ultimately, this is needed for much more, maybe comming from elevation-plus engine)
            # At least use spatial partitioning to find where the point lies
            '''
            dddp = ddd.point([x, y])
            for c in water.children:
                if c.get('ddd:crop:original').intersects(dddp):
                    height = 0
            '''

            height_matrix[yi, xi] = height

    height_max = np.max(height_matrix)
    height_min = np.min(height_matrix)

    logger.info("Heightmap max=%s min=%s (range=%s)", height_max, height_min, height_max - height_min)

    '''
    # Hillshade
    #print(height_matrix)
    height_normalized = (height_matrix - height_min) / (height_max - height_min)
    hillshade_matrix = hillshade(height_matrix, 270 + wgs84_min[1], 45.0)

    # Blend height and hillshade
    height_hillshade_matrix = height_normalized * 0.5 + hillshade_matrix * 0.5

    # Save Hillshade
    encoded_hillshade = (height_hillshade_matrix * 255)
    im = Image.fromarray(np.uint8(encoded_hillshade), "L")
    #im.save("/tmp/hillshade.png", "PNG")
    im.save(pipeline.data['filenamebase'] + ".hillshade.png", "PNG")
    '''


    '''
    # Calculate gradient
    gradient_diff = 0.1
    #gradient_matrix = np.gradient(height_matrix)
    gradient_matrix = np.zeros([heightmap_size, heightmap_size, 2])
    for xi, x in enumerate(np.linspace(ddd_bounds[0], ddd_bounds[2], heightmap_size, endpoint=True)):
        for yi, y in enumerate(reversed(np.linspace(ddd_bounds[1], ddd_bounds[3], heightmap_size, endpoint=True))):

            if (height_matrix[yi, xi] == 0):  # water
                gradient_matrix[yi, xi, 0] = 0
                gradient_matrix[yi, xi, 1] = 0
                continue

            wgs84_point_x0 = terrain.transform_ddd_to_geo(osm.ddd_proj, [x - gradient_diff, y])
            wgs84_point_x1 = terrain.transform_ddd_to_geo(osm.ddd_proj, [x + gradient_diff, y])
            wgs84_point_y0 = terrain.transform_ddd_to_geo(osm.ddd_proj, [x, y - gradient_diff])
            wgs84_point_y1 = terrain.transform_ddd_to_geo(osm.ddd_proj, [x, y + gradient_diff])

            height_x0 = elevation.value(wgs84_point_x0)
            height_x1 = elevation.value(wgs84_point_x1)
            height_y0 = elevation.value(wgs84_point_y0)
            height_y1 = elevation.value(wgs84_point_y1)

            grad_x = (height_x1 - height_x0) / (gradient_diff * 2.0)
            grad_y = -(height_y1 - height_y0) / (gradient_diff * 2.0)  # DDD CRS is positive Y north/up

            gradient_matrix[yi, xi, 0] = grad_x
            gradient_matrix[yi, xi, 1] = grad_y

    #print(gradient_matrix)

    # Encode heightmap
    # R,G = height
    # B = normals
    # A = holes
    '''

    heightmap_offset = height_min
    heightmap_range = height_max - height_min
    heightmap_quantization = 65535

    '''
    encoded_heightmap = np.zeros((heightmap_size, heightmap_size, 4))
    for xi in range(heightmap_size):
        for yi in range(heightmap_size):
            # Encode height
            height = height_matrix[yi, xi]
            normalizedHeight = (height - heightmap_offset) / heightmap_range;
            quantizedHeight = int(normalizedHeight * heightmap_quantization);

            encoded_heightmap[yi, xi, 0] =  quantizedHeight & 0x00ff
            encoded_heightmap[yi, xi, 1] = (quantizedHeight & 0xff00) >> 8

            # Encode normal
            gradient_x = gradient_matrix[yi, xi, 0]
            normal_x = math.cos(math.pi / 2 + math.atan(gradient_x))
            gradient_y = gradient_matrix[yi, xi, 1]
            normal_y = math.cos(math.pi / 2 + math.atan(gradient_y))
            quantized_normal_x = int(((normal_x + 1.0) / 2.0) * 255.0)  # between -128 and 127
            quantized_normal_y = int(((normal_y + 1.0) / 2.0) * 255.0)  # between -128 and 127

            encoded_heightmap[yi, xi, 2] = quantized_normal_x
            encoded_heightmap[yi, xi, 3] = quantized_normal_y
            #encoded_heightmap[yi, xi, 3] = 255
    '''

    # Save heightmap as PNG

    filename = pipeline.data['filenamebase'] + ".heightmap-" + str(heightmap_size) + ".png"

    #im = Image.fromarray(np.uint8(encoded_heightmap), "RGBA")
    #im = Image.fromarray(np.uint16(encoded_heightmap), "I")
    #im.save("/tmp/osm-heightmap.png", "PNG")
    #im.save(filename, "PNG")

    heightmap_uint16 = np.uint16(((height_matrix - heightmap_offset) / heightmap_range) * 65535)
    with open(filename, 'wb') as f:
        writer = png.Writer(width=heightmap_size, height=heightmap_size, bitdepth=16, greyscale=True)
        pngdata = (heightmap_uint16).tolist()
        writer.write(f, pngdata)


    # Metadata (to be saved later to descriptor)
    pipeline.data['height:min'] = height_min
    pipeline.data['height:max'] = height_max
    pipeline.data['heightmap:offset'] = heightmap_offset
    pipeline.data['heightmap:range'] = heightmap_range
    pipeline.data['heightmap:quantization'] = heightmap_quantization


def hillshade(height_matrix, azimuth=45, elevation_angle=45):
    """
    Returns a hillshade matrix, with brightness values between 0.0 and 1.0.

    Azimuth and elevation are geographic (0-360 clockwise, 0-90).

    From http://neondataskills.org/lidar/create-hillshade-py/
    """

    elevation_angle = elevation_angle * ddd.RAD_TO_DEG
    azimuth = math.pi / 2 - azimuth * ddd.RAD_TO_DEG

    x, y = np.gradient(height_matrix)
    slope = np.pi / 2.0 - np.arctan(np.sqrt(x * x + y * y))
    aspect = np.arctan2(-x, y)

    hillshade = np.sin(azimuth) * np.sin(slope) + np.cos(elevation_angle) * np.cos(slope) * np.cos((azimuth - np.pi / 2.0) - aspect)

    return (hillshade + 1.0) / 2.0

