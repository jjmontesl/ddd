# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020

from ddd.ddd import ddd
from ddd.pipeline.decorators import dddtask
from ddd.core.exception import DDDException


svg_size_base = 5.0

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
        obj.extra['svg:image:width'] = svg_size_base
        obj.extra['svg:image:height'] = svg_size_base

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
        obj.extra['svg:image:width'] = svg_size_base
        obj.extra['svg:image:height'] = svg_size_base

