# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import argparse
import logging

from ddd.core.command import DDDCommand
from ddd.pipeline.pipeline import DDDPipeline
from ddd.util.common import parse_bool
from shapely.geometry.geo import shape

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
