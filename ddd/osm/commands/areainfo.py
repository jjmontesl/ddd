# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

from ddd.osm.commands.build import OSMBuildCommand
from shapely.geometry.geo import shape
import logging
import argparse
import json


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class OSMDataInfoCommand(OSMBuildCommand):

    chunk_size = 250  # 500: 4/km2,  250: 16/km2,  200: 25/km2,  125: 64/km2
    chunk_size_extra_filter = 250  # salamanca: 250  # vigo: 500

    def parse_args(self, args):

        #program_name = os.path.basename(sys.argv[0])
        parser = argparse.ArgumentParser()  # description='', usage = ''

        #parser.add_argument("-w", "--worker", default=None, help="worker (i/n)")
        parser.add_argument("--name", type=str, default=None, help="base name for output")
        parser.add_argument("--center", type=str, default=None, help="center of target area")
        parser.add_argument("--area", type=str, default=None, help="target area polygon GeoJSON")
        #parser.add_argument("--radius", type=float, default=None, help="radius of target area")
        #parser.add_argument("--area", type=str, help="GeoJSON polygon of target area")
        #parser.add_argument("--tile", type=float, help="tile size in meters (0 for entire area)")

        args = parser.parse_args(args)

        center = args.center.split(",")
        self.center = (float(center[0]), float(center[1]))

        self.name = args.name
        self.area = shape(json.loads(args.area))

    def run(self):

        logger.info("DDD123 OSM data information.")

        self.areainfo()

