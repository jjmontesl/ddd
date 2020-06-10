# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020


from ddd.ddd import ddd
from ddd.pipeline.decorators import dddtask


@dddtask(order="60.10.+", log=True)
def osm_model_init(root, osm):
    pass

@dddtask()
def osm_model_(osm, root):
    pass

@dddtask(log=True)
def osm_model_rest(pipeline, root, osm):

    # 3D Build

    # Coastline and ground
    osm.areas3.generate_coastline_3d(osm.area_crop if osm.area_crop else osm.area_filter)  # must come before ground
    #osm.areas3.generate_ground_3d(osm.area_crop if osm.area_crop else osm.area_filter) # separate in 2d + 3d, also subdivide (calculation is huge - core dump-)

    # Ways 3D
    osm.ways3.generate_ways_3d()
    osm.ways3.generate_ways_3d_intersections()
    # Areas 3D
    osm.areas3.generate_areas_3d()
    # Buildings 3D
    osm.buildings.generate_buildings_3d()

    # Walls and fences(!) (2D?)

    # Urban decoration (trees, fountains, etc)
    osm.items.generate_items_3d()
    osm.items2.generate_items_3d()

    # Generate custom items
    #osm.customs.generate_customs()

    # Final grouping
    scene = [osm.areas_3d, osm.ground_3d, osm.water_3d,
             #osm.sidewalks_3d_lm1, osm.walls_3d_lm1, osm.ceiling_3d_lm1,
             #osm.sidewalks_3d_l1, osm.walls_3d_l1, osm.floor_3d_l1,
             osm.buildings_3d, osm.items_3d,
             osm.other_3d, osm.roadlines_3d]
    scene = ddd.group(scene + list(osm.ways_3d.values()), name="Scene")
    pipeline.root = scene

