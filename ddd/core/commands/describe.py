# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import argparse
import logging

from ddd.pipeline.pipeline import DDDPipeline
from ddd.core.commands.run import RunCommand

# Get instance of logger for this module
logger = logging.getLogger(__name__)


class DescribeCommand(RunCommand):

    def run(self):

        logger.info("Describing DDD pipeline: %s", self.script)

        pipeline = DDDPipeline(self.script, name="DDD Build Pipeline")

        # TODO: use the text formatter (Jinja2 based) ? (remember to check word-wrapping + indenting for long texts, etc)

        for task in pipeline.tasks:
            #logger.info("Task: %s", task)
            print("Task: %s" % task)
            #print("  %s" % task.description)

            func = task._funcargs[0]
            if func.__doc__:
                print("    %s" % func.__doc__.strip())
                print()


