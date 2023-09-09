# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020

from ddd.ddd import ddd, DDDNode2
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
    pipeline.data['rooms:user_solid_union'] = ddd.group2()
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


@dddtask(path="/Features/*", select='[geom:type="Polygon"]([ddd:polygon:type="solid"];[!ddd:polygon:type])', log=True)
def rooms_generate_solid(root, pipeline, obj):
    """Generate solid from polygon."""
    room_solid = obj.copy()
    room_solid.name = "Room: %s" % obj.name
    room_solid = room_solid.clean(eps=-1)
    rooms_solid = ddd.geomops.remove_holes_split(room_solid)


    for room_solid in rooms_solid.children:

        room_solid = room_solid.material(ddd.mats.rock)
        # room_solid.extra['godot:light_mask'] = 0
        room_solid = ddd.uv.map_2d_linear(room_solid)
        room_solid.extra['ddd:z_index'] = 40
        room_solid.extra['godot:light_mask'] = 0
        root.find("/Rooms").append(room_solid)

        pipeline.data['rooms:solid_union'] = pipeline.data['rooms:solid_union'].union(room_solid)
        pipeline.data['rooms:user_solid_union'] = pipeline.data['rooms:user_solid_union'].union(room_solid)


@dddtask(path="/Features/*", select='[ddd:polygon:type="hollow"]', log=True)
def rooms_generate_hollow(root, pipeline, obj):
    """Generate hollow room from polygon."""

    pipeline.data['rooms:empty_union'] = pipeline.data['rooms:empty_union'].union(obj)
    empty_union = pipeline.data['rooms:empty_union']
    solid_union = pipeline.data['rooms:solid_union']

    room_thickness = 1500.0  # 900.0 # 150.0
    room_buffered = obj.buffer(room_thickness)

    room_solid = room_buffered.subtract(empty_union)
    pipeline.data['rooms:solid_union'] = solid_union.union(room_solid)

    room_solid = room_solid.subtract(solid_union)
    room_solid = room_solid.clean(eps=-1)
    rooms_solid = ddd.geomops.remove_holes_split(room_solid)

    for room_solid in rooms_solid.children:
        room_solid.name = "Room: %s" % obj.name
        room_solid = room_solid.material(ddd.mats.rock)
        room_solid = ddd.uv.map_2d_linear(room_solid)
        room_solid.extra['godot:material'] = "rock" # Enforcing to avoid material applyting to solid, but should be reworked
        room_solid.extra['ddd:z_index'] = 40
        room_solid.extra['godot:light_mask'] = 0
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


@dddtask(path="/Features/*", select='[ddd:polygon:type="fore"]', log=True)
def rooms_fore(root, pipeline, obj):

    bg = obj.copy()
    bg = bg.subtract(pipeline.data['rooms:solid_union'])

    bgs = ddd.geomops.remove_holes_split(bg)

    for bg in bgs.children:
        bg.name = "Foreground"
        bg = bg.material(ddd.mats.rock)
        # bg.mat.color_rgba[3] = 220
        bg = ddd.uv.map_2d_linear(bg)
        bg.extra['ddd:z_index'] = 40
        bg.extra['godot:light_mask'] = 0
        if 'godot:material' in obj.extra: bg.extra['godot:material'] = obj.extra['godot:material']
        root.find("/Rooms").append(bg)


@dddtask(path="/Rooms", select='[geom:type="Polygon"][!floor_line][!ceiling_line]', log=True)
def solids_borders(root, pipeline, obj):

    if 'godot:material' in obj.extra:
        del(obj.extra['godot:material'])

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
        if (angle >= angles_floor1[0] and angle <= angles_floor1[1]):
            borderline = ddd.line([a, b])
            borderline.extra.update(obj.extra)
            floors.append(borderline)
        if (angle >= angles_floor2[0] and angle <= angles_floor2[1]):
            borderline = ddd.line([a, b])
            borderline.extra.update(obj.extra)
            floors.append(borderline)
        if (angle >= angles_ceiling[0] and angle <= angles_ceiling[1]):
            borderline = ddd.line([a, b])
            borderline.extra.update(obj.extra)
            ceilings.append(borderline)

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
    floors.extra.update(obj.extra)
    floors.geom = linemerge([g.geom for g in floor_lines.children])
    # Iterate merged lines
    floors = floors.individualize(always=True).clean()
    for line in floors.children:
        floor = line.buffer(8.0, resolution=1, cap_style=ddd.CAP_FLAT)  # cap_style=ddd.CAP_FLAT)
        floor = floor.material(ddd.mats.grass_fore)
        floor.name = "Floor Fore: %s" % line.name
        floor.extra['floor_line'] = line.copy()
        #floor.extra['godot:material'] = "grass_fore"
        floor.extra['ddd:z_index'] = 46
        # floor = floor.subtract(obj)
        floor = uvmapping.map_2d_path(floor, line, line_x_offset=64.0, line_x_width=63.0)
        if 'uv' in floor.extra:
            floor.extra['uv'] = [(v[0], v[1] * 4.0) for v in floor.extra['uv']]  # temp: transposed and scaled
        floor.extra['ddd:collider'] = False
        floor.extra['ddd:occluder'] = False
        floor.extra['solid'] = False
        floor.extra['godot:light_mask'] = 0
        # floor = filters.noise_random(floor, scale=3.0)
        # ddd.trace(locals())
        # print(floor.get('uv', None))

        floor2 = line.buffer(18.0, resolution=3, cap_style=ddd.CAP_FLAT)
        floor2 = floor2.material(ddd.mats.grass)
        floor2.name = "Floor: %s" % line.name
        floor2.extra['floor_line'] = line.copy()
        #floor.extra['godot:material'] = "grass"
        floor2.extra['ddd:z_index'] = -1
        floor2 = uvmapping.map_2d_path(floor2, line, line_x_offset=64.0, line_x_width=63.0)
        if 'uv' in floor2.extra:
            floor2.extra['uv'] = [(v[0], 16.0 + v[1] * 3.5)for v in floor2.extra['uv']]  # temp: transposed and scaled
        # floor2 = filters.noise_random(floor2, scale=3.0)
        floor2.extra['ddd:collider'] = False
        floor2.extra['ddd:occluder'] = False
        floor2.extra['solid'] = False
        floor2.extra['godot:light_mask'] = 1

        min_length = 50
        if line.length() > min_length and not obj.get('border:floor', None) == 'false':
            floors2.append(floor2)
            line.replace(floor)
        else:
            line.geom = None

    # for f2 in floors2:  floors.append(f2)
    floors.append(floors2)

    # floors.extra['ddd:z_index'] = 40
    # newobj = ddd.group2([obj, floors], name="Solid")
    # obj.replace(newobj)
    root.find("/Rooms").append(floors)
    obj.extra['floors'] = floors

    ceiling_lines = ceilings
    lines = linemerge([g.geom for g in ceiling_lines.children])
    ceilings = DDDNode2(name="Ceilings", geom=lines)
    ceilings.extra.update(obj.extra)
    ceilings.extra['ddd:z_index'] = 40
    ceilings = ceilings.individualize(always=True).clean()
    for pc in ceilings.children:
        c = pc.copy()
        c.extra['ceiling_line'] = c.copy()
        c = c.buffer(15.0)
        c = filters.noise_random(c, scale=10.0)
        pc.replace(c)
    ceilings = ceilings.material(ddd.mats.bricks)
    # ceilings.mat.color_rgba[3] = 128
    ceilings = ceilings.clean()

    ceilings.set('ddd:collider', False, children=True)
    ceilings.set('ddd:occluder', False, children=True)
    ceilings.set('solid', False, children=True)
    ceilings.set('godot:light_mask', 1, children=True)

    # newobj = ddd.group2([obj, floors], name="Solid")
    # obj.replace(newobj)
    root.find("/Rooms").append(ceilings)
    obj.extra['ceilings'] = ceilings


