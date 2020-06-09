# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020

import sys

import pyproj

from ddd.ddd import ddd
from ddd.geo import terrain
from ddd.osm import osm
from ddd.osm.augment.mapillary import MapillaryClient
from ddd.osm.osm import project_coordinates
from ddd.pipeline.decorators import dddtask


@dddtask(order="50.90.+.+", log=True)
def osm_extras_mapillary(pipeline, osm, root, logger):
    pass


@dddtask()
def osm_extras_mapillary_get(pipeline, osm, root, logger):

    # Add mapillary items
    # TODO: Move to separate task and rule module, separate point generation from image/metadata generation, reuse code, this could be much shorter
    mc = MapillaryClient(client_id=pipeline.data['mapillary_client_id'])
    transformer = pyproj.Transformer.from_proj(osm.osm_proj, osm.ddd_proj)
    transformer2 = pyproj.Transformer.from_proj(osm.ddd_proj, osm.osm_proj)
    query_coords = osm.area_crop2.centroid().geom.coords[0]
    query_coords = project_coordinates(query_coords, transformer2)

    query_limit = 200
    query_radius = 500
    logger.info("Requesting Mapillary images near to (limit=%d, radius=%d)", query_coords, query_limit, query_radius)
    data = mc.images_list(query_coords, limit=query_limit, radius=query_radius)
    for feature in data['features'][:]:

        key = feature['properties']['key']
        pano = feature['properties']['pano']
        camera_angle = feature['properties']['ca']
        geom = feature['geometry']
        coords = geom['coordinates']
        #coords = (float(coords[0]) * 111000.0, float(coords[1]) * 111000.0)

        coords = project_coordinates(coords, transformer)
        logger.debug("Mapillary Image: %s  CameraAngle: %.1f  Pano: %s  Coords: %s" % (key, camera_angle, pano, coords))

        mc.request_image(key)
        image = mc.image_textured(feature).scale([3, 3, 3])
        image_height = 1.5
        image = image.translate([0, 1, 0])
        image = image.rotate([0, 0, (0 + (-camera_angle)) * ddd.DEG_TO_RAD])
        image = image.translate([coords[0], coords[1], image_height])

        cam = ddd.cube(d=0.05).translate([coords[0], coords[1], image_height]).material(ddd.mats.highlight)
        image.append(cam)

        image = terrain.terrain_geotiff_min_elevation_apply(image, osm.ddd_proj)

        osm.other_3d.append(image)

    logger.info("Added %d images from Mapillary.", len(osm.other_3d.children))

    # Optinally save Mapillary data only
    if osm.other_3d.children:
        osm.other_3d.save("/tmp/mapi.glb")


