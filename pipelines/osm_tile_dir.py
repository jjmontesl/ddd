# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020

import sys

import pyproj

from ddd.ddd import ddd
from ddd.geo import terrain
from ddd.osm import osm
from ddd.osm.osm import project_coordinates
from ddd.pipeline.decorators import dddtask
import logging
import glob
import re
import os
import shutil


logger = logging.getLogger(__name__)

"""
Called from local data dir as:

    ddd ~/git/ddd/pipelines/osm_tile_dir.py
"""

source_dir = "./output/ddd_http/"
source_regexp = r"ddd_http_([0-9]+)_([0-9]+)_([0-9]+)(.*)"

target_pattern = "./output/ddd_http/{z}/{x}/{y}{remainder}"

logger.info("Moving OSM output results from: %s to %s" % (source_dir, target_pattern))


listing = (glob.glob(source_dir + "*.glb") + glob.glob(source_dir + "*.json") +
           glob.glob(source_dir + "*.png") + glob.glob(source_dir + "*.jpg"))
for filename in listing:

    dirname = os.path.dirname(filename)
    basename = os.path.basename(filename)

    matches = re.match(source_regexp, basename)

    if matches:
        data = {"z": matches.group(1),
                "x": matches.group(2),
                "y": matches.group(3),
                "remainder": matches.group(4)}
        targetname = target_pattern.format(**data)
        logger.info("%s -> %s" % (filename, targetname))
        shutil.move(filename, targetname)


