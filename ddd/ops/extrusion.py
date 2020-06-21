# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging
import math
import random

from csg import geom as csggeom
from csg.core import CSG
import numpy as np
from shapely import geometry, affinity, ops
from shapely.geometry import shape
from trimesh import creation, primitives, boolean, transformations
import trimesh
from trimesh.base import Trimesh
from trimesh.path import segments
from trimesh.path.path import Path
from trimesh.scene.scene import Scene, append_scenes
from trimesh.visual.material import SimpleMaterial
from trimesh.scene.transforms import TransformForest
import copy
from trimesh.visual.texture import TextureVisuals
from matplotlib import colors
import json
import base64
from shapely.geometry.polygon import orient, Polygon


# Get instance of logger for this module
logger = logging.getLogger(__name__)


def extrude_step(obj, shape, offset, cap=True):
    """
    Extrude a shape into another.
    """
    last_shape = obj.extra['_extrusion_last_shape']

    #obj = last_shape.individualize()
    #shape = shape.individualize()

    #obj_a.assert_single()
    #obj_b.assert_single()
    geom_a = last_shape.geom
    geom_b = shape.geom

    result = obj.copy()

    if geom_a is None or geom_a.is_empty:
        logger.debug("Should be extruding from point or line, ignoring and returning argument.")
        # Previous step was empty, avoid destroy the object
        # TODO: this can be improved, previous could be point or line
        return result
    elif geom_a.type in ('MultiPolygon', 'GeometryCollection'):
        logger.warn("Cannot extrude a step from a 'MultiPolygon' or 'GeometryCollection'.")
        return result

    if geom_b is None:
        logger.debug("Extruding to None step (ignoring and returning argument).")
        return result
    elif geom_b.is_empty:
        logger.debug("Extruding to point (should be using line too).")
        geom_b = geom_a.centroid
    elif geom_b.type == "LineString":
        #logger.debug("Extruding to line as point (should be using line).")
        #geom_b = geom_b.centroid
        geom_b = Polygon(list(geom_b.coords) + [geom_b.coords[0]])


    vertices = list(result.mesh.vertices) if result.mesh else []
    faces = list(result.mesh.faces) if result.mesh else []

    # Remove previous last cap before extruding.
    last_cap_idx = result.extra.get('_extrusion_last_cap_idx', None)
    if last_cap_idx is not None:
        faces = faces[:last_cap_idx]

    result.extra['_extrusion_last_shape'] = shape
    result.extra['_extrusion_last_offset'] = obj.extra.get('_extrusion_last_offset', 0) + offset

    if not (geom_a.is_empty or geom_b.is_empty):

        if geom_b.type in ('MultiPolygon', 'GeometryCollection'):
            logger.warn("Cannot extrude a step to a 'MultiPolygon' or 'GeometryCollection'.")

        else:
            mesh = extrude_between_geoms(geom_a, geom_b, offset, obj.extra.get('_extrusion_last_offset', 0) )
            faces =  faces + [[f[0] + len(vertices), f[1] + len(vertices), f[2] + len(vertices)] for f in mesh.faces]
            vertices = vertices + list(mesh.vertices)
            result.extra['_extrusion_steps'] = result.extra['_extrusion_steps'] + 1

    result.extra['_extrusion_last_cap_idx'] = len(faces)

    if cap and not shape.geom.is_empty:
        cap_mesh = shape.triangulate().translate([0, 0, result.extra['_extrusion_last_offset']])
        if cap_mesh.mesh:
            faces = faces + [[f[0] + len(vertices), f[1] + len(vertices), f[2] + len(vertices)] for f in cap_mesh.mesh.faces]
            vertices = vertices + list(cap_mesh.mesh.vertices)
        else:
            result.extra['_extrusion_last_offset']= result.extra['_extrusion_last_offset'] - offset
            cap_mesh = last_shape.triangulate().translate([0, 0, result.extra['_extrusion_last_offset']])
            faces = faces + [[f[0] + len(vertices), f[1] + len(vertices), f[2] + len(vertices)] for f in cap_mesh.mesh.faces]
            vertices = vertices + list(cap_mesh.mesh.vertices)

    # Merge
    mesh = Trimesh(vertices, faces)
    mesh.merge_vertices()
    #mesh.fix_normals()
    result.mesh = mesh

    return result


