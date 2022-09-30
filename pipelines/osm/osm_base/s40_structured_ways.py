# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020

from ddd.osm import osm
from ddd.pipeline.decorators import dddtask
from ddd.ddd import ddd
from shapely import ops
import math
import sys


"""
The "structured" stage of the build process processes the features selected by the previous
stage into the different branches (Ways, Areas, Buildings...).

The output of this stage is structured 2D, using the same tree branches, but with added
information. Ways are given their with and converted to polygons, then resolved in 2D
for intersections (references to the original objects are kept along the whole process,
as original LineStrings are still used for other processes).

This stage of the OSM generation pipeline is not designed in principle to be altered or extended,
as it does most of the heavy lifting of 2D geometry operations and data structures. Styling
and alterations are ideally better done before (during initial selection of features) or
after.

- Split ways:
  - by the middle nodes if needed (eg. for highway crossings).
  - by every join with other ways
  - items are associated to paths (TODO: document criteria)
  - (TODO: itemways processing, what is it doing - other ways ie castle_wall are processed elsewhere ?)
  - ways are generated in 2D from lines
- Areas:
  - areas are generated between ways
  - areas are generated for every other space not occupied in the generation area
  - areas are processed to resolve their relationships (containment, etc)
- Items:
  - items are linked to areas, ways (in 2D) and buildings

"""


@dddtask(order="40.10.+", log=True)
def osm_structured_init(root, osm):
    #osm.ways_1d = root.find("/Ways")
    pass


@dddtask()
def osm_structured_split_ways_by_crossing_log(osm, root, obj, logger):
    ways = root.find("/Ways")
    logger.info("Number of ways before structured processing: %s %s", len(ways.children), ways)

# TODO: Separate the splitting logic to osm.ways, call from here
@dddtask(path="/Features/*", select='["geom:type" = "Point"]["osm:highway" = "crossing"]')
def osm_structured_split_ways_by_crossing(osm, root, obj, logger):
    """
    Splits ways that have crossings in the middle (not in first or end nodes).

    This happens before splitting ways by joins.

    TODO: Separate the splitting logic to osm.ways, call from here
    """
    # Find way (walking ways, as items have not yet been assigned to ways)
    ways = root.find('/Ways')
    for way in list(ways.children):
        if way.distance(obj) < ddd.EPSILON:  # True(obj):

            # TODO: shall this be here?
            if way.get('osm:highway', None) == 'cycleway':
                continue

            # Check which vertex has the item (ensure is not first or last / inform if it is being ignored)
            idx = way.vertex_index(obj)
            if idx <= 0 or idx >= (len(way.geom.coords) - 1):
                #logger.info("Ignoring osm:highway:crossing %s as it is at the end of the way %s.", obj, way)
                continue
                #return

            #ddd.group([way.buffer(0.5), obj.buffer(1.0)]).show()
            #logger.debug('Splitting way %s by osm:highway:crossing %s (vertex index=%s)' % (way, obj, idx))

            # Calculate crossing width
            # TODO: For crossings with area or way, this must come from the area/way
            crossing_width = 2.6 * way.get('ddd:way:lanes', default=1)
            ddd.math.clamp(crossing_width, 4.2, 9.0)

            # Split way at the two points.
            crossing_distance_in_way = way.geom.project(obj.geom)
            crossing_distance_in_way_start = crossing_distance_in_way - crossing_width / 2.0
            crossing_distance_in_way_end = crossing_distance_in_way + crossing_width / 2.0

            if (crossing_distance_in_way_start < 0 or crossing_distance_in_way_start > way.geom.length or
                crossing_distance_in_way_end < 0 or crossing_distance_in_way_end > way.geom.length):
                logger.error("Cannot create crosswalk area as it would lie outside the way (length=%s, p1=%s, p2=%s): %s", way.geom.length, crossing_distance_in_way_start, crossing_distance_in_way_end, way)
                continue

            #crossing_point_in_way_start, segment_idx, segment_coords_a, segment_coords_b = way.interpolate_segment(crossing_distance_in_way_start)
            crossing_point_in_way_start = way.insert_vertex_at_distance(crossing_distance_in_way_start)

            #ddd.group2([way.buffer(0.5), ddd.point(crossing_point_in_way_start).buffer(2.0)]).show()

            split3 = None
            split1, split2 = osm.ways1.split_way_1d_vertex(ways, way, crossing_point_in_way_start)

            #ddd.group2([split1.buffer(0.5, cap_style=ddd.CAP_FLAT), split2.buffer(0.5, cap_style=ddd.CAP_FLAT).material(ddd.MAT_HIGHLIGHT), obj.buffer(0.3)]).show()

            if split2:

                crossing_distance_in_way = split2.geom.project(obj.geom)
                crossing_distance_in_way_end2 = crossing_distance_in_way + crossing_width / 2.0
                if (crossing_distance_in_way_end2 < 0 or crossing_distance_in_way_end2 > split2.geom.length):
                    logger.warn("Crosswalk area split2 lies outside the way (length=%s, p2=%s): %s", split2.geom.length, crossing_distance_in_way_end2, way)
                #crossing_point_in_way_end, segment_idx, segment_coords_a, segment_coords_b = split2.interpolate_segment(crossing_distance_in_way_end2)
                crossing_point_in_way_end = split2.insert_vertex_at_distance(crossing_distance_in_way_end2)
                split2, split3 = osm.ways1.split_way_1d_vertex(ways, split2, crossing_point_in_way_end)
            #else:
            #    ddd.group2([way.buffer(1.0, cap_style=ddd.CAP_FLAT), ddd.point(crossing_point_in_way_start).buffer(0.5).material(ddd.MAT_HIGHLIGHT)]).show()
            #    ddd.group2([split1.buffer(1.0, cap_style=ddd.CAP_FLAT), ddd.point(crossing_point_in_way_start).buffer(0.5).material(ddd.MAT_HIGHLIGHT)]).show()
            #    sys.exit(1)

            if split2 and split3:
                split1.geom = ops.snap(split1.geom, way.geom, 0.05)
                split3.geom = ops.snap(split3.geom, way.geom, 0.05)
                split2.geom = ops.snap(split2.geom, split1.geom, 0.05)
                split2.geom = ops.snap(split2.geom, split3.geom, 0.05)
                split2.extra['ddd:way:crosswalk'] = True
                split2.extra['ddd:way:roadlines'] = False
                split2.name = "Crosswalk: %s" % split2.name

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
                #ddd.group2([split1.buffer(0.5, cap_style=ddd.CAP_FLAT), split2.buffer(0.5, cap_style=ddd.CAP_FLAT).material(ddd.MAT_HIGHLIGHT), obj.buffer(0.3)]).show()
                pass

            '''
            if ('Celso Emilio Ferreiro' in way.name):
                logger.info("Line %s (%s m) split at %s and %s", way, way.length(), crossing_distance_in_way_start, crossing_distance_in_way_end)
                ddd.group2([split1.buffer(0.5, cap_style=ddd.CAP_FLAT), split2.buffer(0.5, cap_style=ddd.CAP_FLAT).material(ddd.MAT_HIGHLIGHT), split3.buffer(0.5, cap_style=ddd.CAP_FLAT)]).show()
            '''

            return

