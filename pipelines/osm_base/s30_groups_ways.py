# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020

from ddd.ddd import ddd
from ddd.osm import osm
from ddd.pipeline.decorators import dddtask



@dddtask(order="30.30.10.+", log=True)
def osm_select_ways(root):

    # Split and junctions first?
    # Possibly: metadata can depend on that, and it needs to be done if it will be done anyway

    # Otherwise: do a pre and post step, and do most things in post (everything not needed for splitting)
    pass


@dddtask(path="/Features/*", select='["geom:type"="LineString"]')
def osm_select_ways_default_name(obj, root):
    """Set way default data."""
    name = (obj.extra.get('osm:name', obj.extra.get('osm:id')))
    obj.name = name


# OSM normalization (sensible defaults)

@dddtask(path="/Features/*", select='["osm:junction" = "roundabout"][!"osm:oneway"]')
def osm_select_ways_roundabouts_oneway(obj, root):
    """Mark roundabouts as one way roads by default."""
    obj.extra['osm:oneway'] = True



'''
@dddtask(path="/Ways/*", select='["osm:footway" = "sidewalk"]')
def osm_select_ways_footway_sidewalk_remove(obj, root):
    """Remove sidewalks."""
    return False

@dddtask(path="/Ways/*", select='["osm:route"]')
def osm_select_ways_routes_remove(obj, root):
    """Remove routes."""
    return False
'''


@dddtask(path="/Features/*", select='["geom:type"="LineString"]["osm:highway" = "motorway"]')
def osm_select_ways_motorway(obj, root):
    """Define road data."""
    obj = obj.copy()
    obj.extra['ddd:way:weight'] = 5
    obj.extra['ddd:way:lane_width'] = 3.6
    obj.extra['ddd:way:lane_width_right'] = 1.5
    obj.extra['ddd:way:lane_width_left'] = 0.8
    obj.extra['ddd:way:roadlines'] = True
    obj.prop_set('ddd:way:lanes', default=2)
    root.find("/Ways").append(obj)


@dddtask(path="/Features/*", select='["geom:type"="LineString"]["osm:highway"="motorway_link"]')
def osm_select_ways_motorway_link(obj, root):
    """Define road data."""
    obj = obj.copy()
    # obj.extra['ddd:way:weight'] = 5
    obj.extra['ddd:way:lane_width'] = 3.6
    obj.extra['ddd:way:lane_width_right'] = 1.5
    obj.extra['ddd:way:lane_width_left'] = 0.8
    obj.extra['ddd:way:roadlines'] = True
    obj.prop_set('ddd:way:lanes', default=1)
    root.find("/Ways").append(obj)

@dddtask(path="/Features/*", select='["geom:type"="LineString"]["osm:highway" = "trunk"]')
def osm_select_ways_trunk(obj, root):
    """Define road data."""
    obj = obj.copy()
    obj.extra['ddd:way:weight'] = 10
    obj.extra['ddd:way:lane_width'] = 3.4
    obj.extra['ddd:way:lane_width_right'] = 1.0
    obj.extra['ddd:way:lane_width_left'] = 0.5
    obj.extra['ddd:way:roadlines'] = True
    obj.prop_set('ddd:way:lanes', default=2)
    root.find("/Ways").append(obj)

@dddtask(path="/Features/*", select='["geom:type"="LineString"]["osm:highway" = "trunk_link"]')
def osm_select_ways_trunk_link(obj, root):
    """Define road data."""
    obj = obj.copy()
    # obj.extra['ddd:way:weight'] = 10
    obj.extra['ddd:way:lane_width'] = 3.4
    obj.extra['ddd:way:lane_width_right'] = 1.0
    obj.extra['ddd:way:lane_width_left'] = 0.5
    obj.extra['ddd:way:roadlines'] = True
    obj.prop_set('ddd:way:lanes', default=1)
    root.find("/Ways").append(obj)

