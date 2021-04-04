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
    ddd.mats.railway = ddd.material(name="RoadRailway", color="#47443e",
                                    metallic_factor=1.0, roughness_factor=0.43, index_of_refraction=1.0, direct_lighting=0.76, bump_strength=2.0,
                                    texture_path=ddd.DATA_DIR + "/osmmaterials/RoadRailway/TexturesCom_Road_Railway_512_albedo.png",
                                    texture_normal_path=ddd.DATA_DIR + "/osmmaterials/RoadRailway/TexturesCom_Road_Railway_512_normal.png",
                                    #alpha_cutoff=0.05,
                                    extra={})

    ddd.mats.roadline = ddd.material(name="Roadline", color='#e8e8e8',
                                 texture_path=ddd.DATA_DIR + "/materials/road_signs/RoadLines_alb.png",
                                 texture_normal_path=ddd.DATA_DIR + "/materials/road_signs/RoadLines_normal.jpg",
                                 alpha_cutoff=0.05,
                                 extra={'ddd:collider': False, 'ddd:shadows': False, 'uv:scale': 0.05, 'zoffset': -8.5})
    ddd.mats.roadline_red = ddd.material(name="Roadline Red", color='#f8a8a8',
                                 texture_path=ddd.DATA_DIR + "/materials/road_signs/RoadLines_alb.png",
                                 texture_normal_path=ddd.DATA_DIR + "/materials/road_signs/RoadLines_normal.jpg",
                                 alpha_cutoff=0.05,
                                 extra={'ddd:collider': False, 'ddd:shadows': False, 'uv:scale': 0.05, 'zoffset': -8.5})

    ddd.mats.roadmarks = ddd.material(name="Roadmarks", color='#e8e8e8',
                                 texture_path=ddd.DATA_DIR + "/osmmaterials/RoadMarks/TexturesCom_Atlas_RoadMarkings2_White_1K_albedo_with_alpha.png",
                                 texture_normal_path=ddd.DATA_DIR + "/osmmaterials/RoadMarks/TexturesCom_Atlas_RoadMarkings2_1K_normal.png",
                                 alpha_cutoff=0.05,
                                 extra={'ddd:collider': False, 'ddd:shadows': False, 'uv:scale': 1.00, 'zoffset': -8.5})

    ddd.mats.traffic_signs = ddd.material(name="TrafficSigns", color="#ffffff", #color="#e01010",
                                      texture_path=ddd.DATA_DIR  + "/materials/traffic_signs/traffic_signs_es_0.png",
                                      atlas_path=ddd.DATA_DIR  + "/materials/traffic_signs/traffic_signs_es_0.plist")

    ddd.mats.asphalt = ddd.material(name="Asphalt", color='#202020', extra={'uv:scale': 1.0},  # 0.25  color='#202020',
                                    metallic_factor=0.0, roughness_factor=0.43, index_of_refraction=1.0, direct_lighting=0.76, bump_strength=2.0,
                                    texture_path=ddd.DATA_DIR + "/osmmaterials/Asphalt/Asphalt01_col.jpg",
                                    texture_normal_path=ddd.DATA_DIR + "/osmmaterials/Asphalt/Asphalt01_nrm.jpg",)

    ddd.mats.pathwalk = ddd.material(name="WayPedestrian", color='#78281e', extra={'uv:scale': 1.0 },  # 0.25
                                     texture_path=ddd.DATA_DIR + "/osmmaterials/Tiles26/Tiles26_col.jpg",
                                     texture_normal_path=ddd.DATA_DIR + "/osmmaterials/Tiles26/Tiles26_nrm.jpg",)

    '''
    # Areas
    self.sea = ddd.material(name="Water4Advanced", color='#3d43b5', extra={'ddd:collider': False, 'ddd:shadows': False, 'ddd:transparent': True})
    self.water = ddd.material(name="WaterBasicDaytime", color='#4d53c5', extra={'ddd:collider': False, 'ddd:shadows': False, 'ddd:transparent': True})
    self.volumetricgrass = ddd.material(name="VolumetricGrass", color='#2dd355', extra={'ddd:export-as-marker': True})  # Warning: duplicated in areas_3d volumetic grass generation
    '''

    ddd.mats.dirt = ddd.material(name="Dirt", color="#b58800", extra={'uv:scale': 1.0},  # 0.25
                                 metallic_factor=0.0, roughness_factor=1.0, bump_strength=2.0,
                                 texture_path=ddd.DATA_DIR + "/osmmaterials/Ground32/Ground32_col.jpg",
                                 texture_normal_path=ddd.DATA_DIR + "/osmmaterials/Ground32/Ground32_nrm.jpg",)

    ddd.mats.grass = ddd.material(name="Grass", color='#2dd355', extra={'uv:scale': 1.0},  # 0.25
                                 metallic_factor=0.35, roughness_factor=0.85, index_of_refraction=1.36, bump_strength=2.0,
                                 texture_path=ddd.DATA_DIR + "/osmmaterials/Grass01/Grass_01_2K_Base_Color.png",
                                 texture_normal_path=ddd.DATA_DIR + "/osmmaterials/Grass01/Grass_01_2K_Normal.png",)

    ddd.mats.park = ddd.material(name="Park", color='#1db345', extra={'uv:scale': 1.0},  # 0.25
                                 metallic_factor=0.3, roughness_factor=0.85, index_of_refraction=1.36, bump_strength=2.0,
                                 texture_path=ddd.DATA_DIR + "/osmmaterials/Ground03/Ground03_col.jpg",
                                 texture_normal_path=ddd.DATA_DIR + "/osmmaterials/Ground03/Ground03_nrm.jpg",)

    ddd.mats.terrain = ddd.material(name="Ground", color='#e6821e', extra={'uv:scale': 1.0},  # 0.2
                                    metallic_factor=0.0, roughness_factor=1.0, bump_strength=2.0,
                                    texture_path=ddd.DATA_DIR + "/osmmaterials/Ground23/Ground23_col.jpg",
                                    texture_normal_path=ddd.DATA_DIR + "/osmmaterials/Ground23/Ground23_nrm.jpg",)

    ddd.mats.sidewalk = ddd.material(name="Sidewalk", color='#f1f1f1', extra={'uv:scale': 1.0},  # 0.2
                                     texture_path=ddd.DATA_DIR + "/osmmaterials/Tiles38/Tiles38_col.jpg",
                                     texture_normal_path=ddd.DATA_DIR + "/osmmaterials/Tiles38/Tiles38_nrm.jpg",)
    ddd.mats.pavement = ddd.material(name="Pavement", color='#e1e1e1', extra={'uv:scale': 1.0},  # 0.2
                                     texture_path=ddd.DATA_DIR + "/osmmaterials/Tiles38/Tiles38_col.jpg",
                                     texture_normal_path=ddd.DATA_DIR + "/osmmaterials/Tiles38/Tiles38_nrm.jpg",)

    ddd.mats.pitch_green = ddd.material(name="Pitch", color='#196118', extra={'uv:scale': 1.0},  # 0.2
                                  texture_path=ddd.DATA_DIR + "/osmmaterials/[2K]Concrete17/Concrete17_col.jpg",
                                  texture_normal_path=ddd.DATA_DIR + "/osmmaterials/[2K]Concrete17/Concrete17_nrm.jpg",)
    ddd.mats.pitch_blue = ddd.material(name="Pitch Blue", color='#2a69b0', extra={'uv:scale': 1.0},  # 0.2
                                  texture_path=ddd.DATA_DIR + "/osmmaterials/[2K]Concrete17/Concrete17_col.jpg",
                                  texture_normal_path=ddd.DATA_DIR + "/osmmaterials/[2K]Concrete17/Concrete17_nrm.jpg",)  # Eg. cycleways
    ddd.mats.pitch_red = ddd.material(name="Pitch Red", color='#b34446', extra={'uv:scale': 1.0},  # 0.2
                                  texture_path=ddd.DATA_DIR + "/osmmaterials/[2K]Concrete17/Concrete17_col.jpg",
                                  texture_normal_path=ddd.DATA_DIR + "/osmmaterials/[2K]Concrete17/Concrete17_nrm.jpg",)  # Eg. leisure track
    ddd.mats.pitch = ddd.mats.pitch_green

    '''
    self.forest = ddd.material(name="Forest", color='#3a6e17')
    self.garden = ddd.material(name="Garden", color='#2f614b')
    self.rock = ddd.material(name="Rock", color='#5f5f4d')
    self.sand = ddd.material(name="Sand", color='#fff694')
    self.wetland = ddd.material(name="Wetland", color='#54610c')

    self.sett = ddd.material(name="Sett", color='#7b719f')


    # Structural / building materials
    self.bronze = ddd.material(name="Bronze", color='#f0cb11')
    self.steel = ddd.material(name="Steel", color='#78839c')
    self.metal = ddd.material(name="Steel", color='#68738c')

    self.stone = ddd.material(name="Stone", color='#9c9378')
    '''
    ddd.mats.cement = ddd.material(name="Concrete", color='#b8b8a0', extra={'uv:scale': 1.0},  #
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
    '''

    # Urban props materials
    ddd.mats.fence = ddd.material(name="Fence", color='282024', extra={'ddd:transparent': True},
                                  texture_path=ddd.DATA_DIR + "/osmmaterials/MetalWalkway002_2K-JPG/MetalWalkway002_2K_ColorAlpha.png",
                                  texture_normal_path=ddd.DATA_DIR + "/osmmaterials/MetalWalkway002_2K-JPG/MetalWalkway002_2K_Normal.jpg",
                                  alpha_cutoff=0.05)
    ddd.mats.railing = ddd.mats.fence
    ddd.mats.metallic_grid = ddd.material(name="MetallicGrid", color='#28281e', extra={'ddd:transparent': True})  # Floors

    '''
    self.cable_metal = ddd.material(name="CableMetal", color='#28282e')
    self.chain = ddd.material(name="CableMetal", color='#28282e')
    self.rope = ddd.material(name="Rope", color='#c7b01c')

    # Buildings
    self.building_1 = ddd.material(color='#f7f0be')
    self.building_2 = ddd.material(color='#bdb9a0')
    self.building_3 = ddd.material(color='#c49156')
    '''

    ddd.mats.roof_tiles = ddd.material("RoofTiles", color='f25129', extra={'uv:scale': 1.0},   # 0.25  # color='#f19f70',
                                       metallic_factor=0.0, roughness_factor=0.7, index_of_refraction=1.08, bump_strength=2.0,
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

