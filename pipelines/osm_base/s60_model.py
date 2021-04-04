# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020


from ddd.ddd import ddd
from ddd.pipeline.decorators import dddtask
from ddd.geo import terrain
from ddd.core.exception import DDDException


def set_base_height(obj):
    container = obj.get('ddd:area:container', None)
    base_height = 0.0
    if container:
        set_base_height(container)
        base_height = container.get('ddd:height:base', 0)
        obj_height = container.get('ddd:height', 0)
        base_height = (base_height if base_height else 0) + (obj_height if obj_height else 0)
    obj.set('ddd:height:base', base_height)

@dddtask(order="60.05.+", path="/Areas/*", select='[!"ddd:height:base"]')
def osm_model_pre_propagate_base_height_areas(root, obj):
    """
    Propagates height and height:base, using already calculated containment relations between areas.
    """
    set_base_height(obj)

@dddtask(order="60.05.+", path="/Ways/*", select='[!"ddd:height:base"]')
def osm_model_pre_propagate_base_height_ways(root, obj):
    """
    Propagates height and height:base, using already calculated containment relations between areas.
    """
    set_base_height(obj)

@dddtask(order="60.05.+", path="/ItemsNodes/*", select='[!"ddd:height:base"]')
def osm_model_pre_propagate_base_height_items_nodes(root, obj):
    """
    Propagates height and height:base, using already calculated containment relations between areas.
    """
    set_base_height(obj)



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

    coastlines_3d = coastlines_3d.individualize().extrude(15.0).translate([0, 0, -15.0])
    coastlines_3d = terrain.terrain_geotiff_elevation_apply(coastlines_3d, osm.ddd_proj)
    coastlines_3d = coastlines_3d.material(ddd.mats.rock)
    coastlines_3d = ddd.uv.map_cubic(coastlines_3d)
    coastlines_3d.name = 'Coastline: %s' % coastlines_3d.name
    root.find("/Other3").append(coastlines_3d)


@dddtask(path="/Ways/*")  # , select='["ddd:area:type"]')
def osm_model_generate_ways(osm, root, pipeline, obj):

    obj.extra['ddd:area:elevation'] = 'path'
    way_3d = osm.areas3.generate_area_3d(obj)

    if not '_ways_areas_new' in pipeline.data:
        pipeline.data['_ways_areas_new'] = ddd.group3(name="Ways")
    pipeline.data['_ways_areas_new'].append(way_3d)

@dddtask()
def osm_model_generate_ways_init(osm, root, pipeline):
    root.remove(root.find("/Ways"))
    if '_ways_areas_new' not in pipeline.data:
        pipeline.data['_ways_areas_new'] = ddd.group3(name="Ways")
    root.append(pipeline.data['_ways_areas_new'])

'''
@dddtask()
def osm_model_generate_ways_old(osm, root, pipeline):

    # TODO: Added to avoid bug with no areas being generated above (review this broken transition between old/new ways/areas)
    if not '_ways_areas_new' in pipeline.data:
        pipeline.data['_ways_areas_new'] = ddd.group3()

    ways_2d = root.find("/Ways")
    ways_3d = osm.ways3.generate_ways_3d(ways_2d)

    # While old and new ways are together
    for o in pipeline.data['_ways_areas_new'].children: ways_3d.append(o)
    del(pipeline.data['_ways_areas_new'])

    root.remove(ways_2d)
    root.append(ways_3d)
'''

'''
# Note: Done as area:elevation=path now
@dddtask(path="/Ways/", select='["ddd:layer_transition"]')  # ;["ddd:layer"="0a"]')
def osm_model_generate_ways_height_apply(osm, root, pipeline, obj):
    # logger.debug("3D layer transition: %s", way)
    # if way.extra['ddd:layer_transition']:
    way = obj
    if ('way_1d' in way.extra):
        path = way.extra['way_1d']
        vertex_func = osm.ways1.get_height_apply_func(path)
        way = way.vertex_func(vertex_func)
    #else:
    #    nway = way.translate([0, 0, osm.ways1.layer_height(way.get('ddd:layer', 0))])
    return way
'''

