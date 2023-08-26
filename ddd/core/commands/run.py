# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020-2023

import argparse
import logging
from ddd.core.cli import D1D2D3Bootstrap

from ddd.core.command import DDDCommand
from ddd.pipeline.pipeline import DDDPipeline


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class RunCommand(DDDCommand):

    def parse_args(self, args):

        parser = argparse.ArgumentParser()  # description='', usage = ''
        parser.prog = parser.prog + " " + D1D2D3Bootstrap._instance.command

        parser.add_argument("--show", action="store_true", default=False, help="show root node at the end")
        #parser.add_argument("--show", const=True, default=False, nargs="?", help="show root node (or use a selector) at the end")
        parser.add_argument("--save", action="store", nargs="?", default=None, type=str, help="save root node at the end")

        parser.add_argument("script", type=str, help="Script to run")

        args = parser.parse_args(args)

        self.script = args.script

        self.save = args.save
        self.show = args.show


    def run(self):

        logger.info("Running DDD123 script: %s", self.script)

        pipeline = DDDPipeline(self.script, name="DDD Build Pipeline")

        # Run pipeline
        pipeline.run()

        if self.show:
            logger.info("Showing root node")
            pipeline.root.show()

        if self.save:
            logger.info("Saving root node to: %s", self.save)
            pipeline.root.save(self.save)

