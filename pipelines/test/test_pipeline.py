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

pipeline = DDDPipeline(['pipelines.test.test_base.s10_init.py',

                        'pipelines.test.test_base.s20_features_generate.py',
                        'pipelines.test.test_base.s20_features_export_2d.py',

                        #'pipelines.godot.godot_base.s40_rooms.py',
                        #'pipelines.godot.godot_base.s60_godot_export_scene.py',

                        ], name="Test Build Pipeline")



pipeline.data['ddd:test'] = True

pipeline.data['ddd:test:output:json'] = True  # associate to debug config if not set
pipeline.data['ddd:test:output:intermediate'] = True  # associate to debug config if not set

pipeline.run()

'''

pipeline.data['ddd:osm:water'] = False
pipeline.data['ddd:osm:underwater'] = False

pipeline.data['ddd:osm:augment:plants'] = False
pipeline.data['ddd:osm:augment:kerbs'] = False
pipeline.data['ddd:osm:augment:way_props'] = False

pipeline.data['ddd:osm:alignment:items'] = False
'''
