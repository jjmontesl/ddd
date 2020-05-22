# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging
from ddd.ddd import ddd
import os
from ddd.pipeline.decorators import DDDTask
import sys
import importlib
from ddd.core.exception import DDDException


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class DDDPipeline():

    def __init__(self, configfiles=None, name=None):

        self.name = name

        self.root = ddd.group2()

        self.data = {}

        if configfiles:
            self.load(configfiles)

    def __repr__(self):
        return "Pipeline(name=%r)" % (self.name)

    def load(self, configfiles):

        if not isinstance(configfiles, str):
            for filename in configfiles:
                self.load(filename)
            return

        # Load file
        logger.info("Loading pipeline config: %s", configfiles)

        if configfiles.endswith(".py"): configfiles = configfiles[:-3]
        try:
            script_abspath = os.path.abspath(configfiles)
            script_dirpath = os.path.dirname(configfiles)
            #sys.path.append(script_dirpath)
            sys.path.append("..")
            importlib.import_module(configfiles)  #, globals={'ddd_bootstrap': self})
        except ModuleNotFoundError as e:
            raise DDDException("Could not load pipeline definition file: %s" % configfiles)


    def run(self):
        logger.info("Running pipeline: %s", self)
        # TODO: Use pydoit to create DAG and run tasks
        for task in DDDTask._tasks:
            task.run(self)

        return self.root
