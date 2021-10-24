# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020

import glob
import re
import os
import shutil

from ddd.pipeline.decorators import dddtask
from ddd.core import settings

"""
Moves tile files to a subdirectory under a z/x/y structure.

Called from local data dir as:

    ddd ~/git/ddd/pipelines/osm_tile_dir.py
"""



@dddtask()
def pipeline_start(pipeline, root, logger):
    """
    """
    source_dir = os.path.join(settings.DDD_WORKDIR, "ddd_http/")
    source_regexp = r"ddd_http_([0-9]+)_([0-9]+)_([0-9]+)(.*)"

    target_pattern = settings.DDD_WORKDIR + "/ddd_http/{z}/{x}/{y}{remainder}"

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
            logger.info("%s -> %s" % (os.path.relpath(filename), os.path.relpath(targetname)))
            shutil.move(filename, targetname)