@dddtask()
def osm_structured_split_ways_by_joins(osm, root):
    """
    Splits all ways into the minimum pieces that have only an intersection at each end.
    This method modifies the passed in node, manipulating children to avoid ways with multiple intersections.
    """

    osm.ways1.split_ways_1d(root.find("/Ways"))  # Move earlier?

@dddtask()
def osm_structured_ways_1d_intersections(osm, root):
    """
    Generate intersection data structure.

    This is currently stored in elements metadata (intersection, intersection_start...).
    """
    osm.ways1.ways_1d_intersections(root.find("/Ways"))


@dddtask(path="/Ways/*")
def osm_structured_ways_length(osm, root, obj):
    """
    """
    obj.set('ddd:way:length', obj.length())


@dddtask()
def osm_structured_ways_1d_height(osm, root):
    """
    """

    ways_1d = root.find("/Ways")

    # Road 1D heights
    # Propagate height across connections for transitions
    osm.ways1.ways_1d_heights_initial(ways_1d)
    osm.ways1.ways_1d_heights_connections(ways_1d)  # and_layers_and_transitions_etc
    osm.ways1.ways_1d_heights_propagate(ways_1d)

    # Propagate height beyond transition layers if gradient is too large?!
    # Soften / subdivide roads if height angle is larger than X (try as alternative to massive subdivision of roads?)


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


@dddtask(path="/ItemsWays/*", select='["geom:type"~"Polygon|MultiPolygon"]["ddd:width"]')
def osm_structured_process_items_ways_polygons(osm, root, obj):
    """Generates lineitems (eg walls) from Items Ways (polygons). Must be done before generating polygons to avoid these being buffered again."""
    width = float(obj.extra.get('ddd:width', 0))
    if width > 0:
        obj = obj.buffer(width * 0.5, cap_style=ddd.CAP_FLAT)
        obj = obj.subtract(obj.buffer(-width * 0.5))    # TODO: add a buffer_lines or argument to support buffering polygons as lines (careful with interiors)
    return obj

