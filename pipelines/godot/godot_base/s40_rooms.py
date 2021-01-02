# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020

from ddd.ddd import ddd, DDDObject2
from ddd.pipeline.decorators import dddtask
from ddd.core.exception import DDDException
import random
import sys
import math
from shapely.ops import linemerge
from ddd.ops import filters, uvmapping


@dddtask(order="40.10.+", log=True)
def rooms_init(root, pipeline):

    pipeline.data['rooms:empty_union'] = ddd.group2()
    pipeline.data['rooms:solid_union'] = ddd.group2()
    pipeline.data['rooms:background_union'] = ddd.group2()
    pipeline.data['rooms:bg_hole_union'] = ddd.group2()

    rooms = ddd.group2(name="Rooms")
    root.append(rooms)

    items = ddd.group2(name="Items")
    root.append(items)

    """
    features = root.find("/Features")

    rooms_union = features.union()
    rooms_union.extrude(100.0).show()

    room_thickness = 150.0
    rooms_buffered = rooms_union.buffer(room_thickness)
    rooms_buffered.extrude(50.0).show()

    rooms_solid = rooms_buffered.subtract(rooms_union)
    rooms_solid.extrude(50.0).show()

    bg3dtest = rooms_union.extrude_step(rooms_union.buffer(-50.0), -30.0, True, False, method=ddd.EXTRUSION_METHOD_SUBTRACT)
    bg3dtest = bg3dtest.extrude_step(rooms_union.buffer(-100.0), -20.0, True, False, method=ddd.EXTRUSION_METHOD_SUBTRACT)
    bg3dtest = bg3dtest.extrude_step(rooms_union.buffer(-150.0), -10.0, True, False, method=ddd.EXTRUSION_METHOD_SUBTRACT)
    ddd.group([rooms_solid.extrude(30.0), bg3dtest]).show()
    """

@dddtask(path="/Features/*", select='[ddd:polygon:type="bg_hole"]', log=True)
def rooms_generate_bghole(root, pipeline, obj):
    """Add empty rooms to empty union."""
    pipeline.data['rooms:bg_hole_union'] = pipeline.data['rooms:bg_hole_union'].union(obj)


@dddtask(path="/Features/*", select='[ddd:polygon:type~"empty|hollow"]', log=True)
def rooms_generate_empty(root, pipeline, obj):
    """Add empty rooms to empty union."""
    pipeline.data['rooms:empty_union'] = pipeline.data['rooms:empty_union'].union(obj)


@dddtask(path="/Features/*", select='[ddd:polygon:type="solid"];[!ddd:polygon:type]', log=True)
def rooms_generate_solid(root, pipeline, obj):
    """Generate solid from polygon."""
    room_solid = obj.copy()
    room_solid.name = "Room: %s" % obj.name
    room_solid = room_solid.material(ddd.mats.rock)
    room_solid.extra['ddd:z_index'] = 40
    root.find("/Rooms").append(room_solid)

    pipeline.data['rooms:solid_union'] = pipeline.data['rooms:solid_union'].union(room_solid)


@dddtask(path="/Features/*", select='[ddd:polygon:type="hollow"]', log=True)
def rooms_generate_hollow(root, pipeline, obj):
    """Generate hollow room from polygon."""

    pipeline.data['rooms:empty_union'] = pipeline.data['rooms:empty_union'].union(obj)
    empty_union = pipeline.data['rooms:empty_union']
    solid_union = pipeline.data['rooms:solid_union']

    room_thickness = 900.0 # 150.0
    room_buffered = obj.buffer(room_thickness)

    room_solid = room_buffered.subtract(empty_union)
    pipeline.data['rooms:solid_union'] = solid_union.union(room_solid)

    room_solid = room_solid.subtract(solid_union)
    room_solid = room_solid.clean(eps=-1)
    room_solid.name = "Room: %s" % obj.name
    room_solid = room_solid.material(ddd.mats.rock)
    room_solid.extra['ddd:z_index'] = 40
    root.find("/Rooms").append(room_solid)


@dddtask(log=True)
def solids_individualize(root, pipeline):
    rooms = root.find("/Rooms").individualize().clean()
    root.find("/Rooms").replace(rooms)

@dddtask(path="/Rooms", select='[geom:type="Polygon"]', log=True)
def solids_collider(root, pipeline, obj):
    obj.extra['ddd:collider'] = True
    obj.extra['ddd:occluder'] = True
    obj.extra['solid'] = True




