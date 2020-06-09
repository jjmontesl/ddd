# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020

import sys

import pyproj

from ddd.ddd import ddd
from ddd.geo import terrain
from ddd.osm import osm
from ddd.osm.augment.mapillary import MapillaryClient
from ddd.osm.osm import project_coordinates
from ddd.pipeline.decorators import dddtask


@dddtask(order="30.10.+", log=True)
def osm_groups_create_root_nodes(root, osm):
    items = ddd.group2(name="Areas")  # 2D
    root.append(items)
    items = ddd.group2(name="Ways")  # 1D
    root.append(items)
    items = ddd.group2(name="Buildings")  # 2D
    root.append(items)
    items = ddd.group2(name="Items")  # 1D
    root.append(items)
    items = ddd.group2(name="Meta")  # 2D meta information (boundaries, etc...)
    root.append(items)

    #root.dump(data=True)

@dddtask(order="30.20.10", path="/Features/*", select='[geom:type="Point"]', log=True)  #  , select='[geom:type="Point"]'  , parent="stage_30_generate_items_node")
def osm_generate_items(root, osm, obj):
    """Generate items for point features."""
    item = obj.copy(name="Item: %s" % obj.name)
    root.find("/Items").append(item)

@dddtask(order="30.20.20", log=True)  #  , select='[geom:type="Point"]'  , parent="stage_30_generate_items_node")
def osm_generate_items_process(root, osm, obj):
    """Generate items for point features."""
    #root.save("/tmp/osm-31-items.svg")
    pass


@dddtask(order="30.30.10.+", path="/Features/*", select='[geom:type="LineString"][osm:highway]', log=True)
def osm_groups_ways(root, obj, logger):
    # Ways depend on buildings
    item = obj.copy(name="Way: %s" % obj.name)
    root.find("/Ways").append(item)
    ## ?? osm.ways.generate_ways_1d()


'''
@dddtask(order="30.30.?.+", path="/Features/*", select='[geom:type="LineString"][]', log=True)
def osm_groups_ways_ignored(root, obj, logger):
    """Collect ignored ways to store, report and visualize."""
    logger.warn("Ignored ways: %s", obj)
'''


@dddtask(order="30.30.20", log=True)
def osm_groups_ways_process(pipeline, osm, root, logger):
    osm.ways_1d = root.find("/Ways")
    #osm.ways.generate_ways_1d()
    #root.find("/Ways").replace(osm.ways_1d)


# Generate buildings
##osm.buildings.generate_buildings_2d()
@dddtask(order="30.40.10", path="/Features/*", select='["geom:type"="Polygon"]', filter=lambda o: o.extra.get("osm:building", None) is not None or o.extra.get("osm:building:part", None) is not None, log=True)
def osm_generate_buildings(root, obj):
    # Ways depend on buildings
    item = obj.copy(name="Building: %s" % obj.name)
    root.find("/Buildings").append(item)
    ## ?? osm.ways.generate_ways_1d()

@dddtask(order="30.40.+")
def osm_generate_buildings_preprocess(pipeline, osm, root, logger):
    #osm.buildings.preprocess_buildings_2d()
    pass

@dddtask(order="30.40.+")
def osm_generate_buildings_postprocess(pipeline, osm, root, logger):
    #osm.buildings.generate_buildings_2d()
    pass


@dddtask(order="30.50.10", path="/Features/*", select='["geom:type" ~ "Polygon|MultiPolygon|GeometryCollection"][!"osm:building"]')
def osm_groups_areas(root, obj):
    # Ways depend on buildings
    item = obj.copy(name="Area: %s" % obj.name)
    root.find("/Areas").append(item)
    ## ?? osm.ways.generate_ways_1d()

@dddtask(order="30.50.20")
def osm_groups_areas_process(pipeline, osm, root, logger):
    pass


@dddtask(order="30.60.+")
def osm_generate_areas_coastline_2d(osm, root):
    #osm.areas.generate_coastline_2d(osm.area_crop if osm.area_crop else osm.area_filter)  # must come before ground
    osm.areas2.generate_coastline_2d(osm.area_filter)  # must come before ground
    root.find("/Areas").append(osm.water_2d)

@dddtask(order="30.70.+")
def osm_generate_areas_ground_2d(osm, root):
    #osm.areas.generate_coastline_2d(osm.area_crop if osm.area_crop else osm.area_filter)  # must come before ground
    osm.areas2.generate_ground_2d(osm.area_filter)  # must come before ground
    for a in osm.ground_2d.children:
        root.find("/Areas").append(a)

@dddtask(order="30.90")
def osm_groups_finished(pipeline, osm, root, logger):
    pass



