# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging
from ddd.ddd import ddd
import os
import functools
import inspect


# Get instance of logger for this module
logger = logging.getLogger(__name__)


# TODO: Define in a separate file, not in decorators
class DDDTask(object):

    _tasks = []

    def __init__(self, name=None, path=None, select=None, filter=None, parent=None, before=None, after=None, log=None):

        self.name = name

        self.parent = parent
        self.before = before
        self.after = after

        self.log = log

        self.path = path
        self.select = select
        self.filter = filter
        self.replace = True

        logger.debug("Task definition: %s", self)

        # TODO: Do this in the decorator, not here. Registry shall possisbly be separate.
        DDDTask._tasks.append(self)

    def __call__(self, *args):
        #logger.info("Task Func: %s %s", self, args)
        self._funcargs = args
        #self._module = args[0].__module__

    def runlog(self, obj=None):
        if self.log:
            if self.log is True:
                logger.info("Running task (task=%s, obj=%s)", self, obj)
            else:
                logger.info("%s (task=%s, obj=%s)", self.log, self, obj)

    def run(self, pipeline):
        if (self.path or self.select or self.filter): return self.run_each(pipeline)

        if self.log:
            self.runlog()
        else:
            logger.debug("Running task: %s", self)

        func = self._funcargs[0]
        sig = inspect.signature(func)
        kwargs = {}
        for arg in sig.parameters.keys():
            if arg == 'r': kwargs['r'] = pipeline.root
            if arg == 'root': kwargs['root'] = pipeline.root
            if arg == 'p': kwargs['r'] = pipeline
            if arg == 'pipeline': kwargs['root'] = pipeline
            if arg == 'o': kwargs['o'] = None
            if arg == 'obj': kwargs['obj'] = None

        func(**kwargs)

    def run_each(self, pipeline):

        func = self._funcargs[0]
        sig = inspect.signature(func)
        kwargs = {}
        for arg in sig.parameters.keys():
            if arg == 'r': kwargs['r'] = pipeline.root
            if arg == 'root': kwargs['root'] = pipeline.root
            if arg == 'p': kwargs['r'] = pipeline
            if arg == 'pipeline': kwargs['root'] = pipeline
            if arg == 'o': kwargs['o'] = None
            if arg == 'obj': kwargs['obj'] = None

        objs = pipeline.root.select(func=self.filter, path=self.path, recurse=False)  # select=self.select,
        logger.debug("Running task for %d objects: %s", objs.count(), self)
        for o in objs.children:
            self.runlog(o)
            if 'o' in kwargs: kwargs['o'] = o
            if 'obj' in kwargs: kwargs['obj'] = o
            result = func(**kwargs)
            if self.replace and result:
                o.replace(result)



'''
class DDDIterateTask(DDDTask):

    def __init__(self, name=None, path=None, select=None, parent=None, before=None, after=None):
        self.name = name
        self.path = path
        self.select = select
        self.parent = parent
        self.before = before
        self.after = after

        logger.debug("Task definition: %s", self)
        DDDTask._tasks.append(self)


    def run(self, pipeline):
        logger.info("Running task: %s", self)

        func = self._funcargs[0]
        sig = inspect.signature(func)
        kwargs = {}
        for arg in sig.parameters.keys():
            if arg == 'r': kwargs['r'] = pipeline.root
            if arg == 'root': kwargs['root'] = pipeline.root
            if arg == 'p': kwargs['r'] = pipeline
            if arg == 'pipeline': kwargs['root'] = pipeline
            if arg == 'o': kwargs['o'] = None
            if arg == 'obj': kwargs['obj'] = None

        func(**kwargs)
'''


dddtask = DDDTask

