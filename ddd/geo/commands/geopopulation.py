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
from ddd.geo.sources.population import PopulationModel


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class GeoPopulationCommand(DDDCommand):
    """
    Simple tests for population queries.
    """

    def parse_args(self, args):

        #program_name = os.path.basename(sys.argv[0])
        parser = argparse.ArgumentParser()  # description='', usage = ''

        #parser.add_argument("--radius", type=float, default=None, help="radius of target area")
        #parser.add_argument("--area", type=str, help="GeoJSON polygon of target area")
        #parser.add_argument("--tile", type=float, help="tile size in meters (0 for entire area)")
        parser.add_argument("--coords", type=str, help="coordinates to sample (x, y)")

        self.args = parser.parse_args(args)

        self.coords = [float(x) for x in self.args.coords.split(",")]

    def run(self):
        self.geo_population_query(self.coords)

    def geo_population_query(self, coords):

        #coords = [-17.7661362, 28.6822893]  # La Palma: 7685.34716796875 p/km2


        population = PopulationModel()
        value = population.population_km2(coords)

        print("Population for coords %s: %s p/km2" % (coords, value))


