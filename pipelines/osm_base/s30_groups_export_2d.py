# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020

from ddd.ddd import ddd
from ddd.pipeline.decorators import dddtask



@dddtask(order="30.90.+", path="/Ways/*")
def osm_groups_ways_svg_style(obj):
    """Sets SVG line width for ways."""
    # Use osm:lanes if set, otherwise use lanes
    obj.extra['svg:stroke-width'] = obj.extra['ddd:way:width']


@dddtask(order="30.90.+")
def osm_groups_export_2d_processed(root):
    """Export current 2D root node without alterations to JSON and SVG."""

    root = root.copy()
    root = root.remove(root.find("/Features"))  # !Altering

    root.save("/tmp/osm-groups.json")
    root.save("/tmp/osm-groups.svg")


@dddtask(order="30.90.+")
def osm_groups_export_2d(root):

    root = root.copy()
    root = root.remove(root.find("/Features"))  # !Altering
    root.find("/Areas").replace(root.find("/Areas").material(ddd.mats.park).prop_set('svg:fill-opacity', 0.6, True))
    root.find("/Ways").replace(root.find("/Ways").buffer(1.0).material(ddd.mats.asphalt).prop_set('svg:fill-opacity', 0.8, True))
    root.find("/Buildings").replace(root.find("/Buildings").material(ddd.mats.stone).prop_set('svg:fill-opacity', 0.7, True))
    root.find("/ItemsAreas").replace(root.find("/ItemsAreas").material(ddd.mats.rock))  # buffer(1.0).
    root.find("/ItemsNodes").replace(root.find("/ItemsNodes").material(ddd.mats.highlight))  # buffer(1.0).
    root.find("/ItemsWays").replace(root.find("/ItemsWays").buffer(0.75).material(ddd.mats.highlight))  # buffer(1.0).
    root.save("/tmp/osm-groups-features.json")
    root.save("/tmp/osm-groups-features.svg")








