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



@dddtask(order="30.30.20.+", log=True)
def osm_groups_ways(root, osm):

    # Split and junctions first?
    # Possibly: metadata can depend on that, and it needs to be done if it will be done anyway

    # Otherwise: do a pre and post step, and do most things in post (everything not needed for splitting)

    pass

@dddtask(path="/Ways/*")
def osm_groups_ways_default_name(obj, osm):
    """Set way default data."""
    name = "Way: " + (obj.extra.get('osm:name', obj.extra.get('osm:id')))
    obj.name = name
    #obj.extra['ddd:ignore'] = True

@dddtask(path="/Ways/*")
def osm_groups_ways_default_material(obj, osm):
    """Assign asphalt as default material for ways."""
    obj = obj.material(ddd.mats.asphalt)
    return obj

@dddtask(path="/Ways/*")
def osm_groups_ways_default_data(obj, osm):
    """Sets default data for ways."""
    obj.extra['ddd:way:weight'] = 100  # Lowest
    obj.extra['ddd:way:lane_width'] = 3.3
    obj.extra['ddd:way:lane_width_right'] = 0.3  # Forward direction
    obj.extra['ddd:way:lane_width_left'] = 0.3  # Reverse direction

    # TODO: rename as ddd:augment: or whatever
    obj.extra['ddd:way:roadlines'] = False
    obj.extra['ddd:way:lamps'] = obj.extra.get('osm:lit', False)
    obj.extra['ddd:way:traffic_signals'] = False
    obj.extra['ddd:way:traffic_signs'] = False


@dddtask(path="/Ways/*", select='["osm:junction" = "roundabout"][!"osm:oneway"]')
def osm_groups_ways_roundabouts_oneway(obj, osm):
    """Mark roundabouts as one way roads by default."""
    obj.extra['osm:oneway'] = True


@dddtask(path="/Ways/*", select='["osm:footway" = "sidewalk"]')
def osm_groups_ways_footway_sidewalk_remove(obj, osm):
    """Remove sidewalks."""
    return False

@dddtask(path="/Ways/*", select='["osm:route"]')
def osm_groups_ways_routes_remove(obj, osm):
    """Remove routes."""
    return False


@dddtask(path="/Ways/*", select='["osm:highway" = "motorway"]')
def osm_groups_ways_motorway(obj, osm):
    """Define road data."""
    obj.extra['ddd:way:weight'] = 5
    obj.extra['ddd:way:lane_width'] = 3.6
    obj.extra['ddd:way:lane_width_right'] = 1.5
    obj.extra['ddd:way:lane_width_left'] = 0.8
    obj.extra['ddd:way:roadlines'] = True
    obj.prop_set('ddd:way:lanes', default=2)

@dddtask(path="/Ways/*", select='["osm:highway" = "motorway_link"]')
def osm_groups_ways_motorway_link(obj, osm):
    """Define road data."""
    #obj.extra['ddd:way:weight'] = 5
    obj.extra['ddd:way:lane_width'] = 3.6
    obj.extra['ddd:way:lane_width_right'] = 1.5
    obj.extra['ddd:way:lane_width_left'] = 0.8
    obj.extra['ddd:way:roadlines'] = True
    obj.prop_set('ddd:way:lanes', default=1)

@dddtask(path="/Ways/*", select='["osm:highway" = "trunk"]')
def osm_groups_ways_trunk(obj, osm):
    """Define road data."""
    obj.extra['ddd:way:weight'] = 10
    obj.extra['ddd:way:lane_width'] = 3.4
    obj.extra['ddd:way:lane_width_right'] = 1.4
    obj.extra['ddd:way:lane_width_left'] = 0.5
    obj.extra['ddd:way:roadlines'] = True
    obj.prop_set('ddd:way:lanes', default=2)