@dddtask(path="/Features/*", select='["geom:type"="LineString"]["osm:highway" = "primary"]')
def osm_select_ways_primary(obj, root):
    """Define road data."""
    obj = obj.copy()
    obj.extra['ddd:way:weight'] = 11
    obj.extra['ddd:way:lane_width'] = 3.4
    obj.extra['ddd:way:lane_width_right'] = 1.0
    obj.extra['ddd:way:lane_width_left'] = 0.5
    obj.extra['ddd:way:roadlines'] = True
    obj.prop_set('ddd:way:lanes', default=2)
    root.find("/Ways").append(obj)

@dddtask(path="/Features/*", select='["geom:type"="LineString"]["osm:highway" = "primary_link"]')
def osm_select_ways_primary_link(obj, root):
    """Define road data."""
    obj = obj.copy()
    # obj.extra['ddd:way:weight'] = 11
    obj.extra['ddd:way:lane_width'] = 3.4
    obj.extra['ddd:way:lane_width_right'] = 1.0
    obj.extra['ddd:way:lane_width_left'] = 0.5
    obj.extra['ddd:way:roadlines'] = True

    lanes = 1 if obj.extra.get('osm:oneway', False) else 2
    obj.prop_set('ddd:way:lanes', default=lanes)
    root.find("/Ways").append(obj)

@dddtask(path="/Features/*", select='["geom:type"="LineString"]["osm:highway" = "secondary"]')
def osm_select_ways_secondary(obj, root):
    """Define road data."""
    obj = obj.copy()
    obj.extra['ddd:way:weight'] = 12
    obj.extra['ddd:way:lane_width'] = 3.4
    obj.extra['ddd:way:roadlines'] = True
    obj.extra['ddd:way:traffic_signals'] = True
    obj.extra['ddd:way:traffic_signs'] = True
    obj.prop_set('ddd:way:lamps', default=True)

    lanes = 2 if obj.extra.get('osm:oneway', False) else 3
    obj.prop_set('ddd:way:lanes', default=lanes)
    root.find("/Ways").append(obj)

@dddtask(path="/Features/*", select='["geom:type"="LineString"]["osm:highway" = "tertiary"]')
def osm_select_ways_tertiary(obj, root):
    """Define road data."""
    obj = obj.copy()
    obj.extra['ddd:way:weight'] = 13
    obj.extra['ddd:way:lane_width'] = 3.4
    obj.extra['ddd:way:roadlines'] = True
    obj.extra['ddd:way:traffic_signals'] = True
    obj.extra['ddd:way:traffic_signs'] = True
    obj.prop_set('ddd:way:lamps', default=True)
    obj.prop_set('ddd:way:lanes', default=2)
    root.find("/Ways").append(obj)

@dddtask(path="/Features/*", select='["geom:type"="LineString"]["osm:highway" = "road"]')
def osm_select_ways_road(obj, root):
    """Define road data."""
    obj = obj.copy()
    obj.extra['ddd:way:weight'] = 14
    obj.extra['ddd:way:lane_width'] = 3.3
    obj.extra['ddd:way:roadlines'] = True
    obj.extra['ddd:way:traffic_signals'] = True
    obj.extra['ddd:way:traffic_signs'] = True
    obj.prop_set('ddd:way:lamps', default=True)
    obj.prop_set('ddd:way:lanes', default=2)
    root.find("/Ways").append(obj)

@dddtask(path="/Features/*", select='["geom:type"="LineString"]["osm:highway" = "service"]')
def osm_select_ways_service(obj, root):
    """Define road data."""
    obj = obj.copy()
    obj.extra['ddd:way:weight'] = 21
    obj.extra['ddd:way:roadlines'] = True
    obj.extra['ddd:way:traffic_signs'] = True
    obj.prop_set('ddd:way:lamps', default=True)
    obj.prop_set('ddd:way:lanes', default=1)
    root.find("/Ways").append(obj)

@dddtask(path="/Features/*", select='["geom:type"="LineString"]["osm:highway" = "residential"]')
def osm_select_ways_residential(obj, root):
    """Define road data."""
    obj = obj.copy()
    obj.extra['ddd:way:weight'] = 22
    obj.extra['ddd:way:roadlines'] = True
    obj.extra['ddd:way:traffic_signs'] = True
    obj.extra['ddd:way:traffic_signals'] = False
    obj.prop_set('ddd:way:lamps', default=True)

    lanes = 2 if obj.extra.get('osm:oneway', False) else 2
    obj.prop_set('ddd:way:lanes', default=lanes)
    root.find("/Ways").append(obj)

