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


import copy
import json
import logging

import trimesh
from trimesh import creation, primitives, boolean, transformations, remesh
from ddd.ddd import D1D2D3, DDDObject3


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class DDDPath3(DDDObject3):
    """
    3D path (backed by Trimesh Path3)
    """


    def __init__(self, name=None, children=None, path3=None, extra=None, material=None):
        super().__init__(name, children, None, extra, material)
        self.path3 = path3

    def __repr__(self):
        return "%s(%s, verts=%d, children=%d)" % (self.__class__.__name__, self.uniquename(), len(self.path3.vertices) if self.path3 else 0, len(self.children) if self.children else 0)

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
        #node_transform = transformations.concatenate_matrices(
        #    transformations.translation_matrix(self.transform.position),
        #    transformations.quaternion_matrix(self.transform.rotation)
        #)
        node_transform = transformations.translation_matrix([0, 0, 0])

        # Material + UVs
        if self.mat:
            self.path3.colors = [self.mat.color_rgba]
            #mat = self.mat._trimesh_material()

        scene.add_geometry(geometry=self.path3, node_name=scene_node_name, geom_name=scene_node_name,
                            parent_node_name=scene_parent_node_name, transform=node_transform, extras=metadata_serializable)
        scene.graph.update(frame_to=scene_node_name, frame_from=scene_parent_node_name, matrix=node_transform, geometry_flags={'visible': True}, extras=metadata_serializable)

        return scene

    def copy(self, name=None):
        if name is None: name = self.name
        obj = DDDPath3(name=name, children=list(self.children), material=self.mat, extra=dict(self.extra))
        obj.path3 = copy.deepcopy(self.path3)
        return obj