@dddtask(path="/Rooms", select='[geom:type="Polygon"]', log=True)
def solids_borders(root, pipeline, obj):
    floors = ddd.group2(name="Floors")
    ceilings = ddd.group2(name="Ceilings")
    walls = ddd.group2(name="Walls")

    angles_ceiling = [-math.pi / 4, math.pi / 4]
    angles_floor1 = [math.pi / 4 * 3, math.pi / 4 * 4]
    angles_floor2 = [-math.pi / 4 * 4, -math.pi / 4 * 3]

    polygon = obj.geom.exterior
    if polygon.is_ccw: polygon.coords = reversed(list(polygon.coords))
    segments = zip(polygon.coords, polygon.coords[1:] + polygon.coords[:1])
    for a, b in segments:
        angle = math.atan2(b[1] - a[1], b[0] - a[0])
        if (angle > angles_floor1[0] and angle < angles_floor1[1]):
            floors.append(ddd.line([a, b]))
        if (angle > angles_floor2[0] and angle < angles_floor2[1]):
            floors.append(ddd.line([a, b]))
        if (angle > angles_ceiling[0] and angle < angles_ceiling[1]):
            ceilings.append(ddd.line([a, b]))

    '''
    ddd.mats.grass = ddd.material(name="Grass", color='#2dd355',
                                  texture_path="res://assets/scene/props/grass-texture-tiled.png",
                                  #alpha_cutoff=0.05,
                                  #extra={'ddd:collider': False, 'ddd:shadows': False, 'uv:scale': 0.05}
                                  )
    '''

    floors2 = ddd.group2(name="Floors Background")

    floor_lines = floors
    floors = ddd.line([[0, 0], [1, 1]], name="Floors")
    floors.geom = linemerge([g.geom for g in floor_lines.children])
    # Iterate merged lines
    floors = floors.individualize(always=True).clean()
    for line in floors.children:
        floor = line.buffer(8.0, resolution=1, cap_style=ddd.CAP_ROUND)  # cap_style=ddd.CAP_FLAT)
        floor = floor.material(ddd.mats.grass_fore)
        floor.extra['floor_line'] = line.copy()
        floor.extra['ddd:z_index'] = 46
        #floor = floor.subtract(obj)
        floor = uvmapping.map_2d_path(floor, line, line_x_offset=64.0, line_x_width=63.0)
        if 'uv' in floor.extra:
            floor.extra['uv'] = [(v[0], v[1] * 2.0) for v in floor.extra['uv']]  # temp: transposed and scaled
        #floor = filters.noise_random(floor, scale=3.0)
        #ddd.trace(locals())
        #print(floor.get('uv', None))

        floor2 = line.buffer(18.0, resolution=3, cap_style=ddd.CAP_ROUND)
        floor2 = floor2.material(ddd.mats.grass)
        floor2.extra['floor_line'] = line.copy()
        floor2.extra['ddd:z_index'] = -1
        floor2 = uvmapping.map_2d_path(floor2, line, line_x_offset=64.0, line_x_width=63.0)
        if 'uv' in floor2.extra:
            floor2.extra['uv'] = [(v[0], 16.0 + v[1] * 4.0)for v in floor2.extra['uv']]  # temp: transposed and scaled
        #floor2 = filters.noise_random(floor2, scale=3.0)
        floors2.append(floor2)

        line.replace(floor)

    # for f2 in floors2:  floors.append(f2)
    floors.append(floors2)


    #floors.extra['ddd:z_index'] = 40
    #newobj = ddd.group2([obj, floors], name="Solid")
    #obj.replace(newobj)
    root.find("/Rooms").append(floors)
    obj.extra['floors'] = floors

    ceiling_lines = ceilings
    lines = linemerge([g.geom for g in ceiling_lines.children])
    ceilings = DDDObject2(name="Ceilings", geom=lines)
    ceilings.extra['ddd:z_index'] = 40
    ceilings = ceilings.individualize(always=True).clean()
    for pc in ceilings.children:
        c = pc.copy()
        c.extra['ceiling_line'] = c.copy()
        c = c.buffer(15.0)
        c = filters.noise_random(c, scale=10.0)
        pc.replace(c)
    ceilings = ceilings.material(ddd.mats.bricks)
    #ceilings.mat.color_rgba[3] = 128
    ceilings = ceilings.clean()
    #newobj = ddd.group2([obj, floors], name="Solid")
    #obj.replace(newobj)
    root.find("/Rooms").append(ceilings)
    obj.extra['ceilings'] = ceilings


@dddtask(path="/Features/*", select='[ddd:polygon:type="hollow"]', log=True)
def hollow_background(root, pipeline, obj):

    bgunion = pipeline.data['rooms:background_union']

    bg = obj.copy()
    bg = bg.subtract(pipeline.data['rooms:bg_hole_union'])
    bg = bg.subtract(bgunion)
    bg.name = "Hollow Room Background"
    bg = bg.material(ddd.mats.bricks)
    #bg.mat.color_rgba[3] = 220
    bg = ddd.uv.map_2d_linear(bg)
    bg.extra['ddd:z_index'] = -10
    root.find("/Rooms").append(bg)

    pipeline.data['rooms:background_union'] = bgunion.union(obj)


