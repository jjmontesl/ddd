# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020

from ddd.ddd import ddd
from ddd.pipeline.decorators import dddtask
from ddd.core.exception import DDDException


@dddtask(order="30.80.+.+", log=True)
def osm_icons(root, osm):
    pass

@dddtask(path="/Items/*", select='["osm:amenity"]')
def osm_icons_amenity(obj, root, osm, logger):
    """Add icons."""

    icon_name = "amenity-" + obj.extra['osm:amenity']
    icon_path = "../data/osmsymbols/" + icon_name + ".svg.png"

    icon_data = None
    try:
        icon_data = open(icon_path, "rb").read()
    except Exception as e:
        logger.info("Could not find icon: %s", icon_path)
        pass

    if icon_data:
        obj.extra['svg:image:data'] = icon_data
        obj.extra['svg:image:width'] = 3
        obj.extra['svg:image:height'] = 3

