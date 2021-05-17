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
    obj = obj.triangulate().twosided().translate([0, 0, depth])
    obj = obj.material(ddd.mats.glass)
    obj = ddd.uv.map_cubic(obj)
    obj = obj.rotate(ddd.ROT_FLOOR_TO_FRONT)

    return obj

def window_border_flat(width=1.6, height=1.2, border_depth=0.05, border_thick=0.1):
    obj = ddd.rect([-width * 0.5, 0, width * 0.5, height], name="Window Border")
    interior = obj.buffer(-border_thick)
    obj = obj.subtract(interior)

    obj = obj.extrude(border_depth)
    obj = obj.material(ddd.mats.stone)
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

def window_with_border(width=1.6, height=1.2, border_depth=0.05, border_thick=0.1):  #, shelf_thick=None):
    interior = window_interior(width=width - border_thick * 2, height=height - border_thick * 2).translate([0, 0, border_thick])
    border = window_border_flat(width=width, height=height, border_depth=border_depth, border_thick=border_thick)
    obj = ddd.group3([interior, border], "Window")
    return obj


def window_grid():
    pass


def door(width=1.5, height=2.2, depth=0.06):
    """
    A door, centered on X and aligned to floor plane, lying on the XZ plane.
    """
    obj = ddd.rect([-width * 0.5, 0, width * 0.5, height], name="Door")
    obj = obj.extrude(depth).translate([0, 0, depth])
    obj = obj.material(ddd.mats.wood)
    obj = ddd.uv.map_cubic(obj)
    obj = obj.rotate(ddd.ROT_FLOOR_TO_FRONT)
    return obj


#def portal(width=1.6, height=2.2, border_depth=0.10):
#    pass


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