@dddtask(path="/ItemsWays/*", select='["geom:type"~"LineString|GeometryCollection"]["ddd:width"]')
def osm_structured_process_items_ways_lines(osm, root, obj):
    """Generates lineitems from Items Ways (lines)."""
    width = float(obj.extra.get('ddd:width', 0))
    if width > 0:
        obj = obj.buffer(width * 0.5, cap_style=ddd.CAP_FLAT)
    return obj



@dddtask()
def osm_structured_generate_ways_2d(pipeline, root, osm):
    """Generates ways 2D (areas) from ways 1D (lines), replacing the /Ways node in the hierarchy."""
    ways1 = root.find("/Ways")
    root.remove(ways1)
    pipeline.data['ways1'] = ways1

    ways2 = osm.ways2.generate_ways_2d(ways1)
    root.append(ways2)


@dddtask(path="/Areas/*", select='[!"ddd:layer"]')
def osm_structured_areas_layer(osm, root, obj):
    layer = obj.extra.get('osm:layer', "0")
    obj.set('ddd:layer', default=layer)

'''
@dddtask(path="/Ways/*", select='[!"ddd:layer"]')
def osm_structured_ways_layer(osm, root, obj):
    layer = obj.extra.get('osm:layer', "0")
    obj.set('ddd:layer', layer)
'''

@dddtask()
def osm_structured_generate_areas_calculate_buildings_ground_footprint(pipeline, osm, root, logger):
    """Calculates building footprint to be removed from areas (terrain, sidewalk...)."""
    # FIXME: This condition for footprints is weak, use a building footprint generation function
    # Also, seems that at this moment ddd:building:min_level, etc are not available (is it too soon? min/max levels/height shall be available earlier)
    buildings = root.select(path="/Buildings/*", func=lambda o:
        (o.get('ddd:building:parent', None) or not o.get('ddd:building:parts', None)) and
        o.get("osm:building:min_level", None) is None)
    buildings = buildings.copy2()
    buildings = buildings.union()
    pipeline.data['buildings_level_0'] = buildings


@dddtask()
def osm_structured_generate_ways_2d_intersections(osm, root):
    """
    Generates ways 2D intersections from ways areas and 1d intersection metadata
    from ways_1d processing, altering the /Ways node in the hierarchy.
    Intersections alter ways geometry, completing joints and gaps, so this must run before generation of sidewalks.
    """

    ways_2d = root.find("/Ways")

    osm.ways2.generate_ways_2d_intersections(ways_2d)

    # TODO: This shall now be replaced by a generic ways / intersections intersection processing and find common platforms
    osm.ways2.generate_ways_2d_intersection_intersections(ways_2d)

    ways_2d.replace(ways_2d.clean())


@dddtask()
def osm_structured_generate_areas_interways_phase1(pipeline, osm, root, logger):
    """
    Generates interior areas between ways (and areas)
    This does not include ways that are overlaid / absorbed into their container areas (eg. paths over sidewalks).
    NOTE: "way:overlay" may be better named "way:interways", as it is really used for that for now (way/area priority is also used for other resolutions, think path/cycle/road)
    """

    logger.info("Generating union for interways.")
    union = root.find("/Ways").select('["ddd:layer" ~ "0|-1a"][ ! "ddd:way:overlay"]')
    #union.append(root.find("/Areas").select('["ddd:layer" ~ "0|-1a"][ ! "ddd:way:overlay"]'))

    # Calculate union
    union = osm.areas2.generate_union_safe(union)
    #union = union.clean()

    # Add building lvel 0
    #buildings = pipeline.data['buildings_level_0']
    #areas = root.find("/Areas").select('["ddd:layer" ~ "0|-1a"]')
    #subtract_union = osm.areas2.generate_union_safe(ddd.group2([buildings, areas]))

    logger.debug("Generating interways from interiors.")
    interiors = osm.areas2.generate_areas_2d_ways_interiors(union)
    interiors = interiors.material(ddd.mats.pavement)  # sidewalk
    interiors.set('ddd:area:type', 'sidewalk', children=True)
    interiors.set('ddd:kerb', True, children=True)
    interiors.set('ddd:height', 0.2, children=True)
    interiors.set('ddd:layer', "0", children=True)
    #interiors = interiors.clean()

    # Set a copy of itself as original area (so it can be cut and used for sidewalk kerb calculations)
    for interior in interiors.children:
        interior.set('ddd:area:area', interior.geom.area)
        interior.set('ddd:area:original', interior.union())
        # TODO: I think this should not be needed here, as buildings/areas shall be removed from all areas later anyway?
        #interior = interior.subtract(subtract_union).clean().individualize(always=True)

        root.find("/Areas").append(interior)