@dddtask()
def osm_model_generate_ways_roadlines_combine(osm, root, pipeline):
    # TODO: Generate lines in 3D at this stage, instead of during 2D stage
    # Also separate 2D/3D for lines
    roadlines = pipeline.data["Roadlines3"]
    del(pipeline.data["Roadlines3"])
    root.append(roadlines.combine())

@dddtask(path="/Areas/*")  # , select='["ddd:area:type"]')
def osm_model_generate_areas(osm, root, pipeline, obj):

    area_3d = osm.areas3.generate_area_3d(obj)

    if not '_areas_areas_new' in pipeline.data:
        pipeline.data['_areas_areas_new'] = ddd.group3(name="Areas")
    pipeline.data['_areas_areas_new'].append(area_3d)

@dddtask()
def osm_model_generate_areas_init(osm, root, pipeline):
    root.remove(root.find("/Areas"))
    root.append(pipeline.data['_areas_areas_new'])


@dddtask()
def osm_model_generate_structures(osm, root, pipeline, logger):
    """

    TODO: Generate structures as a whole, without dealing with individual types, using metadata.
    """

    structures = ddd.group3(name="Structures3")

    #sidewalks_3d = objsidewalks_2d.extrude(0.3).translate([0, 0, -5]).material(ddd.mats.sidewalk)
    walls = root.find("/Structures2/Walls")
    if walls:
        walls_3d = walls.extrude(5.5).translate([0, 0, -6]).material(ddd.mats.cement)
        walls_3d = terrain.terrain_geotiff_elevation_apply(walls_3d, osm.ddd_proj)
        walls_3d = ddd.uv.map_cubic(walls_3d)
        structures.append(walls_3d)

    ceilings = root.find("/Structures2/Ceilings")
    if ceilings:
        ceilings_3d = ceilings.extrude(0.5).translate([0, 0, -1.0]).material(ddd.mats.cement)
        ceilings_3d = terrain.terrain_geotiff_elevation_apply(ceilings_3d, osm.ddd_proj)
        ceilings_3d = ddd.uv.map_cubic(ceilings_3d)
        structures.append(ceilings_3d)

    #sidewalks_3d = terrain.terrain_geotiff_elevation_apply(sidewalks_3d, self.osm.ddd_proj)
    #sidewalks_3d = ddd.uv.map_cubic(sidewalks_3d)
    #floors_3d = floors_2d.extrude(-0.3).translate([0, 0, -5]).material(ddd.mats.sidewalk)
    #floors_3d = floors_2d.triangulate().translate([0, 0, -5]).material(ddd.mats.sidewalk)
    #floors_3d = terrain.terrain_geotiff_elevation_apply(floors_3d, osm.ddd_proj)

    #subway = ddd.group([sidewalks_3d, walls_3d, floors_3d, ceilings_3d], empty=3).translate([0, 0, -0.2])
    #self.osm.other_3d.children.append(subway)

    root.append(structures)



'''
@dddtask()
def osm_model_generate_areas_old(osm, root):
    areas_2d = root.find("/Areas")
    areas_3d = osm.areas3.generate_areas_3d(areas_2d)  # areas_2d.clean()

    root.remove(areas_2d)
    root.append(areas_3d)
'''


@dddtask(path="/Ways/*", select='["ddd:way:stairs"][!"intersection"]')
def osm_models_areas_stairs_combine(pipeline, osm, root, logger, obj):
    """
    """
    obj = obj.combine()
    return obj


@dddtask()
def osm_model_generate_buildings(osm, root):
    buildings_2d = root.find("/Buildings")
    buildings_3d = osm.buildings.generate_buildings_3d(buildings_2d)

    root.remove(buildings_2d)
    root.append(buildings_3d)



@dddtask(path="/ItemsNodes/*", select='[!"ddd:angle"]')
def osm_positioning_ensure_angles(pipeline, obj):
    obj.prop_set('ddd:angle', default=0)


