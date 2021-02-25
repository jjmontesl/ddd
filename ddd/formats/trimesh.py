# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020-2021

import json
import logging
import math

from shapely import geometry, affinity, ops
from trimesh import transformations

from ddd.core.exception import DDDException
from ddd.core.cli import D1D2D3Bootstrap


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class TrimeshSceneFormat():

    @staticmethod
    def export_trimesh_scene(obj, path_prefix="", instance_mesh=True, instance_marker=False):

        pass