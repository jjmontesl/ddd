# Jose Juan Montes 2019-2020

import math
import random

import trimesh

from ddd.ddd import ddd
from ddd.pack.shapes.holes import hole_broken
from ddd.pipeline.decorators import dddtask


@dddtask()
def pipeline_start(pipeline, root):

    item = hole_broken()

    root.append(item)

    root.show()
