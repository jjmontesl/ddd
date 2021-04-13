# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020


from ddd.ddd import ddd
from ddd.pipeline.decorators import dddtask
from ddd.geo import terrain
from ddd.core.exception import DDDException
import json
import datetime
import time


@dddtask(order="70.01.+", cache=True)
def osm_structured_cache(pipeline, osm, root, logger):
    """
    Caches current state to allow for faster reruns.
    """
    #sys.setrecursionlimit(15000)  # This cache operation was failing due to RecursionError during pickle dump
    return pipeline.data['filenamebase'] + ".s60.cache"



@dddtask(order="70.10.+")
def osm_model_pre_propagate_base_height_areas(root, pipeline, osm, logger):
    """
    Write accumulated metadata to a descriptor file.
    """

    # Include heightmap range if used

    data = {

        'ddd:pipeline:current_date': datetime.datetime.now(),
        'generation_start_date': None,

        'attribution': "ODbL © OpenStreetMap Contributors + EEA",
        'generator': "DDD123 - https://github.com/jjmontesl/ddd",

        '_pipeline': pipeline.data  # For debugging purposes
    }

    # Add metadata
    data.update(pipeline.data.get('metadata', {}))


    filepath = pipeline.data['filenamebase'] + ".desc.json"
    logger.info("Writing JSON descriptor to: %s", filepath)

    with open(filepath, "w") as f:
        #json_data = json.dumps(data, default=str)
        json_data = json.dumps(data, default=str, indent=4, sort_keys=True)
        f.write(json_data)


