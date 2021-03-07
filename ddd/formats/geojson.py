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
import geojson


# Get instance of logger for this module
logger = logging.getLogger(__name__)

class DDDGeoJSONFormat():

    @staticmethod
    def export_geojson(obj, path_prefix="", instance_mesh=True, instance_marker=False):

        features = DDDGeoJSONFormat.export_features(obj, path_prefix, "", instance_mesh, instance_marker)

        feature_collection = geojson.FeatureCollection(features)

        #encoded = json.dumps(data, indent=2, default=lambda x: D1D2D3.json_serialize(x))
        from ddd.ddd import D1D2D3
        encoded = geojson.dumps(feature_collection, default=lambda x: D1D2D3.json_serialize(x))  #, sort_keys=True)
        print(encoded)

        return encoded

    @staticmethod
    def export_features(obj, path_prefix="", name_suffix="", instance_mesh=True, instance_marker=False):
        """
        TODO: Unify export code paths and recursion, metadata, path name and mesh production.
        """

        features = []
        node_name = obj.uniquename() + name_suffix

        extra = obj.metadata(path_prefix, name_suffix)
        data = {'_name': node_name,
                '_path': extra['ddd:path'],
                '_str': str(obj),
                '_extra': extra,
                '_material': str(obj.mat)}

        if obj.geom:
            if obj.geom.type == 'Polygon':
                geometry = geojson.Polygon([list(obj.geom.exterior.coords)])
                feature = geojson.Feature(geometry=geometry, name=node_name)
                feature.properties = data
                features.append(feature)
            else:
                logger.warning("Invalid node type or geometry to be exported to GeoJSON: %s", obj)

        for idx, c in enumerate(obj.children):

            cf = DDDGeoJSONFormat.export_features(c, path_prefix=path_prefix + node_name + "/", name_suffix="#%d" % (idx), instance_mesh=instance_mesh, instance_marker=instance_marker)
            features.extend(cf)

        '''
        # FIXME: This code is duplicated from DDDInstance: normalize export / generation
        from ddd.ddd import DDDInstance
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
                    refdata = DDDGeoJSONFormat.export_data(ref, path_prefix="", name_suffix="#ref", instance_mesh=instance_mesh, instance_marker=instance_marker)  #, instance_mesh=instance_mesh, instance_marker=instance_marker)
                    data['_ref'] = refdata

            if instance_marker:
                ref = obj.marker()
                refdata = DDDGeoJSONFormat.export_data(ref, path_prefix="", name_suffix="#marker", instance_mesh=instance_mesh, instance_marker=instance_marker)
                data['_marker'] = refdata

        '''

        return features
