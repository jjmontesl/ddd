# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging
import os
import sys
import argparse
from ddd.core.exception import DDDException
import importlib


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class D1D2D3Bootstrap():

    _logging_initialized = False

    export_marker = True
    export_mesh = False

    commands = {"catalog-show": "ddd.prefab.commands.show",  # TODO: replace with unique command with options (show, export, dump...)
                "catalog-export": "ddd.prefab.commands.export",
                "osm-gen": "ddd.osm.commands.gen",
                "osm-query": "ddd.osm.commands.query",
                }

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

        #program_name = os.path.basename(sys.argv[0])
        parser = argparse.ArgumentParser()  # description='', usage = ''

        parser.add_argument("-d", "--debug", action="store_true", default=False, help="debug logging")
        parser.add_argument("-v", "--visualize-errors", action="store_true", default=False, help="visualize objects that caused exceptions")
        parser.add_argument("-o", "--overwrite", action="store_true", default=False, help="overwrite output files")

        parser.add_argument("--export-mesh", action="store_true", default=False, help="export instance meshes")
        parser.add_argument("--export-marker", action="store_true", default=False, help="export instance markers (default)")
        parser.add_argument("--export-normals", action="store_true", default=False, help="export normals")

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

        parser.add_argument("script", help="script or command to run")
        #parser.add_argument("rest", nargs='*')

        args, unparsed_args = parser.parse_known_args()  # sys.argv[1:]

        self.debug = args.debug
        self.script = args.script
        self.visualize_errors = args.visualize_errors
        self.overwrite = args.overwrite

        D1D2D3Bootstrap.export_marker = args.export_marker
        D1D2D3Bootstrap.export_mesh = args.export_mesh
        if not D1D2D3Bootstrap.export_mesh and not D1D2D3Bootstrap.export_marker:
            D1D2D3Bootstrap.export_marker = True

        D1D2D3Bootstrap.export_normals = args.export_normals

        if self.script in self.commands:
            self.script = self.commands[self.script]

        self._unparsed_args = unparsed_args

    def run(self):
        #data =
        #compiled = compile()
        script_abspath = os.path.abspath(self.script)
        script_dirpath = os.path.dirname(script_abspath)
        logger.info("Running %s", script_abspath)

        sys.path.append(script_dirpath)
        try:
            D1D2D3Bootstrap._instance = self
            if self.script.endswith(".py"):
                self.script = self.script[:-3]
            importlib.import_module(self.script)  #, globals={'ddd_bootstrap': self})
            #__import__(self.script[:-3], globals={'ddd_bootstrap': self})
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
    ddd_bootstrap.run()


if __name__ == "__main__":
    main()


