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

from _collections_abc import Iterable
import base64
import copy
import hashlib
import json
import logging
import math
import random
import sys
import webbrowser
from lark import Lark

import PIL
import cairosvg
from csg import geom as csggeom
from csg.core import CSG
from matplotlib import colors
from shapely import geometry, affinity, ops
from shapely.geometry import shape, polygon
from shapely.geometry.linestring import LineString
from shapely.geometry.polygon import orient
from trimesh import creation, primitives, boolean, transformations, remesh
import trimesh
from trimesh.base import Trimesh
from trimesh.path import segments
from trimesh.path.entities import Line
from trimesh.path.path import Path, Path3D, Path2D
from trimesh.scene.scene import Scene, append_scenes
from trimesh.scene.transforms import TransformForest
from trimesh.transformations import quaternion_from_euler
from trimesh.visual.color import ColorVisuals
from trimesh.visual.material import SimpleMaterial, PBRMaterial
from trimesh.visual.texture import TextureVisuals

from ddd.core.cli import D1D2D3Bootstrap
from ddd.core.exception import DDDException
from ddd.materials.atlas import TextureAtlas
from ddd.ops import extrusion

import numpy as np
from trimesh.util import concatenate
from shapely.ops import unary_union
from geojson.feature import FeatureCollection
from lark.visitors import Transformer
from ddd.core.selectors.selector_ebnf import selector_ebnf
from ddd.core.selectors.selector import DDDSelector
from ddd.formats.json import DDDJSONFormat
from ddd.formats.svg import DDDSVG
from trimesh.convex import convex_hull
import os
from ddd.core import settings


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class D1D2D3():

    #BASE_DIR = os.path.join(os.getenv('PWD'), "..") if os.getenv('PWD') else "../"
    #DATA_DIR = os.path.join(BASE_DIR, "/data")
    settings = settings

    # TODO: Remove all usage
    DATA_DIR = settings.DDD_DATADIR

    CAP_ROUND = 1
    CAP_FLAT = 2
    CAP_SQUARE = 3

    JOIN_ROUND = 1
    JOIN_MITRE = 2
    JOIN_BEVEL = 3

    ROT_FLOOR_TO_FRONT = (math.pi / 2.0, 0, 0)
    ROT_TOP_CW = (0, 0, -math.pi / 2.0)
    ROT_TOP_CCW = (0, 0, math.pi / 2.0)
    ROT_TOP_HALFTURN = (0, 0, math.pi)

    DEG_TO_RAD = (math.pi / 180.0)
    RAD_TO_DEG = (180.0 / math.pi)

    EXTRUSION_METHOD_WRAP = extrusion.EXTRUSION_METHOD_WRAP
    EXTRUSION_METHOD_SUBTRACT = extrusion.EXTRUSION_METHOD_SUBTRACT # For internal/external/vertical extrusions

    _uid_last = 0

    data = {}

    @staticmethod
    def initialize_logging(debug=True):
        """
        Convenience method for users.
        """
        D1D2D3Bootstrap.initialize_logging(debug)

    @staticmethod
    def trace(local=None):
        """
        Start an interactive session.
        Normally, users will use: "ddd.trace(locals())"
        """
        #import pdb; pdb.set_trace()
        import code
        if local is None: local = {}
        local = dict(globals(), **local)
        logger.info("Debugging console: %s", local)
        code.interact(local=local)

    @staticmethod
    def material(name=None, color=None, extra=None, **kwargs):
        #material = SimpleMaterial(diffuse=color, )
        #return (0.3, 0.9, 0.3)
        material = DDDMaterial(name=name, color=color, extra=extra, **kwargs)
        return material

    @staticmethod
    def point(coords=None, name=None, extra=None):
        if coords is None:
            coords = [0, 0, 0]
        elif len(coords) == 2:
            coords = [coords[0], coords[1], 0.0]
        geom = geometry.Point(coords)
        return DDDObject2(geom=geom, name=name, extra=extra)

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
        coords = [[math.cos(-i * math.pi * 2 / sides) * r, math.sin(-i * math.pi * 2 / sides) * r] for i in range(sides)]
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
    def rect(bounds=None, name=None):
        """
        Returns a 2D rectangular polygon for the given bounds [xmin, ymin, xmax, ymax].

        If no bounds are provided, returns a unitary square with corner at 0, 0 along the positive axis.
        """

        if bounds is None: bounds = [0, 0, 1, 1]
        if len(bounds) == 2: bounds = [0, 0, bounds[0], bounds[1]]
        cmin, cmax = ((bounds[0], bounds[1]), (bounds[2], bounds[3]))
        geom = geometry.Polygon([(cmin[0], cmin[1], 0.0), (cmax[0], cmin[1], 0.0),
                                 (cmax[0], cmax[1], 0.0), (cmin[0], cmax[1], 0.0)])
        geom = polygon.orient(geom, -1)
        return DDDObject2(geom=geom, name=name)

    @staticmethod
    def disc(center=None, r=None, resolution=4, name=None):
        if isinstance(center, Iterable): center = ddd.point(center, name=name)
        if center is None: center = ddd.point([0, 0, 0], name=name)
        if r is None: r = 1.0
        geom = center.geom.buffer(r, resolution=resolution)
        return DDDObject2(geom=geom, name=name)

    @staticmethod
    def sphere(center=None, r=None, subdivisions=2, name=None):
        if center is None: center = ddd.point([0, 0, 0])
        if r is None: r = 1.0
        mesh = primitives.Sphere(center=center.geom.coords[0], radius=r, subdivisions=subdivisions)
        mesh = Trimesh([[v[0], v[1], v[2]] for v in mesh.vertices], list(mesh.faces))
        return DDDObject3(mesh=mesh, name=name)

    @staticmethod
    def cube(center=None, d=None, name=None):
        """
        Cube is sitting on the Z plane defined by the center position.
        `d` is the distance to the side, so cube side length will be twice that value.

        @see :func:`box`
        """
        #if center is not None: raise NotImplementedError()  #
        if center is None: center = [0, 0, 0]
        if d is None: d = 1.0
        cube = D1D2D3.rect([-d, -d, d, d], name=name).extrude(d * 2).translate(center)
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
    def cylinder(height, r, center=True, resolution=4, name=None):
        obj = ddd.disc(r=r, resolution=resolution, name=name)
        obj = obj.extrude(height, center=center)
        return obj

    @staticmethod
    def trimesh(mesh=None, name=None):
        """
        """
        result = DDDObject3(name=name, mesh=mesh)
        return result

    @staticmethod
    def mesh(mesh=None, name=None):
        """
        """
        return D1D2D3.trimesh(mesh=mesh, name=name)

    @staticmethod
    def marker(pos=None, name=None, extra=None):
        marker = D1D2D3.box(name=name)
        if pos: marker = marker.translate(pos)
        if extra:
            marker.extra = extra
        marker.extra['ddd:marker'] = True
        return marker

    @staticmethod
    def ddd2(*args, **kwargs):
        return DDDObject2(*args, **kwargs)

    @staticmethod
    def ddd3(*args, **kwargs):
        return DDDObject3(*args, **kwargs)

    @staticmethod
    def grid2(bounds, detail=1.0, name=None):
        rects = []
        cmin, cmax = bounds[:2], bounds[2:]
        if isinstance(detail, int): detail= float(detail)
        if isinstance(detail, float): detail = [detail, detail]
        pointsx = list(np.linspace(cmin[0], cmax[0], 1 + int((cmax[0] - cmin[0]) / detail[0])))
        pointsy = list(np.linspace(cmin[1], cmax[1], 1 + int((cmax[1] - cmin[1]) / detail[1])))

        for (idi, (i, ni)) in enumerate(zip(pointsx[:-1], pointsx[1:])):
            for (idj, (j, nj)) in enumerate(zip(pointsy[:-1], pointsy[1:])):
                rect = ddd.rect([i, j, ni, nj])
                rect.geom = orient(rect.geom, 1)
                rects.append(rect.geom)
        geom = geometry.MultiPolygon(rects)
        #DDDObject2(geom=geom).show()
        #geom = geom.buffer(0.0)  # Sanitize, but this destroys the grid
        #DDDObject2(geom=geom).show()
        return DDDObject2(name=name, geom=geom)

    @staticmethod
    def grid3(bounds2, detail=1.0, name=None):
        grid2 = D1D2D3.grid2(bounds2, detail, name=name)
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
        return DDDObject3(name=name, mesh=mesh)

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

        if not isinstance(children, list):
            raise ValueError("Tried to add a non-list as children of a group.")

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

    @staticmethod
    def json_serialize(obj):
        if hasattr(obj, 'export'):
            data = obj.export()
        else:
            data = repr(obj)
            #data = None
        #if data: print(data)
        return data

    @staticmethod
    def load(name):

        def load_glb():
            scene = trimesh.load("some_file.glb")
            #mesh = trimesh.load_mesh('./test.stl',process=False) mesh.is_watertight
            geometries = list(scene.geometry.values())
            geometry = geometries[0]
            return D1D2D3.mesh(geometry, geometry.name)
            #adjacency_matrix = geometry.edges_sparse

        if (name.endswith(".glb")):
            return load_glb(name)
        else:
            raise DDDException("Cannot load file (unknown extension): %s" % (name))


