# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import argparse
import logging

from ddd.core.command import DDDCommand
from ddd.pipeline.pipeline import DDDPipeline
from ddd.util.common import parse_bool
from shapely.geometry.geo import shape

from ddd.core.commands.run import RunCommand

#from osm import OSMDDDBootstrap
# Get instance of logger for this module
logger = logging.getLogger(__name__)


class DescribeCommand(RunCommand):

    def run(self):

        logger.info("Describing DDD pipeline: %s", self.script)

        pipeline = DDDPipeline(self.script, name="DDD Build Pipeline")

        for task in pipeline.tasks:
            #logger.info("Task: %s", task)
            print("Task: %s" % task)
            #print("  %s" % task.description)

            func = task._funcargs[0]
            if func.__doc__:
                print("    %s" % func.__doc__.strip())
                print()