@dddtask(path="/Ways/*", select='["osm:highway" = "trunk_link"]')
def osm_groups_ways_trunk_link(obj, osm):
    """Define road data."""
    #obj.extra['ddd:way:weight'] = 10
    obj.extra['ddd:way:lane_width'] = 3.4
    obj.extra['ddd:way:lane_width_right'] = 1.4
    obj.extra['ddd:way:lane_width_left'] = 0.5
    obj.extra['ddd:way:roadlines'] = True
    obj.prop_set('ddd:way:lanes', default=1)

@dddtask(path="/Ways/*", select='["osm:highway" = "primary"]')
def osm_groups_ways_primary(obj, osm):
    """Define road data."""
    obj.extra['ddd:way:weight'] = 11
    obj.extra['ddd:way:lane_width'] = 3.4
    obj.extra['ddd:way:lane_width_right'] = 1.0
    obj.extra['ddd:way:lane_width_left'] = 0.5
    obj.extra['ddd:way:roadlines'] = True
    obj.prop_set('ddd:way:lanes', default=2)

@dddtask(path="/Ways/*", select='["osm:highway" = "primary_link"]')
def osm_groups_ways_primary_link(obj, osm):
    """Define road data."""
    #obj.extra['ddd:way:weight'] = 11
    obj.extra['ddd:way:lane_width'] = 3.4
    obj.extra['ddd:way:lane_width_right'] = 1.0
    obj.extra['ddd:way:lane_width_left'] = 0.5
    obj.extra['ddd:way:roadlines'] = True
    obj.prop_set('ddd:way:lanes', default=2)

@dddtask(path="/Ways/*", select='["osm:highway" = "secondary"]')
def osm_groups_ways_secondary(obj, osm):
    """Define road data."""
    obj.extra['ddd:way:weight'] = 12
    obj.extra['ddd:way:lane_width'] = 3.4
    obj.extra['ddd:way:roadlines'] = True
    obj.extra['ddd:way:traffic_signals'] = True
    obj.extra['ddd:way:traffic_signs'] = True
    obj.prop_set('ddd:way:lamps', default=True)

    lanes = 2 if obj.extra.get('osm:oneway', False) else 3
    obj.prop_set('ddd:way:lanes', default=lanes)

@dddtask(path="/Ways/*", select='["osm:highway" = "tertiary"]')
def osm_groups_ways_tertiary(obj, osm):
    """Define road data."""
    obj.extra['ddd:way:weight'] = 13
    obj.extra['ddd:way:lane_width'] = 3.4
    obj.extra['ddd:way:roadlines'] = True
    obj.extra['ddd:way:traffic_signals'] = True
    obj.extra['ddd:way:traffic_signs'] = True
    obj.prop_set('ddd:way:lamps', default=True)
    obj.prop_set('ddd:way:lanes', default=2)

@dddtask(path="/Ways/*", select='["osm:highway" = "road"]')
def osm_groups_ways_road(obj, osm):
    """Define road data."""
    obj.extra['ddd:way:weight'] = 14
    obj.extra['ddd:way:lane_width'] = 3.3
    obj.extra['ddd:way:roadlines'] = True
    obj.extra['ddd:way:traffic_signals'] = True
    obj.extra['ddd:way:traffic_signs'] = True
    obj.prop_set('ddd:way:lamps', default=True)
    obj.prop_set('ddd:way:lanes', default=2)


@dddtask(path="/Ways/*", select='["osm:highway" = "service"]')
def osm_groups_ways_service(obj, osm):
    """Define road data."""
    obj.extra['ddd:way:weight'] = 21
    obj.extra['ddd:way:roadlines'] = True
    obj.extra['ddd:way:traffic_signs'] = True
    obj.prop_set('ddd:way:lamps', default=True)
    obj.prop_set('ddd:way:lanes', default=1)

@dddtask(path="/Ways/*", select='["osm:highway" = "residential"]')
def osm_groups_ways_residential(obj, osm):
    """Define road data."""
    obj.extra['ddd:way:weight'] = 22
    obj.extra['ddd:way:roadlines'] = True
    obj.extra['ddd:way:traffic_signs'] = True
    obj.extra['ddd:way:traffic_signals'] = False
    obj.prop_set('ddd:way:lamps', default=True)

    lanes = 2 if obj.extra.get('osm:oneway', False) else 2
    obj.prop_set('ddd:way:lanes', default=lanes)

