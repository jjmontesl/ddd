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
    poster = poster.triangulate().twosided()
    poster = poster.material(ddd.MAT_TEST)  # ddd.mats.paper_coarse)
    poster = ddd.uv.map_cubic(poster, scale=[1 / width, 1 / height])
    poster = poster.rotate(ddd.ROT_FLOOR_TO_FRONT).translate([-width/2, 0, 0])
    return poster

def poster_fold(width=0.4, height=0.6):
    """
    Poster with a fold at a corner at the top.
    """
    pass


def poster_wrinkled(width=0.4, height=0.6):
    """
    Poster with wrinkles
    """
    pass



def poster_ripped(width=0.4, height=0.6, hole_size_n=[0.5, 0.4], hole_center_n=[0.9, 0.1]):
    """
    Poster with a missing (teared apart) part. UVs are mapped to the full poster so the image it appears ripped.
    """
    poster = ddd.rect([width, height], name="Poster Ripped")
    hole = hole_broken(hole_size_n[0] * width, hole_size_n[1] * height, noise_scale=hole_size_n[0] * width * 0.1)

    hole = hole.recenter().translate([hole_center_n[0] * width, hole_center_n[1] * height])
    #ddd.group([poster, hole]).show()
    poster = poster.subtract(hole)

    poster = poster.triangulate().twosided()
    poster = poster.material(ddd.MAT_TEST)  # ddd.mats.paper_coarse)
    poster = ddd.uv.map_cubic(poster, scale=[1 / width, 1 / height])
    poster = poster.rotate(ddd.ROT_FLOOR_TO_FRONT).translate([-width/2, 0, 0])
    return poster

def image_posterize():
    pass

def image_age():
    pass


def text_note(width=0.210, height=0.297, text="This note is misteriously empty."):
    """
    A paper note.
    Paper is upright centered and facing -Y.
    """
    item = ddd.rect([width, height], name="Note")
    item = item.triangulate().twosided()
    item = item.material(ddd.mats.paper)
    item = ddd.uv.map_cubic(item, scale=[1 / width, 1 / height])
    item = item.rotate(ddd.ROT_FLOOR_TO_FRONT).translate([-width/2, 0, -height * 0.5])
    item.set('ddd:text', text)
    return item

def text_note_teared(width=0.210, height=0.297, tear_height_norm=0.75, text="This note is misteriously empty."):
    """
    Paper note with a missing part.
    Paper is upright centered and facing -Y. The center is the center of the full note (as if it included the teared off part).
    """
    item = ddd.rect([width, height], name="Note Teared")

    hole = hole_broken(width * 2, height * 2, noise_scale=width * 0.05)
    hole = hole.recenter().translate([width * 0.5, -tear_height_norm * height])

    ddd.group([item, hole]).show()
    item = item.subtract(hole)

    item = item.triangulate().twosided()
    item = item.material(ddd.mats.paper)
    item = ddd.uv.map_cubic(item, scale=[1 / width, 1 / height])
    item = item.rotate(ddd.ROT_FLOOR_TO_FRONT).translate([-width/2, 0, -height * 0.5])
    return item
