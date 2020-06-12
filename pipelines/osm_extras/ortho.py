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
from ddd.geo.sources.wms import WMSClient


# TODO: These tasks could be callable repeatedly with different parameters (?) for Orthophotos and OSM images

@dddtask(order="60.80.+.+", log=True)
def osm_extras_orthophoto():
    pass

@dddtask()
def osm_extras_orthophoto_get(pipeline, osm, root, logger):

    # Add mapillary items
    # TODO: Move to separate task and rule module, separate point generation from image/metadata generation, reuse code, this could be much shorter
    url = None  # pipeline.data['wms_ortho_url']
    client = WMSClient("es_ortho", url, width=2048, height=2048)

    transformer1 = pyproj.Transformer.from_proj(osm.ddd_proj, osm.osm_proj)
    transformer2 = pyproj.Transformer.from_proj(osm.osm_proj, osm.webmercator_proj)

    query_bbox_ddd = osm.area_crop2.bounds()
    print(query_bbox_ddd)
    query_bbox_osm = project_coordinates(query_bbox_ddd, transformer1)
    logger.info("Requesting WMS image for: %s", query_bbox_osm)

    query_bbox_webmercator = project_coordinates(query_bbox_osm, transformer2)
    #bbox = [-1007960.7600516, 5131958.1924932, -878017.81196677, 5223682.6264354]
    data = client.request_image(query_bbox_webmercator)
    image = client.image_textured(query_bbox_webmercator)

    # Save to disk (or do by default if not cached)
    bounds = root.bounds()
    area_size = [query_bbox_ddd[2] - query_bbox_ddd[0], query_bbox_ddd[3] - query_bbox_ddd[1]]
    image = image.scale([area_size[0], area_size[1], 1]).translate([query_bbox_ddd[0], query_bbox_ddd[1], bounds[1][2] + 10.0])

    pipeline.data["crop_image"] = image


'''
@dddtask()
def osm_extras_orthophoto_addimage(root, pipeline):
    root.find("/Other3").append(pipeline.data["crop_image"])
'''



@dddtask(order="60.85.+.+", log=True)  # condition=lambda pipeline: pipeline.get('osm_extras_groundimage', True)
def osm_extras_image_as_ground():
    """Replaces areas (terrain, sidewalks...) with a given image."""
    pass

@dddtask(path="/Areas/*", recurse=True)  # condition=lambda pipeline: pipeline.get('osm_extras_groundimage', True)
def osm_extras_image_as_ground_areas(pipeline, osm, obj):
    """Replaces areas (terrain, sidewalks...) with a given image."""
    if obj.mat and obj.mat.extra.get("ddd:export-as-marker", None): return
    if obj.children and not obj.mesh: return

    query_bbox_ddd = osm.area_crop2.bounds()
    area_size = [query_bbox_ddd[2] - query_bbox_ddd[0], query_bbox_ddd[3] - query_bbox_ddd[1]]

    #obj = obj.material(pipeline.data["crop_image"].mat)
    obj.mat = pipeline.data["crop_image"].mat
    obj = ddd.uv.map_cubic(obj, offset=[query_bbox_ddd[0] / area_size[0], query_bbox_ddd[1] / area_size[1]], scale=[1.0 / area_size[0], 1.0 / area_size[1]])
    return obj

@dddtask(path="/Ways/*", recurse=True)  # condition=lambda pipeline: pipeline.get('osm_extras_groundimage', True)
def osm_extras_image_as_ground_ways(pipeline, osm, obj):
    """Replaces ways with a given image."""
    if obj.mat and obj.mat.extra.get("ddd:export-as-marker", None): return
    if obj.children and not obj.mesh: return

    query_bbox_ddd = osm.area_crop2.bounds()
    area_size = [query_bbox_ddd[2] - query_bbox_ddd[0], query_bbox_ddd[3] - query_bbox_ddd[1]]

    #obj = obj.material(pipeline.data["crop_image"].mat)
    obj.mat = pipeline.data["crop_image"].mat
    obj = ddd.uv.map_cubic(obj, offset=[query_bbox_ddd[0] / area_size[0], query_bbox_ddd[1] / area_size[1]], scale=[1.0 / area_size[0], 1.0 / area_size[1]])
    return obj

