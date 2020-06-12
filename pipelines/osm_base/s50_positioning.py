# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020

import sys

import pyproj

from ddd.ddd import ddd
from ddd.geo import terrain
from ddd.osm import osm
from ddd.osm.osm import project_coordinates
from ddd.pipeline.decorators import dddtask

"""
"""


@dddtask(order="50.05.10.+", log=True)
def osm_positioning(pipeline, osm, root, logger):
    """Repositions features in different ways."""
    pass

@dddtask(order="50.05.20.+", log=True)
def osm_positioning_init(pipeline, osm, root, logger):
    """Repositions features in different ways."""

    pipeline.data['positioning_ways_2d_0'] = root.select(path="/Ways/*", selector='["osm:layer" = "0"]', recurse=False)
    pipeline.data['positioning_ways_2d_0_major'] = root.select(path="/Ways/*", selector='["osm:layer" = "0"]', recurse=False).flatten().filter(lambda i: i.extra.get('osm:highway', None) not in ('path', 'track', 'footway', None))
    #pipeline.data['positioning_ways_2d_0_traffic_sign'] = root.select(path="/Ways/*", selector='["osm:layer" = "0"]', recurse=False).flatten().filter(lambda i: i.extra.get('osm:highway', None) not in ('path', 'track', 'footway', None))
    pipeline.data['positioning_buildings_2d'] = root.select(path="/Buildings/*", recurse=False)
    pipeline.data['positioning_ways_2d_0_and_buildings'] = ddd.group([pipeline.data['positioning_ways_2d_0'], pipeline.data['positioning_buildings_2d']]).clean(eps=0.01)

# TODO: Tag earlier, during items creation
@dddtask(order="50.05.30.+", log=True)
def osm_positioning_select(pipeline, osm, root, logger):
    pass

@dddtask(path="/Items/*", select='["osm:amenity" = "bench"]')
def osm_positioning_select_bench(obj, osm, root, logger):
    obj.extra['ddd:positioning:type'] = 'orient-project'
    obj.extra['ddd:positioning:ref'] = 'positioning_ways_2d_0'

@dddtask(path="/Items/*", select='["osm:amenity" = "post_box"]')
def osm_positioning_select_postbox (obj, osm, root, logger):
    obj.extra['ddd:positioning:type'] = 'snap-project'
    obj.extra['ddd:positioning:ref'] = 'positioning_ways_2d_0'
    obj.extra['ddd:positioning:penetrate'] = -1.0

@dddtask(path="/Items/*", select='["osm:amenity" = "waste_basket"]')
def osm_positioning_select_waste_basket(obj, osm, root, logger):
    obj.extra['ddd:positioning:type'] = 'snap-project'
    obj.extra['ddd:positioning:ref'] = 'positioning_ways_2d_0'
    obj.extra['ddd:positioning:penetrate'] = -1.0
    obj.extra['ddd:positioning:validate:ref'] = 'positioning_ways_2d_0_and_buildings'

@dddtask(path="/Items/*", select='["osm:highway" = "bus_stop"]')
def osm_positioning_select_bus_stop(obj, osm, root, logger):
    obj.extra['ddd:positioning:type'] = 'snap-project'
    obj.extra['ddd:positioning:ref'] = 'positioning_ways_2d_0_major'
    obj.extra['ddd:positioning:penetrate'] = -0.5

@dddtask(path="/Items/*", select=r'[~"^osm:traffic_sign"][!"ddd:angle"]')
def osm_positioning_select_traffic_sign(obj, osm, root, logger):
    obj.extra['ddd:positioning:type'] = 'snap-project'
    obj.extra['ddd:positioning:ref'] = 'positioning_ways_2d_0'
    obj.extra['ddd:positioning:penetrate'] = -0.5

@dddtask(path="/Items/*", select='["osm:highway" = "traffic_signals"][!"ddd:angle"]')
def osm_positioning_select_traffic_signals(obj, osm, root, logger):
    # TODO: This shall be calculated along with way items.
    obj.extra['ddd:positioning:type'] = 'snap-project'
    obj.extra['ddd:positioning:ref'] = 'positioning_ways_2d_0'
    #obj.extra['ddd:positioning:penetrate'] = -0.5


@dddtask(path="/Items/*", select='["osm:tourism" = "artwork"]["osm:artwork_type" = "sculpture"]')
def osm_positioning_select_sculpture(obj, osm, root, logger):
    obj.extra['ddd:positioning:type'] = 'orient-project'
    obj.extra['ddd:positioning:ref'] = 'positioning_ways_2d_0'
    #obj.extra['ddd:positioning:penetrate'] = -0.5

