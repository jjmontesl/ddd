# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging

from ddd.ddd import ddd
from trimesh import transformations
from ddd.math.vector3 import Vector3
from ddd.ops import grid
from ddd.math.transform import DDDTransform

from ddd.ops.layout import DDDLayout, VerticalDDDLayout


# Get instance of logger for this module
logger = logging.getLogger(__name__)


def wc_cistern(height=0.8 - 0.42, width=0.36, depth=0.16):
    """
    WC cistern (water tank).
    """

    # TODO: This construction (beveled trapezoid box) should be in the "shapes" pack (e.g. shapes.volumes.parallelepiped)
    base = ddd.rect([width, depth - 0.03]).translate([-width / 2, - (depth - 0.03)])
    base = base.buffer(-0.01).buffer(0.01, join_style=ddd.JOIN_BEVEL)
    top = base.scale([1, (depth + 0.03) / depth])

    cistern = base.buffer(-0.005).extrude_step(base, 0.005)
    cistern = cistern.extrude_step(top, height - 2 * 0.005)
    cistern = cistern.extrude_step(top.buffer(-0.005), 0.005)

    cistern = cistern.material(ddd.mats.porcelain_white)
    cistern = cistern.merge_vertices().smooth(ddd.PI)
    cistern = ddd.uv.map_cubic(cistern, scale=[0.5, 0.5, 0.5])


    return cistern

def wc_seat(height=0.42, width=0.36, depth=0.63):
    sects = [
        ddd.svgpath("M -22.597 -21.419 L 21.199 -21.419 L 20.349 35.944 L 15.225 51.034 L 7.141 54.819 L -5.939 54.819 L -14.694 50.829 L -21.954 35.456 L -22.597 -21.419 Z"),
        ddd.svgpath("M -27.404 -47.227 L 25.347 -47.461 L 24.881 35.505 L 17.645 53.478 L 7.141 57.913 L -8.264 58.146 L -19.002 52.311 L -26.938 35.038 L -27.404 -47.227 Z"),
        #ddd.svgpath("M -41.344 -69.692 L 42.327 -68.322 L 27.447 55.112 L 17.178 69.583 L 7.141 71.217 L -5.697 71.217 L -17.135 68.884 C -17.135 68.884 -28.572 55.579 -28.572 55.346 C -28.572 55.113 -41.811 -70.159 -41.344 -69.692 Z"),
        ddd.svgpath("M -41.344 -69.692 L 42.327 -68.322 L 30.122 54.844 L 17.178 69.583 L 7.141 71.217 L -5.697 71.217 L -17.135 68.884 C -17.135 68.884 -28.572 55.579 -28.572 55.346 C -28.572 55.113 -41.811 -70.159 -41.344 -69.692 Z"),
        ddd.svgpath("M -42.622 -70.656 L 43.457 -69.554 L 44.361 39.434 L 38.105 58.988 L 29.608 68.901 L 14.692 77.208 L 0.114 80.418 L -17.14 76.673 L -28.209 70.022 L -37.139 60.162 C -37.139 60.162 -43.493 39.901 -43.493 39.668 C -43.493 39.435 -43.089 -71.123 -42.622 -70.656 Z"),

        ddd.svgpath("M 0.230 -8.272 L -15.821 -3.992 L -26.790 8.314 L -30.268 29.716 L -27.860 50.315 L -15.822 65.564 L -0.038 69.309 L 17.083 66.099 L 29.657 50.047 L 30.995 29.716 L 27.784 7.244 L 17.618 -3.724 Z")
    ]

    scale = [width / sects[3].size()[0], -depth / sects[3].size()[1]]  # Inverts Y as SVGs grow downwards

    sects = [s.scale(scale) for s in sects]

    wc = sects[0]
    wc = wc.extrude_step(sects[1], height / 3)
    wc = wc.extrude_step(sects[2], height / 3)
    wc = wc.extrude_step(sects[3], height / 3 - 0.005)

    wc = wc.extrude_step(sects[3].buffer(-0.005), 0.005, method=ddd.EXTRUSION_METHOD_SUBTRACT)
    wc = wc.extrude_step(sects[4].buffer(0.005), 0.00, method=ddd.EXTRUSION_METHOD_SUBTRACT)
    wc = wc.extrude_step(sects[4], -0.005, method=ddd.EXTRUSION_METHOD_SUBTRACT)

    wc = wc.extrude_step(sects[4].scale([0.75, 0.75]), -height * 0.4, method=ddd.EXTRUSION_METHOD_SUBTRACT)
    wc = wc.extrude_step(sects[4].scale([0.25, 0.25]), -height * 0.25, method=ddd.EXTRUSION_METHOD_SUBTRACT)

    wc = ddd.align.reanchor(wc, [0.5, 1])

    wc = wc.merge_vertices().smooth()
    wc = wc.material(ddd.mats.porcelain_white)
    wc = ddd.uv.map_cubic(wc, scale=[0.5, 0.5, 0.5], split=False)

    return wc

def wc_lid(width=0.36, depth=0.63 - 0.16, thickness=0.02):

    lid = ddd.DDDNode3()
    return lid

def wc_base(height=0.42, width=0.36, depth=0.63, lid_thickness=0.02):
    """
    Seat + lid. Lid may exceed base height (thickness is added).
    """
    seat = wc_seat(height=height, width=width, depth=depth)
    lid = wc_lid(width=width, depth=depth, thickness=lid_thickness)
    wc_base = ddd.group2([seat, lid], name="WCBase")
    return wc_base

