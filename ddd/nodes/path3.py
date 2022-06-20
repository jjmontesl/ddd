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
from trimesh.path import entities
from ddd.ddd import D1D2D3, DDDObject3
from ddd.nodes.node3 import DDDNode3




# Get instance of logger for this module
logger = logging.getLogger(__name__)


class DDDPath3(DDDNode3):
    """
    3D path (backed by Trimesh Path3)
    """


    def __init__(self, name=None, children=None, path3=None, extra=None, material=None):
        super().__init__(name, children, extra, material)
        self.path3 = path3

    def __repr__(self):
        return "%s (%s %dv %de %dc)" % (self.uniquename(), self.__class__.__name__, len(self.path3.vertices) if self.path3 else 0, len(self.path3.entities) if self.path3 else 0, len(self.children) if self.children else 0)

    def _recurse_scene_tree(self, path_prefix, name_suffix, instance_mesh, instance_marker, include_metadata, scene=None, scene_parent_node_name=None):

        if len(self.path3.entities) < 0:
            return scene

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

        # Get node transform
        #node_transform = transformations.identity_matrix()
        node_transform = self.transform.to_matrix()

        # Material + UVs


        if self.mat and len(self.path3.entities) > 0:

            self.path3.colors = [self.mat.color_rgba] * len(self.path3.entities)

            '''
            # Test: different colors for sections
            # TODO: support colors for sections
            mats = [D1D2D3.mats.red, D1D2D3.mats.blue, D1D2D3.mats.green]
            colors = [mats[i % len(mats)].color_rgba for i in range(len(self.path3.entities))]
            self.path3.colors = colors
            '''


        scene.add_geometry(geometry=self.path3, node_name=scene_node_name, geom_name=scene_node_name,
                            parent_node_name=scene_parent_node_name, transform=node_transform, extras=metadata_serializable)
        scene.graph.update(frame_to=scene_node_name, frame_from=scene_parent_node_name, matrix=node_transform, geometry_flags={'visible': True}, extras=metadata_serializable)

        return scene

    def copy(self, name=None):
        if name is None: name = self.name
        path3_copy = copy.deepcopy(self.path3)
        obj = DDDPath3(name=name, children=list(self.children), path3=path3_copy, extra=dict(self.extra), material=self.mat)
        obj.transform = self.transform.copy()
        return obj

    def discretize(self, distance=1.0):

        coords = []
        for entity in self.path3.entities:
            if not coords:
                last_p = self.path3.vertices[entity.points[0]]
                coords.append(last_p)
            if isinstance(entity, entities.Line):
                for p in entity.points[1:]:
                    last_p = self.path3.vertices[p]
                    coords.append(last_p)
            elif isinstance(entity, entities.Arc):
                point_num = max(2, int(entity.length(self.path3.vertices) / distance) + 1)
                for p in list(entity.discrete(self.path3.vertices, point_num))[1:]:
                    last_p = p
                    coords.append(last_p)
            elif isinstance(entity, entities.Bezier):
                point_num = max(2, int(entity.length(self.path3.vertices) / distance) + 1)
                for p in list(entity.discrete(self.path3.vertices, 1.0, point_num))[1:]:
                    last_p = p
                    coords.append(last_p)
            elif isinstance(entity, entities.BSpline):
                point_num = max(2, int(entity.length(self.path3.vertices) / distance) + 1)
                for p in list(entity.discrete(self.path3.vertices, point_num))[1:]:
                    last_p = p
                    coords.append(last_p)
            else:
                raise NotImplementedError(entity)

        result = self.copy()
        result.path3 = trimesh.path.path.Path3D([
            entities.Line(range(len(coords))),
        ], coords)

        return result

    def to_line(self):
        """
        This assumes that the path is a single Line entity (eg. as returned by `discretize()`).

        Note: this currently ignores children.
        """
        result = D1D2D3.line([self.path3.vertices[i] for i in self.path3.entities[0].points])
        result.copy_from(self, copy_material=True)
        return result