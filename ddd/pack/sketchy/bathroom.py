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
    base = ddd.rect([width, depth]).translate([-width / 2, -depth])
    base = base.buffer(-0.01).buffer(0.01, join_style=ddd.JOIN_BEVEL)

    cistern = base.buffer(-0.005).extrude_step(base, 0.005)
    cistern = cistern.extrude_step(base, height - 2 * 0.005)
    cistern = cistern.extrude_step(base.buffer(-0.005), 0.005)

    cistern = cistern.material(ddd.mats.porcelain_white)
    cistern = cistern.merge_vertices().smooth(ddd.PI)
    cistern = ddd.uv.map_cubic(cistern, scale=[0.5, 0.5, 0.5])


    return cistern

def wc_seat(height=0.42, width=0.36, depth=0.63):
    sects = [
        ddd.svgpath("M -22.597 -21.419 L 21.199 -21.419 L 20.349 35.944 L 15.225 51.034 L 7.141 54.819 L -5.939 54.819 L -14.694 50.829 L -21.954 35.456 L -22.597 -21.419 Z"),
        ddd.svgpath("M -27.404 -47.227 L 25.347 -47.461 L 24.881 35.505 L 17.645 53.478 L 7.141 57.913 L -8.264 58.146 L -19.002 52.311 L -26.938 35.038 L -27.404 -47.227 Z"),
        ddd.svgpath("M -41.344 -69.692 L 42.327 -68.322 L 27.447 55.112 L 17.178 69.583 L 7.141 71.217 L -5.697 71.217 L -17.135 68.884 C -17.135 68.884 -28.572 55.579 -28.572 55.346 C -28.572 55.113 -41.811 -70.159 -41.344 -69.692 Z"),
        ddd.svgpath("M -42.622 -70.656 L 43.457 -69.554 L 44.361 39.434 L 38.105 58.988 L 29.608 68.901 L 14.692 77.208 L 0.114 80.418 L -17.14 76.673 L -28.209 70.022 L -37.139 60.162 C -37.139 60.162 -43.493 39.901 -43.493 39.668 C -43.493 39.435 -43.089 -71.123 -42.622 -70.656 Z"),

        #ddd.svgpath("M 0.230 -8.272 L -15.821 -3.992000102996826 L -26.790000915527344 8.314000129699707 L -30.26799964904785 29.715999603271484 L -27.860000610351562 50.314998626708984 L -15.821999549865723 65.56400299072266 L -0.03800000250339508 69.30899810791016 L 17.08300018310547 66.0989990234375 L 29.656999588012695 50.047000885009766 L 30.9950008392334 29.715999603271484 L 27.784000396728516 7.24399995803833 L 17.618000030517578 -3.7239999771118164 Z")
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



def sink():
    pass

#def utility_sink():
#    pass


def bathtub():
    pass


def shower_base():
    """
    Shower tray.
    """
    pass

def shower_outlet_wall():
    pass

def shower_taps_wall():
    """
    """
    pass

def shower():
    pass


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