def wc(height=0.8, base_height=0.42, width=0.36, depth=0.63, lid_thickness=0.02):
    # TODO: Use itembuilder and slots?
    base = wc_base(height=base_height, width=width, depth=depth, lid_thickness=lid_thickness)
    cistern = wc_cistern(height=height - base_height).translate([0, 0, base_height])
    wc = ddd.group([base, cistern], name="WC")
    return wc


def urinal():
    """
    Vertical urinal.
    """
    pass


def sink_base(height=0.66, width=0.14, depth=0.16):
    """
    Base of a sink.
    """
    base = ddd.disc(r = width / 2, resolution=4, name="SinkBase").scale([1, (depth / width)])

    column = base.extrude_step(base, height)
    column = column.merge_vertices().smooth()
    column = column.material(ddd.mats.porcelain_white)
    column = ddd.uv.map_cylindrical(column, scale=[0.5, 0.5, 0.5], split=False)

    return column

def sink_vase(height=0.17, width=0.60, depth=0.43):
    """
    Vase of a sink.
    """
    sects = [
        ddd.svgpath("M -1.143 -23.514 L 90.542 -22.809 L 90.542 93.56 L 72.205 101.671 L 49.989 107.666 L 30.594 111.545 L 11.199 114.013 L -0.438 113.66 L -1.143 -23.514 Z"),

        # Vase interior, could be separated to continue extrusions from other objects (e.g. fill rects)
        ddd.svgpath("M -1.496 20.565 L 59.157 20.565 L 65.857 26.56 L 65.504 83.686 L 61.978 88.623 L 53.515 91.797 L 43.641 94.265 L 25.304 97.439 L 10.846 98.85 L -0.791 98.85 L -1.496 20.565 Z")
    ]

    sects = [ddd.geomops.mirror_x(s, simplify_dist=width * 0.05) for s in sects]
    scale = [width / sects[0].size()[0], -depth / sects[0].size()[1]]  # Inverts Y as SVGs grow downwards

    sects = [s.scale(scale) for s in sects]

    vase = sects[0].scale([1, 0.5])
    vase = vase.extrude_step(sects[0].scale([1, 0.8]), height / 3)
    vase = vase.extrude_step(sects[0].scale([1, 0.9]), height / 3)
    vase = vase.extrude_step(sects[0], height / 3 - 0.005)

    vase = vase.extrude_step(sects[0].buffer(-0.005), 0.005, method=ddd.EXTRUSION_METHOD_SUBTRACT)
    vase = vase.extrude_step(sects[1].buffer(0.005), 0.00, method=ddd.EXTRUSION_METHOD_SUBTRACT)
    vase = vase.extrude_step(sects[1], -0.005, method=ddd.EXTRUSION_METHOD_SUBTRACT)

    vase = vase.extrude_step(sects[1].buffer(-0.03), -height * 0.5, method=ddd.EXTRUSION_METHOD_SUBTRACT)
    vase = vase.extrude_step(sects[1].buffer(-0.1), -height * 0.225, method=ddd.EXTRUSION_METHOD_SUBTRACT)

    vase = ddd.align.reanchor(vase, [0.5, 1])

    vase = vase.merge_vertices().smooth()
    vase = vase.material(ddd.mats.porcelain_white)
    vase = ddd.uv.map_cubic(vase, scale=[0.5, 0.5, 0.5], split=False)

    return vase

def sink_bathroom(height=0.83, base_height=0.66, width=0.60, depth=0.43):
    base = sink_base(height=base_height, width=width * 0.25, depth=depth * 0.35).translate([0, - depth * 0.3, 0])
    vase = sink_vase(height=height - base_height, width=width, depth=depth).translate([0, 0, base_height])
    sink = ddd.group([base, vase], name="Sink")
    return sink
    

#def utility_sink():
#    pass


def bathtub():
    pass


def shower_base(width=0.8, depth=0.8, height=0.1):
    """
    Shower tray.
    """
    border_width = 0.05
    inner_radius = 0.03
    inner_height = 0.03

    exterior = ddd.rect([width, depth]).translate([-width / 2, -depth])
    interior = exterior.buffer(-border_width - inner_radius).buffer(inner_radius, join_style=ddd.JOIN_ROUND, resolution=2)
    exterior = exterior.buffer(-0.01).buffer(0.01, join_style=ddd.JOIN_BEVEL)   # TODO: Better method for rounded corners, or use shapes

    base = exterior.extrude_step(exterior, height - 0.005, base=False)
    base = base.extrude_step(exterior.buffer(-0.005), 0.005)
    base = base.extrude_step(interior.buffer(0.005), 0.0, method=ddd.EXTRUSION_METHOD_SUBTRACT)
    base = base.extrude_step(interior, -0.005, method=ddd.EXTRUSION_METHOD_SUBTRACT)
    base = base.extrude_step(interior.buffer(-0.01), - (height - inner_height), method=ddd.EXTRUSION_METHOD_SUBTRACT)
    base = base.extrude_step(interior.buffer(-0.02), -0.01, method=ddd.EXTRUSION_METHOD_SUBTRACT)

    base = base.material(ddd.mats.porcelain_white)
    base = base.merge_vertices().smooth(ddd.PI)
    base = ddd.uv.map_cubic(base, scale=[0.5, 0.5, 0.5], split=False)
    return base

def shower_outlet_wall():
    pass

def shower_taps_wall():
    """
    """
    pass

def shower(width=0.8, depth=0.8, height=1.9, base_height=0.1):
    """
    """
    base = shower_base(width=width, depth=depth, height=base_height)
    return base


def shower_curtain_bar():
    pass

def shower_curtain_cloth():
    pass

def shower_curtain():
    pass


def mirror():
    pass

def towel_rack():
    pass


def toilet_paper():
    pass

def toilet_paper_holder():
    pass

