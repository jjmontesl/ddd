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


@dddtask(order="69.89.+.+")
def osm_gdterain_export_heightmap(root, osm, pipeline, logger):

    # Get chunk heightmap from elevation engine

    # TODO: Correct heightmap with calculated alterations (ponds, riverbanks, elevation augmentation...)

    #terrain.terrain_geotiff_elevation_apply(ceilings_3d, osm.ddd_proj)
    elevation = ElevationModel.instance()
    ddd_bounds = osm.area_crop.bounds
    wgs84_min = terrain.transform_ddd_to_geo(osm.ddd_proj, ddd_bounds[:2])
    wgs84_max = terrain.transform_ddd_to_geo(osm.ddd_proj, ddd_bounds[2:])
    wgs84_bounds = wgs84_min + wgs84_max

    heightmap_size = 128

    logger.info("Generating heightmap for area: ddd_bounds=%s, wgs84_bounds=%s, size=%s", ddd_bounds, wgs84_bounds, heightmap_size)

    #height_matrix = elevation.dem.area(wgs84_bounds)
    #print(height_matrix)

    # Interpolate over DDD coordinates and resolve height
    height_matrix = np.zeros([heightmap_size, heightmap_size])
    for xi, x in enumerate(np.linspace(ddd_bounds[0], ddd_bounds[2], heightmap_size, endpoint=True)):
        for yi, y in enumerate(np.linspace(ddd_bounds[1], ddd_bounds[3], heightmap_size, endpoint=True)):
            wgs84_point = terrain.transform_ddd_to_geo(osm.ddd_proj, [x, y])
            height = elevation.value(wgs84_point)
            height_matrix[yi, xi] = height

    #print(height_matrix)

    #gradient = np.gradient(height_matrix)

    # Encode heightmap
    # R,G = height
    # B = normals
    # A = holes
    encoded_heightmap = np.zeros((heightmap_size, heightmap_size, 4))
    for xi in range(heightmap_size):
        for yi in range(heightmap_size):
            height = height_matrix[yi, xi]
            patch_height_offset = 0.0
            patch_height_range = 512 # 65535.0  # 65535.0
            normalizedHeight = (height - patch_height_offset) / patch_height_range;
            quantizedHeight = int(normalizedHeight * 65535);

            encoded_heightmap[yi, xi, 0] =  quantizedHeight & 0x00ff
            encoded_heightmap[yi, xi, 1] = (quantizedHeight & 0xff00) >> 8
            #encoded_heightmap[yi, xi, 2] = 0
            encoded_heightmap[yi, xi, 3] = 255

    height_max = np.max(height_matrix)
    height_min = np.min(height_matrix)

    #print(encoded_heightmap)
    logger.info("Heightmap max=%s min=%s (range=%s)", height_max, height_min, height_max - height_min)

    # Save heightmap as PNG
    im = Image.fromarray(np.uint8(encoded_heightmap), "RGBA")
    im.save("/tmp/heightmap.png", "PNG")
    im.save(pipeline.data['filenamebase'] + ".heightmap.png", "PNG")

