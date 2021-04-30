# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging
import math

from csg.core import CSG
from shapely.geometry import shape
from shapely.geometry.polygon import orient, Polygon
from shapely.geometry import Point
from trimesh import creation, primitives, boolean, transformations, util, \
    constants, triangles, grouping, geometry
from trimesh.base import Trimesh

from ddd.core.exception import DDDException
import numpy as np


# Get instance of logger for this module
logger = logging.getLogger(__name__)


EXTRUSION_METHOD_WRAP = "extrusion-wrap"
EXTRUSION_METHOD_SUBTRACT = "extrusion-contained"  # For internal/external/vertical extrusions


def extrude_step(obj, shape, offset, cap=True, method=EXTRUSION_METHOD_WRAP):
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
        logger.warn("Cannot extrude-step to None (ignoring and returning argument).")
        return result
    elif geom_b.type in ('MultiPolygon', 'GeometryCollection'):
        logger.warn("Cannot extrude a step to a 'MultiPolygon' or 'GeometryCollection' (skipping/flattening).")
        geom_b = Point()
    elif geom_b.is_empty and method == EXTRUSION_METHOD_WRAP:
        logger.debug("Extruding to point (should be using line too).")
        geom_b = geom_a.centroid
    elif geom_b.type == "LineString" and method == EXTRUSION_METHOD_WRAP:
        geom_b = Polygon(list(geom_b.coords) + [geom_b.coords[0]])
    elif geom_b.is_empty and method == EXTRUSION_METHOD_SUBTRACT:
        logger.debug("Cannot extrude subtract to empty geometry. Skipping / flattening.")
    elif geom_b.type == "LineString" and method == EXTRUSION_METHOD_SUBTRACT:
        logger.info("Cannot extrude subtract to linestring. Skipping / flattening.")
        geom_b = Point()

    vertices = list(result.mesh.vertices) if result.mesh else []
    faces = list(result.mesh.faces) if result.mesh else []

    # Remove previous last cap before extruding.
    last_cap_idx = result.extra.get('_extrusion_last_cap_idx', None)
    if last_cap_idx is not None:
        faces = faces[:last_cap_idx]

    if not geom_b.is_empty:
        result.extra['_extrusion_last_shape'] = shape
        result.extra['_extrusion_last_offset'] = obj.extra.get('_extrusion_last_offset', 0) + offset

    if not (geom_a.is_empty or geom_b.is_empty):

        mesh = None

        if method == EXTRUSION_METHOD_WRAP:
            mesh = extrude_between_geoms_wrap(geom_a, geom_b, offset, obj.extra.get('_extrusion_last_offset', 0))
        elif method == EXTRUSION_METHOD_SUBTRACT:
            try:
                mesh = extrude_between_geoms_subtract(last_shape, shape, offset, obj.extra.get('_extrusion_last_offset', 0))
            except DDDException as e:
                logger.error("Could not extrude subtract between geometries (%s): %s", obj, e)
                mesh = None
                result.extra['_extrusion_last_shape'] = last_shape
                result.extra['_extrusion_last_offset'] = result.extra['_extrusion_last_offset'] - offset
        else:
            raise DDDException("Invalid extrusion method: %s", method)

        if mesh:
            faces =  faces + [[f[0] + len(vertices), f[1] + len(vertices), f[2] + len(vertices)] for f in mesh.faces]
            vertices = vertices + list(mesh.vertices)
            result.extra['_extrusion_steps'] = result.extra['_extrusion_steps'] + 1

    result.extra['_extrusion_last_cap_idx'] = len(faces)

    if cap and not result.extra['_extrusion_last_shape'].geom.is_empty:
        #print(result.extra['_extrusion_last_shape'])
        #result.extra['_extrusion_last_shape'].dump()
        #print(result.extra['_extrusion_last_shape'].geom)
        try:
            cap_mesh = result.extra['_extrusion_last_shape'].triangulate().translate([0, 0, result.extra.get('_extrusion_last_offset', 0)])

            if cap_mesh and cap_mesh.mesh:
                faces = faces + [[f[0] + len(vertices), f[1] + len(vertices), f[2] + len(vertices)] for f in cap_mesh.mesh.faces]
                vertices = vertices + list(cap_mesh.mesh.vertices)
            else:
                result.extra['_extrusion_last_offset'] = result.extra['_extrusion_last_offset'] - offset
                cap_mesh = last_shape.triangulate().translate([0, 0, result.extra['_extrusion_last_offset']])
                faces = faces + [[f[0] + len(vertices), f[1] + len(vertices), f[2] + len(vertices)] for f in cap_mesh.mesh.faces]
                vertices = vertices + list(cap_mesh.mesh.vertices)
        except Exception as e:
            logger.error("Could not generate extrude cap triangulation (%s): %s", result.extra['_extrusion_last_shape'], e)
            cap_mesh = None


    # Merge
    if len(vertices) > 0 and len(faces) > 0:
        mesh = Trimesh(vertices, faces)
        mesh.merge_vertices()
        #mesh.fix_normals()
        result.mesh = mesh

    return result


