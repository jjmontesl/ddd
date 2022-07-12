# Jose Juan Montes 2019-2021

"""
Tests several 2D and 3D geometry operations.
"""

from ddd.pack.sketchy import urban, landscape
from ddd.ddd import ddd
import math
import sys
from ddd.text.text3d import Text3D
import logging

from ddd.pipeline.decorators import dddtask


@dddtask()
def pipeline_start(pipeline, root):
    """
    Generate different geometric objects.
    """

    items = ddd.group3()

    # Remember to use JOIN_ROUND so resolution is applied when buffering points
    fig = ddd.point([0, 0]).buffer(1.0, resolution=2, join_style=ddd.JOIN_ROUND, cap_style=ddd.CAP_ROUND).triangulate()
    items.append(fig)
    fig = ddd.point([0, 0]).buffer(1.0, resolution=3, join_style=ddd.JOIN_ROUND, cap_style=ddd.CAP_ROUND).triangulate()
    items.append(fig)
    fig = ddd.point([0, 0]).buffer(1.0, resolution=4, join_style=ddd.JOIN_ROUND, cap_style=ddd.CAP_ROUND).triangulate()
    items.append(fig)

    # Extrusion with optional caps
    fig = ddd.disc().extrude(5)
    items.append(fig)
    fig = ddd.disc().extrude(5, base=False)
    items.append(fig)
    fig = ddd.disc().extrude(5, cap=False)
    items.append(fig)
    fig = ddd.disc().extrude(5, cap=False, base=False)
    items.append(fig)


    # Extrude line (to faces, not volume)
    fig1 = ddd.line([[-2, 0], [0, 0], [2, 2]])
    fig = fig1.extrude(2.0).twosided()
    items.append(fig)

    # Extrusion to line (explicit)
    fig1 = ddd.rect([-4, -2, 4, 2])
    fig2 = ddd.line([[-4, 0], [4, 0]])
    fig = fig1.extrude_step(fig2, 1.0)
    items.append(fig)

    # Extrusion to line (explicit)
    fig1 = ddd.rect([-4, -2, 4, 2])
    fig2 = ddd.line([[-3, 0], [3, 0]])
    fig = fig1.extrude_step(fig2, 1.0)
    items.append(fig)

    # Extrusion to line (explicit, method subtract)
    fig1 = ddd.rect([-4, -2, 4, 2])
    fig2 = ddd.line([[-3, 0], [3, 0]])
    fig = fig1.extrude_step(fig2, 1.0, method=ddd.EXTRUSION_METHOD_SUBTRACT)  # TODO: this currently fails but should be fixed
    items.append(fig)

    # Extrusion to line with vertical (explicit) for skillion roofs
    fig1 = ddd.rect([-4, -2, 4, 2])
    fig2 = ddd.line([[-4, 2], [4, 2]])
    fig = fig1.extrude_step(fig2, 1.0)  # TODO: this currently fails but should be fixed
    items.append(fig)

    # Extrusion to line (axis middle)
    fig1 = ddd.rect([-4, -2, 4, 2]) #.rotate(math.pi * 1.5)
    axis_major, axis_minor, axis_angle = ddd.geomops.oriented_axis(fig1)
    fig = fig1.extrude_step(axis_minor, 1.0)
    items.append(fig)

    # Extrusion to line (axis middle)
    fig1 = ddd.rect([-4, -2, 4, 2]) #.rotate(math.pi * 1.5)
    axis_major, axis_minor, axis_angle = ddd.geomops.oriented_axis(fig1)
    fig = fig1.extrude_step(axis_major, 1.0)
    items.append(fig)

    # Extrusion to line (buffered geometry) - currently fails (shapely does not return the reduced polygon linestring)
    fig1 = ddd.rect([-4, -2, 4, 2])
    fig = fig1.extrude_step(fig1.buffer(-2.5), 1.0)
    items.append(fig)

    # Extrusion to line (buffered geometry) and back (fails, extrusion from point to shape)
    fig1 = ddd.rect([-4, -2, 4, 2])
    fig = fig1.extrude_step(fig1.buffer(-2.5), 1.0)
    fig = fig.extrude_step(fig1, 1.0)
    items.append(fig)

    # Triangulation with hole
    fig1 = ddd.rect([-4, -2, 4, 2])
    fig2 = ddd.rect([-3, -1, -1, 1])
    fig = fig1.subtract(fig2).triangulate()
    items.append(fig)

    # Extrusion with hole
    fig1 = ddd.rect([-4, -2, 4, 2])
    fig2 = ddd.rect([-3, -1, -1, 1])
    fig = fig1.subtract(fig2).extrude(1.0)
    items.append(fig)

    # Extrusion with steps with hole
    fig1 = ddd.rect([-4, -2, 4, 2])
    fig2 = ddd.rect([-3, -1, -1, 1])
    figh = fig1.subtract(fig2)
    fig = figh.extrude_step(figh, 1.0, base=False)
    fig = fig.extrude_step(figh.buffer(-0.25), 1.0)
    items.append(fig)

    # Extrusion with steps with hole 2
    fig1 = ddd.rect([-4, -2, 4, 2])
    fig2 = ddd.rect([-3, -1, -1, 1])
    figh = fig1.subtract(fig2)
    fig = figh.extrude_step(figh, 1.0, base=False, method=ddd.EXTRUSION_METHOD_SUBTRACT)
    fig = fig.extrude_step(figh.buffer(-0.25), 1.0, method=ddd.EXTRUSION_METHOD_SUBTRACT)
    items.append(fig)


    # Simple extrusion
    fig = ddd.point([0, 0]).buffer(1.0, cap_style=ddd.CAP_ROUND).extrude(5.0)
    items.append(fig)

    # Simple extrusion
    fig = ddd.regularpolygon(5).extrude(5.0)
    items.append(fig)


    # Simple extrusion no caps
    fig = ddd.point([0, 0]).buffer(1.0, cap_style=ddd.CAP_ROUND)
    fig = fig.extrude_step(fig, 5.0, base=False, cap=False)
    items.append(fig)

    # Extrusion between shapes
    fig1 = ddd.point([0, 0]).buffer(1.0)
    fig2 = ddd.point([0, 0]).buffer(1.0, cap_style=ddd.CAP_ROUND)
    fig3 = ddd.point([0, 0]).buffer(1.0)
    fig = fig1.extrude_step(fig2, 3.0).extrude_step(fig3, 2.0)
    items.append(fig)

    # Extrusion
    fig = ddd.point([0, 0]).buffer(1.0)
    for i in range(10):
        fign = ddd.point([0, 0]).buffer(1.0).rotate(math.pi / 12 * i)
        fig = fig.extrude_step(fign, 0.5)
    items.append(fig)

    # Pointy end
    fig = ddd.point().buffer(2.0, cap_style=ddd.CAP_ROUND)
    fig = fig.extrude_step(ddd.point(), 5.0)
    items.append(fig)

    # Convex shapes (this fails)
    coords = [[10, 10], [5, 9], [3, 12], [1, 5], [-8, 0], [10, 0]]
    #coords.reverse()
    fig = ddd.polygon(coords).scale(0.25)
    fig = fig.extrude_step(fig.buffer(-0.5), 1)
    items.append(fig)

    # Convex shapes - subtract method (works)
    coords = [[10, 10], [5, 9], [3, 12], [1, 5], [-8, 0], [10, 0]]
    #coords.reverse()
    fig = ddd.polygon(coords).scale(0.25)
    fig = fig.extrude_step(fig.buffer(-0.5), 1, method=ddd.EXTRUSION_METHOD_SUBTRACT)
    items.append(fig)

    # Extrude-subtract to bigger
    fig = ddd.point([0, 0]).buffer(1.0, cap_style=ddd.CAP_ROUND)
    fig = fig.extrude_step(fig.buffer(1.0), 5.0, method=ddd.EXTRUSION_METHOD_SUBTRACT)
    items.append(fig)

    # Extrude-subtract downwards
    shape = ddd.disc().scale([3, 2])
    fig = shape.extrude_step(shape.buffer(-0.5), -1.0, base=False, method=ddd.EXTRUSION_METHOD_SUBTRACT)
    fig = fig.extrude_step(shape.buffer(-1.0), -0.5, method=ddd.EXTRUSION_METHOD_SUBTRACT)
    items.append(fig)

    # Extrude-subtract vertical case
    fig = ddd.point([0, 0]).buffer(1.0, cap_style=ddd.CAP_ROUND)
    fig = fig.extrude_step(fig, 5.0, method=ddd.EXTRUSION_METHOD_SUBTRACT)
    items.append(fig)

    # Convex shapes with holes - subtract method
    fig = ddd.group3()
    text = Text3D.quick_text("86A").scale(2.0)
    for f in text.children:
        #f.replace(f.subtract(f.buffer(-0.2)))
        fe = f.extrude_step(f.buffer(-0.05), 0.2, method=ddd.EXTRUSION_METHOD_SUBTRACT)
        fig.append(fe)
    items.append(fig)

    # Extrude to point
    fig = ddd.point([0, 0]).buffer(1.0, cap_style=ddd.CAP_ROUND)
    fig = fig.extrude_step(fig.centroid(), 2.0)
    items.append(fig)
    """
    fig = ddd.point([0, 0]).buffer(1.0, cap_style=ddd.CAP_ROUND)
    fig = fig.extrude_step(fig.centroid(), 2.0, method=ddd.EXTRUSION_METHOD_SUBTRACT)
    items.append(fig)
    """

    # Extrude to empty
    fig = ddd.point([0, 0]).buffer(1.0, cap_style=ddd.CAP_ROUND)
    fig = fig.extrude_step(fig.buffer(-2.0), 2.0)
    items.append(fig)
    fig = ddd.point([0, 0]).buffer(1.0, cap_style=ddd.CAP_ROUND)
    fig = fig.extrude_step(fig.buffer(-2.0), 2.0, base=False, method=ddd.EXTRUSION_METHOD_SUBTRACT)
    items.append(fig)


    # Extrude with division
    fig1 = ddd.disc().translate([1.5, 0]).union(ddd.disc())
    fig = fig1.extrude_step(fig1.buffer(-0.2), 0.5, method=ddd.EXTRUSION_METHOD_SUBTRACT)
    fig = fig.extrude_step(fig1.buffer(-0.5), 0.5, method=ddd.EXTRUSION_METHOD_SUBTRACT)
    items.append(fig)


    # Extrude multiple with empty geometry
    fig1 = ddd.point([0, 0]).buffer(2.0, cap_style=ddd.CAP_ROUND)
    fig = fig1.extrude_step(fig1.buffer(-0.5), 0.5, method=ddd.EXTRUSION_METHOD_SUBTRACT)
    fig = fig.extrude_step(fig1.buffer(-1.5), 0.5, method=ddd.EXTRUSION_METHOD_SUBTRACT)
    fig = fig.extrude_step(fig1.buffer(-2.5), 0.5, method=ddd.EXTRUSION_METHOD_SUBTRACT)
    fig = fig.extrude_step(fig1.buffer(-2.5), 0.5, method=ddd.EXTRUSION_METHOD_SUBTRACT)
    items.append(fig)

    # Triangulate/Extrude with colinear segments
    fig1 = ddd.polygon([[0, 0], [1, 0], [2, 0], [2, 1], [1, 1], [0, 1]])
    #fig = fig1.triangulate()
    fig = fig1.extrude(1.0)
    items.append(fig)


    # All items
    items = ddd.align.grid(items, space=10.0)
    #items.append(ddd.helper.all())

    items = ddd.uv.map_cubic(items)
    items = items.material(ddd.MAT_TEST)


    root.append(items)
    #pipeline.root = items

    root.show()

