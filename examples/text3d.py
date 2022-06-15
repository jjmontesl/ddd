# ddd - DDD123
# Library for simple scene modelling.
# Jose Juan Montes and Contributors 2019-2021

from ddd.ddd import ddd
from ddd.pipeline.decorators import dddtask
from ddd.text.text3d import Text3D


@dddtask()
def pipeline_start(pipeline, root, logger):
    """
    Test 3D text generation.
    """
    #pipeline.data['font'] = Font()
    pass

@dddtask()
def pipeline_text_3d(pipeline, root):
    """
    """

    #ddd.disc(r=5).subtract(ddd.disc(r=3)).extrude(0.2).show()

    #test_str = "Filarmónica !\"$%&/() 🌟 😀 🎩 🐲 - iüáí¿?¡!"
    test_str = "Filarmónica pidgeon !\"·$%&/() 🌟 😀 🎩 🐲 - iüáíñÑçÇñÁÉÄÖ~ ¿?¡!"

    text3d = Text3D()
    result = text3d.text(test_str)
    #result = result.buffer(0.05)
    result = result.extrude(0.2)
    result = result.rotate(ddd.ROT_FLOOR_TO_FRONT)
    #result.simplify(0.005).extrude(0.2).show()

    result = result.smooth()
    result = result.material(ddd.mats.marble_white)
    result = ddd.uv.map_cubic(result, split=False)

    root.append(result)
    root.append(ddd.helper.all(size=20.0, center=[2, 2, 0]))

    root.show()

