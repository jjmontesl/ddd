# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020-2021

import argparse
import asyncio
from concurrent import futures
import concurrent
import logging
import sys

from aiohttp import web
import socketio
from watchdog.events import FileSystemEventHandler, FileModifiedEvent
from watchdog.observers import Observer

from ddd.core import settings
from ddd.core.cli import D1D2D3Bootstrap
from ddd.core.command import DDDCommand
from ddd.pipeline.pipeline import DDDPipeline
import json
import os
import traceback
from ddd.formats.presentation.generic import Generic3DPresentation


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class RollbackImporter:
    """
    Monkey patches "import" to keep track of imported modules, in order to
    later remove and reload them if needed.
    """

    def __init__(self):
        "Creates an instance and installs as the global importer"
        self.previousModules = sys.modules.copy()
        self.realImport = __builtins__['__import__']
        __builtins__['__import__'] = self._import
        self.newModules = {}

    def _import(self, name, globals=None, locals=None, fromlist=[], *args):
        #print(fromlist)
        #print(args)
        #print(kwargs)
        #raise()
        result = self.realImport(*(name, globals, locals, fromlist, *args))
        self.newModules[name] = 1
        return result

    def uninstall(self):
        for modname in self.newModules.keys():
            if not modname in self.previousModules:
                # Force reload when modname next imported
                try:
                    del(sys.modules[modname])
                    logger.info("Uninstalled module from sys.modules for reload: %s", modname)
                except Exception as e:
                    logger.warn("Could not uninstall module from sys.modules for reload: %s", modname)
        __builtins__['__import__'] = self.realImport


class FileChangedEventHandler(FileSystemEventHandler):

    def __init__(self, dddserver):
        super().__init__()
        self.dddserver = dddserver

    def on_any_event(self, ev):

        logger.info("File monitoring event: %s", ev)

        if not isinstance(ev, FileModifiedEvent):
            return
        if not ev.src_path.endswith(".py"):
            return

        if self.dddserver.running:
            logger.warn("Pipeline is already running (ignoring reload due to saved file)")
            return

        logger.info("Reloading pipeline.")
        try:
            self.dddserver.pipeline_reload()
        except Exception as e:
            logger.warn("Could not reload pipeline: %s", e)
            print(traceback.format_exc())
            return

        # TODO: Move this interface to ServerServeCommand
        asyncio.run_coroutine_threadsafe(self.dddserver.pipeline_run(), self.dddserver.loop)


