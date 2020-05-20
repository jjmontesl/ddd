# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging
from ddd.ddd import ddd
import os
from ddd.pipeline.decorators import DDDTask


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class DDDPipeline():

    def __init__(self, configfiles=None, name=None):

        self.name = name

        self.root = ddd.group2()

        if configfiles:
            self.load(configfiles)

    def load(self, configfiles):

        if not isinstance(configfiles, str):
            for filename in configfiles:
                self.load(filename)
            return

        # Load file
        logger.info("Loading pipeline config: %s", configfiles)

    def run(self):
        logger.info("Running  pipeline: %s", self)
        # TODO: Use pydoit to create DAG and run tasks
        for task in DDDTask._tasks:
            task.run(self)

        return self.root
