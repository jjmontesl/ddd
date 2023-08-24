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


def wc_cistern():
    """
    WC cistern (water tank).
    """
    pass

def wc_seat():
    pass

def wc_lid():
    pass

def wc_base():
    # seat + lid...
    pass


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

