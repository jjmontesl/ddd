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

"""
"""


@dddtask(order="10")
def osm_init(pipeline, root):
    """
    Run at initial stage, load data.
    """
    #pipeline.run()
    pass




@dddtask(order="90", log=True)
def osm_finish_rest(pipeline, osm, root, logger):

    #self.features_2d.filter(lambda o: o.extra.get('osm:building:part', None) is not None).dump()
    # TODO: Shall already be done earlier
    osm.features_2d = root.find("/Features")
    osm.items_1d = root.find("/Items")
    #osm.ways_1d = root.find("/Ways")
    #osm.buildings_2d = root.find("/Buildings")

    # Generate items for point features
    ##osm.items.generate_items_1d()

    # TODO: Move to pipeline, remove from builder
    osm.save_tile_2d(pipeline.data['filenamebase'] + ".png")
    return

    # Roads sorted + intersections + metadata
    #osm.ways.split_ways_1d()  # Where to put?

    #root.dump()
    #sys.exit(1)

    # Generate buildings
    osm.buildings.preprocess_buildings_2d()
    osm.buildings.generate_buildings_2d()

    # Ways depend on buildings
    osm.ways.generate_ways_2d()

    osm.areas.generate_areas_2d()
    osm.areas.generate_areas_2d_interways()  # and assign types



    osm.areas.generate_areas_2d_postprocess()
    osm.areas.generate_areas_2d_postprocess_water()

    # Associate features (amenities, etc) to 2D objects (buildings, etc)
    osm.buildings.link_features_2d()

    # Coastline and ground
    osm.areas.generate_coastline_3d(osm.area_crop if osm.area_crop else osm.area_filter)  # must come before ground
    osm.areas.generate_ground_3d(osm.area_crop if osm.area_crop else osm.area_filter) # separate in 2d + 3d, also subdivide (calculation is huge - core dump-)

    # Generates items defined as areas (area fountains, football fields...)
    osm.items2.generate_items_2d()  # Objects related to areas (fountains, playgrounds...)

    # Road props (traffic lights, lampposts, fountains, football fields...) - needs. roads, areas, coastline, etc... and buildings
    osm.ways.generate_props_2d()  # Objects related to ways

    # 2D output (before cropping, crop here -so buildings and everything is cropped-)
    #self.save_tile_2d("/tmp/osm2d.png")
    #self.save_tile_2d("/tmp/osm2d.svg")

    # Crop if necessary
    if osm.area_crop:
        logger.info("Cropping to: %s" % (osm.area_crop.bounds, ))
        crop = ddd.shape(osm.area_crop)
        osm.areas_2d = osm.areas_2d.intersection(crop)
        osm.ways_2d = {k: osm.ways_2d[k].intersection(crop) for k in osm.layer_indexes}

        #osm.items_1d = osm.items_1d.intersect(crop)
        osm.items_1d = ddd.group([b for b in osm.items_1d.children if osm.area_crop.contains(b.geom.centroid)], empty=2)
        osm.items_2d = ddd.group([b for b in osm.items_2d.children if osm.area_crop.contains(b.geom.centroid)], empty=2)
        osm.buildings_2d = ddd.group([b for b in osm.buildings_2d.children if osm.area_crop.contains(b.geom.centroid)], empty=2)

    # 3D Build

    # Ways 3D
    osm.ways.generate_ways_3d()
    osm.ways.generate_ways_3d_intersections()
    # Areas 3D
    osm.areas.generate_areas_3d()
    # Buildings 3D
    osm.buildings.generate_buildings_3d()

    # Walls and fences(!) (2D?)

    # Urban decoration (trees, fountains, etc)
    osm.items.generate_items_3d()
    osm.items2.generate_items_3d()

    # Generate custom items
    osm.customs.generate_customs()


    # Final grouping
    scene = [osm.areas_3d, osm.ground_3d, osm.water_3d,
             #osm.sidewalks_3d_lm1, osm.walls_3d_lm1, osm.ceiling_3d_lm1,
             #osm.sidewalks_3d_l1, osm.walls_3d_l1, osm.floor_3d_l1,
             osm.buildings_3d, osm.items_3d,
             osm.other_3d, osm.roadlines_3d]
    scene = ddd.group(scene + list(osm.ways_3d.values()), name="Scene")

    pipeline.root = scene
    #return scene

    osmbuilder = pipeline.data['osm']

    # TODO: Move inside pipeline (outputs depend on pipeline config)
    scene = pipeline.root

    #scene.dump()
    scene.save("/tmp/dddosm.json")
    scene.save(pipeline.data['filenamebase'])

