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
from shapely.geometry import shape, polygon
from trimesh import creation, primitives, boolean, transformations
import trimesh
from trimesh.base import Trimesh
from trimesh.path import segments
from trimesh.path.path import Path, Path3D, Path2D
from trimesh.scene.scene import Scene, append_scenes
from trimesh.visual.material import SimpleMaterial, PBRMaterial
from trimesh.scene.transforms import TransformForest
import copy
from trimesh.visual.texture import TextureVisuals
from matplotlib import colors
import json
import base64
from shapely.geometry.polygon import orient
from ddd.ops import extrusion
from trimesh.transformations import quaternion_from_euler
from trimesh.path.entities import Line
from ddd.core.cli import D1D2D3Bootstrap
from ddd.core.exception import DDDException
from shapely.geometry.linestring import LineString


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class D1D2D3():

    BASE_DIR = "../"

    CAP_ROUND = 1
    CAP_FLAT = 2
    CAP_SQUARE = 3

    JOIN_ROUND = 1
    JOIN_MITRE = 2
    JOIN_BEVEL = 3

    @staticmethod
    def initialize_logging(debug=True):
        """
        Convenience method for users.
        """
        D1D2D3Bootstrap.initialize_logging(debug)

    @staticmethod
    def material(name=None, color=None, extra=None):
        #material = SimpleMaterial(diffuse=color, )
        #return (0.3, 0.9, 0.3)
        material = DDDMaterial(name=name, color=color, extra=extra)
        return material

    @staticmethod
    def point(coords=None, name=None):
        if coords is None:
            coords = [0, 0, 0]
        elif len(coords) == 2:
            coords = [coords[0], coords[1], 0.0]
        geom = geometry.Point(coords)
        return DDDObject2(geom=geom, name=name)

    @staticmethod
    def line(points, name=None):
        '''
        Expects an array of coordinate tuples.
        '''
        geom = geometry.LineString(points)
        return DDDObject2(geom=geom, name=name)

    @staticmethod
    def polygon(coords, name=None):
        geom = geometry.Polygon(coords)
        return DDDObject2(geom=geom, name=name)

    @staticmethod
    def regularpolygon(sides, r=1.0, name=None):
        coords = [[math.cos(i * math.pi * 2 / sides) * r, math.sin(i * math.pi * 2 / sides) * r] for i in range(sides)]
        return D1D2D3.polygon(coords, name=name)

    @staticmethod
    def shape(geometry, name=None):
        """
        GeoJSON or dict
        """
        geom = shape(geometry)
        return DDDObject2(geom=geom, name=name)

    @staticmethod
    def geometry(geometry):
        """
        @deprecate in favour of shape
        """
        geom = shape(geometry)
        return DDDObject2(geom=geom)

    @staticmethod
    def rect(bounds, name=None):
        cmin, cmax = ((bounds[0], bounds[1]), (bounds[2], bounds[3]))
        geom = geometry.Polygon([(cmin[0], cmin[1], 0.0), (cmax[0], cmin[1], 0.0),
                                 (cmax[0], cmax[1], 0.0), (cmin[0], cmax[1], 0.0)])
        geom = polygon.orient(geom, -1)
        return DDDObject2(geom=geom, name=name)

    @staticmethod
    def disc(center=None, r=None, resolution=8, name=None):
        if center is None: center = ddd.point([0, 0, 0], name=name)
        if r is None: r = 1.0
        geom = center.geom.buffer(r, resolution=resolution)
        return DDDObject2(geom=geom)

    @staticmethod
    def sphere(center=None, r=None, subdivisions=2):
        if center is None: center = ddd.point([0, 0, 0])
        if r is None: r = 1.0
        mesh = primitives.Sphere(center=center.geom.coords[0], radius=r, subdivisions=subdivisions)
        mesh = Trimesh([[v[0], v[1], v[2]] for v in mesh.vertices], list(mesh.faces))
        return DDDObject3(mesh=mesh)

    @staticmethod
    def cube(center=None, d=None):
        """
        Cube is sitting on the Z plane defined by the center position.
        `d` is the distance to the side, so cube side length will be twice that value.

        @see :func:`box`
        """
        #if center is not None: raise NotImplementedError()  #
        if center is None: center = [0, 0, 0]
        if d is None: d = 1.0
        cube = D1D2D3.rect([-d, -d, d, d]).extrude(d * 2).translate(center)
        return cube

    @staticmethod
    def box(bounds=None, name=None):
        """
        """
        if bounds is None:
            bounds = [0, 0, 0, 1, 1, 1]
        cube = D1D2D3.rect([bounds[0], bounds[1], bounds[3], bounds[4]], name=name)
        cube = cube.extrude(bounds[5] - bounds[2]).translate([0, 0, bounds[2]])
        return cube

    @staticmethod
    def marker(name=None):
        marker = D1D2D3.box(name=name)
        marker.extra['ddd:marker'] = True
        #marker.extra['ddd:collider'] = False  # should not be explicit
        return marker

    @staticmethod
    def ddd2(*args, **kwargs):
        return DDDObject2(*args, **kwargs)

    @staticmethod
    def ddd3(*args, **kwargs):
        return DDDObject3(*args, **kwargs)

    @staticmethod
    def grid2(bounds, detail=1.0):
        rects = []
        cmin, cmax = bounds[:2], bounds[2:]
        pointsx = list(np.linspace(cmin[0], cmax[0], 1 + int((cmax[0] - cmin[0]) / detail)))
        pointsy = list(np.linspace(cmin[1], cmax[1], 1 + int((cmax[1] - cmin[1]) / detail)))

        for (idi, (i, ni)) in enumerate(zip(pointsx[:-1], pointsx[1:])):
            for (idj, (j, nj)) in enumerate(zip(pointsy[:-1], pointsy[1:])):
                rect = ddd.rect([i, j, ni, nj])
                rect.geom = orient(rect.geom, 1)
                rects.append(rect.geom)
        geom = geometry.MultiPolygon(rects)
        #DDDObject2(geom=geom).show()
        #geom = geom.buffer(0.0)  # Sanitize, but this destroys the grid
        #DDDObject2(geom=geom).show()
        return DDDObject2(geom=geom)

    @staticmethod
    def grid3(bounds2, detail=1.0):
        grid2 = D1D2D3.grid2(bounds2, detail)
        cmin, cmax = bounds2[:2], bounds2[2:]
        #grid2 = D1D2D3.rect(cmin, cmax)
        vertices = []
        faces = []
        idi = 0
        idj = 0
        for geom in grid2.geom:
            flip = ((idi % 2) + (idj % 2)) % 2
            gvs, gfs = creation.triangulate_polygon(geom)
            if flip:
                gfs = np.array([[3, 0, 2], [1, 2, 0]])  # Alternate faces
            gfs = [gf + len(vertices) for gf in gfs]
            faces.extend(gfs)
            vertices.extend(gvs)

            hitmax = False
            for v in gvs:
                if v[0] >= cmax[0] or v[1] >= cmax[1]:
                    hitmax = True

            idi += 1
            if hitmax:
                idi = 0
                idj += 1

        vertices = [[v[0], v[1], 0.0] for v in vertices]
        mesh = Trimesh(vertices, faces)
        #mesh.fix_normals()
        mesh.merge_vertices()
        return DDDObject3(mesh=mesh)

    @staticmethod
    def group2(children=None, name=None, empty=None):
        return D1D2D3.group(children, name, empty=2)

    @staticmethod
    def group3(children=None, name=None, empty=None):
        return D1D2D3.group(children, name, empty=3)

    @staticmethod
    def group(children=None, name=None, empty=None):
        """
        """

        if children is None:
            children = []

        if not children:
            if empty is None:
                raise ValueError("Tried to add empty collection to children group and no empty value is set.")
            elif empty in (2, "2", "2d"):
                result = DDDObject2(name=name)
            elif empty in (3, "3", "3d"):
                result = DDDObject3(name=name)
            else:
                raise ValueError("Tried to add empty collection to children group and passed invalid empty parameter: %s", empty)

            #logger.debug("Tried to create empty group.")
            #return None
        elif isinstance(children[0], DDDObject2):
            result = DDDObject2(children=children, name=name)
        elif isinstance(children[0], DDDObject3) or isinstance(children[0], DDDInstance):
            result = DDDObject3(children=children, name=name)
        else:
            raise ValueError("Invalid object for ddd.group(): %s" % children[0])

        if any((c is None for c in children)):
            raise ValueError("Tried to add null to object children list.")

        return result

    @staticmethod
    def instance(obj, name=None):
        obj = DDDInstance(obj, name)
        return obj


