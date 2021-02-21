# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020

import sys

import pyproj

from ddd.ddd import ddd
from ddd.geo import terrain
from ddd.osm import osm
from ddd.osm.osm import project_coordinates
from ddd.pipeline.decorators import dddtask

"""
"""


# Materials used by this pipeline
ddd.mats.railway = ddd.material(name="RoadRailway", color="#47443e")
ddd.mats.roadline = ddd.material(name="Roadline", color='#e8e8e8',
                             texture_path=ddd.DATA_DIR + "/materials/road_signs/RoadLines_alb.png",
                             texture_normal_path=ddd.DATA_DIR + "/materials/road_signs/RoadLines_normal.jpg",
                             alpha_cutoff=0.05,
                             extra={'ddd:collider': False, 'ddd:shadows': False, 'uv:scale': 0.05})
ddd.mats.traffic_signs = ddd.material(name="TrafficSigns", color="#ffffff", #color="#e01010",
                                  texture_path=ddd.DATA_DIR  + "/materials/traffic_signs/traffic_signs_es_0.png",
                                  atlas_path=ddd.DATA_DIR  + "/materials/traffic_signs/traffic_signs_es_0.plist")


@dddtask(order="10")
def osm_init(pipeline, root):
    """
    Pipeline initialization (variables, etc).
    """
    pass


@dddtask(order="50.999999", log=True)
def osm_finish_rest_before_3d(pipeline, osm, root, logger):

    # Generate items for point features
    ##osm.items.generate_items_1d()

    pass

