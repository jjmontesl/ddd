# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging

from ddd.ddd import ddd
from trimesh import transformations
from ddd.math.vector3 import Vector3

from ddd.ops.layout import DDDLayout, VerticalDDDLayout


# Get instance of logger for this module
logger = logging.getLogger(__name__)


def tap_push(r=0.01, height=0.1, length=0.15):
    base = ddd.point(name="Tap").buffer(r, resolution=2)
    path = ddd.point().line_to([0, height]).line_to([length, height]).line_to([length, height * 0.5])
    item = base.extrude_along(path)
    item = item.rotate(ddd.ROT_FLOOR_TO_FRONT).rotate(ddd.ROT_TOP_CW)
    item = item.material(ddd.mats.steel)
    item = ddd.uv.map_cubic(item)
    return item

def tap():
    return tap_push()


def handle_knob(r=0.03):
    knob = ddd.sphere(r=r, subdivisions=0.5, name="Knob")
    knob = knob.material(ddd.mats.plastic_white)
    knob = knob.smooth()
    return knob

def handle_block():
    # TODO: bring here door_handle... from buildings.py
    pass

def handle_bar_u():
    pass

def handle_door():
    pass

#def handle_plate(shape_func=shapes.squared):
#    pass

def drawer(width=0.4, height=0.2, depth=0.4, thick=0.03, height_side=0.15):
    """
    A drawer, with the front base lying on the front plane, and lying on the xy plane, centered on X.
    """
    front_face = ddd.rect([-width / 2, 0, width / 2, height])
    side_face = ddd.rect([0, 0, depth - 2 * thick, height_side])
    base_face = ddd.rect([-width / 2 + thick, thick, width / 2 - thick, depth - thick])

    base = base_face.extrude(thick)
    front = front_face.extrude(thick).rotate(ddd.ROT_FLOOR_TO_FRONT).translate([0, thick, 0])
    back = front.translate([0, depth - thick, 0])
    side_l = side_face.extrude(thick).rotate(ddd.ROT_FLOOR_TO_FRONT).rotate(ddd.ROT_TOP_CCW).translate([-width / 2, thick, 0])
    side_r = side_l.translate([width - thick, 0, 0])

    drawer = ddd.group([base, side_l, side_r, front, back], name="Drawer")
    drawer = drawer.combine()
    drawer = drawer.material(ddd.mats.wood)
    drawer = ddd.uv.map_cubic(drawer)

    knob_r = 0.03
    handle = handle_knob(r=knob_r)
    handle.transform.translate([0, -knob_r, height / 2])

    drawer.append(handle)

    return drawer

def shelf(width=0.4, depth=0.4, thick=0.04):
    """
    Extends backwards (positive Y)
    """
    shelf = ddd.box([-width/2, 0, 0, width/2, depth, thick], name="Shelf")
    shelf = shelf.material(ddd.mats.wood)
    shelf = ddd.uv.map_cubic(shelf)
    return shelf

def cabinet_door(height=0.5, width=0.4, hinge=0, thick=0.04, front_thick=0.02, knob_height_n = 0.5):
    """
    A door, with the hinge on the Z axis, resting on its base (hinge is on the left (0) or right (1)).
    """
    door_face = ddd.rect([width, height], name="Cabinet Door")
    door = door_face.extrude_step(door_face, thick)
    door = door.extrude_step(door_face.buffer(-thick), front_thick)

    door = door.rotate(ddd.ROT_FLOOR_TO_FRONT).translate((0, thick, 0))
    door = door.material(ddd.mats.wood)
    door = door.smooth(angle=0)
    door = ddd.uv.map_cubic(door)
    if hinge == 1:
        door = door.translate((-width, 0, 0))

    knob_r = 0.03
    knob = handle_knob(r=knob_r)
    knob_pos = 0.2 * width
    if hinge == 1: knob_pos = width - knob_pos

    knob.transform.translate((knob_pos, -front_thick - knob_r, height * knob_height_n))
    door.append(knob)

    return door


