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




@dddtask(order="30.50.20.+", log=True)
def osm_groups_areas(root, osm):

    # Split and junctions first?
    # Possibly: metadata can depend on that, and it needs to be done if it will be done anyway

    # Otherwise: do a pre and post step, and do most things in post (everything not needed for splitting)

    pass

@dddtask(path="/Areas/*")
def osm_groups_areas_default_name(obj, osm):
    """Set way default data."""
    name = "Area: " + (obj.extra.get('osm:name', obj.extra.get('osm:id')))
    obj.name = name
    #obj.extra['ddd:ignore'] = True

@dddtask(path="/Areas/*")
def osm_groups_areas_default_material(obj, osm):
    """Assign default material."""
    #obj = obj.material(ddd.mats.asphalt)
    return obj

@dddtask(path="/Areas/*")
def osm_groups_areas_default_data(obj, osm):
    """Sets default data."""
    obj.extra['ddd:area:weight'] = 100  # Lowest
    obj.extra['ddd:area:height'] = 0  # Lowest



