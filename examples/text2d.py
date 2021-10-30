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
    pipeline.data['font:material'] = ddd.material(name="Font2", color='#f88888',
                                                  texture_path="test-greyscale.png",
                                                  #texture_normal_path=ddd.DATA_DIR + "/materials/road-marks-es/TexturesCom_Atlas_RoadMarkings2_1K_normal.png",
                                                  #atlas_path="/materials/road-marks-es/RoadMarkings2.plist",
                                                  alpha_cutoff=0.5, metallic_factor=0.0, roughness_factor=1.0,
                                                  extra={'ddd:collider': False, 'ddd:shadows': False, 'uv:scale': 1.00, 'zoffset': -5.0, 'ddd:texture:resize': 4096})

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
    item = image_textured("test-greyscale.png")
    #item = item.material(ddd.MAT_HIGHLIGHT)
    item = item.material(pipeline.data['font:material'])
    root.append(item)

@dddtask()
def pipeline_text_2d(pipeline, root):
    """
    """

    #ddd.disc(r=5).subtract(ddd.disc(r=3)).extrude(0.2).show()

    #test_str = "Filarmónica !\"$%&/() 🌟 😀 🎩 🐲 - iüáí¿?¡!"
    test_str = "Filarmónica pidgeon !\"·$%&/() 🌟 😀 🎩 🐲 - iüáíñÑçÇñÁÉÄÖ~ ¿?¡!"
    atlas = DDDFontAtlas.load_atlas("test-font.dddfont.json")
    text2d = Text2D(atlas)
    result = text2d.text(test_str)
    #result.dump()
    result = result.material(pipeline.data['font:material'])
    #result = result.material(ddd.MAT_HIGHLIGHT)
    result = result.rotate(ddd.ROT_FLOOR_TO_FRONT)
    #result = result.scale([4, 1, 4])
    #result = result.rotate(ddd.ROT_TOP_HALFTURN)

    root.append(result)
    root.append(ddd.helper.all(size=20.0, center=[2, 2, 0]))


    result.show()