class DDDMaterial():

    def __init__(self, name=None, color=None, extra=None, texture_path=None, atlas_path=None, alpha_cutoff=None, alpha_mode=None, texture_normal_path=None):
        """
        Color is hex color.
        """
        self.name = name
        self.extra = extra if extra else {}

        self.color = color
        self.color_rgba = None
        if self.color:
            self.color_rgba = trimesh.visual.color.hex_to_rgba(self.color)

        self.alpha_cutoff = alpha_cutoff
        self.alpha_mode = alpha_mode

        self.texture = texture_path
        self._texture_cached = None  # currently a PIL image, shall be a DDDTexture
        self.texture_normal = texture_normal_path

        self.atlas = None
        if atlas_path:
            self.load_atlas(atlas_path)

        self._trimesh_material_cached = None

    def __repr__(self):
        return "DDDMaterial(name=%r, color=%r)" % (self.name, self.color)

    def __hash__(self):
        return abs(hash((self.name, self.color)))  #, self.extra)))

    def _trimesh_material(self):
        """
        Returns a Trimesh material for this DDDMaterial.
        Materials are cached to avoid repeated materials and image loading (which may crash the app).
        """
        if self._trimesh_material_cached is None:
            if self.texture and D1D2D3Bootstrap.export_textures:
                im = PIL.Image.open(self.texture)  #.convert("RGBA")
                if self.texture and (self.alpha_cutoff or self.texture_normal):
                    alpha_mode = self.alpha_mode if self.alpha_mode else ('MASK' if self.alpha_cutoff else 'OPAQUE')
                    im_normal = PIL.Image.open(self.texture_normal) if self.texture_normal else None
                    mat = PBRMaterial(baseColorTexture=im, baseColorFactor=self.color_rgba,
                                      normalTexture=im_normal,
                                      alphaMode=alpha_mode, alphaCutoff=self.alpha_cutoff)  # , ambient, specular, glossiness)
                else:
                    mat = SimpleMaterial(image=im, diffuse=self.color_rgba)  # , ambient, specular, glossiness)
            else:
                mat = SimpleMaterial(diffuse=self.color_rgba)
            #mat = PBRMaterial(doubleSided=True)  # , emissiveFactor= [0.5 for v in self.mesh.vertices])
            self._trimesh_material_cached = mat
        return self._trimesh_material_cached

    def load_atlas(self, filepath):
        self.atlas = TextureAtlas.load_atlas(filepath)

    def get_texture(self):
        """
        Returns the texture (currently a PIL image)
        """
        if not self._texture_cached:
            self._texture_cached = PIL.Image.open(self.texture)
        return self._texture_cached


