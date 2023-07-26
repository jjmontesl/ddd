# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging

from ddd.ddd import ddd
from trimesh import transformations
from ddd.math.vector3 import Vector3

from ddd.ops.layout import DDDLayout, VerticalDDDLayout
from ddd.pack.shapes.holes import hole_broken


# Get instance of logger for this module
logger = logging.getLogger(__name__)


def poster_flat(width=0.4, height=0.6):
    """
    Poster is upright centered and facing -Y, on the XY plane.
    """
    poster = ddd.rect([width, height], name="Poster")
    poster = poster.triangulate()
    poster = poster.material(ddd.MAT_TEST)  # ddd.mats.paper_coarse)
    poster = ddd.uv.map_cubic(poster, scale=[1 / width, 1 / height])
    poster = poster.rotate(ddd.ROT_FLOOR_TO_FRONT).translate([-width/2, 0, 0])
    return poster

def poster_fold(width=0.4, height=0.6):
    """
    Poster with a fold at the top.
    """
    pass

def poster_ripped(width=0.4, height=0.6, hole_size_n=[0.5, 0.4], hole_center_n=[0.9, 0.1]):
    """
    Poster with a missing part.
    """
    poster = ddd.rect([width, height], name="Poster Ripped")
    hole = hole_broken(hole_size_n[0] * width, hole_size_n[1] * height, noise_scale=hole_size_n[0] * width * 0.1)

    hole = hole.recenter().translate([hole_center_n[0] * width, hole_center_n[1] * height])
    ddd.group([poster, hole]).show()
    poster = poster.subtract(hole)

    poster = poster.triangulate()
    poster = poster.material(ddd.MAT_TEST)  # ddd.mats.paper_coarse)
    poster = ddd.uv.map_cubic(poster, scale=[1 / width, 1 / height])
    poster = poster.rotate(ddd.ROT_FLOOR_TO_FRONT).translate([-width/2, 0, 0])
    return poster


def image_posterize():
    pass

def image_age():
    pass

