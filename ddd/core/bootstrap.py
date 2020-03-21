# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020
import logging
import os
import sys
import argparse


class D1D2D3Bootstrap():

    def __init__(self):
        self.debug = True

    def initialize_logging(self):

        default_level = logging.INFO if not self.debug else logging.DEBUG
        #logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=default_level)
        #logging.basicConfig(format='%(asctime)s - %(levelname)s - %(name)s - %(message)s', level=default_level)
        #logging.basicConfig(format='%(asctime)s - %(levelname)s - %(name)s - %(message)s', level=default_level)

        if self.debug:
            logging.basicConfig(format='%(asctime)s - %(levelname)s - %(module)s - %(message)s', level=default_level)
            #logging.basicConfig(format='%(asctime)s - %(levelname)s - %(name)s - %(message)s', level=default_level)
        else:
            #logging.basicConfig(format='%(asctime)s %(message)s', level=default_level)
            logging.basicConfig(format='%(message)s', level=default_level)


        #warnings.filterwarnings(action='ignore',module='.*paramiko.*')
        logging.getLogger('paramiko.transport').setLevel(logging.WARN)
        logging.getLogger('invoke').setLevel(logging.WARN)

    def parse_args(self, st):

        #program_name = os.path.basename(sys.argv[0])
        parser = argparse.ArgumentParser()  # description='', usage = ''

        parser.add_argument("-d", "--debug", action="store_true", default=False, help="debug logging")

        #exclusive_grp = parser.add_mutually_exclusive_group()
        #exclusive_grp.add_argument('--color', action='store_true', dest='color', default=None, help='color')
        #exclusive_grp.add_argument('--no-color', action='store_false', dest='color', help='no-color')

        # Tasks to run (short, long, area, catalog...) - depends on script (define tasks?)
        # Catalog tasks (common)
        # Overwrite / Fail / Skip task
        # Run only 1 chunk / task
        # Show / no show / custom debug shows  | logging categories
        # Timings
        # Exoort instance-markers and/or instance-geometry by default

        parser.add_argument("script", nargs='?', default=None, help="script to run")
        #parser.add_argument("rest", nargs='*')

        args, unknown = parser.parse_known_args()  # sys.argv[1:]

        self.debug = args.debug
        self.script = args.script

        command = command_class(st.ctx)
        command.parse_args(unknown)

    def run(self):
        pass

    def main(self):
        pass


if __name__ == "__main__":
    # Run

    ddd_bootstrap = D1D2D3Bootstrap()

    ddd_bootstrap.parse_args()

    ddd_bootstrap.initialize_logging()

    ddd_bootstrap.main()

    return 0
