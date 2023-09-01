# DDD(123) - Library for procedural generation of 2D and 3D geometries and scenes
# Copyright (C) 2021 Jose Juan Montes
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from ddd.ddd import ddd
from ddd.pack.sketchy import interior

"""
Pocedures to build building related items, as seen from outside,
like windows, doors, showcases, awnings...
"""


def window_interior(width=1.6, height=1.2, depth=0.02):
    """
    A window, centered on X and aligned to floor plane, lying on the XZ plane.
    """
    obj = ddd.rect([-width * 0.5, 0, width * 0.5, height], name="Window")
    #obj = obj.extrude(depth)
    obj = obj.triangulate().translate([0, 0, depth])
    #obj = obj.twosided()  # shall be optional, as back is not seen in many cases
    obj = obj.material(ddd.mats.glass)
    obj = ddd.uv.map_cubic(obj)
    obj = obj.rotate(ddd.ROT_FLOOR_TO_FRONT)

    return obj

def window_border_flat(width=1.6, height=1.2, border_depth=0.05, border_thick=0.04, border_material=None):
    obj = ddd.rect([-width * 0.5, 0, width * 0.5, height], name="Window Border")
    interior = obj.buffer(-border_thick)
    obj = obj.subtract(interior)

    obj = obj.extrude(border_depth)
    
    if border_material is None: material = ddd.mats.wood
    obj = obj.material(border_material)

    obj = ddd.uv.map_cubic(obj)
    obj = obj.rotate(ddd.ROT_FLOOR_TO_FRONT)

    return obj

def window_border_grille(width=1.6, height=1.2, border_depth=0.05, border_thick=0.04, border_material=None, grille=(2, 2)):
    
    grille_width = width / grille[0]
    grille_height = height / grille[1]
    grille_depth = border_depth - 0.01
    grille_thick = border_thick - 0.01

    result = ddd.group3(name="Window Grille")
    
    vertical_bar = ddd.rect([0, 0, grille_thick, grille_depth]).extrude(height).translate([-border_thick * 0.5, -border_depth, 0])
    for x in range(grille[0] - 1):
        bar = vertical_bar.copy().translate([-width * 0.5 + grille_width * (x + 1), 0, 0])
        result = result.append(bar)

    horizontal_bar = ddd.rect([0, 0, width, grille_depth]).extrude(grille_thick).translate([-width * 0.5, -border_depth, -grille_thick * 0.5])
    for y in range(grille[1] - 1):
        bar = horizontal_bar.copy().translate([0, 0, grille_height * (y + 1)])
        result = result.append(bar)

    obj = result.combine()
    if border_material is None: material = ddd.mats.wood
    obj = obj.material(border_material)

    obj = ddd.uv.map_cubic(obj)

    return obj
    


'''
def window_border_shelf(width=1.6, height=1.2, border_depth=0.05, border_thick=0.1):
    obj = ddd.rect([-width * 0.5, 0, width * 0.5, height], name="Window Border Shelf")
    interior = obj.buffer(-border_thick)
    obj = obj.subtract(interior)

    obj = obj.extrude(border_depth)
    obj = obj.material(ddd.mats.stone)
    obj = ddd.uv.map_cubic(obj)
    obj = obj.rotate(ddd.ROT_FLOOR_TO_FRONT)

    return obj
'''

def window_with_border(width=1.6, height=1.2, border_depth=0.05, border_thick=0.04, border_material=None):  #, shelf_thick=None):
    interior = window_interior(width=width - border_thick * 2, height=height - border_thick * 2).translate([0, 0, border_thick])
    border = window_border_flat(width=width, height=height, border_depth=border_depth, border_thick=border_thick, border_material=border_material)
    obj = ddd.group3([interior, border], "Window")
    return obj

def window_with_border_and_grille(width=1.6, height=1.2, border_depth=0.05, border_thick=0.04, border_material=None, grille=(2,2)):  #, shelf_thick=None):
    interior = window_interior(width=width - border_thick * 2, height=height - border_thick * 2).translate([0, 0, border_thick])
    
    border = window_border_flat(width=width, height=height, border_depth=border_depth, border_thick=border_thick, border_material=border_material)
    grille = window_border_grille(width=width - border_thick * 2, height=height - border_thick * 2, grille=grille).translate([0, 0, border_thick])
    border = border.append(grille).combine()

    obj = ddd.group3([interior, border], "Window")
    return obj


#def door_surface_panels_raised():
#    """
#    Builds a door, composed of 1) a flat padding  2) 1 o 2 raised/carved panels with given shapes optionally separated leaving the center empty.
#    """
#    pass


