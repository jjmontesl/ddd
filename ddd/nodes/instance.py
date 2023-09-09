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

import json
import logging

import numpy as np
from ddd.core.exception import DDDException
from ddd.nodes.node import DDDNode
from ddd.util.common import parse_bool
from trimesh import transformations
from trimesh.convex import convex_hull
from trimesh.transformations import quaternion_from_euler, quaternion_conjugate
from trimesh import transformations, transform_points
from ddd.ddd import ddd

# Get instance of logger for this module
logger = logging.getLogger(__name__)


class DDDInstance(DDDNode):

    def __init__(self, ref, name=None, extra=None):
        super().__init__(name, None, extra)
        self.ref = ref

    def __repr__(self):
        return "%s (%s ref: %s)" % (self.name, self.__class__.__name__, self.ref)

    def copy(self):
        obj = DDDInstance(ref=self.ref, name=self.name, extra=dict(self.extra))
        obj.transform = self.transform.copy()
        return obj

    def is_empty(self):
        """
        Instances are never considered empty, as they are assumed to contain something.
        """
        return False

    def clean(self, remove_empty=False, validate=True):
        return self

    def translate(self, v):
        obj = self.copy()
        obj.transform.position = [obj.transform.position[0] + v[0], obj.transform.position[1] + v[1], obj.transform.position[2] + v[2]]
        #obj.transform.translate()
        return obj

    def rotate(self, v, origin=None):
        """
        In an instance this rotates the transform, relative to the local origin.
        """

        center_coords = [0, 0, 0]
        if origin == 'local':
            center_coords = None
            #center_coords = self.transform.position
            #center_coords = [0, 0, 0]
        elif origin == 'bounds_center' or origin == 'centroid':  # group_centroid, use for children
            center_coords = self.center_aabb()
        elif origin:
            center_coords = origin
        
        obj = self.copy()

        rotation_matrix = transformations.euler_matrix(v[0], v[1], v[2], 'sxyz')
        if center_coords is not None:
            translate_before = transformations.translation_matrix(np.array(center_coords) * -1)
            translate_after = transformations.translation_matrix(np.array(center_coords))
            #transf = translate_before * rot # * rot * translate_after  # doesn't work, these matrices are 4x3, not 4x4 HTM
            rotation_matrix = transformations.concatenate_matrices(translate_before, rotation_matrix, translate_after)

        # Update the transform
        obj.transform.position = np.dot(rotation_matrix, obj.transform.position + [1])[:3]

        rotation_quat = quaternion_from_euler(v[0], v[1], v[2], "sxyz")
        #rotation_quat_conj = quaternion_conjugate(rotation_quat)
        ##rotation_quat_inv = quaternion_inverse(rotation_quat)
        #obj.transform.rotation = transformations.quaternion_multiply(obj.transform.rotation, rotation_quat_conj)
        #obj.transform.rotation = transformations.quaternion_multiply(rotation_quat, obj.transform.rotation)

        obj.transform.rotation = transformations.quaternion_multiply(rotation_quat, obj.transform.rotation)  

        return obj

    def scale(self, v):
        obj = self.copy()
        obj.transform.position = np.array(v) * obj.transform.position
        return obj

    def bounds(self):
        if self.ref:
            return self.ref.bounds()
        return None

    def marker(self, world_space=True, use_normal_box=False):
        if self.name is None:
            raise DDDException("Cannot create marker for instance without name: %s (%s)" % (self, self.extra))
        ref = ddd.marker(name=self.name, extra=dict(self.extra), use_normal_box=use_normal_box)
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

    def vertex_iterator(self):
        # FIXME: this approach to transformations is invalid, doesn't account for nested transforms (use world_matrix...)
        rotation_matrix = transformations.quaternion_matrix(self.transform.rotation)
        for v in self.ref.vertex_iterator():
            vtransformed = np.dot(rotation_matrix, v)
            vtransformed = [vtransformed[0] + self.transform.position[0], vtransformed[1] + self.transform.position[1], vtransformed[2] + self.transform.position[2], v[3]]
            # FIXME: TODO: apply full transform via numpy
            yield vtransformed

    def vertex_func(self, func, mask=None, world_matrix=None):
        """
        Applies a vertex function as a transform to the instance.
        """
        obj = self.copy()
        
        _parent_world_matrix = world_matrix
        if world_matrix is None:
            world_matrix = obj.transform.to_matrix()
        else:
            world_matrix = transformations.concatenate_matrices(world_matrix, obj.transform.to_matrix())
        
        obj.set("_world_matrix", _parent_world_matrix)

        world_xyz = obj.transform.position
        #obj.transform.position = func(obj.transform.position[0], obj.transform.position[1], obj.transform.position[2], None, obj)
        obj.transform.position = func(world_xyz[0], world_xyz[1], world_xyz[2], None, obj)
        
        #obj.children = [c.vertex_func(func, mask=mask, world_matrix=world_matrix) for c in obj.children]
        
        obj.unset("_world_matrix", children=True)

        return obj


    '''
    def combine(self, name=None):
        """
        Combine geometry of this instance.

        This is done by combining the actual geometry of each mesh referenced by the instance·

        This allows instances to be combined or expanded in batches, at the expense of multiplying their geometry.

        TODO: Maybe this method should not exist, and client code should either replace instances before combining (there's currently no method for that),
              or remove them if they are to be managed separately.
        """
        return DDDNode3(name=name)

        # This was all commented out before the entire combine function was
        if self.ref:
            meshes = self.ref._recurse_meshes(True, False)
            obj = ddd.group3(name=name)
            for m in meshes:
                mo = ddd.DDDNode3(mesh=m)
                obj.append(mo)
            return obj.combine(name=name)
        else:
            return ddd.DDDNode3(name=name)
    '''

    def expanded_instances(self):
        """
        Return a copy of the referenced node by this DDDInstance.
        TODO: seems there's some inconsistency about whether this (or rather, catalog-export) needs to include an intermediate node (see catalog export)
        """
        if not self.ref:
            raise DDDException("Cannot expand instance without reference: %s" % (self, ))
        
        result = self.ref.expanded_instances()  # already a copy
        result.copy_from(self, copy_transform=True)
        
        return result
    
    def _recurse_scene_tree(self, path_prefix, name_suffix, instance_mesh, instance_marker, include_metadata, scene=None, scene_parent_node_name=None, usednames=None, axis=None):

        #node_name = self.uniquename()
        #node_name = self.name
        if usednames is None: usednames = set()
        node_name = self.uniquename(usednames)
        usednames.add(node_name)

        # Add metadata to name
        metadata = self.metadata(path_prefix, name_suffix)

        #if True:
        #    serialized_metadata = base64.b64encode(json.dumps(metadata, default=D1D2D3.json_serialize).encode("utf-8")).decode("ascii")
        #    encoded_node_name = node_name + "_" + str(serialized_metadata)

        metadata_serializable = None
        if include_metadata:
            metadata_serializable = json.loads(json.dumps(metadata, default=ddd.json_serialize))

        node_transform = self.transform.to_matrix()
        
        if axis:  # "xZy"
            base_change = np.array([
                [1, 0, 0, 0],
                [0, 0, 1, 0],
                [0, -1, 0, 0],
                [0, 0, 0, 1],
            ])

            base_change_conj = np.transpose(base_change.copy())
            #node_transform = transformations.concatenate_matrices(base_change, node_transform)
            node_transform = transformations.concatenate_matrices(node_transform, base_change_conj)
            node_transform = transformations.concatenate_matrices(base_change, node_transform)
            #node_transform = transformations.quaternion_multiply(obj.transform.rotation, rotation_quat_conj)
            #obj.transform.rotation = transformations.quaternion_multiply(rotation_quat, obj.transform.rotation)

        scene_node_name = node_name # .replace(" ", "_")
        #scene_node_name = metadata['ddd:path'].replace(" ", "_")  # TODO: Trimesh requires unique names, but using the full path makes them very long. Not using it causes instanced geeometry to fail.

        if instance_mesh:
            if self.ref:

                if self.transform.scale != [1, 1, 1]:
                    raise DDDException("Invalid scale for an instance object (%s): %s", self.transform.scale, self)

                # TODO: Use a unique buffer! (same geom name for trimesh?)
                #ref = self.ref.copy()
                ref = self.ref.copy()  #.copy()

                # FIXME: TODO: NOTE: this line was used to fix issues with instances and prefabs and catalog and some exports or import pipelines, but it's unclear when to use it.
                #   - Note: compensation for: .save() rotation may be involved
                #   - ddd catalog-show  => seems to work with and without it (LEARNED: because there's no cal to rotate when presenting)
                #   - vrspace --export-meshes, creating and instancing (no catalog)  => seems to work only without it
                #   - vrspace --export-meshes, instancing from previously written catalog  => seems to work only without it
                #   - examples/lights --export-meshes  => seems to work only without it
                #   - vrspace .glb file imported via ddd-unity => ?
                # FIXME: Only needed when the scene_tree requires rotation/axis (try directly altering axis?)
                #ref = ref.rotate([-ddd.PI_OVER_2, 0, 0])  

                '''
                ##ref = ref.scale(self.transform.scale)
                #ref = ref.rotate(transformations.euler_from_quaternion(self.transform.rotation, axes='sxyz'))
                #ref = ref.translate(self.transform.position)

                #refscene = ref._recurse_scene(path_prefix=path_prefix + node_name + "/", name_suffix="#ref", instance_mesh=instance_mesh, instance_marker=instance_marker)
                #scene = append_scenes([scene] + [refscene])
                '''

                # Empty node with transform
                #print("Instancing %s on %s" % (scene_node_name, scene_parent_node_name))
                #scene.add_geometry(geometry=D1D2D3.marker().mesh, node_name=scene_node_name, geom_name="Geom %s" % scene_node_name, parent_node_name=scene_parent_node_name, transform=node_transform)
                scene.graph.update(frame_to=scene_node_name, frame_from=scene_parent_node_name, matrix=node_transform, geometry_flags={'visible': True}, extras=metadata_serializable)

                # Child
                ref._recurse_scene_tree(path_prefix=path_prefix + node_name + "/", name_suffix="#ref",
                                        instance_mesh=instance_mesh, instance_marker=instance_marker, include_metadata=include_metadata,
                                        scene=scene, scene_parent_node_name=scene_node_name, usednames=usednames, axis=axis)

            else:
                if type(self) == type(DDDInstance):
                    raise DDDException("Instance should reference another object: %s" % (self, ))


        if not instance_marker and not instance_mesh:
            # Node for export
            instance_marker_cube = False
            if instance_marker_cube:
                ref = self.marker(world_space=False, use_normal_box=True)
                scene.add_geometry(geometry=ref.mesh, node_name=scene_node_name + "_marker", geom_name="Marker %s" % scene_node_name,
                                   parent_node_name=scene_parent_node_name, transform=node_transform, extras=metadata_serializable)
            else:
                scene.graph.update(frame_to=scene_node_name, frame_from=scene_parent_node_name, matrix=node_transform, geometry_flags={'visible': True}, extras=metadata_serializable)

        '''
        # Instance markers for visualization
        if instance_marker and not self.children:
            marker = self.marker(world_space=False)
            marker._recurse_scene_tree(path_prefix=path_prefix + node_name + "/", name_suffix="#marker",
                                    instance_mesh=instance_mesh, instance_marker=instance_marker, include_metadata=include_metadata,
                                    scene=scene, scene_parent_node_name=scene_node_name, usednames=usednames)
        '''

        return scene

    def _recurse_meshes(self, instance_mesh, instance_marker):
        #raise

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

