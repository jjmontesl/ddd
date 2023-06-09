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


import logging
import sys
import time
from typing import Iterable
import numpy as np
from ddd.core.exception import DDDException
from ddd.core.selectors.selector import DDDSelector
from ddd.formats.presentation.generic import Generic3DPresentation
from ddd.math.transform import DDDTransform
from trimesh import transformations
from ddd.ddd import ddd

# Get instance of logger for this module
logger = logging.getLogger(__name__)



class DDDNode():

    def __init__(self, name=None, children=None, extra=None, material=None, transform=None):
        self.name = name
        self.children = children if children is not None else []
        self.extra = extra if extra is not None else {}

        self.mat = material
        self.transform = transform if transform is not None else DDDTransform()

        # TODO: FIXME: Adding A) parenting + full-blown hierarchy  and  B) per-function copy/alter semantics,  will impact tons of code... triple think and...
        self.parent = None

        self._uid = None

        #self.geom = None
        #self.mesh = None

        '''
        for c in self.children:
            if not isinstance(c, self.__class__) and not (isinstance(c, DDDInstance) and isinstance(self, DDDNode3)):
                #raise DDDException("Invalid children type on %s (not %s): %s" % (self, self.__class__, c), ddd_obj=self)
                pass
        '''

    def __repr__(self):
        #return "DDDObject(name=%r, children=%d)" % (self.name, len(self.children) if self.children else 0)
        return "%s (%s %dc)" % (self.name, self.__class__.__name__, len(self.children) if self.children else 0)

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

    def setname(self, name):
        name = name.replace('{}', str(self.name))
        self.name = name
        return self

    def rename_unique(self):
        """
        Walks hierarchy ensuring each node has a unique name.
        This process is also done by recurse_scene, since Trimesh doens't support repeated names, but we need to do it
        before in order to be able to also save other formats JSON with consistent naming.
        """
        usednames = {}  # name + count pairs
        def _rename_unique(obj, usednames):
            if str(obj.name) in usednames:
                usednames[str(obj.name)] += 1
                obj.name = str(obj.name) + "#" + str(usednames[str(obj.name)])
            else:
                usednames[str(obj.name)] = 1

            for c in obj.children:
                _rename_unique(c, usednames)

        _rename_unique(self, usednames)
        return self

    def copy(self, name=None, copy_children=True):
        if name is None: name = self.name
        children = []
        # TODO: FIXME: Whether to clone geometry and recursively copy children (in all Node, Node2 and Node3) heavily impacts performance, but removing it causes errors (and is semantically incorect) -> we should use a dirty/COW mechanism?
        if copy_children:
            children = [c.copy(copy_children=True) for c in self.children]
        obj = DDDNode(name=name, children=children, material=self.mat, extra=dict(self.extra))
        obj.transform = self.transform.copy()
        return obj

    def copy2(self, name=None, copy_children=True):
        if name is None: name = self.name
        children = []
        # TODO: FIXME: Whether to clone geometry and recursively copy children (in all Node, Node2 and Node3) heavily impacts performance, but removing it causes errors (and is semantically incorect) -> we should use a dirty/COW mechanism?
        if copy_children:
            children = [c.copy(copy_children=True) for c in self.children]
        obj = ddd.DDDNode2(name=name, children=children, material=self.mat, extra=dict(self.extra))
        obj.transform = self.transform.copy()
        return obj

    def copy3(self, name=None, copy_children=False):
        """
        Copies this DDDObject2 into a DDDObject3, maintaining metadata but NOT children or geometry.
        """
        # TODO: FIXME: Whether to clone geometry and recursively copy children (in all Node, Node2 and Node3) heavily impacts performance, but removing it causes errors (and is semantically incorect) -> we should use a dirty/COW mechanism?
        if copy_children:
            obj = ddd.DDDObject3(name=name if name else self.name, children=[(c.copy3(copy_children=True) if hasattr(c, 'copy3') else c.copy()) for c in self.children], mesh=None, extra=dict(self.extra), material=self.mat)
        else:
            obj = ddd.DDDObject3(name=name if name else self.name, children=[], mesh=None, extra=dict(self.extra), material=self.mat)
        obj.transform = self.transform.copy()

        return obj


    def copy_from(self, obj, copy_material=False, copy_children=False, copy_metadata_to_children=False, copy_transform=False):
        """
        Copies metadata (without replacing), and optionally material and children from another object.

        Modifies this object in place, and returns itself. This does not copy geometry or meshes or other non-node data.

        TODO: copy_material shall possibly be True by default
        """
        if obj.name:
            self.name = obj.name

        if copy_transform:
            self.transform = obj.transform.copy()

        # Copy attributes
        for k, v in obj.extra.items():
            self.set(k, default=v, children=copy_metadata_to_children)
        self.extra.update(obj.extra)

        if copy_children:
            self.children = [c.copy(copy_children=True) for c in obj.children]
        if copy_material and obj.mat:
            self.mat = obj.mat

        return self

    def highlight(self):
        return self.material(ddd.MAT_HIGHLIGHT)

    def reprname(self):
        node_name = self.name if self.name else self.__class__.__name__
        return node_name

    def uniquename(self, usednames=None):
        """
        Returns a unique name for this node (adding _2, _3... as needed).

        This is used by exporters that require a unique name, but note that this depends on the context
        and may vary if other objects are added to the hierarchy.
        """
        # Hashing
        #node_name = "%s_%s" % (self.name if self.name else 'Node', self.hash().hexdigest()[:8])

        # Number
        #if self._uid is None:
        #    D1D2D3._uid_last += 1
        #    self._uid = D1D2D3._uid_last  # random.randint(0, 2 ** 32)
        #node_name = "%s_%s" % (self.name if self.name else 'Node', self._uid)

        reprname = self.reprname()
        node_name = reprname

        # Check used names
        separator = '#'  # '_'
        if usednames:
            idx = 1
            while node_name in usednames:
                idx += 1
                node_name = reprname + separator + str(idx)

        return node_name

    def transform_translate(self, coords):
        result = self.copy()
        result.transform.translate(coords)
        return result

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
        self.transform = obj.transform
        return self

    def metadata(self, path_prefix, name_suffix):
        """
        Returns metadata
        """

        node_name = self.reprname() + name_suffix

        metadata = dict(self.extra)
        metadata['ddd:name'] = node_name
        metadata['ddd:path'] = path_prefix + node_name
        metadata['ddd:str'] = str(self)
        metadata['ddd:transform'] = str(self.transform)  # For debugging, but this string does not really belong here? (e.g. it's properly exported as underscore attributes in JSON)
        #metadata['ddd:parent'] = str(self.parent)
        metadata['ddd:type'] = '2d' if hasattr(self, "geom") else '3d'
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

        metadata = {k: v for k, v in metadata.items() if k not in ddd.METADATA_IGNORE_KEYS}  # and v is not None
        #metadata = json.loads(json.dumps(metadata, default=D1D2D3.json_serialize))

        return metadata

    def dump(self, data=False, indent_level=0):
        if indent_level == 0:
            total_children_len = sum(1 for _ in self.iterate_objects())
            logger.info("Dumping: %s (%d objects)", self, total_children_len)

        strdata = ""
        if data:
            #metadata = self.extra
            #metadata = self.metadata("", "")
            metadata = {k: v for k, v in self.extra.items() if not (k.startswith("_") or k in ddd.METADATA_IGNORE_KEYS)}
            if data != 'ddd':
                metadata = {k: v for k, v in metadata.items() if not k.startswith("ddd:")}
            strdata = strdata + " " + str(self.transform.position) + " " + str(metadata)
        print("  " * indent_level + str(self) + strdata)

        for c in self.children:
            c.dump(data=data, indent_level=indent_level + 1)

    def objlog(self, logstr):
        """
        Adds a log string to the object. This is used to store information about the object processing.
        """
        current_log = self.get('ddd:_log', "")
        current_log = current_log + logstr + " "
        self.set('ddd:_log', current_log)

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

    def select(self, selector=None, path=None, func=None, recurse=True, apply_func=None, _rec_path=None, empty=None):
        """

        Note: Recurse is True in this function, but False for selectors in DDDTasks.
        TODO: Make recurse default to False (this will require extensive testing)
        """

        if empty is None:
            if isinstance(self, ddd.DDDNode2):
                empty = 2
            elif isinstance(self, ddd.DDDNode3):
                empty = 3

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
            # TODO: Implement path pattern matching (ie. css selectors, path selectors... ?)
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
            for idx, c in enumerate(list(o.children)):
                cr = c.select(func=func, selector=selector, path=path, recurse=recurse, apply_func=apply_func, _rec_path=_rec_path, empty=empty)
                if hasattr(cr, '_remove_object') and cr._remove_object:
                    to_remove.append(c)
                if hasattr(cr, '_add_object') and cr._add_object:
                    if isinstance(cr._add_object, list):
                        to_add.append((idx, cr._add_object))
                    else:
                        to_add.append((idx, [cr._add_object]))
                        #to_add.extend(cr.children)
                delattr(cr, '_remove_object')
                delattr(cr, '_add_object')
                result.extend(cr.children)

            # Operate coherently (maintain order)
            newchildren = list(o.children)
            for ta in reversed(to_add):
                newchildren = newchildren[:ta[0]] + ta[1] + newchildren[ta[0] + 1:]
            newchildren = [coc for coc in newchildren if coc not in to_remove]
            o.children = newchildren

            # Deprecated: Old method (added all new items at the end)
            #o.children = [coc for coc in o.children if coc not in to_remove]
            #for ta in to_add: o.children.extend(ta[1])

        #if (isinstance(o, list)):
        #    o.children.extend()

        #self.children = [c for c in self.children if c not in result]

        res = self.grouptyped(result, empty=empty)
        res._remove_object = remove_object
        res._add_object = add_object
        return res

    def filter(self, func):
        """
        @deprecated Use `select`
        """
        return self.select(func=func)

    def select_remove(self, selector=None, path=None, func=None, recurse=True):
        def task_select_apply_remove(o):
            return False
        return self.select(selector=selector, path=path, func=func, apply_func=task_select_apply_remove, recurse=recurse)

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
                if isinstance(comp, DDDNode):
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

        if ddd.data is not None: dicts.append(ddd.data)

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

    def unset(self, key, children=False):
        if key in self.extra:
            del(self.extra[key])

        if children:
            # Apply to select_all
            for o in self.children:
                o.unset(key, children=children)

        return self

    def set(self, key, value=None, children=False, default=(None, )):
        """
        If the key is a dictionary, all its keys/values are set.
        """

        # If the key is a dictionary, all its keys/values are set
        if isinstance(key, dict):
            for k, v in key.items():
                self.set(k, v, children=children, default=default)
            return self

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

    def grouptyped(self, children=None, name=None, empty=None):
        result = None
        if isinstance(self, ddd.DDDObject2):
            result = ddd.group(children, empty=2)
        elif isinstance(self, ddd.DDDObject3) or isinstance(self, ddd.DDDInstance):
            result = ddd.group(children, empty=3)
        else:
            result = ddd.group(children, empty=empty)
        if name:
            result.name = name
        return result

    def flatten(self):
        """
        Flattens the node hierarchy recursively.

        This affects the node hierarchy only, not geometries (in contrast to individualize, which will
        for example also split multipolygons).
        """

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

    def children_len(self):
        return len(self.children)

    def append(self, obj):
        """
        Adds an object as a children to this node.
        If a list is passed, each element is added.
        """
        if isinstance(obj, Iterable):
            for i in obj:

                # FIXME: sanity check (exploratory)
                #if i.parent is not None:
                #    raise DDDException("Cannot append object(s) '%s' to '%s' children (already has parent: '%s')" % (i, self, i.parent))
                
                self.children.append(i)
                i.parent = self
        elif isinstance(obj, DDDNode):
            # FIXME: sanity check (exploratory)
            #if obj.parent is not None:
            #    raise DDDException("Cannot append object '%s' to '%s' children (already has parent: '%s')" % (obj, self, obj.parent))
            
            self.children.append(obj)
            obj.parent = self
        else:
            raise DDDException("Cannot append object to DDDObject children (wrong type): %s" % obj)
        return self

    def remove(self, obj, by_name=False):
        """
        Removes an object from this node children recursively. Modifies objects in-place.

        TODO: since copy() was changed to copy children recursively, this can no longer be used to remove results from a copied object :?
        """
        self.children = [c.remove(obj, by_name) for c in self.children if c and (c != obj and (not by_name or c.name != obj.name))]
        return self

    def is_empty(self):
        """
        Tells whether this object has no geometry, or geometry is empty, and
        all children are also empty.
        """
        for c in self.children:
            if not c.is_empty():
                return False
        return True

    def save(self, path, instance_marker=None, instance_mesh=None, include_metadata=True, size=None):
        # FIXME: Review: for base DDDNode, we are converting to DDDNode2/3 in order to save with a weak criteria
        if path.endswith(".svg"):
            obj = ddd.DDDNode2()
            obj.copy_from(self, copy_children=True)
        else:
            obj = ddd.DDDNode3.from_node(self)

        obj.save(path)

    def show(self, label=None):
        """
        Shows the node and its descendants.
        """
        #try:

        # Present 2D objects as 3D (recursively)
        showobj = Generic3DPresentation.present(self)
        showobj.show3(label=label)

        #except Exception as e:
        #    logger.error("Could not show object %s: %s", self, e)
        #    raise

    def translate(self, v):
        obj = self.copy()
        obj.transform.position = [obj.transform.position[0] + v[0], obj.transform.position[1] + v[1], obj.transform.position[2] + v[2]]
        return obj

    def rotate(self, v, origin=None):

        obj = self.copy()

        rot = transformations.quaternion_from_euler(v[0], v[1], v[2], "sxyz")
        obj.transform.rotation = transformations.quaternion_multiply(rot, obj.transform.rotation) # [0]

        '''
        obj = self.copy()
        rot = transformations.quaternion_from_euler(v[0], v[1], v[2], "sxyz")
        rotation_matrix = transformations.quaternion_matrix(rot)
        '''

        '''
        center_coords = None
        if origin == 'local':
            center_coords = None
        elif origin == 'bounds_center':  # group_centroid, use for children
            ((xmin, ymin, zmin), (xmax, ymax, zmax)) = self.bounds()
            center_coords = [(xmin + xmax) / 2, (ymin + ymax) / 2, (zmin + zmax) / 2]
        elif origin:
            center_coords = origin

        obj = self.copy()
        if obj.mesh:
            rot = transformations.euler_matrix(v[0], v[1], v[2], 'sxyz')
            if center_coords:
                translate_before = transformations.translation_matrix(np.array(center_coords) * -1)
                translate_after = transformations.translation_matrix(np.array(center_coords))
                #transf = translate_before * rot # * rot * translate_after  # doesn't work, these matrifes are 4x3, not 4x4 HTM
                obj.mesh.vertices = trimesh.transform_points(obj.mesh.vertices, translate_before)
                obj.mesh.vertices = trimesh.transform_points(obj.mesh.vertices, rot)
                obj.mesh.vertices = trimesh.transform_points(obj.mesh.vertices, translate_after)
            else:
                #transf = rot
                obj.mesh.vertices = trimesh.transform_points(obj.mesh.vertices, rot)
        '''

        '''
        obj.transform.position = np.dot(rotation_matrix, obj.transform.position + [1])[:3]  # Hack: use matrices
        obj.transform.rotation = transformations.quaternion_multiply(rot, obj.transform.rotation)  # order matters!
        '''

        return obj

    def scale(self, v):
        obj = self.copy()
        obj.transform.position = np.array(v) * obj.transform.position
        return obj

    def iterate_objects(self):
        """Preorder."""
        yield self
        for o in self.children:
            yield from o.iterate_objects()

    def material(self, material, include_children=True):
        obj = self.copy()
        obj.mat = material

        #if obj.mesh and material is not None:
        #    obj.mesh.visual.face_colors = material

        #visuals = mesh.visuatrimesh.visual.ColorVisuals(mesh=mesh, face_colors=[material])  # , material=material
        #mesh.visuals = visuals

        if include_children:
            obj.children = [c.material(material) for c in obj.children]

        return obj