class DDDMaterial():

    def __init__(self, name=None, color=None, extra=None):
        """
        Color is hex color.
        """
        self.name = name
        self.color = color
        self.color_rgba = None
        self.extra = extra

        if self.color:
            self.color_rgba = trimesh.visual.color.hex_to_rgba(self.color)

    def __repr__(self):
        return "DDDMaterial(name=%s, color=%s)" % (self.name, self.color)


class DDDObject():

    def __init__(self, name=None, children=None, extra=None, material=None):
        self.name = name
        self.children = children if children is not None else []
        self.extra = extra if extra is not None else {}
        self.mat = material

        #self.geom = None
        #self.mesh = None

        for c in self.children:
            if not isinstance(c, self.__class__) and not (isinstance(c, DDDInstance) and isinstance(self, DDDObject3)):
                raise ValueError("Invalid children type (not %s): %s" % (self.__class__, c))

    def __repr__(self):
        return "<DDDObject (name=%s, children=%d)>" % (self.name, len(self.children) if self.children else 0)

    def dump(self, indent_level=0):
        print("  " * indent_level + str(self))
        for c in self.children:
            c.dump(indent_level=indent_level + 1)

    def select(self, func):
        """
        """

        result = []
        if func(self):
            result.append(self)

        for c in self.children:
            cr = c.filter(func)
            if cr: result.extend(cr.children)

        if isinstance(self, DDDObject2):
            return ddd.group(result, empty=2)
        elif isinstance(self, DDDObject3):
            return ddd.group(result, empty=3)
        else:
            return ddd.group(result)

    def filter(self, func):
        return self.select(func)

    def append(self, obj):
        self.children.append(obj)
        return self


