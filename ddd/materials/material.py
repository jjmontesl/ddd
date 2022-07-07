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

import logging
import os

import numpy as np
import PIL
import trimesh
from csg import geom as csggeom
from ddd.core.cli import D1D2D3Bootstrap
from ddd.materials.atlas import TextureAtlas
from PIL import Image
from trimesh.scene.scene import Scene, append_scenes
from trimesh.transformations import quaternion_from_euler
from trimesh.visual.color import ColorVisuals
from trimesh.visual.material import PBRMaterial, SimpleMaterial
from trimesh.visual.texture import TextureVisuals

# Get instance of logger for this module
logger = logging.getLogger(__name__)


class DDDMaterial():

    _texture_cache = {}

    # These need to be sorted from longer to shorter
    TEXTURE_DISCOVER = {
        'albedo': ['_Base_Color', '_Color', '_ColorAlpha', '_albedo', '_col', '_alb' ],
        'normal': ['_Normal', '_NormalGL', '_normal', '_nrm'],
        'displacement': ['_Height', '_Displacement', '_Disp', '_disp', '_dis'],
        'roughness': ['_Roughness', '_rgh'],
        'emissive': ['_Emission'],
        #: ['_AO', ],
    }

    @staticmethod
    def load_texture_cached(path, material=None):
        """
        If material is passed, its metadata is used.

        Will automatically resample a texture if ddd:texture:resize` is set in
        the passed material or in the config (in that order).
        """
        image = DDDMaterial._texture_cache.get(path, None)
        if image is None:
            image = PIL.Image.open(path)

            # Resample texture if needed
            resample_size = None  # 512
            resample_size = D1D2D3Bootstrap.data.get('ddd:texture:resize', resample_size)
            if material:
                resample_size = material.extra.get('ddd:texture:resize', resample_size)
            if resample_size:
                resample_size = int(resample_size)

            if resample_size and resample_size > 0 and image.size[0] > resample_size:
                logger.info("Resampling texture to %dx%d: %s", resample_size, resample_size, path)
                image = image.resize((resample_size, resample_size), PIL.Image.BICUBIC)

            DDDMaterial._texture_cache[path] = image

        return image

    def __init__(self, name=None, color=None, extra=None, texture_color=None, texture_path=None, atlas_path=None, alpha_cutoff=None, alpha_mode=None, texture_normal_path=None,
                 metallic_factor=None, roughness_factor=None, index_of_refraction=None, direct_lighting=None, bump_strength=None, double_sided=False,
                 texture_displacement_path=None, #displacement_strength=1.0,
                 texture_roughness_path=None,
                 emissive_factor=None, texture_emissive_path=None):
        """
        A name based on the color will be assigned if not set.
            - texture_color: optional color to be used if a textured material is being generated (--export-texture), instead of the default color.
            - alpha_mode: one of OPAQUE, BLEND and MASK (used with alpha_cutoff)

        TODO: texture_color was a hack and it's being used inconsistently, along with vertex colors usage which need to be reviewed and its impact on BabylonJS checked

        Color is hex color.
        """

        self.name = name if name else "Color_%s" % (color)
        self.extra = extra if extra else {}

        self.color = color
        self.color_rgba = None
        if self.color:
            self.color_rgba = trimesh.visual.color.hex_to_rgba(self.color)

        self.texture_color = texture_color
        self.texture_color_rgba = None
        if self.texture_color:
            self.texture_color_rgba = trimesh.visual.color.hex_to_rgba(self.texture_color)

        self.alpha_cutoff = alpha_cutoff
        self.alpha_mode = alpha_mode

        self.texture = texture_path
        #self._texture_cached = None  # currently a PIL image, shall be a DDDTexture
        self.texture_normal_path = texture_normal_path
        #self._texture_normal_cached = None
        self.texture_displacement_path = texture_displacement_path
        #self._texture_displacement_cached = None
        self.texture_roughness_path = texture_roughness_path

        self.emissive_factor = emissive_factor
        self.texture_emissive_path = texture_emissive_path

        self.metallic_factor = metallic_factor
        self.roughness_factor = roughness_factor
        #self.index_of_refraction = index_of_refraction
        #self.direct_lighting = direct_lighting
        #self.bump_strength = bump_strength
        self.double_sided = double_sided

        '''
        if name and ' ' in name:
            raise DDDException("Spaces in material names are not allowed (TODO: check what he root cause was): %s", self.name)
        if name is None:
            logger.warn("Material with no name: %s", self)
        '''

        self.atlas = None
        self.atlas_path = atlas_path
        if atlas_path:
            self.load_atlas(atlas_path)

        self._trimesh_material_cached = None

        if self.texture and '*' in self.texture:
            self.auto_texture_discover()

    def __repr__(self):
        return "DDDMaterial(name=%r, color=%r)" % (self.name, self.color)

    def __hash__(self):
        return abs(hash((self.name, self.color)))  #, self.extra)))

    def copy(self, name):
        result = DDDMaterial(name, color=self.color, extra=dict(self.extra), texture_color=self.texture_color, texture_path=self.texture,
                             atlas_path=self.atlas_path, alpha_cutoff=self.alpha_cutoff, alpha_mode=self.alpha_mode,
                             texture_normal_path=self.texture_normal_path, metallic_factor=self.metallic_factor, roughness_factor=self.roughness_factor,
                             index_of_refraction=None, direct_lighting=None, bump_strength=None, double_sided=self.double_sided,
                             texture_displacement_path=self.texture_displacement_path, texture_roughness_path=self.texture_roughness_path,
                             emissive_factor=self.emissive_factor, texture_emissive_path=self.texture_emissive_path)
        return result

    def _trimesh_material(self):
        """
        Returns a Trimesh material for this DDDMaterial.
        Materials are cached to avoid repeated materials and image loading (which may crash the app).
        """
        if not hasattr(self, "texture_normal_path"): self.texture_normal_path = None # quick fix for older catalog pickles, can be removed
        if self._trimesh_material_cached is None:
            if self.texture and D1D2D3Bootstrap.export_textures:
                im = self.get_texture()
                if self.texture:  # and (self.alpha_cutoff or self.alpha_mode or self.texture_normal_path):
                    alpha_mode = self.alpha_mode if self.alpha_mode else ('MASK' if self.alpha_cutoff else 'OPAQUE')
                    im_normal = self.get_texture_normal() if self.texture_normal_path else None
                    im_emissive = self.get_texture_emissive() if self.texture_emissive_path else None
                    im_metallicroughness = self.get_texture_roughness() if self.texture_roughness_path else None
                    mat = PBRMaterial(name=self.name, baseColorTexture=im, baseColorFactor=self.texture_color_rgba if self.texture_color_rgba is not None else self.color_rgba,
                                      normalTexture=im_normal, doubleSided=self.double_sided,
                                      metallicRoughnessTexture=im_metallicroughness,
                                      metallicFactor=self.metallic_factor, roughnessFactor=self.roughness_factor,
                                      alphaMode=alpha_mode, alphaCutoff=self.alpha_cutoff,
                                      emissiveFactor=np.array([self.emissive_factor, self.emissive_factor, self.emissive_factor, 1.0][:3]), emissiveTexture=im_emissive)  # , ambient, specular, glossiness)
                else:
                    #mat = SimpleMaterial(name=self.name, image=im, diffuse=self.color_rgba)  # , ambient, specular, glossiness)
                    alpha_mode = self.alpha_mode if self.alpha_mode else ('MASK' if self.alpha_cutoff else 'OPAQUE')
                    mat = PBRMaterial(name=self.name, baseColorFactor=self.texture_color_rgba if self.texture_color_rgba is not None else self.color_rgba,
                                      doubleSided=self.double_sided, metallicFactor=self.metallic_factor, roughnessFactor=self.roughness_factor,
                                      alphaMode=alpha_mode, alphaCutoff=self.alpha_cutoff,
                                      emissiveFactor=self.emissive_factor)  # , ambient, specular, glossiness)
            else:
                mat = SimpleMaterial(name=self.name, diffuse=self.color_rgba)
            #mat = PBRMaterial(doubleSided=True)  # , emissiveFactor= [0.5 for v in self.mesh.vertices])
            self._trimesh_material_cached = mat
        return self._trimesh_material_cached

    def _auto_texture_discover_try(self, basepath, patterns):
        # Try also patterns without '_', in case path is defined as "texture_*"
        for p in list(patterns):
            if p.startswith("_"):
                patterns.append(p[1:])
        for pattern in patterns:
            trypath = basepath.replace('*', pattern)
            if os.path.exists(trypath):
                return trypath
        return None

    def auto_texture_discover(self):
        """
        Tries to automatically discover textures trying common name patterns.
        """
        basepath = self.texture
        self.texture = self._auto_texture_discover_try(basepath, self.TEXTURE_DISCOVER['albedo'])
        self.texture_normal_path = self._auto_texture_discover_try(basepath, self.TEXTURE_DISCOVER['normal'])
        self.texture_displacement_path = self._auto_texture_discover_try(basepath, self.TEXTURE_DISCOVER['displacement'])
        self.texture_roughness_path = self._auto_texture_discover_try(basepath, self.TEXTURE_DISCOVER['roughness'])
        self.texture_emissive_path = self._auto_texture_discover_try(basepath, self.TEXTURE_DISCOVER['emissive'])

    def load_atlas(self, filepath):
        self.atlas = TextureAtlas.load_atlas(filepath)

    def get_texture(self):
        """
        Returns the texture (currently a PIL image).
        Returns a cached image if available.
        """
        if not self.texture:
            return None
        #if not self._texture_cached:
        #    self._texture_cached = PIL.Image.open(self.texture)
        #return self._texture_cached
        return DDDMaterial.load_texture_cached(self.texture, self)

    def get_texture_normal(self):
        """
        Returns the normal texture.
        Returns a cached image if available.
        """
        if not self.texture_normal_path:
            return None
        #if not self._texture_normal_cached:
        #    self._texture_normal_cached = PIL.Image.open(self.texture_normal_path)
        #return self._texture_normal_cached
        return DDDMaterial.load_texture_cached(self.texture_normal_path, self)

    def get_texture_displacement(self):
        """
        Returns the displacement texture.
        Returns a cached image if available.
        """
        if not self.texture_displacement_path:
            return None
        #if not self._texture_displacement_cached:
        #    self._texture_displacement_cached = PIL.Image.open(self.texture_displacement_path)
        #return self._texture_displacement_cached
        return DDDMaterial.load_texture_cached(self.texture_displacement_path, self)

    def get_texture_roughness(self):
        """
        Returns the roughness texture.
        Returns a cached image if available.
        """
        if not self.texture_roughness_path:
            return None
        #if not self._texture_displacement_cached:
        #    self._texture_displacement_cached = PIL.Image.open(self.texture_displacement_path)
        #return self._texture_displacement_cached
        return DDDMaterial.load_texture_cached(self.texture_roughness_path, self)

    def get_texture_emissive(self):
        """
        Returns the emissive texture.
        Returns a cached image if available.
        """
        if not self.texture_emissive_path:
            return None
        #if not self._texture_displacement_cached:
        #    self._texture_displacement_cached = PIL.Image.open(self.texture_displacement_path)
        #return self._texture_displacement_cached
        return DDDMaterial.load_texture_cached(self.texture_emissive_path, self)