def door(width=1.4, height=2.2, depth=0.06):  # , handle_height=None, surface_front=None, surface_back=None):
    """
    A door, centered on X and aligned to floor plane, lying on the XZ plane.

    TODO: Support left/right door
    """
    obj = ddd.rect([-width * 0.5, 0, width * 0.5, height], name="Door")
    obj = obj.extrude(depth) # .translate([0, 0, depth])
    obj = obj.material(ddd.mats.wood)
    obj = obj.smooth()
    obj = ddd.uv.map_cubic(obj, split=True)
    obj = obj.rotate(ddd.ROT_FLOOR_TO_FRONT)

    # TODO: Provide data for hinge joints (Q: as slots?)

    # Slots:

    # Handle front (start of the handle, closest to the door border)
    ddd.slots.slot_add(obj, 'handle-front', [-width * 0.35, -depth, 1.07])
    # Handle back (start of the handle, closest to the door border)
    ddd.slots.slot_add(obj, 'handle-back', [-width * 0.35, 0, 1.07], rotation=ddd.ROT_TOP_HALFTURN)
    # Knocker / doorbell / banner... (center of the area)

    
    handle = interior.handle_TEST()  # TODO: add handles as item/builder defs, keep door(s) as a simple geometry and/or with decoration
    ddd.slots.slot_connect(obj, 'handle-front', handle)
    handle = interior.handle_TEST()  # TODO: add handles as item/builder defs, keep door(s) as a simple geometry and/or with decoration
    # FIXME: causes failures also when moving+exporting the object afterwards, see sketchy_interior example (or is it the slot rotation?)
    handle = handle.scale([-1, 1, 1]).invert()  # Hackish way to invert the handle 
    
    ddd.slots.slot_connect(obj, 'handle-back', handle)

    #handle.transform.translate([-width * 0.35, -depth, 1.07])
    #obj.append(handle)

    #handle = door_handle()
    #obj.append(handle)

    return obj


def portal(width=3.6, height=2.8, frame_width=0.08, frame_depth=0.05, door_width=1.4, top_panel_height=0.8, bottom_panel_height=0.4):
    """
    A portal door set.
    """

    pdoor = door(door_width, height - top_panel_height)

    obj = ddd.rect([-width * 0.5, 0, width * 0.5, height], name="Door Frame")
    obj = obj.subtract(ddd.rect([-width * 0.5 + frame_width, -1, width * 0.5 - frame_width, height - frame_width]))

    if top_panel_height > 0:
        obj = obj.union(ddd.rect([-width * 0.5, height - top_panel_height, width * 0.5, height - top_panel_height + frame_width]))

    if bottom_panel_height > 0:
        obj = obj.union(ddd.rect([-width * 0.5, 0, width * 0.5, bottom_panel_height]))

    obj = obj.extrude(frame_depth)

    obj = obj.material(ddd.mats.wood)
    obj = ddd.uv.map_cubic(obj)

    glass = ddd.rect([-width * 0.5 + frame_width, bottom_panel_height, width * 0.5 - frame_width, height - frame_width], name="Window")
    #obj = obj.extrude(depth)
    glass = glass.triangulate()
    glass = glass.translate([0, 0, 0.02])  # Translate a bit to avoid z-fighting
    glass = glass.material(ddd.mats.glass)
    glass = ddd.uv.map_cubic(glass)

    obj.append(glass)
    obj = obj.rotate(ddd.ROT_FLOOR_TO_FRONT)

    obj.append(pdoor)

    return obj


# TODO: the "column" concept conflicts with other column concepts
#def column():
#    pass


def column(height=2.00, r=0.075):
    """
    A column. 
    
    Columns may be usable for exterior columns, as well as for interior both structural and decorative (e.g. railings) columnns. 
    In some configurations, they may also be usable as support.
    """

    col = ddd.point([0, 0], name="Column").buffer(r, resolution=0, cap_style=ddd.CAP_SQUARE).extrude(height)  # , cap=False, base=False)
    #col = col.smooth(math.pi)
    col = col.material(ddd.mats.stone)
    col = ddd.uv.map_cylindrical(col)  #, split=False)
    #col = ddd.collision.aabox_from_aabb(col)

    return col



'''
def building_level(height, sides_buffer=None):
    pass

def building_columns(spacing=10.0, sides_buffer=None):
    pass

def building_roof_angled(sides_buffer=None):
    pass

def building_roof_rooftop():
    pass

def building():
    pass
'''
