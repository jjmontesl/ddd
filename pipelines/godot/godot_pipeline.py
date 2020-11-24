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
from ddd.pipeline.pipeline import DDDPipeline

"""
Run as:

    (env) jjmontes@j2ws:~/git/ddd/private (master)$ ddd pipelines.godot.godot_pipeline

    cp ~/git/NinjaCow/scenes/test/TestProcedural.tscn .
    ddd pipelines.godot.godot_pipeline --renderer=pyrender
    cp /tmp/ddd-godot.tscn ~/git/NinjaCow/scenes/test/

"""

pipeline = DDDPipeline(['pipelines.godot.godot_base.s10_init.py',
                        #'pipelines.godot_common.s10_locale_config.py',

                        'pipelines.godot.godot_base.s20_godot_features.py',
                        'pipelines.godot.godot_base.s20_godot_features_export_2d.py',

                        'pipelines.godot.godot_base.s40_rooms.py',
                        #'pipelines.godot.godot_base.s40_structured_export_2d.py',

                        'pipelines.godot.godot_base.s60_godot_export_scene.py',

                        ], name="Godot Polygon2D Build Pipeline")


'''
                        'pipelines.osm_base.s30_groups_ways.py',
                        'pipelines.osm_base.s30_groups_buildings.py',
                        'pipelines.osm_base.s30_groups_areas.py',
                        'pipelines.osm_base.s30_groups_items_nodes.py',
                        'pipelines.osm_base.s30_groups_items_ways.py',
                        'pipelines.osm_base.s30_groups_items_areas.py',
                        'pipelines.osm_base.s30_groups_export_2d.py',

                        'pipelines.osm_base.s40_structured.py',

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
'''


pipeline.data['ddd:godot'] = True

pipeline.data['ddd:godot:output:json'] = True  # associate to debug config if not set
pipeline.data['ddd:godot:output:itermediate'] = True  # associate to debug config if not set

pipeline.run()

'''

pipeline.data['ddd:osm:water'] = False
pipeline.data['ddd:osm:underwater'] = False

pipeline.data['ddd:osm:augment:plants'] = False
pipeline.data['ddd:osm:augment:kerbs'] = False
pipeline.data['ddd:osm:augment:way_props'] = False

pipeline.data['ddd:osm:alignment:items'] = False
'''
