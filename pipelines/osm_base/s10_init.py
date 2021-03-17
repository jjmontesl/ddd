# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020

import sys

import pyproj

from ddd.ddd import ddd
from ddd.geo import terrain
from ddd.osm import osm
from ddd.osm.osm import project_coordinates
from ddd.pipeline.decorators import dddtask

"""
"""


@dddtask(order="10")
def osm_init(pipeline, root):
    """
    Pipeline initialization (variables, etc).
    """
    pass

@dddtask()
def osm_materials():

    # Materials used by this pipeline
    ddd.mats.railway = ddd.material(name="RoadRailway", color="#47443e")
    ddd.mats.roadline = ddd.material(name="Roadline", color='#e8e8e8',
                                 texture_path=ddd.DATA_DIR + "/materials/road_signs/RoadLines_alb.png",
                                 texture_normal_path=ddd.DATA_DIR + "/materials/road_signs/RoadLines_normal.jpg",
                                 alpha_cutoff=0.05,
                                 extra={'ddd:collider': False, 'ddd:shadows': False, 'uv:scale': 0.05})
    ddd.mats.traffic_signs = ddd.material(name="TrafficSigns", color="#ffffff", #color="#e01010",
                                      texture_path=ddd.DATA_DIR  + "/materials/traffic_signs/traffic_signs_es_0.png",
                                      atlas_path=ddd.DATA_DIR  + "/materials/traffic_signs/traffic_signs_es_0.plist")

    ddd.mats.asphalt = ddd.material(name="Asphalt", color='#202020', extra={'uv:scale': 0.5},
                                    texture_path=ddd.DATA_DIR + "/osmmaterials/Asphalt/Asphalt01_col.jpg",
                                    texture_normal_path=ddd.DATA_DIR + "/osmmaterials/Asphalt/Asphalt01_nrm.jpg",)

    ddd.mats.pathwalk = ddd.material(name="WayPedestrian", color='#78281e', extra={'uv:scale': 0.25},
                                     texture_path=ddd.DATA_DIR + "/osmmaterials/Tiles26/Tiles26_col.jpg",
                                     texture_normal_path=ddd.DATA_DIR + "/osmmaterials/Tiles26/Tiles26_nrm.jpg",)

    '''

    # Areas
    self.sea = ddd.material(name="Water4Advanced", color='#3d43b5', extra={'ddd:collider': False, 'ddd:shadows': False, 'ddd:transparent': True})
    self.water = ddd.material(name="WaterBasicDaytime", color='#4d53c5', extra={'ddd:collider': False, 'ddd:shadows': False, 'ddd:transparent': True})
    self.volumetricgrass = ddd.material(name="VolumetricGrass", color='#2dd355', extra={'ddd:export-as-marker': True})  # Warning: duplicated in areas_3d volumetic grass generation
    '''

    ddd.mats.dirt = ddd.material(name="Dirt", color="#b58800", extra={'uv:scale': 0.25},
                                 texture_path=ddd.DATA_DIR + "/osmmaterials/Ground32/Ground32_col.jpg",
                                 texture_normal_path=ddd.DATA_DIR + "/osmmaterials/Ground32/Ground32_nrm.jpg",)

    ddd.mats.grass = ddd.material(name="Grass", color='#2dd355', extra={'uv:scale': 0.5},
                                 texture_path=ddd.DATA_DIR + "/osmmaterials/Grass01/Grass_01_2K_Base_Color.png",
                                 texture_normal_path=ddd.DATA_DIR + "/osmmaterials/Grass01/Grass_01_2K_Normal.png",)

    ddd.mats.park = ddd.material(name="Park", color='#1db345', extra={'uv:scale': 0.25},
                                 texture_path=ddd.DATA_DIR + "/osmmaterials/Ground03/Ground03_col.jpg",
                                 texture_normal_path=ddd.DATA_DIR + "/osmmaterials/Ground03/Ground03_nrm.jpg",)

    ddd.mats.terrain = ddd.material(name="Ground", color='#e6821e', extra={'uv:scale': 0.2},
                                    texture_path=ddd.DATA_DIR + "/osmmaterials/Ground23/Ground23_col.jpg",
                                    texture_normal_path=ddd.DATA_DIR + "/osmmaterials/Ground23/Ground23_nrm.jpg",)

    ddd.mats.sidewalk = ddd.material(name="Sidewalk", color='#e0d0d0', extra={'uv:scale': 0.2},
                                     texture_path=ddd.DATA_DIR + "/osmmaterials/Tiles38/Tiles38_col.jpg",
                                     texture_normal_path=ddd.DATA_DIR + "/osmmaterials/Tiles38/Tiles38_nrm.jpg",)
    ddd.mats.pavement = ddd.material(name="Pavement", color='#c0c0b0', extra={'uv:scale': 0.2},
                                     texture_path=ddd.DATA_DIR + "/osmmaterials/Tiles38/Tiles38_col.jpg",
                                     texture_normal_path=ddd.DATA_DIR + "/osmmaterials/Tiles38/Tiles38_nrm.jpg",)

    '''
    self.forest = ddd.material(name="Forest", color='#3a6e17')
    self.garden = ddd.material(name="Garden", color='#2f614b')
    self.rock = ddd.material(name="Rock", color='#5f5f4d')
    self.sand = ddd.material(name="Sand", color='#fff694')
    self.wetland = ddd.material(name="Wetland", color='#54610c')

    self.sett = ddd.material(name="Sett", color='#7b719f')

    self.pitch = ddd.material(name="Pitch", color='#196118')
    self.pitch_blue = ddd.material(name="Pitch Blue", color='#2a69b0')  # Eg. cycleways
    self.pitch_red = ddd.material(name="Pitch Red", color='#b34446')  # Eg. leisure track

    # Structural / building materials
    self.bronze = ddd.material(name="Bronze", color='#f0cb11')
    self.steel = ddd.material(name="Steel", color='#78839c')
    self.metal = ddd.material(name="Steel", color='#68738c')

    self.stone = ddd.material(name="Stone", color='#9c9378')
    '''
    ddd.mats.cement = ddd.material(name="Concrete", color='#b8b8a0', extra={'uv:scale': 0.5},
                                   texture_path=ddd.DATA_DIR + "/osmmaterials/[2K]Concrete17/Concrete17_col.jpg",
                                   texture_normal_path=ddd.DATA_DIR + "/osmmaterials/[2K]Concrete17/Concrete17_nrm.jpg",)
    '''
    self.bricks = ddd.material(name="Bricks", color='#d49156')

    self.wood = ddd.material(name="Wood", color='#efae85')

    # Painted materials
    self.metal_paint_red = ddd.material("PaintRed", color='#d01010')
    self.metal_paint_green = ddd.material("PaintGreen", color='#265e13')
    self.metal_paint_yellow = ddd.material("PaintYellow", color='#ebe015')
    self.metal_paint_blue = ddd.material("PaintBlue", color='#184794')
    self.metal_paint_white = ddd.material("PaintWhite", color='#f8fbff')
    self.metal_paint_black = ddd.material("PaintYellow", color='#000a17')

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
    '''

    ddd.mats.roof_tiles = ddd.material("RoofTiles", color='#f25129', extra={'uv:scale': 0.25},
                                       texture_path=ddd.DATA_DIR + "/osmmaterials/[2K]RoofingTiles05/RoofingTiles05_col.jpg",
                                       texture_normal_path=ddd.DATA_DIR + "/osmmaterials/[2K]RoofingTiles05/RoofingTiles05_nrm.jpg",)

    '''
    # Colors
    self.red = ddd.material(color='#ff0000')
    self.green = ddd.material(color='#00ff00')
    self.blue = ddd.material(color='#0000ff')
    '''


@dddtask(order="50.999999", log=True)
def osm_finish_rest_before_3d(pipeline, osm, root, logger):

    # Generate items for point features
    ##osm.items.generate_items_1d()

    pass

