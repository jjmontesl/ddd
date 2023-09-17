# ddd - DDD123
# Library for simple scene modelling.
# Jose Juan Montes 2020-2022

import logging
from ddd.ddd import ddd
from ddd.materials.materials import MaterialsCollection

# Get instance of logger for this module
logger = logging.getLogger(__name__)


class DefaultMaterials(MaterialsCollection):
    """
    A list of materials that is used by some packs to assign default materials to objects.

    This object is available through 'ddd.mats', and it can be overriden or members added dynamically
    (also see: MaterialsCollection).
    """

    def __init__(self):

        # Various
        self.logo = ddd.material(name="DDD Logo", color='#7ed956',
                                 metallic_factor=1.0, roughness_factor=0.00,  # index_of_refraction=1.36,
                                 texture_path=ddd.DATA_DIR + "/materials/dddlogo.png")

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

        self.rock_black = ddd.material(name="Rock Black", color='#5f5f4d')  # formerly named simply "Rock"
        self.rock_lightbrown = ddd.material(name="Rock Orange", color='#bd8658')
        self.rock = self.rock_black

        self.terrain_ground = ddd.material(name="Ground Clear", color='#a48f74')
        self.terrain_pebbles_sparse = ddd.material(name="Ground Pebbles Sparse", color='#e6821e')
        self.terrain_veg_dead_sparse = ddd.material(name="Ground Veg Dead Sparse", color='#8c6d2a')
        self.terrain = self.terrain_veg_dead_sparse.copy("Ground")


        self.sand = ddd.material(name="Sand", color='#fff694')
        self.wetland = ddd.material(name="Wetland", color='#54610c')

        self.pavement = ddd.material(name="Sidewalk", color='#c0c0b0')
        self.sett = ddd.material(name="Sett", color='#7b719f')
        self.sidewalk = ddd.material(name="Sidewalk", color='#e0d0d0')

        self.pitch = ddd.material(name="Pitch", color='#196118')
        self.pitch_blue = ddd.material(name="Pitch Blue", color='#2a69b0')  # Eg. cycleways
        self.pitch_red = ddd.material(name="Pitch Red", color='#b34446')  # Eg. leisure track

        self.painted_line = ddd.material(name="Painted Line", color='#ffffff',
                                         metallic_factor=0.0, roughness_factor=1.0,
                                         extra={'zoffset': -8.5, 'ddd:collider': False, 'ddd:shadows': False})  # Eg. leisure track

        # Structural / building materials
        self.bronze = ddd.material(name="Bronze", color='#f0cb11', metallic_factor=0.95, roughness_factor=0.25)
        self.steel = ddd.material(name="Steel", color='#78839c', metallic_factor=0.975, roughness_factor=0.125)
        self.metal = self.steel

        #self.stones_black...
        #self.stones

        #self.stone_white...
        self.stone = ddd.material(name="Stone", color='#9c9378')

        self.bricks = ddd.material(name="Bricks", color='#d49156')
        self.bricks_raw = ddd.material(name="Bricks Raw", color='#d49156')
        self.cement = ddd.material(name="Cement", color='#b8b8a0')
        self.concrete = ddd.material(name="Concrete", color='#a9b7ba')
        self.concrete_planks = ddd.material(name="Concrete Planks", color='#8e999c')

        self.clay = ddd.material(name="Clay", color='#e57757', metallic_factor=0.02, roughness_factor=0.85)  # E.g. pottery...

        self.granite_polished = ddd.material(name="Granite Polished", color='#9e9380', metallic_factor=0.025, roughness_factor=0.2)
        self.granite = self.stone

        self.marble_white = ddd.material(name="Marble White", color='#c0c3c8', metallic_factor=0.4, roughness_factor=0.05)

        self.porcelain_white = ddd.material("Porcelain White", color='#f2f5fe', metallic_factor=0.2, roughness_factor=0.2)
        self.porcelain = self.porcelain_white

        # Tiles (bathrooms, kitchens, pools) - made of porcelain, etc (not floor or wooden tiles)
        self.porcelain_blue_tiles = ddd.material("Porcelain Blue Tiles", color='#1a6fbf', 
                                                metallic_factor=0.15, roughness_factor=0.3)
        self.porcelain_blue_tiles_round = ddd.material("Porcelain Blue Tiles Round", color='#166fcf', 
                                                metallic_factor=0.05, roughness_factor=0.5)

        # Woods and natural materials
        self.wood = ddd.material(name="Wood", color='#efae85', metallic_factor=0.0, roughness_factor=0.7)
        self.wood_planks = ddd.material(name="Wood Planks", color='#b57857', metallic_factor=0.0, roughness_factor=0.6)
        self.wood_planks_stained = ddd.material(name="Wood Planks Stained", color='#856231', metallic_factor=0.0, roughness_factor=0.65)


        # Painted materials
        self.metal_paint_red = ddd.material("PaintRed", color='#d01010', metallic_factor=0.975, roughness_factor=0.2)
        self.metal_paint_green = ddd.material("PaintGreen", color='#265e13', metallic_factor=0.975, roughness_factor=0.2)
        self.metal_paint_yellow = ddd.material("PaintYellow", color='#ebe015', metallic_factor=0.975, roughness_factor=0.2)
        self.metal_paint_blue = ddd.material("PaintBlue", color='#184794', metallic_factor=0.975, roughness_factor=0.3)
        self.metal_paint_white = ddd.material("PaintWhite", color='#f8fbff', metallic_factor=0.975, roughness_factor=0.2)
        self.metal_paint_black = ddd.material("PaintBlack", color='#000a17', metallic_factor=0.975, roughness_factor=0.2)

        # Lights
        self.lightbulb = ddd.material("LightLampOff", color='e8e0e4')
        self.light_green = ddd.material("LightGreen", color='#00ff00')
        self.light_orange = ddd.material("LightOrange", color='#ffff00')
        self.light_red = ddd.material("LightRed", color='#ff0000')
        self.light_yellow = ddd.material("LightYellow", color='#ffff00')

        # Plastics
        self.plastic_transparent = ddd.material("Plastic Transparent", color='e8e0e4', metallic_factor=0.0, roughness_factor=0.7, extra={'ddd:transparent': True})  # name="PlasticTransparent",
        self.plastic_black = ddd.material("Plastic Black", color='#2c2936', metallic_factor=0.0, roughness_factor=0.43)
        self.plastic_black_ridges = ddd.material("Plastic Black Ridges", color='#1a1821', metallic_factor=0.1, roughness_factor=0.0) 
        self.plastic_red = ddd.material("Plastic Red", color='#cc2b2b', metallic_factor=0.0, roughness_factor=0.7)
        self.plastic_green = ddd.material("Plastic Green", color='#64a80a', metallic_factor=0.0, roughness_factor=0.7)
        self.plastic_yellow = ddd.material("Plastic Yellow", color='#fffb08', metallic_factor=0.0, roughness_factor=0.7)
        self.plastic_blue = ddd.material("Plastic Blue", color='#1763bf', metallic_factor=0.0, roughness_factor=0.7)
        self.plastic_white = ddd.material("Plastic White", color='#f2f5f7', metallic_factor=0.0, roughness_factor=0.7)

        # Fabrics
        self.carpet_red = ddd.material("Carpet Red", color='#9c0b0b', metallic_factor=0.0, roughness_factor=0.975)

        # Glass
        # FIXME: ddd:reflection, which semantically relates to mirrors / reflective surfaces (rel: reflection probes) in VRS, should NOT be a default for glass (which does requires env reflections but not necessarily a probe)
        self.glass = ddd.material("Glass", color=[46/255, 65/255, 63/255, 0.5], metallic_factor=0.5, roughness_factor=0.0, extra={'ddd:transparent': True, 'ddd:reflection': True}, alpha_mode='BLEND')  #  , extra={'ddd:transparent': True}
        self.glass_red = ddd.material("Glass Red", color=[255/255, 65/255, 63/255, 0.5], metallic_factor=0.5, roughness_factor=0.0, extra={'ddd:transparent': True, 'ddd:reflection': True}, alpha_mode='BLEND')  #  , extra={'ddd:transparent': True}
        
        self.glass_mirror = ddd.material("Glass", color=[46/255, 65/255, 63/255, 0.5], metallic_factor=0.9, roughness_factor=0.0, extra={'ddd:transparent': False, 'ddd:reflection': True})  #  , extra={'ddd:transparent': True}

        # Vegetation (trees, hedges)
        self.bark = ddd.material(name="Bark", color='#df9e75')
        self.treetop = ddd.material(name="Treetop", color='#1da345', extra={'ddd:collider': False})
        #self.hedge = 

        # Grass and flowers blades
        self.flowers_blue_blade = ddd.material(name="Flowers Blue", color='#51b8da', metallic_factor=0.0, roughness_factor=0.90, 
                                               double_sided=True, alpha_mode='MASK',
                                               extra={'ddd:collider': False})
        self.flowers_roses_blade = ddd.material(name="Flowers Roses", color='#e96969',
                                                metallic_factor=0.0, roughness_factor=0.95,
                                                double_sided=True, alpha_mode='MASK',
                                                extra={'ddd:collider': False})
        self.grass_blade = ddd.material(name="Grass Blade", color='#2de355',
                                        metallic_factor=0.0, roughness_factor=1.00,
                                        double_sided=True, alpha_mode='MASK',
                                        extra={'ddd:collider': False})
        self.grass_blade_dry = ddd.material(name="Grass Blade Dry", color='#956542',
                                            metallic_factor=0.0, roughness_factor=1.00,
                                            double_sided=True, alpha_mode='MASK',
                                            extra={'ddd:collider': False})    

        # Urban props materials
        self.fence = ddd.material(name="Fence", color='282024', extra={'ddd:transparent': True})
        self.railing = ddd.material(name="Fence", color='282024', extra={'ddd:transparent': True})
        self.metallic_grid = ddd.material(name="Fence", color='#28281e', extra={'ddd:transparent': True})  # Floors

        self.chain = ddd.material(name="Chain", color='#202022')
        self.rope = ddd.material(name="Rope", color='#c7b01c')
        self.cable_metal = self.metal #   ddd.material(name="CableMetal", color='#1a1a20')  # Aluminum matte coated/ high voltage lines

        self.rubber_orange = ddd.material(name="Rubber Orange", color="#8B4513", metallic_factor=0.01, roughness_factor=0.9)

        # Interior (props) materials
        self.paper = ddd.material(name="Paper", color='#f2f5f7', metallic_factor=0.0, roughness_factor=0.8)

        self.ball_soccer = ddd.material(name="Ball Soccer", color="#f8f8f8", metallic_factor=0.04, roughness_factor=0.5)
        self.ball_basketball = self.rubber_orange

        # Buildings
        self.building_1 = ddd.material(color='#f7f0be')
        self.building_2 = ddd.material(color='#bdb9a0')
        self.building_3 = ddd.material(color='#c49156')
        self.roof_tiles = ddd.material("RoofTiles", color='#f25129')

        # Transparents
        #self.transparent_green = ddd.material("Transparent Green", color='#00ff00', extra={'ddd:transparent': True})

        # Colors
        self.red = ddd.material("Color Red", color='#ff0000')
        self.green = ddd.material("Color Green", color='#00ff00')  # Should be 008000
        self.blue = ddd.material("Color Blue", color='#0000ff')
        self.white = ddd.material("Color White", color='#ffffff')
        self.black = ddd.material("Color Black", color='#000000')

        self.brown = ddd.material("Color Brown", color='#a52a2a')
        self.crimson = ddd.material("Color Crimson", color='#dc143c')
        self.coral = ddd.material("Color Crimson", color='#ff7f50')
        self.cyan = ddd.material("Color Cyan", color='#00ffff')
        self.darkblue = ddd.material("Color DarkBlue", color='#00008b')
        self.darkslategrey = ddd.material("Color DarkSlateGrey", color='#2f4f4f')
        self.darkturquoise = ddd.material("Color DarkTurquoise", color='#00ced1')
        self.gray = ddd.material("Color Gray", color='#808080')
        self.orange = ddd.material("Color Orange", color='#ffa500')
        self.yellow = ddd.material("Color Yellow", color='#ffff00')
        self.pink = ddd.material("Color Pink", color='#ffc0cb')
        self.violet = ddd.material("Color Violet", color='#ee82ee')

