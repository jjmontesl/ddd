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


def window_grille():
    pass


def door(width=1.4, height=2.2, depth=0.06):
    """
    A door, centered on X and aligned to floor plane, lying on the XZ plane.
    """
    obj = ddd.rect([-width * 0.5, 0, width * 0.5, height], name="Door")
    obj = obj.extrude(depth) # .translate([0, 0, depth])
    obj = obj.material(ddd.mats.wood)
    obj = obj.smooth()
    obj = ddd.uv.map_cubic(obj, split=True)
    obj = obj.rotate(ddd.ROT_FLOOR_TO_FRONT)

    handle = door_handle_bar()
    handle.transform.translate([-width * 0.4, -depth, 1.07])
    obj.append(handle)

    #handle = door_handle()
    #obj.append(handle)

    return obj


def door_handle_bar(width=0.1, height=0.3, depth=0.05, separation=0.06):
    """
    """
    shape = ddd.rect([width, height], name="Door Handle").recenter()
    obj = shape.scale([0.5, 0.5]).extrude_step(shape, separation, base=False)
    obj = obj.extrude_step(shape, depth)
    obj = obj.material(ddd.mats.metal)
    obj = ddd.uv.map_cubic(obj)
    obj = obj.rotate(ddd.ROT_FLOOR_TO_FRONT)
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


#def column():
#    pass


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
