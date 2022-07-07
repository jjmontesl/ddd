# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import argparse
from functools import partial
import json
import logging
import math
import os
import subprocess
import sys

import geojson
from pygeotile.tile import Tile
import pyproj
from shapely import ops
from shapely.geometry.geo import shape

from ddd.core import settings
from ddd.core.cli import D1D2D3Bootstrap
from ddd.core.command import DDDCommand
from ddd.ddd import ddd, D1D2D3
from ddd.geo import terrain
from ddd.osm import osm
from ddd.pipeline.pipeline import DDDPipeline
from ddd.osm.commands import downloader
from ddd.geo.elevation import ElevationModel
import datetime
from ddd.util.common import parse_bool


#from osm import OSMDDDBootstrap
# Get instance of logger for this module
logger = logging.getLogger(__name__)


class RunCommand(DDDCommand):

    def parse_args(self, args):

        #program_name = os.path.basename(sys.argv[0])
        parser = argparse.ArgumentParser()  # description='', usage = ''

        parser.add_argument("--show", action="store_true", default=False, help="show root node at the end")
        parser.add_argument("--save", action="store", nargs="?", default=None, type=str, help="save root node at the end")

        parser.add_argument("script", type=str, help="Script to run")

        args = parser.parse_args(args)

        self.script = args.script

        self.save = args.save
        self.show = args.show


    def run(self):

        logger.info("Running DDD123 script.")

        pipeline = DDDPipeline(self.script, name="DDD Server Build Pipeline")

        # Run pipeline
        pipeline.run()

        if self.show:
            logger.info("Showing root node")
            pipeline.root.show()

        if self.save:
            logger.info("Saving root node to: %s", self.save)
            pipeline.root.save(self.save)
