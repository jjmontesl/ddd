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
- As texture atlas (textures are converted to linear color space first).

This is run as:

    ddd osm_materials.py  --export-textures

The result is then copied to the client app, eg:

    cp catalog_materials.glb ~/git/ddd-viewer2/public/assets/

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

    for key in dir(ddd.mats):
        mat = getattr(ddd.mats, key)
        if isinstance(mat, DDDMaterial):
            marker = ddd.marker(name=mat.name)
            marker = marker.material(mat)
            mats.append(marker)

@dddtask()
def materials_show(root):
    mats = root.find("/Materials")
    mats = ddd.align.grid(mats, space=2.0)
    mats.show()

@dddtask()
def materials_save(root):
    material_texsize = 512
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

    atlas_texsize = 512
    atlas_cols = 4
    atlas_rows = 4

    mats = [
        ddd.mats.terrain,
        ddd.mats.dirt,
        ddd.mats.asphalt,
        ddd.mats.pavement,

        ddd.mats.sidewalk,
        ddd.mats.pathwalk,
        ddd.mats.terrain, #None,
        ddd.mats.terrain, #None,

        ddd.mats.grass,
        ddd.mats.garden,
        ddd.mats.park,
        ddd.mats.forest,

        ddd.mats.sand,
        ddd.mats.rock,
        ddd.mats.terrain, #None,
        ddd.mats.terrain, #None
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

            albedo_image = DDDMaterial.load_texture_cached(mat.texture)
            albedo_array = np.array(albedo_image)
            albedo_array = convert_to_linear(albedo_array)
            texture_albedo[atposy:atposy + atlas_texsize, atposx:atposx + atlas_texsize, 0:3] = albedo_array[:,:,0:3]
            albedo_array_padded = np.array(Image.fromarray(albedo_array).resize((atlas_texsize - 2, atlas_texsize - 2), PIL.Image.LANCZOS))  # Resize -2 and pad
            texture_albedo[atposy+1:atposy + atlas_texsize - 1, atposx + 1:atposx + atlas_texsize - 1, 0:3] = albedo_array_padded[:,:,0:3]
            texture_albedo[atposy:atposy + atlas_texsize, atposx:atposx + atlas_texsize, 3] = 255

            normals_image = DDDMaterial.load_texture_cached(mat.texture_normal)
            normals_array = np.array(normals_image)
            texture_normals[atposy:atposy + atlas_texsize, atposx:atposx + atlas_texsize, 0] = normals_array[:,:,0]
            texture_normals[atposy:atposy + atlas_texsize, atposx:atposx + atlas_texsize, 1] = normals_array[:,:,1]
            texture_normals[atposy:atposy + atlas_texsize, atposx:atposx + atlas_texsize, 2] = normals_array[:,:,2]
            texture_normals[atposy:atposy + atlas_texsize, atposx:atposx + atlas_texsize, 3] = 255


    filename = "/tmp/splatmap-textures-atlas-%d.png" % atlas_texsize
    logger.info("Writing texture atlas to: %s", filename)
    im = Image.fromarray(np.uint8(texture_albedo), "RGBA")
    im.save(filename, "PNG")
    #im.save(pipeline.data['filenamebase'] + ".splatmap-4chan-0_3-" + str(splatmap_size) + ".png", "PNG")

    im = Image.fromarray(np.uint8(texture_normals), "RGBA")
    im.save("/tmp/splatmap-textures-atlas-normals-%d.png" % atlas_texsize, "PNG")
    #im.save(pipeline.data['filenamebase'] + ".splatmap-4chan-0_3-" + str(splatmap_size) + ".png", "PNG")


pipeline.run()


