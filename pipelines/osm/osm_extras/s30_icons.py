# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020

from ddd.ddd import ddd
from ddd.pipeline.decorators import dddtask
from ddd.core.exception import DDDException


SVG_SIZE_BASE = 8.0  # In units in the SVG drawing (in OSM, the scale is 1unit = 1m)

@dddtask(order="30.80.+.+", log=True)
def osm_icons(root, osm):
    pass

@dddtask(path="/ItemsNodes/*", select='["osm:amenity"]')
def osm_icons_amenity(obj, root, osm, logger):
    """Add icons."""

    icon_name = "amenity-" + obj.extra['osm:amenity']
    icon_path = ddd.DATA_DIR + "/osmsymbols/" + icon_name + ".svg.png"

    icon_data = None
    try:
        icon_data = open(icon_path, "rb").read()
    except Exception as e:
        logger.debug("Could not find icon: %s", icon_path)

    if icon_data:
        obj.extra['svg:image:data'] = icon_data
        obj.extra['svg:image:width'] = SVG_SIZE_BASE
        obj.extra['svg:image:height'] = SVG_SIZE_BASE

@dddtask(path="/ItemsNodes/*", select='["osm:shop"]')
def osm_icons_shop(obj, root, osm, logger):
    """Add icons."""

    icon_name = "shop-" + obj.extra['osm:shop']
    icon_path = ddd.DATA_DIR + "/osmsymbols/" + icon_name + ".svg.png"

    icon_data = None
    try:
        icon_data = open(icon_path, "rb").read()
    except Exception as e:
        logger.debug("Could not find icon: %s", icon_path)

    if icon_data:
        obj.extra['svg:image:data'] = icon_data
        obj.extra['svg:image:width'] = SVG_SIZE_BASE
        obj.extra['svg:image:height'] = SVG_SIZE_BASE