@dddtask()
def osm_structured_generate_areas_interways_phase1_ways_sidewalks(pipeline, osm, root, logger):
    """
    Experimenting with aumenting sidewalks / kerbs
    """

    # TODO: if done, this shall generate at different layers and according to way metadata

    logger.info("Generating sidewalks for ways.")
    ways = root.find("/Ways").select('["ddd:layer" ~ "0|-1a"][ ! "ddd:way:overlay"]["ddd:way:sidewalk:width"]')

    # Calculate union
    union = root.find("/Ways").select('["ddd:layer" ~ "0|-1a"]').union()
    union = union.append(pipeline.data['buildings_level_0'])
    union = union.append(root.find("/Areas"))
    union = osm.areas2.generate_union_safe(union)
    union = union.clean()

    # Buffer sidewalks
    sidewalks = ddd.group2()
    for sidewalk in ways.flatten().children:
        sidewalk_width = sidewalk.get('ddd:way:sidewalk:width', None)
        if not sidewalk_width: continue
        sidewalk = sidewalk.buffer(sidewalk_width)
        sidewalks.append(sidewalk)

    sidewalks = sidewalks.union().subtract(union).individualize(always=True).flatten().clean(eps=0.0)  # -0.01)

    # Construct sidewalks 2D
    for sidewalk in sidewalks.children:

        if sidewalk.is_empty(): continue

        sidewalk.name = "Way Sidewalk"
        sidewalk = sidewalk.material(ddd.mats.pavement)
        sidewalk.set('ddd:area:type', 'sidewalk', children=True)
        sidewalk.set('ddd:area:interways', True, children=True)  # It's not interways, but this is used to subtract areas from them
        sidewalk.set('ddd:kerb', True, children=True)
        sidewalk.set('ddd:height', 0.2, children=True)
        sidewalk.set('ddd:layer', "0", children=True)

        sidewalk.set('ddd:area:area', sidewalk.geom.area)
        # Set a copy of itself as original area (so it can be cut and used for sidewalk kerb calculations)
        sidewalk.set('ddd:area:original', sidewalk.copy())
        # TODO: I think this should not be needed here, as buildings shall be removed from all areas later anyway?
        #interior.replace(interior.subtract(buildings).clean())
        root.find("/Areas").append(sidewalk)


@dddtask()
def osm_structured_subtract_buildings_calculate(pipeline, root, logger):

    buildings = root.find("/Buildings").union()
    #buildings = ddd.group2()
    #buildings = buildings.clean(eps=0.00)
    #buildings.show()
    pipeline.data['buildings'] = buildings


@dddtask(path="/Ways/*", select='["ddd:subtract_buildings" = True]')
def osm_structured_subtract_buildings(pipeline, root, logger, obj):
    """Subtract buildings from objects that cannot overlap them."""
    #buildings_2d_union = self.osm.buildings_2d.union()
    #way_2d = way_2d.subtract(self.osm.buildings_2d_union)
    obj = obj.clean(eps=0.05)

    #buildings = pipeline.data['buildings']
    buildings = pipeline.data['buildings_level_0']

    try:
        obj = obj.subtract(buildings)
    except Exception as e:
        logger.error("Could not subtract buildings %s from way %s: %s", buildings, obj, e)
    return obj


@dddtask()
def osm_structured_generate_ways_2d_individualize(osm, root, logger):
    """
    Individualize all ways in MultiPolygons and flatten them all.
    """
    logger.warn("Individualizing ways early works around way overlay issues with multipolygons, but causes wrong joints (eg. for road lines).")
    ways_2d = root.find("/Ways")

    ways_2d = ways_2d.individualize().flatten()
    root.find("/Ways").replace(ways_2d)


@dddtask()
def osm_structured_structures_init(osm, root, pipeline):
    structures = ddd.group2(name="Structures2")
    root.append(structures)

