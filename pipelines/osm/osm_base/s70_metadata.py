# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020


from ddd.ddd import ddd, DDDObject
from ddd.pipeline.decorators import dddtask
from ddd.geo import terrain
from ddd.core.exception import DDDException
import json
import datetime
import time
from PIL.Image import Image


'''
@dddtask(order="70.01.+", cache=True)
def osm_metadata_condition(pipeline, osm, root, logger):
    """
    Caches current state to allow for faster reruns.
    """
    #sys.setrecursionlimit(15000)  # This cache operation was failing due to RecursionError during pickle dump
    return pipeline.data['filenamebase'] + ".s60.cache"
'''


@dddtask(order="70.10.+")
def osm_metadata_generate_scene_metadata(root, pipeline, osm, logger):
    """
    Write accumulated metadata to a descriptor file.
    """

    # TODO: Unify metadata

    # Include heightmap range if used

    data = {

        'ddd:pipeline:current_date': datetime.datetime.now(),
        'generation_start_date': None,

        'attribution': "ODbL © OpenStreetMap Contributors + EEA",
        'generator': "DDD123 - https://github.com/jjmontesl/ddd",

        #'_pipeline':   # For debugging purposes
    }

    data.update(pipeline.data)
    data['metadata'] = None

    # Add metadata
    data.update(pipeline.data.get('metadata', {}))

    data = {k: v for k, v in data.items() if not k[0] == '_' and not isinstance(v, DDDObject)}


    filepath = pipeline.data['filenamebase'] + ".desc.json"
    logger.info("Writing JSON descriptor to: %s", filepath)

    # Avoid writing DDDObjects or entire Pillow images to descriptor
    def metadata_serialize_default(data):
        if (isinstance(data, DDDObject) or isinstance(data, Image)):
            return data.__class__.__name__
        else:
            return str(data)

    with open(filepath, "w") as f:
        #json_data = json.dumps(data, default=str)
        json_data = json.dumps(data, default=metadata_serialize_default, indent=4, sort_keys=True)
        f.write(json_data)