class DDDObject2(DDDObject):

    def __init__(self, name=None, children=None, geom=None, extra=None, material=None):
        super().__init__(name, children, extra, material)
        self.geom = geom

    def __repr__(self):
        return "<DDDObject2 (name=%s, geom=%s (%s verts), children=%d, id=%s)>" % (self.name, self.geom.type if self.geom else None, self.vertex_count(), len(self.children) if self.children else 0, id(self))

    def vertex_count(self):
        if not self.geom:
            return 0
        if self.geom.type == 'MultiPolygon':
            return sum([len(p.exterior.coords) for p in self.geom.geoms])
        if self.geom.type == 'Polygon':
            if self.geom.is_empty: return 0
            return len(self.geom.exterior.coords) + sum([len(i.coords) for i in self.geom.interiors])
        else:
            return len(self.geom.coords)
        return None

    def copy(self, name=None):
        obj = DDDObject2(name=name if name else self.name, children=[c.copy() for c in self.children], geom=copy.deepcopy(self.geom) if self.geom else None, extra=dict(self.extra), material=self.mat)
        return obj

    def material(self, material):
        obj = self.copy()
        obj.mat = material
        #mesh.visuals = visuals
        obj.children = [c.material(material) for c in obj.children]
        return obj

    def end(self):
        coords = self.geom.coords[-1]
        return D1D2D3.point(coords)

    def line_rel(self, coords):
        if len(coords) == 2: coords = [coords[0], coords[1], 0.0]
        linecoords = [p for p in self.geom.coords]
        nextpoint = [linecoords[-1][0] + coords[0], linecoords[-1][1] + coords[1], linecoords[-1][2] + coords[2]]
        linecoords.append(nextpoint)

        geom = geometry.LineString(linecoords)
        return DDDObject2(geom=geom)

    def line_to(self, coords):
        if len(coords) == 2: coords = [coords[0], coords[1], 0.0]
        linecoords = [p for p in self.geom.coords]
        linecoords.append(coords)

        geom = geometry.LineString(linecoords)
        return DDDObject2(geom=geom)

    def translate(self, coords):
        if len(coords) == 2: coords = [coords[0], coords[1], 0.0]
        result = self.copy()
        if self.geom:
            trans_func = lambda x, y, z=0.0: (x + coords[0], y + coords[1], z + coords[2])
            result.geom = ops.transform(trans_func, self.geom)
        result.children = [c.translate(coords) for c in self.children]
        return result

    def rotate(self, angle, origin='centroid'):
        result = self.copy()
        if self.geom:
            result.geom = affinity.rotate(self.geom, angle / (math.pi / 180), origin=origin)
        result.children = [c.rotate(angle, origin) for c in self.children]
        return result

    def scale(self, coords):
        if isinstance(coords, float): coords = [coords, coords, 1.0]
        if len(coords) == 2: coords = [coords[0], coords[1], 1.0]
        result = self.copy()
        if self.geom:
            trans_func = lambda x, y, z=0.0: (x * coords[0], y * coords[1], z * coords[2])
            result.geom = ops.transform(trans_func, self.geom)
        result.children = [c.scale(coords) for c in self.children]
        return result

    def clean(self, eps=None):
        result = self.copy()
        if result.geom and not result.geom.is_valid:
            logger.warn("Removed invalid geometry: %s", result)
            result.geom = None
        if result.geom and not result.geom.is_simple:
            logger.warn("Removed geometry that crosses itself: %s", result)
            result.geom = None
        if result.geom and not self.children and eps:
            result = result.buffer(eps, 1, join_style=ddd.JOIN_MITRE).buffer(-eps, 1, join_style=ddd.JOIN_MITRE)
        result.children = [c.clean() for c in self.children]
        return result

    def outline(self):
        result = self.copy().individualize()
        if result.geom and result.geom.type == "Polygon":
            result.geom = LineString(list(result.geom.exterior.coords))
        result.children = [c.outline() for c in result.children]
        return result

    def buffer(self, distance, resolution=8, cap_style=D1D2D3.CAP_SQUARE, join_style=D1D2D3.JOIN_MITRE, mitre_limit=5.0):
        '''
        Resolution is:

        shapely.geometry.CAP_STYLE
            round    1
            flat    2
            square    3
        shapely.geometry.JOIN_STYLE
            round    1
            mitre    2
            bevel    3
        '''
        result = self.copy()
        if self.geom:
            result.geom = self.geom.buffer(distance, resolution=resolution,
                                           cap_style=cap_style, join_style=join_style,
                                           mitre_limit=5.0)
        result.children = [c.buffer(distance, resolution, cap_style, join_style, mitre_limit) for c in self.children]

        return result

    def subtract(self, other):

        result = self.copy()
        if self.geom and other.geom:
            try:
                result.geom = result.geom.difference(other.geom)
            except Exception as e:
                raise DDDException("Cannot subtract geometries: %s - %s: %s" % (self, other, e),
                                   ddd_obj=ddd.group2([self, other.material(ddd.mats.highlight)]))
        for c in other.children:
            result = result.subtract(c)
        #if self.geom:
        #    union = other.union()
        #    result.geom = result.geom.difference(union.geom)
        result.children = [c.subtract(other) for c in result.children]

        return result

    def union(self, other=None):
        """
        Returns a copy of this object to which geometry from other object has been unioned.
        If the second object has children, they are also unioned recursively.

        If the second object is None, all children of this are unioned.
        """
        result = self.copy()
        result.children = []

        # If other has children, union them too
        objs = self.children
        while len(objs) > 1:
            newo = objs[0].union().union(objs[1].union())
            objs = objs[2:] + [newo]
        if objs:
            if result.geom:
                result.geom = result.geom.union(objs[0].geom)
            else:
                result.geom = objs[0].geom

        if other:
            union = other.union()
            if result.geom and union.geom:
                result.geom = result.geom.union(union.geom)
            elif other.geom:
                result.geom = other.geom

        return result

    def intersect(self, other):
        """
        Calculates the intersection of this object and children with
        the other object (and children).
        """
        result = self.copy()
        other = other.union()

        if self.geom and other.geom:
            result.geom = self.geom.intersection(other.geom)
        result.children = [c.intersect(other) for c in self.children]

        return result

    def intersects(self, other):
        """
        Calculates if this object and children intersects with any of
        the other object (and children).
        """
        other = other.union()

        if not other.geom or other.geom.empty:
            return False

        if self.geom:
            if self.geom.intersects(other.geom):
                return True
        for c in self.children:
            if c.intersects(other):
                return True
        return False

    def contains(self, other):
        other = other.union()
        if self.geom:
            if self.geom.contains(other.geom):
                return True
        for c in self.children:
            if c.contains(other):
                return True
        return False

    def convex_hull(self):
        result = self.copy().union()
        result.geom = result.geom.convex_hull
        return result

    def validate(self):
        if self.geom:
            if not self.geom.is_valid:
                raise AssertionError()
            if self.geom.is_empty:
                raise AssertionError()
            if not self.geom.is_simple:
                raise AssertionError()
            if self.geom.type == "Polygon":
                if len(list(self.geom.exterior.coords)) < 3:
                    raise AssertionError()
                for interior in self.geom.interiors:
                    if len(list(interior.coords)) < 3:
                        raise AssertionError()

        for c in self.children:
            c.validate()

    def individualize(self, remove_interiors=False):
        """
        Return a group of multiple DDD2Objects if the object is a GeometryCollection.
        """
        result = self.copy()

        newchildren = []

        if self.geom and self.geom.type == 'GeometryCollection':
            result.geom = None
            for partialgeom in self.geom.geoms:
                newobj = self.copy()
                newobj.geom = partialgeom
                newchildren.append(newobj)

        elif self.geom and self.geom.type == 'MultiPolygon':
            result.geom = None
            for partialgeom in self.geom.geoms:
                newobj = self.copy()
                newobj.geom = partialgeom
                newchildren.append(newobj)

        elif self.geom and self.geom.type == 'MultiLineString':
            result.geom = None
            for partialgeom in self.geom.geoms:
                newobj = self.copy()
                newobj.geom = partialgeom
                newchildren.append(newobj)

        elif self.geom and self.geom.type == 'Polygon' and remove_interiors and self.geom.interiors:
            result.geom = None
            newobj = self.copy()
            newobj.geom = self.geom.exterior
            newchildren.append(newobj)

        result.children = [c.individualize() for c in (self.children + newchildren)]

        return result

    def triangulate(self):
        """
        Returns a triangulated mesh (3D) from this 2D shape.
        """
        if self.geom:
            if self.geom.type == 'MultiPolygon' or self.geom.type == 'GeometryCollection':
                meshes = []
                for geom in self.geom.geoms:
                    pol = DDDObject2(geom=geom)
                    mesh = pol.triangulate()
                    meshes.append(mesh)
                result = ddd.group(children=meshes, name=self.name)
            elif not self.geom.is_empty and not self.geom.type == 'LineString' and not self.geom.type == 'Point':
                # Triangulation mode is critical for the resulting quality and triangle count.
                #mesh = creation.extrude_polygon(self.geom, height)
                #vertices, faces = creation.triangulate_polygon(self.geom)  # , min_angle=math.pi / 180.0)
                vertices, faces = creation.triangulate_polygon(self.geom, triangle_args="p", engine='triangle')  # Flat, minimal, non corner-detailing ('pq30' produces more detailed triangulations)
                mesh = Trimesh([(v[0], v[1], 0.0) for v in vertices], faces)
                #mesh = creation.extrude_triangulation(vertices=vertices, faces=faces, height=0.2)
                mesh.merge_vertices()
                result = DDDObject3(mesh=mesh, name=self.name)
            else:
                result = DDDObject3()
        else:
            result = DDDObject3()

        result.children.extend([c.triangulate() for c in self.children])

        # Copy extra information from original object
        result.name = self.name if result.name is None else result.name
        result.extra = dict(self.extra)
        result.extra['extruded_shape'] = self

        if self.mat is not None:
            result = result.material(self.mat)

        return result

    def extrude(self, height, center=False):
        """
        If height is negative, the object is aligned with is top face on the XY plane.
        If center is true, the object is centered relative to the extruded height.
        """

        #logger.debug("Extruding: %s", self)

        # Extrude exterior line(s)
        '''
        coords = self.geom.exterior.coords
        segs = []
        for i in range(len(coords) - 1):
            segs.append([coords[i], coords[i + 1]])

        v, f = segments.extrude(segs, abs(height), False)
        mesh = Trimesh(v, f)
        mesh.invert()  # mesh normals face polygon interior, invert it

        # Triangulate polygon and create caps
        if caps:
            v, f = creation.triangulate_polygon(self.geom)
            mesh_cap_top = Trimesh(v, f)
            v, f = creation.triangulate_polygon(self.geom)
            mesh_cap_bottom = Trimesh(v, f)
        '''

        if self.geom:
            if self.geom.type == 'MultiPolygon' or self.geom.type == 'GeometryCollection':
                meshes = []
                for geom in self.geom.geoms:
                    pol = DDDObject2(geom=geom, material=self.mat)
                    try:
                        mesh = pol.extrude(height)
                        meshes.append(mesh)
                    except ValueError as e:
                        logger.error("Could not extrude Polygon in MultiPolygon: %s", e)
                    except IndexError as e:
                        logger.error("Could not extrude Polygon in MultiPolygon: %s", e)
                result = DDDObject3(children=meshes, name="%s (split extr)" % self.name)
            #elif self.geom.type == "Polygon" and self.geom.exterior.type == "LinearRing" and len(list(self.geom.exterior.coords)) < 3:
            #    logger.warn("Cannot extrude: A LinearRing must have at least 3 coordinate tuples (cleanup first?)")
            #    result = DDDObject3(children=[], name="%s (empty polygon extr)" % self.name)
            elif not self.geom.is_empty and not self.geom.type == 'LineString' and not self.geom.type == 'Point':
                # Triangulation mode is critical for the resulting quality and triangle count.
                #mesh = creation.extrude_polygon(self.geom, height)
                #vertices, faces = creation.triangulate_polygon(self.geom, engine="meshpy")  # , min_angle=math.pi / 180.0)
                #vertices, faces = creation.triangulate_polygon(self.geom, triangle_args="p30", engine='triangle')

                #self.geom = ops.transform(lambda x, y, *z: (x, y), self.geom)
                #print(self.geom, self.geom.type, self.geom.exterior, self.geom.exterior.type)

                vertices, faces = creation.triangulate_polygon(self.geom, triangle_args="p", engine='triangle')  # Flat, minimal, non corner-detailing ('pq30' produces more detailed triangulations)
                try:
                    mesh = creation.extrude_triangulation(vertices=vertices,
                                                          faces=faces,
                                                          height=abs(height))
                    mesh.merge_vertices()
                    result = DDDObject3(mesh=mesh)
                except Exception as e:
                    raise DDDException("Could not extrude: %s" % self, ddd_obj=self)

                if center:
                    result = result.translate([0, 0, -height / 2])
                elif height < 0:
                    result = result.translate([0, 0, height])
            elif not self.geom.is_empty and self.geom.type == 'LineString':
                coords_a = list(self.geom.coords)
                coords_b = list(self.geom.coords)
                mesh = extrusion.extrude_coords(coords_a, coords_b, abs(height))
                mesh2 = extrusion.extrude_coords(list(reversed(coords_a)), list(reversed(coords_b)), abs(height))

                offset = len(list(mesh.vertices))
                mesh.vertices = list(mesh.vertices) + list(mesh2.vertices)
                mesh.faces = list(mesh.faces) + [(f[0] + offset, f[1] + offset, f[2] + offset) for f in mesh2.faces]

                result = DDDObject3(mesh=mesh)
            else:
                #logger.warn("Cannot extrude (empty polygon)")
                result = DDDObject3()
        else:
            result = DDDObject3()

        result.children.extend([c.extrude(height) for c in self.children])

        # Copy extra information from original object
        result.name = self.name if result.name is None else result.name
        result.extra = dict(self.extra)
        result.extra['extruded_shape'] = self

        if self.mat is not None:
            result = result.material(self.mat)

        return result

    def extrude_step(self, obj_2d, offset, cap=True, base=True):
        # Triangulate and store info for 3D extrude_step

        if base:
            result = self.triangulate()
            if result.mesh:
                result.mesh.faces = np.fliplr(result.mesh.faces)
        else:
            # TODO: unify in copy2d->3d method
            result = DDDObject3()
            # Copy extra information from original object
            result.name = self.name if result.name is None else result.name
            result.extra = dict(self.extra)
            if self.mat is not None:
                result = result.material(self.mat)

        result.extra['_extrusion_last_shape'] = self
        result = result.extrude_step(obj_2d, offset, cap)
        return result

    def simplify(self, distance):
        result = self.copy()
        if self.geom:
            result.geom = result.geom.simplify(distance, preserve_topology=True)
        result.children = [c.simplify(distance) for c in self.children]
        return result

    def random_points(self, num_points=1, density=None):
        # TODO: use density or count, accoridng to poligon area :?
        result = []
        minx, miny, maxx, maxy = self.geom.bounds
        while len(result) < num_points:
            pnt = geometry.Point(random.uniform(minx, maxx), random.uniform(miny, maxy))
            if self.geom.contains(pnt):
                result.append(pnt.coords[0])

        return result

    def linearize(self):
        """
        Converts all 2D shapes to Linear objects (LineStrings or LinearRing).
        It takes exterior polygons when holes are present.
        """
        result = self.copy()
        if self.geom:
            result.geom = result.geom.exterior if result.geom.type == "Polygon" else result.geom
        result.children = [c.linearize() for c in self.children]
        return result

    def distance(self, other):
        """
        Returns the minimum distance from this object to other.
        """
        if self.children: raise AssertionError()
        if other.children: raise AssertionError()

        return self.geom.distance(other.geom)

    def closest(self, other):
        """
        Returns distance and closest object from object and children to other object.
        Does not support children in "other" geometry.

        @return (closest_object, closest_distance)
        """
        if other.children: raise AssertionError()

        closest_o = None
        closest_d = math.inf

        if self.geom:
            closest_o = self
            closest_d = self.geom.distance(other.geom)

        for c in self.children:
            c_o, c_d = c.closest(other)
            if c_d < closest_d:
                closest_o, closest_d = c_o, c_d

        return closest_o, closest_d

    def interpolate_segment(self, d):
        """
        Interpolates along a LineString, returning:
            coords_p, segment_idx, segment_coords_a, segment_coords_b

        Note that returns coordinates, not DDD objects.
        """
        # Walk segment
        l = 0.0
        coords = self.geom.coords
        #length = self.geom.length
        for idx in range(len(coords) - 1):
            p, pn = coords[idx:idx+2]
            pl = math.sqrt((pn[0] - p[0]) ** 2 + (pn[1] - p[1]) ** 2)
            l += pl
            if l >= d:
                return (self.geom.interpolate(d).coords[0], idx, p, pn)
        return None

    def closest_segment(self, other):
        """
        Closest segment in a LineString to other geometry.
        Does not support children in "other" geometry.
        """
        closest_self, closest_d = self.closest(other)
        #logger.debug("Closest: %s  %s > %s", closest_d, closest_self, other)

        d = closest_self.geom.project(other.geom)

        result = (*closest_self.interpolate_segment(d), closest_self)
        #ddd.group([other.buffer(5.0),  ddd.point(result[2]).buffer(5.0).material(ddd.mat_highlight), ddd.line([result[2], result[3]]).buffer(2.0), ddd.point(result[0]).buffer(5.0), closest_self.buffer(0.2)]).show()
        return result

    def geom_recursive(self):
        geoms = []
        if self.geom: geoms = [self.geom]
        if self.children:
            for c in self.children:
                cgems = c.geom_recursive()
                geoms.extend(cgems)
        return geoms

    def save(self, path):

        # $$('path').forEach(function(p) {console.log(p); p.setAttribute('stroke-width', 1.0)});

        geoms = self.geom_recursive()
        with open(path, 'w') as f:
            geom = geometry.GeometryCollection(geoms)
            f.write(geom._repr_svg_())

    def show(self):
        #self.extrude(1.0).show()
        self.triangulate().show()