def furniture_layout(layout, depth=0.4, thick=0.04):

    obj = ddd.DDDNode3(name="Furniture").copy_from(layout, copy_children=False)

    fobj = None

    width = obj.get('ddd:layout:width')
    height = obj.get('ddd:layout:height')
    ftype = obj.get('ddd:furniture', None)

    if ftype == 'shelf':
        fobj = shelf(width, depth, thick).translate([width / 2, 0, -height])
    elif ftype == 'cabinet':
        fobj = cabinet_door(height, width, thick=thick).translate([0, 0, -height])
    elif ftype == 'drawer':
        fobj = drawer(width, height, depth=depth, thick=thick).translate([width / 2, 0, -height])

    obj.children = [furniture_layout(c, depth, thick) for c in layout.children]

    if fobj:
        obj.append(fobj)
    #furniture = furniture.smooth(angle=0)

    # Position (by copy_from)
    obj.transform.position = Vector3((layout.transform.position[0], 0, layout.transform.position[1]))
    #obj.show()

    return obj


def furniture_test_out_in(height=1.6, width=0.8, thick=0.04, shelf_height=0.30, drawer_height=0.25):

    furniture = ddd.DDDNode2(name="Furniture").set({'ddd:layout': 'vertical', 'ddd:layout:spacing': thick, 'ddd:layout:margin': thick, 'ddd:layout:width': width, 'ddd:layout:height': height})

    shelves = ddd.DDDNode2(name="Shelves").set({'ddd:layout': 'vertical', 'ddd:layout:width:expand': True})
    furniture.append(shelves)
    for i in range(1):
        shelf = ddd.DDDNode2(name=f"Shelf {i}").set({'ddd:furniture': 'shelf', 'ddd:layout': 'element', 'ddd:layout:width:expand': True, 'ddd:layout:height': shelf_height})
        shelves.append(shelf)

    cabinets = ddd.DDDNode2(name="Cabinet").set({'ddd:layout': 'vertical', 'ddd:layout:width:expand': True, 'ddd:layout:height:flexible': 1.0})
    furniture.append(cabinets)
    for i in range(1):
        cabinet = ddd.DDDNode2(name=f"Cabinet {i}").set({'ddd:furniture': 'cabinet', 'ddd:layout': 'element', 'ddd:layout:width:expand': True, 'ddd:layout:height:flexible': 1.0})
        cabinets.append(cabinet)

    drawers = ddd.DDDNode2(name="Drawers").set({'ddd:layout': 'vertical', 'ddd:layout:width:expand': True})
    furniture.append(drawers)
    for i in range(2):
        drawer = ddd.DDDNode2(name=f"Drawer {i}").set({'ddd:furniture': 'drawer', 'ddd:layout': 'element', 'ddd:layout:width:expand': True, 'ddd:layout:height': drawer_height})
        drawers.append(drawer)

    base = ddd.DDDNode2(name=f"Base").set({'ddd:layout': 'element', 'ddd:layout:width:expand': True, 'ddd:layout:height': 0.2})
    furniture.append(base)

    furniture = DDDLayout.layout(furniture)
    furniture.transform.translate([0, furniture.get('ddd:layout:height'), 0])

    furniture_viz = DDDLayout.to_rects(furniture)
    furniture_viz = ddd.helper.colorize_objects(furniture_viz)
    #furniture_viz.dump(data="ddd")
    #ddd.group([furniture_viz, ddd.helper.grid_xy(size=4.0, grid_space=0.2).recenter()]).show()

    furniture = furniture_layout(furniture)
    #furniture = furniture.rotate(ddd.ROT_FLOOR_TO_FRONT)
    #furniture.show()

    return furniture

def furniture_cabinet_vertical_shelf_drawer_cabinet(height=None, width=1.0, depth=0.4, thick=0.04,
                                                    shelves=1, shelf_height=0.25, shelf_depth=0.35, shelf_thick=0.03,
                                                    drawers=2,
                                                    cabinet_height=None, cabinet_shelves=2, cabinet_doors=1, cabinet_doors_hinge=0):

    shelves = VerticalDDDLayout()
    '''
    for i in range(shelves):
        shelf = DDDLayoutElement(width=width, height=shelf_height, spacing=shelf_thick), depth=shelves_depth, thick=shelves_thick)
        elements.append(shelf)

    layout = VerticalDDDLayout(elements, height=height)

    obj = furniture_cabinet(elements, height, width, depth, thick)
    return obj
    '''

