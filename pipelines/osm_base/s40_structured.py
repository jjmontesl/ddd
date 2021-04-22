# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020

from ddd.osm import osm
from ddd.pipeline.decorators import dddtask
from ddd.ddd import ddd
import math
import sys


@dddtask(order="40.10.+", log=True)
def osm_structured_init(root, osm):
    #osm.ways_1d = root.find("/Ways")
    pass



@dddtask(path="/Features/*", select='["geom:type" = "Point"]["osm:highway" = "crossing"]')
def osm_structured_split_ways_by_crossing(osm, root, obj, logger):
    """
    Splits ways that have crossings in the middle (not in first or end nodes).
    """
    # Find way (walking ways, as items have not yet been assigned to ways)
    ways = root.find('/Ways')
    for way in list(ways.children):
        if way.distance(obj) < 1e-8:  # True(obj):

            if way.get('osm:highway', None) == 'cycleway':
                continue

            # Check which vertex has the item (ensure is not first or last / inform if it is being ignored)
            idx = way.vertex_index(obj)
            if idx <= 0 or idx >= (len(way.geom.coords) - 1):
                logger.info("Ignoring osm:highway:crossing %s as it is at the end of the way %s.", obj, way)
                return

            #ddd.group([way.buffer(0.5), obj.buffer(1.0)]).show()
            #logger.info('Splitting way %s by osm:highway:crossing %s (vertex index=%s)' % (way, obj, idx))

            # Calculate crossing width
            crossing_width = 2.6 * way.get('ddd:way:lanes', default=1)
            ddd.math.clamp(crossing_width, 4.2, 9.0)  # Unless it's area defined


            # Split way at the two points.
            crossing_distance_in_way = way.geom.project(obj.geom)
            crossing_distance_in_way_start = crossing_distance_in_way - crossing_width / 2.0
            #crossing_point_in_way_start, segment_idx, segment_coords_a, segment_coords_b = way.interpolate_segment(crossing_distance_in_way_start)
            crossing_point_in_way_start = way.insert_vertex_at_distance(crossing_distance_in_way_start)

            #ddd.group2([way.buffer(0.5), ddd.point(crossing_point_in_way_start).buffer(2.0)]).show()

            split3 = None
            split1, split2 = osm.ways1.split_way_1d_vertex(ways, way, crossing_point_in_way_start)

            #ddd.group2([split1.buffer(0.5, cap_style=ddd.CAP_FLAT), split2.buffer(0.5, cap_style=ddd.CAP_FLAT).material(ddd.MAT_HIGHLIGHT), obj.buffer(0.3)]).show()

            if split2:


                crossing_distance_in_way = split2.geom.project(obj.geom)
                crossing_distance_in_way_end = crossing_distance_in_way + crossing_width / 2.0
                #crossing_point_in_way_end, segment_idx, segment_coords_a, segment_coords_b = split2.interpolate_segment(crossing_distance_in_way_end)
                crossing_point_in_way_end = split2.insert_vertex_at_distance(crossing_distance_in_way_end)
                split2, split3 = osm.ways1.split_way_1d_vertex(ways, split2, crossing_point_in_way_end)

            if split2 and split3:
                #split2.extra['ddd:material'] = ddd.MAT_HIGHLIGHT
                split2.extra['ddd:way:crosswalk'] = True
                split2.extra['ddd:way:roadlines'] = False

            # This seems not to help Points appearing in ways_2d build (intersections)
            if (split1 and split1.geom.type == 'Point'):
                ways.remove(split1)
            if (split2 and split2.geom.type == 'Point'):
                ways.remove(split2)
            if (split3 and split3.geom.type == 'Point'):
                ways.remove(split3)

            if (split2 and split3):
                #ddd.group2([split1.buffer(0.5, cap_style=ddd.CAP_FLAT), split2.buffer(0.5, cap_style=ddd.CAP_FLAT).material(ddd.MAT_HIGHLIGHT), split3.buffer(0.5, cap_style=ddd.CAP_FLAT), obj.buffer(0.3)]).show()
                pass
            elif (split2):
                ddd.group2([split1.buffer(0.5, cap_style=ddd.CAP_FLAT), split2.buffer(0.5, cap_style=ddd.CAP_FLAT).material(ddd.MAT_HIGHLIGHT), obj.buffer(0.3)]).show()

            return


@dddtask()
def osm_structured_split_ways_by_joins(osm, root):
    """
    Splits all ways into the minimum pieces that have only an intersection at each end.
    This method modifies the passed in node, manipulating children to avoid ways with multiple intersections.
    """

    osm.ways1.split_ways_1d(root.find("/Ways"))  # Move earlier?