class DDDInstance(DDDObject):

    def __init__(self, ref, name=None, extra=None, material=None):
        super().__init__(name, None, extra, material)
        self.ref = ref
        self.transform = DDDTransform()

    def __repr__(self):
        return "<DDDInstance (name=%s, ref=%s, id=%s)>" % (self.name, self.ref, id(self))

    def copy(self):
        obj = DDDInstance(ref=self.ref, name=self.name, extra=dict(self.extra))
        obj.transform = self.transform.copy()
        return obj

    def vertex_iterator(self):
        rotation_matrix = transformations.quaternion_matrix(self.transform.rotation)
        for v in self.ref.vertex_iterator():
            vtransformed = np.dot(rotation_matrix, v)
            vtransformed = [vtransformed[0] + self.transform.position[0], vtransformed[1] + self.transform.position[1], vtransformed[2] + self.transform.position[2], v[3]]
            # FIXME: TODO: apply full transform via numpy
            yield vtransformed

    def translate(self, v):
        obj = self.copy()
        obj.transform.position = [obj.transform.position[0] + v[0], obj.transform.position[1] + v[1], obj.transform.position[2] + v[2]]
        return obj

    def rotate(self, v):
        obj = self.copy()
        rot = quaternion_from_euler(v[0], v[1], v[2], "sxyz")
        rotation_matrix = transformations.quaternion_matrix(rot)
        obj.transform.position = np.dot(rotation_matrix, obj.transform.position + [1])[:3]  # Hack: use matrices
        obj.transform.rotation = transformations.quaternion_multiply(rot, obj.transform.rotation)  # order matters!
        return obj

    def _recurse_scene(self, path_prefix=""):

        auto_name = "node_%s" % (id(self))
        node_name = ("%s_%s" % (self.name, id(self))) if self.name else auto_name

        # Add metadata to name
        if True:
            ignore_keys = ('uv', 'osm:feature', 'connections')
            metadata = dict(self.extra)
            metadata['path'] = path_prefix + node_name
            if self.mat and self.mat.name:
                metadata['ddd:material'] = self.mat.name
            if self.mat and self.mat.color:
                metadata['ddd:material:color'] = self.mat.color  # hex
            if self.mat and self.mat.extra:
                # If material has extra metadata, add it but do not replace
                metadata.update({k:v for k, v in self.mat.extra.items() if k not in metadata or metadata[k] is None})

            metadata = json.loads(json.dumps(metadata, default=lambda x: None))
            metadata = {k: v for k,v in metadata.items() if v is not None and k not in ignore_keys}
            serialized_metadata = base64.b64encode(json.dumps(metadata).encode("utf-8")).decode("ascii")
            encoded_node_name = node_name + "_" + str(serialized_metadata)

        scene = Scene()
        if self.ref:

            generate_marker = True
            generate_mesh = True

            ref = self.ref.copy()
            if generate_mesh:
                ref = ref.scale(self.transform.scale)
                ref = ref.rotate(transformations.euler_from_quaternion(self.transform.rotation, axes='sxyz'))
                ref = ref.translate(self.transform.position)
                refscene = ref._recurse_scene(path_prefix=path_prefix + node_name + "/")
                scene = append_scenes([scene] + [refscene])

            if generate_marker:
                ref = D1D2D3.marker(self.name)
                ref = ref.scale(self.transform.scale)
                ref = ref.rotate(transformations.euler_from_quaternion(self.transform.rotation, axes='sxyz'))
                ref = ref.translate(self.transform.position)
                ref.extra.update(self.ref.extra)
                ref.extra.update(self.extra)
                refscene = ref._recurse_scene(path_prefix=path_prefix + node_name + "/")
                scene = append_scenes([scene] + [refscene])

        else:
            raise ValueError("Instance should reference another object.")

        '''
        cscenes = []
        if self.children:
            for c in self.children:
                cscene = c._recurse_scene(path_prefix=path_prefix + node_name + "/")
                cscenes.append(cscene)

        scene = append_scenes([scene] + cscenes)
        '''

        return scene

    def recurse_meshes(self):

        ref = self.ref.copy()
        ref = ref.scale(self.transform.scale)
        ref = ref.rotate(transformations.euler_from_quaternion(self.transform.rotation, axes='sxyz'))
        ref = ref.translate(self.transform.position)

        cmeshes = []
        if ref.mesh:
            mesh = ref._process_mesh()
            cmeshes = [mesh]
        if ref.children:
            for c in ref.children:
                cmeshes.extend(c.recurse_meshes())
        return cmeshes


