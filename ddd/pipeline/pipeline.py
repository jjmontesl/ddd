# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import importlib
import logging
import os
import sys

from doit import cmd_run
import doit
from doit.task import dict_to_task

from ddd.core.exception import DDDException
from ddd.ddd import ddd
from ddd.pipeline.decorators import DDDTask
import datetime


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class DDDPipeline():

    def __init__(self, configfiles=None, name=None):

        self.name = name
        self.tasks = None

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
            order = task.order
            if order is None: order = '*.+'
            if order.startswith('*.'):
                order = ".".join([str(e) for e in tasks[-1]._order_num[:-1]] + ['+'])

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

        tasks.sort(key=lambda t: (t._order_num, ))
        return tasks

    def run_pipeline_internal(self):
        tasks = self.tasks_sorted()
        for task in tasks:
            print("  " + str(task))
        for task in tasks:
            task.run(self)

    def run_pipeline_doit(self):
        from doit.doit_cmd import DoitMain
        args = {}  # sys.argv[1:]
        doit_run_cmd = cmd_run.Run(task_loader=DDDDoItTaskLoader(self))
        doit_run_cmd.parse_execute(args)

    def run(self):
        logger.info("Running pipeline: %s (%s configured tasks)", self, len(self.tasks))
        #self.run_pipeline_doit()
        time_start = datetime.datetime.now()
        self.run_pipeline_internal()
        time_end = datetime.datetime.now()

        time_run = (time_end - time_start).total_seconds()
        time_run_m = int(time_run / 60)
        time_run_s = time_run - (time_run_m * 60)

        logger.info("Pipeline processing time: %d:%04.1f m" % (time_run_m, time_run_s))

        return self.root


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
