# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020


import numpy as np

from ddd.ddd import ddd
from ddd.pipeline.decorators import dddtask
from ddd.geo import terrain
from ddd.core.exception import DDDException
import datetime
from ddd.util.common import parse_bool


"""
The "model post optimize" stage of the build process apply some optimizations,
such as mesh combination or instance grouping, before writing the output
model to file.

These tasks should be optional (currently, this steps can be removed to obtain
individual objects as without object / instance combining.
"""




@dddtask(order="65.30.40")
def osm_model_metadata_freeze_before_combine(pipeline, root):
    """
    This task walks the scene tree and eagerly resolves path information.
    This is done in order to preserve scene hierarchy information before it is destroyed
    by collapsing meshes into unique objects.
    """
    ddd.meshops.freeze_metadata(root)


@dddtask()  # path="/Items3/*", select='[ddd:material="Roadmarks"]')
def osm_model_combine_ways_road_markings(osm, root, pipeline):
    """
    Combine road markings in a single mesh, as they use the same atlas material.
    (Note that road marks are currently instanced via catalog, so using this requires considering that).
    """
    roadmarks = root.find("/Items3").select(selector='["ddd:material"="Roadmarks"]')
    roadmarks = roadmarks.combine()
    # Remove roadmark elements
    root.find("/Items3").select('[ddd:material="Roadmarks"]', apply_func=lambda o: False)
    root.find("/Roadlines3/").append(roadmarks)


@dddtask(order="65.40", condition=True)
def osm_model_combine_materials_condition(pipeline):
    """
    Combine meshes by material condition (default is True).
    """
    return parse_bool(pipeline.data.get('ddd:osm:model:combine_materials', True))

@dddtask(order="65.40.+")  # path="/Items3/*", select='[ddd:material="Roadmarks"]')
def osm_model_combine_materials(osm, root, pipeline):
    """
    Combine meshes with the same material in a single mesh.
    """
    ddd.meshops.combine_group(root.find("/Buildings"), key_func=lambda o: o.mat.name if o.mat else None)
    ddd.meshops.combine_group(root.find("/Areas"), key_func=lambda o: o.mat.name if o.mat else None)
    ddd.meshops.combine_group(root.find("/Ways"), key_func=lambda o: o.mat.name if o.mat else None)

    ddd.meshops.combine_empty(root.find("/Buildings"))
    ddd.meshops.combine_empty(root.find("/Areas"))
    ddd.meshops.combine_empty(root.find("/Ways"))


@dddtask(order="65.45")  # [!"intersection"]
def osm_models_instances_buffers_buildings(pipeline, osm, root, logger):
    """
    Generates geometry instancing buffers for repeated DDDInstance objects in buildings.
    """
    keys = ('building-window',)

    for key in keys:
        instances = root.select(path="/Buildings/*", selector='["ddd:instance:key" = "%s"]' % key)

        if len(instances.children) > 0:
            logger.info("Replacing %d building instances (%s) with a buffer.", len(instances.children), key)
            buffer_matrices = np.zeros([len(instances.children) * 16, ])

            for idx, instance in enumerate(instances.children):
                buffer_matrices[idx * 16:idx * 16 + 16] = instance.transform.to_matrix().transpose().flatten()

            instance_buffer = instances.children[0].copy()
            instance_buffer.set('ddd:instance:buffer:matrices', list(buffer_matrices))

            root.select_remove(path="/Buildings/*", selector='["ddd:instance:key" = "%s"]' % key)
            root.find("/Buildings").append(instance_buffer)

@dddtask()  # [!"intersection"]
def osm_models_instances_buffers_items(pipeline, osm, root, logger):
    """
    Generates geometry instancing buffers for repeated scenery DDDInstance objects.
    """
    keys = ('grassblade', 'grassblade-dry')

    for key in keys:
        instances = root.select(path="/Items3/*", selector='["ddd:instance:key" = "%s"]' % key)

        if len(instances.children) > 0:
            logger.info("Replacing %d items instances (%s) with a buffer.", len(instances.children), key)
            buffer_matrices = np.zeros([len(instances.children) * 16, ])

            for idx, instance in enumerate(instances.children):
                buffer_matrices[idx * 16:idx * 16 + 16] = instance.transform.to_matrix().transpose().flatten()

            instance_buffer = instances.children[0].copy()
            instance_buffer.set('ddd:instance:buffer:matrices', list(buffer_matrices))

            root.select_remove(path="/Items3/*", selector='["ddd:instance:key" = "%s"]' % key)
            root.find("/Items3").append(instance_buffer)


