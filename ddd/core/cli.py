# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging
import os
import sys
import argparse
from ddd.core.exception import DDDException
import importlib
from collections import OrderedDict


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class D1D2D3Bootstrap():

    _logging_initialized = False

    export_marker = True
    export_mesh = False

    # TODO: make classes that provide help, leave "run" for user scripts
    commands = OrderedDict(
        {"catalog-show": ("ddd.catalog.commands.show", "Show catalog"),
        "catalog-export": ("ddd.catalog.commands.export", "Export catalog to file"),
        "catalog-clear": ("ddd.catalog.commands.clear", "Clear catalog"),
        "osm-build": ("ddd.osm.commands.build.OSMBuildCommand", "Build a scene or tile using the OSM Builder"),
        "osm-query": ("ddd.osm.commands.query", None),
        "run": ("ddd.core.commands.run", "Runs a user-given script (default)"),  # default
        })

    def __init__(self):
        self.debug = True

    @staticmethod
    def initialize_logging(debug=False):

        if D1D2D3Bootstrap._logging_initialized:
            return

        D1D2D3Bootstrap._logging_initialized = True

        default_level = logging.INFO if not debug else logging.DEBUG
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
        logger.debug("DDD debug logging enabled.")


    def parse_args(self, st):

        description = "DDD123 Procedural geometry and mesh scene generator.\n\n"

        for k, (v, d) in self.commands.items():
            description = description + ("  %20s %s\n" % (k, d))

        #program_name = os.path.basename(sys.argv[0])
        parser = argparse.ArgumentParser(description=description, add_help=False, formatter_class=argparse.RawTextHelpFormatter)  #usage = ''

        parser.add_argument("-d", "--debug", action="store_true", default=False, help="debug logging")
        parser.add_argument("-h", "--help", action="store_true", default=False, help="show help and exit")
        parser.add_argument("-v", "--visualize-errors", action="store_true", default=False, help="visualize objects that caused exceptions")
        parser.add_argument("-o", "--overwrite", action="store_true", default=False, help="overwrite output files")

        parser.add_argument("-c", "--config", action="append", help="load config file before running")

        parser.add_argument("--export-meshes", action="store_true", default=False, help="export instance meshes")
        parser.add_argument("--export-markers", action="store_true", default=False, help="export instance markers (default)")
        parser.add_argument("--export-normals", action="store_true", default=False, help="export normals")

        parser.add_argument("command", help="script or command to run", nargs="?")

        #sp = parser.add_subparsers(dest="script", description="script or command to run")
        #for k, v in self.commands.items():
        #    sp.add_parser(k)


        #exclusive_grp = parser.add_mutually_exclusive_group()
        #exclusive_grp.add_argument('--color', action='store_true', dest='color', default=None, help='color')
        #exclusive_grp.add_argument('--no-color', action='store_false', dest='color', help='no-color')

        # Tasks to run (short, long, area, catalog...) - depends on script (define tasks?)
        # Workers/ Multiprocess
        # Catalog tasks (common: generate catalog, show catalog)
        # Overwrite / Fail / Skip task
        # Generate GIS GeoJSON with chunks and info
        # Generate classification input data
        # Generate custom data (customs_1d, etc)
        # Run only 1 chunk / task
        # Show / no show / custom debug shows  | logging categories
        # Timings
        # Exoort instance-markers and/or instance-geometry by default

        #parser.add_argument("rest", nargs='*')

        args, unparsed_args = parser.parse_known_args()  # sys.argv[1:]

        self.debug = args.debug
        self.command = args.command
        self.configs = args.config if args.config else []
        self.visualize_errors = args.visualize_errors
        self.overwrite = args.overwrite

        if args.help:
            if not self.command:
                print(parser.format_help())
                sys.exit(0)
            else:
                unparsed_args = unparsed_args + ['-h']

        D1D2D3Bootstrap.export_marker = args.export_markers
        D1D2D3Bootstrap.export_mesh = args.export_meshes
        if not D1D2D3Bootstrap.export_mesh and not D1D2D3Bootstrap.export_marker:
            D1D2D3Bootstrap.export_marker = True

        D1D2D3Bootstrap.export_normals = args.export_normals

        if self.command in self.commands:
            self.command = self.commands[self.command][0]

        self._unparsed_args = unparsed_args

    def runconfig(self):
        for configname in self.configs:
            logger.info("Running config file: %s", configname)
            self.runcommand(configname)

    def runcommand(self, command):
        #data =
        #compiled = compile()

        if not command:
            return

        try:

            D1D2D3Bootstrap._instance = self
            if command.endswith(".py"):
                command = command[:-3]

            # Try to import as module
            result = None

            try:
                script_abspath = os.path.abspath(command)
                script_dirpath = os.path.dirname(script_abspath)
                sys.path.append(script_dirpath)
                importlib.import_module(command)  #, globals={'ddd_bootstrap': self})
                result = True
            except ModuleNotFoundError as e:
                result = False

            if not result:
                modulename = ".".join(command.split(".")[:-1])
                classname = command.split(".")[-1]
                if modulename:
                    try:
                        modul = importlib.import_module(modulename)
                        clazz = getattr(modul, classname)
                        cliobj = clazz()
                        cliobj.parse_args(self._unparsed_args)
                        cliobj.run()
                        result = True
                    except AttributeError as e:
                        pass

                if not result:
                    modulename = command
                    importlib.import_module(modulename)
                    result = True

            # Try to import as class

            #__import__(command[:-3], globals={'ddd_bootstrap': self})

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
    D1D2D3Bootstrap.initialize_logging(debug=ddd_bootstrap.debug)
    ddd_bootstrap.runconfig()

    logger.info("Running %s", ddd_bootstrap.command)
    ddd_bootstrap.runcommand(ddd_bootstrap.command)


if __name__ == "__main__":
    main()


