# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020

import sys

import numpy as np
from PIL import Image

from ddd.ddd import ddd, DDDMaterial
from ddd.pipeline.decorators import dddtask
from ddd.pipeline.pipeline import DDDPipeline
import PIL

"""
Collects materials and exports them in different formats:

- As GLB file.
- As texture atlas (textures are first converted to linear color space).

Run as:

    ddd osm_materials.py  --export-textures --cache-clear [-p ddd:texture:resize=256]
"""

pipeline = DDDPipeline(['pipelines.osm_base.s10_init.py',
                        ], name="OSM Build Pipeline")

# TODO: Move to init?
#osmbuilder = osm.OSMBuilder(area_crop=area_crop, area_filter=area_filter, osm_proj=osm_proj, ddd_proj=ddd_proj)
pipeline.data['osm'] = None

@dddtask()
def materials_list(root, osm):

    mats = ddd.group3(name="Materials")
    root.append(mats)

    # Avoid exporting the same material twice
    added_names = []

    for key in dir(ddd.mats):
        mat = getattr(ddd.mats, key)
        if isinstance(mat, DDDMaterial):
            if mat.name not in added_names:

                '''
                # This was a test, but these materials need not be converted to linear color space
                if mat.texture:
                    albedo_image = DDDMaterial.load_texture_cached(mat.texture)
                    albedo_array = np.array(albedo_image)
                    albedo_array_linear = convert_to_linear(albedo_array[:,:,:3])
                    if albedo_array.shape[2] == 4:
                        albedo_array_linear_rgba = np.empty((albedo_array.shape[0], albedo_array.shape[1], 4))
                        albedo_array_linear_rgba[:,:,:3] = albedo_array_linear[:,:,:]
                        albedo_array_linear_rgba[:,:,3] = albedo_array[:,:,3]
                    image_linear = Image.fromarray(np.uint8(albedo_array_linear), "RGBA" if albedo_array_linear.shape[2] == 4 else "RGB")
                    DDDMaterial._texture_cache[mat.texture] = image_linear
                '''

                marker = ddd.marker(name=mat.name)
                marker = marker.material(mat)
                mats.append(marker)
                added_names.append(mat.name)

@dddtask()
def materials_show(root):
    mats = root.find("/Materials")
    mats = ddd.align.grid(mats, space=2.0)
    mats.show()

@dddtask()
def materials_save(pipeline, root):
    material_texsize = int(pipeline.data.get('ddd:texture:resize', None))
    mats = root.find("/Materials")
    mats = ddd.align.grid(mats, space=2.0)  # Not really needed for export
    mats.save('catalog_materials-default%d.glb' % material_texsize)

def convert_to_linear(im):
    # From: https://stackoverflow.com/questions/31300865/srgb-aware-image-resize-in-pillow

    # Convert to numpy array of float
    arr = np.array(im, dtype=np.float32) / 255.0
    # Convert sRGB -> linear
    arr = np.where(arr <= 0.04045, arr/12.92, ((arr+0.055)/1.055)**2.4)
    arrOut = np.uint8(np.rint(arr * 255.0))
    return arrOut


