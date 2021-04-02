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
        self.pathwalk = ddd.material(name="WayPedestrian", color='#78281e')

        # Areas
        self.sea = ddd.material(name="Water4Advanced", color='#3d43b5', extra={'ddd:collider': False, 'ddd:shadows': False, 'ddd:transparent': True})
        self.water = ddd.material(name="WaterBasicDaytime", color='#4d53c5', extra={'ddd:collider': False, 'ddd:shadows': False, 'ddd:transparent': True})
        self.volumetricgrass = ddd.material(name="VolumetricGrass", color='#2dd355', extra={'ddd:export-as-marker': True})  # Warning: duplicated in areas_3d volumetic grass generation


        self.dirt = ddd.material(name="Dirt", color="#b58800")
        self.forest = ddd.material(name="Forest", color='#3a6e17')
        self.garden = ddd.material(name="Garden", color='#2f614b')
        self.grass = ddd.material(name="Grass", color='#2dd355')
        self.park = ddd.material(name="Park", color='#1db345')
        self.rock = ddd.material(name="Rock", color='#5f5f4d')
        self.sand = ddd.material(name="Sand", color='#fff694')
        self.terrain = ddd.material(name="Ground", color='#e6821e')
        self.wetland = ddd.material(name="Wetland", color='#54610c')

        self.pavement = ddd.material(name="Sidewalk", color='#c0c0b0')
        self.sett = ddd.material(name="Sett", color='#7b719f')
        self.sidewalk = ddd.material(name="Sidewalk", color='#e0d0d0')

        self.pitch = ddd.material(name="Pitch", color='#196118')
        self.pitch_blue = ddd.material(name="Pitch Blue", color='#2a69b0')  # Eg. cycleways
        self.pitch_red = ddd.material(name="Pitch Red", color='#b34446')  # Eg. leisure track

        # Structural / building materials
        self.bronze = ddd.material(name="Bronze", color='#f0cb11')
        self.steel = ddd.material(name="Steel", color='#78839c')
        self.metal = ddd.material(name="Steel", color='#68738c')

        self.stone = ddd.material(name="Stone", color='#9c9378')
        self.cement = ddd.material(name="Concrete", color='#b8b8a0')
        self.bricks = ddd.material(name="Bricks", color='#d49156')

        self.wood = ddd.material(name="Wood", color='#efae85')

        # Painted materials
        self.metal_paint_red = ddd.material("PaintRed", color='#d01010')
        self.metal_paint_green = ddd.material("PaintGreen", color='#265e13')
        self.metal_paint_yellow = ddd.material("PaintYellow", color='#ebe015')
        self.metal_paint_blue = ddd.material("PaintBlue", color='#184794')
        self.metal_paint_white = ddd.material("PaintWhite", color='#f8fbff')
        self.metal_paint_black = ddd.material("PaintBlack", color='#000a17')

        # Plastics
        self.plastic_transparent = ddd.material(color='e8e0e4', extra={'ddd:transparent': True})  # name="PlasticTransparent",
        self.plastic_black = ddd.material(color='#2c2936')

        # Glass
        self.glass = ddd.material("Glass", color='#baf3f5')  #  , extra={'ddd:transparent': True}

        # Lights
        self.lightbulb = ddd.material("LightLampOff", color='e8e0e4')
        self.light_green = ddd.material(color='#00ff00')
        self.light_orange = ddd.material(color='#ffff00')
        self.light_red = ddd.material(color='#ff0000')

        # Trees
        self.bark = ddd.material(name="Bark", color='#df9e75')
        self.treetop = ddd.material(name="Treetop", color='#1da345')

        # Urban props materials
        self.fence = ddd.material(name="Fence", color='282024', extra={'ddd:transparent': True})
        self.railing = ddd.material(name="Fence", color='282024', extra={'ddd:transparent': True})
        self.metallic_grid = ddd.material(name="Fence", color='#28281e', extra={'ddd:transparent': True})  # Floors

        self.cable_metal = ddd.material(name="CableMetal", color='#28282e')
        self.chain = ddd.material(name="CableMetal", color='#28282e')
        self.rope = ddd.material(name="Rope", color='#c7b01c')

        # Buildings
        self.building_1 = ddd.material(color='#f7f0be')
        self.building_2 = ddd.material(color='#bdb9a0')
        self.building_3 = ddd.material(color='#c49156')
        self.roof_tiles = ddd.material("RoofTiles", color='#f25129')


        # Colors
        self.red = ddd.material(color='#ff0000')
        self.green = ddd.material(color='#00ff00')
        self.blue = ddd.material(color='#0000ff')