'''
@dddtask(path="/Rooms/*", select='[solid]', log=True)
def floor_items(root, pipeline, obj):

    if ('floors' not in obj.extra):
        return

    floors = obj.extra['floors']
    floor_lines = floors.extra['floor_lines']

    floor_lines = floor_lines.individualize()
    if len(floor_lines.children) < 1: return
    line = floor_lines.children[0]
    l = line.geom.length
    d = l / 2
    p, segment_idx, segment_coords_a, segment_coords_b = line.interpolate_segment(d)

    pos = [p[0], p[1] - 50.0]
    item = ddd.point(pos, "Item")
    item.extra['godot:instance'] = "res://scenes/items/ItemGeneric.tscn"
    root.find("/Items").append(item)
'''






# Separate floors, ceiling, walls
#  foreach room, separate segments, each can be generated and have the empty space subtracted (also using weight)#

# Add floor surfaces, ceiling surfaces
# Add props, etc...
# Background (hollow), foreground....
# Assign colliders meta, etc

# Generate Godot tscn (export colliders correctly, etc)



'''
@dddtask(order="40.10.+", log=True)
def rooms_split_parts(root, osm, pipeline):

    items = ddd.group2(name="Ceiling")
    root.append(items)
    items = ddd.group2(name="Ways")
    root.append(items)
    items = ddd.group2(name="Buildings")
    root.append(items)
    items = ddd.group2(name="ItemsNodes")
    root.append(items)
    items = ddd.group2(name="ItemsAreas")
    root.append(items)
    items = ddd.group2(name="ItemsWays")
    root.append(items)
    items = ddd.group2(name="Meta")  # 2D meta information (boundaries, etc...)
    root.append(items)

    #root.dump(data=True)

@dddtask(order="30.20.10", path="/Features/*", select='[geom:type="Point"]', log=True)  #  , select='[geom:type="Point"]'  , parent="stage_30_generate_items_node")
def osm_generate_items(root, osm, obj):
    """Generate items for point features."""
    item = obj.copy(name="Item: %s" % obj.name)
    item = item.material(ddd.mats.red)
    if item.geom:
        root.find("/ItemsNodes").append(item)

@dddtask(order="30.20.20", log=True)  #  , select='[geom:type="Point"]'  , parent="stage_30_generate_items_node")
def osm_generate_items_process(root, osm, obj):
    """Generate items for point features."""
    #root.save("/tmp/osm-31-items.svg")
    pass



@dddtask(order="30.30.10.+", log=True)
def osm_select_ways(root):
    # Ways depend on buildings
    pass




@dddtask(order="30.30.20", log=True)
def osm_groups_ways_process(pipeline, osm, root, logger):
    #osm.ways_1d = root.find("/Ways")
    #osm.ways.generate_ways_1d()
    #root.find("/Ways").replace(osm.ways_1d)
    pass



# Generate buildings (separate file)


@dddtask(order="30.50.10", path="/Features/*", select='["geom:type" ~ "Polygon|MultiPolygon|GeometryCollection"][!"osm:building"]')
def osm_groups_areas(root, osm, obj, logger):

    item = obj.copy(name="Area: %s" % obj.name)

    try:
        area = item.individualize().flatten()
        area.validate()
    except DDDException as e:
        logger.warn("Invalid geometry (cropping area) for area %s (%s): %s", area, area.extra, e)
        try:
            area = area.clean(eps=0.001).intersection(ddd.shape(osm.area_crop))
            area = area.individualize().flatten()
            area.validate()
        except DDDException as e:
            logger.warn("Invalid geometry (ignoring area) for area %s (%s): %s", area, area.extra, e)
            return

    for a in area.children:
        if a.geom:
            a.extra['ddd:area:area'] = a.geom.area
            root.find("/Areas").append(a)

    #root.find("/Areas").append(item)

@dddtask(order="30.50.20")
def osm_groups_areas_process(pipeline, osm, root, logger):
    pass


@dddtask(order="30.50.90.+", path="/Areas/*", select='[! "ddd:area:type"]')
def osm_groups_areas_remove_ignored(root, obj, logger):
    """Remove ignored areas."""
    return False


@dddtask(order="30.60.+")
def osm_generate_areas_coastline_2d(osm, root, logger):
    #osm.areas.generate_coastline_2d(osm.area_crop if osm.area_crop else osm.area_filter)  # must come before ground
    water_2d = osm.areas2.generate_coastline_2d(osm.area_filter)  # must come before ground
    logger.info("Coastline 2D areas generated: %s", water_2d)
    if water_2d:
        root.find("/Areas").children.extend(water_2d.children)


@dddtask(order="30.70.+")
def osm_groups_items_areas(osm, root, logger):
    # In separate file
    pass


@dddtask(order="30.90")
def osm_groups_finished(pipeline, osm, root, logger):
    pass



@dddtask(order="39.95.+", cache=True)
def osm_groups_cache(pipeline, osm, root, logger):
    """
    Caches current state to allow for faster reruns.
    """
    return pipeline.data['filenamebase'] + ".s30.cache"
'''

