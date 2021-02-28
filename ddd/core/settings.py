# ddd - DDD123
# Library for simple scene modelling.
# Jose Juan Montes and Contributors 2019-2021

import logging
import os
import sys


# Get instance of logger for this module
logger = logging.getLogger(__name__)

DDD_EXECUTABLE = sys.executable

DDD_BASEDIR = './'  # Stress we are using the working directory and avoids /

DDD_DATADIR = DDD_BASEDIR + 'data/'
if 'DDD_DATADIR' in os.environ:
    DDD_DATADIR = os.environ['DDD_DATADIR']
DDD_DATADIR = os.path.abspath(DDD_DATADIR) + "/"

# Allow config files to include other files
def DDD_INCLUDE(config_file):
    config_file = os.path.expanduser(config_file)
    if (os.path.exists(config_file)):
        sys.stderr.write("Loading config from: %s\n" % config_file)
        exec(open(config_file).read(), locals(), globals())


DDD_INCLUDE('~/.ddd.conf')

DDD_INCLUDE(DDD_DATADIR + '/ddd.conf')

