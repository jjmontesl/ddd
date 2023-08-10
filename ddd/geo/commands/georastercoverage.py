# ddd - DDD123
# Library for simple scene modelling.
# Jose Juan Montes and Contributors 2019-2021

import glob
import json
import logging
import math
import os
from pathlib import Path
from shapely.geometry.geo import shape

import argparse
from geographiclib.geodesic import Geodesic
import pyproj
from pyproj.proj import Proj
from ddd.core.cli import D1D2D3Bootstrap

from ddd.core.command import DDDCommand
from ddd.geo.georaster import GeoRasterTile
from ddd.ddd import ddd
from ddd.core import settings


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class GeoRasterCoverageCommand(DDDCommand):
    """
    """

    def parse_args(self, args):

        #program_name = os.path.basename(sys.argv[0])
        parser = argparse.ArgumentParser()  # description='', usage = ''
        parser.prog = parser.prog + " " + D1D2D3Bootstrap._instance.command

        #parser.add_argument("--radius", type=float, default=None, help="radius of target area")
        #parser.add_argument("--area", type=str, help="GeoJSON polygon of target area")
        #parser.add_argument("--tile", type=float, help="tile size in meters (0 for entire area)")

        args = parser.parse_args(args)

    def run(self):
        logger.info("Generate a Geo Raster config files report map.")
        self.georaster_coverage()

    def georaster_coverage(self):

        covermap = ddd.group2(name="DDD GeoRaster Coverage")

        tiles_config = settings.DDD_GEO_DEM_TILES
        transformers = {}
        for tc in tiles_config:

            logger.info("Inspecting DEM file: %s", tc['path'])

            crs = tc['crs'].lower()
            transformer = transformers.get(crs, None)
            if not transformer:
                transformer = pyproj.Transformer.from_proj(crs, 'epsg:4326', always_xy=True)
                transformers[crs] = transformer

            projected_point_x0y0 = transformer.transform(tc['bounds'][0], tc['bounds'][1])
            projected_point_x0y1 = transformer.transform(tc['bounds'][0], tc['bounds'][3])
            projected_point_x1y0 = transformer.transform(tc['bounds'][2], tc['bounds'][1])
            projected_point_x1y1 = transformer.transform(tc['bounds'][2], tc['bounds'][3])

            # Generate polygon in wgs84
            tile = ddd.polygon([projected_point_x0y0, projected_point_x1y0, projected_point_x1y1, projected_point_x0y1])
            tile.name = "Tile: %s" % tc['path']

            tile.extra.update(tc)

            file_size = None
            try:
                file_size = os.path.getsize(tc['path'])
            except FileNotFoundError as e:
                pass

            tile.extra['file_size'] = file_size
            tile.extra['file_available'] = file_size is not None

            covermap.append(tile)

            #print(tc)

        #map.show()
        filename = "/tmp/ddd-georaster-coverage.geojson"
        logger.info("Saving map to: %s", filename)
        covermap.save(filename)