@dddtask(path="/Ways/*", select='["osm:highway" = "living_street"]')
def osm_groups_ways_living_street(obj, osm):
    """Define road data."""
    obj.extra['ddd:way:weight'] = 23
    obj.extra['ddd:way:lane_width'] = 0.3 * 1.2 if obj.extra.get('osm:oneway', False) else 0.3
    obj.extra['ddd:way:roadlines'] = True
    obj.extra['ddd:way:traffic_signs'] = True
    obj.extra['ddd:way:traffic_signals'] = False
    obj.prop_set('ddd:way:lamps', default=True)

    lanes = 1 if obj.extra.get('osm:oneway', False) else 2
    obj.prop_set('ddd:way:lanes', default=lanes)

@dddtask(path="/Ways/*", select='["osm:highway" = "track"]')
def osm_groups_ways_track(obj, osm):
    """Define road data."""
    obj.extra['ddd:way:weight'] = 26
    obj.extra['ddd:way:roadlines'] = False
    obj.extra['ddd:way:traffic_signs'] = True
    obj.extra['ddd:way:traffic_signals'] = False
    obj.prop_set('ddd:way:lamps', default=False)
    obj.prop_set('ddd:way:lanes', default=1)
    obj.extra['ddd:way:height'] = 0.2

@dddtask(path="/Ways/*", select='["osm:highway" = "footway"]')
def osm_groups_ways_footway(obj, osm):
    """Define road data."""
    obj.extra['ddd:way:weight'] = 31
    obj.extra['ddd:way:height'] = 0.2
    obj.extra['ddd:way:width'] = 1.5
    obj.extra['ddd:way:lanes'] = 0
    obj = obj.material(ddd.mats.dirt)
    return obj


@dddtask(path="/Ways/*", select='["osm:highway" = "path"]')
def osm_groups_ways_path(obj, osm):
    """Define road data."""
    obj.extra['ddd:way:lanes'] = 0
    obj.extra['ddd:way:weight'] = 31
    obj.extra['ddd:way:height'] = 0.2
    obj.extra['ddd:way:width'] = 1.5
    obj = obj.material(ddd.mats.dirt)

    # TODO: Do later, after applying elevations, in a select ("add fences to elevated ways")... improve
    obj.extra['ddd:way:elevated:border'] = 'fence'
    obj.extra['ddd:way:elevated:material'] = ddd.mats.pathwalk
    obj.extra['ddd:way:weight'] = 42

    return obj

@dddtask(path="/Ways/*", select='["osm:highway" ~ "steps|stairs"]')
def osm_groups_ways_stairs(obj, osm):
    """Define road data."""
    obj.extra['ddd:way:lanes'] = 0
    obj.extra['ddd:way:weight'] = 31
    obj.extra['ddd:way:height'] = 0.2
    obj.extra['ddd:way:width'] = 1.5
    obj = obj.material(ddd.mats.pathwalk)
    # TODO: Do later, after applying elevations, in a select ("add fences to elevated ways")... improve
    #obj.extra['ddd:way:elevated:border'] = 'fence'
    #obj.extra['ddd:way:elevated:material'] = ddd.mats.pathwalk
    #obj.extra['ddd:way:weight'] = 42
    return obj

@dddtask(path="/Ways/*", select='["osm:highway" = "pedestrian"]')
def osm_groups_ways_pedestrian(obj, osm):
    """Define road data."""
    obj.extra['ddd:way:lanes'] = 0
    obj.extra['ddd:way:weight'] = 32
    obj.extra['ddd:way:height'] = 0.2
    obj.extra['ddd:way:width'] = 6.60
    obj = obj.material(ddd.mats.pathwalk)
    obj.prop_set('ddd:way:lamps', default=True)
    return obj

