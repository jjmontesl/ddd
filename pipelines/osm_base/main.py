# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020

from ddd.osm import osm
from ddd.pipeline.decorators import dddtask
from ddd.ddd import ddd
import sys


@dddtask()
def start_run(pipeline, root):
    """
    Run at initial stage, load data.
    """
    pass

'''
@dddtask(log=True)
def stage_10_preprocess_features(pipeline, osm):
    #pipeline.data['osm'].preprocess_features()
    #osm.preprocess_features()
    pass

@dddtask(parent="stage_01_preprocess_features", log=True)
def preprocess_features(pipeline, osm):
    #pipeline.data['osm'].preprocess_features()
    osm.preprocess_features()
'''

@dddtask(filter=lambda o: o.geom, log=True)  # and o.geom.type in ('Point', 'Polygon', 'MultiPolygon') .. and o.geom.type == 'Polygon' |  ... path="/Features", select=r'["geom:type"="Polygon"]'
def stage_10_crop_extended_area(pipeline, osm, root, obj):
    """Crops to extended area size to avoid working with huge areas."""

    # TODO: Crop centroids of buildings and lines and entire areas...

    #pipeline.data['osm'].preprocess_features()
    #osm.preprocess_features()
    obj = obj.intersection(osm.area_filter2)

    return obj

@dddtask(log=True)
def stage_20_preprocess_features(pipeline, osm, root):
    #pipeline.data['osm'].preprocess_features()
    #osm.preprocess_features()
    #root.show()
    #sys.exit(1)
    root.save("/tmp/osm-20-features.svg")
    root.save("/tmp/osm-20-features.json")

@dddtask(log=True)
def stage_30_create_nodes(root, osm):
    items = ddd.group2(name="Items")  # 1D
    root.append(items)
    items = ddd.group2(name="Ways")  # 1D
    root.append(items)
    items = ddd.group2(name="Areas")  # 2D
    root.append(items)
    items = ddd.group2(name="Buildings")  # 2D
    root.append(items)

    #root.dump(data=True)

@dddtask(path="/Features/*", select='[geom:type="Point"]', log=True)  #  , select='[geom:type="Point"]'  , parent="stage_30_generate_items_node")
def stage_30_generate_items(root, osm, obj):
    """Generate items for point features."""
    item = obj.copy(name="Item: %s" % obj.name)
    item = item.material(ddd.mats.highlight)
    root.find("/Items").append(item)

@dddtask(log=True)  #  , select='[geom:type="Point"]'  , parent="stage_30_generate_items_node")
def stage_31_process_items(root, osm, obj):
    """Generate items for point features."""
    root.save("/tmp/osm-31-items.svg")

@dddtask(path="/Features/*", select='[geom:type="LineString"]', log=True)
def osm_40_generate_ways(root, obj):
    # Ways depend on buildings
    item = obj.copy(name="Way: %s" % obj.name)

    item = item.material(ddd.mats.asphalt)
    root.find("/Ways").append(item)

    ## ?? osm.ways.generate_ways_1d()

@dddtask(log=True)
def osm_45_process_ways(pipeline, osm, root, logger):
    pass


@dddtask(path="/Features/*", select='[geom:type="Polygon"]', log=True)
def osm_50_generate_areas(root, obj):
    # Ways depend on buildings
    item = obj.copy(name="Area: %s" % obj.name)
    root.find("/Features").append(item)

    ## ?? osm.ways.generate_ways_1d()

@dddtask(log=True)
def osm_55_process_areas(pipeline, osm, root, logger):
    pass



@dddtask(log=True)
def osm_99_rest(pipeline, osm, root, logger):

    #self.features_2d.filter(lambda o: o.extra.get('osm:building:part', None) is not None).dump()


    root.save("/tmp/osm-99.json")

    # TODO: Shall already be done earlier
    osm.features_2d = root.find("/Features")
    osm.items_1d = root.find("/Items")
    osm.ways_1d = root.find("/Ways")

    # Generate items for point features
    ##osm.items.generate_items_1d()

    # Roads sorted + intersections + metadata
    ##osm.ways.generate_ways_1d()
    osm.ways.split_ways_1d()

    #root.dump()
    #sys.exit(1)

    # Generate buildings
    osm.buildings.generate_buildings_2d()

    # Ways depend on buildings
    osm.ways.generate_ways_2d()

    osm.save_tile_2d("/tmp/tile.svg")
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

    # Trees, parks, gardens...

    scene = [osm.areas_3d, osm.ground_3d, osm.water_3d,
             #osm.sidewalks_3d_lm1, osm.walls_3d_lm1, osm.ceiling_3d_lm1,
             #osm.sidewalks_3d_l1, osm.walls_3d_l1, osm.floor_3d_l1,
             osm.buildings_3d, osm.items_3d,
             osm.other_3d, osm.roadlines_3d]
    scene = ddd.group(scene + list(osm.ways_3d.values()), name="Scene")

    pipeline.root = scene
    #return scene