class DDDObject():

    def __init__(self, name=None, children=None, extra=None, material=None):
        self.name = name
        self.children = children if children is not None else []
        self.extra = extra if extra is not None else {}
        self.mat = material

        self._uid = None

        #self.geom = None
        #self.mesh = None

        for c in self.children:
            if not isinstance(c, self.__class__) and not (isinstance(c, DDDInstance) and isinstance(self, DDDObject3)):
                raise DDDException("Invalid children type on %s (not %s): %s" % (self, self.__class__, c), ddd_obj=self)

    def __repr__(self):
        return "DDDObject(name=%r, children=%d)" % (self.name, len(self.children) if self.children else 0)

    def hash(self):
        h = hashlib.new('sha256')
        h.update(self.__class__.__name__.encode("utf8"))
        if self.name:
            h.update(self.name.encode("utf8"))
        for k, v in self.extra.items():
            h.update(k.encode("utf8"))
            if not v or isinstance(v, (str, int, float)):
                h.update(str(v).encode("utf8"))
        #h.update(str(hash(frozenset(self.extra.items()))).encode("utf8"))
        for c in self.children:
            h.update(c.hash().digest())
        return h
        #print(self.__class__.__name__, self.name, hash((self.__class__.__name__, self.name)))
        #return abs(hash((self.__class__.__name__, self.name)))  #, ((k, self.extra[k]) for k in sorted(self.extra.keys())))))

    def copy_from(self, obj):
        """
        Copies metadata and children from another. Returns self.
        """
        if obj.name:
            self.name = obj.name

        self.children = list(obj.children)
        self.extra.update(obj.extra)
        self.material = obj.material

        return self

    def uniquename(self):
        # Hashing
        #node_name = "%s_%s" % (self.name if self.name else 'Node', self.hash().hexdigest()[:8])

        # Random number
        if self._uid is None:
            D1D2D3._uid_last += 1
            self._uid = D1D2D3._uid_last  # random.randint(0, 2 ** 32)

        node_name = "%s_%s" % (self.name if self.name else 'Node', self._uid)

        return node_name

    def replace(self, obj):
        """
        Replaces self data with data from other object. Serves to "replace"
        instances in lists.
        """
        # TODO: Study if the system shall modify instances and let user handle cloning, this method would be unnecessary
        self.name = obj.name
        self.extra = obj.extra
        self.mat = obj.mat
        self.children = obj.children
        return self

    def metadata(self, path_prefix, name_suffix):

        node_name = self.uniquename() + name_suffix

        ignore_keys = ('uv', 'osm:feature', 'ddd:connections')
        metadata = dict(self.extra)
        metadata['ddd:path'] = path_prefix + node_name
        if hasattr(self, "geom"):
            metadata['geom:type'] = self.geom.type if self.geom else None
        if self.mat and self.mat.name:
            metadata['ddd:material'] = self.mat.name
        if self.mat and self.mat.color:
            metadata['ddd:material:color'] = self.mat.color  # hex
        if self.mat and self.mat.extra:
            # TODO: Resolve material and extra properties earlier, as this is copied in every place it's used.
            # If material has extra metadata, add it but do not replace (it's restored later)
            metadata.update({k:v for k, v in self.mat.extra.items()})  # if k not in metadata or metadata[k] is None})

        metadata['ddd:object'] = self

        # FIXME: This is suboptimal
        metadata = {k: v for k, v in metadata.items() if k not in ignore_keys}  # and v is not None
        #metadata = json.loads(json.dumps(metadata, default=D1D2D3.json_serialize))

        return metadata

    def dump(self, indent_level=0, data=False):
        strdata = ""
        if data:
            strdata = strdata + " " + str(self.extra)
        print("  " * indent_level + str(self) + strdata)
        for c in self.children:
            c.dump(indent_level=indent_level + 1, data=data)

    def count(self):
        # TODO: Is this semantically correct? what about hte root node and children?
        # This is used for select() set results, so maybe that should be a separate type
        return len(self.children)

    def one(self):
        if len(self.children) != 1:
            raise DDDException("Expected 1 object but found %s." % len(self.children))
        return self.children[0]

    def find(self, path=None):

        # Shortcuts for performance
        # TODO: Path filtering shall be improved in select() method
        if path.startswith("/") and '*' not in path and (path.count('/') == 1 or (path.count('/') == 2 and path.endswith("/"))):
            parts = path[1:].split("/")
            result = [o for o in self.children if o.name == parts[0]]
            result = self.grouptyped(result)
        else:
            result = self.select(path=path, recurse=False)

        if len(result.children) != 1:
            raise DDDException("Find '%s' expected 1 object but found %s." % (path, len(result.children)), ddd_obj=self)
        return result.one()

    def select(self, selector=None, path=None, func=None, recurse=True, apply_func=None, _rec_path=None):
        """
        """
        if selector and not isinstance(selector, DDDSelector):
            selector = DDDSelector(selector)

        #if _rec_path is None:
        #    logger.debug("Select: func=%s selector=%s path=%s recurse=%s _rec_path=%s", func, selector, path, recurse, _rec_path)

        # TODO: Recurse should be false by default

        result = []

        if _rec_path is None:
            _rec_path = "/"
        elif _rec_path == "/":
            _rec_path = _rec_path + str(self.name)
        else:
            _rec_path = _rec_path + "/" + str(self.name)

        selected = True

        if path:
            # TODO: Implement path pattern matching (hint: gitpattern lib)
            path = path.replace("*", "")  # Temporary hack to allow *
            pathmatches = _rec_path.startswith(path)
            selected = selected and pathmatches

        if func:
            selected = selected and func(self)
        if selector:
            selected = selected and selector.evaluate(self)

        remove_object = False
        add_object = False

        o = self
        if selected:
            result.append(self)
            if apply_func:
                o = apply_func(self)
                if o is False or (o and o is not self):  # new object or delete
                    add_object = o
                    remove_object = True
            if o is None:
                o = self

        # If a list was returned, children are not evaluated
        if o and (not isinstance(o, list)) and (not selected or recurse):
            to_remove = []
            to_add = []
            for c in list(o.children):
                cr = c.select(func=func, selector=selector, path=path, recurse=recurse, apply_func=apply_func, _rec_path=_rec_path)
                if cr.extra['_remove_object']:
                    to_remove.append(c)
                if cr.extra['_add_object']:
                    if isinstance(cr.extra['_add_object'], list):
                        to_add.extend(cr.extra['_add_object'])
                    else:
                        to_add.append(cr.extra['_add_object'])
                        #to_add.extend(cr.children)
                del(cr.extra['_remove_object'])
                del(cr.extra['_add_object'])
                result.extend(cr.children)
            o.children = [coc for coc in o.children if coc not in to_remove]
            o.children.extend(to_add)

        #if (isinstance(o, list)):
        #    o.children.extend()

        #self.children = [c for c in self.children if c not in result]

        res = self.grouptyped(result)
        res.extra['_remove_object'] = remove_object
        res.extra['_add_object'] = add_object
        return res

    def filter(self, func):
        return self.select(func=func)

    '''
    def apply(self, func):
        for obj in self.select().children:
            func(obj)
    '''

    def apply_components(self, methodname, *args, **kwargs):
        """
        Applies a method with arguments to all applicable components in this object
        (eg. apply transformation to colliders).

        Does not act on children.
        """

        for k in ('ddd:collider:primitive',):
            if k in self.extra:
                comp = self.extra[k]
                if isinstance(comp, DDDObject):
                    method_to_call = getattr(comp, methodname)
                    self.extra[k] = method_to_call(*args, **kwargs)

    def get(self, keys, default=(None, ), extra=None):
        """
        Returns a property from dictionary and settings.

        Keys can be a string or an array of strings which will be tried in order.
        """
        if isinstance(keys, str):
            keys = [keys]

        dicts = [self.extra]
        if extra is not None:
            if not isinstance(extra, (list, set, tuple)): extra = [extra]
            dicts.extend(extra)
        if D1D2D3.data is not None: dicts.append(D1D2D3.data)

        #logger.debug("Resolving %s in %s (def=%s)", keys, dicts, default)

        result = None
        key = None
        for k in keys:
            if key: break
            for d in dicts:
                if k in d:
                    key = k
                    result = d[k]
                    # logger.info("Found key in dictionary: %s", result)
                    break

        if key is None:
            if default is not self.get.__defaults__[0]:
                result = default
            else:
                raise DDDException("Cannot resolve property %r in object '%s'." % (keys, self))

        # Resolve lambda
        if callable(result):
            result = result()
            self.extra[key] = result

        return result

    def set(self, key, value=None, children=False, default=(None, )):
        """
        """
        if children:
            # Apply to select_all
            for o in self.select().children:
                o.prop_set(key, value, False, default)
        else:
            if default is self.set.__defaults__[2]:
                self.extra[key] = value
            else:
                if key not in self.extra or self.extra[key] is None:
                    self.extra[key] = default
        return self

    def prop_set(self, key, *args, **kwargs):
        return self.set(key, *args, **kwargs)

    def grouptyped(self, children=None):
        if isinstance(self, DDDObject2):
            return ddd.group(children, empty=2)
        elif isinstance(self, DDDObject3) or isinstance(self, DDDInstance):
            return ddd.group(children, empty=3)
        else:
            return ddd.group(children)

    def flatten(self):

        result = self.copy()
        result.children = []
        result.geom = None

        res = self.copy()
        children = res.children
        res.children = []

        result.append(res)
        for c in children:
            result.children.extend(c.flatten().children)

        return result

    def append(self, obj):
        """
        Adds an object as a children to this node.
        If a list is passed, each element is added.
        """
        if isinstance(obj, Iterable):
            for i in obj:
                self.children.append(i)
        elif isinstance(obj, DDDObject):
            self.children.append(obj)
        else:
            raise ValueError("Cannot append object of this type to DDDObject children: %s", obj)
        return self

    def remove(self, obj):
        """
        Removes an object from this node children recursively. Modifies objects in-place.
        """
        self.children = [c.remove(obj) for c in self.children if c and c != obj]
        return self


