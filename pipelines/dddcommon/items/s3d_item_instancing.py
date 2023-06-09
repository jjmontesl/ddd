# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020-2023


from ddd.math.vector3 import Vector3
from ddd.pack.sketchy import plants, landscape
from ddd.pipeline.decorators import dddtask
from ddd.ddd import ddd
import random
import noise
from ddd.util.common import parse_bool
from ddd.core.exception import DDDException
import math


# TODO: Move to ops.items...
def generate_item_3d_generic(item_2d, gen_func, name):

    item_3d = gen_func()

    if item_3d is None:
        return None

    #item_3d = item_3d.rotate([0, 0, angle if angle is not None else item_2d.extra['ddd:angle'] - math.pi / 2])
    #item_3d = item_3d.translate([coords[0], coords[1], 0.0])
    #item_3d.prop_set('ddd:static', False, children=True)  # TODO: Make static or not via styling
    
    item_3d.name = name
    return item_3d

# TODO: Generalize to 'ddd:common' and move code to ops.items...?
def generate_item_3d_generic_catalog(catalog, key, item_2d, gen_func, name):

    item_3d = catalog.instance(key)
    if not item_3d:
        item_3d = gen_func()
        item_3d = catalog.add(key, item_3d)

    #coords = item_2d.geom.coords[0]
    #item_3d = item_3d.rotate([0, 0, item_2d.extra['ddd:angle'] - math.pi / 2])
    #item_3d = item_3d.translate([coords[0], coords[1], 0.0])
    #item_3d.set('_height_mapping', default='terrain_geotiff_incline_elevation_apply')
    item_3d.set('ddd:instance:key', key)
    
    item_3d.name = name
    return item_3d


@dddtask(select='["ddd:item"][ddd:type="3d"]')
def ddd_common_item_instance(logger, pipeline, root, obj):
    """
    Instances items. It's meant to instance 3D items from 3D nodes that are already positioned (their transform)
    in place (or at least pending only elevation adjustments).

    Currently, item instancing removes any children in the object, as it always returns a new object or instance.

    TODO: Support for catalog, also review OSM pipeline to reuse this.
    """

    item_key = obj.get('ddd:item')

    item_idx = pipeline.data.get('ddd:item:instance:idx', 0)
    pipeline.data['ddd:item:instance:idx'] = item_idx + 1

    # FIXME: Call DDD pack/catalog instancer that should account for types, packs, parameters, etc...
    # FIXME: Normalize catalog usage vs not (for all pipelines: DDD / OSM / VRS)
    
    #item = pipeline.catalog.instance('CabinetSet')
    if item_key == 'tree':
         #item = plants.tree_default(height=random.uniform(5,9))
         item = generate_item_3d_generic_catalog(pipeline.catalog, 'Tree 0', obj, plants.tree_default, 'Tree %s' % obj.name)
    elif item_key == 'bush':
        #item = plants.tree_bush()
        item = generate_item_3d_generic_catalog(pipeline.catalog, 'Bush 0', obj, plants.tree_bush, 'Bush %s' % obj.name)
    elif item_key == 'grass_blade':
        #item = plants.grass_blade()
        item = generate_item_3d_generic_catalog(pipeline.catalog, 'Grass Blade 0', obj, plants.grass_blade, 'Grass Blade %s' % obj.name)
    elif item_key == 'rock':
        #item = landscape.rock()
        item = generate_item_3d_generic_catalog(pipeline.catalog, 'Rock 0', obj, landscape.rock, 'Rock %s' % obj.name)
    else:
        raise DDDException("Unknown item: %s" % item_key)

    # Copy data
    item.copy_from(obj)
    #item.name = "Item: %s %s %d" % (obj.name, item_key, item_idx)
    item.name = "Item: %s %d" % (item_key, item_idx)
    
    # FIXME: what is this hack? why do we rename children? (possibly to avoid name collisions for trimesh :? but this is not fully correct)
    for c in item.children:
        c.name = str(c.name) + " " + str(item_idx)

    # Changes to the item (should be done in a separate task, or in many cases, when the object is created for the catalog)
    # FIXME: Trees should not have colliders in the leaves
    # FIXME: Use cylinder colliders as possible (in general, define custom colliders in object creation, enable it here)
    item.select(selector='[ddd:material = "Bark"]', recurse=True).set('ddd:collider', True, children=True)


    #centroid = obj.centroid().geom.coords[0]
    #centroid = obj.point_coords()
    centroid = obj.transform.position

    #(major, minor, rotation) = ddd.geomops.oriented_axis(obstacle2)
    #rotation = transformations.quaternion_from_euler(0, 0, -rotation, "sxyz")
    #cabinetset.transform.rotation = rotation

    #item.transform.position = cabinetset.transform.forward() * 0.2 + cabinetset.transform.position
    
    #item = item.translate([0, 0, -0.2])
    #item = ddd.instance(item)  # FIXME: Try/test instancing for easy positioning (and ability to use rotation)
    
    # FIXME: Using transform here causes height function to use the wrong point coordinates (not transformed), always 0,0
    #item = item.translate(centroid)
    item.transform.position = Vector3(centroid)  # (centroid[0], centroid[1], 0))

    item.set('ddd:height', 'min')
    item.set('ddd:angle', default=ddd.random.angle())

    return item
