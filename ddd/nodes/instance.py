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
from ddd.ddd import DDDObject
from ddd.materials.atlas import TextureAtlas
from ddd.math.transform import DDDTransform
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

    def is_empty(self):
        """
        Instances are never considered empty, as they are assumed to contain something.
        """
        return False

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

    def rotate(self, v, origin=None):

        obj = self.copy()
        rot = quaternion_from_euler(v[0], v[1], v[2], "sxyz")
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

    def material(self, material, include_children=True):
        logger.warning("Ignoring material set to DDDInstance: %s", self)
        return self

    def combine(self, name=None):
        """
        Combine geometry of this instance.

        This is done by combining the actual geometry of each mesh referenced by the instance·

        This allows instances to be combined or expanded in batches, at the expense of multiplying their geometry.

        TODO: Maybe this method should not exist, and client code should either replace instances before combining (there's curerntly no method for that),
              or remove them if they are to be managed separately.
        """
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