@dddtask(path="/Ways/*", select='["osm:highway" = "cycleway"]')
def osm_groups_ways_cycleway(obj, osm):
    """Define road data."""
    obj.extra['ddd:way:lanes'] = 1
    obj.extra['ddd:way:lane_width'] = 1.5
    obj.extra['ddd:way:weight'] = 10
    #obj.extra['ddd:way:height'] = 0.2
    obj.extra['ddd:way:roadlines'] = True
    obj = obj.material(ddd.mats.pitch_blue)
    obj.prop_set('ddd:way:lamps', default=True)
    return obj

@dddtask(path="/Ways/*", select='["osm:highway" = "corridor"]')
def osm_groups_ways_corridor(obj, osm):
    """Define road data."""
    obj.extra['ddd:way:lanes'] = 0
    obj.extra['ddd:way:width'] = 2.2
    obj.extra['ddd:way:weight'] = 41
    obj.extra['ddd:way:height'] = 0.35
    obj = obj.material(ddd.mats.pathwalk)
    return obj

@dddtask(path="/Ways/*", select='["osm:highway" = "unclassified"]')
def osm_groups_ways_unclassified(obj, osm):
    """Define road data."""
    obj.extra['ddd:way:lanes'] = 1
    obj = obj.material(ddd.mats.dirt)
    return obj

@dddtask(path="/Ways/*", select='["osm:highway" = "raceway"]')
def osm_groups_ways_raceway(obj, osm):
    """Define road data."""
    obj.extra['ddd:way:lanes'] = 1
    obj.extra['ddd:way:width'] = 8.0
    #obj = obj.material(ddd.mats.dirt)

@dddtask(path="/Ways/*", select='["osm:highway" = "raceway"]')
def osm_groups_ways_railway(obj, osm):
    """Define road data."""
    obj.name = "Railway: %s" % obj.name
    obj.extra['ddd:way:lanes'] = 0
    obj.extra['ddd:way:width'] = 3.6
    obj = obj.material(ddd.mats.dirt)
    return obj