class DDDTransform():

    def __init__(self):
        self.position = [0, 0, 0]
        self.rotation = quaternion_from_euler(0, 0, 0, "sxyz")
        self.scale = [1, 1, 1]

    def copy(self):
        result = DDDTransform()
        result.position = list(self.position)
        result.rotation = list(self.rotation)
        result.scale = list(self.scale)
        return result


class DDDObject3(DDDObject):

    def __init__(self, name=None, children=None, mesh=None, extra=None, material=None):
        super().__init__(name, children, extra, material)
        self.mesh = mesh

    def __repr__(self):
        return "<DDDObject3 (name=%s, faces=%d, children=%d, id=%s)>" % (self.name, len(self.mesh.faces) if self.mesh else 0, len(self.children) if self.children else 0, id(self))

    def copy(self):
        obj = DDDObject3(name=self.name, children=list(self.children), mesh=self.mesh.copy() if self.mesh else None, material=self.mat, extra=dict(self.extra))
        return obj

    '''
    def instance(self):
        obj = D1D2D3.cube(d=1.0)  #[0, 0, 0], 1)
        obj.extra['ddd:instance'] = self
        return obj
    '''

    def translate(self, v):
        obj = self.copy()
        if obj.mesh:
            obj.mesh.apply_translation(v)
        obj.children = [c.translate(v) for c in self.children]
        return obj

    def rotate(self, v):
        obj = self.copy()
        if obj.mesh:
            rot = transformations.euler_matrix(v[0], v[1], v[2], 'sxyz')
            obj.mesh.vertices = trimesh.transform_points(obj.mesh.vertices, rot)
        obj.children = [c.rotate(v) for c in obj.children]
        return obj

    def scale(self, v):
        obj = self.copy()
        if obj.mesh:
            sca = np.array([[v[0], 0.0, 0.0, 0.0],
                            [0.0, v[1], 0.0, 0.0],
                            [0.0, 0.0, v[2], 0.0],
                            [0.0, 0.0, 0.0, 1.0]])
            obj.mesh.vertices = trimesh.transform_points(obj.mesh.vertices, sca)
        obj.children = [c.scale(v) for c in self.children]
        return obj

    def material(self, material):
        obj = self.copy()
        obj.mat = material
        if obj.mesh and material is not None:
            obj.mesh.visual.face_colors = material

        #visuals = mesh.visuatrimesh.visual.ColorVisuals(mesh=mesh, face_colors=[material])  # , material=material
        #mesh.visuals = visuals

        obj.children = [c.material(material) for c in obj.children]
        return obj

    def elevation_func(self, func):
        obj = self.copy()
        for v in obj.mesh.vertices:
            dz = func(v[0], v[1])
            v[2] += dz
        obj.children = [c.elevation_func(func) for c in obj.children]
        return obj

    def vertex_func(self, func):
        obj = self.copy()
        if obj.mesh:
            for iv, v in enumerate(obj.mesh.vertices):
                res = func(v[0], v[1], v[2], iv)
                v[0] = res[0]
                v[1] = res[1]
                v[2] = res[2]
        obj.children = [c.vertex_func(func) for c in self.children]
        return obj

    def vertex_iterator(self):
        meshes = self.recurse_meshes()
        for m in meshes:
            for idx, v in enumerate(m.vertices):
                yield (v[0], v[1], v[2], idx)

    def _csg(self, other, operation):

        if not other or not other.mesh:
            return self.copy()

        if not self.mesh and operation == 'union':
            return other.copy()

        logger.debug("CSG operation: %s %s %s" % (self, operation, other))

        pols1 = []
        for f in self.mesh.faces:
            verts = [self.mesh.vertices[f[0]], self.mesh.vertices[f[1]], self.mesh.vertices[f[2]]]
            pols1.append(csggeom.Polygon([csggeom.Vertex(verts[0]), csggeom.Vertex(verts[1]), csggeom.Vertex(verts[2])]))

        pols2 = []
        for f in other.mesh.faces:
            verts = [other.mesh.vertices[f[0]], other.mesh.vertices[f[1]], other.mesh.vertices[f[2]]]
            pols2.append(csggeom.Polygon([csggeom.Vertex(verts[0]), csggeom.Vertex(verts[1]), csggeom.Vertex(verts[2])]))

        csg1 = CSG.fromPolygons(pols1)
        csg2 = CSG.fromPolygons(pols2)

        if operation == 'subtract':
            pols = csg1.subtract(csg2).toPolygons()
        elif operation == 'union':
            pols = csg1.union(csg2).toPolygons()
        else:
            raise AssertionError()

        #mesh = boolean.difference([self.mesh, other.mesh], 'blender')
        v = []
        f = []
        i = 0
        for p in pols:
            for vi in range(len(p.vertices) - 2):
                v.extend([[p.vertices[0].pos[0], p.vertices[0].pos[1], p.vertices[0].pos[2]],
                          [p.vertices[vi + 1].pos[0], p.vertices[vi + 1].pos[1], p.vertices[vi + 1].pos[2]],
                          [p.vertices[vi + 2].pos[0], p.vertices[vi + 2].pos[1], p.vertices[vi + 2].pos[2]]])
                f.append([i, i+1, i+2])
                i += 3

        mesh = Trimesh(v, f)
        mesh.fix_normals()
        mesh.merge_vertices()

        obj = DDDObject3(mesh=mesh, children=self.children, material=self.mat)
        return obj

    def subtract(self, other):
        return self._csg(other, operation='subtract')

    def union(self, other):
        return self._csg(other, operation='union')

    def extrude_step(self, obj_2d, offset, cap=True):
        result = self.copy()
        result = extrusion.extrude_step(result, obj_2d, offset, cap=cap)
        return result

    def _recurse_scene(self, path_prefix=""):

        scene = Scene()
        auto_name = "node_%s" % (id(self))
        node_name = ("%s_%s" % (self.name, id(self))) if self.name else auto_name

        # Add metadata to name
        metadata = None
        if True:
            ignore_keys = ('uv', 'osm:feature', 'connections')
            metadata = dict(self.extra)
            metadata['path'] = path_prefix + node_name
            if self.mat and self.mat.name:
                metadata['ddd:material'] = self.mat.name
            if self.mat and self.mat.color:
                metadata['ddd:material:color'] = self.mat.color  # hex

            metadata = json.loads(json.dumps(metadata, default=lambda x: None))
            metadata = {k: v for k,v in metadata.items() if v is not None and k not in ignore_keys}
            serialized_metadata = base64.b64encode(json.dumps(metadata).encode("utf-8")).decode("ascii")
            encoded_node_name = node_name + "_" + str(serialized_metadata)

        # UV coords test
        if self.mesh:
            self.mesh = self._process_mesh()

        scene.add_geometry(geometry=self.mesh, node_name=encoded_node_name.replace(" ", "_"))

        cscenes = []
        if self.children:
            for c in self.children:
                cscene = c._recurse_scene(path_prefix=path_prefix + node_name + "/")
                cscenes.append(cscene)

        scene = append_scenes([scene] + cscenes)

        """
        # rotate the camera view transform
        camera_old, _geometry = scene.graph[scene.camera.name]
        camera_new = np.dot(camera_old, rotate)

        # apply the new transform
        scene.graph[scene.camera.name] = camera_new
        """

        return scene

    def _process_mesh(self):
        if self.extra.get('uv', None):
            uvs = self.extra['uv']
        else:
            # Note that this does not flatten normals (that should be optional)
            uvs = [(v[0], v[2]) for v in self.mesh.vertices]

        if len(uvs) != len(self.mesh.vertices):
            raise AssertionError("Invalid number of UV coordinates: %s", self)
        #if self.mesh.visual is None:
        #    self.mesh.visual = TextureVisuals(uv=uvs, material=mat)
        #else:
        #    self.mesh.visual.uv = uvs

        if self.mat:
            mat = SimpleMaterial(diffuse=self.mat.color_rgba)
            self.mesh.visual = TextureVisuals(uv=uvs, material=mat)
            #mat = PBRMaterial(doubleSided=True)  # , emissiveFactor= [0.5 for v in self.mesh.vertices])
            #self.mesh.visual = TextureVisuals(uv=uvs, material=mat)
        else:
            #logger.debug("No material set for mesh: %s", self)
            pass

        return self.mesh

    def _recurse_scene_ALT(self, base_frame=None, graph=None):

        if graph is None:
            graph = TransformForest()
        if base_frame is None:
            base_frame = "world"

        scene = Scene(base_frame=base_frame, graph=None)

        auto_name = "node_%s" % (id(self))
        node_name = self.name + "_%s" % id(self) if self.name else auto_name
        node_name = node_name.replace(" ", "_")
        scene.add_geometry(geometry=self.mesh, node_name=node_name)

        #tf = TransformForest()

        cscenes = []
        if self.children:
            for c in self.children:
                cscene = c._recurse_scene(node_name, graph)

                sauto_name = "node_%s" % (id(c))
                cscene_name = c.name + "_%s" % id(c) if c.name else sauto_name
                cscene_name = cscene_name.replace(" ", "_")

                scene.add_geometry(geometry=cscene, node_name=cscene_name)
                cscenes.append(cscene)

                #changed = scene.graph.transforms.add_edge(node_name, cscene_name)

        #matrix = np.eye(4)
        #scene.graph.update(frame_from=new_base,
        #                   frame_to=self.graph.base_frame,
        #                   matrix=matrix)
        #scene.graph.base_frame = new_base

        #scene = append_scenes([scene] + cscenes)

        """
        # rotate the camera view transform
        camera_old, _geometry = scene.graph[scene.camera.name]
        camera_new = np.dot(camera_old, rotate)

        # apply the new transform
        scene.graph[scene.camera.name] = camera_new
        """

        return scene

    def __rezero(self):
        # From Trimesh as graph example
        """
        Move the current scene so that the AABB of the whole
        scene is centered at the origin.
        Does this by changing the base frame to a new, offset
        base frame.
        """
        if self.is_empty or np.allclose(self.centroid, 0.0):
            # early exit since what we want already exists
            return

        # the transformation to move the overall scene to AABB centroid
        matrix = np.eye(4)
        matrix[:3, 3] = -self.centroid

        # we are going to change the base frame
        new_base = str(self.graph.base_frame) + '_I'
        self.graph.update(frame_from=new_base,
                          frame_to=self.graph.base_frame,
                          matrix=matrix)
        self.graph.base_frame = new_base

    def recurse_meshes(self):
        cmeshes = []
        if self.mesh:
            mesh = self._process_mesh()
            cmeshes = [mesh]
        if self.children:
            for c in self.children:
                cmeshes.extend(c.recurse_meshes())
        return cmeshes

    def recurse_objects(self):
        cobjs = [self]
        for c in self.children:
            cobjs.extend(c.recurse_objects())
        return cobjs

    def show(self):

        #rotated = self.rotate([-math.pi / 2.0, 0, 0])
        #scene = rotated._recurse_scene()
        #scene.show('gl')

        # Example code light
        #light = trimesh.scene.lighting.DirectionalLight()
        #light.intensity = 10
        #scene.lights = [light]

        import pyrender
        #pr_scene = pyrender.Scene.from_trimesh_scene(rotated)

        # Scene not rotated, as pyrender seems to use Z for vertical.
        meshes = self.recurse_meshes()  # rotated
        pr_scene = pyrender.Scene()
        for m in meshes:
            prm = pyrender.Mesh.from_trimesh(m, smooth=False) #, wireframe=True)
            pr_scene.add(prm)

        pyrender.Viewer(pr_scene, lighting="direct")  #, viewport_size=resolution)
        #pyrender.Viewer(scene, lighting="direct")  #, viewport_size=resolution)

    def save(self, path):
        logger.info("Saving to: %s (%s)", path, self)

        if path.endswith('.obj'):
            # Exporting just first mesh
            logger.warning("NOTE: Exporting just first object to .obj.")
            meshes = self.recurse_meshes()
            data = trimesh.exchange.obj.export_obj(self.meshes[0])

        elif path.endswith('.dae'):
            meshes = self.recurse_meshes()
            data = trimesh.exchange.dae.export_collada(meshes)

        elif path.endswith('.glb'):
            rotated = self.rotate([-math.pi / 2.0, 0, 0])
            scene = rotated._recurse_scene()
            data = trimesh.exchange.gltf.export_glb(scene)

        else:
            raise ValueError()

        #scene.export(path)
        with open(path, 'wb') as f:
            f.write(data)


ddd = D1D2D3

from ddd.materials.materials import MaterialsCollection
from ddd.pack.mats.defaultmats import DefaultMaterials
ddd.mats = MaterialsCollection()
ddd.mats.highlight = D1D2D3.material(color='#ff00ff')
ddd.mats.load_from(DefaultMaterials())

from ddd.ops.geometry import DDDGeometry
ddd.geomops = DDDGeometry()

from ddd.ops.align import DDDAlign
ddd.align = DDDAlign()

from ddd.ops.snap import DDDSnap
ddd.snap = DDDSnap()

from ddd.ops.uvmapping import DDDUVMapping
ddd.uv = DDDUVMapping()

from ddd.ops.helper import DDDHelper
ddd.helper = DDDHelper()


