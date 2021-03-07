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

        #parser.add_argument("--radius", type=float, default=None, help="radius of target area")
        #parser.add_argument("--area", type=str, help="GeoJSON polygon of target area")
        #parser.add_argument("--tile", type=float, help="tile size in meters (0 for entire area)")

        args = parser.parse_args(args)

    def run(self):

        logger.info("Generate a Geo Raster config files report map.")

        self.georaster_coverage()

    def georaster_coverage(self):

        map = ddd.group2(name="DDD GeoRaster Coverage")

        tiles_config = settings.DDD_GEO_DEM_TILES
        for tc in tiles_config:

            # Generate polygon in wgs84
            tile = ddd.rect(tc['bounds_wgs84_xy'])
            tile.name = "Tile: %s" % tc['path']
            map.append(tile)

            print(tc)

        #map.show()
        map.save("/tmp/ddd-georaster-coverage.geojson")

