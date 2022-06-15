# ddd - DDD123
# Library for simple scene modelling.
# Jose Juan Montes and Contributors 2019-2021

from ddd.ddd import ddd
from ddd.pack.symbols.dddlogo import dddlogo
from ddd.pipeline.decorators import dddtask


@dddtask(order="10")
def pipeline_start(pipeline, root):
    """
    Tests subdivision on several geometries (check wireframe).
    """

    root = ddd.group3(name="Root")
    pipeline.root = root

    logo = dddlogo()

    root.append(logo)
    #root.append(ddd.helper.all(center=[10, 10, 1]))

    root.save("/tmp/logo.fbx")
    root.dump()
    #root.show()