@dddtask(path="/Features/*", select='["geom:type"="LineString"]["osm:highway" = "living_street"]')
def osm_select_ways_living_street(obj, root):
    """Define road data."""
    obj = obj.copy()
    obj.extra['ddd:way:weight'] = 23
    obj.extra['ddd:way:roadlines'] = True
    obj.extra['ddd:way:traffic_signs'] = True
    obj.extra['ddd:way:traffic_signals'] = False
    obj.prop_set('ddd:way:lamps', default=True)

    lanes = 1 if obj.extra.get('osm:oneway', False) else 2
    obj.extra['ddd:way:lane_width'] = 3.2 * 1.2 if lanes == 1 else 3.0
    obj.prop_set('ddd:way:lanes', default=lanes)
    root.find("/Ways").append(obj)

@dddtask(path="/Features/*", select='["geom:type"="LineString"]["osm:highway" = "track"]')
def osm_select_ways_track(obj, root):
    """Define road data."""
    obj = obj.copy()
    obj.extra['ddd:way:weight'] = 26
    obj.extra['ddd:way:roadlines'] = False
    obj.extra['ddd:way:traffic_signs'] = True
    obj.extra['ddd:way:traffic_signals'] = False
    obj.prop_set('ddd:way:lamps', default=False)
    obj.prop_set('ddd:way:lanes', default=1)
    obj.extra['ddd:way:height'] = 0 #0.2
    root.find("/Ways").append(obj)


@dddtask(path="/Features/*", select='["geom:type"="LineString"]["osm:highway" = "footway"]')
def osm_select_ways_footway(obj, root):
    """Define road data."""
    obj = obj.copy()
    obj.extra['ddd:way:weight'] = 31
    obj.extra['ddd:way:height'] = 0.2
    obj.extra['ddd:way:width'] = 1.5
    obj.extra['ddd:way:lanes'] = 0
    obj = obj.material(ddd.mats.dirt)
    root.find("/Ways").append(obj)

@dddtask(path="/Features/*", select='["geom:type"="LineString"]["osm:highway" = "path"]')
def osm_select_ways_path(obj, root):
    """Define road data."""
    obj = obj.copy()
    obj.extra['ddd:way:lanes'] = 0
    obj.extra['ddd:way:weight'] = 31
    #obj.extra['ddd:way:height'] = 0
    obj.extra['ddd:way:width'] = 1.5
    obj = obj.material(ddd.mats.dirt)

    # TODO: Do later, after applying elevations, in a select ("add fences to elevated ways")... improve
    obj.extra['ddd:way:elevated:border'] = 'fence'
    obj.extra['ddd:way:elevated:material'] = ddd.mats.pathwalk
    obj.extra['ddd:way:weight'] = 42

    root.find("/Ways").append(obj)


@dddtask(path="/Features/*", select='["geom:type"="LineString"]["osm:highway" ~ "steps|stairs"]')
def osm_select_ways_stairs(obj, root):
    """Define road data."""
    obj = obj.copy()
    obj.extra['ddd:way:lanes'] = 0
    obj.extra['ddd:way:weight'] = 31
    obj.extra['ddd:way:height'] = 0.2
    obj.extra['ddd:way:width'] = 1.5
    obj.extra['ddd:way:stairs'] = True
    obj.extra['ddd:area:type'] = "stairs"
    obj = obj.material(ddd.mats.pathwalk)
    # TODO: Do later, after applying elevations, in a select ("add fences to elevated ways")... improve
    # obj.extra['ddd:way:elevated:border'] = 'fence'
    # obj.extra['ddd:way:elevated:material'] = ddd.mats.pathwalk
    # obj.extra['ddd:way:weight'] = 42
    root.find("/Ways").append(obj)


@dddtask(path="/Features/*", select='["geom:type"="LineString"]["osm:highway" = "pedestrian"]')
def osm_select_ways_pedestrian(obj, root):
    """Define road data."""
    obj = obj.copy()
    obj.extra['ddd:way:lanes'] = 0
    obj.extra['ddd:way:weight'] = 32
    obj.extra['ddd:way:height'] = 0.2
    obj.extra['ddd:way:width'] = 6.60
    obj = obj.material(ddd.mats.pathwalk)
    obj.prop_set('ddd:way:lamps', default=True)
    root.find("/Ways").append(obj)