def extrude_between_geoms(geom_a, geom_b, offset, base_height):

    # Ensure winding
    if (geom_a.type == "Polygon" and geom_b.type == "Polygon"):
        if (geom_a.exterior.is_ccw != geom_b.exterior.is_ccw):
            #logger.debug("Cannot extrude between polygons with different winding. Orienting polygons.")
            geom_a = orient(geom_a, -1)
            geom_b = orient(geom_b, -1)

    coords_a = geom_a.coords if geom_a.type == 'Point' else geom_a.exterior.coords[:-1]  # Linearrings repeat first/last point
    coords_b = geom_b.coords if geom_b.type == 'Point' else geom_b.exterior.coords[:-1]  # Linearrings repeat first/last point

    # Find closest to coords_a[0] in b, and shift coords in b to match 0
    closest_idx = 0
    closest_dist = float("inf")
    for idx, v in enumerate(coords_b):
        dist = ((v[0] - coords_a[0][0]) ** 2) + ((v[1] - coords_a[0][1]) ** 2)
        if dist < closest_dist:
            closest_idx = idx
            closest_dist = dist
    #if closest_idx != 0: print("Closest Idx: %s" % closest_idx)
    coords_b = coords_b[closest_idx:] + coords_b[:closest_idx]

    coords_a = coords_a[:] + [coords_a[0]]
    coords_b = coords_b[:] + [coords_b[0]]
    return extrude_coords(coords_a, coords_b, offset, base_height)

    '''
    vertices = []
    vertices.extend([(x, y, base_height) for x, y, *z in coords_a])
    vertices_b_idx = len(vertices)
    vertices.extend([(x, y, base_height + offset) for x, y, *z in coords_b])

    shape_a_idx = 0
    shape_b_idx = 0

    def va(shape_a_idx): return vertices[shape_a_idx % len(coords_a)]
    def vb(shape_b_idx): return vertices[(shape_b_idx % len(coords_b)) + vertices_b_idx]
    def ang(v): return (math.atan2(v[1], v[0]) + (math.pi * 2)) % (math.pi * 2)
    def diff(va, vb): return  [va[0] - vb[0], va[1] - vb[1], va[2] - vb[2]]
    def distsqr(v): return v[0] * v[0] + v[1] * v[1] + v[2] * v[2]

    faces = []
    finished_a = False
    finished_b = False
    last_tri = None
    while not (finished_a and finished_b):
        la = distsqr(diff(va(shape_a_idx + 1), vb(shape_b_idx)))
        lb = distsqr(diff(vb(shape_b_idx + 1), va(shape_a_idx)))
        aa = ang(va(shape_a_idx))
        aan = ang(va(shape_a_idx + 1))
        ab = ang(vb(shape_b_idx))
        abn = ang(vb(shape_b_idx + 1))

        norm = 'l2'
        if norm == 'angle':
            advance_b = (abs(abn - aa) < abs(aan - ab))
        elif norm == 'l2':
            advance_b = lb < la

        if advance_b:
            ntri = [shape_a_idx, shape_b_idx + vertices_b_idx, (shape_b_idx + 1) % len(coords_b) + vertices_b_idx]
            if not finished_b: shape_b_idx +=1
        else:
            ntri = [shape_a_idx, shape_b_idx + vertices_b_idx, (shape_a_idx + 1) % len(coords_a)]
            if not finished_a: shape_a_idx +=1

        if last_tri == ntri: break

        faces.append(ntri)
        last_tri = ntri
        #print(ntri)

        if shape_a_idx >= len(coords_a):
            shape_a_idx = 0
            finished_a = True
        if shape_b_idx >= len(coords_b):
            shape_b_idx = 0
            finished_b = True

    return Trimesh(vertices, faces)
    '''


