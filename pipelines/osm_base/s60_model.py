# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020


from ddd.ddd import ddd
from ddd.pipeline.decorators import dddtask


@dddtask(order="60.10.+", log=True)
def osm_model_init(root, osm):

    root.append(ddd.group3(name="Items3"))
    #root.append(ddd.group3(name="Ways3"))
    #root.append(ddd.group3(name="Areas3"))
    #root.append(ddd.group3(name="Buildings3"))
    #root.append(ddd.group3(name="Items3"))
    #root.append(ddd.group3(name="Meta3"))


@dddtask(order="60.20.+", log=True)
def osm_model_generate(osm, root):
    pass

@dddtask()
def osm_model_generate_coastline(osm, root):
    osm.areas3.generate_coastline_3d(osm.area_crop if osm.area_crop else osm.area_filter)

@dddtask()
def osm_model_generate_ways(osm, root):
    ways_2d = root.find("/Ways")
    ways_3d = osm.ways3.generate_ways_3d(ways_2d)

    root.remove(ways_2d)
    root.append(ways_3d)


@dddtask()
def osm_model_generate_areas(osm, root):
    areas_2d = root.find("/Areas")
    areas_3d = osm.areas3.generate_areas_3d(areas_2d)

    root.remove(areas_2d)
    root.append(areas_3d)


@dddtask()
def osm_model_generate_buildings(osm, root):
    buildings_2d = root.find("/Buildings")
    buildings_3d = osm.buildings.generate_buildings_3d(buildings_2d)

    root.remove(buildings_2d)
    root.append(buildings_3d)


@dddtask(path="/Items/*")
def osm_model_generate_items1(obj, osm, root):
    item_3d = osm.items.generate_item_3d(obj)
    if item_3d:
        #item_3d.name = item_3d.name if item_3d.name else item_2d.name
        root.find("/Items3").append(item_3d)

@dddtask(path="/Items2/*")
def osm_model_generate_items2(obj, osm, root):
    """Generating 3D area items."""
    item_3d = osm.items2.generate_item_3d(obj)
    if item_3d:
        root.find("/Items3").append(item_3d)


@dddtask(log=True)
def osm_model_rest(pipeline, root, osm):

    # Final grouping
    scene = [root.find("/Areas"),
             #root.find("/Water"),
             root.find("/Ways"),
             root.find("/Buildings"),
             root.find("/Items3"),
             #root.find("/Other"),
             #root.find("/Roadlines"),
             ]
    scene = ddd.group(scene, name="Scene")
    pipeline.root = scene

