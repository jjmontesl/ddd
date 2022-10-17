# DDD(123) - Library for procedural generation of 2D and 3D geometries and scenes
# Copyright (C) 2021 Jose Juan Montes
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import base64
import copy
import json
import logging
import math
import random

import cairosvg
import numpy as np
from ddd.core.cli import D1D2D3Bootstrap
from ddd.core.exception import DDDException
from ddd.core.selectors.selector_ebnf import selector_ebnf
from ddd.ddd import ddd
from ddd.formats.geojson import DDDGeoJSONFormat
from ddd.formats.json import DDDJSONFormat
from ddd.formats.svg import DDDSVG
from ddd.math.vector2 import Vector2
from ddd.math.vector3 import Vector3
from ddd.nodes.node import DDDNode
from ddd.nodes.node3 import DDDObject3
from ddd.ops import extrusion
from ddd.util.common import parse_bool
from shapely import affinity, geometry, ops
from shapely.geometry import polygon, shape
from shapely.geometry.linestring import LineString
from shapely.geometry.multipolygon import MultiPolygon
from shapely.geometry.polygon import Polygon, orient
from shapely.geometry.point import Point
from shapely.ops import polygonize, unary_union
from shapely.strtree import STRtree
from trimesh import boolean, creation, primitives, remesh, transformations
from trimesh.base import Trimesh

# Get instance of logger for this module
logger = logging.getLogger(__name__)



