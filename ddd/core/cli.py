# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020
import logging
import os
import sys
import argparse
from abc import abstractstaticmethod


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class D1D2D3Bootstrap():

    def __init__(self):
        self.debug = True

    @staticmethod
    def initialize_logging(debug=False):

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

        #exclusive_grp = parser.add_mutually_exclusive_group()
        #exclusive_grp.add_argument('--color', action='store_true', dest='color', default=None, help='color')
        #exclusive_grp.add_argument('--no-color', action='store_false', dest='color', help='no-color')

        # Tasks to run (short, long, area, catalog...) - depends on script (define tasks?)
        # Workers/ Multiprocess
        # Catalog tasks (common)
        # Overwrite / Fail / Skip task
        # Run only 1 chunk / task
        # Show / no show / custom debug shows  | logging categories
        # Timings
        # Exoort instance-markers and/or instance-geometry by default

        parser.add_argument("script", help="script to run")
        #parser.add_argument("rest", nargs='*')

        args, unknown = parser.parse_known_args()  # sys.argv[1:]

        self.debug = args.debug
        self.script = args.script

    def run(self):
        #data =
        #compiled = compile()
        script_abspath = os.path.abspath(self.script)
        script_dirpath = os.path.dirname(script_abspath)
        logger.info("Running %s", script_abspath)

        sys.path.append(script_dirpath)
        __import__(self.script[:-3])


def main():
    ddd_bootstrap = D1D2D3Bootstrap()
    ddd_bootstrap.parse_args(sys.argv)
    D1D2D3Bootstrap.initialize_logging(debug=ddd_bootstrap.debug)
    ddd_bootstrap.run()


if __name__ == "__main__":
    main()


