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

    # Straight Line

    # Sharp angles

    # Circle

    # Flattened Path3 from Shapely: with segmented curves (arc_to()), and also angles

    # 3D (with Z) open Path3 from Shapely: with segmented curves (arc_to()), and also angles

    # 3D (with Z) closed Path3 from Shapely: with segmented curves (arc_to()), and also angles

    # 3D (with Z) open Path3 from Trimesh: with splines/arcs and also angles

    # 3D (with Z) closed Path3 from Trimesh: with splines/arcs and also angles

    pass


@dddtask()
def create_pathheights_for_curves():
    pass

def height_func_bump(coords, center, r, h):
    dif = (coords[0] - center[0], coords[1] - center[1])
    d = math.sqrt(dif[0] * dif[0] + dif[1] * dif[1])
    d = DDDMath.clamp(d, 0, r)
    return h * (1.0 - d / r)

def height_func_bump_smooth(coords, center, r, h):
    dif = (coords[0] - center[0], coords[1] - center[1])
    d = math.sqrt(dif[0] * dif[0] + dif[1] * dif[1])
    f = DDDMath.smoothstep(0.1, 0.9, d / r)
    return h * (1.0 - f)

def height_func_path(x, y, z, idx, path):
    # Find nearest points in path, then interpolate z
    #coords = path.geom.coords if path.geom.type == "LineString" else sum([list(g.coords) for g in path.geom.geoms], [])

    #arch = height_func_arc(x, y, z, [10, 10], 0, 2, math.pi * (7/4) - (math.pi * 5 / 180), math.pi / 4, 10)
    #if (arch[2] != z):
    #    return arch

    coords_p, segment_idx, segment_coords_a, segment_coords_b, closest_obj, closest_d = path.closest_segment(ddd.point([x, y]))
    #dist_a = math.sqrt( (segment_coords_a[0] - coords_p[0]) ** 2 + (segment_coords_a[1] - coords_p[1]) ** 2 )
    #dist_b = math.sqrt( (segment_coords_b[0] - coords_p[0]) ** 2 + (segment_coords_b[1] - coords_p[1]) ** 2 )
    #factor_b = dist_a / (dist_a + dist_b)
    #factor_a = 1 - factor_b  # dist_b / (dist_a + dist_b) #1 - factor_b  #
    #interp_z = segment_coords_a[2] * factor_a + segment_coords_b[2] * factor_b
    #print(interp_z, closest_d, segment_coords_a, segment_coords_b)

    interp_z = coords_p[2]
    return (x, y, z + interp_z)  # FIXME: z should not be added here, or not by default, as Z coordinates are already local in the path

def line_vertex_bisector(line, vertex_index, length=1.0):
    """
    Returns the bisector at a vertex in a line segment (this is the "perpendicular" at the vertex)
    """

    if vertex_index == 0:
        return line.perpendicular(distance=0.0, length=length, double=True)
    if vertex_index >= len(line.geom.coords) - 1:
        return line.perpendicular(distance=line.length(), length=length, double=True)

    vm1 = Vector3(line.geom.coords[vertex_index - 1])
    v0 = Vector3(line.geom.coords[vertex_index])
    v1 = Vector3(line.geom.coords[(vertex_index + 1) % len(line.geom.coords)])

    d = v1 - v0
    dm1 = v0 - vm1

    bs0 = (dm1.normalized() + d.normalized()).normalized()
    bs0 = Vector3([-bs0.y, bs0.x, 0])

    p1 = v0 + bs0 * length
    p2 = v0 - bs0 * length
    perpendicular = ddd.line([p1, p2])
    return perpendicular

