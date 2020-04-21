# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import json
import logging
import math

from shapely import geometry, affinity, ops
from trimesh import transformations

from ddd.core.exception import DDDException


# Get instance of logger for this module
logger = logging.getLogger(__name__)

class DDDJSON():

    @staticmethod
    def export_json(obj, path_prefix=""):

        from ddd.ddd import D1D2D3
        data = DDDJSON.export_data(obj, path_prefix)
        encoded = json.dumps(data, indent=2, default=lambda x: D1D2D3.json_serialize(x))

        return encoded

    @staticmethod
    def export_data(obj, path_prefix=""):
        """
        TODO: Unify export code paths and recursion, metadata, path name and mesh production.
        """

        auto_name = "node_%s" % (id(obj))
        node_name = ("%s_%s" % (obj.name, id(obj))) if obj.name else auto_name

        extra = obj.metadata(path_prefix)
        data = {'_name': node_name,
                '_path': extra['path'],
                '_str': str(obj),
                '_extra': extra,
                '_material': str(obj.mat)}

        for c in obj.children:
            cdata = DDDJSON.export_data(c, path_prefix + node_name + "/")
            cpath = cdata['_extra']['path']
            data[cpath] = cdata

        # FIXME: This code is duplicated from DDDInstance: normalize export / generation
        from ddd.ddd import DDDInstance
        if isinstance(obj, DDDInstance) and obj.ref:

            instance_mesh = True
            instance_marker = False

            data['_transform'] = obj.transform

            ref = obj.ref.copy()
            if instance_mesh:
                if obj.transform.scale != [1, 1, 1]:
                    raise DDDException("Invalid scale for an instance object (%s): %s", obj.transform.scale, obj)
                #ref = ref.rotate(transformations.euler_from_quaternion(obj.transform.rotation, axes='sxyz'))
                #ref = ref.translate(self.transform.position)
                refdata = DDDJSON.export_data(ref, path_prefix=path_prefix + node_name + "/")  #, instance_mesh=instance_mesh, instance_marker=instance_marker)
                data['_ref'] = refdata

            '''
            if instance_marker:
                ref = D1D2D3.marker(self.name)
                ref = ref.scale(self.transform.scale)
                ref = ref.rotate(transformations.euler_from_quaternion(self.transform.rotation, axes='sxyz'))
                ref = ref.translate(self.transform.position)
                ref.extra.update(self.ref.extra)
                ref.extra.update(self.extra)
                refscene = ref._recurse_scene(path_prefix=path_prefix + node_name + "/", instance_mesh=instance_mesh, instance_marker=instance_marker)
                scene = append_scenes([scene] + [refscene])
            '''

        return data


