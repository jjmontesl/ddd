# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging
import os
import plistlib
import sys

from ddd.core.exception import DDDException
from trimesh.visual.material import SimpleMaterial


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class TextureAtlasSprite():
    """
    A rectangular sprite in a texture atlas. 
    
    The sprite is defined by its bounds in pixels and normalized into the texture size. It may be rotated.
    """

    def __init__(self, name, bounds_pixel, bounds_norm, rot):
        self.name = name
        self.bounds_pixel = bounds_pixel
        self.bounds_norm = bounds_norm
        self.rot = rot
        #self.texture =

    def __repr__(self):
        return "%s (%s, %s, rot=%s)" % (self.name, self.bounds_pixel, self.bounds_norm, self.rot)


class TextureAtlas():
    """
    TODO: Support multiple textures atlas (wrap texture atlas and materials, allow to retrieve sprite+material)
    """

    def __init__(self):

        self.sprites = {}
        #self.texture = None
        self.texture_width = None
        self.texture_height = None

    @staticmethod
    def load_atlas(filepath):
        """
        Process a Texture Atlas definition file, in PropertyList file (plistlib) format generated by PyTexturePack.

        This method creates a TextureAtlasSprite for each sprite in the atlas, 
        and provides methods to retrieve them by name.
        """

        # Open file
        try:
            with open(filepath, 'rb') as fp:
                pl = plistlib.load(fp)
        except:
            raise DDDException("Could not load atlas texture definition from: %s" % (filepath,) )

        atlas = TextureAtlas()
        texture_size = pl['metadata']['size'][1:-1].split(",")
        atlas.texture_width = int(texture_size[0])
        atlas.texture_height = int(texture_size[1])

        # Process the atlas descriptor (creating TextureAtlasSprite objects)
        #print(pl)
        for key, frame in pl['frames'].items():
            bounds_str = frame['frame']
            bounds_str_split = bounds_str[1:-1].split(",")
            bounds_str_min, bounds_str_max = ",".join(bounds_str_split[:2]), ",".join(bounds_str_split[2:]),
            bounds_str_min = bounds_str_min[1:-1].split(",")
            bounds_str_max = bounds_str_max[1:-1].split(",")
            bounds_pixel = [int(bounds_str_min[0]), int(bounds_str_min[1]),
                            int(bounds_str_min[0]) + int(bounds_str_max[0]), int(bounds_str_min[1]) + int(bounds_str_max[1])]
            bounds_norm = [bounds_pixel[0] / atlas.texture_width, bounds_pixel[1] / atlas.texture_height,
                           bounds_pixel[2] / atlas.texture_width, bounds_pixel[3] / atlas.texture_height]
            rotated = frame['rotated']
            sprite = TextureAtlasSprite(key, bounds_pixel, bounds_norm, rotated)
            atlas.sprites[key.lower()] = sprite

        logger.info("Loaded texture atlas %s with %d sprites.", filepath, len(atlas.sprites))
        return atlas

    def keys(self):
        return list(self.sprites.keys())

    def sprite(self, key):
        return self.sprites[key.lower()]


class TextureAtlasUtils():

    def create_sprite_from_atlas(self, material, sprite_key):
        """
        Creates a 2D quad with the given sprite from the given material (which must have an asociated texture atlas).

        The quad UV coordinates are mapped to the sprite bounds in the atlas.

        TODO: examples where this is used, how this works 2d vs 3d...
        """
        
        from ddd.ddd import ddd
        sprite = material.atlas.sprite(sprite_key)

        plane = ddd.rect(name="Texture Atlas Sprite Rect: %s" % sprite_key)  #.triangulate().material(material)
        plane = plane.material(material)
        plane = ddd.uv.map_2d_linear(plane)

        plane = plane.recenter()

        if sprite.rot:
            plane.extra['uv'] = [(sprite.bounds_norm[0] + (sprite.bounds_norm[3] - sprite.bounds_norm[1]) * v[1],
                                  1.0 - (sprite.bounds_norm[1] + (sprite.bounds_norm[2] - sprite.bounds_norm[0]) * v[0]))
                                  for v in plane.extra['uv']]
        else:
            plane.extra['uv'] = [(sprite.bounds_norm[0] + (sprite.bounds_norm[2] - sprite.bounds_norm[0]) * v[0],
                                  1.0 - (sprite.bounds_norm[1] + (sprite.bounds_norm[3] - sprite.bounds_norm[1]) * (1 - v[1])))
                                  for v in plane.extra['uv']]

        #plane = plane.translate([-0.5, -0.5, 0]).scale([plane, plane, 1]).translate([0, plane / 2, 0])
        #decal = decal.rotate(ddd.ROT_FLOOR_TO_FRONT).translate([0, -thick / 2 - 0.005, 0])
        #decal.extra['ddd:shadows'] = False
        #decal.extra['ddd:collider'] = False

        # TODO: TEMP: Rope Cow / Godot export
        # plane.extra['uv'] = [(1024 - v[1] * 1024.0, v[0] * 1024.0) for v in plane.extra['uv']]  # temp: transposed and scaled
        #print(plane.extra['uv'])

        plane.extra['ddd:sprite'] = True
        plane.extra['ddd:sprite:bounds'] = sprite.bounds_pixel

        return plane

    def create_sprite_rect(self, material):
        """
        Createds a sprite rect using a single image (from a material).
        """

        from ddd.ddd import ddd

        plane = ddd.rect(name="Sprite Rect")  #.triangulate().material(material)
        plane = plane.material(material)
        plane = ddd.uv.map_2d_linear(plane)

        plane = plane.recenter()

        texture_size = material.get_texture().size
        sprite = TextureAtlasSprite("sprite", [0, 0, texture_size[0], texture_size[1]], [0.0, 0.0, 1.0, 1.0], False)

        if sprite.rot:
            plane.extra['uv'] = [(sprite.bounds_norm[0] + (sprite.bounds_norm[3] - sprite.bounds_norm[1]) * v[1],
                                  1.0 - (sprite.bounds_norm[1] + (sprite.bounds_norm[2] - sprite.bounds_norm[0]) * v[0]))
                                  for v in plane.extra['uv']]
        else:
            plane.extra['uv'] = [(sprite.bounds_norm[0] + (sprite.bounds_norm[2] - sprite.bounds_norm[0]) * v[0],
                                  1.0 - (sprite.bounds_norm[1] + (sprite.bounds_norm[3] - sprite.bounds_norm[1]) * (1 - v[1])))
                                  for v in plane.extra['uv']]

        #plane = plane.scale(texture_size)

        #plane = plane.translate([-0.5, -0.5, 0]).scale([plane, plane, 1]).translate([0, plane / 2, 0])
        #decal = decal.rotate(ddd.ROT_FLOOR_TO_FRONT).translate([0, -thick / 2 - 0.005, 0])
        #decal.extra['ddd:shadows'] = False
        #decal.extra['ddd:collider'] = False

        # TODO: TEMP: Rope Cow / Godot export
        #plane.extra['uv'] = [(texture_size[1] - v[1] * texture_size[1], v[0] * texture_size[0]) for v in plane.extra['uv']]  # temp: transposed and scaled

        plane.extra['ddd:sprite'] = True
        plane.extra['ddd:sprite:bounds'] = sprite.bounds_pixel


        return plane