@dddtask(path="/ItemsNodes/*")
def osm_model_generate_items_nodes(obj, osm, root):
    item_3d = osm.items.generate_item_3d(obj)
    if item_3d:
        #item_3d.name = item_3d.name if item_3d.name else item_2d.name
        root.find("/Items3").append(item_3d)

@dddtask(path="/ItemsAreas/*")
def osm_model_generate_items_areas(obj, osm, root):
    """Generating 3D area items."""
    item_3d = osm.items2.generate_item_3d(obj)
    if item_3d:
        root.find("/Items3").append(item_3d)

@dddtask(path="/ItemsWays/*")
def osm_model_generate_items_ways(obj, osm, root):
    item_3d = osm.items.generate_item_3d(obj)
    if item_3d:
        #item_3d.name = item_3d.name if item_3d.name else item_2d.name
        root.find("/Items3").append(item_3d)

@dddtask(path="/ItemsWays/*", select='["ddd:height"]')
def osm_model_generate_items_ways_height(obj, osm, root):
    """
    This is currently used to extrude ItemsWays that have a height (eg. piers)
    """

    # TODO: Removing fence here, but what we should do is use exclusively these common generators based on TAGS. Keep refactoring.

    if obj.extra.get('osm:barrier', None) in ("fence", "hedge"):
        return

    max_height = float(obj.extra.get('ddd:height'))
    min_height = float(obj.extra.get('ddd:min_height', 0.0))
    dif_height = max_height - min_height

    obj = obj.extrude(dif_height)
    if min_height:
        obj = obj.translate([0, 0, min_height])
    obj = ddd.uv.map_cubic(obj)

    obj.extra['ddd:elevation'] = obj.get('ddd:area:elevation', 'geotiff')

    root.find("/Items3").append(obj)

@dddtask(path="/Items3/*", select='["ddd:building:parent"]')
def osm_model_elevation_items_buildings(obj, osm, root):
    """Apply elevation from building to building related items."""
    # TODO: (?) Associate earlier to building, and build building with all items, then apply elevation from here to building?
    obj.extra['ddd:elevation'] = "building"
    return obj


@dddtask(path="/Items3/*", select='["ddd:elevation" = "geotiff"]')
def osm_model_elevation_apply_terrain(obj, osm, root):
    obj = terrain.terrain_geotiff_elevation_apply(obj, osm.ddd_proj)
    return obj

@dddtask(path="/Items3/*", select='["ddd:elevation" = "building"]')
def osm_model_elevation_apply_building(logger, obj, osm, pipeline, root):
    """Apply elevation to items contained in a building."""
    building_parent = obj.extra['ddd:building:parent']
    logger.info("Building parent: %s %s", building_parent, building_parent.extra)
    if 'ddd:building:elevation' in building_parent.extra:
        building_elevation = float(building_parent.extra['ddd:building:elevation'])
        obj = obj.translate([0, 0, building_elevation])
    else:
        ddd.trace(locals())
        logger.error("No parent building elevation found for object %s (parent building: %s)", obj, building_parent)
        raise DDDException("No parent building elevation found for object %s (parent building: %s)" % (obj, building_parent))
    obj = obj.translate([0, 0, -0.20])
    return obj

@dddtask(path="/Items3/*", select='["ddd:elevation" = "min"]')
def osm_model_elevation_apply_terrain_min(obj, osm, root):
    obj = terrain.terrain_geotiff_min_elevation_apply(obj, osm.ddd_proj)
    return obj

@dddtask(order="60.50.+", log=True)
def osm_model_rest(pipeline, root, osm):

    # Final grouping
    scene = [root.find("/Areas"),
             #root.find("/Water"),
             root.find("/Ways"),
             root.find("/Structures3"),
             root.find("/Buildings"),
             root.find("/Items3"),
             root.find("/Other3"),
             root.find("/Roadlines3"),
             ]
    scene = ddd.group(scene, name="Scene")
    pipeline.root = scene

