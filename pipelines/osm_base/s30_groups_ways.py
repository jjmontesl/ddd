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

@dddtask(order="30.30.20.+", path="/Ways/*")
def osm_groups_ways_defaults(obj, osm):

    # Set name
    name = "Way: " + (obj.extra.get('osm:name', obj.extra.get('osm:id')))
    obj.name = name

@dddtask(order="30.30.20.+", path="/Ways/*", select='["osm:junction"="roundabout"][!"osm:oneway"]')
def osm_groups_ways_roundabouts_oneway(obj, osm):
    """Mark roundabouts as one way roads by default."""
    obj.extra['osm:oneway'] = True

@dddtask(order="30.30.20.+", path="/Ways/*")
def osm_groups_ways_asphalt(obj, osm):
    """Mark roundabouts as one way roads by default."""
    obj = obj.material(ddd.mats.asphalt)
    return obj




def generate_way_1d(feature):


    width = None  # if not set will be discarded
    material = ddd.mats.asphalt
    extra_height = 0.0
    lanes = None
    lamps = False
    traffic_signals = False
    roadlines = False
    path.extra['ddd:way:weight'] = 100  # Lowest

    layer = None

    lane_width = 3.3
    lane_width_right = 0.30
    lane_width_left = 0.30

    create_as_item = False

    if path.extra.get('osm:highway', None) in ('proposed', 'construction', ):
        return None

    elif path.extra.get('osm:highway', None) == "motorway":
        lane_width = 3.6
        lane_width_right = 1.5
        lane_width_left = 0.8
        lanes = 2
        roadlines = True
        path.extra['ddd:way:weight'] = 5
    elif path.extra.get('osm:highway', None) == "motorway_link":
        lanes = 1
        lane_width = 3.6
        lane_width_right = 1.5
        lane_width_left = 0.8
        roadlines = True
    elif path.extra.get('osm:highway', None) == "trunk":
        lanes = 1
        lane_width = 3.4
        lane_width_right = 1.4
        lane_width_left = 0.5
        roadlines = True
        path.extra['ddd:way:weight'] = 10
    elif path.extra.get('osm:highway', None) == "trunk_link":
        lanes = 1
        lane_width = 3.4
        lane_width_right = 1.4
        lane_width_left = 0.5
        roadlines = True

    elif path.extra.get('osm:highway', None) == "primary":
        lanes = 2
        lane_width = 3.4
        lane_width_right = 1.0
        lane_width_left = 0.5
        roadlines = True
        path.extra['ddd:way:weight'] = 11
    elif path.extra.get('osm:highway', None) == "primary_link":
        lanes = 2
        lane_width = 3.4
        lane_width_right = 1.0
        lane_width_left = 0.5
        roadlines = True
    elif path.extra.get('osm:highway', None) == "secondary":
        lanes = 2 if path.extra.get('osm:oneway', False) else 3
        lane_width = 3.4
        lamps = True
        traffic_signals = True
        roadlines = True
        path.extra['ddd:way:weight'] = 12
    elif path.extra.get('osm:highway', None) in ("tertiary", "road"):
        lanes = 2
        lane_width = 3.4
        lamps = True  # shall be only in city?
        traffic_signals = True
        roadlines = True
        path.extra['ddd:way:weight'] = 13
    elif path.extra.get('osm:highway', None) == "service":
        lanes = 1
        lamps = True  # shall be only in city?
        roadlines = True
        path.extra['ddd:way:weight'] = 21
    elif path.extra.get('osm:highway', None) in ("residential", ):
        # lanes = 1.0  # Using 1 lane for residential/living causes too small roads
        lanes = 2 if path.extra.get('osm:oneway', False) else 2
        lamps = path.extra.get('osm:lit', True)  # shall be only in city?
        traffic_signals = True
        roadlines = True
        path.extra['ddd:way:weight'] = 22
    elif path.extra.get('osm:highway', None) in ("living_street", ):
        # extra_height = 0.1
        lanes = 1 if path.extra.get('osm:oneway', False) else 2
        lane_width = lane_width * 1.2 if path.extra.get('osm:oneway', False) else lane_width
        lamps = path.extra.get('osm:lit', True)  # shall be only in city?
        traffic_signals = False
        roadlines = True
        path.extra['ddd:way:weight'] = 23

    elif path.extra.get('osm:highway', None) in ("track", ):
        lanes = 1
        material = ddd.mats.asphalt
        extra_height = 0.2  # TODO: Curve along, add noise, add "roderas" inside, add roderas/merge outside...
        roadlines = False
        traffic_signals = True  # put signals, not lights
        lamps = path.extra.get('osm:lit', False)  # shall be only in city?
        path.extra['ddd:way:weight'] = 26

    elif path.extra.get('osm:highway', None) in ("footway",):
        if path.extra.get('osm:footway', None) == 'sidewalk': return None  # Dropping sidewalks!
        lanes = 0
        material = ddd.mats.dirt
        extra_height = 0.0
        width = 0.6 * 3.3
        path.extra['ddd:way:weight'] = 31
    elif path.extra.get('osm:highway', None) in ("path", ):
        lanes = 0
        material = ddd.mats.dirt
        # extra_height = 0.2
        width = 0.6 * 3.3

        # TODO: Do later, after applying elevations, in a select ("add fences to elevated ways")
        path.extra['ddd:way:elevated:border'] = 'fence'
        path.extra['ddd:way:elevated:material'] = ddd.mats.pathwalk
        path.extra['ddd:way:weight'] = 42


    elif path.extra.get('osm:highway', None) in ("steps", "stairs"):
        lanes = 0
        material = ddd.mats.pathwalk
        extra_height = 0.2  # 0.2 allows easy car driving
        width = 0.6 * 3.3
        path.extra['ddd:way:weight'] = 31
    elif path.extra.get('osm:highway', None) == "pedestrian":
        lanes = 0
        material = ddd.mats.pathwalk
        extra_height = 0.2
        width = 2 * 3.30
        lamps = True  # shall be only in city?
        path.extra['ddd:way:weight'] = 32

    elif path.extra.get('osm:highway', None) == "cycleway":
        lanes = 1
        lane_width = 1.5
        material = ddd.mats.pitch_blue
        #extra_height = 0.0
        roadlines = True
        path.extra['ddd:way:weight'] = 10
    elif path.extra.get('osm:highway', None) == "corridor":
        lanes = 0
        material = ddd.mats.pathwalk
        extra_height = 0.35  # 0.2 allows easy car driving
        width = 2.2
        path.extra['ddd:way:weight'] = 41

    elif path.extra.get('osm:highway', None) == "unclassified":
        lanes = 1
        material = ddd.mats.dirt

    elif path.extra.get('osm:highway', None) == "raceway":
        lanes = 1
        lane_width = 10.0
        material = ddd.mats.dirt
        # extra_height = 0.2

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

    elif path.extra.get('osm:railway', None):
        lanes = None
        width = 3.6
        material = ddd.mats.dirt
        name = "Railway: %s" % name_id
        #extra_height = 0.0

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

    elif path.extra.get('osm:route', None):
        # Ignore routes
        return None

    elif path.extra.get('osm:highway', None):
        logger.info("Unknown highway type: %s (%s)", path.extra.get('osm:highway', None), path.extra)
        lanes = 2.0

    else:
        logger.debug("Unknown way (discarding): %s", path.extra)
        return None

    # Calculated properties
    if path.extra.get('osm:junction', None) == "roundabout":
        path.extra['ddd:way:weight'] = 1

    flanes = path.extra.get('osm:lanes', None)
    if flanes:
        lanes = int(float(flanes))

    lanes = int(lanes) if lanes is not None else None
    if lanes is None or lanes < 1:
        roadlines = False

    if not path.extra.get('osm:oneway', None):
        lane_width_left = lane_width_right

    if width is None:
        try:
            if lanes == 1: lane_width = lane_width * 1.25
            width = lanes * lane_width + lane_width_left + lane_width_right
        except Exception as e:
            logger.error("Cannot calculate width from lanes: %s", feature['properties'])
            raise

    path = path.material(material)
    path.name = name

    '''
    path.extra['osm:highway'] = highway
    path.extra['osm:barrier'] = barrier
    path.extra['osm:railway'] = railway
    path.extra['osm:historic'] = historic
    path.extra['osm:natural'] = natural
    path.extra['osm:tunnel'] = tunnel
    path.extra['osm:bridge'] = bridge
    path.extra['osm:junction'] = junction
    path.extra['osm:waterway'] = waterway
    path.extra['osm:lanes'] = lanes
    '''
    path.extra['ddd:layer'] = layer if layer is not None else path.extra['osm:layer']
    path.extra['ddd:extra_height'] = extra_height
    path.extra['ddd:width'] = width
    path.extra['ddd:height'] = extra_height
    path.extra['ddd:way:width'] = width
    path.extra['ddd:way:lanes'] = lanes
    path.extra['ddd:way:lane_width'] = lane_width
    path.extra['ddd:way:lane_width_left'] = lane_width_left
    path.extra['ddd:way:lane_width_right'] = lane_width_right
    path.extra['ddd:way:augment_lamps'] = lamps  # Add via augmenting as well, adding metadata for this shall be avoided
    path.extra['ddd:way:augment_traffic_signals'] = traffic_signals  # Add via augmenting pipeline, do not add nmetadata here or avoid metadat if possible
    path.extra['ddd:way:roadlines'] = roadlines  # should be ddd:road:roadlines ?
    path.extra['ddd:item'] = create_as_item
    path.extra['ddd:item:height'] = extra_height
    # print(feature['properties'].get("name", None))

    return path