@dddtask()
def materials_pack_atlas(root, logger):

    atlas_texsize = int(pipeline.data.get('ddd:texture:resize', None))
    atlas_cols = 4
    atlas_rows = 4

    mats = [
        ddd.mats.terrain,
        ddd.mats.dirt,
        ddd.mats.asphalt,
        ddd.mats.pavement,

        ddd.mats.sidewalk,
        ddd.mats.pathwalk,
        ddd.mats.terrain,
        ddd.mats.terrain, #None,

        ddd.mats.grass,
        ddd.mats.garden,
        ddd.mats.park,
        ddd.mats.forest,

        ddd.mats.sand,
        ddd.mats.rock,
        ddd.mats.terrain_rock,
        ddd.mats.terrain_ground,
        ]

    #mats = [ddd.mats.pathwalk, ddd.mats.park, ddd.mats.terrain, ddd.mats.dirt] * 4

    texture_albedo = np.zeros((atlas_texsize * atlas_rows, atlas_texsize * atlas_cols, 4))
    texture_normals = np.zeros((atlas_texsize * atlas_rows, atlas_texsize * atlas_cols, 4))

    mat_idx = 0
    for row in range(atlas_rows):
        for col in range(atlas_cols):

            mat = mats[mat_idx]
            mat_idx += 1

            if mat is None:
                continue

            atposx = atlas_texsize * col
            atposy = atlas_texsize * row

            albedo_image = DDDMaterial.load_texture_cached(mat.texture, mat)
            albedo_array = np.array(albedo_image)

            # Linearize
            albedo_array = convert_to_linear(albedo_array)

            # Colorize
            texture_color_rgba = np.array(mat.texture_color_rgba if mat.texture_color_rgba is not None else mat.color_rgba)
            colorize_strength = 0.5
            white = np.array([255, 255, 255])
            texture_color_rgba[:3] = texture_color_rgba[:3] + (white - texture_color_rgba[:3]) * (1.0 - colorize_strength)
            albedo_array[:,:,:3] = ((albedo_array[:,:,:3] / 255) * (texture_color_rgba[:3] / 255)) * 255

            texture_albedo[atposy:atposy + atlas_texsize, atposx:atposx + atlas_texsize, 0:3] = albedo_array[:,:,0:3]
            albedo_array_padded = np.array(Image.fromarray(albedo_array).resize((atlas_texsize - 2, atlas_texsize - 2), PIL.Image.LANCZOS))  # Resize -2 and pad
            texture_albedo[atposy+1:atposy + atlas_texsize - 1, atposx + 1:atposx + atlas_texsize - 1, 0:3] = albedo_array_padded[:,:,0:3]

            # Encode displacement/height in the alpha channel
            displacement_image = mat.get_texture_displacement()
            if displacement_image:
                displacement_array = np.array(displacement_image)
                texture_albedo[atposy:atposy + atlas_texsize, atposx:atposx + atlas_texsize, 3] = displacement_array[:,:]
            else:
                texture_albedo[atposy:atposy + atlas_texsize, atposx:atposx + atlas_texsize, 3] = 128

            #texture_albedo[atposy:atposy + atlas_texsize, atposx:atposx + atlas_texsize, 3] = 255

            # Normals
            normals_image = mat.get_texture_normal()
            normals_array = np.array(normals_image)
            texture_normals[atposy:atposy + atlas_texsize, atposx:atposx + atlas_texsize, 0] = normals_array[:,:,0]
            texture_normals[atposy:atposy + atlas_texsize, atposx:atposx + atlas_texsize, 1] = normals_array[:,:,1]
            texture_normals[atposy:atposy + atlas_texsize, atposx:atposx + atlas_texsize, 2] = normals_array[:,:,2]

            # Roughnes
            rough_image = mat.get_texture_roughness()
            if rough_image:
                rough_array = np.array(rough_image)
                texture_normals[atposy:atposy + atlas_texsize, atposx:atposx + atlas_texsize, 3] = rough_array[:,:]
            else:
                texture_normals[atposy:atposy + atlas_texsize, atposx:atposx + atlas_texsize, 3] = 128

            # roughness + ?

    filename = "splatmap-textures-atlas-%d.png" % atlas_texsize
    logger.info("Writing texture atlas to: %s", filename)
    im = Image.fromarray(np.uint8(texture_albedo), "RGBA")
    im.save(filename, "PNG")
    #im.save(pipeline.data['filenamebase'] + ".splatmap-4chan-0_3-" + str(splatmap_size) + ".png", "PNG")

    im = Image.fromarray(np.uint8(texture_normals), "RGBA")
    im.save("splatmap-textures-atlas-normals-%d.png" % atlas_texsize, "PNG")
    #im.save(pipeline.data['filenamebase'] + ".splatmap-4chan-0_3-" + str(splatmap_size) + ".png", "PNG")


pipeline.run()


