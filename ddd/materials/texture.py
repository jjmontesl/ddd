# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

from shapely import geometry
from trimesh.path import segments
from trimesh.scene.scene import Scene, append_scenes
from trimesh.base import Trimesh
from trimesh.path.path import Path
from trimesh.visual.material import SimpleMaterial
from trimesh import creation, primitives, boolean
import trimesh
from csg.core import CSG
from csg import geom as csggeom
import random
from ddd.ddd import ddd
import noise
from ddd.georaster import ElevationChunk
import pyproj
import math


