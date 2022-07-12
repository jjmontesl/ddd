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
import json
import logging
import math


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
from trimesh.scene.scene import Scene, append_scenes
from trimesh.transformations import quaternion_from_euler
from trimesh.visual.color import ColorVisuals
from trimesh.visual.material import SimpleMaterial, PBRMaterial
from trimesh.visual.texture import TextureVisuals

from ddd.core.cli import D1D2D3Bootstrap
from ddd.core.exception import DDDException
from ddd.formats.fbx import DDDFBXFormat
from ddd.materials.atlas import TextureAtlas
from ddd.materials.material import DDDMaterial
from ddd.math.vector3 import Vector3
from ddd.nodes.node import DDDNode
from ddd.ops import extrusion
from ddd.ddd import ddd

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
from ddd.formats.presentation.generic import Generic3DPresentation


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class DDDNode3(DDDNode):

    def __init__(self, name=None, children=None, mesh=None, extra=None, material=None):
        self.mesh = mesh
        super().__init__(name, children, extra, material)

    def __repr__(self):
        #return "%s(%s, faces=%d, children=%d)" % (self.__class__.__name__, self.uniquename(), len(self.mesh.faces) if self.mesh else 0, len(self.children) if self.children else 0)
        return "%s (%s %df %dc)" % (self.name, self.__class__.__name__, len(self.mesh.faces) if self.mesh else 0, len(self.children) if self.children else 0)
        #return "%s (%s %s %sv %dc)" % (self.name, self.__class__.__name__, self.geom.type if hasattr(self, 'geom') and self.geom else None, self.vertex_count() if hasattr(self, 'geom') else None, len(self.children) if self.children else 0)

    def copy(self, name=None):
        if name is None: name = self.name
        obj = DDDNode3(name=name, children=list(self.children), mesh=self.mesh.copy() if self.mesh else None, material=self.mat, extra=dict(self.extra))
        obj.transform = self.transform.copy()
        #obj = DDDObject3(name=name, children=[c.copy() for c in self.children], mesh=self.mesh.copy() if self.mesh else None, material=self.mat, extra=dict(self.extra))

        return obj

    def is_empty(self):
        """
        Tells whether this object has no mesh, or mesh is empty, and
        all children are also empty.
        """
        if self.mesh and not self.mesh.is_empty and not len(self.mesh.faces) == 0:
            return False
        for c in self.children:
            if not c.is_empty():
                return False
        return True

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

    def rotate(self, v, origin='local'):
        """
        If origin is 'local' or None, object is rotated around its local origin.
        If origin is 'centroid', the centroid of the group is used (the same center is used for all children).
        """
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

        obj.apply_components("rotate", v, origin=center_coords)
        obj.children = [c.rotate(v, origin=center_coords if origin != 'local' else 'local') for c in obj.children]
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
        """
        Inverts mesh triangles (which inverts triangle face normals).
        FIXME: What is the difference with flip_faces(), should both exist? document differences
        """
        obj = self.copy()
        if self.mesh:
            obj.mesh.invert()
        obj.children = [c.invert() for c in self.children]
        return obj

    def elevation_func(self, func):
        obj = self.copy()
        if obj.mesh:
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
        mesh.merge_vertices(merge_norm=True)

        obj = DDDObject3(mesh=mesh, children=self.children, material=self.mat)
        return obj

    def subtract(self, other):
        return self._csg(other, operation='subtract')

    def union(self, other):
        return self._csg(other, operation='union')

    def combine(self, name=None, indexes=False):
        """
        Combine geometry for this and all children meshes into a single mesh.
        This will also combine UVs (note: normals currently not considered).

        Metadata of the new element is cleaned (except for UVs and normals).
        If indexes is true, metadata will contain 'ddd:batch:indexes' which
        will contain triangle indexes and metadata for the combined objects.

        Does not modify the object, returns a copy of the geometry.

        TODO: consider normals
        TODO: currently, the first material found will be applied to the parent -show warning (?)-
        """
        result = self.copy(name=name)
        indexes_list = []
        base_index = 0

        if result.mesh:
            base_index = len(result.mesh.faces)
            indexes_list.append( (base_index, self.metadata("", "")) )

        for c in self.children:
            cc = c.combine(indexes=indexes)
            if result.mat is None and cc.mat is not None: result = result.material(cc.mat)

            # Remove visuals, as when joining meshes Trimesh will try to concatenate UV but also textures
            if result.mesh: result.mesh.visual = ColorVisuals()
            if cc.mesh: cc.mesh.visual = ColorVisuals()

            result.mesh = result.mesh + cc.mesh if result.mesh else cc.mesh

            # TODO: Combine metadata
            if cc.get('ddd:material:splatmap', None):
                result.set('ddd:material:splatmap', cc.get('ddd:material:splatmap'))

            #result.extra.update(cc.extra)
            #vertices = list(result.mesh.vertices) + list(cc.mesh.vertices)
            #result.mesh = Trimesh(vertices, faces)
            if 'uv' not in result.extra: result.extra['uv'] = []
            if cc.extra.get('uv', None):
                #offset = len(result.extra['uv'])
                result.extra['uv'] = result.extra['uv'] + list(cc.extra['uv'])

            # Store indexes and original objects
            if indexes:
                for ci in cc.get('ddd:batch:indexes'):
                    base_index += ci[0]  # Accumulate for siblings
                    indexes_list.append( (base_index, ci[1]) )

        #if result.mesh:
        #    result.mesh.merge_vertices()  # Causes incorrect UV coordinates. This would vertices duplicated for UV coords
        #result.mesh.fix_normals()

        result.children = []
        if indexes:
            result.set('ddd:batch:indexes', indexes_list)

        return result

    #def extrude_step(self, obj_2d, offset, cap=True, base=None, method=D1D2D3.EXTRUSION_METHOD_WRAP):
    def extrude_step(self, obj_2d, offset, cap=True, base=None, method=extrusion.EXTRUSION_METHOD_WRAP):
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

    def flip_faces(self):
        """
        FIXME: What is the difference with invert(), should both exist? document differences
        """
        result = self.copy()
        if result.mesh:
            flipped_faces = np.fliplr(result.mesh.faces)
            result.mesh.faces = flipped_faces
            #result.geom = result.geom.simplify(distance)  #, preserve_topology=True)
        result.children = [c.flip_faces() for c in self.children]
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

        Note that other subdivision methods exist:
        - for 2D LineStrings, check .subdivide_to_size()
        - for 3D meshes, also see .subdivide_to_grid()

        TODO: Move this to meshops.
        """
        result = self.copy()

        result.children = [c.subdivide_to_size(max_edge, max_iter) for c in result.children]

        if result.mesh:
            vertices, faces = result.mesh.vertices, result.mesh.faces
            rvertices, rfaces = remesh.subdivide_to_size(vertices, faces, max_edge, max_iter=max_iter)
            result.mesh = Trimesh(rvertices, rfaces)

        return result

    def merge_vertices(self, keep_normals=False):
        """
        Merges vertices. Modifies the object in place

        Merges vertices of each children recursively (but keeps structure, does not merge between objects).

        @see Also see trimesh.smoothed and trimesh.merge_vertices.
        """

        for c in self.children:
            c.merge_vertices(keep_normals=keep_normals)

        if self.mesh:
            self.mesh.merge_vertices(merge_norm=not keep_normals)  # , digits_vertex=5, digits_norm=5)  # merge_tex=True, digits_text
            # FIXME: Account for UVs instead of clearing them
            if self.extra.get('uv') and len(self.extra['uv']) != len(self.mesh.vertices):
                logger.warn("FIXME: removing UVs (invalid count) after merge_vertices for: %s", self)
                self.extra['uv'] = None

        return self

    def smooth(self, angle=math.pi * 0.475):  #, facet_minarea=None):
        """
        Smoothes normals. Returns a copy of the object.

        Eg. Using PI/2 (90 degrees) or above produces smoothed square corners, using < PI/3 keeps square corners.

        Note that this requires vertices that need smoothed to be merged already, but this operation may split
        vertices if needed (and vertex count will change).

        It smoothes vertices of each children recursively (but keeps structure, does not smooth between objects).

        @see Also see trimesh.smoothed and trimesh.merge_vertices.
        """
        result = self.copy()

        result.children = [c.smooth(angle=angle) for c in result.children]

        if self.mesh:
            #self.mesh.fix_normals()
            result.mesh = self.mesh.smoothed(angle=angle)  # , facet_minarea=None)  # facet_minarea)

            # FIXME: Account for UVs instead of clearing them
            if self.extra.get('uv') and len(self.extra['uv']) != len(self.mesh.vertices):
                logger.warn("FIXME: removing UVs (invalid count) after smooth for: %s", self)
                self.extra['uv'] = None

        #result.mesh.merge_vertices(use_tex=True, merge_norm=False)

        return result


    def clean(self, remove_empty=True, remove_degenerate=True):
        """
        """
        result = self.copy()
        if result.mesh and remove_degenerate:
            result.mesh.remove_degenerate_faces()

        result.children = [c.clean(remove_empty, remove_degenerate) for c in result.children]
        if remove_empty:
            result.children = [c for c in result.children if not c.is_empty()]

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

            # Apply material uv:scale from material metadata if available
            uvscale = self.mat.extra.get('uv:scale', None)
            if uvscale and uvs:
                if not isinstance(uvscale, list):
                    uvscale = (uvscale, uvscale)
                try:
                    uvscale_x, uvscale_y = uvscale
                    nuvs = [[v[0] * uvscale_x, v[1] * uvscale_y] for v in uvs]
                    uvs = nuvs
                except Exception as e:
                    logger.error("Error computing UV coordinates for %s: %s", self, e)

            # Material + UVs
            mat = self.mat._trimesh_material()
            self.mesh.visual = TextureVisuals(uv=uvs, material=mat)  # Material + UVs

            # Vertex Colors (note that vertex colors take space)
            # Vertex colors tint meshes in BabylonJS (multiply)
            if self.mat.color:
                # Note that color and texture_color seem to be used inconsistently when creating the PBRMaterial: document, move to metadata...?
                #cvs = ColorVisuals(mesh=self.mesh, face_colors=[self.mat.color_rgba for f in self.mesh.faces])  # , material=material

                #Force vertex colors for test purposes
                #test_color = (1.0, 0.2, 0.2, 1.0)  #trimesh.visual.color.hex_to_rgba("#ff0000")
                #cvs = ColorVisuals(mesh=self.mesh, face_colors=[test_color for f in self.mesh.faces])  # , material=material

                # Assign vertex colors (this takes more space)
                #self.mesh.visual.vertex_attributes['color'] = cvs.vertex_colors
                pass

        else:
            #logger.debug("No material set for mesh: %s", self)
            pass

        return self.mesh

    def _recurse_scene_tree(self, path_prefix, name_suffix, instance_mesh, instance_marker, include_metadata, scene=None, scene_parent_node_name=None, usednames=None):
        """
        Produces a Trimesh scene.
        """

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

        mesh = self.mesh

        # UV coords test
        if mesh:
            try:
                mesh = self._process_mesh()
            except Exception as e:
                logger.error("Could not process mesh for serialization (%s %s): %s", self, metadata, e,)
                raise DDDException("Could not process mesh for serialization: %s" % e, ddd_obj=self)

        # Get node transform
        ##node_transform = transformations.identity_matrix()
        ##transformations.euler_from_quaternion(obj.transform.rotation, axes='sxyz')
        #node_transform = transformations.translation_matrix([0, 0, 0])
        node_transform = self.transform.to_matrix()

        #node_name = encoded_node_name.replace(" ", "_")
        scene_node_name = node_name  #.replace(" ", "_")
        #scene_node_name = metadata['ddd:path'] #.replace(" ", "_")  # TODO: Trimesh requires unique names, but using the full path makes them very long. Not using it causes instanced geeometry to fail.

        if scene is None:
            scene = Scene(base_frame=scene_node_name)
            # Add node metadata to scene metadata (first node metadata seems not available at least in blender)
            scene.metadata['extras'] = metadata_serializable

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
                                      scene=scene, scene_parent_node_name=scene_node_name, usednames=usednames)

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
        """
        Returns a list of all objects recursively in preorder.
        Includes the root node in first place.
        Does not include DDDInstance or other objects.
        """
        cobjs = [self]
        for c in self.children:
            if isinstance(c, DDDObject3):
                cobjs.extend(c.recurse_objects())
        return cobjs

    def show3(self, instance_mesh=None, instance_marker=None, label=None):

        logger.info("Showing: %s", self)

        #self.dump()

        if instance_marker is None:
            instance_marker = D1D2D3Bootstrap.export_marker
        if instance_mesh is None:
            instance_mesh = D1D2D3Bootstrap.export_mesh

        if D1D2D3Bootstrap.renderer == 'pyglet':

            from trimesh import viewer

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
                prm = pyrender.Mesh.from_trimesh(m)  #, smooth=False) #, wireframe=True)
                pr_scene.add(prm)
            pyrender.Viewer(pr_scene, lighting="direct")  #, viewport_size=resolution)
            #pyrender.Viewer(scene, lighting="direct")  #, viewport_size=resolution)

        elif D1D2D3Bootstrap.renderer == 'none':

            logger.info("Skipping rendering (renderer=none).")

        elif callable(D1D2D3Bootstrap.renderer):
            logger.info("Generating result through show() callback: %s", self)
            D1D2D3Bootstrap.renderer(self, label=label)

        else:

            raise DDDException("Unknown rendering backend: %s" % D1D2D3Bootstrap.renderer)


    def save(self, path, instance_marker=None, instance_mesh=None, include_metadata=True, size=None):
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

        elif path.endswith('.fbx'):

            rotated = self.rotate([-math.pi / 2.0, 0, 0])
            #scene = rotated._recurse_scene("", "", instance_mesh=instance_mesh, instance_marker=instance_marker)
            trimesh_scene = rotated._recurse_scene_tree("", "", instance_mesh=instance_mesh, instance_marker=instance_marker, include_metadata=include_metadata)
            #data = trimesh.exchange.fbx.export_fbx(trimesh_scene)
            data = DDDFBXFormat.export_fbx(self, path)

        elif path.endswith('.glb'):
            rotated = self.rotate([-math.pi / 2.0, 0, 0])
            #scene = rotated._recurse_scene("", "", instance_mesh=instance_mesh, instance_marker=instance_marker)
            trimesh_scene = rotated._recurse_scene_tree("", "", instance_mesh=instance_mesh, instance_marker=instance_marker, include_metadata=include_metadata)
            data = trimesh.exchange.gltf.export_glb(trimesh_scene, include_normals=D1D2D3Bootstrap.export_normals)

        elif path.endswith('.gltf'):
            rotated = self.rotate([-math.pi / 2.0, 0, 0])
            #scene = rotated._recurse_scene("", "", instance_mesh=instance_mesh, instance_marker=instance_marker)
            trimesh_scene = rotated._recurse_scene_tree("", "", instance_mesh=instance_mesh, instance_marker=instance_marker, include_metadata=include_metadata)
            files = trimesh.exchange.gltf.export_gltf(trimesh_scene, include_normals=D1D2D3Bootstrap.export_normals)
            data = files['model.gltf']
            #trimesh_scene.export(path)  # files = trimesh.exchange.gltf.export_glb(trimesh_scene, include_normals=D1D2D3Bootstrap.export_normals)

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

        elif path.endswith('.png'):
            #rotated = self.rotate([-math.pi / 2.0, 0, 0])
            #scene = rotated._recurse_scene("", instance_mesh=instance_mesh, instance_marker=instance_marker)
            data = DDDPNG3DRenderFormat.export_png_3d_render(self, instance_mesh=instance_mesh, instance_marker=instance_marker, size=size)

        else:
            logger.error("Cannot save. Invalid 3D filename format: %s", path)
            raise DDDException("Cannot save. Invalid 3D filename format: %s" % path)

        # If path is just a .extension (eg .glb), returns the result file as a byte buffer.
        return_data = (path.split(".")[0] == '')
        if return_data:
            return data

        #scene.export(path)
        if data is not False:
            with open(path, 'wb') as f:
                f.write(data)


DDDObject3 = DDDNode3