def height_func_path_perp(x, y, z, idx, path):

    # TODO: precalculate the point list and perpendiculars at each node

    # Find the closest point in the path
    point = ddd.point([x, y, z])

    points = ddd.group2()
    for i, c in enumerate(path.coords_iterator()):
        points.append(ddd.point(c).set('index', i))

    closest, closest_d = points.closest(point)

    # Calculate perpendiculars to their bisecting angles
    index = closest.get('index')

    perpm1 = line_vertex_bisector(path, max(index - 1, 0), length=10.0)
    perp0 = line_vertex_bisector(path, index, length=10.0)
    perp1 = line_vertex_bisector(path, min(index + 1, len(points.children) - 1), length=10.0)

    # Debug
    #if (random.uniform(0, 1) < 0.01):
    #    root.append(perpm0.material(ddd.MAT_HIGHLIGHT))

    # Project point to perpendiculars
    dm1 = point.distance(perpm1)
    d0 = point.distance(perp0)
    d1 = point.distance(perp1)

    # Find which side of perp0 we are at
    perp0norm = (Vector3([perp0.geom.coords[1][0], perp0.geom.coords[1][1], 0]) - Vector3([perp0.geom.coords[0][0], perp0.geom.coords[0][1], 0])).normalized()
    perp0norm = Vector3([-perp0norm[1], perp0norm[0], perp0norm[2]]).normalized()

    perp0side = perp0norm.dot((Vector3(point.geom.coords[0]) - Vector3(closest.geom.coords[0])).normalized())


    interp_z = 0  # closest.geom.coords[0][2]
    try:
        if (perp0side < 0):
            interp_z = (d0 / (dm1 + d0)) * perpm1.geom.coords[0][2] + (dm1 / (dm1 + d0)) * perp0.geom.coords[0][2]

            # Debug
            '''
            if (random.uniform(0, 1) < 0.02):
                print(dm1, d0, d1, perp0side, perp0.geom.coords[0])
                coords_p, segment_idx, segment_coords_a, segment_coords_b, closest_obj, closest_d = perp0.closest_segment(ddd.point([x, y, z]))
                marker = ddd.path3(ddd.line([[x, y, interp_z], coords_p]))
                if (marker.path3.length > 0): root.append(marker.material(ddd.MAT_HIGHLIGHT))
                coords_p, segment_idx, segment_coords_a, segment_coords_b, closest_obj, closest_d = perpm1.closest_segment(ddd.point([x, y, z]))
                marker = ddd.path3(ddd.line([[x, y, interp_z], coords_p]))
                if (marker.path3.length > 0): root.append(marker)

                #coords_p, segment_idx, segment_coords_a, segment_coords_b, closest_obj, closest_d = perpm1.closest_segment(ddd.point(c))
                #root.append(ddd.line([[x, y, z], coords_p]).material(ddd.MAT_HIGHLIGHT))
            '''

        else:
            interp_z = (d0 / (d1 + d0)) * perp1.geom.coords[0][2] + (d1 / (d1 + d0)) * perp0.geom.coords[0][2]
    except Exception as e:
        logger.error("Error interpolating height using path perpendicular strategy: %s", e)

    #dist_a = math.sqrt( (segment_coords_a[0] - coords_p[0]) ** 2 + (segment_coords_a[1] - coords_p[1]) ** 2 )
    #dist_b = math.sqrt( (segment_coords_b[0] - coords_p[0]) ** 2 + (segment_coords_b[1] - coords_p[1]) ** 2 )
    #factor_b = dist_a / (dist_a + dist_b)
    #factor_a = 1 - factor_b  # dist_b / (dist_a + dist_b) #1 - factor_b  #
    #interp_z = segment_coords_a[2] * factor_a + segment_coords_b[2] * factor_b
    #print(interp_z, closest_d, segment_coords_a, segment_coords_b)

    #print(list(closest.geom.coords))
    #interp_z = closest.geom.coords[0][2]

    return (x, y, z + interp_z)  # FIXME: z should not be added here, or not by default, as Z coordinates are already local in the path


@dddtask()
def track(pipeline, root):

    # TODO: second point is colinear if we use [7.0, 21.0], and the division gets removed in the buffer operation, which is sometimes not desired
    line = ddd.point([3, 25, 4]).line_to([7.01, 21.01, 4]).line_to([14, 14, 2]).arc_to([14, 6, 0], [10, 10], False, 8).line_to([4, -4])

    path = ddd.path3(line)
    #root.append(path)

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
        perp = line_vertex_bisector(line, i, length=1.0)
        root.append(perp.material(ddd.MAT_HIGHLIGHT))

    #print(path_smoothed.path3.entities)
    root.append(path_smoothed.material(ddd.MAT_HIGHLIGHT))

    #line_fine = path_smoothed.discretize(distance=0.2).to_line()  # FIXME: should have transform already
    track = track.vertex_func(lambda x, y, z, idx: height_func_path_perp(x, y, z, idx, line))

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
    track = track.vertex_func(lambda x, y, z, idx: height_func_path_perp(x, y, z, idx, line))

    #track = track.smooth()
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

