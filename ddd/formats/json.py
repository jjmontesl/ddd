# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import json
import logging
import math

from shapely import geometry, affinity, ops
from trimesh import transformations

from ddd.core.exception import DDDException
from ddd.core.cli import D1D2D3Bootstrap


# Get instance of logger for this module
logger = logging.getLogger(__name__)

class DDDJSONFormat():
    """
    If 'export_mesh' is set, the mesh data (vertices, triangles, UV if present) will be included in the JSON file.

    Note: it's recommended to use a JSON exploring tool (e.g. https://github.com/antonmedv/fx) to browse generated JSON files.
    """

    @staticmethod
    def export_json(obj, path_prefix="", instance_mesh=True, instance_marker=False, export_mesh=False, indent=None):

        from ddd.ddd import ddd
        data = DDDJSONFormat.export_data(obj, path_prefix, "", instance_mesh, instance_marker, export_mesh=export_mesh)
        encoded = json.dumps(data, indent=indent, default=lambda x: ddd.json_serialize(x))

        return encoded

    @staticmethod
    def export_data(obj, path_prefix="", name_suffix="", instance_mesh=True, instance_marker=False, export_mesh=False):
        """
        TODO: Unify export code paths and recursion, metadata, path name and mesh production.
        """

        node_name = obj.uniquename() + name_suffix

        extra = obj.metadata(path_prefix, name_suffix)
        data = {'_name': node_name,
                '_path': extra['ddd:path'],
                '_str': str(obj),
                '_parent': str(obj.parent),
                '_extra': extra,
                '_material': str(obj.mat)}

        # Include geometry if 'export_mesh' is set
        if export_mesh:
            if obj.mesh:
                data['_mesh'] = {
                    'vertices': obj.mesh.vertices.tolist(),
                    'faces': obj.mesh.faces.reshape((obj.mesh.faces.shape[0] * 3,)).tolist(),  # Flatten triangles (3 vertices per face) to a single list
                }
                if 'uv' in obj.extra:
                    data['_mesh']['uv'] = obj.extra['uv']


        for idx, c in enumerate(obj.children):

            cdata = DDDJSONFormat.export_data(c, path_prefix=path_prefix + node_name + "/", instance_mesh=instance_mesh, instance_marker=instance_marker, export_mesh=export_mesh)  # , name_suffix="#%d" % (idx)
            cpath = cdata['_extra']['ddd:path']
            data[cpath] = cdata


        # FIXME: This code is duplicated from DDDInstance: normalize export / generation (instances, markers...)
        from ddd.nodes.instance import DDDInstance
        if isinstance(obj, DDDInstance):

            data['_transform'] = obj.transform

            if instance_mesh:
                # Export mesh if object instance has a referenced object (it may not, eg lights)
                if obj.ref:
                    ref = obj.ref.copy()

                    if obj.transform.scale != [1, 1, 1]:
                        raise DDDException("Invalid scale for an instance object (%s): %s", obj.transform.scale, obj)

                    #ref = ref.rotate(transformations.euler_from_quaternion(obj.transform.rotation, axes='sxyz'))
                    #ref = ref.translate(self.transform.position)

                    # Export complete references? (too verbose)
                    refdata = DDDJSONFormat.export_data(ref, path_prefix="", name_suffix="#ref", instance_mesh=instance_mesh, instance_marker=instance_marker, export_mesh=export_mesh)  #, instance_mesh=instance_mesh, instance_marker=instance_marker)
                    data['_ref'] = refdata

            if instance_marker and not instance_mesh:
                ref = obj.marker()
                refdata = DDDJSONFormat.export_data(ref, path_prefix="", name_suffix="#marker", instance_mesh=instance_mesh, instance_marker=instance_marker, export_mesh=export_mesh)
                data['_marker'] = refdata

        return data