@dddtask(path="/Items/*", select='["osm:tourism" = "artwork"]["osm:artwork_type" = "statue"]')
def osm_positioning_select_statue(obj, osm, root, logger):
    obj.extra['ddd:positioning:type'] = 'orient-project'
    obj.extra['ddd:positioning:ref'] = 'positioning_ways_2d_0'
    #obj.extra['ddd:positioning:penetrate'] = -0.5


@dddtask(path="/Items/*", select='["osm:historic" = "monument"]')
def osm_positioning_select_historic_monument(obj, osm, root, logger):
    obj.extra['ddd:positioning:type'] = 'orient-project'
    obj.extra['ddd:positioning:ref'] = 'positioning_ways_2d_0'
    #obj.extra['ddd:positioning:penetrate'] = -0.5

@dddtask(path="/Items/*", select='["osm:historic" = "memorial"]')
def osm_positioning_select_historic_memorial(obj, osm, root, logger):
    obj.extra['ddd:positioning:type'] = 'orient-project'
    obj.extra['ddd:positioning:ref'] = 'positioning_ways_2d_0'
    #obj.extra['ddd:positioning:penetrate'] = -0.5

@dddtask(path="/Items/*", select='["osm:historic" = "wayside_cross"]')
def osm_positioning_select_historic_wayside_cross(obj, osm, root, logger):
    obj.extra['ddd:positioning:type'] = 'orient-project'
    obj.extra['ddd:positioning:ref'] = 'positioning_ways_2d_0'
    #obj.extra['ddd:positioning:penetrate'] = -0.5

@dddtask(path="/Items/*", select='["osm:highway" = "street_lamp"]')
def osm_positioning_select_highway_street_lamp(obj, osm, root, logger):
    obj.extra['ddd:positioning:validate:ref'] = 'positioning_ways_2d_0_and_buildings'

@dddtask(path="/Items/*", select='["osm:amenity" = "table"]')
def osm_positioning_select_amenity_table(obj, osm, root, logger):
    obj.extra['ddd:positioning:type'] = 'orient-project'
    obj.extra['ddd:positioning:ref'] = 'positioning_ways_2d_0'
    #obj.extra['ddd:positioning:penetrate'] = -1

@dddtask(path="/Items/*", select='["osm:amenity" = "seat"]')
def osm_positioning_select_amenity_seat(obj, osm, root, logger):
    obj.extra['ddd:positioning:type'] = 'orient-project'
    obj.extra['ddd:positioning:ref'] = 'positioning_ways_2d_0'
    #obj.extra['ddd:positioning:penetrate'] = -1

@dddtask(path="/Items/*", select='["osm:amenity" = "umbrella"]')
def osm_positioning_select_amenity_umbrella(obj, osm, root, logger):
    obj.extra['ddd:positioning:type'] = 'orient-project'
    obj.extra['ddd:positioning:ref'] = 'positioning_ways_2d_0'
    #obj.extra['ddd:positioning:penetrate'] = -1

@dddtask(path="/Items/*", select='["osm:emergency" = "fire_hydrant"]')
def osm_positioning_select_emergency_fire_hydrant(obj, osm, root, logger):
    obj.extra['ddd:positioning:type'] = 'orient-project'
    obj.extra['ddd:positioning:ref'] = 'positioning_ways_2d_0'
    #obj.extra['ddd:positioning:penetrate'] = -1


# Apply
@dddtask(order="50.05.50.+", log=True)
def osm_positioning_apply(pipeline, osm, root, logger):
    """Apply positioning tagging (ddd:positioning)."""
    pass

@dddtask(order="50.05.50.10.+", select='["ddd:positioning:type" = "snap-project"]')
def osm_positioning_apply_snap_project(obj, pipeline, osm, root, logger):
    obj = ddd.snap.project(obj, pipeline.data[obj.extra['ddd:positioning:ref']], penetrate=obj.extra.get('ddd:positioning:penetrate', None))
    return obj

@dddtask(order="50.05.50.10.+", select='["ddd:positioning:type" = "orient-project"]')
def osm_positioning_apply_orient_project(obj, pipeline, osm, root, logger):
    if obj.extra.get('ddd:angle', None) is None:
        projected_point = ddd.snap.project(obj, pipeline.data[obj.extra['ddd:positioning:ref']], penetrate=obj.extra.get('ddd:positioning:penetrate', None))
        obj.extra['ddd:angle'] = projected_point.extra['ddd:angle']
    return obj

@dddtask(order="50.05.50.50.+", select='["ddd:positioning:validate:ref"]')
def osm_positioning_apply_validate_overlap(obj, pipeline, osm, root, logger):
    """Check if item can be placed."""
    invalid = pipeline.data[obj.extra['ddd:positioning:validate:ref']]
    if not osm.osmops.placement_valid(obj.buffer(0.2), invalid=invalid):
        return False

