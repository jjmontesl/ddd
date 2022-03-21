# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020


import numpy as np
import trimesh

from ddd.ddd import ddd
from ddd.pipeline.decorators import dddtask
from ddd.geo import terrain
from ddd.core.exception import DDDException
import datetime
from ddd.util.common import parse_bool
from ddd.text.font import DDDFontAtlas
from ddd.text.text2d import Text2D
import random


"""
The "model" stage of the build process is the first stage to handle 3D data.
It selects 2D objects from the node tree (/Areas, /Buildings...) and generates the 3D
geometry from them.

The last steps of this stage (in separate files) apply some optimizations,
such as mesh combination or instance grouping,
before writing the output model to file.

Note: Currently this stage replaces some branches of the node tree, and/or renames others
(eg items are here put into /Items3).
"""


def set_base_height(obj):
    container = obj.get('ddd:area:container', None)
    base_height = 0.0
    if container and container != obj:
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


@dddtask()
def osm_model_generate_ways_roadlines(osm, root, pipeline):
    # TODO: Generate lines in 3D at this stage, instead of during 2D stage
    # Also separate 2D/3D for lines
    roadlines = pipeline.data["Roadlines3"]
    del(pipeline.data["Roadlines3"])
    root.append(roadlines.clean())

@dddtask(path="/Roadlines3/*", select='[!"ddd:height:base"]')
def osm_model_pre_propagate_base_height_roadlines(root, obj):
    """
    Calculates and applies base height to roadlines, since they were not included before
    """
    set_base_height(obj)
    # Translate, since lines 3d are being early generated (but shouldn't)
    base_height = obj.get('ddd:height:base')
    if base_height:
        obj = obj.translate([0, 0, base_height])
        return obj


@dddtask(order="60.10.+", log=True)
def osm_model_init(root, osm):
    """
    Initializes the 3D output node tree structure.
    """

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
def osm_model_generate_coastline(osm, root, obj, logger):

    # Crop this feature as it has not been cropped
    area_crop = osm.area_crop2 if osm.area_crop2 else osm.area_filter2
    coastlines_3d = obj.intersection(area_crop).union().clean()
    if not coastlines_3d.geom:
        return

    coastlines_3d = coastlines_3d.individualize().extrude(15.0).flip_faces().translate([0, 0, -15.0])

    # Subdivide
    if int(ddd.data.get('ddd:area:subdivide', 0)) > 0:
        logger.debug("Subdividing coastline meshes: %s", obj)
        coastlines_3d = ddd.meshops.subdivide_to_grid(coastlines_3d, float(ddd.data.get('ddd:area:subdivide')))

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
    # TODO: Ways2 should not be removed, some other parts may need it later. Just not exported.
    root.remove(root.find("/Ways"))
    if '_ways_areas_new' not in pipeline.data:
        pipeline.data['_ways_areas_new'] = ddd.group3(name="Ways")
    root.append(pipeline.data['_ways_areas_new'])

@dddtask()
def osm_model_generate_ways_roadlines_combine(osm, root, pipeline):
    # TODO: Generate lines in 3D at this stage, instead of during 2D stage
    # Also separate 2D/3D for lines
    roadlines = root.find("/Roadlines3")
    roadlines.replace(roadlines.combine())


@dddtask(path="/Areas/*")  # , select='["ddd:area:type"]')
def osm_model_generate_areas(osm, root, pipeline, obj):

    area_3d = osm.areas3.generate_area_3d(obj)

    if not '_areas_areas_new' in pipeline.data:
        pipeline.data['_areas_areas_new'] = ddd.group3(name="Areas")
    pipeline.data['_areas_areas_new'].append(area_3d)

@dddtask()
def osm_model_generate_areas_replacenode(osm, root, pipeline):
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
        if int(ddd.data.get('ddd:area:subdivide', 0)) > 0:
            walls_3d = ddd.meshops.subdivide_to_grid(walls_3d, float(ddd.data.get('ddd:area:subdivide')))
        walls_3d = ddd.uv.map_cubic(walls_3d)
        structures.append(walls_3d)

    ceilings = root.find("/Structures2/Ceilings")
    if ceilings:
        ceilings_3d = ceilings.extrude(0.5).translate([0, 0, -1.0]).material(ddd.mats.cement)
        ceilings_3d = terrain.terrain_geotiff_elevation_apply(ceilings_3d, osm.ddd_proj)
        if int(ddd.data.get('ddd:area:subdivide', 0)) > 0:
            ceilings_3d = ddd.meshops.subdivide_to_grid(ceilings_3d, float(ddd.data.get('ddd:area:subdivide')))
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


