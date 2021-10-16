# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import functools
import inspect
import logging
import os

from lark.lark import Lark

from ddd.core.selectors.selector import DDDSelector
from ddd.core.selectors.selector_ebnf import selector_ebnf
from ddd.ddd import ddd
from ddd.core.exception import DDDException


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class DDDTask(object):
    """
    Defines a task for DDD pipelines.

    - order: A string in the form '#.#...'. See below.

    Order is a string that defines the ordering within this pipeline.
    If not specified, order is taken from the last defined task with its last number
    incremented (eg if last task is 10.10.1, this task becomes 10.10.2), equivalent to '*.+'.
    It order starts with '*', the asterisk is replaced by the previous task number except the
    last number (eg if last task is 10.10.1, with '*.50' this task becomes '10.10.50').

    """


    _tasks = []

    def __init__(self, name=None, path=None, select=None, filter=None,
                 order=None, #parent=None, before=None, after=None,
                 log=None, recurse=False,
                 condition=False, cache=False, cache_override=False):

        self.name = name

        self.order = order
        self._order_num = None

        #self.parent = parent
        #self.before = before
        #self.after = after

        self.condition = condition
        self.cache = cache
        self.cache_override = cache_override

        self.log = log

        self.path = path
        self.filter = filter
        self.recurse = recurse
        self.replace = True

        try:
            self.selector = DDDSelector(select) if select else None
        except Exception as e:
            logger.error("Invalid selector: %s", select)
            #raise DDDException("Invalid selector: %s", select)
            raise

        # Sanity check
        if (self.path or self.selector or self.filter) and (self.condition):
            raise DDDException("A task cannot have both path/selector/filter and a condition parameters.")

        # TODO: Do this in the decorator, not here. Registry shall possisbly be separate, what if someone needs an unregistered task
        DDDTask._tasks.append(self)

    def __call__(self, *args):
        #logger.info("Task Func: %s %s", self, args)
        self._funcargs = args
        if self.name is None:
            self.name = args[0].__name__
        #self._module = args[0].__module__

    def __repr__(self):
        return "%s(%s-%s)" % (self.__class__.__name__, ".".join([str(n) for n in self._order_num]) if self._order_num else self.order, self.name)

    def runlog(self, obj=None):
        if self.log in (True, False, None) :
            logger.info("Running %s (obj=%s)", self, obj)
        else:
            logger.info("%s (task=%s, obj=%s)", self.log, self, obj)

    def run(self, pipeline):

        try:
            #logger.warn("DEBUG: %s", pipeline.root.select(path="/Areas", selector='[osm:id = "way-112075680"]', recurse=True))
            #logger.warn("DEBUG: %s", pipeline.root.select(path="/Ways", selector='[osm:id = "way-112075680"]', recurse=True))
            #logger.warn("DEBUG: %s %s", pipeline.root.select(path="/Areas"), pipeline.root.select(path="/Ways"))
            pass
        except:
            pass

        #logger.info("Task select: filter=%s select=%s path=%s", self.filter, self.selector, self.path)

        if (self.path or self.selector or self.filter): return self.run_each(pipeline)

        #if self.log:
        self.runlog()
        #else:
        #    logger.debug("Running task: %s", self)

        func = self._funcargs[0]
        sig = inspect.signature(func)
        kwargs = {}
        for arg in sig.parameters.keys():
            if arg == 'r': kwargs['r'] = pipeline.root
            elif arg == 'root': kwargs['root'] = pipeline.root
            elif arg == 'p': kwargs['r'] = pipeline
            elif arg == 'pipeline': kwargs['pipeline'] = pipeline
            elif arg == 'o': kwargs['o'] = None
            elif arg == 'obj': kwargs['obj'] = None
            elif arg == 'logger': kwargs['logger'] = logging.getLogger(func.__module__)
            elif arg in pipeline.data: kwargs[arg] = pipeline.data[arg]

        result = func(**kwargs)

        return result

    def run_each(self, pipeline):

        func = self._funcargs[0]
        sig = inspect.signature(func)
        kwargs = {}
        for arg in sig.parameters.keys():
            if arg == 'r': kwargs['r'] = pipeline.root
            elif arg == 'root': kwargs['root'] = pipeline.root
            elif arg == 'p': kwargs['r'] = pipeline
            elif arg == 'pipeline': kwargs['pipeline'] = pipeline
            elif arg == 'o': kwargs['o'] = None
            elif arg == 'obj': kwargs['obj'] = None
            elif arg == 'logger': kwargs['logger'] = logging.getLogger(func.__module__)
            elif arg in pipeline.data: kwargs[arg] = pipeline.data[arg]
            else:
                raise DDDException("Unknown argument in task parameter list: %s (task: %s)" % (arg, self))

        logger.debug("Select: func=%s selector=%s path=%s recurse=%s ", self.filter, self.selector, self.path, self.recurse)
        objs = pipeline.root.select(func=self.filter, selector=self.selector, path=self.path, recurse=self.recurse)

        #if self.log:
        self.runlog(objs.count())
        #else:
        #    logger.debug("Running task %ws for %d objects.", self, objs.count())

        def task_select_apply(o):
            try:
                if 'o' in kwargs: kwargs['o'] = o
                if 'obj' in kwargs: kwargs['obj'] = o
                result = func(**kwargs)
                if self.replace:
                    return result
                else:
                    if result or result is False:
                        logger.error("Task function returned a replacement object or a delete (None), but task replace is set to False.")
                        raise DDDException("Task function returned a replacement object or a delete (None), but task replace is set to False.")
                    return o

            except Exception as e:
                logger.error("Error running task %s on %s: %s", self, o, e)
                raise DDDException("Error running task %s on %s: %s" % (self, o, e), ddd_obj=o)

        pipeline.root.select(func=self.filter, selector=self.selector, path=self.path, recurse=self.recurse, apply_func=task_select_apply)

        '''
        for o in objs.children:
            #logger.debug("Running task %s for object: %s", self, o)
            try:
                if 'o' in kwargs: kwargs['o'] = o
                if 'obj' in kwargs: kwargs['obj'] = o
                result = func(**kwargs)
                if self.replace:
                    if result:
                        o.replace(result)
                    elif result is False:
                        pipeline.root.remove(o)
            except Exception as e:
                logger.error("Error running task %s on %s: %s", self, o, e)
                raise DDDException("Error running task %s on %s: %s" % (self, o, e), ddd_obj=o)

            #interactive.showbg(pipeline.root)
        '''



'''
class DDDIterateTask(DDDTask):

    def __init__(self, name=None, path=None, select=None, parent=None, before=None, after=None):
        self.name = name
        self.path = path
        self.selector = select
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
