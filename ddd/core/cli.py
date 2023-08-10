# ddd - DDD123
# Library for simple scene modelling.
# Jose Juan Montes and Contributors 2019-2021

import argparse
from collections import OrderedDict
import importlib
import logging
import os
import sys

from ddd.core.exception import DDDException

from ddd.core import settings

# Get instance of logger for this module
logger = logging.getLogger(__name__)


class D1D2D3Bootstrap():

    _logging_initialized = False

    # Config ideally shall be an object set to ddd or ctx if anything? also check ddd.conf, settings, (dir + home + data dir???!)  pipeline conf...
    export_marker = True
    export_mesh = False

    commands = OrderedDict({
        "catalog-show": ("ddd.catalog.commands.show.CatalogShowCommand", "Show catalog"),
        "catalog-export": ("ddd.catalog.commands.export.CatalogExportCommand", "Export catalog to file"),
        "catalog-clear": ("ddd.catalog.commands.clear", "Clear catalog"),
        "font-generate": ("ddd.text.commands.fontatlasgen.FontAtlasGenerateCommand", "Generate a font atlas"),
        "texture-pack": ("ddd.materials.commands.texturepack.TexturePackCommand", "Pack textures into texture atlases"),
        "geo-raster-collect": ("ddd.geo.commands.georastercollect.GeoRasterCollectCommand", "Collect georaster files and generate config."),
        "geo-raster-coverage": ("ddd.geo.commands.georastercoverage.GeoRasterCoverageCommand", "Generate a georaster coverage map."),
        "geo-population": ("ddd.geo.commands.geopopulation.GeoPopulationCommand", "Query the population model."),
        "serve": ("ddd.server.commands.serve.ServerServeCommand", "Start the DDD Tool API for a pipeline."),
        "describe": ("ddd.core.commands.describe.DescribeCommand", "Describes a pipeline or script."),
        "run": ("ddd.core.commands.run.RunCommand", "Runs a given pipeline or script (default)."),  # default
        })

    def __init__(self):
        self.debug = True

    @staticmethod
    def initialize_logging(debug=False, warnonly=False):

        if D1D2D3Bootstrap._logging_initialized:
            return

        D1D2D3Bootstrap._logging_initialized = True

        default_level = logging.WARN if warnonly else (logging.INFO if not debug else logging.DEBUG)
        #logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=default_level)
        #logging.basicConfig(format='%(asctime)s - %(levelname)s - %(name)s - %(message)s', level=default_level)
        #logging.basicConfig(format='%(asctime)s - %(levelname)s - %(name)s - %(message)s', level=default_level)

        if debug:
            logging.basicConfig(format='%(asctime)s - %(levelname)s - %(module)s - %(message)s', level=default_level)
            #logging.basicConfig(format='%(asctime)s - %(levelname)s - %(name)s - %(message)s', level=default_level)
        else:
            #logging.basicConfig(format='%(asctime)s %(message)s', level=default_level)
            logging.basicConfig(format='%(asctime)s  %(message)s', level=default_level)

        #warnings.filterwarnings(action='ignore',module='.*paramiko.*')
        logging.getLogger("trimesh").setLevel(logging.INFO)
        logging.getLogger('paramiko.transport').setLevel(logging.WARN)
        logging.getLogger('invoke').setLevel(logging.WARN)

        logger.info("DDD logging initialized.")
        logger.debug("DDD debug logging enabled (%d settings).", len(settings.__dict__))


    def parse_args(self, st):

        description = "DDD123 Procedural geometry and mesh scene generator.\n\n"

        for k, (v, d) in self.commands.items():
            description = description + ("  %20s %s\n" % (k, d))

        #program_name = os.path.basename(sys.argv[0])
        parser = argparse.ArgumentParser(description=description, add_help=False, formatter_class=argparse.RawTextHelpFormatter)  #usage = ''

        parser.add_argument("-d", "--debug", action="store_true", default=False, help="debug logging")
        parser.add_argument("-h", "--help", action="store_true", default=False, help="show help and exit")
        parser.add_argument("-v", "--visualize-errors", action="store_true", default=False, help="visualize object that caused exception if available")
        parser.add_argument("-o", "--overwrite", action="store_true", default=False, help="overwrite output files")

        parser.add_argument("-r", "--profile", type=str, default=False, help="profile execution writing results to filename")

        parser.add_argument("-c", "--config", action="append", help="load config file before running")
        parser.add_argument("-p", action="append", type=str, nargs="?", dest="properties", default=None, help="set property (key=value)")

        parser.add_argument("--export-meshes", action="store_true", default=False, help="export instance meshes")
        parser.add_argument("--export-markers", action="store_true", default=False, help="export instance markers (default)")

        parser.add_argument("--no-normals", dest="export_normals", action="store_false", default=True, help="don't export normals")
        parser.add_argument("--no-textures", dest="export_textures", action="store_false", default=True, help="don't export textures")

        parser.add_argument("--renderer", default="pyglet", nargs="?", choices=('pyrender', 'pyglet', 'none'), help="renderer backend (default: %(default)s)")

        parser.add_argument("--naming", default="name", nargs="?", choices=('path', 'name_numbered', 'name_unique'), help="node naming for export (default: %(default)s)")

        parser.add_argument("--catalog-overwrite", action="store_true", default=False, help="overwrite catalog items")
        parser.add_argument("--catalog-ignore", action="store_true", default=False, help="do not use catalog (read, write or store)")

        # Cache should be part of a more general pipeline build approach
        parser.add_argument("--cache-ro", action="store_true", default=False, help="disables pipeline cache writing")
        parser.add_argument("--cache-clear", action="store", nargs="?", default=None, const=(1, ), help="clear pipeline cache (from task order 1 or argument if set)")

        parser.add_argument("command", help="script or command to run", nargs="?")

        #sp = parser.add_subparsers(dest="script", description="script or command to run")
        #for k, v in self.commands.items():
        #    sp.add_parser(k)


        #exclusive_grp = parser.add_mutually_exclusive_group()
        #exclusive_grp.add_argument('--color', action='store_true', dest='color', default=None, help='color')
        #exclusive_grp.add_argument('--no-color', action='store_false', dest='color', help='no-color')

        #parser.add_argument("rest", nargs='*')

        args, unparsed_args = parser.parse_known_args()  # sys.argv[1:]

        self.debug = args.debug
        self.command = args.command
        self.command_class = None

        self.configs = args.config if args.config else []
        #self.configs = ['~/.ddd.conf', './ddd.conf'] + self.configs

        self.visualize_errors = args.visualize_errors
        self.overwrite = args.overwrite
        self.properties = args.properties

        self.help = args.help
        if self.help or not self.command:
            if not self.command:
                print(parser.format_help())
                sys.exit(0)
            else:
                #print(parser.format_help())  # prints general help before any per-command help
                unparsed_args = unparsed_args + ['-h']

        self.profile = args.profile

        D1D2D3Bootstrap.debug = self.debug

        D1D2D3Bootstrap.export_marker = args.export_markers
        D1D2D3Bootstrap.export_mesh = args.export_meshes
        #if not D1D2D3Bootstrap.export_mesh and not D1D2D3Bootstrap.export_marker:
        #    D1D2D3Bootstrap.export_marker = True

        D1D2D3Bootstrap.export_normals = args.export_normals
        D1D2D3Bootstrap.export_textures = args.export_textures
        D1D2D3Bootstrap.renderer = args.renderer

        D1D2D3Bootstrap.catalog_overwrite = args.catalog_overwrite
        D1D2D3Bootstrap.catalog_ignore = args.catalog_ignore

        D1D2D3Bootstrap.cache_clear = args.cache_clear
        if isinstance(D1D2D3Bootstrap.cache_clear, str):
            D1D2D3Bootstrap.cache_clear = tuple(int(v) for v in D1D2D3Bootstrap.cache_clear.split("."))

        D1D2D3Bootstrap.cache_ro = args.cache_ro

        D1D2D3Bootstrap.data = {}
        if args.properties:
            for prop in args.properties:
                key, value = prop.split("=", 1)
                D1D2D3Bootstrap.data[key] = value

        if self.command in self.commands:
            self.command_class = self.commands[self.command][0]
        else:
            unparsed_args = [self.command] + unparsed_args
            self.command = 'run'
            self.command_class = self.commands['run'][0]

        self._unparsed_args = unparsed_args

    def runconfig(self):
        for configname in self.configs:
            path = configname
            path = os.path.expanduser(path)
            path = os.path.abspath(path)
            if os.path.exists(path):
                logger.info("Running config file: %s", configname)
                #source = None
                #with open(path) as f:
                #    source = f.read()
                #exec(source, globals(), {'data': data})
                settings.DDD_INCLUDE(path)  # Uses DDD_INCLUDE from settings
                settings.DDD_NORMALIZE_PATHS()
            else:
                logger.warn("Config file not found: %s", configname)

        # Override default configs and loaded configs with command line parameters (originally in D1D2D3Bootstrap.data)
        data = settings.data
        data.update(D1D2D3Bootstrap.data)
        D1D2D3Bootstrap.data = data


    def runcommand(self, command):
        logger.info("Properties: %s", D1D2D3Bootstrap.data)
        if not self.profile:
            self._runcommand(command)
        else:
            import cProfile
            logger.warning("Profiling execution (WARNING this is SLOW) and saving results to: %s" % self.profile)
            cProfile.runctx("self._runcommand(command)", globals(), locals(), self.profile)

    def _runcommand(self, command):
        #data =
        #compiled = compile()

        if not command:
            return

        try:

            D1D2D3Bootstrap._instance = self
            if command.endswith(".py"):
                command = command[:-3]

            # Try to import as module
            modulename = ".".join(command.split(".")[:-1])
            classname = command.split(".")[-1]
            if modulename:
                modul = importlib.import_module(modulename)
                if hasattr(modul, classname):
                    clazz = getattr(modul, classname)
                    cliobj = clazz()
                    cliobj.parse_args(self._unparsed_args)
                    cliobj.run()

            '''
            result = None
            try:
                script_abspath = os.path.abspath(command)
                logger.debug("Running command: %s", script_abspath)
                script_dirpath = os.path.dirname(script_abspath)
                scriptname = os.path.basename(command)

                importlib.import_module(scriptname)  #, globals={'ddd_bootstrap': self})
                result = True
            except ModuleNotFoundError as e:
                result = False
            '''

            '''
            if not result:
                modulename = ".".join(command.split(".")[:-1])
                classname = command.split(".")[-1]
                if modulename:
                    modul = importlib.import_module(modulename)
                    if hasattr(modul, classname):
                        clazz = getattr(modul, classname)
                        cliobj = clazz()
                        cliobj.parse_args(self._unparsed_args)
                        cliobj.run()
                        result = True

                if not result:
                    modulename = command
                    importlib.import_module(modulename)
                    result = True

            # Try to import as class

            #__import__(command[:-3], globals={'ddd_bootstrap': self})
            '''

        except DDDException as e:
            logger.error("Error: %s (obj: %s)" % (e, e.ddd_obj))
            if e.ddd_obj and self.visualize_errors:
                e.ddd_obj.dump()
                try:
                    e.ddd_obj.show()
                except Exception as e:
                    logger.warn("Cannot show error object: %s", e)
            raise


def main():
    ddd_bootstrap = D1D2D3Bootstrap()
    ddd_bootstrap.parse_args(sys.argv)
    D1D2D3Bootstrap.initialize_logging(debug=ddd_bootstrap.debug, warnonly=ddd_bootstrap.help)
    ddd_bootstrap.runconfig()

    logger.info("Running %s", ddd_bootstrap.command_class)
    ddd_bootstrap.runcommand(ddd_bootstrap.command_class)


if __name__ == "__main__":
    main()


