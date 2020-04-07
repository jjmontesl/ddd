# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging
from ddd.ddd import ddd
from ddd.materials.materials import MaterialsCollection


# Get instance of logger for this module
logger = logging.getLogger(__name__)



class DefaultMaterials(MaterialsCollection):

    def __init__(self):

        # Ways
        self.asphalt = ddd.material(name="Asphalt", color='#202020')
        self.dirt = ddd.material(name="Dirt", color="#b58800")
        self.sidewalk = ddd.material(name="Sidewalk", color='#e0d0d0')
        self.pavement = ddd.material(name="Sidewalk", color='#c0c0b0')
        self.pathwalk = ddd.material(name="WayPedestrian", color='#78281e')

        self.roadline = ddd.material(name="Roadline", color='#e8e8e8', extra={'ddd:collider': False, 'ddd:shadows': False})
        self.railway = ddd.material(name="RoadRailway", color="#47443e", extra={'ddd:shadows': False})

        # Areas
        self.sea = ddd.material(name="Water4Advanced", color='#3d43b5', extra={'ddd:collider': False, 'ddd:shadows': False})
        self.water = ddd.material(name="WaterBasicDaytime", color='#4d53c5', extra={'ddd:collider': False, 'ddd:shadows': False})

        self.terrain = ddd.material(name="Ground", color='#e6821e')

        self.park = ddd.material(name="Park", color='#1db345')
        self.pitch = ddd.material(name="Pitch", color='#196118')

        # Structural / building materials
        self.bronze = ddd.material(name="Bronze", color='#f0cb11')
        self.steel = ddd.material(name="Steel", color='#78839c')

        self.stone = ddd.material(name="Stone", color='#9c9378')
        self.rock = ddd.material(name="Rock", color='#7c5378')
        self.cement = ddd.material(name="Concrete", color='#b8b8a0')
        self.bricks = ddd.material(name="Bricks", color='#d49156')

        self.wood = ddd.material(color='#efae85')

        # Painted materials
        self.metal_paint_red = ddd.material("PaintRed", color='#d01010')
        self.metal_paint_green = ddd.material("PaintGreen", color='#265e13')
        self.metal_paint_yellow = ddd.material("PaintYellow", color='#ebe015')

        # Lights
        self.lightbulb = ddd.material(color='e8e0e4')
        self.light_green = ddd.material(color='#00ff00')
        self.light_orange = ddd.material(color='#ffff00')
        self.light_red = ddd.material(color='#ff0000')

        # Trees
        self.bark = ddd.material(name="Bark", color='#df9e75')
        self.treetop = ddd.material(name="Treetop", color='#1da345')

        # Urban props materials
        self.lightbulb = ddd.material(color='e8e0e4')
        self.fence = ddd.material(name="Fence", color='282024')
        self.railing = ddd.material(name="Fence", color='282024')

        # Buildings
        self.building_1 = ddd.material(color='#f7f0be')
        self.building_2 = ddd.material(color='#bdb9a0')
        self.building_3 = ddd.material(color='#c49156')
        self.roof_tiles = ddd.material("RoofTiles", color='#f25129')