'''
def generate_way_1d(feature):


    width = None  # if not set will be discarded
    extra_height = 0.0
    lanes = None
    layer = None
    create_as_item = False

    if path.extra.get('osm:highway', None) in (None):
        return None


    elif path.extra.get('osm:natural', None) == "coastline":
        lanes = None
        name = "Coastline: %s" % name_id
        create_as_item = True
        width = 0.01
        material = ddd.mats.terrain
        #extra_height = 5.0  # FIXME: Things could cross othis, height shall reach sea precisely

    elif path.extra.get('osm:waterway', None) == "river":
        lanes = None
        name = "River: %s" % name_id
        width = 6.0
        material = ddd.mats.sea
        path.extra['ddd:area:type'] = 'water'
        path.extra['ddd:baseheight'] = -0.5
    elif path.extra.get('osm:waterway', None) == "stream":
        lanes = None
        name = "Stream: %s" % name_id
        width = 3.5
        material = ddd.mats.sea
        path.extra['ddd:area:type'] = 'water'
        path.extra['ddd:baseheight'] = -0.5


    elif path.extra.get('osm:barrier', None) == 'city_wall':
        width = 1.0
        material = ddd.mats.stone
        extra_height = 2.0
        name = "City Wall: %s" % name_id
        path.extra['ddd:subtract_buildings'] = True
    elif path.extra.get('osm:historic', None) == 'castle_wall':
        width = 3.0
        material = ddd.mats.stone
        extra_height = 3.5
        name = "Castle Wall: %s" % name_id
        path.extra['ddd:subtract_buildings'] = True

    elif path.extra.get('osm:barrier', None)== 'hedge':
        width = 0.6
        lanes = None
        material = ddd.mats.treetop
        extra_height = 1.2
        create_as_item = True
        name = "Hedge: %s" % name_id
        path.extra['ddd:subtract_buildings'] = True

    elif path.extra.get('osm:barrier', None) == 'fence':
        width = 0.05
        lanes = None
        material = ddd.mats.fence
        extra_height = 1.2
        create_as_item = True
        name = "Fence: %s" % name_id
        path.extra['ddd:subtract_buildings'] = True

    elif path.extra.get('osm:kerb', None) == 'kerb':
        logger.debug("Ignoring kerb")
        return None

    elif path.extra.get('osm:man_made', None) == 'pier':
        width = 1.8
        material = ddd.mats.wood

    elif path.extra.get('osm:barrier', None) == 'retaining_wall':
        width = 0.7
        material = ddd.mats.stone
        extra_height = 1.5
        name = "Wall Retaining: %s" % name_id
        path.extra['ddd:subtract_buildings'] = True
    elif path.extra.get('osm:barrier', None) == 'wall':
        # TODO: Get height and material from metadata
        width = 0.35
        material = ddd.mats.bricks
        extra_height = 1.8
        name = "Wall: %s" % name_id
        path.extra['ddd:subtract_buildings'] = True

    elif path.extra.get('osm:power', None) == 'line':
        width = 0.1
        material = ddd.mats.steel
        layer = "3"
        create_as_item = True

    elif path.extra.get('osm:highway', None):
        logger.info("Unknown highway type: %s (%s)", path.extra.get('osm:highway', None), path.extra)
        lanes = 2.0

    else:
        logger.debug("Unknown way (discarding): %s", path.extra)
        return None


    # Calculated properties

    flanes = path.extra.get('osm:lanes', None)
    if flanes:
        lanes = int(float(flanes))

    lanes = int(lanes) if lanes is not None else None
    if lanes is None or lanes < 1:
        roadlines = False

    if width is None:
        try:
            if lanes == 1: lane_width = lane_width * 1.25
            width = lanes * lane_width + lane_width_left + lane_width_right
        except Exception as e:
            logger.error("Cannot calculate width from lanes: %s", feature['properties'])
            raise

    return path
'''


@dddtask(order="30.30.50.+", path="/Ways/*")
def osm_groups_ways_calculated(osm):
    # TODO: Tag identified ways
    pass

@dddtask(path="/Ways/*")
def osm_groups_ways_calculated_discard_untagged(osm):
    # TODO: Tag identified ways
    pass

@dddtask(path="/Ways/*", select='["osm:junction" = "roundabout"]')
def osm_groups_ways_calculated_roundabout_weight(obj):
    obj.extra['ddd:way:weight'] = 1

@dddtask(path="/Ways/*", select='["osm:oneway"]')
def osm_groups_ways_calculated_oneway_lane_margins(obj):
    obj.extra['ddd:way:lane_width_left'] = obj.extra['ddd:way:lane_width_right']

@dddtask(path="/Ways/*")
def osm_groups_ways_calculated_data(obj, osm):
    """Sets calculated data for ways."""

    # Use osm:lanes if set, otherwise use lanes
    obj.extra['ddd:way:lanes'] = int(obj.extra.get('osm:lanes', obj.extra.get('ddd:way:lanes', 0)))
    if obj.extra['ddd:way:lanes'] < 1: obj.extra['ddd:way:lanes'] = 1

    if obj.extra.get('ddd:way:width', None) is None:
        obj.extra['ddd:way:width'] = (obj.extra['ddd:way:lanes'] * obj.extra['ddd:way:lane_width'] +
                                      obj.extra['ddd:way:lane_width_left'] + obj.extra['ddd:way:lane_width_right'])

    # TODO: use these generic attribs? possibly avoid
    obj.extra['ddd:height'] = obj.extra.get('ddd:way:height', None)
    obj.extra['ddd:extra_height'] = obj.extra['ddd:height']
    obj.extra['ddd:width'] = obj.extra['ddd:way:width']

    #path.extra['ddd:item'] = create_as_item
    #path.extra['ddd:item:height'] = extra_height

