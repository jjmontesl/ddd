# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import argparse
from functools import partial
import logging
import os
import subprocess

from PyTexturePacker import Packer
import geojson
import pyproj
from shapely import ops

from ddd.core.cli import D1D2D3Bootstrap
from ddd.core.command import DDDCommand
from ddd.ddd import ddd
from ddd.geo import terrain
from ddd.osm import osm


#from osm import OSMDDDBootstrap
# Get instance of logger for this module
logger = logging.getLogger(__name__)


class TexturePackCommand(DDDCommand):
    """
    Uses PyTexturePacker to pack textures.
    """

    def parse_args(self, args):


        #program_name = os.path.basename(sys.argv[0])
        parser = argparse.ArgumentParser()  # description='', usage = ''

        #parser.add_argument("-w", "--worker", default=None, help="worker (i/n)")
        #parser.add_argument("-l", "--limit", type=int, default=None, help="tasks limit")
        #parser.add_argument("--name", type=str, default=None, help="base name for output")
        #parser.add_argument("--radius", type=float, default=None, help="radius of target area")
        #parser.add_argument("--area", type=str, help="GeoJSON polygon of target area")
        #parser.add_argument("--tile", type=float, help="tile size in meters (0 for entire area)")

        args = parser.parse_args(args)
        #self.limit = args.limit
        #self.name = args.name
        #self.radius = args.radius

    def pack_atlas(self):
        # create a MaxRectsBinPacker
        packer = Packer.create(max_width=2048, max_height=2048, bg_color=0xffffff, enable_rotated=False)  # bg_color=0xffffff00)
        # pack texture images under directory "test_case/" and name the output images as "test_case".
        # "%d" in output file name "test_case%d" is a placeholder, which is a multipack index, starting with 0.

        #def (self, bg_color=0x00000000, texture_format=".png", max_width=4096, max_height=4096, enable_rotated=True,
        #      force_square=False, border_padding=2, shape_padding=2, inner_padding=0, trim_mode=0,
        #      reduce_border_artifacts=False):

        #packer.pack("es/", "traffic_signs_es_%d")
        packer.pack("sprites/", "spritesheet_%d")


    def run(self):

        D1D2D3Bootstrap._instance._unparsed_args = None

        logger.info("Running DDD123 Texture Packer command.")

        self.pack_atlas()