@dddtask(path="/Features/*", select='["geom:type"="LineString"]["osm:highway" = "cycleway"]')
def osm_select_ways_cycleway(obj, root):
    """Define road data."""
    obj = obj.copy()
    obj.extra['ddd:way:lanes'] = 1
    obj.extra['ddd:way:lane_width'] = 1.5
    obj.extra['ddd:way:weight'] = 10
    # obj.extra['ddd:way:height'] = 0.2
    obj.extra['ddd:way:roadlines'] = True
    obj = obj.material(ddd.mats.pitch_blue)
    obj.prop_set('ddd:way:lamps', default=True)
    root.find("/Ways").append(obj)


@dddtask(path="/Features/*", select='["geom:type"="LineString"]["osm:highway" = "corridor"]')
def osm_select_ways_corridor(obj, root):
    """Define road data."""
    obj = obj.copy()
    obj.extra['ddd:way:lanes'] = 0
    obj.extra['ddd:way:width'] = 2.2
    obj.extra['ddd:way:weight'] = 41
    obj.extra['ddd:way:height'] = 0.35
    obj = obj.material(ddd.mats.pathwalk)
    root.find("/Ways").append(obj)

@dddtask(path="/Features/*", select='["geom:type"="LineString"]["osm:highway" = "unclassified"]')
def osm_select_ways_unclassified(obj, root):
    """Define road data."""
    obj = obj.copy()
    obj.extra['ddd:way:lanes'] = 1
    obj = obj.material(ddd.mats.dirt)
    root.find("/Ways").append(obj)


@dddtask(path="/Features/*", select='["geom:type"="LineString"]["osm:highway" = "raceway"]')
def osm_select_ways_raceway(obj, root):
    """Define road data."""
    obj = obj.copy()
    obj.extra['ddd:way:lanes'] = 1
    obj.extra['ddd:way:width'] = 8.0
    # obj = obj.material(ddd.mats.dirt)
    root.find("/Ways").append(obj)

@dddtask(path="/Features/*", select='["geom:type"="LineString"]["osm:highway" = "raceway"]')
def osm_select_ways_railway(obj, root):
    """Define road data."""
    obj = obj.copy()
    obj.name = "Railway: %s" % obj.name
    obj.extra['ddd:way:lanes'] = 0
    obj.extra['ddd:way:width'] = 3.6
    obj = obj.material(ddd.mats.dirt)
    root.find("/Ways").append(obj)


@dddtask(path="/Features/*", select='["geom:type"="LineString"]["osm:waterway" = "river"]')
def osm_select_ways_waterway_river(obj, root):
    """Define item data."""
    obj = obj.copy()
    obj.name = "River: %s" % obj.name
    obj.extra['ddd:way:lanes'] = None
    obj.extra['ddd:way:width'] = 6.0
    obj.extra['ddd:area:type'] = "water"
    # obj.extra['ddd:baseheight'] = -0.5
    obj = obj.material(ddd.mats.sea)
    root.find("/Ways").append(obj)

@dddtask(path="/Features/*", select='["geom:type"="LineString"]["osm:waterway" = "canal"]')
def osm_select_ways_waterway_canal(obj, root):
    """Define item data."""
    obj = obj.copy()
    obj.name = "Canal: %s" % obj.name
    obj.extra['ddd:way:lanes'] = None
    obj.extra['ddd:way:width'] = 3.0
    obj.extra['ddd:area:type'] = "water"
    # obj.extra['ddd:baseheight'] = -0.5
    obj = obj.material(ddd.mats.sea)
    root.find("/Ways").append(obj)

@dddtask(path="/Features/*", select='["geom:type"="LineString"]["osm:waterway" = "stream"]')
def osm_select_ways_waterway_stream(obj, root):
    """Define item data."""
    obj = obj.copy()
    obj.name = "Stream: %s" % obj.name
    obj.extra['ddd:way:lanes'] = None
    obj.extra['ddd:way:width'] = 3.5
    obj.extra['ddd:area:type'] = "water"
    # obj.extra['ddd:baseheight'] = -0.5
    obj = obj.material(ddd.mats.sea)
    root.find("/Ways").append(obj)