"""
class DDDNode(DDDObject3):


    def __init__(self, name=None, children=None, extra=None, material=None):
        self.transform = DDDTransform()

        # Temporary while we extend DDDObject3
        super().__init__(name, children, None, extra, material)

    def __repr__(self):
        return "%s(%s, ref=%s)" % (self.__class__.__name__, self.uniquename(), self.ref)

    def copy(self):
        obj = DDDNode(ref=self.ref, name=self.name, extra=dict(self.extra))
        obj.transform = self.transform.copy()
        return obj

    def is_empty(self):
        '''
        Instances are never considered empty, as they are assumed to contain something.
        '''
        return False

    def vertex_iterator(self):
        rotation_matrix = transformations.quaternion_matrix(self.transform.rotation)
        node_transform = self.transform.to_matrix()
        for v in self.ref.vertex_iterator():
            vtransformed = np.dot(rotation_matrix, v)
            vtransformed = [vtransformed[0] + self.transform.position[0], vtransformed[1] + self.transform.position[1], vtransformed[2] + self.transform.position[2], v[3]]
            # FIXME: TODO: apply full transform via numpy
            yield vtransformed

    def translate(self, v):
        obj = self.copy()
        obj.transform.position = [obj.transform.position[0] + v[0], obj.transform.position[1] + v[1], obj.transform.position[2] + v[2]]
        return obj

    def rotate(self, v, origin=None):

        obj = self.copy()
        rot = transformations.quaternion_from_euler(v[0], v[1], v[2], "sxyz")
        rotation_matrix = transformations.quaternion_matrix(rot)

        '''
        center_coords = None
        if origin == 'local':
            center_coords = None
        elif origin == 'bounds_center':  # group_centroid, use for children
            ((xmin, ymin, zmin), (xmax, ymax, zmax)) = self.bounds()
            center_coords = [(xmin + xmax) / 2, (ymin + ymax) / 2, (zmin + zmax) / 2]
        elif origin:
            center_coords = origin

        obj = self.copy()
        if obj.mesh:
            rot = transformations.euler_matrix(v[0], v[1], v[2], 'sxyz')
            if center_coords:
                translate_before = transformations.translation_matrix(np.array(center_coords) * -1)
                translate_after = transformations.translation_matrix(np.array(center_coords))
                #transf = translate_before * rot # * rot * translate_after  # doesn't work, these matrifes are 4x3, not 4x4 HTM
                obj.mesh.vertices = trimesh.transform_points(obj.mesh.vertices, translate_before)
                obj.mesh.vertices = trimesh.transform_points(obj.mesh.vertices, rot)
                obj.mesh.vertices = trimesh.transform_points(obj.mesh.vertices, translate_after)
            else:
                #transf = rot
                obj.mesh.vertices = trimesh.transform_points(obj.mesh.vertices, rot)
        '''

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

    '''
    def marker(self, world_space=True):
        ref = D1D2D3.marker(name=self.name, extra=dict(self.extra))
        if world_space:
            ref = ref.scale(self.transform.scale)
            ref = ref.rotate(transformations.euler_from_quaternion(self.transform.rotation, axes='sxyz'))
            ref = ref.translate(self.transform.position)
        if self.ref:
            ref.extra.update(self.ref.extra)
        ref.extra.update(self.extra)
        return ref
    '''

    def combine(self, name=None):
        '''
        Combine geometry of this instance.

        This is done by combining the actual geometry of each mesh referenced by the instance·

        This allows instances to be combined or expanded in batches, at the expense of multiplying their geometry.

        TODO: Maybe this method should not exist, and client code should either replace instances before combining (there's curerntly no method for that),
              or remove them if they are to be managed separately.
        '''
        return DDDObject3(name=name)
        if self.ref:
            meshes = self.ref._recurse_meshes(True, False)
            obj = ddd.group3(name=name)
            for m in meshes:
                mo = DDDObject3(mesh=m)
                obj.append(mo)
            return obj.combine(name=name)
        else:
            return DDDObject3(name=name)

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


        # TODO: Call transform to_matrix
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

            instance_marker_cube = False
            if instance_marker_cube:
                ref = self.marker(world_space=False)
                scene.add_geometry(geometry=ref.mesh, node_name=scene_node_name + "_marker", geom_name="Marker %s" % scene_node_name,
                                   parent_node_name=scene_parent_node_name, transform=node_transform, extras=metadata_serializable)
            else:
                scene.graph.update(frame_to=scene_node_name, frame_from=scene_parent_node_name, matrix=node_transform, geometry_flags={'visible': True}, extras=metadata_serializable)

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
"""