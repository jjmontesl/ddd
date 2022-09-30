# ddd - D1D2D3
# Library for simple scene modelling.

import logging
import math
import random

import trimesh
from trimesh.path import entities

from ddd.ddd import ddd
from ddd.math.math import DDDMath
from ddd.math.vector3 import Vector3
from ddd.ops.height.height import CompositeHeightFunction
from ddd.ops.height.pathheight import BankingPathProfileHeightFunction, NodeBisectPathHeightFunction, PathHeightFunction
from ddd.pipeline.decorators import dddtask

import numpy as np

# Get instance of logger for this module
logger = logging.getLogger(__name__)


"""
Tests of Path3 Height tool, which manages path height including profile / camber, interpolation for transitions (curves and height).
"""

@dddtask()
def create_curves(pipeline, root):
    """
    Create several curves:
    """

    curves = ddd.node(name="Curves")

    # Straight Line
    curve = ddd.line([[0, 0, 0], [10, 0, 0]], name="Straight Line")
    #curves.append(curve)

    # Sharp angles

    # Circle

    # Flattened Path3 from Shapely: with segmented curves (arc_to()), and also angles

    # 3D (with Z) open Path3 from Shapely: with segmented curves (arc_to()), and also angles

    # 3D (with Z) closed Path3 from Shapely: with segmented curves (arc_to()), and also angles

    # 3D (with Z) open Path3 from Trimesh: with splines/arcs and also angles

    # 3D (with Z) closed Path3 from Trimesh: with splines/arcs and also angles

    root.append(curves)


@dddtask()
def create_pathheights_for_curves():
    pass


@dddtask()
def track(pipeline, root):

    # TODO: second point is colinear if we use [7.0, 21.0], and the division gets removed in the buffer operation, which is sometimes not desired
    line = ddd.point([3, 25, 4]).line_to([7.01, 21.01, 4]).line_to([14, 14, 2]).arc_to([14, 6, 0], [10, 10], False, 8).line_to([4, -4, 0])

    path = ddd.path3(line)
    root.append(path)

    track = line.buffer(2.0).triangulate()
    track = ddd.meshops.subdivide_to_grid(track, 0.25)

    #path_smoothed = ddd.path3(line)
    #entity, control = trimesh.path.simplify.points_to_spline_entity(list(line.geom.coords), smooth=0.5)  # , count=None)
    #path_smoothed.path3 = trimesh.path.path.Path3D([entity], control)

    #path_smoothed = ddd.paths.from_points_spline(line)
    path_smoothed = ddd.paths.from_points_heuristic(line, distance=5)
    #path_smoothed = path
    #path_smoothed = ddd.paths.path_to_arcs(path_smoothed)  # , tolerance=.0001)

    for i, c in enumerate(line.coords_iterator()):
        perp = line.vertex_bisector(i, length=1.0)
        root.append(perp.material(ddd.MAT_HIGHLIGHT))

    #print(path_smoothed.path3.entities)
    root.append(path_smoothed.material(ddd.MAT_HIGHLIGHT))

    line_fine = path_smoothed.discretize(distance=0.2).to_line()

    height_func = CompositeHeightFunction([
        #PathHeightFunction(line_fine),
        NodeBisectPathHeightFunction(line_fine),
        BankingPathProfileHeightFunction(line_fine, {
            'banking_ext_h': 5.0,
            'banking_int_h': 1.0,
            'banking_w': 2.0,
            #'banking_offset': 1.0,
            #'banking_clamp': [-2.0, 2.0]
        })
    ])

    track = track.vertex_func(height_func.vertex_function)
    #track = track.vertex_func(lambda x, y, z, idx: height_func_path_perp(x, y, z, idx, line_fine))

    '''
    # For each point in the border, calculate closest
    for c in line.buffer(2.0).coords_iterator():
        coords_p, segment_idx, segment_coords_a, segment_coords_b, closest_obj, closest_d = line_fine.closest_segment(ddd.point(c))
        marker = ddd.line([(c[0], c[1], coords_p[2]), coords_p])
        marker = ddd.path3(marker).material(ddd.mats.highlight)
        root.append(marker)

    # For several points, calculate closest
    i = 0
    for c in track.mesh.vertices:
        i += 1
        if i % 3 != 0: continue
        coords_p, segment_idx, segment_coords_a, segment_coords_b, closest_obj, closest_d = line_fine.closest_segment(ddd.point(c))
        try:
            marker = ddd.line([c, coords_p])
            #marker.validate()
            if marker.geom.length < 0.01: continue
            marker = ddd.path3(marker).material(ddd.mats.highlight)
            #marker = marker.buffer(0.01).extrude(0.01).translate([0, 0, coords_p[2]]).material(ddd.mats.highlight)
            root.append(marker)
        except:
            pass
    '''

    #track = track.smooth()
    track = track.material(ddd.MAT_TEST)
    track = ddd.uv.map_cubic(track, split=False)
    root.append(track)