@dddtask()
def osm_structured_link_ways_items(osm, root):
    osm.ways1.ways_1d_link_items(root.find("/Ways"), root.find("/ItemsNodes"))


@dddtask()
def osm_structured_buildings(osm, root):
    # dependencies? (document)
    features = root.find("/Features")
    #osm.buildings.preprocess_buildings_features(features)
    #root.find("/Buildings").children = []  # Remove as they will be generated from features: TODO: change this
    #osm.buildings.generate_buildings_2d(root.find("/Buildings"))


@dddtask(path="/ItemsWays/*", select='["ddd:width"]')
def osm_structured_process_items_ways(osm, root, obj):
    """Generates items from Items Ways (lines)."""
    width = float(obj.extra.get('ddd:width', 0))
    if width > 0:
        obj = obj.buffer(width, cap_style=ddd.CAP_FLAT)
    return obj


@dddtask()
def osm_structured_generate_ways_2d(osm, root):
    """Generates ways 2D (areas) from ways 1D (lines), replacing the /Ways node in the hierarchy."""
    ways1 = root.find("/Ways")
    root.remove(ways1)

    ways2 = osm.ways2.generate_ways_2d(ways1)
    ways2 = ways2.clean()
    root.append(ways2)


@dddtask()
def osm_structured_subtract_buildings_calculate(pipeline, root, logger):

    buildings = root.find("/Buildings").union()
    pipeline.data['buildings'] = buildings

@dddtask(path="/Ways/*", select='["ddd:subtract_buildings" = True]')
def osm_structured_subtract_buildings(pipeline, root, logger, obj):
    """Subtract buildings from objects that cannot overlap them."""
    #buildings_2d_union = self.osm.buildings_2d.union()
    #way_2d = way_2d.subtract(self.osm.buildings_2d_union)
    obj = obj.clean(eps=0.05)
    buildings = pipeline.data['buildings']
    try:
        obj = obj.subtract(buildings)
    except Exception as e:
        logger.error("Could not subtract buildings %s from way %s: %s", buildings, obj, e)
    return obj


@dddtask(path="/Areas/*", select='[!"ddd:layer"]')
def osm_structured_areas_layer(osm, root, obj):
    layer = obj.extra.get('osm:layer', "0")
    obj.set('ddd:layer', layer)


@dddtask()
def osm_structured_surfaces(osm, root, pipeline):
    """
    Walk layers and their transitions for ways and areas.
    Does this after all structured partitioning, so ways and areas are the smallest possible.

    This is done before ground filling, so this information can be used.

    This information is used to build tunnels and bridges, joining the ways that
    go across them onto a unique surface, as long as they belong to the same layer or its transition layer.
    """

    # UNUSED: WIP. Move to roads subsystem (style + osm code)

    layer_m1 = root.select(path="/Ways/", selector='["ddd:layer" = "-1"];["ddd:layer" = "-1a"]')
    layer_1 = root.select(path="/Ways/", selector='["ddd:layer" = "0a"];["ddd:layer" = "1"]')
    groups = [layer_m1, layer_1]

    structures = ddd.group2(name="Structures2")
    root.append(structures)

    surfaces = ddd.group2(name="Surfaces")
    root.append(surfaces)

    for group in groups:
        # Calculate influence areas, tag them (type of tunnel / bridge, etc)
        surfaces = group.union().buffer(2.0).individualize()  # .remove_holes()
        #surfaces.show()
        surfaces.children.extend(surfaces.children)

        # Currently unused