class ServerServeCommand(DDDCommand):

    def parse_args(self, args):

        #program_name = os.path.basename(sys.argv[0])
        parser = argparse.ArgumentParser()  # description='', usage = ''

        #parser.add_argument("-w", "--worker", default=None, help="worker (i/n)")
        parser.add_argument("script", help="script or pipeline entry point")

        args = parser.parse_args(args)

        self.script = args.script

        self.files_changed = False
        self.rollbackImporter = None

        self._results = {}

    def show(self, obj, label=None):
        logger.info("Server processing generated result (show): label=%s %s", label, obj)
        loop = self.loop

        result_index = len(self._results) + 1
        self._results[result_index] = {'data': obj.copy(),
                                       'label': label}

        asyncio.run_coroutine_threadsafe(self.result_send(None, result_index), self.loop)

    def run(self):

        logger.info("Starting DDD server tool API (ws://).")

        D1D2D3Bootstrap._instance._unparsed_args = None

        # Disable builtin rendering
        logger.info("Disabling builtin rendering.")
        D1D2D3Bootstrap.renderer = self.show

        self.loop = asyncio.get_event_loop()

        # Create pipeline
        self.pipeline = None
        self.running = False

        # Start python-socketio
        self.sio = socketio.AsyncServer(cors_allowed_origins='*')
        app = web.Application()
        self.sio.attach(app)

        async def index(request):
            """
            """
            #with open('index.html') as f:
            #    return web.Response(text=f.read(), content_type='text/html')
            return web.Response(text="DDD SocketIO API Server", content_type='text/html')

        @self.sio.event
        def connect(sid, environ):
            logger.info("Websocket connect: %s %s", sid, environ)

        @self.sio.event
        async def chat_message(sid, data):
            logger.info("Websocket chat_message: %s %s", sid, data)

        @self.sio.event
        async def status_get(sid, data):
            logger.info("Websocket status_get: %s %s", sid, data)
            status = self.status_get()
            #logger.debug("Sending status: %s", status)
            await self.sio.emit('status', status, room=sid)

        @self.sio.event
        async def result_get(sid, data):
            logger.info("Websocket result_get: %s %s", sid, data)

            if self.running:
                return

            await self.result_send(sid)

        @self.sio.event
        def disconnect(sid):
            logger.info('Websocket disconnect: %s', sid)

        #app.router.add_static('/static', 'static')
        app.router.add_get('/', index)

        # Run pipeline initially
        asyncio.ensure_future(self.pipeline_init())

        try:
            web.run_app(app, host="0.0.0.0", port=8085)
            #web.run_app(app, host="127.0.0.1", port=8085)
            #web.run_app(app, host="localhost", port=8085)
        except KeyboardInterrupt:
            logger.info("Interrupted by user.")


    def status2_get(self):
        status = {
            'script': self.script,
            'status': {
                'running': self.running,
            }
        }

    def status_get(self):

        tasks_sorted = self.pipeline.tasks_sorted()

        tasks = [{
            'name': t.name,
            'order': t.order,
            'order_num': t._order_num,

            'path': t.path,
            'condition': t.condition != None,
            'selector': t.selector.selector if t.selector else None,
            'filter': t.filter != None,
            'recurse': t.recurse,
            'replace': t.replace,

            'cache': t.cache,
            'cache_override': t.cache_override,

            #'funcargs': t._funcargs,
            'description': t._funcargs[0].__doc__,

            'params': t.params,

            'run_seconds': t._run_seconds,
            'run_selected': t._run_selected,
        } for t in tasks_sorted]

        # Serialize and deserialize to ensure data is JSON serializable (converts objects to strings)
        data = json.loads(json.dumps(self.pipeline.data, default=str))

        status = {
            'script': self.script,
            'data': data,
            'tasks': tasks
        }

        return status

    def result_get(self, result_index=0):

        if result_index:
            result = self._results[result_index]
        else:
            result = {'data': self.pipeline.root, 'label': 'DDDServer Root Node'}

        # Process result
        #if isinstance(root, DDDObject2):
        #    root = root.copy3(copy_children=True)
        #root = root.find("/Elements3")

        # Export
        try:
            result_node = Generic3DPresentation.present(result['data'])
            result_data = result_node.save(".glb")
        except Exception as e:
            logger.error("Could not produce result model (.glb): %s", e)
            print(traceback.format_exc())
            result_data = None

        return {'data': result_data,
                'label': result['label']}

    async def result_send(self, sid=None, result_index=0):

        result = self.result_get(result_index)
        #return status
        if result and result['data']:
            logger.info("Sending result: %s bytes", len(result['data']) if result['data'] else None)
            await self.sio.emit('result', {"key": result_index, 'data': result['data'], "label": result['label']}, room=sid)
        else:
            logger.info("No result to send.")

    async def pipeline_init(self):
        #self.pipeline = DDDPipeline([self.script], name="DDD Server Build Pipeline")
        self.pipeline_reload()

        # Start file monitoring
        self.start_file_monitoring()

        # Run pipeline initially
        await self.pipeline_run()

    def pipeline_reload(self):
        #self.pipeline = None
        if self.rollbackImporter:
            self.rollbackImporter.uninstall()
        else:
            self.rollbackImporter = RollbackImporter()

        try:
            del(sys.modules[self.script.replace(".py", "")])
        except Exception as e:
            pass

        self.pipeline = DDDPipeline(self.script, name="DDD Server Build Pipeline")

    async def pipeline_run(self):

        if self.running:
            logger.warn("Pipeline already running.")
            return

        self.running = True

        with futures.ThreadPoolExecutor() as pool:
            logger.info("Running in thread pool.")

            run_result = await self.loop.run_in_executor(pool, self.pipeline_run_blocking)
            logger.info("Thread pool result: %s", run_result)

        self.running = False

        asyncio.ensure_future(self.result_send())

    def pipeline_run_blocking(self):
        try:
            self.pipeline.run()
        except Exception as e:
            logger.warn("Error running pipeline: %s", e)
            print(traceback.format_exc())
            return False

        return True

    def start_file_monitoring(self):

        event_handler = FileChangedEventHandler(self)

        path = self.script

        logger.info("Starting file monitoring.")
        observer = Observer()

        # Main file
        #observer.schedule(event_handler, path, recursive=False)

        # Main file dir recursively
        observer.schedule(event_handler, os.path.dirname(os.path.abspath(path)), recursive=True)

        # Imported files
        '''
        for modname in self.rollbackImporter.newModules.keys():
            logger.info("Monitoring: %s", modname)
            try:
                observer.schedule(event_handler, sys.modules[modname].__file__, recursive=False)
            except Exception as e:
                logger.info(e)
        '''

        observer.start()

        #try:
        #    while True:
        #        time.sleep(1)
        #except KeyboardInterrupt:

        # Stop file monitoring
        #observer.stop()
        #observer.join()