@dddtask()
def track(pipeline, root):

    os = 0
    path = ddd.path3()  # [[0, 0, 0], [2, 2, 2], [4, 4, 4]])
    path.path3 = trimesh.path.path.Path3D([
        entities.Line([0, 1, 2]),
        entities.Bezier([2, 3, 4, 5]),
        entities.Line([5, 6]),
    ], [
        [0, os, 4], [4, os+0.01, 4], [8, os, 2],
        [10, os, 1], [12, os + 2, 0], [12, os + 4, 0],  # Tangent arc (smooth path)
        #[10, os, 0], [12, os + 2, 4], [12, os + 4, 0],  # Curved test
        [12, os + 8, 0]
    ])

    path = path.translate([-5, 5, 0])
    root.append(path)

    path_arcs = ddd.paths.path_to_arcs(path)  # , tolerance=0.0001)
    root.append(path_arcs.material(ddd.MAT_HIGHLIGHT))

    #line = path.discretize(distance=2.0).to_line().translate([-5, 5, 0])  # FIXME: should have transform already
    line = path.discretize(distance=1.0).to_line().translate([-5, 5, 0])  # FIXME: should have transform already
    #ºline_fine = path.discretize(distance=0.1).to_line().translate([-5, 5, 0])  # FIXME: should have transform already
    #root.append(line.material(ddd.MAT_HIGHLIGHT))

    track = line.buffer(2.0).triangulate()

    track = ddd.meshops.subdivide_to_grid(track, 0.5)

    height_func = CompositeHeightFunction([
        #PathHeightFunction(line_fine),
        NodeBisectPathHeightFunction(line),
        #BankingPathHeightFunction(line_fine, )
    ])
    track = track.vertex_func(height_func.vertex_function)
    #track = track.vertex_func(lambda x, y, z, idx: height_func_path_perp(x, y, z, idx, line))

    #track = track.smooth()
    track = track.material(ddd.MAT_TEST)
    track = ddd.uv.map_cubic(track, split=False)
    root.append(track)

    '''
    # Per vertex?
    # width = ? (per vertex width)
    # left/right vs interior/exterior

    # Banking angle (from https://physicsteacher.in/2020/08/09/banked-curve-banking-angle-derivation/)
    tan(banking_angle) = v ** 2 / (r * g)  # v = speed (m/s)  r = curve radius (on the horizontal plane)  g = gravity

    camber_exterior = 2
    camber_interior = 0.5
    camber_offset = 1  # towards interior
    pathheight_camber = pathheight_camber_default(width=2, exterior_h=2, interior_h=0.5, offset_interior=1, width_clamp=[-2.5, 2.5])
    #profile = pathheight_profile_flat #
    #profile = pathheight_profile_flat #
    pathheight_profile = pathheight_profile_square(h=0.2)
    pathheight = pathheight_combine([pathheight_profile, pathheight])
    '''



@dddtask()
def track(pipeline, root):
    pass


@dddtask()
def show(pipeline, root):

    root.show()