@dddtask()
def osm_structured_tunnel(osm, root, pipeline):
    """
    Create tunnel walls for tunnels.
    TODO: More tunnel types
    """
    #layer_m1 = root.select(path="/Ways/", selector='["ddd:layer" = "-1"];["ddd:layer" = "-1a"]')
    #layer_1 = root.select(path="/Ways/", selector='["ddd:layer" = "0a"];["ddd:layer" = "1"]')
    #groups = [layer_m1, layer_1]

    layer_m1 = root.select(path="/Ways/", selector='["ddd:layer" = "-1"]')
    layer_m1a = root.select(path="/Ways/", selector='["ddd:layer" = "-1a"]')

    ways = layer_m1.children + layer_m1a.children

    union = layer_m1.union()
    union_with_transitions = ddd.group(ways, empty="2").union()
    union_sidewalks = union_with_transitions.buffer(0.6, cap_style=2, join_style=2)

    sidewalks_2d = union_sidewalks.subtract(union_with_transitions)  # we include transitions
    sidewalks_2d.name="Tunnel Sidewalks"
    sidewalks_2d.set("ddd:layer", "-1")
    sidewalks_2d = sidewalks_2d.material(ddd.mats.pavement)
    root.find("/Areas").append(sidewalks_2d)

    walls_2d = sidewalks_2d.buffer(0.5, cap_style=2, join_style=2).subtract(union_sidewalks)
    walls_2d.name = "Walls"
    walls_2d.set("ddd:layer", "-1")
    root.find("/Structures2").append(walls_2d)

    floors_2d = union_sidewalks.copy()

    ceilings_2d = union.buffer(0.6, cap_style=2, join_style=2).subtract(layer_m1a)
    ceilings_2d.name = "Ceilings"
    ceilings_2d.set("ddd:layer", "-1")
    root.find("/Structures2").append(ceilings_2d)

    # FIXME: Move cropping to generic site, use interintermediatemediate osm.something for storage
    #crop = ddd.shape(self.osm.area_crop)
    #sidewalks_2d = sidewalks_2d.intersection(crop)
    #walls_2d = walls_2d.intersection(crop)
    #floors_2d = floors_2d.intersection(crop)
    #ceilings_2d = ceilings_2d.intersection(crop)


@dddtask()
def osm_structured_areas_postprocess_water(root, osm):
    areas_2d = root.find("/Areas")
    ways_2d = root.find("/Ways")
    osm.areas2.generate_areas_2d_postprocess_water(areas_2d, ways_2d)



@dddtask()
def osm_structured_generate_areas_interways(pipeline, osm, root, logger):
    """Generates interior areas between ways."""

    logger.info("Generating union for interways.")
    union = ddd.group2([root.find("/Ways").select('["ddd:layer" ~ "0|-1a"]'),
                        root.find("/Areas").select('["ddd:layer" ~ "0|-1a"]') ])
    #union = union.clean()
    union = osm.areas2.generate_union_safe(union)
    #union = union.clean()

    logger.info("Generating interways from interiors.")
    interiors = osm.areas2.generate_areas_2d_ways_interiors(union)
    interiors = interiors.material(ddd.mats.pavement)
    interiors.prop_set('ddd:area:type', 'sidewalk', children=True)
    interiors.prop_set('ddd:kerb', True, children=True)
    interiors.prop_set('ddd:height', 0.2, children=True)
    interiors.prop_set('ddd:layer', "0", children=True)
    #interiors = interiors.clean()

    root.find("/Areas").append(interiors.children)

@dddtask()
def osm_structured_generate_areas_ground_fill(osm, root, logger):
    """
    Generates (fills) remaining ground areas (not between ways or otherwise occupied by other areas).
    Ground must come after every other area (interways, etc), as it is used to "fill" missing gaps.
    """

    area_crop = osm.area_filter
    logger.info("Generating terrain (bounds: %s)", area_crop.bounds)

    union = ddd.group2([root.find("/Ways").select('["ddd:layer" ~ "^(0|-1a)$"]'),
                        root.find("/Areas").select('["ddd:layer" ~ "^(0|-1a)$"]'),
                        #root.find("/Water")
                        ])
    #union = union.clean_replace(eps=0.01)
    ##union = union.clean(eps=0.01)
    union = osm.areas2.generate_union_safe(union)
    union = union.clean(eps=0.01)  # Removing this causes a core dump during 3D generation

    terr = ddd.rect(area_crop.bounds, name="Ground")
    terr = terr.material(ddd.mats.terrain)
    terr.extra["ddd:layer"] = "0"
    terr.extra["ddd:height"] = 0

    try:
        terr = terr.subtract(union)
        terr = terr.clean(eps=0.0)  #eps=0.01)
    except Exception as e:
        logger.error("Could not subtract areas_2d from terrain.")
        return

    root.find("/Areas").append(terr)


@dddtask(path="/Areas/*", select='["geom:type" ~ "Polygon|MultiPolygon|GeometryCollection"]', recurse=True)
def osm_groups_areas_assign_area_m2(root, osm, obj, logger):
    """
    Assign area in m2. It was assigned earlier to areas, but will be used by areas_process in the
    following steps to resolve area containment.
    This updates and assigns areas to areas that might have been added (although ideally they should
    have been selected earlier during groups_areas).
    """

    # Removed as causes stairs to be assigned as areas
    #obj.extra['ddd:area:area'] = obj.geom.area
    #obj.set('ddd:area:weight', default=100)  # Lowest
    #obj.set('ddd:area:height', default=0)

    # Create container and contained metadata
    obj.extra['ddd:area:container'] = None
    obj.extra['ddd:area:contained'] = []