def extrude_coords(coords_a, coords_b, distance, base_height=0):

    '''
    closest_idx = 0
    closest_dist = float("inf")
    for idx, v in enumerate(coords_b):
        dist = ((v[0] - coords_a[0][0]) ** 2) + ((v[1] - coords_a[0][1]) ** 2)
        if dist < closest_dist:
            closest_idx = idx
            closest_dist = dist
    if closest_idx != 0:
        print("Closest Idx: %s" % closest_idx)
    coords_b = coords_b[closest_idx:] + coords_b[:closest_idx]
    '''

    vertices = []
    vertices.extend([(x, y, base_height) for x, y, *z in coords_a])
    vertices_b_idx = len(vertices)
    vertices.extend([(x, y, base_height + distance) for x, y, *z in coords_b])

    shape_a_idx = 0
    shape_b_idx = 0

    def va(shape_a_idx): return vertices[shape_a_idx]
    def vb(shape_b_idx): return vertices[(shape_b_idx) + vertices_b_idx]
    def ang(v): return (math.atan2(v[1], v[0]) + (math.pi * 2)) % (math.pi * 2)
    def diff(va, vb): return  [va[0] - vb[0], va[1] - vb[1], va[2] - vb[2]]
    def distsqr(v): return v[0] * v[0] + v[1] * v[1] + v[2] * v[2]

    faces = []
    finished_a = False
    finished_b = False
    last_tri = None
    while not (finished_a and finished_b):

        la = distsqr(diff(va(shape_a_idx + 1), vb(shape_b_idx))) if (shape_a_idx < len(coords_a) - 1) else float("inf")
        lb = distsqr(diff(vb(shape_b_idx + 1), va(shape_a_idx))) if (shape_b_idx < len(coords_b) - 1) else float("inf")
        aa = ang(va(shape_a_idx))
        aan = ang(va(shape_a_idx + 1)) if (shape_a_idx < len(coords_a) - 1) else float("inf")
        ab = ang(vb(shape_b_idx))
        abn = ang(vb(shape_b_idx + 1)) if (shape_b_idx < len(coords_b) - 1) else float("inf")

        #norm = 'l2'
        norm = 'l2'
        if norm == 'angle':
            advance_b = (abs(abn - aa) < abs(aan - ab))
        elif norm == 'l2':
            advance_b = lb < la

        if advance_b or finished_a:
            ntri = [shape_a_idx, shape_b_idx + vertices_b_idx, (shape_b_idx + 1) + vertices_b_idx]
            shape_b_idx +=1
        elif not advance_b or finished_b:
            ntri = [shape_a_idx, shape_b_idx + vertices_b_idx, (shape_a_idx + 1)]
            shape_a_idx +=1
        else:
            raise AssertionError()

        if last_tri == ntri: break

        faces.append(ntri)
        last_tri = ntri
        #print(ntri)

        if shape_a_idx >= len(coords_a) - 1:
            finished_a = True
        if shape_b_idx >= len(coords_b) - 1:
            finished_b = True

    #print(vertices)
    #print(faces)
    return Trimesh(vertices, faces)


def extrude_step_multi(obj, steps, cap=True, base=True, scale_y=1.0, shape_callback=None):
    """
    If height is passed, shape is adjusted to it.
    """

    base = obj
    obj = obj.copy()

    ref_x = steps[0][0]
    last_y = steps[0][1] * scale_y
    for step in steps[1:]:
        step_scale = step[0] / ref_x
        step_shape = base.scale([step_scale, step_scale])
        step_dy = (step[1] * scale_y) - last_y
        obj = obj.extrude_step(step_shape, step_dy, cap=cap, base=base)
        last_y = last_y + step_dy

    return obj

def extrude_dome(obj, height, steps=6):
    """
    If height is passed, shape is adjusted to it.
    """

    base = obj
    obj = obj.copy()

    stepheight = 1.0 / steps
    for i in range(steps):
        stepy = (i + 1) * stepheight
        stepx = math.sqrt(1 - (stepy ** 2))
        stepbuffer = -(1 - stepx)
        #obj = obj.extrude_step(base.buffer(stepbuffer * height), stepheight * height)

        shp = base.scale([stepx, stepx]) if stepx > 0 else base.centroid()
        obj = obj.extrude_step(shp, stepheight * height)

    return obj