class DDDNode2(DDDNode):

    def __init__(self, name=None, children=None, geom=None, extra=None, material=None, transform=None):
        super().__init__(name, children, extra, material, transform)
        self.geom = geom
        self._strtree = None

    def __repr__(self):
        return "%s (%s %s %sv %dc)" % (self.name, self.__class__.__name__, self.geom.type if hasattr(self, 'geom') and self.geom else None, self.vertex_count() if hasattr(self, 'geom') else None, len(self.children) if self.children else 0)

    def copy(self, name=None, copy_children=True):
        """
        Copies children, geometry (deep copying the object) and metadata (shallow copy) recursively.
        """
        children = []
        if copy_children:
            # TODO: FIXME: Whether to clone geometry and recursively copy children (in all Node, Node2 and Node3) heavily impacts performance, but removing it causes errors (and is semantically incorect) -> we should use a dirty/COW mechanism?
            children = [c.copy() for c in self.children]
        # TODO: FIXME: Whether to clone geometry and recursively copy children (in all Node, Node2 and Node3) heavily impacts performance, but removing it causes errors (and is semantically incorect) -> we should use a dirty/COW mechanism?
        #obj = DDDObject2(name=name if name else self.name, children=children, geom=copy.deepcopy(self.geom) if self.geom else None, extra=dict(self.extra), material=self.mat, transform=self.transform.copy())
        obj = DDDObject2(name=name if name else self.name, children=children, geom=self.geom if self.geom else None, extra=dict(self.extra), material=self.mat, transform=self.transform.copy())
        return obj

    def copy3(self, name=None, mesh=None, copy_children=False):
        """
        Copies this DDDObject2 into a DDDObject3, maintaining metadata but NOT children or geometry.
        """
        # TODO: FIXME: Whether to clone geometry and recursively copy children (in all Node, Node2 and Node3) heavily impacts performance, but removing it causes errors (and is semantically incorect) -> we should use a dirty/COW mechanism?
        if copy_children:
            obj = ddd.DDDObject3(name=name if name else self.name, children=[(c.copy3() if hasattr(c, 'copy3') else c.copy()) for c in self.children], mesh=mesh, extra=dict(self.extra), material=self.mat, transform=self.transform.copy())
        else:
            obj = ddd.DDDObject3(name=name if name else self.name, children=[], mesh=mesh, extra=dict(self.extra), material=self.mat, transform=self.transform.copy())
        return obj

    def replace(self, obj):
        """
        Replaces self data with data from other object. Serves to "replace"
        instances in lists.
        """
        # TODO: Study if the system shall modify instances and let user handle cloning, this method would be unnecessary
        super(DDDObject2, self).replace(obj)
        self.geom = obj.geom
        return self

    def index_create(self):
        self._strtree = STRtree(self.geom_recursive())

    def index_clear(self):
        self._strtree = None

    def start(self):
        coords = self.geom.coords[0]
        return ddd.point(coords)

    def end(self):
        coords = self.geom.coords[-1]
        return ddd.point(coords)

    def line_rel(self, coords):
        if len(coords) == 2: coords = [coords[0], coords[1], 0.0]
        linecoords = [p for p in self.geom.coords]
        nextpoint = [linecoords[-1][0] + coords[0], linecoords[-1][1] + coords[1], linecoords[-1][2] + coords[2]]
        linecoords.append(nextpoint)

        geom = geometry.LineString(linecoords)
        return DDDObject2(geom=geom)

    def line_to(self, coords):
        if len(coords) == 2: coords = [coords[0], coords[1], 0.0]

        if self.geom.type == "Point":
            linecoords = [self.geom.coords[0], coords]
        else:
            linecoords = [p for p in self.geom.coords]
            linecoords.append(coords)

        result = self.copy()
        result.geom = geometry.LineString(linecoords)
        return result

    def arc_to(self, coords, center, ccw, resolution=4):
        if len(coords) == 2: coords = [coords[0], coords[1], 0.0]
        if len(center) == 2: center = [center[0], center[1], 0.0]

        # Calculate arc coordinates from center
        linecoords = list(self.geom.coords)
        angle_start = math.atan2(linecoords[-1][1] - center[1], linecoords[-1][0] - center[0])
        angle_end = math.atan2(coords[1] - center[1], coords[0] - center[0])

        h_start = linecoords[-1][2] if len(linecoords[-1]) > 2 else 0
        h_end = coords[2] if len(coords) > 2 else 0

        angle_diff = angle_end - angle_start
        radius_vec = (coords[0] - center[0], coords[1] - center[1])
        radius_l = math.sqrt(radius_vec[0] * radius_vec[0] + radius_vec[1] * radius_vec[1])
        if ccw: angle_diff = (math.pi * 2) - angle_diff

        numpoints = math.ceil(abs(angle_diff) * (resolution / (math.pi / 2)))
        angles = np.linspace(angle_start, angle_end, numpoints + 1, endpoint=True)
        for a in angles[1:]:
            interp_factor = (a - angle_start) / (angle_end - angle_start)
            linecoords.append([center[0] + math.cos(a) * radius_l, center[1] + math.sin(a) * radius_l, h_start + (h_end - h_start) * interp_factor])

        result = self.copy()
        result.geom = geometry.LineString(linecoords)
        return result

    def centroid(self):
        if self.geom.type == 'Point':
            return ddd.point(self.geom.coords[0])

        geom = self.union().geom
        if geom is None:
            raise DDDException("Cannot find centroid (no geometry) for object: %s" % self)
        result = ddd.point(geom.centroid.coords)
        result.copy_from(self, copy_material=True)
        return result

    def point_coords(self):
        """Return the coordinates of the geometry, asuming it is a single point (e.g. as returned by `centroid()`)."""
        if self.geom and self.geom.type == 'Point':
            coords = self.geom.coords[0]
            return Vector3.array(coords)
        else:
            raise DDDException("Cannot get point coordinates of a geometry with none or more than one coordinate: %s" % self)

    def line_angle(self):
        """Returns the angle to +X, asuming it is a LineString with 2 vertices. Z coordinates, if present, are ignored."""
        if self.geom and self.geom.type == 'LineString' and len(self.geom.coords) == 2:
            p0 = Vector2.array(self.geom.coords[0])
            p1 = Vector2.array(self.geom.coords[1])
            segment = p1 - p0
            return segment.angle()
        else:
            raise DDDException("Cannot get line angle of a geometry other than a 2-vertex LineString: %s" % self)

    def translate(self, coords):
        """
        This method modifies the object (since v0.7 2022-10).
        """

        if hasattr(coords, 'geom'):
            coords = coords.geom.coords[0]

        if len(coords) == 2: coords = [coords[0], coords[1], 0.0]
        #result = self.copy()
        result = self

        #if math.isnan(coords[0]) or math.isnan(coords[1]):
        #    logger.warn("Invalid translate coords (%s) for object: %s", coords, self)
        #    return result
        '''
        def _trfun(x, y, z=0.0):
            print(coords)
            print(x, y, z)
            return (x + coords[0], y + coords[1], z + coords[2])
        '''

        if self.geom:
            #trans_func = _trfun
            trans_func = lambda x, y, z=0.0: (x + coords[0], y + coords[1], z + coords[2])
            result.geom = ops.transform(trans_func, self.geom)

        #result.children = [c.translate(coords) for c in self.children]
        for c in self.children:
            c.translate(coords)

        return result

    def rotate(self, angle, origin=None):  # center (bb center), centroid, point
        """
        Angle is in radians.

        This method modifies the object (since v0.7 2022-10).
        """
        if origin is None: origin = (0, 0)
        #result = self.copy()
        result = self
        if self.geom:
            result.geom = affinity.rotate(self.geom, angle, origin=origin, use_radians=True)

        #result.children = [c.rotate(angle, origin) for c in self.children]
        for c in self.children:
            c.rotate(angle, origin)
        return result

    def scale(self, coords, origin=None): # None=(0,0), centroid
        if isinstance(coords, int): coords = float(coords)
        if isinstance(coords, float): coords = [coords, coords, 1.0]
        if len(coords) == 2: coords = [coords[0], coords[1], 1.0]

        if origin is None: origin = (0, 0)
        result = self.copy()
        if self.geom:
            result.geom = affinity.scale(self.geom, coords[0], coords[1], coords[2] if len(coords) > 2 else 0.0, origin)
        result.children = [c.scale(coords, origin) for c in self.children]
        return result

    def bounds(self):
        xmin, ymin, xmax, ymax = (float("inf"), float("inf"), float("-inf"), float("-inf"))
        if self.geom:
            xmin, ymin, xmax, ymax = self.geom.bounds
        for c in self.children:
            cbounds = c.bounds()
            cxmin, cymin = (cbounds[0][0], cbounds[0][1])
            cxmax, cymax = (cbounds[1][0], cbounds[1][1])
            xmin = min(xmin, cxmin)
            ymin = min(ymin, cymin)
            xmax = max(xmax, cxmax)
            ymax = max(ymax, cymax)

        return ((xmin, ymin, 0), (xmax, ymax, 0))

    def size(self):
        bounds = self.bounds()
        return Vector2((bounds[1][0] - bounds[0][0], bounds[1][1] - bounds[0][1]))

    def recenter(self):
        bounds = self.bounds()
        xmin, ymin = bounds[0][:2]
        xmax, ymax = bounds[1][:2]
        center = ((xmin + xmax) / 2, (ymin + ymax) / 2)
        result = self.translate([-center[0], -center[1], 0])
        return result

    def clean(self, eps=None, remove_empty=True, validate=True, fix_invalid=True):
        result = self.copy()
        if result.geom and eps is not None:
            #result = result.buffer(eps, 1, join_style=ddd.JOIN_MITRE).buffer(-eps, 1, join_style=ddd.JOIN_MITRE)
            if eps != 0:
                result.geom = result.geom.buffer(eps, 1, join_style=ddd.JOIN_MITRE, cap_style=ddd.CAP_FLAT)
                #if result.geom and result.geom.is_valid and not result.geom.is_empty:
                result.geom = result.geom.buffer(-eps, 1, join_style=ddd.JOIN_MITRE, cap_style=ddd.CAP_FLAT)
                #else:
                #    result.geom = None
            else:
                result = result.buffer(0)

        if result.geom and result.geom.is_empty:
            result.geom = None

        if result.geom and not result.geom.is_valid:  # Removing this check causes a core dump during 3D generation

            if fix_invalid:
                polygons = []
                geoms = [result.geom] if result.geom.type not in ("MultiPolygon", "MultiLineString", "GeometryCollection") else result.geom.geoms
                for geom in geoms:
                    if geom.type == 'LineString':
                        pass
                    else:
                        item_ext = LineString(geom.exterior.coords[:] + geom.exterior.coords[0:1])
                        #item_ext = Polygon(list(result.geom.exterior.coords)).interiors # coords)
                        item_mls = unary_union(item_ext)
                        geom_polygons = list(polygonize(item_mls))
                        polygons.extend(geom_polygons)
                valid_item = MultiPolygon(polygons)
                result.geom = valid_item  # .convex_hull

                #ddd.group2([result, ddd.shape(LineString(item_ext)).buffer(1).material(ddd.mats.highlight)]).show()

            if not result.geom.is_valid:
                logger.warn("Removed invalid geometry: %s", result)
                result.geom = None

        if result.geom and (result.geom.type != 'GeometryCollection' and not result.geom.is_simple):
            logger.warn("Removed geometry that crosses itself: %s", result)
            result.geom = None

        result.children = [c.clean(eps=eps, remove_empty=remove_empty, validate=validate, fix_invalid=fix_invalid) for c in self.children]

        if remove_empty:
            result.children = [c for c in result.children if (c.children or c.geom)]
            if result.geom and result.geom.is_empty:
                result.geom = None

        if validate:
            try:
                result.validate()
            except DDDException as e:
                logger.debug("Removed geom that didn't pass validation check (%s): %s", result, e)
                result.geom = None

        return result

    def clean_replace(self, eps=None, remove_empty=True, validate=True):
        """
        TODO: This duplicity with .clean() is undesirable, also, implementation has diverged, at a minimum needs to
        implement "fix_invalid" and behave like .clean()
        """
        result = self
        if result.geom and eps is not None:
            #result = result.buffer(eps, 1, join_style=ddd.JOIN_MITRE).buffer(-eps, 1, join_style=ddd.JOIN_MITRE)
            if eps != 0:
                result.geom = result.geom.buffer(eps, 1, join_style=ddd.JOIN_MITRE, cap_style=ddd.CAP_FLAT)
                #if result.geom and result.geom.is_valid and not result.geom.is_empty:
                result.geom = result.geom.buffer(-eps, 1, join_style=ddd.JOIN_MITRE, cap_style=ddd.CAP_FLAT)
                #else:
                #    result.geom = None
            else:
                result = result.buffer(0)
        if result.geom and result.geom.is_empty:
            result.geom = None
        if result.geom and not result.geom.is_valid:
            logger.warn("Removed invalid geometry: %s", result)
            result.geom = None
        if result.geom and (result.geom.type != 'GeometryCollection' and not result.geom.is_simple):
            logger.warn("Removed geometry that crosses itself: %s", result)
            result.geom = None

        result.children = [c.clean_replace(eps=eps, remove_empty=remove_empty, validate=validate) for c in self.children]

        if remove_empty:
            result.children = [c for c in result.children if (c.children or c.geom)]

        if validate:
            try:
                result.validate()
            except DDDException as e:
                logger.warn("Removed geom that didn't pass validation check (%s): %s", result, e)
                result.geom = None

        return result

    def buffer(self, distance, resolution=8, cap_style=ddd.CAP_SQUARE, join_style=ddd.JOIN_MITRE, mitre_limit=5.0):
        '''
        Resolution is the number of points to approximate a quarter circle (as in Shapely).

        Note that, when buffering points, resolution will be applied only if join_style=ddd.JOIN_ROUND

        There are shortcuts to cap and join styles in ddd (eg. ddd.CAP_SQUARE and ddd.JOIN_ROUND).

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
                                           cap_style=cap_style, join_style=join_style, mitre_limit=mitre_limit)
        result.children = [c.buffer(distance, resolution, cap_style, join_style, mitre_limit) for c in self.children]

        return result

    def subtract(self, other):
        """
        Subtracts `other` object from this. If `other` has children, all of them are subtracted.
        Children of this object are conserved.

        Returns a copy of the object.
        """

        result = self.copy()

        # Attempt to optimize (test)
        #if not result.intersects(other):
        #    return result

        '''
        if self.geom and other.geom:
            try:
                diffgeom = result.geom.difference(other.geom)
                result.geom = diffgeom
            except Exception as e:
                logger.error("Error subtracting geometry. Trying cleaning.")
                result = result.clean(eps=0.01)
                if result.geom:
                    try:
                        diffgeom = result.geom.difference(other.geom)
                        result.geom = diffgeom
                    except Exception as e:
                        raise DDDException("Cannot subtract geometries: %s - %s: %s" % (self, other, e),
                                           ddd_obj=ddd.group2([self, other.material(ddd.mats.highlight)]))
        '''

        if other.children or (self.geom and self.geom.type in ('MultiPolygon', 'GeometryCollection')):
            other = other.union()

        #for c in other.children:
        #    result = result.subtract(c)
        if self.geom:
            #union = other.union()
            if other.geom and not other.geom.is_empty:
                result.geom = result.geom.difference(other.geom)

        result.children = [c.subtract(other) for c in result.children]

        return result

    def recurse_geom(self):

        geoms = []
        if self.geom:
            geoms.append(self.geom)

        for c in self.children:
            geoms.extend(c.recurse_geom())

        return geoms

    def coords_iterator(self, recurse=True):
        if self.geom and self.geom.type == 'MultiPolygon':
            for g in self.geom.geoms:
                for coord in g.exterior.coords:
                    yield coord
        elif self.geom and self.geom.type == 'Polygon':
            for coord in self.geom.exterior.coords:
                yield coord
        elif self.geom and self.geom.type == 'GeometryCollection':
            for g in self.geom.geoms:
                for coord in ddd.shape(g).coords_iterator():
                    yield coord
        elif self.geom and self.geom.type == 'LineString':
            for coord in self.geom.coords:
                yield coord
        elif self.geom and self.geom.type == 'Point':
            for coord in self.geom.coords:
                yield coord
        elif self.geom and self.geom.type == 'MultiPoint':
            for g in self.geom.geoms:
                yield g.coords[0]
        elif self.geom and self.geom.type == 'MultiLineString':
            for g in self.geom.geoms:
                for coord in g.coords:
                    yield coord
        elif self.geom:
            raise NotImplementedError("Not implemented coords_iterator for geom: %s" % self.geom.type)

        if recurse:
            for c in self.children:
                for coord in c.coords_iterator(recurse):
                    yield coord


    def _vertex_func_coords(self, func, coords, mask=None):
        ncoords = []
        for iv, v in enumerate(coords):
            if mask is None or mask(v[0], v[1], v[2], iv):
                res = func(v[0], v[1], v[2] if len(v) > 2 else 0.0, iv)
            else:
                res = (v[0], v[1], v[2] if len(v) > 2 else 0.0, iv)
            ncoords.append(res[:len(v)])
            #print("%s > %s" % (v, res))
        return ncoords

    def vertex_func(self, func, mask=None):
        obj = self.copy()
        if obj.geom:
            if obj.geom.type == 'MultiPolygon':
                logger.warn("Vertex Func applied to MultiPolygon is currently invalid (only applies to exteriors and uses deprecated Shapely coords assignation)")
                for g in obj.geom.geoms:
                    g.exterior.coords = self._vertex_func_coords(func, g.exterior.coords, mask=mask)
            elif obj.geom.type == 'Polygon':
                obj.geom = ddd.polygon(self._vertex_func_coords(func, obj.geom.exterior.coords, mask=mask)).geom
            elif obj.geom.type == 'LineString':
                obj.geom = ddd.line(self._vertex_func_coords(func, obj.geom.coords, mask=mask)).geom
            else:
                #logger.warn("Unknown geometry for 2D vertex func")
                raise DDDException("Unknown geometry for 2D vertex func: %s" % self)

        obj.children = [c.vertex_func(func) for c in self.children]
        return obj

    def vertex_list(self, recurse=True):
        return list(self.coords_iterator(recurse=recurse))

    def vertex_count(self):
        """
        Currently this count does not include children vertex count.
        """
        if not self.geom:
            return 0
        elif self.geom.type == 'MultiPolygon':
            return sum([len(p.exterior.coords) for p in self.geom.geoms])
        elif self.geom.type == 'MultiLineString':
            return sum([len(p.coords) for p in self.geom.geoms])
        elif self.geom.type == 'MultiPoint':
            return sum([len(p.coords) for p in self.geom.geoms])
        elif self.geom.type == 'Polygon':
            if self.geom.is_empty: return 0
            return len(self.geom.exterior.coords) + sum([len(i.coords) for i in self.geom.interiors])
        else:
            try:
                return len(self.geom.coords)
            except Exception as e:
                logger.warn("Error calculating vertex count %s: %s", self.geom, e)  # Cannot log self here, as this method is used in __repr__
        return None

    def remove_z(self):
        """
        Removes the z coordinate leaving 2-dimension vectors for coordinates.

        This method returns a copy of the object, and applies the same operation to children.
        """
        result = self.copy()
        if self.geom:
            if result.geom.type == "MultiPolygon":
                pols = []
                for g in result.geom.geoms:
                    nnext = [(c[0], c[1]) for c in g.exterior.coords]
                    nnints = []
                    for gi in g.interiors:
                        nnints.append([(c[0], c[1]) for c in gi.coords])
                    pols.append(Polygon(nnext, nnints))
                result.geom = MultiPolygon(pols)
            elif result.geom.type == "MultiLineString":
                for g in result.geom.geoms:
                    g.coords = [(c[0], c[1]) for c in g.coords]
                    #g.coords[:,2] = 0
            elif result.geom.type == "Polygon":
                #result.geom.exterior.coords = [(x, y) for (x, y, _) in result.geom.exterior.coords]
                #for g in result.geom.interiors:
                #    g.coords = [(x, y) for (x, y, _) in g.coords]
                nnext = [(c[0], c[1]) for c in result.geom.exterior.coords]
                nnints = []
                for g in result.geom.interiors:
                    nnints.append([(c[0], c[1]) for c in g.coords])
                result.geom = Polygon(nnext, nnints)

            else:
                result.geom.coords = [(c[0], c[1]) for c in result.geom.coords]
        result.children = [c.remove_z() for c in result.children]
        return result

    def union(self, other=None):
        result = self.copy()
        return result.union_replace(other)

    def union_replace(self, other=None):
        """
        Returns a copy of this object to which geometry from other object has been unioned.
        If the second object has children, they are also unioned recursively.

        If the second object is None, all children of this are unioned.
        """

        result = self
        #result = result.flatten().clean()

        #
        '''
        geoms = result.geom_recursive() + (other.geom_recursive() if other else [])
        geoms = [g for g in geoms if g is not None]
        if geoms:
            try:
                result.geom = ops.unary_union(geoms)
                result.validate()
            except Exception as e:
                logger.warn("Could not calculate union for: %s", geoms)
                raise DDDException("Could not calculate union for: %s", self)
        else:
            result.geom = None
        result.children = []
        #result = result.clean()
        return result
        '''

        if not result.is_empty():
            if len(result.children) == 1:
                # Individualize(always=true) was added to solve "single children multipolygon".union() returning empty,
                # but seems to fail if applied to every object, so the workaround above was applied
                result = result.individualize(always=True)
            else:
                result = result.individualize()

        objs = result.children
        result.children = []

        if len(objs) > 0:
            objs[0].union_replace()
            while len(objs) > 1:
                newo = objs[0].union_replace(objs[1])
                objs = objs[2:] + [newo]
        if objs:
            if result.geom:
                if objs[0].geom and not objs[0].is_empty():
                    #result.geom = result.geom.union(objs[0].geom)
                    result.geom = ops.unary_union([result.geom, objs[0].geom])
            else:
                result.geom = objs[0].geom

        if other:
            union = other.union()  # .clean(eps=0)  # NOTE: Until 2022-10 this involved 'clean(eps=0), but this destroys degenerate intersections
            if result.geom and union.geom:
                try:
                    #result.geom = result.geom.union(union.geom)
                    result.geom = ops.unary_union([result.geom, union.geom])
                except Exception as e:
                    logger.error("Cannot perform union (1st try) between %s and %s: %s", result, other, e)
                    try:
                        result.geom = ops.unary_union([result.geom, union.geom])
                        result = result.clean(eps=0)
                    except Exception as e:
                        logger.error("Cannot perform union (2nd try) between %s and %s: %s", result, other, e)
                        result = result.clean(eps=0.001) #.simplify(0.001)
                        other = other.clean(eps=0.001) #.simplify(0.001)
                        #result.geom = result.geom.union(union.geom)
                        result.geom = ops.unary_union([result.geom, union.geom])

            elif union.geom:
                result.geom = union.geom

        return result

    def intersection(self, other):
        """
        Calculates the intersection of this object and children with
        the other object (and children). Does not perform a union on this object, so
        if this object contains children, each intersection will be calculated
        separately.
        """
        result = self.copy()
        other = other.union()

        if result.geom and other.geom:
            result.geom = result.geom.intersection(other.geom)
        result.children = [c.intersection(other) for c in self.children]
        result.children = [c for c in result.children if not c.is_empty()]

        return result

    def intersects(self, other):
        """
        Calculates if this object and children intersects with any of
        the other object (and children).
        """
        #logger.debug("Intersects: %s with %s", self, other)
        other = other.union()

        if (not other.geom) or other.geom.is_empty:
            return False

        if self._strtree:
            #logger.info("Using STRTree for 'intersects' operation: %s", self)
            cand_geoms = self._strtree.query(other.geom)
            return any((cg.intersects(other.geom) for cg in cand_geoms))

        if self.geom:
            if self.geom.intersects(other.geom):
                return True
        for c in self.children:
            if c.intersects(other):
                return True
        return False

    def overlaps(self, other):
        """
        """
        other = other.union()
        if self.geom and not self.geom.empty:
            if self.geom.overlaps(other.geom):
                return True
        for c in self.children:
            if c.overlaps(other):
                return True
        return False

    def crosses(self, other):
        """
        """
        other = other.union()
        if self.geom:
            if self.geom.crosses(other.geom):
                return True
        for c in self.children:
            if c.crosses(other):
                return True
        return False

    def touches(self, other):
        """
        """
        geom = self.union()
        other = other.union()
        if self.geom and other.geom:
            return geom.geom.touches(other.geom)
        return False

    def contains(self, other):
        """
        Note: distinction between union self or each of the children (currently, each children in self vs other union)
        """
        other = other.union()
        if self.geom and not self.geom.is_empty and other.geom and not other.geom.is_empty:
            if self.geom.contains(other.geom):
                return True
        for c in self.children:
            if c.contains(other):
                return True
        return False

    def length(self):
        return self.geom.length

    def snap_vertices_to(self, other, tolerance=ddd.EPSILON * 10):
        """
        """
        result = self.copy()
        if other.is_empty():
            raise DDDException("Cannot snap geometry %s to empty geometry %s." % (self, other))
        if other.children:
            raise DDDException("Cannot snap geometry %s to geometry with children: %s." % (self, other))

        result.geom = ops.snap(result.geom, other.geom, tolerance)
        result.children = [c.snap(other, tolerance) for c in self.children]

        return result

    def area(self):
        """
        Returns the area of this shape.
        Children are unioned before computing the area.
        If the geometry is empty or there is no geometry, 0 is returned.
        """
        area_union = self
        if self.children:
            area_union = self.union()

        area = area_union.geom.area if self.geom else 0
        return area

    def is_empty(self):
        """
        Tells whether this object has no geometry, or geometry is empty, and
        all children are also empty.
        """
        if self.geom and not self.geom.is_empty:
            return False
        for c in self.children:
            if not c.is_empty():
                return False
        return True

    def convex_hull(self):
        result = self.copy().union()
        if result.geom:
            result.geom = result.geom.convex_hull
        else:
            return None
        return result

    def validate(self):
        if self.geom:
            if not self.geom.is_valid:
                raise DDDException("Invalid polygon: polygon is invalid for Shapely.")
            if self.geom.is_empty:
                raise DDDException("Invalid polygon: empty.")
            #if not self.geom.is_simple:
            #    raise DDDException("Invalid polygon: polygon is not simple.")
            if self.geom.type == "Polygon":
                if len(list(self.geom.exterior.coords)) < 3:
                    raise DDDException("Polygon with invalid number of coordinates (<3).", ddd_obj=self)
                for interior in self.geom.interiors:
                    if len(list(interior.coords)) < 3:
                        raise DDDException("Polygon with invalid number of interior coordinates (<3).", ddd_obj=self)
                if self.geom.area < ddd.EPSILON:
                    raise DDDException("Polygon with null area.", ddd_obj=self)

        for c in self.children:
            c.validate()

    def individualize(self, remove_interiors=False, always=False):
        """
        Return a group of multiple DDD2Objects if the object is a GeometryCollection.

        If `always` is true, always create a parent node which contains a node per geometry even
        if it was already a simple geometry. This is useful if we want to iterate individual
        geometries regardless of the original geometry type.
        """
        result = self.copy()

        newchildren = []

        if self.geom and self.geom.type == 'GeometryCollection':
            result.geom = None
            for partialgeom in self.geom.geoms:
                newobj = self.copy(copy_children=False)
                newobj.geom = partialgeom
                newchildren.append(newobj)

        elif self.geom and self.geom.type == 'MultiPolygon':
            result.geom = None
            for partialgeom in self.geom.geoms:
                newobj = self.copy(copy_children=False)
                newobj.geom = partialgeom
                newchildren.append(newobj)

        elif self.geom and self.geom.type == 'MultiLineString':
            result.geom = None
            for partialgeom in self.geom.geoms:
                newobj = self.copy(copy_children=False)
                newobj.geom = partialgeom
                newchildren.append(newobj)

        elif self.geom and self.geom.type == 'MultiPoint':
            result.geom = None
            for partialgeom in self.geom.geoms:
                newobj = self.copy(copy_children=False)
                newobj.geom = Point(partialgeom.coords[0])
                newchildren.append(newobj)

        elif self.geom and self.geom.type == 'Polygon' and remove_interiors and self.geom.interiors:
            result.geom = None
            newobj = self.copy(copy_children=False)
            newobj.geom = self.geom.exterior
            newchildren.append(newobj)

        elif always:
            # Move as a child for consistency
            result.geom = None
            newobj = self.copy(copy_children=False)
            newobj.geom = self.geom
            newchildren.append(newobj)

        try:
            result.children = [c.individualize() for c in (self.children + newchildren)]
        except Exception as e:
            logger.error("Error calling individualize on %s, children (%s): %s", self, (self.children + newchildren), e)
            raise

        return result


    def triangulate(self, twosided=False, ignore_children=False):
        """
        Returns a triangulated mesh (3D) from this 2D shape.
        """
        if (twosided):
            logger.warn("Calling 'triangulate' with twosided=True has seen to give wrong normals (black materials) due to vertex merging: %s", self)
        if self.geom:
            if self.geom.type == 'MultiPolygon' or self.geom.type == 'MultiLineString' or self.geom.type == 'GeometryCollection':
                meshes = []
                for geom in self.geom.geoms:
                    pol = DDDObject2(geom=geom, extra=dict(self.extra), name="Triangulated Multi: %s" % self.name)
                    mesh = pol.triangulate(twosided)
                    meshes.append(mesh)
                result = self.copy3()
                result.children = meshes
            elif not self.geom.is_empty and not self.geom.type == 'LineString' and not self.geom.type == 'Point':
                # Triangulation mode is critical for the resulting quality and triangle count.
                #mesh = creation.extrude_polygon(self.geom, height)
                #vertices, faces = creation.triangulate_polygon(self.geom)  # , min_angle=math.pi / 180.0)
                try:
                    vertices, faces = creation.triangulate_polygon(self.geom, triangle_args="p", engine='triangle')  # Flat, minimal, non corner-detailing ('pq30' produces more detailed triangulations)
                except Exception as e:
                    logger.info("Could not triangulate geometry for %s (geom=%s): %s", self, self.geom, e)
                    return ddd.DDDObject3("Cannot triangulate: %s" % e)
                    #raise

                    try:
                        self.geom = self.clean(eps=0.01).geom
                        vertices, faces = creation.triangulate_polygon(self.geom, triangle_args="p", engine='triangle')  # Flat, minimal, non corner-detailing ('pq30' produces more detailed triangulations)
                    except Exception as e:
                        logger.error("Could not triangulate geometry (after clean) %s: %s", self.geom, e)
                        #raise DDDException("Could triangulate geometry (after convex hull) %s: %s" % (self.geom, e), ddd_obj=self)
                        vertices, faces = None, None
                        raise

                if vertices is not None:
                    # FIXME: This seems to cause materials to fail (eg. golf flag material), as opossed ot  .twosided() method
                    if twosided:
                        faces2 = np.fliplr(faces)
                        faces = np.concatenate((faces, faces2))

                    mesh = Trimesh([(v[0], v[1], 0.0) for v in vertices], faces)
                    #mesh = creation.extrude_triangulation(vertices=vertices, faces=faces, height=0.2)
                    mesh.merge_vertices()
                    result = self.copy3(mesh=mesh)
                else:
                    result = DDDObject3(name="Could not triangulate (error during triangulation)")

                # Map UV coordinates if they were set on the polygon
                if self.get('uv', None):
                    from ddd.ops import uvmapping
                    result = uvmapping.map_3d_from_2d(result, self)

            else:
                result = ddd.DDDObject3("Cannot triangulate: unknown geometry type")
        else:
            result = ddd.DDDObject3()

        if self.mat is not None:
            result = result.material(self.mat)

        # Copy extra information from original object
        #result.name = self.name if result.name is None else result.name
        result.extra['_extruded_shape'] = self

        if not ignore_children:
            result.children.extend([c.triangulate(twosided) for c in self.children])

        return result

    def revolve(self):
        # Coords are reversed so 'creation.revolve' creates outwards-facing meshes for ddd.polygon()
        coords = list(reversed(list(self.remove_z().coords_iterator())))
        tmesh = creation.revolve(coords)
        obj = ddd.mesh(tmesh, name=self.name)
        return obj

    def extrude(self, height, center=False, cap=True, base=True):
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
                for (idx, geom) in enumerate(self.geom.geoms):
                    pol = ddd.shape(geom).copy_from(self, copy_children=False)
                    pol.name = "%s (split extr %d)" % (self.name, idx)
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
                    mesh = extrusion.extrude_triangulation(vertices=vertices,
                                                           faces=faces,
                                                           height=abs(height),
                                                           cap=cap, base=base)
                    mesh.merge_vertices()
                    result = ddd.DDDObject3(mesh=mesh)
                except Exception as e:
                    raise DDDException("Could not extrude %s: %s" % (self, e), ddd_obj=self)

                if center:
                    result = result.translate([0, 0, -height / 2])
                elif height < 0:
                    result = result.translate([0, 0, height])

            elif not self.geom.is_empty and self.geom.type == 'LineString':
                coords_a = list(self.geom.coords)
                coords_b = list(self.geom.coords)
                mesh = extrusion.extrude_coords(coords_a, coords_b, abs(height))

                #mesh2 = extrusion.extrude_coords(list(reversed(coords_a)), list(reversed(coords_b)), abs(height))
                #offset = len(list(mesh.vertices))
                #mesh.vertices = list(mesh.vertices) + list(mesh2.vertices)
                #mesh.faces = list(mesh.faces) + [(f[0] + offset, f[1] + offset, f[2] + offset) for f in mesh2.faces]

                result = DDDObject3(mesh=mesh)
                if center:
                    result = result.translate([0, 0, -height / 2])
                elif height < 0:
                    result = result.translate([0, 0, height])

            else:
                #logger.warn("Cannot extrude (empty polygon)")
                result = DDDObject3()
        else:
            result = DDDObject3()

        result.children.extend([c.extrude(height, cap=cap, base=base) for c in self.children])

        # Copy extra information from original object
        result.name = self.name if result.name is None else result.name
        result.extra = dict(self.extra)
        result.extra['_extruded_shape'] = self

        if self.mat is not None:
            result = result.material(self.mat)

        return result

    def extrude_along(self, path):
        """
        Extrudes a shape along a path
        """
        trimesh_path = path.geom.coords
        mesh = creation.sweep_polygon(self.remove_z().geom, trimesh_path, triangle_args="p", engine='triangle')
        mesh.fix_normals()
        result = self.copy3()
        result.mesh = mesh
        return result

    def extrude_step(self, obj_2d, offset, cap=True, base=True, method=ddd.EXTRUSION_METHOD_WRAP):
        # Triangulate and store info for 3D extrude_step

        if obj_2d.children:
            raise DDDException("Cannot extrude_step with children: %s" % obj_2d, ddd_obj=obj_2d)

        if base:
            result = self.triangulate()
            if result.mesh:
                result.mesh.faces = np.fliplr(result.mesh.faces)
        else:
            result = self.copy3()
            '''
            result = DDDObject3()
            # Copy extra information from original object
            result.name = self.name if result.name is None else result.name
            result.extra = dict(self.extra)
            if self.mat is not None:
                result = result.material(self.mat)
            '''

        result.extra['_extrusion_steps'] = 0
        result.extra['_extrusion_last_shape'] = self
        result = result.extrude_step(obj_2d, offset, cap, method=method)
        return result

    def split(self, other):
        splitter = other  # .union()
        result = self.copy()
        result.name = "%s (split)" % self.name

        result.children = [c.split(other) for c in self.children]

        if self.geom:
            splits = ops.split(self.geom, splitter.geom)
            result.geom = None
            for s in splits.geoms:
                shape = ddd.shape(s)
                shape.copy_from(self, copy_children=False)
                result.append(shape)
            #result.append(ddd.shape(splits[1]))qq
            #self.geom = splits[1]

        return result

    def orient(self, ccw=True):
        result = self.copy()
        if result.geom:
            result.geom = polygon.orient(result.geom, 1 if ccw else -1)
        result.children = [c.orient(ccw) for c in self.children]
        return result

    def orient_from(self, other):
        """
        Orients a line so it starts from the closest point to `other` object.
        """
        result = self.copy()
        dist_0 = other.distance(ddd.point(self.geom.coords[0]))
        dist_1 = other.distance(ddd.point(self.geom.coords[-1]))
        if dist_1 < dist_0:
            result.geom.coords = reversed(list(result.geom.coords))
        return result

    def simplify(self, distance):
        """
        Keywords: decimate, collapse
        """
        result = self.copy()
        if self.geom:
            result.geom = result.geom.simplify(distance, preserve_topology=True)
            #result.geom = result.geom.simplify(distance)  #, preserve_topology=True)
        result.children = [c.simplify(distance) for c in self.children]
        return result

    def grid_points(self, spacing=0.1):
        """
        """
        result = []
        shape = self.union()
        bounds = self.bounds()

        start_x = (bounds[0][0] - spacing) // spacing * spacing
        end_x = (bounds[1][0] + spacing) // spacing * spacing
        start_y = (bounds[0][1] - spacing) // spacing * spacing
        end_y = (bounds[1][1] + spacing) // spacing * spacing

        for x in np.linspace(start_x, end_x, int((end_x - start_x) / spacing + 1), endpoint=True):
            for y in np.linspace(start_y, end_y, int((end_y - start_y) / spacing + 1), endpoint=True):
                point = ddd.point((x, y))
                if point.intersects(shape):
                    result.append([x, y])
        return result

    def random_points(self, num_points=1, density=None, filter_func=None):
        """
        If filter_func is specified, points are passed to this function and accepted if it returns True.

        This function returns an array, not a Node2.
        """
        # TODO: use density or count, accoridng to polygon area :?
        # TODO: support line geometries
        result = []
        (minx, miny, _), (maxx, maxy, _) = self.bounds()

        while len(result) < num_points:
            pnt = geometry.Point(random.uniform(minx, maxx), random.uniform(miny, maxy))
            #if self.contains(ddd.point(pnt.coords)):
            if self.geom.contains(pnt):
                if filter_func is None or filter_func(pnt.coords[0]):
                    result.append(pnt.coords[0])

        return result

    def linearize(self):
        """
        Converts all 2D shapes to Linear objects (LineStrings or LinearRing).
        It takes exterior polygons when holes are present.

        TODO: How is this method different from outline() ?  check usages + fix/document // linearstring vs linearrings, last vertex, etc
        """
        result = self.copy()
        if self.geom:
            result.geom = result.geom.exterior if result.geom.type == "Polygon" else result.geom
        result.children = [c.linearize() for c in self.children]
        return result

    def outline(self):
        """
        Returns the outline of the current shape **as linear features**.
        Works for Polygon and MultiPolygon shapes (input is individualize() first).

        TODO: How is this method different from linearize() ?  check usages + fix/document // linearstring vs linearrings, last vertex, etc
        TODO: review Shapely exterior vs boundary
        """
        result = self.copy().individualize().clean()
        if result.geom and result.geom.type == "Polygon":
            result.geom = LineString(list(result.geom.exterior.coords))
        #elif result.geom:
        #    raise DDDException("Cannot take linearized outline from geometry:
        result.children = [c.outline() for c in result.children]
        return result

    '''
    def outline(self):
        result = self.copy()
        if result.geom:
            result.geom = result.geom.boundary
        #if result.geom and result.geom.type == "Polygon":
        #    result.geom = LineString(list(result.geom.exterior.coords))
        result.children = [c.outline() for c in result.children]
        return result
    '''


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

        if self._strtree:
            #logger.info("Using STRTree for 'closest' operation: %s", self)
            nearest = self._strtree.nearest(other.geom)
            return (nearest._ddd_obj, nearest._ddd_obj.geom.distance(other.geom))

        if self.geom:
            closest_o = self
            closest_d = self.geom.distance(other.geom)

        for c in self.children:
            c_o, c_d = c.closest(other)
            if c_d < closest_d:
                closest_o, closest_d = c_o, c_d

        return closest_o, closest_d


    def iterate_segments(self):
        vertices = list(self.coords_iterator())
        for (s1, s2) in zip(vertices[:-1], vertices[1:]):
            yield ddd.line((s1, s2), name="%s Segment" % self.name)

    def interpolate_segment(self, d, normalized=False):
        """
        Interpolates a distance along a LineString, returning:
            coords_p, segment_idx, segment_coords_a, segment_coords_b

        Z coordinate will also be interpolated if available (as Shapely .interpolate() does).

        Returns:
        - coords_p:
        - segment_idx: index of the previous point
        - segment_coords_a, segment_coords_b:

        Note that returns coordinates, not DDD objects.
        """
        # Walk segment
        l = 0.0
        coords = None
        try:
            coords = self.geom.coords
        except Exception as e:
            raise DDDException("Could not interpolate distance on segment %s: %s" % (self, e))

        length = self.geom.length
        for idx in range(len(coords) - 1):
            p, pn = coords[idx:idx+2]
            pl = math.sqrt((pn[0] - p[0]) ** 2 + (pn[1] - p[1]) ** 2)
            l += pl
            if l >= ((d * length) if normalized else d):
                return (self.geom.interpolate(d, normalized).coords[0], idx, p, pn)
        return (self.geom.interpolate(d, normalized).coords[0], idx, p, pn)

    def closest_segment(self, other):
        """
        Closest segment in a LineString to other geometry.
        Does not support children in "other" geometry.

        If Z coordinates are available, coords_p will be interpolated in the Z dimension too (as interpolate_segment() and Shapely .interpolate() do).

        Returns: coords_p, segment_idx, segment_coords_a, segment_coords_b, closest_object, closest_object_d
        """
        closest_self, closest_d = self.closest(other)
        #logger.debug("Closest: %s  %s > %s", closest_d, closest_self, other)

        try:
            # For ring types we care about the segment
            # FIXME: this does not account for polygon interiors, in case they are needed
            if closest_self.geom.type == 'Polygon':
                linearized = closest_self.outline()
                d = linearized.geom.project(other.geom)
                result = (*linearized.interpolate_segment(d), closest_self, d)
            #elif closest_self.geom.type in ('MultiPolygon', 'MultiGeometry'):
            #    # WARNING: resulting indexes will be incorrect, the individualized object does not really exist in the self
            #    closest_self, closest_d = closest_self.individualize().closest(other)
            #    linearized = closest_self.outline()
            #    d = linearized.geom.project(other.geom)
            #    result = (*linearized.interpolate_segment(d), closest_self, d)
            else:
                d = closest_self.geom.project(other.geom)
                result = (*closest_self.interpolate_segment(d), closest_self, d)
        except Exception as e:
            raise DDDException("Error finding closest segment from %s to %s (closest_self=%s): %s" % (self, other, closest_self, e))

        #ddd.group([other.buffer(5.0),  ddd.point(result[2]).buffer(5.0).material(ddd.mat_highlight), ddd.line([result[2], result[3]]).buffer(2.0), ddd.point(result[0]).buffer(5.0), closest_self.buffer(0.2)]).show()
        return result

    def vertex_index(self, coords):
        """
        Returns the closest vertex in this geometry to other geometry.
        Coords can be a coordinate tuple or a Point-like DDDObject2
        Does not support children in "other" geometry.
        """
        if isinstance(coords, DDDObject2) and coords.geom.type == "Point":
            if coords.children:
                raise DDDException("Calculating closest vertex to a geometry with children is not supported.")
            coords = coords.geom.coords[0]
        coords = np.array(coords)
        if self.geom.type != 'LineString':
            raise Exception("Only LineString is supported for 'closest_vertex' method: %s %s" % (self, coords))
        if self.geom:
            for idx, c in enumerate(self.geom.coords):
                #print (idx, c, other.geom.coords[0])
                #if (c == other.geom.coords[0]):
                if np.linalg.norm(np.array(c) - coords) < (2 * ddd.EPSILON):
                    return idx

        return None

    def insert_vertex_at_distance(self, distance):
        """
        Inserts a vertex at a given distance on this geometry. Distance is interpolated along the object.

        If the vertex coincides with an existing neighbour vertex, it won't be added.

        Returns the coordinates of the inserted vertex.

        This method mutates the object.
        """

        coords, segment_idx, segment_coords_a, segment_coords_b = self.interpolate_segment(distance)

        dist1 = np.linalg.norm(np.array(coords) - np.array(segment_coords_a))
        dist2 = np.linalg.norm(np.array(coords) - np.array(segment_coords_b))

        if dist1 > ddd.EPSILON and dist2 > ddd.EPSILON:
            self.geom.coords = self.geom.coords[:segment_idx + 1] + [coords] + self.geom.coords[segment_idx + 1:]

        return coords

    def perpendicular(self, distance=0.0, length=1.0, double=False, normalized=False):

        (coords_p, segment_idx, segment_coords_a, segment_coords_b) = self.interpolate_segment(distance, normalized)

        try:
            dir_vec = (segment_coords_b[0] - segment_coords_a[0], segment_coords_b[1] - segment_coords_a[1])
            dir_vec_length = math.sqrt(dir_vec[0] ** 2 + dir_vec[1] ** 2)
            dir_vec = (dir_vec[0] / dir_vec_length, dir_vec[1] / dir_vec_length)
            perpendicular_vec = (-dir_vec[1], dir_vec[0])
        except  ZeroDivisionError as e:
            raise DDDException("Error calculating perpendicular geometry to: %s" % self, ddd_obj=self)

        left = (coords_p[0] + perpendicular_vec[0] * length, coords_p[1] + perpendicular_vec[1] * length, coords_p[2] if len(coords_p) > 2 else 0)
        right = (coords_p[0] - perpendicular_vec[0] * length, coords_p[1] - perpendicular_vec[1] * length, coords_p[2] if len(coords_p) > 2 else 0)

        #self.copy(children=None)
        if not double:
            result = ddd.line([coords_p, left])
        else:
            result = ddd.line([right, left])

        #ddd.group2([self.buffer(0.1), result.buffer(0.1).material(ddd.mats.highlight)]).show()

        return result

    def vertex_bisector(self, vertex_index, length=1.0):
        """
        Returns the bisector at a vertex in a line segment (this is the "perpendicular" at the vertex)
        """

        if vertex_index == 0:
            return self.perpendicular(distance=0.0, length=length, double=True)
        if vertex_index >= len(self.geom.coords) - 1:
            return self.perpendicular(distance=self.length(), length=length, double=True)

        vm1 = Vector3(self.geom.coords[vertex_index - 1])
        v0 = Vector3(self.geom.coords[vertex_index])
        v1 = Vector3(self.geom.coords[(vertex_index + 1) % len(self.geom.coords)])

        d = v1 - v0
        dm1 = v0 - vm1

        bs0 = (dm1.normalized() + d.normalized()).normalized()
        bs0 = Vector3([-bs0.y, bs0.x, 0])

        p1 = v0 + bs0 * length
        p2 = v0 - bs0 * length

        perpendicular = ddd.line([p1, p2])
        return perpendicular

    def line_substring(self, start_dist, end_dist, normalized=False):
        """
        Returns a line between the specified distances.
        Negative values are taken in the reverse direction.
        This is based on the Shapely operation of the same name.
        """

        if self.children:
            raise DDDException("Cannot calculate line_substring of objects with children.")
        if not self.geom or self.geom.type != "LineString":
            raise DDDException("Cannot calculate line_substring of non LineString objects.")

        substr_length = self.geom.length if not normalized else 1.0

        if end_dist < 0: end_dist = substr_length + end_dist
        if start_dist < 0: start_dist = substr_length + start_dist

        result = self.copy()
        geom = ops.substring(result.geom, start_dist, end_dist, normalized)
        result.geom = geom

        return result

    def geom_recursive(self):
        """
        Returns a list of all Shapely geometries recursively.

        Note: Currently this method also adds Shapely geometries an attribute `_ddd_obj` pointing to the DDD object that references it. This will be changed.
        """
        geoms = []
        if self.geom:
            self.geom._ddd_obj = self  # TODO: This is unsafe, generate a dictionary of id(geom) -> object (see https://shapely.readthedocs.io/en/stable/manual.html#strtree.STRtree.strtree.query)
            geoms = [self.geom]
        if self.children:
            for c in self.children:
                cgems = c.geom_recursive()
                geoms.extend(cgems)
        return geoms

    # DDDObject2 didn't have this, and Presentations are used instead: normalize with DDDNode. Added to support render to pyrender (?)
    def _recurse_meshes(self, instance_mesh, instance_marker):
        cmeshes = []
        if self.children:
            for c in self.children:
                cmeshes.extend(c._recurse_meshes(instance_mesh, instance_marker))
        return cmeshes

    # DDDObject2 didn't have this, and Presentations are used instead: normalize with DDDNode
    def _recurse_scene_tree(self, path_prefix, name_suffix, instance_mesh, instance_marker, include_metadata, scene=None, scene_parent_node_name=None, usednames=None):

        if usednames is None: usednames = set()
        node_name = self.uniquename(usednames)
        usednames.add(node_name)

        # Add metadata to name
        metadata = self.metadata(path_prefix, name_suffix)

        if False:  # serialize metadata in name
            #print(json.dumps(metadata))
            serialized_metadata = base64.b64encode(json.dumps(metadata, default=D1D2D3.json_serialize).encode("utf-8")).decode("ascii")
            encoded_node_name = node_name + "_" + str(serialized_metadata)

        metadata_serializable = None
        if include_metadata:
            metadata_serializable = json.loads(json.dumps(metadata, default=ddd.json_serialize))
        #scene.metadata['extras'] = test_metadata

        # Do not export nodes indicated 'ddd:export-as-marker' if not exporting markers
        if metadata.get('ddd:export-as-marker', False) and not instance_marker:
            return scene
        if metadata.get('ddd:marker', False) and not instance_marker:
            return scene

        scene_node_name = node_name.replace(" ", "_")
        scene_node_name = metadata['ddd:path'].replace(" ", "_")  # TODO: Trimesh requires unique names, but using the full path makes them very long. Not using it causes instanced geeometry to fail.

        node_transform = transformations.identity_matrix()

        #if scene is None:
        #    scene = Scene(base_frame=scene_node_name)
        #    # Add node metadata to scene metadata (first node metadata seems not available at least in blender)
        #    scene.metadata['extras'] = metadata_serializable

        #if mesh is None: mesh = ddd.marker().mesh
        #print("Adding: %s to %s" % (scene_node_name, scene_parent_node_name))
        scene.graph.update(frame_to=scene_node_name, frame_from=scene_parent_node_name, matrix=node_transform, geometry_flags={'visible': True}, extras=metadata_serializable)

        # TODO: scene.graph.transforms contain the list of transform names, so using "usednames" may be unnecesary
        #print(scene.graph.transforms.__dict__)

        if self.children:
            for idx, c in enumerate(self.children):
                c._recurse_scene_tree(path_prefix=path_prefix + node_name + "/", name_suffix="#%d" % (idx),
                                      instance_mesh=instance_mesh, instance_marker=instance_marker, include_metadata=include_metadata,
                                      scene=scene, scene_parent_node_name=scene_node_name, usednames=usednames)

        # Serialize metadata as dict
        #if False:
        #    #serializable_metadata_dict = json.loads(json.dumps(metadata, default=D1D2D3.json_serialize))
        #    #scene.metadata['extras'] = serializable_metadata_dict

        return scene

    def save(self, path, instance_marker=None, instance_mesh=None, scale=1.0):
        """
        """

        if instance_marker is None:
            instance_marker = D1D2D3Bootstrap.export_marker
        if instance_mesh is None:
            instance_mesh = D1D2D3Bootstrap.export_mesh

        if path.endswith(".svg"):
            logger.info("Exporting 2D as SVG to: %s", path)
            #data = geom._repr_svg_().encode()
            data = DDDSVG.export_svg(self, instance_mesh=instance_mesh, instance_marker=instance_marker, scale=scale)
            data = data.encode()

        elif path.endswith(".png"):
            logger.info("Exporting 2D as PNG to: %s", path)
            data = DDDSVG.export_svg(self, instance_mesh=instance_mesh, instance_marker=instance_marker, scale=scale)
            svgdata = data.encode("utf8")
            data = cairosvg.svg2png(bytestring=svgdata, scale=1.0)  # scale  #, write_to=path) parent_width, parent_height, dpi, scale, unsafe.

            # NOTE: Also, using Inkscape: https://stackoverflow.com/questions/6589358/convert-svg-to-png-in-python

        elif path.endswith(".json"):
            logger.info("Exporting 2D as JSON to: %s", path)
            #rotated = self.rotate([-math.pi / 2.0, 0, 0])
            #scene = rotated._recurse_scene("", instance_mesh=instance_mesh, instance_marker=instance_marker)
            data = DDDJSONFormat.export_json(self, "", instance_mesh=instance_mesh, instance_marker=instance_marker)
            data = data.encode("utf8")

        elif path.endswith('.geojson'):
            logger.info("Exporting 2D as GeoJSON to: %s", path)
            #rotated = self.rotate([-math.pi / 2.0, 0, 0])
            #scene = rotated._recurse_scene("", instance_mesh=instance_mesh, instance_marker=instance_marker)
            data = DDDGeoJSONFormat.export_geojson(self, "", instance_mesh=instance_mesh, instance_marker=instance_marker)
            data = data.encode("utf8")

        else:
            raise DDDException("Invalid 2D save format (filename=%s)" % path)

        # If path is just a .extension (eg .glb), returns the result file as a byte buffer.
        return_data = (path.split(".")[0] == '')
        if return_data:
            return data

        with open(path, 'wb') as f:
            f.write(data)

DDDObject2 = DDDNode2