'''
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

    surfaces = ddd.group2(name="Surfaces")
    root.append(surfaces)

    for group in groups:
        # Calculate influence areas, tag them (type of tunnel / bridge, etc)
        surfaces = group.union().buffer(2.0).individualize()  # .remove_holes()
        #surfaces.show()
        surfaces.children.extend(surfaces.children)

        # Currently unused
'''

@dddtask()
def osm_structured_tunnel(osm, root, pipeline):
    """
    Create tunnel walls for tunnels.
    TODO: More tunnel types
    """
    #layer_m1 = root.select(path="/Ways/", selector='["ddd:layer" = "-1"];["ddd:layer" = "-1a"]')
    #layer_1 = root.select(path="/Ways/", selector='["ddd:layer" = "0a"];["ddd:layer" = "1"]')
    #groups = [layer_m1, layer_1]

    layer_m1 = root.select(path="/Ways/", selector='["ddd:layer" = "-1"]', empty=2)
    layer_m1a = root.select(path="/Ways/", selector='["ddd:layer" = "-1a"]', empty=2)

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
def osm_structured_generate_areas_ground_fill(pipeline, osm, root, logger):
    """
    Generates (fills) remaining ground areas (not between ways or otherwise occupied by other areas).
    Ground must come after every other area (interways, etc), as it is used to "fill" missing gaps.
    """

    # Fill terrain for a chunk as large as the area filter
    area_fill = osm.area_filter

    logger.info("Generating terrain (bounds: %s)", area_fill.bounds)

    union = ddd.group2([root.find("/Ways").select('["ddd:layer" ~ "^(0|-1a)$"]'),
                        root.find("/Areas").select('["ddd:layer" ~ "^(0|-1a)$"]'),
                        ])
    #union = union.clean_replace(eps=0.01)
    ##union = union.clean(eps=0.01)

    # Add buildings
    buildings = pipeline.data['buildings_level_0']
    union.append(buildings)

    union = osm.areas2.generate_union_safe(union)
    union = union.clean(eps=0.01)  # Removing this causes a core dump during 3D generation

    terr = ddd.rect(area_fill.bounds, name="Ground")
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

    #obj.extra['ddd:area:area'] = obj.geom.area  # Removed as causes many troubles: stairs to be assigned as areas, repeated surfaces, but everything here should be buildable!
    #obj.set('ddd:area:weight', default=100)  # FIXME: weight should be positive (otherwise should call it priority)
    #obj.set('ddd:area:height', default=0)

    # Create container and contained metadata
    obj.extra['ddd:area:container'] = None
    obj.extra['ddd:area:contained'] = []


'''
@dddtask()
def debug(root, osm, pipeline):
    root.remove(root.find("/Features"))
    pipeline.stop()
'''


@dddtask(path="/Areas/*")
def osm_structured_areas_subtract_buildings(pipeline, osm, root, obj, logger):
    buildings = pipeline.data['buildings_level_0']
    obj = obj.subtract(buildings)
    return obj

@dddtask()
def osm_structured_areas_calculate_areas_subtract(pipeline, osm, root, logger):
    """"""
    areas_2d = root.find("/Areas").select('["ddd:layer" = "%s"][!"ddd:area:interways"]' % 0)
    areas_2d = areas_2d.union()
    pipeline.data['areas_2d_level_0'] = areas_2d

@dddtask(path="/Areas/*", select='["ddd:area:interways"]')
def osm_structured_areas_subtract_areas_from_interways(pipeline, osm, root, obj, logger):
    areas_2d = pipeline.data['areas_2d_level_0']
    obj = obj.subtract(areas_2d)
    if obj.is_empty():
        return False
    return obj


@dddtask()
def osm_structured_areas_process(logger, osm, root):
    """
    Resolves container / contained relationships between areas, and subtracts contained areas from containers.
    """

    layers = set([n.extra.get('ddd:layer', '0') for n in root.select(path="*", recurse=True).children])
    logger.info("Layers found in areas: %s", (layers, ))

    # Clean areas
    #root.find("/Areas").replace(root.find("/Areas").clean())

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


@dddtask(path="/Ways/*", select='["ddd:way:overlay" = true]')
def osm_structured_areas_postprocess_overlay_absorb(root, osm, obj):

    container = obj.get('ddd:area:container', None)
    if container and container != obj and container.mat == ddd.mats.pavement:
        obj.set('debug:overlay:absorbed', True)
        # Apply material if we are an absobed path, not eg a cycleway
        if obj.get('osm:highway', None) in ('footway', 'path'):
            obj = obj.material(container.mat)
            obj.set('ddd:material:splatmap', container.get('ddd:material:splatmap', False))
            # Note: Base height is being assigned (accumulated) in s60_model (maybe bring it here or as early as possible?)

    return obj