@dddtask(path="/Features/*", select='["geom:type"="LineString"]["osm:barrier" = "retaining_wall"]')
def osm_select_ways_barrier_retaining_wall(root, osm, obj):
    """Define item data."""
    obj = obj.copy()
    obj.name = "Retaining Wall: %s" % obj.name
    #obj.extra['ddd:way:weight'] = 90
    #obj.extra['ddd:way:lanes'] = None
    obj.extra['ddd:width'] = float(obj.extra.get('osm:width', 0.50))
    obj.extra['ddd:height'] = float(obj.extra.get('osm:height', 1.4))
    obj.extra['ddd:min_height'] = float(obj.extra.get('osm:min_height', 0.0))
    obj.extra['ddd:subtract_buildings'] = True
    obj = obj.material(ddd.mats.stone)
    root.find("/ItemsWays").append(obj)

@dddtask(path="/Features/*", select='["geom:type"="LineString"]["osm:barrier" = "wall"]')
def osm_select_ways_barrier_wall(root, osm, obj):
    """Define item data."""
    obj = obj.copy()
    obj.name = "Wall: %s" % obj.name
    #obj.extra['ddd:way:weight'] = 91
    #obj.extra['ddd:way:lanes'] = None
    obj.extra['ddd:width'] = float(obj.extra.get('osm:width', 0.35))
    obj.extra['ddd:height'] = float(obj.extra.get('osm:height', 1.8))
    obj.extra['ddd:min_height'] = float(obj.extra.get('osm:min_height', 0.0))
    obj.extra['ddd:subtract_buildings'] = True
    obj = obj.material(ddd.mats.bricks)
    root.find("/ItemsWays").append(obj)

@dddtask(path="/Features/*", select='["geom:type"="LineString"]["osm:barrier" = "city_wall"]')
def osm_select_ways_barrier_city_wall(root, osm, obj):
    """Define item data."""
    obj = obj.copy()
    obj.name = "City Wall: %s" % obj.name
    #obj.extra['ddd:way:weight'] = 91
    #obj.extra['ddd:way:lanes'] = None
    obj.extra['ddd:width'] = float(obj.extra.get('osm:width', 1.00))
    obj.extra['ddd:height'] = float(obj.extra.get('osm:height', 2.0))
    obj.extra['ddd:min_height'] = float(obj.extra.get('osm:min_height', 0.0))
    obj.extra['ddd:subtract_buildings'] = True
    obj = obj.material(ddd.mats.stone)
    root.find("/ItemsWays").append(obj)

@dddtask(path="/Features/*", select='["geom:type"="LineString"](["osm:barrier" = "castle_wall"];["osm:historic" = "castle_wall"])')
def osm_select_ways_barrier_castle_wall(root, osm, obj):
    """Define item data."""
    obj = obj.copy()
    obj.name = "Castle Wall: %s" % obj.name
    #obj.extra['ddd:way:weight'] = 91
    #obj.extra['ddd:way:lanes'] = None
    obj.extra['ddd:width'] = float(obj.extra.get('osm:width', 3.00))
    obj.extra['ddd:height'] = float(obj.extra.get('osm:height', 3.5))
    obj.extra['ddd:min_height'] = float(obj.extra.get('osm:min_height', 0.0))
    obj.extra['ddd:subtract_buildings'] = True
    obj = obj.material(ddd.mats.stone)
    root.find("/ItemsWays").append(obj)


