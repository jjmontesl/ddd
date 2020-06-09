# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020

import sys

import pyproj

from ddd.ddd import ddd
from ddd.geo import terrain
from ddd.osm import osm
from ddd.osm.augment.wms import WMSClient
from ddd.osm.osm import project_coordinates
from ddd.pipeline.decorators import dddtask


# TODO: These tasks could be callable repeatedly with different parameters (?) for Orthophotos and OSM images

@dddtask(order="50.90.+.+", log=True)
def osm_extras_orthophoto():
    pass

@dddtask()
def osm_extras_orthophoto_get(pipeline, osm, root, logger):

    # Add mapillary items
    # TODO: Move to separate task and rule module, separate point generation from image/metadata generation, reuse code, this could be much shorter
    url = pipeline.data['wms_ortho_url']
    client = WMSClient(url)

    transformer = pyproj.Transformer.from_proj(osm.osm_proj, osm.ddd_proj)
    transformer2 = pyproj.Transformer.from_proj(osm.ddd_proj, osm.osm_proj)

    #query_coords = osm.area_crop2.centroid().geom.coords[0]
    #query_coords = project_coordinates(query_coords, transformer2)

    logger.info("Requesting WMS image for: %s", osm.area_crop2.geom.coords)

    client.request()
    # Save to disk (or do by default if not cached)


@dddtask()
def osm_extras_orthophoto_addimage():

    coords = project_coordinates(coords, transformer)
    logger.debug("Mapillary Image: %s  CameraAngle: %.1f  Pano: %s  Coords: %s" % (key, camera_angle, pano, coords))

    mc.request_image(key)
    # Reuse the image_textured
    image = mc.image_textured(feature).scale([3, 3, 3])
    image_height = 1.5
    image = image.translate([0, 1, 0])
    image = image.rotate([0, 0, (0 + (-camera_angle)) * ddd.DEG_TO_RAD])
    image = image.translate([coords[0], coords[1], image_height])

    cam = ddd.cube(d=0.05).translate([coords[0], coords[1], image_height]).material(ddd.mats.highlight)
    image.append(cam)

    image = terrain.terrain_geotiff_min_elevation_apply(image, osm.ddd_proj)

    osm.other_3d.append(image)


@dddtask(order="60.90.+.+", onlyif=lambda pipeline: pipeline.get('osm_extras_groundimage', False), log=True)
def osm_extras_image_as_ground():
    """Replaces areas (terrain, sidewalks...) with a given image."""
    pass

