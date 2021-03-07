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

pipeline = DDDPipeline(['pipelines.osm_base.s10_init.py',
                        'pipelines.osm_common.s10_locale_config.py',

                        'pipelines.osm_base.s20_osm_features.py',
                        'pipelines.osm_base.s20_osm_features_export_2d.py',
                        'pipelines.osm_base.s30_groups.py',
                        'pipelines.osm_base.s30_groups_ways.py',
                        'pipelines.osm_base.s30_groups_buildings.py',
                        'pipelines.osm_base.s30_groups_areas.py',
                        'pipelines.osm_base.s30_groups_items_nodes.py',
                        'pipelines.osm_base.s30_groups_items_ways.py',
                        'pipelines.osm_base.s30_groups_items_areas.py',
                        'pipelines.osm_base.s30_groups_export_2d.py',

                        'pipelines.osm_base.s40_structured.py',
                        'pipelines.osm_base.s40_structured_export_2d.py',

                        'pipelines.osm_common.s45_pitch.py',

                        'pipelines.osm_base.s50_positioning.py',
                        'pipelines.osm_base.s50_crop.py',
                        'pipelines.osm_base.s50_90_export_2d.py',

                        'pipelines.osm_base.s60_model.py',
                        'pipelines.osm_base.s60_model_export_3d.py',

                        'pipelines.osm_augment.s50_ways.py',
                        'pipelines.osm_augment.s55_plants.py',

                        'pipelines.osm_default_2d.s30_icons.py',

                        #'pipelines.osm_extras.mapillary.py',
                        #'pipelines.osm_extras.ortho.py',

                        ], name="OSM Build Pipeline")


pipeline.data['ddd:osm:output:json'] = True  # associate to debug config if not set
pipeline.data['ddd:osm:output:intermediate'] = True  # associate to debug config if not set
#ddd:osm:output:structured_2d

pipeline.data['ddd:osm:water'] = False
pipeline.data['ddd:osm:underwater'] = False

pipeline.data['ddd:osm:augment:plants'] = False
pipeline.data['ddd:osm:augment:kerbs'] = False
pipeline.data['ddd:osm:augment:way_props'] = False

pipeline.data['ddd:osm:alignment:items'] = False

