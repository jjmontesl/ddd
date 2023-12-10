# ddd - DDD123
# Library for simple scene modelling.
# Jose Juan Montes and Contributors 2019-2021

import os
import sys

# Data properties (these properties are shared with ddd / pipeline)
# TODO: Remove this global variable (?) + normalize settings between settings module, ddd, dddbootstrap and pipeline
data = {}

# Allow config files to include other files
def DDD_INCLUDE(config_file):
    config_file = os.path.expanduser(config_file)
    if (os.path.exists(config_file)):
        sys.stderr.write("Loading config from: %s\n" % config_file)
        exec(open(config_file).read(), locals(), globals())

def DDD_SETTINGS_GET(key, default=None):
    return globals().get(key, default)

def DDD_NORMALIZE_PATHS():
    global DDD_DATADIR
    DDD_DATADIR = os.path.abspath(os.path.expanduser(DDD_DATADIR)) + "/"
    global DDD_WORKDIR
    DDD_WORKDIR = os.path.abspath(os.path.expanduser(DDD_WORKDIR)) + "/"

# Global settings
DDD_EXECUTABLE = sys.executable

DDD_WORKDIR = './'

DDD_DATADIR = os.path.join(os.path.dirname(DDD_EXECUTABLE), "/../../data/")  # Tested to at least work in dev environment (no need for this setting on ~/.ddd.conf)


# Load environment variables starting with DDD_
for k, v in os.environ.items():
    if k.startswith('DDD_'):
        globals()[k] = v

DDD_NORMALIZE_PATHS()

# Default settings


# Load user settings
DDD_INCLUDE('~/.ddd.conf')

# Load extra settings in the data directory (recommended for data-related settings)
DDD_INCLUDE(os.path.join(DDD_DATADIR, '/ddd.conf'))


DDD_NORMALIZE_PATHS()


