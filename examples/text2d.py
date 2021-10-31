# ddd - DDD123
# Library for simple scene modelling.
# Jose Juan Montes and Contributors 2019-2021

from ddd.ddd import ddd
from ddd.pipeline.decorators import dddtask
from ddd.text.text2d import Text2D
from ddd.text.font import DDDFontAtlas

"""
Atlas is generated using:

    ddd font-generate


"""

@dddtask()
def pipeline_start(pipeline, root, logger):
    """
    Test 2D text generation.
    """
    #pipeline.data['font'] = Font()
    pipeline.data['font:atlas:opensansemoji64'] = ddd.material(name="FontOpenSansEmoji-64", color='#f88888',
                                                texture_path=ddd.DATA_DIR + "/fontatlas/opensansemoji64.greyscale.png",
                                                #texture_normal_path=ddd.DATA_DIR + "/materials/road-marks-es/TexturesCom_Atlas_RoadMarkings2_1K_normal.png",
                                                #atlas_path="/materials/road-marks-es/RoadMarkings2.plist",
                                                alpha_cutoff=0.5, metallic_factor=0.0, roughness_factor=1.0,
                                                extra={'ddd:material:type': 'font', 'ddd:collider': False, 'ddd:shadows': False, 'uv:scale': 1.00, 'zoffset': -5.0, 'ddd:texture:resize': 4096})

    pipeline.data['font:atlas:dddfonts_01_64'] = ddd.material(name="DDDFonts-01-64", color='#f88888',
                                                texture_path=ddd.DATA_DIR + "/fontatlas/dddfonts_01_64.greyscale.png",
                                                #texture_normal_path=ddd.DATA_DIR + "/materials/road-marks-es/TexturesCom_Atlas_RoadMarkings2_1K_normal.png",
                                                #atlas_path="/materials/road-marks-es/RoadMarkings2.plist",
                                                alpha_cutoff=0.5, metallic_factor=0.0, roughness_factor=1.0,
                                                extra={'ddd:material:type': 'font', 'ddd:collider': False, 'ddd:shadows': False, 'uv:scale': 1.00, 'zoffset': -5.0, 'ddd:texture:resize': 4096})


#/home/jjmontes/git/ddd/data/fonts/extra/Adolphus.ttf
#/home/jjmontes/git/ddd/data/fonts/extra/LinBiolinum_RB.ttf
#/home/jjmontes/git/ddd/data/fonts/extra/Oliciy.ttf
#/home/jjmontes/git/ddd/data/fonts/extra/TechnaSans-Regular.ttf

def image_textured(filename):

    material = ddd.material(texture_path=filename)  # name="Image: %s" % filename

    plane = ddd.rect(name="Image Rect").triangulate().material(material)
    plane = ddd.uv.map_cubic(plane)
    plane = plane.rotate(ddd.ROT_FLOOR_TO_FRONT)
    plane = plane.scale([5, 1, 5])
    plane = plane.translate([0, 1, 0])

    return plane

@dddtask()
def pipeline_text_textureimage(pipeline, root):
    """
    Show a rect with the full atlas texture.
    """
    item = image_textured(ddd.DATA_DIR + "/fontatlas/dddfonts_01_64.greyscale.png").translate([-8, 0, 0])
    item = item.material(pipeline.data['font:atlas:dddfonts_01_64'])
    #item = item.material(ddd.MAT_HIGHLIGHT)
    root.append(item)

@dddtask()
def pipeline_text_2d(pipeline, root):
    """
    """

    #ddd.disc(r=5).subtract(ddd.disc(r=3)).extrude(0.2).show()

    #test_str = "Filarmónica !\"$%&/() 🌟 😀 🎩 🐲 - iüáí¿?¡!"
    test_str = "Filarmónica pidgeon !\"·$%&/() 🌟 😀 🎩 🐲 - iüáíñÑçÇñÁÉÄÖ~ ¿?¡!"
    atlas = DDDFontAtlas.load_atlas(ddd.DATA_DIR + "/fontatlas/dddfonts_01_64.dddfont.json")

    fontfaces = ['OpenSansEmoji-default-64', 'Oliciy-default-64', 'TechnaSans-default-64', 'Adolphus-default-64' ]

    for idx, fontface in enumerate(fontfaces):
        text2d = Text2D(atlas, fontface=fontface)
        result = text2d.text(test_str)

        result = result.material(pipeline.data['font:atlas:dddfonts_01_64'])
        result = result.rotate(ddd.ROT_FLOOR_TO_FRONT)
        result = result.translate([0, 0, 2 * idx])

        root.append(result)

    root.append(ddd.helper.all(size=20.0, center=[2, 2, 0]))

    #root.show()

