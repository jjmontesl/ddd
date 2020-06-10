# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020


from ddd.ddd import ddd
from ddd.pipeline.decorators import dddtask



'''
@dddtask(order="30.50.20.+", log=True)
def osm_groups_areaitems(root, osm):

    # Split and junctions first?
    # Possibly: metadata can depend on that, and it needs to be done if it will be done anyway

    # Otherwise: do a pre and post step, and do most things in post (everything not needed for splitting)

    pass

@dddtask(path="/Areas/*")
def osm_groups_areas_default_name(obj, osm):
    """Set default name."""
    name = "Area: " + (obj.extra.get('osm:name', obj.extra.get('osm:id')))
    obj.name = name
    #obj.extra['ddd:ignore'] = True

@dddtask(path="/Areas/*")
def osm_groups_areas_default_material(obj, osm):
    """Assign default material."""
    obj = obj.material(ddd.mats.terrain)
    return obj

@dddtask(path="/Areas/*")
def osm_groups_areas_default_data(obj, osm):
    """Sets default data."""
    obj.extra['ddd:area:weight'] = 100  # Lowest
    obj.extra['ddd:area:height'] = 0  # Lowest
'''


