# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020


from ddd.ddd import ddd
from ddd.pipeline.decorators import dddtask
from ddd.geo import terrain


@dddtask(order="60.10.+", log=True)
def osm_model_init(root, osm):

    root.append(ddd.group3(name="Items3"))
    #root.append(ddd.group3(name="Ways3"))
    #root.append(ddd.group3(name="Areas3"))
    #root.append(ddd.group3(name="Buildings3"))
    #root.append(ddd.group3(name="Items3"))
    root.append(ddd.group3(name="Other3"))
    #root.append(ddd.group3(name="Meta3"))


@dddtask(order="60.20.+", log=True)
def osm_model_generate(osm, root):
    pass

@dddtask(path="/Features", select='["osm:natural" = "coastline"]')
def osm_model_generate_coastline(osm, root, obj):

    # Crop this feature as it has not been cropped
    area_crop = osm.area_crop2 if osm.area_crop2 else osm.area_filter2
    coastlines_3d = obj.intersection(area_crop).union().clean()
    if not coastlines_3d.geom:
        return

    coastlines_3d = coastlines_3d.individualize().extrude(10.0).translate([0, 0, -10.0])
    coastlines_3d = terrain.terrain_geotiff_elevation_apply(coastlines_3d, osm.ddd_proj)
    coastlines_3d = ddd.uv.map_cubic(coastlines_3d)
    coastlines_3d.name = 'Coastline: %s' % coastlines_3d.name
    root.find("/Other3").append(coastlines_3d)


@dddtask()
def osm_model_generate_ways(osm, root):
    ways_2d = root.find("/Ways")
    ways_3d = osm.ways3.generate_ways_3d(ways_2d)

    root.remove(ways_2d)
    root.append(ways_3d)


@dddtask()
def osm_model_generate_ways_roadlines(osm, root, pipeline):
    # TODO: Do this here, instead of during 2D stage
    roadlines = pipeline.data["Roadlines3"]
    del(pipeline.data["Roadlines3"])
    root.append(roadlines)


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


@dddtask(order="60.50.+", log=True)
def osm_model_rest(pipeline, root, osm):

    # Final grouping
    scene = [root.find("/Areas"),
             #root.find("/Water"),
             root.find("/Ways"),
             root.find("/Buildings"),
             root.find("/Items3"),
             root.find("/Other3"),
             root.find("/Roadlines3"),
             ]
    scene = ddd.group(scene, name="Scene")
    pipeline.root = scene