@dddtask(path="/Features/*", select='[ddd:polygon:type~"hollow|bg"]', log=True)
def hollow_background(root, pipeline, obj):

    bgunion = pipeline.data['rooms:background_union']

    bg = obj.copy()

    bg = bg.subtract(pipeline.data['rooms:bg_hole_union'])
    bg = bg.subtract(pipeline.data['rooms:solid_union'])

    bg = bg.subtract(bgunion)

    intersects = root.select(path="/Features/*", selector='[ddd:polygon:type="intersect"]').union()
    bg = bg.subtract(intersects)

    bgs = ddd.geomops.remove_holes_split(bg)

    for bg in bgs.children:
        bg.name = "Hollow Room Background"
        bg = bg.material(ddd.mats.bricks)
        # bg.mat.color_rgba[3] = 220
        bg = ddd.uv.map_2d_linear(bg)
        bg.extra['ddd:z_index'] = -10
        if 'godot:material' in obj.extra: bg.extra['godot:material'] = obj.extra['godot:material']

        # Do not add to rooms if no background
        # TODO: We may need separate groups for "areas" and "bgground", or remove afterwards
        if obj.get('godot:bg', "default") in (None, "null", "None"):
            continue

        root.find("/Rooms").append(bg)

    pipeline.data['rooms:background_union'] = bgunion.union(obj)


@dddtask(path="/Features/*", select='[ddd:polygon:type="intersect"]', log=True)
def hollow_background_intersect(root, pipeline, obj):

    bgunion = pipeline.data['rooms:background_union']

    bg = obj.copy()
    bg = bg.intersection(pipeline.data['rooms:background_union'])

    bgs = ddd.geomops.remove_holes_split(bg)

    for bg in bgs.children:
        bg.name = "Hollow Room Background Intersect"
        bg = bg.material(ddd.mats.bricks)
        # bg.mat.color_rgba[3] = 220
        bg = ddd.uv.map_2d_linear(bg)
        bg.extra['ddd:z_index'] = -10
        if 'godot:material' in obj.extra: bg.extra['godot:material'] = obj.extra['godot:material']
        root.find("/Rooms").append(bg)

        # Subtract from background
        # for room in root.find("/Rooms").children:
        #    room.replace(room.subtract(bg))
        # root.find("/Rooms").replace(root.find("/Rooms").subtract(bg).individualize().flatten())

    # pipeline.data['rooms:background_union'] = bgunion.union(obj)


@dddtask(path="/Rooms/*", select='[godot:material]', log=True)
def room_materials(root, pipeline, obj):
    mat_name = obj.extra['godot:material']
    mat = getattr(ddd.mats, mat_name)
    obj = obj.material(mat)
    return obj


@dddtask(path="/Features/*", select='[ddd:polygon:type="bg_hole"][ddd:polygon:frame:material]', log=True)
def holes_frames(root, pipeline, obj):
    mat_name = obj.extra['ddd:polygon:frame:material']
    mat = getattr(ddd.mats, mat_name)
    dist = float(obj.get('ddd:polygon:frame:dist', 10))

    obj = obj.copy()
    obj = obj.subtract(obj.buffer(-dist))
    bgs = ddd.geomops.remove_holes_split(obj)
    for bg in bgs.children:
        bg = bg.material(mat)
        bg = ddd.uv.map_2d_linear(bg)
        bg.extra['ddd:z_index'] = -10
        bg.name = "Frame: %s" % bg.name
        root.find("/Rooms").append(bg)
