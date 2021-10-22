# ddd - DDD123
# Library for simple scene modelling.
# Jose Juan Montes and Contributors 2019-2021

import datetime
import importlib
import logging
import os
import sys

from ddd.core.cli import D1D2D3Bootstrap
from ddd.core.exception import DDDException
from ddd.ddd import ddd
from ddd.pipeline.decorators import DDDTask
import pickle


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class DDDPipeline():

    def __init__(self, config=None, name=None):

        self.name = name
        self.tasks = None

        self.root = ddd.group2()

        self.data = dict(D1D2D3Bootstrap.data)

        self.config = config
        if config:
            self.load(config)

    def __repr__(self):
        return "Pipeline(name=%r)" % (self.name)

    def load(self, configfile):

        DDDTask._tasks = []

        # Load file
        logger.debug("Loading pipeline config: %s", configfile)

        script_abspath = os.path.abspath(configfile)
        script_dirpath = os.path.dirname(configfile)
        script_name = os.path.basename(configfile)
        module_name = script_name[:-3]  # remove .py

        try:
            # Add to path
            #sys.path.append(script_dirpath)
            if script_dirpath not in sys.path:
                logger.info("Appending to path: %s", script_dirpath)
                sys.path.append(script_dirpath)

            importlib.import_module(module_name)  #, globals={'ddd_bootstrap': self})
        except ModuleNotFoundError as e:
            raise DDDException("Could not load pipeline definition file: %s" % configfile)

        self.tasks = DDDTask._tasks

    def _find_last_order(self, tasks, order_split):

        last_order = 0
        idx_track = len(order_split)
        for t in tasks:
            if t._order_num[:idx_track] == order_split[:idx_track]:
                if idx_track < len(t._order_num):
                    last_order = t._order_num[idx_track]
        return last_order

    def tasks_sorted(self):
        tasks = []

        for task in self.tasks:

            try:
                order = task.order
                if order is None: order = '*.+'
                if order.startswith('*.'):
                    if len(tasks) == 0:
                        order = "1"
                    else:
                        order = ".".join([str(e) for e in tasks[-1]._order_num[:-1]] + order.split(".")[1:])

                order_split = order.split(".")
                for (el_idx, el_str) in enumerate(order_split):
                    if el_str == '+':
                        previous_order_num = self._find_last_order(tasks, order_split[:el_idx])
                        el = previous_order_num + 1
                    else:
                        el = int(el_str)
                    order_split[el_idx] = el
                task._order_num = order_split
                tasks.append(task)
            except ValueError as e:
                raise DDDException("Cannot parse order of task %s: %s" % (task, order))

        tasks.sort(key=lambda t: (t._order_num, ))
        return tasks

    def cache_save(self, path):
        logger.info("Saving DDD Pipeline cache data to: %s", path)
        data = {'root': self.root, 'data': self.data}
        with open(path, "wb") as f:
            pickle.dump(data, f)

    def cache_load(self, path):
        logger.info("Loading DDD Pipeline cache data from: %s", path)
        with open(path, "rb") as f:
            data = pickle.load(f)
        self.root = data['root']
        self.data.update(data['data'])

        # This shouldn't be done by osm build pipeline, but this fix is needed meanwhile
        #D1D2D3.data = pipeline.data

    def run_pipeline_internal(self):

        tasks = self.tasks_sorted()
        if D1D2D3Bootstrap.debug:
            for task in tasks:
                logger.debug("  " + str(task))

        # Run init tasks
        for task_idx, task in enumerate(tasks):
            if task.init:
                # Get cache filename (None means that the task is not cached but needed to run before other cache tasks)
                logger.info("Running initialization task: %s", task)
                filename = task.run(self)

        # Find cached task
        first_task_idx = 0
        for task_idx, task in enumerate(reversed(tasks)):
            if task.cache:
                # Get cache filename (None means that the task is not cached but needed to run before other cache tasks)
                logger.debug("Running caching task evaluation: %s", task)
                filename = task.run(self)
                if filename and os.path.exists(filename):
                    # Delete cached file if so specified
                    if D1D2D3Bootstrap.cache_clear is not None and tuple(task._order_num) >= D1D2D3Bootstrap.cache_clear:
                        logger.info("Deleting cached pipeline state (--cache-clear=%s): %s", D1D2D3Bootstrap.cache_clear, filename)
                        os.unlink(filename)
                    else:
                        logger.info("Continuing from cached state: %s", filename)
                        self.cache_load(filename)
                        first_task_idx = len(tasks) - task_idx
                        break

        #tasks = tasks[first_task_idx:]

        skip_tasks = None
        for task_idx, task in enumerate(tasks):

            if task.init:
                continue

            if task_idx < first_task_idx and not task.cache_override:
                continue

            if skip_tasks and task._order_num[:len(skip_tasks)] == skip_tasks:
                logger.info("Skipping: %s", task)
                continue
            skip_tasks = None

            try:
                result = task.run(self)

                if task.condition and not result:
                    # Skip remaining tasks in order
                    skip_tasks = task._order_num
                    logger.info("Skipping tasks: %s", ".".join([str(s) for s in skip_tasks]))

                if task.cache and result:
                    if D1D2D3Bootstrap.cache_ro:
                        logger.info("Skipping caching state (cache_ro is set to True) for: %s", result)
                    else:
                        #logger.info("Caching state to: %s", result)
                        self.cache_save(result)

            except Exception as e:
                logger.error("Error running task %s: %s", task, e)
                #raise DDDException("Error running task %s: %s" % (task, e))
                raise

    '''
    def run_pipeline_doit(self):
        from doit.doit_cmd import DoitMain
        args = {}  # sys.argv[1:]
        doit_run_cmd = cmd_run.Run(task_loader=DDDDoItTaskLoader(self))
        doit_run_cmd.parse_execute(args)
    '''

    def run(self):
        logger.info("Running pipeline: %s (%s configured tasks)", self, len(self.tasks))

        time_start = datetime.datetime.now()
        #self.run_pipeline_doit()
        self.run_pipeline_internal()
        time_end = datetime.datetime.now()

        time_run = (time_end - time_start).total_seconds()
        time_run_m = int(time_run / 60)
        time_run_s = time_run - (time_run_m * 60)

        logger.info("Pipeline processing time: %d:%04.1f m" % (time_run_m, time_run_s))

        return self.root

'''
class DDDDoItTaskLoader(doit.cmd_base.TaskLoader2):

    def __init__(self, pipeline, **kwargs):
        super().__init__(**kwargs)
        self.pipeline = pipeline

    def load_doit_config(self):
        return {'verbosity': 2}
        #return {}

    def load_tasks(self, cmd, pos_args):
        logger.info("Generating tasks for doit runner (%s)", len(DDDTask._tasks))
        tasks = []
        for task in self.pipeline.tasks:
            taskdef = {'name': task.name,
                       'actions': [self.run_task(task)]}
            doittask = dict_to_task(taskdef)
            tasks.append(doittask)
        return tasks

    def run_task(self, task):
        def func():
            result = task.run(self.pipeline)
            return True
        return func

    def setup(self, opt_values):
        pass
'''
