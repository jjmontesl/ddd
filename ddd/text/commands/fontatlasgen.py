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


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class FontAtlasGenerateCommand(DDDCommand):
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

        logger.info("DDD123 Generate a Raster Font Atlas.")

        self.font_generate()

    def font_generate(self):

        # For mesh generation:
        # OpenGL mesh-based font rendering: https://learnopengl.com/In-Practice/Text-Rendering

        # pyvips raster + atlas generation: Python TTF font rasterizing with cursive support:
        # https://stackoverflow.com/questions/49155546/properly-render-text-with-a-given-font-in-python-and-accurately-detect-its-bound

        codepage = 'latin1'
        font = ''
        font_size = ''

        pass