@dddtask()
def osm_structured_areas_process(logger, osm, root):
    """
    Resolves container / contained relationships between areas.
    """

    layers = set([n.extra.get('ddd:layer', '0') for n in root.select(path="*", recurse=True).children])

    for layer in layers:
        logger.info("Processing areas for layer: %s", layer)
        areas_2d = root.find("/Areas").select('["ddd:layer" = "%s"]' % layer)
        subtract = root.find("/Ways").select('["ddd:layer" = "%s"]' % layer)

        subtract = osm.areas2.generate_union_safe(subtract)

        osm.areas2.generate_areas_2d_process(root.find("/Areas"), areas_2d, subtract)


@dddtask()
def osm_structured_areas_postprocess_cut_outlines(root, osm):
    areas_2d = root.find("/Areas")
    ways_2d = root.find("/Ways")
    osm.areas2.generate_areas_2d_postprocess_cut_outlines(areas_2d, ways_2d)


@dddtask()
def osm_structured_areas_link_items_nodes(root, osm):
    """Associate features (amenities, etc) to buildings."""
    # TODO: There is some logic for specific items inside: use tagging for linkable items.
    items = root.find("/ItemsNodes")

    areas = root.find("/Areas")
    ways = root.find("/Ways")
    #areas.children.extend(ways.children)  # DANGEROUS! Should have never been here, it adds ways to areas

    osm.areas2.link_items_to_areas(areas, items)
    osm.areas2.link_items_to_areas(ways, items)


@dddtask(log=True)
def osm_structured_building_link_items_nodes(root, osm):
    """Associate features (amenities, etc) to buildings."""
    # TODO: There is some logic for specific items inside: use tagging for linkable items.
    items = root.find("/ItemsNodes")
    buildings = root.find("/Buildings")
    osm.buildings.link_items_to_buildings(buildings, items)


@dddtask(log=True)
def osm_structured_building_link_items_ways(root, osm):
    """Associate features (amenities, etc) to buildings."""
    items = root.find("/ItemsWays")
    buildings = root.find("/Buildings")
    osm.buildings.link_items_ways_to_buildings(buildings, items)


@dddtask(path="/ItemsWays/*", select='["ddd:building:parent"]')  # filter=lambda o: "ddd:building:parent" in o.extra)  #
def osm_structured_building_link_items_ways_elevation(root, osm, obj):
    obj.extra['ddd:elevation'] = 'building'
    obj.extra['_height_mapping'] = 'none'


@dddtask()
def osm_structured_items_2d_generate(root, osm):
    # Generates items defined as areas (area fountains, football fields...)
    #osm.items2.generate_items_2d()  # Objects related to areas (fountains, playgrounds...)  # check: this no longer applies?
    pass


@dddtask(order="40.80.+.+")
def osm_structured_ways_2d_generate_roadlines(root, osm, pipeline, logger):
    """
    Roadlines are incorporated here, but other augmented properties (traffic lights, lamp posts, traffic signs...)
    are added during augmentation.
    """
    logger.info("Generating roadlines.")
    root.append(ddd.group2(name="Roadlines2"))
    # TODO: This shall be moved to s60, in 3D, and separated from 2D roadline generation
    pipeline.data["Roadlines3"] = ddd.group3(name="Roadlines3")

@dddtask(path="/Ways/*", select='["ddd:way:roadlines" = True]')
def osm_structured_ways_2d_generate_roadlines_way(root, osm, pipeline, obj):
    """
    Generate roadlines (2D) for each way.
    """
    osm.ways2.generate_roadlines(pipeline, obj)
    #props_2d(root.find("/Ways"), pipeline)  # Objects related to ways

@dddtask(path="/Ways/*", select='["ddd:way:crosswalk" = True]')
def osm_structured_ways_2d_generate_crosswalk_way(root, osm, pipeline, obj):
    """
    Generate roadlines (2D) for each way.
    """
    osm.ways2.generate_crosswalk(pipeline, obj)
    #props_2d(root.find("/Ways"), pipeline)  # Objects related to ways
    #obj = obj.material(ddd.MAT_HIGHLIGHT)
    return obj

@dddtask(order="40.80.+")
def osm_structured_rest(root, osm):
    pass


@dddtask(order="49.50")
def osm_structured_finished(pipeline, osm, root, logger):
    pass


@dddtask(order="49.95.+", cache=True)
def osm_structured_cache(pipeline, osm, root, logger):
    """
    Caches current state to allow for faster reruns.
    """
    sys.setrecursionlimit(15000)  # This cache operation was failing due to RecursionError during pickle dump
    return pipeline.data['filenamebase'] + ".s40.cache"

