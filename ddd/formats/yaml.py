# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import json
import logging
import math
import yaml

from shapely import geometry, affinity, ops
from trimesh import transformations
from PIL import Image

from ddd.core.exception import DDDException
from ddd.core.cli import D1D2D3Bootstrap
from ddd.ddd import ddd


# Get instance of logger for this module
logger = logging.getLogger(__name__)

class DDDYAMLFormat():

    @staticmethod
    def export_yaml(obj, path_prefix="", instance_mesh=True, instance_marker=False):

        from ddd.ddd import D1D2D3
        data = DDDYAMLFormat.export_data(obj, path_prefix, "", instance_mesh, instance_marker)

        encoded = yaml.dump(data, indent=2, sort_keys=True)

        return encoded

    @staticmethod
    def export_data(obj, path_prefix="", name_suffix="", instance_mesh=True, instance_marker=False):
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
                '_transform': repr(obj.transform),
                '_material': str(obj.mat)}

        for idx, c in enumerate(obj.children):

            cdata = DDDYAMLFormat.export_data(c, path_prefix=path_prefix + node_name + "/", instance_mesh=instance_mesh, instance_marker=instance_marker)  # , name_suffix="#%d" % (idx)
            cpath = cdata['_extra']['ddd:path']
            data[cpath] = cdata

        # FIXME: this serializes objects and dicts incorrectly, we need to deep-process dictionaries to remove some references while keeping structure
        for k, v in extra.items():
            if not isinstance(v, (str, float, int, bool)):
                dv = ddd.json_serialize(v)
                extra[k] = dv


        # FIXME: This code is duplicated from DDDInstance: normalize export / generation
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
                    refdata = DDDYAMLFormat.export_data(ref, path_prefix="", name_suffix="#ref", instance_mesh=instance_mesh, instance_marker=instance_marker)  #, instance_mesh=instance_mesh, instance_marker=instance_marker)
                    data['_ref'] = refdata

            if instance_marker:
                ref = obj.marker()
                refdata = DDDYAMLFormat.export_data(ref, path_prefix="", name_suffix="#marker", instance_mesh=instance_mesh, instance_marker=instance_marker)
                data['_marker'] = refdata

        return data