'''
def generate_way_1d(feature):

    create_as_item = False

    elif path.extra.get('osm:man_made', None) == 'pier':
        width = 1.8
        material = ddd.mats.wood


    elif path.extra.get('osm:power', None) == 'line':
        width = 0.1
        material = ddd.mats.steel
        layer = "3"
        create_as_item = True

    elif path.extra.get('osm:kerb', None) == 'kerb':
        logger.debug("Ignoring kerb")
        return None
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




@dddtask(order="30.30.40.+", path="/Ways/*")
def osm_select_ways_default_data(obj, root):
    """Sets default data for ways."""
    obj.prop_set('ddd:way:weight', default=100)  # Lowest
    obj.prop_set('ddd:way:lanes', default=None)
    obj.prop_set('ddd:way:lane_width', default=3.3)
    obj.prop_set('ddd:way:lane_width_right', default=0.3)  # Forward direction
    obj.prop_set('ddd:way:lane_width_left', default=0.3)  # Reverse direction

    obj.prop_set('ddd:way:roadlines', default=False)


    # TODO: rename as ddd:augment: or whatever
    obj.prop_set('ddd:way:lamps', default=False)
    if obj.extra.get('osm:lit', None) is not None:
        obj.extra['ddd:way:lamps'] = obj.extra['osm:lit']
    obj.prop_set('ddd:way:traffic_signals', default=False)
    obj.prop_set('ddd:way:traffic_signs', default=False)


@dddtask(order="30.30.40.+", path="/Ways/*")
def osm_select_ways_default_material(obj, root):
    """Assign asphalt as default material for ways."""
    if obj.mat is None:
        obj = obj.material(ddd.mats.asphalt)
    return obj



@dddtask(path="/Ways/*", select='["osm:highway" = "pedestrian"]["osm:area" = "yes"]')
def osm_select_ways_pedestrian_ignore(obj, root):
    return False



@dddtask(order="30.30.50.+")
def osm_select_ways_calculated(osm):
    # TODO: Tag identified ways
    pass

@dddtask(order="30.30.50.+")
def osm_select_ways_calculated_clean(osm, root):
    # TODO: Tag identified ways
    root.find("/Ways").replace(root.find("/Ways").clean())

'''
# Disabled: currently selecting highways and water only
@dddtask(path="/Ways/*", )
def osm_select_ways_calculated_discard_untagged(osm):
    """By convention, we discard everything that has not been assigned a material."""
    return False
'''


@dddtask(path="/Ways/*", select='["osm:junction" = "roundabout"]')
def osm_select_ways_calculated_roundabout_weight(obj):
    obj.extra['ddd:way:weight'] = 1

@dddtask(path="/Ways/*", select='["osm:oneway"]["osm:highway" != "motorway"]["osm:highway" != "motorway_link"]')
def osm_select_ways_calculated_oneway_lane_margins(obj):
    obj.extra['ddd:way:lane_width_left'] = obj.extra['ddd:way:lane_width_right']


@dddtask(path="/Ways/*")
def osm_select_ways_calculated_data(obj, root, logger):
    """Sets calculated data for ways."""

    # Use osm:lanes if set, otherwise use lanes
    try:
        obj.extra['ddd:way:lanes'] = int(obj.extra.get('osm:lanes', obj.extra.get('ddd:way:lanes', 0)))
    except TypeError as e:
        #logger.warning("Invalid lanes value (%s %s): %s (%s - %s)", obj.extra.get('osm:lanes', None), obj.extra.get('ddd:way:lanes', None), e, obj, obj.extra)
        obj.extra['ddd:way:lanes'] = None

    if obj.extra.get('ddd:way:width', None) is None:

        lanes = obj.extra.get('ddd:way:lanes', 0)
        if lanes is None or lanes < 1: lanes = 1

        obj.extra['ddd:way:width'] = (lanes * obj.extra['ddd:way:lane_width'] +
                                      obj.extra['ddd:way:lane_width_left'] + obj.extra['ddd:way:lane_width_right'])

    # TODO: use these generic attribs? possibly avoid
    obj.extra['ddd:height'] = obj.extra.get('ddd:way:height', None)
    obj.extra['ddd:extra_height'] = obj.extra['ddd:height']
    obj.set('ddd:width', default=obj.extra['ddd:way:width'])

    # path.extra['ddd:item'] = create_as_item


@dddtask(path="/Ways/*", select='["osm:highway"="pedestrian"]["osm:bridge"]')
def osm_select_ways_calculated_adjustments_pedestrian_bridge(obj, root):
    """
    """
    obj.extra['ddd:way:width'] = obj.extra['ddd:way:width'] * 0.5