'''
@dddtask()
def debug_areas_processed(root, osm, pipeline):
    root.remove(root.find("/Features"))
    root.show(label="Areas Processed")
    pipeline.stop()
'''


@dddtask()
def osm_structured_areas_link_items_nodes(root, osm):
    """Associate features (amenities, etc) to areas (both ways and areas)."""
    # TODO: There is some logic for specific items inside: use tagging for linkable items.
    items = root.find("/ItemsNodes")

    areas = root.find("/Areas")
    ways = root.find("/Ways")
    #areas.children.extend(ways.children)  # DANGEROUS! Should have never been here, it adds ways to areas

    osm.areas2.link_items_to_areas(areas, items)
    osm.areas2.link_items_to_areas(ways, items)


@dddtask(log=True)
def osm_structured_building_fixes(pipeline, root, osm):
    """
    Fixes (OSM) buildings that contain `building:part`s that do not cover the entire footprint area,
    by creating a building part for the remainder.
    This does not apply to single-part buildings, which are kept as single objects.
    """
    buildings = root.find("/Buildings")
    osm.buildings2.preprocess_building_fixes(buildings)


@dddtask(log=True)
def osm_structured_building_reparent(pipeline, root, osm):
    """
    Reparents building parts to buildings.
    """
    buildings = root.find("/Buildings")
    osm.buildings2.preprocess_building_reparent(buildings)

@dddtask(log=True)
def osm_structured_building_analyze(pipeline, root, osm):
    """
    Produce building information: segments, floors, contacted buildings...
    """
    # TODO: There is some logic for specific items inside: use tagging for linkable items.
    buildings = root.find("/Buildings")
    #ways = root.select(path="/Ways/*", selector='["osm:layer" = "0"]', recurse=False)
    ways = pipeline.data['ways1']

    osm.buildings2.process_buildings_analyze(buildings, ways)
    #buildings.show()

    #buildings.save("/tmp/buildings.json")
    #buildings.dump(data=True)
    #sys.exit(1)


@dddtask(log=True)
def osm_structured_building_link_items_nodes(root, osm):
    """Associate features (amenities, etc) to buildings."""
    # TODO: There is some logic for specific items inside: use tagging for linkable items.
    items = root.find("/ItemsNodes")
    buildings = root.find("/Buildings")
    osm.buildings2.process_buildings_link_items_to_buildings(buildings, items)


@dddtask(log=True)
def osm_structured_building_link_items_ways(root, osm):
    """Associate features (amenities, etc) to buildings."""
    items = root.find("/ItemsWays")
    buildings = root.find("/Buildings")
    osm.buildings2.process_buildings_link_items_ways_to_buildings(buildings, items)


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


@dddtask()
def debug_ways_roadlines(root, osm, pipeline):
    ways = root.find("/Ways")
    roadlines = root.find("/Roadlines2")
    #ddd.group([ways, roadlines]).show(label="Ways + Roadlines2")


@dddtask(path="/Ways/*", select='["ddd:way:crosswalk" = True]')
def osm_structured_ways_2d_generate_crosswalk_way(root, osm, pipeline, obj):
    """
    Generate roadlines (2D) for each way.
    """
    osm.ways2.generate_crosswalk(pipeline, obj)
    #props_2d(root.find("/Ways"), pipeline)  # Objects related to ways
    #obj = obj.material(ddd.MAT_HIGHLIGHT)
    return obj


@dddtask()
def osm_structured_splatmap_materials(pipeline, osm, root, logger):
    """
    Mark materials for splatmap usage.
    """
    root.find("/Areas").select('[ddd:layer="0"]([!ddd:height];[ddd:height = 0])').set('ddd:material:splatmap', True, children=True)
    root.find("/Ways").select('[ddd:layer="0"][ddd:area:type != "stairs"]').set('ddd:material:splatmap', True, children=True)

@dddtask(order="40.80.+")
def osm_structured_rest(root, osm):
    pass


@dddtask(order="49.50")
def osm_structured_finished(pipeline, osm, root, logger):
    pass


@dddtask(order="49.95.+", cache=True)
def osm_structured_cache(pipeline, root, logger):
    """
    Caches current state to allow for faster reruns.
    """
    sys.setrecursionlimit(15000)  # This cache operation was failing due to RecursionError during pickle dump
    return pipeline.data['filenamebase'] + ".s40.cache"

