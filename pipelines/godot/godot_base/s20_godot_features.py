# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020

import sys

from ddd.ddd import ddd
import godot_parser

from ddd.pipeline.decorators import dddtask
import random
import math
from ddd.core.exception import DDDException

def godot_vector2array(data):
    coords = [(x, y) for x, y in zip(data[0::2], data[1::2])]
    return coords

def godot_vector2(data):
    coords = (data[0], data[1])
    return coords

@dddtask(order="20.1", log=True)
def features_load(pipeline, root, logger):
    #filename = 'Trial1.tscn'
    #filename = 'TestProcedural.tscn'
    filename = '/tmp/_ddd-godot-tmp.tscn'
    logger.info("Loading Godot file: %s" % filename)
    scene = godot_parser.load(filename)

    features = ddd.group2(name="Features")

    def process_node_meta(feat, node):
        meta = node['__meta__'] if '__meta__' in node.properties else {}
        if '_editor_description_' in meta:
            for l in meta['_editor_description_'].split("\n"):
                try:
                    l = l.strip()
                    if not l or l.startswith('#'): continue
                    k, v = l.split("=", 2)
                    feat.extra[k] = v
                except Exception as e:
                    raise DDDException("Cannot read meta key=value (%s) from node %s: %s" % (l, node, e))

    def process_node(prefix, node):
        node_path = prefix + "/" + node.name

        if (node.type == "Polygon2D"):
            #print(node['polygon'])
            #print(node['polygon'].__class__.__name__)
            coords = godot_vector2array(node['polygon'].args)
            position = godot_vector2(node['position'].args) if ('position' in node.properties) else [0, 0]
            #scale = godot_vector2(node['scale'].args) if ('scale' in node.properties) else [1, 1]
            rotation = node['rotation'] if ('rotation' in node.properties) else 0.0
            visible = node['visible'] if ('visible' in node.properties) else True

            feat = ddd.polygon(coords, name=node.name)
            feat = feat.rotate(rotation)
            feat = feat.translate(position)  # Transform should be maintained
            #feat = feat.scale([0.6, 0.6])  #T TODO: support scale somehow (ideally through godot hierarchy, but at least in metadata)

            feat.extra['godot:node:path'] = node_path
            feat.extra['godot:visible'] = visible
            #print(node_path)

            process_node_meta(feat, node)
            features.append(feat)

        elif (node.type == "Line2D"):
            coords = godot_vector2array(node['points'].args)
            position = godot_vector2(node['position'].args) if ('position' in node.properties) else [0, 0]
            visible = node['visible'] if ('visible' in node.properties) else True

            feat = ddd.line(coords, name=node.name)
            feat = feat.translate(position)

            feat.extra['godot:node:path'] = node_path
            feat.extra['godot:visible'] = visible

            process_node_meta(feat, node)
            features.append(feat)


        for c in node.get_children():
            process_node(prefix + "/" + node.name, c)

    with scene.use_tree() as tree:
        rootnode = tree.get_node(".")
        process_node(".", rootnode)

    root.append(features)


@dddtask(log=True, path="/Features/*")
def osm_features_filter(pipeline, root, obj):
    filter_path = './Main/Scene/Trial/ZoneProc/DDDProc/Data'
    if not obj.extra['godot:node:path'].startswith(filter_path):
        return False
    if not obj.extra['godot:visible']:
        return False


@dddtask(order="30.50.90.+", path="/Areas/*", select='[! "ddd:area:type"]')
def osm_groups_areas_remove_untagged(root, obj, logger):
    """Remove ignored areas."""
    return False


@dddtask(log=True)
def osm_features_preprocess(pipeline):
    #pipeline.data['osm'].preprocess_features()
    #pipeline.root.append(osm.features_2d)
    pass


'''
@dddtask(log=True)
def osm_features_test_random(pipeline, root):

    features = ddd.group2(name="Features")

    extents = [3000, 3000]
    sizerange = [400, 1500]
    for i in range(20):
        #feat = ddd.polygon(coords, name=node.name)
        center = [random.uniform(-extents[0], extents[0]), random.uniform(-extents[1], extents[1])]
        size = [random.uniform(sizerange[0], sizerange[1]), random.uniform(sizerange[0], sizerange[1])]

        feat = ddd.rect([center[0] - size[0], center[1] - size[1], center[0] + size[0], center[1] + size[1]], name="Random")
        feat.extra['ddd:polygon:type'] = "hollow"
        feat = feat.rotate(random.uniform(0, math.pi * 2))

        features.append(feat)

    root.find("/Features").replace(features)
'''


'''
@dddtask(path="/Features/*", log=True)  # and o.geom.type in ('Point', 'Polygon', 'MultiPolygon') .. and o.geom.type == 'Polygon' |  ... path="/Features", select=r'["geom:type"="Polygon"]'
def osm_features_crop_extended_area(pipeline, osm, root, obj):
    """Crops to extended area size to avoid working with huge areas."""

    # TODO: Crop centroids of buildings and lines and entire areas...

    #pipeline.data['osm'].preprocess_features()
    #osm.preprocess_features()
    obj.extra['osm:original'] = obj.copy()
    obj = obj.intersection(osm.area_filter2)
    return obj

@dddtask(order="20.95.+", cache=True)
def osm_features_cache(pipeline, osm, root, logger):
    """
    Caches current state to allow for faster reruns.
    """
    return pipeline.data['filenamebase'] + ".s20.cache"
'''