@dddtask(path="/Ways/*", select='["ddd:way:stairs"]')  # [!"intersection"]
def osm_models_areas_stairs_combine(pipeline, osm, root, logger, obj):
    """
    """
    # Remove faces pointing down, as they prevent UV mapping from working correclty
    obj = ddd.meshops.remove_faces_pointing(obj, ddd.VECTOR_DOWN)

    obj = obj.combine()
    obj = ddd.uv.map_cubic(obj)

    return obj


@dddtask()
def osm_model_generate_buildings_preprocess(osm, root):
    buildings_2d = root.find("/Buildings")
    osm.buildings3.preprocess_buildings_3d(buildings_2d)


@dddtask()
def osm_model_generate_buildings(osm, root):
    buildings_2d = root.find("/Buildings")
    buildings_3d = osm.buildings3.generate_buildings_3d(buildings_2d)

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

    TODO: FIXME: This is only for piers? and is excluding fences and hedges. Reconsider this step entirely.
    """

    # TODO: Removing fence here, but what we should do is use exclusively these common generators based on TAGS. Keep refactoring.
    if obj.extra.get('osm:barrier', None) in ("fence", "hedge"):
        return

    # TODO: Ambiguity with height (is it total or top.... normalize in ddd: attributes)
    max_height = float(obj.extra.get('ddd:height'))
    min_height = float(obj.extra.get('ddd:min_height', 0.0))
    if min_height > max_height:
        max_height = min_height + max_height
    dif_height = max_height - min_height

    obj = obj.extrude(dif_height)
    if min_height:
        obj = obj.translate([0, 0, min_height])

    # Subdivide
    # TODO: Is this the correct place to subdivide fences? ItemWays are also subdivides but in s60_model
    if int(ddd.data.get('ddd:area:subdivide', 0)) > 0:
        obj = ddd.meshops.subdivide_to_grid(obj, float(ddd.data.get('ddd:area:subdivide')))

    obj = ddd.uv.map_cubic(obj)

    obj.set('ddd:elevation', default=obj.get('ddd:area:elevation', 'geotiff'))

    root.find("/Items3").append(obj)


@dddtask(path="/Items3/*", select='["ddd:building:parent"]')
def osm_model_elevation_items_buildings(obj, osm, root):
    """Apply elevation from building to building related items."""
    # TODO: (?) Associate earlier to building, and build building with all items, then apply elevation from here to building?
    # Note: this is used for fences and other objects, but not to items (nodes) that are linked to the building, there is some divergence here
    obj.extra['ddd:elevation'] = "building"
    return obj


'''
@dddtask(path="/Items3/*", select='["ddd:min_height"]')
def osm_model_elevation_apply_min_height(obj, osm, root):
    """
    Apply min_height to items.
    """
    min_height = float(obj.extra.get('ddd:min_height', 0.0))
    obj = obj.translate([0, 0, min_height])
    return obj
'''

@dddtask(path="/Items3/*", select='["ddd:elevation" = "geotiff"]')
def osm_model_elevation_apply_terrain(obj, osm, root):
    obj = terrain.terrain_geotiff_elevation_apply(obj, osm.ddd_proj)
    return obj

@dddtask(path="/Items3/*", select='["ddd:elevation" = "building"]')
def osm_model_elevation_apply_building(logger, obj, osm, pipeline, root):
    """
    Apply elevation to items contained in a building.

    This applies the base building elevation in the same fashion that all building parts
    are leveled at the same base elevation.

    This does not apply elevation based on the height of the container building part
    (that remains TODO).
    """

    building_parent = obj.extra['ddd:building:parent']
    logger.info("Building parent: %s %s", building_parent, building_parent.extra)
    if 'ddd:building:elevation' in building_parent.extra:
        building_elevation = float(building_parent.extra['ddd:building:elevation'])
        obj = obj.translate([0, 0, building_elevation])
    else:
        #ddd.trace(locals())
        logger.error("No parent building elevation found for object %s (parent building: %s)", obj, building_parent)
        #raise DDDException("No parent building elevation found for object %s (parent building: %s)" % (obj, building_parent))
    obj = obj.translate([0, 0, -0.20])
    return obj

@dddtask(path="/Items3/*", select='["ddd:elevation" = "min"]')
def osm_model_elevation_apply_terrain_min(obj, osm, root):
    obj = terrain.terrain_geotiff_min_elevation_apply(obj, osm.ddd_proj)
    return obj

@dddtask(path="/Items3/*", select='["ddd:elevation" = "max"]')
def osm_model_elevation_apply_terrain_max(obj, osm, root):
    obj = terrain.terrain_geotiff_max_elevation_apply(obj, osm.ddd_proj)
    return obj


'''
# Moved to 40
@dddtask()
def osm_models_splatmap_materials(pipeline, osm, root, logger):
    """
    Mark materials for splatmap usage.
    """
    root.find("/Areas").select('[ddd:layer="0"]([!ddd:height];[ddd:height = 0])').set('ddd:material:splatmap', True, children=True)
    root.find("/Ways").select('[ddd:layer="0"][ddd:area:type != "stairs"]').set('ddd:material:splatmap', True, children=True)
'''


@dddtask()
def osm_model_texts_fonts(pipeline, root, logger):
    """
    Test 2D text generation.
    """
    #pipeline.data['font'] = Font()
    pipeline.data['font:atlas:opensansemoji_64'] = ddd.material(name="FontOpenSansEmoji-64", color='#f88888',
                                                texture_path=ddd.DATA_DIR + "/fontatlas/opensansemoji64.greyscale.png",
                                                alpha_cutoff=0.5, metallic_factor=0.0, roughness_factor=1.0,
                                                extra={'ddd:material:type': 'font', 'ddd:collider': False, 'ddd:shadows': False,
                                                       'uv:scale': 1.00, 'zoffset': -5.0, 'ddd:texture:resize': 4096})
    pipeline.data['font:atlas:dddfonts_01_64'] = ddd.material(name="DDDFonts-01-64", color='#f88888',
                                                texture_path=ddd.DATA_DIR + "/fontatlas/dddfonts_01_64.greyscale.png",
                                                #texture_normal_path=ddd.DATA_DIR + "/materials/road-marks-es/TexturesCom_Atlas_RoadMarkings2_1K_normal.png",
                                                #atlas_path="/materials/road-marks-es/RoadMarkings2.plist",
                                                alpha_cutoff=0.5, metallic_factor=0.0, roughness_factor=1.0,
                                                extra={'ddd:material:type': 'font', 'ddd:collider': False, 'ddd:shadows': False,
                                                       'uv:scale': 1.00, 'zoffset': -5.0, 'ddd:texture:resize': 4096})

    atlas = DDDFontAtlas.load_atlas(ddd.DATA_DIR + "/fontatlas/dddfonts_01_64.dddfont.json")

    pipeline.data['font:opensansemoji'] = Text2D(atlas, "OpenSansEmoji-default-64", pipeline.data['font:atlas:dddfonts_01_64'])
    pipeline.data['font:oliciy'] = Text2D(atlas, "Oliciy-default-64", pipeline.data['font:atlas:dddfonts_01_64'])
    pipeline.data['font:technasans'] = Text2D(atlas, "TechnaSans-default-64", pipeline.data['font:atlas:dddfonts_01_64'])
    pipeline.data['font:adolphus'] = Text2D(atlas, "Adolphus-default-64", pipeline.data['font:atlas:dddfonts_01_64'])

    pipeline.data['ddd:osm:fonts'] = ['font:opensansemoji',
                                      'font:oliciy',
                                      'font:technasans',
                                      'font:adolphus']


@dddtask(path="/*", select='["ddd:text"]')
def osm_model_texts_generate(pipeline, osm, root, logger, obj):

    text = obj.get('ddd:text')
    fontkey = obj.get('ddd:text:font', None)
    if fontkey:
        fontkey = 'font:' + fontkey
    if fontkey is None:
        fontkey = random.choice(pipeline.data['ddd:osm:fonts'])

    text2d = pipeline.data[fontkey]

    #logger.info("Creating 2D text for: %s", text)

    width = obj.get('ddd:text:width') / len(text)
    height = obj.get('ddd:text:height') / 2.5

    item = text2d.text(text)
    item = item.combine().recenter()
    item = item.material(text2d.material)

    # Place text on object
    if item.mesh:
        #xform = obj.transform.to_matrix()
        item = item.scale([width, height, 1])
        item = item.rotate(ddd.ROT_FLOOR_TO_FRONT)
        #item.mesh.vertices = trimesh.transform_points(item.mesh.vertices, xform)
        item.mesh.vertices = obj.transform.transform_vertices(item.mesh.vertices)

        root.find("/Items3").append(item)
    else:
        logger.error("Failed to generate text 2D mesh: %s %s", text, obj)


#@dddtask(order="65.50.+", log=True)
@dddtask(order="60.95.+", log=True)
def osm_model_rest(pipeline, root, osm, logger):

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

    # Add metadata to tile root object
    # (some of these are used by ddd-viewer format)
    metadataobj = ddd.instance(None, name="Metadata")
    metadataobj.set('tile:bounds_wgs84', pipeline.data['tile:bounds_wgs84'])
    metadataobj.set('tile:bounds_m', pipeline.data['tile:bounds_m'])
    metadataobj.set('tile:create_time', str(datetime.datetime.now()))
    scene.append(metadataobj)

    logger.info("Scene properties: %s", (scene.extra))

    pipeline.root = scene