def extrude_between_geoms_subtract(shape_a, shape_b, offset, base_height):
    """
    This extrusion method works on the assumption that geometries are contained one within another.

    This is useful for extrusion of areas or roofs, where each step is known to be entirely inside
    or outside of the shape of previous steps, including possible holes. This method works for
    convex and concave shapes.

    This method calculates the containment relation between shapes and subtracts them,
    triangulates the result and adjusts height of vertices.
    """
    from ddd.ddd import ddd

    #shape_a = shape_a.intersection(ddd.rect(shape_a.bounds()))
    #shape_b = shape_b.intersection(ddd.rect(shape_b.bounds()))
    shape_a.validate()
    shape_b.validate()

    inverted = False
    big, small = None, None
    if shape_a.geom.equals(shape_b.geom):
        # Calculate vertical extrusion
        vert = shape_a.extrude(offset, cap=False, base=False).translate([0, 0, base_height])
        return vert.mesh
    elif shape_a.contains(shape_b):
        big, small = shape_a, shape_b
    elif shape_b.contains(shape_a):
        big, small = shape_b, shape_a
        inverted = True
    else:
        raise DDDException("Cannot extrude-subtract between shapes as one is not contained within another.",
                           ddd_obj=ddd.group2([shape_a, shape_b.material(ddd.mats.highlight)]))

    # Calculate difference and set heights
    diff = big.subtract(small).triangulate()

    if diff.mesh:

        shape_a_coords = list(shape_a.geom.exterior.coords)
        for g in shape_a.geom.interiors: shape_a_coords.extend(list(g.coords))
        shape_b_coords = list(shape_b.geom.exterior.coords)
        for g in shape_b.geom.interiors: shape_b_coords.extend(list(g.coords))
        """
        shape_b_coords = list(shape_b.geom.exterior.coords) if shape_b.geom.type == "Polygon" else list(shape_b.geom.coords)
        if shape_b.geom.type == "Polygon":
            for g in shape_b.geom.interiors: shape_b_coords.extend(list(g.coords))
        """

        def func(x, y , z, i):
            if (x, y) in shape_a_coords or (x, y, z) in shape_a_coords: z = base_height
            elif (x, y) in shape_b_coords or (x, y, z) in shape_b_coords: z = base_height + offset
            else:
                logger.warn("Could not match coordinate during extrusion-subtract (%s, %s, %s) between %s and %s.", x, y, z, shape_a, shape_b)
                z = base_height
            return x, y, z

        diff = diff.vertex_func(func)
        if inverted:
            diff.mesh.invert()

    return diff.combine().mesh


def extrude_between_geoms_wrap(geom_a, geom_b, offset, base_height):

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


def extrude_coords(coords_a, coords_b, distance, base_height=0):


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


def extrude_triangulation(vertices, faces, height, cap=True, base=True, transform=None):
    """
    Based on Trimesh extrude_triangulation, but allows to exclude cap and base.
    """
    vertices = np.asanyarray(vertices, dtype=np.float64)
    height = float(height)
    faces = np.asanyarray(faces, dtype=np.int64)

    if not util.is_shape(vertices, (-1, 2)):
        raise ValueError('Vertices must be (n,2)')
    if not util.is_shape(faces, (-1, 3)):
        raise ValueError('Faces must be (n,3)')
    if np.abs(height) < constants.tol.merge:
        raise ValueError('Height must be nonzero!')

    # Make sure triangulation winding is pointing up
    normal_test = triangles.normals([util.stack_3D(vertices[faces[0]])])[0]

    normal_dot = np.dot(normal_test, [0.0, 0.0, np.sign(height)])[0]

    # Make sure the triangulation is aligned with the sign of
    # the height we've been passed
    if normal_dot < 0.0: faces = np.fliplr(faces)

    # stack the (n,3) faces into (3*n, 2) edges
    edges = geometry.faces_to_edges(faces)
    edges_sorted = np.sort(edges, axis=1)
    # Edges which only occur once are on the boundary of the polygon
    # since the triangulation may have subdivided the boundary of the
    # shapely polygon, we need to find it again
    edges_unique = grouping.group_rows(edges_sorted, require_count=1)

    # (n, 2, 2) set of line segments (positions, not references)
    boundary = vertices[edges[edges_unique]]

    # We are creating two vertical  triangles for every 2D line segment
    # on the boundary of the 2D triangulation
    vertical = np.tile(boundary.reshape((-1, 2)), 2).reshape((-1, 2))
    vertical = np.column_stack((vertical,np.tile([0, height, 0, height], len(boundary))))
    vertical_faces = np.tile([3, 1, 2, 2, 1, 0], (len(boundary), 1))
    vertical_faces += np.arange(len(boundary)).reshape((-1, 1)) * 4
    vertical_faces = vertical_faces.reshape((-1, 3))

    # Stack the (n,2) vertices with zeros to make them (n, 3)
    vertices_3D = util.stack_3D(vertices)

    # A sequence of zero- indexed faces, which will then be appended
    # with offsets to create the final mesh

    if not base and not cap:
        vertices_seq = [vertical]
        faces_seq = [vertical_faces]
    elif not base and cap:
        vertices_seq = [vertices_3D.copy() + [0.0, 0, height], vertical]
        faces_seq = [faces.copy(), vertical_faces]
    elif base and not cap:
        vertices_seq = [vertices_3D, vertical]
        faces_seq = [faces[:, ::-1], vertical_faces]
    else:
        vertices_seq = [vertices_3D, vertices_3D.copy() + [0.0, 0, height], vertical]
        faces_seq = [faces[:, ::-1], faces.copy(), vertical_faces]

    # Append sequences into flat nicely indexed arrays
    vertices, faces = util.append_faces(vertices_seq, faces_seq)

    # Apply transform here to avoid later bookkeeping
    if transform is not None:
        vertices = transformations.transform_points(
            vertices, transform)
        # If the transform flips the winding flip faces back so that the normals will be facing outwards
        if transformations.flips_winding(transform):
            faces = np.ascontiguousarray(np.fliplr(faces))  # fliplr makes arrays non-contiguous

    # create mesh object with passed keywords
    mesh = Trimesh(vertices=vertices, faces=faces)

    return mesh


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


