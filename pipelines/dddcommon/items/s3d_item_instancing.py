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

@dddtask(select='["ddd:item"][ddd:type="3d"]')
def ddd_common_item(logger, pipeline, root, obj):
    """
    Instances items. It's meant to instance 3D items from 3D nodes that are already positioned (their transform)
    in place (or at least pending only elevation adjustments).

    Currently, item instancing removes any children in the object, as it always returns a new object or instance.

    TODO: Support for catalog, also review OSM pipeline to reuse this.
    """

    '''
    print(obj)
    try:
        obj.point_coords()
        return
    except:
        #print("Cannot common item: %s" % (obj, ))
        #ddd.trace(locals())
        #return
        pass
    '''

    item_key = obj.get('ddd:item')

    item_idx = pipeline.data.get('ddd:item:instance:idx', 0)
    pipeline.data['ddd:item:instance:idx'] = item_idx + 1

    #item = pipeline.catalog.instance('CabinetSet')
    if item_key == 'tree':
        item = plants.tree_default(height=random.uniform(5,9))
    elif item_key == 'bush':
        item = plants.tree_bush()
    elif item_key == 'grass_blade':
        item = plants.grass_blade()
    elif item_key == 'rock':
        item = landscape.rock()
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
    
    # FIXME: Using transform here causes height function to use the wrong point coordinates (not transformed), always 0,0
    #item.transform.position = Vector3(centroid)  # (centroid[0], centroid[1], 0))
    item = item.translate(centroid)

    #root.append(item)

    #item = item.translate([0, 0, -0.2])
    #item = ddd.instance(item)  # Try/test instancing for easy positioning
    item.set('ddd:height', 'min')

    return item
