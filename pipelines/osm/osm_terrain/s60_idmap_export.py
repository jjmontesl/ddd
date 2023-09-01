# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020

import sys

import pyproj
import numpy as np

from ddd.ddd import ddd
from ddd.geo import terrain
from ddd.osm import osm
from ddd.osm.osm import project_coordinates
from ddd.pipeline.decorators import dddtask
from ddd.geo.elevation import ElevationModel
from PIL import Image
import math
from shapely.strtree import STRtree
import hashlib


# This file is currently unused. Refer to splatmap_export.

'''

# TODO: Doing this on stage 59 as buildings are deleted (keep 2D and 3D versions in the tree for late usage, also for terrain_export)

@dddtask(order="59.89.+.10", condition=True)
def osm_terrain_export_idmap_condition(pipeline):
    return bool(pipeline.data.get('ddd:terrain:idmap', False))


@dddtask(order="*.10.+")
def osm_terrain_export_idmap(root, pipeline, osm, logger):

    ddd_bounds = osm.area_crop.bounds
    wgs84_min = terrain.transform_ddd_to_geo(osm.ddd_proj, ddd_bounds[:2])
    wgs84_max = terrain.transform_ddd_to_geo(osm.ddd_proj, ddd_bounds[2:])
    wgs84_bounds = wgs84_min + wgs84_max

    idmap_size = 128
    logger.info("Generating idmap for area: ddd_bounds=%s, wgs84_bounds=%s, size=%s", ddd_bounds, wgs84_bounds, idmap_size)

    idmap = root.copy()
    idmap = idmap.remove(idmap.find("/Features"))  # !Altering
    idmap.set('svg:stroke-width', 0.1, children=True)
    idmap.set('svg:fill-opacity', 0.7, children=True)

    #root.find("/Areas").replace(root.find("/Areas").material(ddd.mats.park).set('svg:fill-opacity', 0.6, True))
    #root.find("/Ways").replace(root.find("/Ways").buffer(1.0).material(ddd.mats.asphalt).set('svg:fill-opacity', 0.8, True))
    #root.find("/Buildings").replace(root.find("/Buildings").material(ddd.mats.stone).set('svg:fill-opacity', 0.7, True))
    #root.find("/Items").replace(root.find("/Items").buffer(1.0).material(ddd.mats.highlight))

    #path = pipeline.data['filenamebase'] + ".idmap.svg"
    #idmap.save("/tmp/osm-idmap.svg")

    tile = ddd.group2([
        #ddd.shape(osm.area_crop).material(ddd.material(color='#ffffff')),  # White background (?)
        #self.ground_2d,
        root.select(path="/Water", recurse=False),
        root.select(path="/Areas", recurse=False),
        root.select(path="/Ways", recurse=False),  #, select="")  self.ways_2d['-1a'], self.ways_2d['0'], self.ways_2d['0a'], self.ways_2d['1'],
        root.select(path="/Buildings", recurse=False),
        #root.select(path="/Roadlines2", recurse=False),
        #root.select(path="/ItemsAreas", recurse=False),  #self.items_2d,
        #root.select(path="/ItemsWays", recurse=False),  #self.items_2d,
        #root.select(path="/ItemsNodes", recurse=False).buffer(0.5).material(ddd.mats.red),

    ]).flatten().select(func=lambda o: o.extra.get('ddd:area:type') != 'underwater')

    '''
    # Save a cropped tileable idmap image of the scene.
    tile = tile.intersection(ddd.shape(osm.area_crop))
    tile = tile.clean()
    tile.set('svg:stroke-width', 0, children=True)  # 0.01,

    path = pipeline.data['filenamebase'] + ".idmap.png"
    tile.save("/tmp/osm-idmap.png")
    #tile.save(path)
    '''

    SPLAT_NONE =        0x00
    SPLAT_UNKNOWN =     0x08

    # Spatial index

    rtree = STRtree(tile.geom_recursive())

    # Interpolate over DDD coordinates and resolve height
    splat_keys = {}
    splat_matrix = np.zeros([idmap_size, idmap_size])
    for xi, x in enumerate(np.linspace(ddd_bounds[0], ddd_bounds[2], idmap_size, endpoint=True)):
        for yi, y in enumerate(reversed(np.linspace(ddd_bounds[1], ddd_bounds[3], idmap_size, endpoint=True))):

            # Temporarily enhance with areas (ultimately, this is needed for much more, maybe comming from elevation-plus engine)
            # At least use spatial partitioning to find where the point lies
            probe_radius = 0.5
            dddp = ddd.point([x, y]).buffer(probe_radius)

            cand_items = rtree.query(dddp.geom)
            items = [c for c in cand_items if c.intersects(dddp.geom)]

            if not items:
                logger.warn("No item found while generating idmap for point: %s" % (dddp.geom.coords[0], ))
                splat_matrix[yi, xi] = SPLAT_NONE
                continue

            items = sorted(items, key=lambda o: o.area)
            item = items[0]._ddd_obj  # TODO: This is unsafe, generate a dictionary of id(geom) -> object (see https://shapely.readthedocs.io/en/stable/manual.html#strtree.STRtree.strtree.query), and see DDDObject2.geom_recursive

            item_splat_key = SPLAT_UNKNOWN

            # Temporarily using material as identifier
            item_material = item.mat.name if item.mat else item.get('osm:element', None)
            if item_material:
                item_splat_key = hashlib.sha256(item_material.encode()).digest()[-1]
                splat_keys[item_splat_key] = item_material

            splat_matrix[yi, xi] = item_splat_key

    im = Image.fromarray(np.uint8(splat_matrix), "L")
    im.save("/tmp/osm-idmap.png", "PNG")
    #im.save(pipeline.data['filenamebase'] + ".hillshade.png", "PNG")

    logger.info("IDMap keys:")
    for k in sorted(splat_keys.keys()):
        logger.info("  %x %s" % (k, splat_keys[k]))
'''
