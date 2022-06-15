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
from PIL import Image
import cairosvg
from csg import geom as csggeom
from csg.core import CSG
from matplotlib import colors
from shapely import geometry, affinity, ops
from shapely.geometry import shape, polygon
from shapely.geometry.linestring import LineString
from shapely.geometry.polygon import orient, Polygon
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
from shapely.ops import unary_union, polygonize
from geojson.feature import FeatureCollection
from lark.visitors import Transformer
from ddd.core.selectors.selector_ebnf import selector_ebnf
from ddd.core.selectors.selector import DDDSelector
from ddd.formats.json import DDDJSONFormat
from ddd.formats.svg import DDDSVG
from trimesh.convex import convex_hull
import os
from ddd.core import settings
from ddd.formats.geojson import DDDGeoJSONFormat
from shapely.geometry.multipolygon import MultiPolygon
from ddd.formats.png3drender import DDDPNG3DRenderFormat
from ddd.util.common import parse_bool
from shapely.strtree import STRtree


# Get instance of logger for this module
logger = logging.getLogger(__name__)


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

    def copy_from(self, obj, copy_material=False, copy_children=False, copy_metadata_to_children=False):
        """
        Copies metadata (without replacing), and optionally material and children from another object.

        Modifies this object in place, and returns itself.
        """
        if obj.name:
            self.name = obj.name

        # Copy item_2d attributes
        for k, v in obj.extra.items():
            self.set(k, default=v, children=copy_metadata_to_children)
        self.extra.update(obj.extra)

        if copy_children:
            self.children = list(obj.children)
        if copy_material and obj.material:
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

        ignore_keys = ('uv', 'osm:feature')  #, 'ddd:connections')
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

    #def find_or_none(self, path=None):

    def find(self, path=None):
        """
        Note: recently changed to return None instead of an exception if no objects are found.
        """

        # Shortcuts for performance
        # TODO: Path filtering shall be improved in select() method
        if path.startswith("/") and '*' not in path and (path.count('/') == 1 or (path.count('/') == 2 and path.endswith("/"))):
            parts = path[1:].split("/")
            result = [o for o in self.children if o.name == parts[0]]
            result = self.grouptyped(result)
        else:
            result = self.select(path=path, recurse=False)

        #if len(result.children) > 1:
        #    raise DDDException("Find '%s' expected 1 object but found %s." % (path, len(result.children)), ddd_obj=self)
        if len(result.children) == 0:
            return None

        return result.one()

    def select(self, selector=None, path=None, func=None, recurse=True, apply_func=None, _rec_path=None):
        """

        Note: Recurse is True in this function, but False for selectors in DDDTasks.
        TODO: Make recurse default to False (this will require extensive testing)
        """

        if hasattr(self, '_remove_object'): delattr(self, '_remove_object')
        if hasattr(self, '_add_object'): delattr(self, '_add_object')

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
                if hasattr(cr, '_remove_object') and cr._remove_object:
                    to_remove.append(c)
                if hasattr(cr, '_add_object') and cr._add_object:
                    if isinstance(cr._add_object, list):
                        to_add.extend(cr._add_object)
                    else:
                        to_add.append(cr._add_object)
                        #to_add.extend(cr.children)
                delattr(cr, '_remove_object')
                delattr(cr, '_add_object')
                result.extend(cr.children)
            o.children = [coc for coc in o.children if coc not in to_remove]
            o.children.extend(to_add)

        #if (isinstance(o, list)):
        #    o.children.extend()

        #self.children = [c for c in self.children if c not in result]

        res = self.grouptyped(result)
        res._remove_object = remove_object
        res._add_object = add_object
        return res

    def filter(self, func):
        """
        @deprecated Use `select`
        """
        return self.select(func=func)

    def select_remove(self, selector=None, path=None, func=None):
        def task_select_apply_remove(o):
            return False
        return self.select(selector=selector, path=path, func=func, apply_func=task_select_apply_remove)

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
                    try:
                        method_to_call = getattr(comp, methodname)
                        self.extra[k] = method_to_call(*args, **kwargs)
                    except Exception as e:
                        print(method_to_call.__code__)
                        raise DDDException("Cannot apply method to components of %s component %s: %s" % (self, comp, e))

    def get(self, keys, default=(None, ), extra=None, type=None):
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
                raise DDDException("Cannot resolve property %r in object '%s' (own: %s)" % (keys, self, self.extra))

        # Resolve lambda
        if callable(result):
            result = result()
            self.extra[key] = result

        if type is not None:
            if type == "bool":
                result = parse_bool(result)

        return result

    def set(self, key, value=None, children=False, default=(None, )):
        """
        """
        if children:
            # Apply to select_all
            for o in self.select().children:
                o.set(key, value, False, default)
        else:
            if default is self.set.__defaults__[2]:
                self.extra[key] = value
            else:
                if key not in self.extra or self.extra[key] is None:
                    self.extra[key] = default
        return self

    def prop_set(self, key, *args, **kwargs):
        return self.set(key, *args, **kwargs)

    def counter(self, key, add=1):
        """
        Increments current value of a property by a given value. Sets the property if it did not exist.
        """
        value = add + int(self.get(key, 0))
        self.set(key, value)
        return value

    def grouptyped(self, children=None, name=None):
        result = None
        if isinstance(self, DDDObject2):
            result = ddd.group(children, empty=2)
        elif isinstance(self, DDDObject3) or isinstance(self, DDDInstance):
            result = ddd.group(children, empty=3)
        else:
            result = ddd.group(children)
        if name:
            result.name = name
        return result

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
            raise DDDException("Cannot append object to DDDObject children (wrong type): %s" % obj)
        return self

    def remove(self, obj):
        """
        Removes an object from this node children recursively. Modifies objects in-place.
        """
        self.children = [c.remove(obj) for c in self.children if c and c != obj]
        return self

