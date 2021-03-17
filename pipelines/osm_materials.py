# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020

import sys

from ddd.ddd import ddd, DDDMaterial
from ddd.pipeline.decorators import dddtask
from ddd.pipeline.pipeline import DDDPipeline

"""
"""

pipeline = DDDPipeline(['pipelines.osm_base.s10_init.py',
                        ], name="OSM Build Pipeline")

# TODO: Move to init?
#osmbuilder = osm.OSMBuilder(area_crop=area_crop, area_filter=area_filter, osm_proj=osm_proj, ddd_proj=ddd_proj)
pipeline.data['osm'] = None

@dddtask()
def materials_list(root, osm):

    mats = ddd.group3(name="Materials")
    root.append(mats)

    for key in dir(ddd.mats):
        mat = getattr(ddd.mats, key)
        if isinstance(mat, DDDMaterial):
            marker = ddd.marker(name=mat.name)
            marker = marker.material(mat)
            mats.append(marker)

@dddtask()
def materials_show(root):
    mats = root.find("/Materials")
    mats = ddd.align.grid(mats, space=2.0)
    mats.show()

@dddtask()
def materials_save(root):
    mats = root.find("/Materials")
    mats = ddd.align.grid(mats, space=2.0)  # Not really needed for export
    mats.save('catalog_materials.glb')


pipeline.run()