class DDDObject2(DDDObject):

    def __init__(self, name=None, children=None, geom=None, extra=None, material=None):
        super().__init__(name, children, extra, material)
        self.geom = geom

    def __repr__(self):
        return "%s(%s, name=%s, geom=%s (%s verts), children=%d)" % (self.__class__.__name__, id(self), self.name, self.geom.type if hasattr(self, 'geom') and self.geom else None, self.vertex_count() if hasattr(self, 'geom') else None, len(self.children) if self.children else 0)

    def copy(self, name=None):
        obj = DDDObject2(name=name if name else self.name, children=[c.copy() for c in self.children], geom=copy.deepcopy(self.geom) if self.geom else None, extra=dict(self.extra), material=self.mat)
        return obj

    def copy3(self, name=None):
        obj = DDDObject3(name=name if name else self.name, children=[], mesh=None, extra=dict(self.extra), material=self.mat)
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
        angle_diff = angle_end - angle_start
        radius_vec = (coords[0] - center[0], coords[1] - center[1])
        radius_l = math.sqrt(radius_vec[0] * radius_vec[0] + radius_vec[1] * radius_vec[1])
        if ccw: angle_diff = (math.pi * 2) - angle_diff

        numpoints = math.ceil(abs(angle_diff) * (resolution / (math.pi / 2)))
        angles = np.linspace(angle_start, angle_end, numpoints)
        for a in angles:
            linecoords.append([center[0] + math.cos(a) * radius_l, center[1] + math.sin(a) * radius_l, coords[2]])

        result = self.copy()
        result.geom = geometry.LineString(linecoords)
        return result

    def centroid(self):
        result = self.copy()
        geom = self.union().geom
        if geom is None:
            raise DDDException("Cannot find centroid (no geometry) for object: %s" % self)
        result.geom = geom.centroid
        return result

    def translate(self, coords):

        if hasattr(coords, 'geom'):
            coords = coords.geom.coords[0]

        if len(coords) == 2: coords = [coords[0], coords[1], 0.0]
        result = self.copy()
        if self.geom:
            trans_func = lambda x, y, z=0.0: (x + coords[0], y + coords[1], z + coords[2])
            result.geom = ops.transform(trans_func, self.geom)
        result.children = [c.translate(coords) for c in self.children]
        return result

    def rotate(self, angle, origin=None):  # center (bb center), centroid, point
        """
        Angle is in radians.
        """
        if origin is None: origin = (0, 0)
        result = self.copy()
        if self.geom:
            result.geom = affinity.rotate(self.geom, angle, origin=origin, use_radians=True)
        result.children = [c.rotate(angle, origin) for c in self.children]
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
        xmin, ymin, xmax, ymax = (float("-inf"), float("-inf"), float("inf"), float("inf"))
        if self.geom:
            xmin, ymin, xmax, ymax = self.geom.bounds
        for c in self.children:
            cxmin, cymin, cxmax, cymax = c.bounds()
            xmin = min(xmin, cxmin)
            ymin = min(ymin, cymin)
            xmax = max(xmax, cxmax)
            ymax = max(ymax, cymax)

        return (xmin, ymin, xmax, ymax)

    def recenter(self):
        xmin, ymin, xmax, ymax = self.bounds()
        center = ((xmin + xmax) / 2, (ymin + ymax) / 2)
        result = self.translate([-center[0], -center[1], 0])
        return result

    def clean(self, eps=None, remove_empty=True, validate=True):
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
            logger.warn("Removed invalid geometry: %s", result)
            result.geom = None
        if result.geom and (result.geom.type != 'GeometryCollection' and not result.geom.is_simple):
            logger.warn("Removed geometry that crosses itself: %s", result)
            result.geom = None

        result.children = [c.clean(eps=eps, remove_empty=remove_empty, validate=validate) for c in self.children]

        if remove_empty:
            result.children = [c for c in result.children if (c.children or c.geom)]

        if validate:
            try:
                result.validate()
            except DDDException as e:
                logger.warn("Removed geom that didn't pass validation check (%s): %s", result, e)
                result.geom = None

        return result

    def clean_replace(self, eps=None, remove_empty=True, validate=True):
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

        # Attempt to optimize (test)
        #if not result.intersects(other):
        #    return result

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

        #for c in other.children:
        #    result = result.subtract(c)
        if self.geom:
            union = other.union()
            if union.geom and not union.geom.is_empty:
                result.geom = result.geom.difference(union.geom)

        result.children = [c.subtract(other) for c in result.children]

        return result

    def recurse_geom(self):

        geoms = []
        if self.geom:
            geoms.append(self.geom)

        for c in self.children:
            geoms.extend(c.recurse_geom())

        return geoms

    def coords_iterator(self):
        if self.geom.type == 'MultiPolygon':
            for g in self.geom.geoms:
                for coord in g.exterior.coords:
                    yield coord
        elif self.geom.type == 'Polygon':
            for coord in self.geom.exterior.coords:
                yield coord
        elif self.geom.type == 'GeometryCollection':
            for g in self.geom.geoms:
                for coord in D1D2D3.shape(g).coords_iterator():
                    yield coord
        elif self.geom.type == 'LineString':
            for coord in self.geom.coords:
                yield coord
        else:
            raise NotImplementedError("Not implemented coords_iterator for geom: %s" % self.geom.type)

        for c in self.children:
            for coord in c.coords_iterator():
                yield coord


    def _vertex_func_coords(self, func, coords):
        ncoords = []
        for iv, v in enumerate(coords):
            res = func(v[0], v[1], v[2] if len(v) > 2 else 0.0, iv)
            ncoords.append(res[:len(v)])
            #print("%s > %s" % (v, res))
        return ncoords

    def vertex_func(self, func):
        obj = self.copy()
        if obj.geom:
            if obj.geom.type == 'MultiPolygon':
                logger.warn("Unknown geometry for 2D vertex func")
                for g in obj.geom.geoms:
                    g.exterior.coords = self._vertex_func_coords(func, g.exterior.coords)
            elif obj.geom.type == 'Polygon':
                obj.geom = ddd.polygon(self._vertex_func_coords(func, obj.geom.exterior.coords)).geom
            elif obj.geom.type == 'LineString':
                obj.geom = ddd.line(self._vertex_func_coords(func, obj.geom.coords)).geom
            else:
                #logger.warn("Unknown geometry for 2D vertex func")
                raise DDDException("Unknown geometry for 2D vertex func: %s" % self)

        obj.children = [c.vertex_func(func) for c in self.children]
        return obj

    def vertex_list(self, ):
        return list(self.coords_iterator())

    def vertex_count(self):
        if not self.geom:
            return 0
        if self.geom.type == 'MultiPolygon':
            return sum([len(p.exterior.coords) for p in self.geom.geoms])
        if self.geom.type == 'Polygon':
            if self.geom.is_empty: return 0
            return len(self.geom.exterior.coords) + sum([len(i.coords) for i in self.geom.interiors])
        else:
            try:
                return len(self.geom.coords)
            except Exception as e:
                #logger.debug("Invalid vertex count (multi-part geometry involved): %s", self)
                pass
        return None

    def remove_z(self):
        result = self.copy()
        if self.geom:
            if result.geom.type == "MultiPolygon":
                for g in result.geom.geoms:
                    g.coords = [(x, y) for (x, y, _) in g.coords]
            elif result.geom.type == "MultiLineString":
                for g in result.geom.geoms:
                    g.coords = [(x, y) for (x, y, _) in g.coords]
            elif result.geom.type == "Polygon":
                result.geom.exterior.coords = [(x, y) for (x, y, _) in result.geom.exterior.coords]
                for g in result.geom.interior:
                    g.coords = [(x, y) for (x, y, _) in g.coords]

            else:
                result.geom.coords = [(x, y) for (x, y, _) in result.geom.coords]
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

        objs = result.children
        result.children = []
        while len(objs) > 1:
            newo = objs[0].union_replace().union_replace(objs[1].union_replace())
            objs = objs[2:] + [newo]
        if objs:
            if result.geom:
                result.geom = result.geom.union(objs[0].geom)
            else:
                result.geom = objs[0].geom

        if other:
            union = other.union().clean(eps=0)
            if result.geom and union.geom:
                try:
                    result.geom = result.geom.union(union.geom)
                except Exception as e:
                    logger.error("Cannot perform union (1st try) between %s and %s: %s", result, other, e)
                    try:
                        result.geom = ops.unary_union([result.geom, union.geom])
                        #result = result.clean(eps=0.001).simplify(0.001)
                        #other = other.clean(eps=0.001).simplify(0.001)
                        #result.geom = result.geom.union(union.geom)
                        result = result.clean(eps=0)
                    except Exception as e:
                        logger.error("Cannot perform union (2nd try) between %s and %s: %s", result, other, e)
                        result = result.clean(eps=0.001) #.simplify(0.001)
                        other = other.clean(eps=0.001) #.simplify(0.001)
                        result.geom = result.geom.union(union.geom)

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
        result.children = [c for c in result.children if c.children or (c.geom and not c.geom.is_empty)]

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
        if self.geom:
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
        Note: distinctio between union self or each of the children (currently, each children in self vs other union)
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

        for c in self.children:
            c.validate()

    def individualize(self, remove_interiors=False, always=False):
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

        elif always:
            # Move as a children for consistency
            result.geom = None
            newobj = self.copy()
            newobj.geom = self.geom
            newchildren.append(newobj)

        result.children = [c.individualize() for c in (self.children + newchildren)]

        return result

    def triangulate(self, twosided=False):
        """
        Returns a triangulated mesh (3D) from this 2D shape.
        """
        if self.geom:
            if self.geom.type == 'MultiPolygon' or self.geom.type == 'MultiLineString' or self.geom.type == 'GeometryCollection':
                meshes = []
                for geom in self.geom.geoms:
                    pol = DDDObject2(geom=geom, extra=dict(self.extra), name="Triangulated Multi: %s" % self.name)
                    mesh = pol.triangulate(twosided)
                    meshes.append(mesh)
                result = ddd.group(children=meshes, name=self.name)
            elif not self.geom.is_empty and not self.geom.type == 'LineString' and not self.geom.type == 'Point':
                # Triangulation mode is critical for the resulting quality and triangle count.
                #mesh = creation.extrude_polygon(self.geom, height)
                #vertices, faces = creation.triangulate_polygon(self.geom)  # , min_angle=math.pi / 180.0)
                try:
                    vertices, faces = creation.triangulate_polygon(self.geom, triangle_args="p", engine='triangle')  # Flat, minimal, non corner-detailing ('pq30' produces more detailed triangulations)
                except Exception as e:
                    logger.info("Could not triangulate geometry %s: %s", self.geom, e)
                    raise
                    try:
                        self.geom = self.clean(eps=0.01).geom
                        vertices, faces = creation.triangulate_polygon(self.geom, triangle_args="p", engine='triangle')  # Flat, minimal, non corner-detailing ('pq30' produces more detailed triangulations)
                    except Exception as e:
                        logger.error("Could not triangulate geometry (after clean) %s: %s", self.geom, e)
                        #raise DDDException("Could triangulate geometry (after convex hull) %s: %s" % (self.geom, e), ddd_obj=self)
                        vertices, faces = None, None
                        raise

                if vertices is not None:
                    if twosided:
                        faces2 = np.fliplr(faces)
                        faces = np.concatenate((faces, faces2))

                    mesh = Trimesh([(v[0], v[1], 0.0) for v in vertices], faces)
                    #mesh = creation.extrude_triangulation(vertices=vertices, faces=faces, height=0.2)
                    mesh.merge_vertices()
                    result = DDDObject3(mesh=mesh, name=self.name)
                else:
                    result = DDDObject3(name="Could not triangulate (error during triangulation)")
            else:
                result = DDDObject3("Cannot triangulate: unknown geometry type")
        else:
            result = DDDObject3()

        result.children.extend([c.triangulate(twosided) for c in self.children])

        # Copy extra information from original object
        result.name = self.name if result.name is None else result.name
        result.extra = dict(self.extra)
        result.extra['extruded_shape'] = self

        if self.mat is not None:
            result = result.material(self.mat)

        return result

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
                    mesh = extrusion.extrude_triangulation(vertices=vertices,
                                                           faces=faces,
                                                           height=abs(height),
                                                           cap=cap, base=base)
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
                if center:
                    result = result.translate([0, 0, -height / 2])
                elif height < 0:
                    result = result.translate([0, 0, height])

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

    def extrude_along(self, path):
        trimesh_path = path.geom.coords
        mesh = creation.sweep_polygon(self.geom, trimesh_path, triangle_args="p", engine='triangle')
        mesh.fix_normals()
        result = self.copy3()
        result.mesh = mesh
        return result

    def extrude_step(self, obj_2d, offset, cap=True, base=True, method=D1D2D3.EXTRUSION_METHOD_WRAP):
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
            result.append(ddd.shape(splits[0]))
            #result.append(ddd.shape(splits[1]))

        return result

    def orient_from(self, other):
        """
        Orients a line so it starts from the closest point to other
        """
        result = self.copy()
        dist_0 = other.distance(ddd.point(self.geom.coords[0]))
        dist_1 = other.distance(ddd.point(self.geom.coords[-1]))
        if dist_1 < dist_0:
            result.geom.coords = reversed(list(result.geom.coords))
        return result

    def simplify(self, distance):
        result = self.copy()
        if self.geom:
            result.geom = result.geom.simplify(distance, preserve_topology=True)
        result.children = [c.simplify(distance) for c in self.children]
        return result

    def random_points(self, num_points=1, density=None):
        # TODO: use density or count, accoridng to polygon area :?
        # TODO: support line geometries
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

    def outline(self):
        result = self.copy().individualize().clean()
        if result.geom and result.geom.type == "Polygon":
            result.geom = LineString(list(result.geom.exterior.coords))
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
        Interpolates a distance along a LineString, returning:
            coords_p, segment_idx, segment_coords_a, segment_coords_b

        Note that returns coordinates, not DDD objects.
        """
        # Walk segment
        l = 0.0
        coords = None
        try:
            coords = self.geom.coords
        except Exception as e:
            raise DDDException("Could not interpolate distance on segment %s: %s" % (self, e))

        #length = self.geom.length
        for idx in range(len(coords) - 1):
            p, pn = coords[idx:idx+2]
            pl = math.sqrt((pn[0] - p[0]) ** 2 + (pn[1] - p[1]) ** 2)
            l += pl
            if l >= d:
                return (self.geom.interpolate(d).coords[0], idx, p, pn)
        return (self.geom.interpolate(d).coords[0], idx, p, pn)
        return None

    def closest_segment(self, other):
        """
        Closest segment in a LineString to other geometry.
        Does not support children in "other" geometry.

        Returns: coords_p, segment_idx, segment_coords_a, segment_coords_b, closest_object, closest_object_d
        """
        closest_self, closest_d = self.closest(other)
        #logger.debug("Closest: %s  %s > %s", closest_d, closest_self, other)

        d = closest_self.geom.project(other.geom)

        result = (*closest_self.interpolate_segment(d), closest_self, d)
        #ddd.group([other.buffer(5.0),  ddd.point(result[2]).buffer(5.0).material(ddd.mat_highlight), ddd.line([result[2], result[3]]).buffer(2.0), ddd.point(result[0]).buffer(5.0), closest_self.buffer(0.2)]).show()
        return result

    def perpendicular(self, distance=0.0, length=1.0, double=False):

        (coords_p, segment_idx, segment_coords_a, segment_coords_b) = self.interpolate_segment(distance)

        dir_vec = (segment_coords_b[0] - segment_coords_a[0], segment_coords_b[1] - segment_coords_a[1])
        dir_vec_length = math.sqrt(dir_vec[0] ** 2 + dir_vec[1] ** 2)
        dir_vec = (dir_vec[0] / dir_vec_length, dir_vec[1] / dir_vec_length)
        perpendicular_vec = (-dir_vec[1], dir_vec[0])

        left = (coords_p[0] + perpendicular_vec[0] * length, coords_p[1] + perpendicular_vec[1] * length)
        right = (coords_p[0] - perpendicular_vec[0] * length, coords_p[1] - perpendicular_vec[1] * length)

        #self.copy(children=None)
        if not double:
            result = ddd.line([coords_p, left])
        else:
            result = ddd.line([right, left])

        #ddd.group2([self.buffer(0.1), result.buffer(0.1).material(ddd.mats.highlight)]).show()

        return result

    def geom_recursive(self):
        geoms = []
        if self.geom: geoms = [self.geom]
        if self.children:
            for c in self.children:
                cgems = c.geom_recursive()
                geoms.extend(cgems)
        return geoms

    def save(self, path, instance_marker=None, instance_mesh=None, scale=1.0):

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
        else:
            raise DDDException("Invalid 2D save format (filename=%s)" % path)

        with open(path, 'wb') as f:
            f.write(data)

    def show(self):

        # Show in 3D view
        #self.extrude(0.2).show()
        try:
            self.triangulate().show()
        except Exception as e:
            logger.error("Could not show object %s: %s", self, e)

        # Show in browser
        #logger.info("Showing 2D image via shell.")
        #FIXME: save to a temporary/uniquefilename
        #self.save("/tmp/tmp-MAKEUNIQUE.svg")
        #webbrowser.open('file:///tmp/tmp-MAKEUNIQUE.svg', new=2)


class DDDInstance(DDDObject):

    def __init__(self, ref, name=None, extra=None):
        super().__init__(name, None, extra)
        self.ref = ref
        self.transform = DDDTransform()

    def __repr__(self):
        return "%s(%s, ref=%s)" % (self.__class__.__name__, self.uniquename(), self.ref)

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

    def scale(self, v):
        obj = self.copy()
        obj.transform.position = np.array(v) * obj.transform.position
        return obj

    def bounds(self):
        if self.ref:
            return self.ref.bounds()
        return None

    def marker(self):
        ref = D1D2D3.marker(name=self.name, extra=dict(self.extra))
        ref = ref.scale(self.transform.scale)
        ref = ref.rotate(transformations.euler_from_quaternion(self.transform.rotation, axes='sxyz'))
        ref = ref.translate(self.transform.position)
        if self.ref:
            ref.extra.update(self.ref.extra)
        ref.extra.update(self.extra)
        return ref


    def _recurse_scene_tree(self, path_prefix, name_suffix, instance_mesh, instance_marker, include_metadata, scene=None, scene_parent_node_name=None):

        #node_name = self.uniquename() + name_suffix
        node_name = self.uniquename()

        # Add metadata to name
        metadata = self.metadata(path_prefix, name_suffix)

        #if True:
        #    serialized_metadata = base64.b64encode(json.dumps(metadata, default=D1D2D3.json_serialize).encode("utf-8")).decode("ascii")
        #    encoded_node_name = node_name + "_" + str(serialized_metadata)

        metadata_serializable = None
        if include_metadata:
            metadata_serializable = json.loads(json.dumps(metadata, default=D1D2D3.json_serialize))

        #scene_node_name = node_name.replace(" ", "_")
        scene_node_name = metadata['ddd:path'].replace(" ", "_")  # TODO: Trimesh requires unique names, but using the full path makes them very long. Not using it causes instanced geeometry to fail.


        node_transform = transformations.concatenate_matrices(
            transformations.translation_matrix(self.transform.position),
            transformations.quaternion_matrix(self.transform.rotation)
            )

        if instance_mesh:
            if self.ref:

                if self.transform.scale != [1, 1, 1]:
                    raise DDDException("Invalid scale for an instance object (%s): %s", self.transform.scale, self)

                # TODO: Use a unique buffer! (same geom name for trimesh?)
                #ref = self.ref.copy()
                ref = self.ref.copy()  #.copy()

                ##ref = ref.scale(self.transform.scale)
                #ref = ref.rotate(transformations.euler_from_quaternion(self.transform.rotation, axes='sxyz'))
                #ref = ref.translate(self.transform.position)

                #refscene = ref._recurse_scene(path_prefix=path_prefix + node_name + "/", name_suffix="#ref", instance_mesh=instance_mesh, instance_marker=instance_marker)
                #scene = append_scenes([scene] + [refscene])

                # Empty node with transform
                #print("Instancing %s on %s" % (scene_node_name, scene_parent_node_name))
                #scene.add_geometry(geometry=D1D2D3.marker().mesh, node_name=scene_node_name, geom_name="Geom %s" % scene_node_name, parent_node_name=scene_parent_node_name, transform=node_transform)
                scene.graph.update(frame_to=scene_node_name, frame_from=scene_parent_node_name, matrix=node_transform, geometry_flags={'visible': True}, extras=metadata_serializable)

                # Child
                ref._recurse_scene_tree(path_prefix=path_prefix + node_name + "/", name_suffix="#ref",
                                        instance_mesh=instance_mesh, instance_marker=instance_marker, include_metadata=include_metadata,
                                        scene=scene, scene_parent_node_name=scene_node_name)

            else:
                if type(self) == type(DDDInstance):
                    raise DDDException("Instance should reference another object: %s" % (self, ))

        if instance_marker:
            # Marker
            ref = self.marker()
            scene.add_geometry(geometry=ref.mesh, node_name=scene_node_name + "_marker", geom_name="Marker %s" % scene_node_name,
                               parent_node_name=scene_parent_node_name, transform=node_transform, extras=metadata_serializable)

        return scene

    def _recurse_meshes(self, instance_mesh, instance_marker):

        cmeshes = []

        if instance_mesh:
            if self.ref:
                ref = self.ref.copy()
                ref = ref.scale(self.transform.scale)
                ref = ref.rotate(transformations.euler_from_quaternion(self.transform.rotation, axes='sxyz'))
                ref = ref.translate(self.transform.position)

                cmeshes.extend(ref._recurse_meshes(instance_mesh, instance_marker))

        if instance_marker:
            # Marker
            ref = self.marker()
            cmeshes.extend(ref._recurse_meshes(instance_mesh, instance_marker))

        '''
        if hasattr(ref, 'mesh'):
            if ref.mesh:
                mesh = ref._process_mesh()
                cmeshes = [mesh]
            if ref.children:
                for c in ref.children:
                    cmeshes.extend(c.recurse_meshes())
        '''
        return cmeshes


class DDDTransform():
    """
    Stores position, rotation and scale.

    These can be used to form an homogeneous transformation matrix.
    """

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

    def export(self):
        result = {'position': self.position,
                  'rotation': self.rotation,
                  'scale': self.scale}
        return result


class DDDObject3(DDDObject):

    def __init__(self, name=None, children=None, mesh=None, extra=None, material=None):
        self.mesh = mesh
        super().__init__(name, children, extra, material)

    def __repr__(self):
        return "%s(%s, faces=%d, children=%d)" % (self.__class__.__name__, self.uniquename(), len(self.mesh.faces) if self.mesh else 0, len(self.children) if self.children else 0)

    def copy(self, name=None):
        if name is None: name = self.name
        obj = DDDObject3(name=name, children=list(self.children), mesh=self.mesh.copy() if self.mesh else None, material=self.mat, extra=dict(self.extra))
        #obj = DDDObject3(name=name, children=[c.copy() for c in self.children], mesh=self.mesh.copy() if self.mesh else None, material=self.mat, extra=dict(self.extra))
        return obj

    def replace(self, obj):
        """
        Replaces self data with data from other object. Serves to "replace"
        instances in lists.
        """
        # TODO: Study if the system shall modify instances and let user handle cloning, this method would be unnecessary
        super(DDDObject3, self).replace(obj)
        self.mesh = obj.mesh
        return self

    def bounds(self):
        """
        Returns the axis aligned bounding box for this object's geometry.

        Ref: https://github.com/mikedh/trimesh/issues/57
        """

        corners = list()
        for c in self.children:
            cb = c.bounds()
            if cb is not None:
                corners.extend((*cb, ))

        if self.mesh:
            corners.extend((*list(self.mesh.bounds), ))

        if corners:
            corners = np.array(corners)
            bounds = np.array([corners.min(axis=0),
                               corners.max(axis=0)])
        else:
            bounds = None

        return bounds

    def recenter(self, onplane=False):
        ((xmin, ymin, zmin), (xmax, ymax, zmax)) = self.bounds()
        center = [(xmin + xmax) / 2, (ymin + ymax) / 2, (zmin + zmax) / 2]
        if onplane: center[2] = zmin
        result = self.translate([-center[0], -center[1], -center[2]])
        return result

    def translate(self, v):
        if len(v) == 2: v = (v[0], v[1], 0)
        obj = self.copy()
        if obj.mesh:
            obj.mesh.apply_translation(v)
        obj.apply_components("translate", v)
        obj.children = [c.translate(v) for c in self.children]
        return obj

    def rotate(self, v):
        obj = self.copy()
        if obj.mesh:
            rot = transformations.euler_matrix(v[0], v[1], v[2], 'sxyz')
            obj.mesh.vertices = trimesh.transform_points(obj.mesh.vertices, rot)
        obj.apply_components("rotate", v)
        obj.children = [c.rotate(v) for c in obj.children]
        return obj

    def rotate_quaternion(self, quaternion):
        obj = self.copy()
        if obj.mesh:
            rot = transformations.quaternion_matrix(quaternion)
            obj.mesh.vertices = trimesh.transform_points(obj.mesh.vertices, rot)
        obj.apply_components("rotate_quaternion", quaternion)
        obj.children = [c.rotate_quaternion(quaternion) for c in obj.children]
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

    def invert(self):
        """Inverts mesh triangles (which inverts triangle face normals)."""
        obj = self.copy()
        obj.mesh.invert()
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
        meshes = self._recurse_meshes(instance_mesh=False, instance_marker=False)
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

    def combine(self):
        """
        Combine geometry for this and all children meshes.
        """
        result = self.copy()
        for c in self.children:
            cc = c.combine()
            if result.mat is None and cc.mat is not None: result = result.material(cc.mat)
            result.mesh = result.mesh + cc.mesh if result.mesh else cc.mesh
            #result.extra.update(cc.extra)
            #vertices = list(result.mesh.vertices) + list(cc.mesh.vertices)
            #result.mesh = Trimesh(vertices, faces)
            if cc.extra.get('uv', None):
                if 'uv' not in result.extra: result.extra['uv'] = []
                #offset = len(result.extra['uv'])
                result.extra['uv'] = result.extra['uv'] + list(cc.extra['uv'])

        #result.mesh.merge_vertices()  # This would vertices duplicated for UV coords
        #result.mesh.fix_normals()

        result.children = []
        return result

    def extrude_step(self, obj_2d, offset, cap=True, base=None, method=D1D2D3.EXTRUSION_METHOD_WRAP):
        """
        Base argument is supported for compatibility with DDDObject2 signature, but ignored.
        """

        if self.children:
            raise DDDException("Cannot extrude_step with children.")

        result = self.copy()
        result = extrusion.extrude_step(result, obj_2d, offset, cap=cap, method=method)
        return result

    '''
    def metadata(self, path_prefix, name_suffix):
        node_name = self.uniquename() + name_suffix
        ignore_keys = ('uv', 'osm:feature', 'ddd:connections')
        metadata = dict(self.extra)
        metadata['ddd:path'] = path_prefix + node_name
        if self.mat and self.mat.name:
            metadata['ddd:material'] = self.mat.name
        if self.mat and self.mat.color:
            metadata['ddd:material:color'] = self.mat.color  # hex
        if self.mat and self.mat.extra:
            # If material has extra metadata, add it but do not replace
            metadata.update({k:v for k, v in self.mat.extra.items()})  # if k not in metadata or metadata[k] is None})

        metadata = json.loads(json.dumps(metadata, default=lambda x: D1D2D3.json_serialize(x)))
        metadata = {k: v for k,v in metadata.items() if v is not None and k not in ignore_keys}

        return metadata
    '''

    def twosided(self):
        result = self.copy()

        result.children = [c.twosided() for c in result.children]

        if result.mesh:
            inverted = self.mesh.copy()
            inverted.invert()
            #result.append(ddd.mesh(inverted))
            result.mesh = concatenate(result.mesh, inverted)

        return result

    def convex_hull(self):
        result = self.copy()
        if result.mesh:
            result.mesh = convex_hull(result.mesh)

        for c in result.children:
            result = result.combine(c.convex_hull())
            result.mesh = convex_hull(result.mesh)

        return result



    def subdivide_to_size(self, max_edge, max_iter=10):
        """
        Subdivide a mesh until every edge is shorter than a specified length.

        This method is based on the Trimesh method of the same name.
        """
        result = self.copy()

        result.children = [c.subdivide_to_size(max_edge, max_iter) for c in result.children]

        if result.mesh:
            vertices, faces = result.mesh.vertices, result.mesh.faces
            rvertices, rfaces = remesh.subdivide_to_size(vertices, faces, max_edge, max_iter=max_iter)
            result.mesh = Trimesh(rvertices, rfaces)

        return result


    def clean(self):
        result = self.copy()
        result.mesh.merge_vertices()
        result.mesh.remove_degenerate_faces()
        result.mesh.merge_vertices()
        return result

    '''
    def triangulate(self, twosided=False):
        return self
    '''

    '''
    def _recurse_scene(self, path_prefix, name_suffix, instance_mesh, instance_marker):
        """
        Produces a Trimesh scene.
        """

        scene = Scene()

        node_name = self.uniquename()

        # Add metadata to name
        metadata = None
        if True:
            metadata = self.metadata(path_prefix, name_suffix)
            #print(json.dumps(metadata))
            serialized_metadata = base64.b64encode(json.dumps(metadata, default=D1D2D3.json_serialize).encode("utf-8")).decode("ascii")
            encoded_node_name = node_name + "_" + str(serialized_metadata)

        # Do not export nodes indicated 'ddd:export-as-marker' if not exporting markers
        if metadata.get('ddd:export-as-marker', False) and not instance_marker:
            return scene
        if metadata.get('ddd:marker', False) and not instance_marker:
            return scene

        # UV coords test
        if self.mesh:
            try:
                self.mesh = self._process_mesh()
            except Exception as e:
                logger.error("Could not process mesh for serialization (%s %s): %s", self, metadata, e,)
                raise DDDException("Could not process mesh for serialization: %s" % e, ddd_obj=self)

        scene.add_geometry(geometry=self.mesh, node_name=encoded_node_name.replace(" ", "_"))

        cscenes = []
        if self.children:
            for idx, c in enumerate(self.children):
                cscene = c._recurse_scene(path_prefix=path_prefix + node_name + "/", name_suffix="#%d" % (idx), instance_mesh=instance_mesh, instance_marker=instance_marker)
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
    '''

    def _process_mesh(self):
        if self.extra.get('uv', None):
            uvs = self.extra['uv']
        else:
            # Note that this does not flatten normals (that should be optional) - also, we assume mesh is rotated (XZ)
            uvs = [[v[0], v[2]] for v in self.mesh.vertices]

        if len(uvs) != len(self.mesh.vertices):
            logger.warning("Invalid number of UV coordinates: %s (vertices: %s, uv: %s)", self, len(self.mesh.vertices), len(uvs))
            #raise DDDException("Invalid number of UV coordinates: %s", self)
            uvs = [[v[0], v[2]] for v in self.mesh.vertices]

        #if self.mesh.visual is None:
        #    self.mesh.visual = TextureVisuals(uv=uvs, material=mat)
        #else:
        #    self.mesh.visual.uv = uvs

        if self.mat:

            uvscale = self.mat.extra.get('uv:scale', None)
            if uvscale:
                uvs = [[v[0] * uvscale, v[1] * uvscale] for v in uvs]

            # Material + UVs
            mat = self.mat._trimesh_material()
            self.mesh.visual = TextureVisuals(uv=uvs, material=mat)  # Material + UVs

            # Vertex Colors
            #if self.mat.extra.get('ddd:vertex_colors', False):
            if self.mat.color:
                cvs = ColorVisuals(mesh=self.mesh, face_colors=[self.mat.color_rgba for f in self.mesh.faces])  # , material=material
                # Hack vertex_colors into TextureVisuals
                # WARN: Trimehs GLTF export modified to suppot this:
                #  gltf.py:542:      if mesh.visual.kind in ['vertex', 'face'] or hasattr(mesh.visual, 'vertex_colors'):
                #  gltf.py:561       remove elif, use if
                # TODO: UPDATE: new approach see https://github.com/mikedh/trimesh/pull/925 TextureVisuals.vertex_attributes['color']
                self.mesh.visual.vertex_colors = cvs.vertex_colors

        else:
            #logger.debug("No material set for mesh: %s", self)
            pass

        return self.mesh

    def _recurse_scene_tree(self, path_prefix, name_suffix, instance_mesh, instance_marker, include_metadata, scene=None, scene_parent_node_name=None):
        """
        Produces a Trimesh scene.
        """

        node_name = self.uniquename()

        # Add metadata to name
        metadata = self.metadata(path_prefix, name_suffix)

        if False:  # serialize metadata in name
            #print(json.dumps(metadata))
            serialized_metadata = base64.b64encode(json.dumps(metadata, default=D1D2D3.json_serialize).encode("utf-8")).decode("ascii")
            encoded_node_name = node_name + "_" + str(serialized_metadata)

        metadata_serializable = None
        if include_metadata:
            metadata_serializable = json.loads(json.dumps(metadata, default=D1D2D3.json_serialize))
        #scene.metadata['extras'] = test_metadata

        # Do not export nodes indicated 'ddd:export-as-marker' if not exporting markers
        if metadata.get('ddd:export-as-marker', False) and not instance_marker:
            return scene
        if metadata.get('ddd:marker', False) and not instance_marker:
            return scene

        mesh = self.mesh

        # UV coords test
        if mesh:
            try:
                mesh = self._process_mesh()
            except Exception as e:
                logger.error("Could not process mesh for serialization (%s %s): %s", self, metadata, e,)
                raise DDDException("Could not process mesh for serialization: %s" % e, ddd_obj=self)


        node_transform = transformations.translation_matrix([0, 0, 0])
        # transformations.euler_from_quaternion(obj.transform.rotation, axes='sxyz')
        #node_name = encoded_node_name.replace(" ", "_")
        scene_node_name = node_name.replace(" ", "_")
        scene_node_name = metadata['ddd:path'].replace(" ", "_")  # TODO: Trimesh requires unique names, but using the full path makes them very long. Not using it causes instanced geeometry to fail.

        if scene is None:
            scene = Scene(base_frame=scene_node_name)

        #if mesh is None: mesh = ddd.marker().mesh
        #print("Adding: %s to %s" % (scene_node_name, scene_parent_node_name))
        if mesh is None:
            scene.graph.update(frame_to=scene_node_name, frame_from=scene_parent_node_name, matrix=node_transform, geometry_flags={'visible': True}, extras=metadata_serializable)
        else:
            scene.add_geometry(geometry=mesh, node_name=scene_node_name, geom_name="Geom %s" % scene_node_name, parent_node_name=scene_parent_node_name, transform=node_transform, extras=metadata_serializable)

        if self.children:
            for idx, c in enumerate(self.children):
                c._recurse_scene_tree(path_prefix=path_prefix + node_name + "/", name_suffix="#%d" % (idx),
                                      instance_mesh=instance_mesh, instance_marker=instance_marker, include_metadata=include_metadata,
                                      scene=scene, scene_parent_node_name=scene_node_name)

        # Serialize metadata as dict
        #if False:
        #    #serializable_metadata_dict = json.loads(json.dumps(metadata, default=D1D2D3.json_serialize))
        #    #scene.metadata['extras'] = serializable_metadata_dict

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

    def _recurse_meshes(self, instance_mesh, instance_marker):
        cmeshes = []
        if self.mesh:
            mesh = self._process_mesh()
            cmeshes = [mesh]
        if self.children:
            for c in self.children:
                cmeshes.extend(c._recurse_meshes(instance_mesh, instance_marker))
        return cmeshes

    def recurse_objects(self):
        cobjs = [self]
        for c in self.children:
            cobjs.extend(c.recurse_objects())
        return cobjs

    def show(self, instance_mesh=None, instance_marker=None):

        logger.info("Showing: %s", self)

        self.dump()

        if instance_marker is None:
            instance_marker = D1D2D3Bootstrap.export_marker
        if instance_mesh is None:
            instance_mesh = D1D2D3Bootstrap.export_mesh

        if D1D2D3Bootstrap.renderer == 'pyglet':

            # OpenGL
            #rotated = self.rotate([-math.pi / 2.0, 0, 0])
            rotated = ddd.group([self]).rotate([-math.pi / 2.0, 0, 0])

            #scene = rotated._recurse_scene("", "", instance_mesh=instance_mesh, instance_marker=instance_marker)
            trimesh_scene = rotated._recurse_scene_tree("", "", instance_mesh=instance_mesh, instance_marker=instance_marker, include_metadata=True)

            # Example code light
            #light = trimesh.scene.lighting.DirectionalLight()
            #light.intensity = 10
            #scene.lights = [light]
            trimesh_scene.show('gl')

        elif D1D2D3Bootstrap.renderer == 'pyrender':

            # PyRender
            import pyrender
            #pr_scene = pyrender.Scene.from_trimesh_scene(rotated)
            # Scene not rotated, as pyrender seems to use Z for vertical.
            meshes = self._recurse_meshes(instance_mesh=instance_mesh, instance_marker=instance_marker)  # rotated
            pr_scene = pyrender.Scene()
            for m in meshes:
                prm = pyrender.Mesh.from_trimesh(m, smooth=False) #, wireframe=True)
                pr_scene.add(prm)
            pyrender.Viewer(pr_scene, lighting="direct")  #, viewport_size=resolution)
            #pyrender.Viewer(scene, lighting="direct")  #, viewport_size=resolution)

        elif D1D2D3Bootstrap.renderer == 'none':

            logger.info("Skipping rendering (renderer=none).")

        else:

            raise DDDException("Unknown rendering backend: %s" % D1D2D3Bootstrap.renderer)


    def save(self, path, instance_marker=None, instance_mesh=None, include_metadata=True):
        """
        Saves this object to a file.

        Format is chosen based on the file extension:

            .glb - GLB (GLTF) binary format
            .json - DDD custom JSON export format

        @todo: Unify export code paths and recursion, metadata, path name and mesh production.
        """

        # Unify export code paths and recursion, metadata, path name and mesh production.

        logger.info("Saving to: %s (%s)", path, self)

        if instance_marker is None:
            instance_marker = D1D2D3Bootstrap.export_marker
        if instance_mesh is None:
            instance_mesh = D1D2D3Bootstrap.export_mesh

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
            #scene = rotated._recurse_scene("", "", instance_mesh=instance_mesh, instance_marker=instance_marker)
            trimesh_scene = rotated._recurse_scene_tree("", "", instance_mesh=instance_mesh, instance_marker=instance_marker, include_metadata=include_metadata)
            data = trimesh.exchange.gltf.export_glb(trimesh_scene, include_normals=D1D2D3Bootstrap.export_normals)

        #elif path.endswith('.gltf'):
        #    rotated = self.rotate([-math.pi / 2.0, 0, 0])
        #    scene = rotated._recurse_scene("", "", instance_mesh=instance_mesh, instance_marker=instance_marker)
        #    #scene = rotated._recurse_scene_tree("", "", instance_mesh=instance_mesh, instance_marker=instance_marker)
        #    data = trimesh.exchange.gltf.export_gltf(scene, include_normals=D1D2D3Bootstrap.export_normals)
        #    print(files["model.gltf"])
        #    for k, v in files.items(): print(k, v)
        #    data = None

        elif path.endswith('.json'):
            #rotated = self.rotate([-math.pi / 2.0, 0, 0])
            #scene = rotated._recurse_scene("", instance_mesh=instance_mesh, instance_marker=instance_marker)
            data = DDDJSONFormat.export_json(self, "", instance_mesh=instance_mesh, instance_marker=instance_marker)
            data = data.encode("utf8")

        else:
            logger.error("Cannot save. Invalid 3D filename format: %s", path)
            raise DDDException("Cannot save. Invalid 3D filename format: %s" % path)

        #scene.export(path)
        with open(path, 'wb') as f:
            f.write(data)



ddd = D1D2D3

Node = DDDObject
Geometry2D = DDDObject2
Mesh = DDDObject3

from ddd.ops.collision import DDDCollision
from ddd.ops.geometry import DDDGeometry
from ddd.ops.reduction import DDDMeshOps
from ddd.ops.helper import DDDHelper
from ddd.ops.snap import DDDSnap
from ddd.ops.uvmapping import DDDUVMapping
from ddd.ops.align import DDDAlign
from ddd.pack.mats.defaultmats import DefaultMaterials
from ddd.materials.materials import MaterialsCollection
from ddd.util.dddrandom import DDDRandom

ddd.mats = MaterialsCollection()
ddd.mats.highlight = D1D2D3.material(color='#ff00ff')
ddd.MAT_HIGHLIGHT = ddd.mats.highlight
ddd.mats.load_from(DefaultMaterials())

ddd.geomops = DDDGeometry()

ddd.meshops = DDDMeshOps()

ddd.align = DDDAlign()

ddd.snap = DDDSnap()

ddd.collision = DDDCollision()

ddd.uv = DDDUVMapping()

ddd.helper = DDDHelper()

ddd.random = DDDRandom()


'''
# Selectors
class DDDSelectors():
    def extra_eq(self, k, v):
        return lambda o: o.extra.get(k, None) == v
    def extra(self, k, v):
        return self.extra_eq(k, v)
ddd.sel = DDDSelectors()
'''


