# ddd - DDD123
# Library for simple scene modelling.
# Jose Juan Montes and Contributors 2019-2021

from ddd.ddd import ddd
from ddd.pipeline.decorators import dddtask


@dddtask(order="10")
def pipeline_start(pipeline, root):
    """
    Tests subdivision on several geometries (check wireframe).
    """

    items = ddd.group3()

    # Subdivision to grid
    fig1 = ddd.rect([-4, -2, 4, 2])
    fig2 = ddd.rect([-3, -1, -1, 1])
    figh = fig1.subtract(fig2)
    fig = figh.extrude_step(figh, 1.0, base=True, method=ddd.EXTRUSION_METHOD_SUBTRACT)
    fig = fig.extrude_step(figh.buffer(-0.25), 1.0, method=ddd.EXTRUSION_METHOD_SUBTRACT)
    fig = fig.material(ddd.mats.logo)
    fig = ddd.uv.map_cubic(fig)
    fig = ddd.meshops.subdivide_to_grid(fig, 0.5)

    root.append(fig)

    fig.show()

    #root.save("/tmp/export_fbx.fbx")
    fig.save("/tmp/export_fbx.fbx")



