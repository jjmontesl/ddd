# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

from collections import defaultdict, namedtuple
import logging
import math
import random

import numpy
from shapely.geometry.linestring import LineString

from ddd.ddd import ddd
from ddd.geo import terrain
from ddd.ops import uvmapping
from ddd.core.exception import DDDException
import sys
from shapely import ops
from shapely.ops import linemerge

# Get instance of logger for this module
logger = logging.getLogger(__name__)


class Ways3DOSMBuilder():

    def __init__(self, osmbuilder):
        self.osm = osmbuilder

    """
    def generate_ways_3d(self, ways_2d):
        #for layer_idx in self.osm.layer_indexes:
        ways_2d = ways_2d.individualize().flatten().clean()
        ways_3d = self.generate_ways_3d_base(ways_2d)

        #self.generate_ways_3d_subways()
        #self.generate_ways_3d_elevated()

        return ways_3d


    def generate_ways_3d_base(self, ways_2d):
        '''
        - Sorts ways (more important first),
        - Generates 2D shapes
        - Resolve intersections
        - Add metadata (road name, surface type, connections?)
        - Consider elevation and level roads on the transversal axis
        '''
        logger.info("Generating 3D ways for: %s", ways_2d)

        ways_3d = []
        for way_2d in ways_2d.children:
            # if way_2d.extra['oms:natural'] == "coastline": continue
            #layer_height = self.layer_height(layer_idx)
            try:
                if way_2d.extra.get('osm:railway', None):
                    way_3d = self.generate_way_3d_railway(way_2d)
                else:
                    way_3d = self.generate_way_3d_common(way_2d)

                way_3d.extra['way_2d'] = way_2d
                way_3d = terrain.terrain_geotiff_elevation_apply(way_3d, self.osm.ddd_proj)
                ways_3d.append(way_3d)

            except ValueError as e:
                logger.error("Could not generate 3D way %s: %s", way_2d, e)
            except IndexError as e:
                logger.error("Could not generate 3D way %s: %s", way_2d, e)
            except Exception as e:
                logger.error("Could not generate 3D way %s: %s", way_2d, e)

        ways_3d = ddd.group3(ways_3d)

        nways = []
        for way in ways_3d.children:
            # logger.debug("3D layer transition: %s", way)
            # if way.extra['ddd:layer_transition']:
            if 'way_1d' in way.extra['way_2d'].extra:
                path = way.extra['way_2d'].extra['way_1d']
                vertex_func = self.osm.ways1.get_height_apply_func(path)
                nway = way.vertex_func(vertex_func)
            else:
                nway = way.translate([0, 0, self.layer_height(way.extra['ddd:layer'])])
            nways.append(nway)

        ways_3d = ddd.group3(nways, name="Ways")
        return ways_3d


    def generate_way_3d_common(self, way_2d):
        '''
        '''

        way_2d = way_2d.individualize()

        extra_height = way_2d.extra['ddd:extra_height']
        if extra_height:
            try:
                way_3d = way_2d.extrude(-0.2 - extra_height).translate([0, 0, extra_height])  # + layer_height
            except DDDException as e:
                logger.error("Could not extrude (1st try) way %s: %s", way_2d, e)
                way_2d = way_2d.clean(eps=0.001)
                way_3d = way_2d.extrude(-0.2 - extra_height).translate([0, 0, extra_height])  # + layer_height

            way_3d = ddd.uv.map_cubic(way_3d)
        else:
            way_3d = way_2d.triangulate()  # + layer_height
            way_3d = ddd.uv.map_cubic(way_3d)
            way_3d.extra['ddd:shadows'] = False  # Should come from style

        #if way_2d.extra.get('osm:natural', None) == "coastline": way_3d = way_3d.translate([0, 0, -5 + 0.3])  # FIXME: hacks coastline wall with extra_height
        if way_2d.extra.get('ddd:area:type') == 'water': way_3d = way_3d.translate([0, 0, -0.5])
        return way_3d
    """

    def generate_way_3d_railway(self, way_2d):
        '''
        '''
        # TODO: Elevation shall be applied for ways in a common way: Way generation if special could be handled by ddd:area:type ?

        rail_height = 0.20

        result = ddd.group3()

        for way_2d in way_2d.individualize().flatten().children:

            way_2d_interior = way_2d.buffer(-0.3)  # .individualize()
            if (len(way_2d_interior.individualize().children) > 1):
                way_3d = way_2d.triangulate()
            else:
                way_3d = way_2d.extrude_step(way_2d_interior, rail_height, base=False, cap=False, method=ddd.EXTRUSION_METHOD_SUBTRACT)

            way_3d = way_3d.material(ddd.mats.dirt)
            way_3d = ddd.uv.map_cubic(way_3d)
            way_3d.extra['ddd:shadows'] = False
            way_3d.extra['ddd:collider'] = True

            pathline = way_2d_interior.extra['way_1d'].copy()
            way_2d_interior = uvmapping.map_2d_path(way_2d_interior, pathline, line_x_offset=0.5, line_x_width=0.5, line_d_scale=0.25)
            railroad_3d = way_2d_interior.triangulate().translate([0, 0, rail_height]).material(ddd.mats.railway)
            railroad_3d.extra['ddd:collider'] = True
            railroad_3d.extra['ddd:shadows'] = False
            try:
                uvmapping.map_3d_from_2d(railroad_3d, way_2d_interior)
            except Exception as e:
                logger.error("Could not map railway UV coordinates: %s", e)
                railroad_3d.extra['uv'] = None

            railroad_group = ddd.group3([way_3d, railroad_3d])
            if int(ddd.data.get('ddd:area:subdivide', 0)) > 0:
                railroad_group = ddd.meshops.subdivide_to_grid(railroad_group, float(ddd.data.get('ddd:area:subdivide')))

            result.append(railroad_group)

        # Apply elevation
        result = self.osm.areas3.generate_area_3d_apply_elevation(way_2d, result)

        return result

    def generate_ways_3d_subways(self):
        """
        Generates boxing for sub ways.
        """
        logger.info("Generating subways.")
        logger.warn("IMPLEMENT 2D/3D separation for this, as it needs to be cropped, and it's being already cropped earlier")

        # Take roads
        ways = [w for w in self.osm.ways_2d["-1a"].children] + [w for w in self.osm.ways_2d["-1"].children]

        union = self.osm.ways_2d["-1"].union()
        union_with_transitions = ddd.group(ways, empty="2").union()
        union_sidewalks = union_with_transitions.buffer(0.6, cap_style=2, join_style=2)

        sidewalks_2d = union_sidewalks.subtract(union_with_transitions)  # we include transitions
        walls_2d = sidewalks_2d.buffer(0.5, cap_style=2, join_style=2).subtract(union_sidewalks)
        floors_2d = union_sidewalks.copy()
        ceilings_2d = union.buffer(0.6, cap_style=2, join_style=2).subtract(self.osm.ways_2d["-1a"])

        # FIXME: Move cropping to generic site, use interintermediatemediate osm.something for storage
        crop = ddd.shape(self.osm.area_crop)
        sidewalks_2d = sidewalks_2d.intersection(crop)
        walls_2d = walls_2d.intersection(crop)
        floors_2d = floors_2d.intersection(crop)
        ceilings_2d = ceilings_2d.intersection(crop)

        sidewalks_3d = sidewalks_2d.extrude(0.3).translate([0, 0, -5]).material(ddd.mats.sidewalk)
        walls_3d = walls_2d.extrude(5).translate([0, 0, -5]).material(ddd.mats.cement)
        #floors_3d = floors_2d.extrude(-0.3).translate([0, 0, -5]).material(ddd.mats.sidewalk)
        floors_3d = floors_2d.triangulate().translate([0, 0, -5]).material(ddd.mats.sidewalk)
        ceilings_3d = ceilings_2d.extrude(0.5).translate([0, 0, -1.0]).material(ddd.mats.cement)

        sidewalks_3d = terrain.terrain_geotiff_elevation_apply(sidewalks_3d, self.osm.ddd_proj)
        sidewalks_3d = ddd.uv.map_cubic(sidewalks_3d)
        walls_3d = terrain.terrain_geotiff_elevation_apply(walls_3d, self.osm.ddd_proj)
        walls_3d = ddd.uv.map_cubic(walls_3d)
        floors_3d = terrain.terrain_geotiff_elevation_apply(floors_3d, self.osm.ddd_proj)
        ceilings_3d = terrain.terrain_geotiff_elevation_apply(ceilings_3d, self.osm.ddd_proj)
        ceilings_3d = ddd.uv.map_cubic(ceilings_3d)

        subway = ddd.group([sidewalks_3d, walls_3d, floors_3d, ceilings_3d], empty=3).translate([0, 0, -0.2])

        # Subdivide
        if int(ddd.data.get('ddd:area:subdivide', 0)) > 0:
            subway = ddd.meshops.subdivide_to_grid(subway, float(ddd.data.get('ddd:area:subdivide')))

        self.osm.other_3d.children.append(subway)

    def generate_ways_3d_elevated(self):

        logger.info("Generating elevated ways.")
        logger.warn("IMPLEMENT 2D/3D separation for this, as it needs to be cropped")

        elevated = []

        # Walk roads
        ways = ([w for w in self.osm.ways_2d["1"].children] +
                [w for w in self.osm.ways_2d["0a"].children] +
                [w for w in self.osm.ways_2d["-1a"].children])
        # ways_union = ddd.group(ways).union()

        sidewalk_width = 0.4

        elevated_union = DDDObject2()
        for way in ways:
            # way_longer = way.buffer(0.3, cap_style=1, join_style=2)

            if 'intersection' in way.extra: continue

            way_with_sidewalk_2d = way.buffer(sidewalk_width, cap_style=2, join_style=2)
            #way_with_sidewalk_2d_extended = node2/geomops/already_implemented? -> extend_way(way).buffer(sidewalk_width, cap_style=2, join_style=2)
            sidewalk_2d = way_with_sidewalk_2d.subtract(way).material(ddd.mats.sidewalk)
            wall_2d = way_with_sidewalk_2d.buffer(0.25, cap_style=2, join_style=2).subtract(way_with_sidewalk_2d).buffer(0.001, cap_style=2, join_style=2).material(ddd.mats.cement)
            floor_2d = way_with_sidewalk_2d.buffer(0.3, cap_style=2, join_style=2).buffer(0.001, cap_style=2, join_style=2).material(ddd.mats.cement)

            sidewalk_2d.extra['way_2d'] = way
            wall_2d.extra['way_2d'] = way
            floor_2d.extra['way_2d'] = way

            # Get connected ways
            connected = self.osm.ways1.follow_way(way.extra['way_1d'], 1)
            connected_2d = ddd.group([self.osm.ways2.get_way_2d(c) for c in connected])
            if 'intersection_start_2d' in way.extra['way_1d'].extra:
                connected_2d.append(way.extra['way_1d'].extra['intersection_start_2d'])
            if 'intersection_end_2d' in way.extra['way_1d'].extra:
                connected_2d.append(way.extra['way_1d'].extra['intersection_end_2d'])
            # print(connected)

            sidewalk_2d = sidewalk_2d.subtract(connected_2d).buffer(0.001)
            wall_2d = wall_2d.subtract(connected_2d.buffer(sidewalk_width))
            # TODO: Subtract floors from connected or resolve intersections
            wall_2d = wall_2d.subtract(elevated_union)

            # FIXME: Move cropping to generic site, use itermediate osm.something for storage
            crop = ddd.shape(self.osm.area_crop)
            sidewalk_2d = sidewalk_2d.intersection(crop.buffer(-0.003)).clean(eps=0.01)
            wall_2d = wall_2d.intersection(crop.buffer(-0.003)).clean(eps=0.01)
            floor_2d = floor_2d.intersection(crop.buffer(-0.003)).clean(eps=0.01)

            #FIXME: TODO: this shal be done earlier, before generating the path
            #if way.extra.get('ddd:way:elevated:material', None):
            #    way.extra['way_2d'].material(way.extra.get('ddd:way:elevated:material'))

            # ddd.group((sidewalk_2d, wall_2d)).show()
            if way.extra.get('ddd:way:elevated:border', None) == 'fence':
                fence_2d =  wall_2d.outline().clean()
                fence_2d = fence_2d.material(ddd.mats.fence)
                #fence_2d.dump()
                #wall_2d.show()
                fence_2d.extra['ddd:item'] = True
                fence_2d.extra['ddd:item:height'] = 1.2
                fence_2d.extra['ddd:height'] = 1.2
                fence_2d.extra['barrier'] = "fence"
                fence_2d.extra['_height_mapping'] = "terrain_geotiff_and_path_apply"
                fence_2d.extra['way_1d'] = way.extra['way_1d']

                self.osm.items_1d.append(fence_2d)
                elevated.append((sidewalk_2d, None, floor_2d))
            else:
                elevated.append((sidewalk_2d, wall_2d, floor_2d))

            elevated_union = elevated_union.union(ddd.group([sidewalk_2d, wall_2d, floor_2d]))

            # Bridge piers
            path = way.extra['way_1d']
            if path.geom.length > 15.0:  # and path.extra['ddd:bridge:posts']:
                # Generate posts
                interval = 35.0
                length = path.geom.length
                numposts = int(length / interval)
                idx = 0

                logger.debug("Piers for bridge (length=%s, num=%d, way=%s)", length, numposts, way)
                for d in numpy.linspace(0.0, length, numposts, endpoint=False):
                    if d == 0.0: continue

                    # Calculate left and right perpendicular intersections with sidewalk, park, land...
                    p, segment_idx, segment_coords_a, segment_coords_b = path.interpolate_segment(d)

                    # FIXME: Use items and crop in a generic way (same for subways) (so ignore below in common etc)
                    if not self.osm.area_crop.contains(ddd.point(p).geom):
                        continue

                    dir_vec = (segment_coords_b[0] - segment_coords_a[0], segment_coords_b[1] - segment_coords_a[1])
                    dir_vec_length = math.sqrt(dir_vec[0] ** 2 + dir_vec[1] ** 2)
                    dir_vec = (dir_vec[0] / dir_vec_length, dir_vec[1] / dir_vec_length)
                    angle = math.atan2(dir_vec[1], dir_vec[0])

                    idx = idx + 1

                    if len(p) < 3:
                        logger.error("Bridge path with less than 3 components when building bridge piers.")
                        continue

                    if p[2] > 1.0:  # If no height, no pilar, but should be a margin and also corrected by base_height
                        item = ddd.rect([-way.extra['ddd:way:width'] * 0.3, -0.5, way.extra['ddd:way:width'] * 0.3, 0.5], name="Bridge Post %s" % way.name)
                        item = item.extrude(-(math.fabs(p[2]) - 0.5)).material(ddd.mats.cement)
                        item = ddd.uv.map_cubic(item)
                        item = item.rotate([0, 0, angle - math.pi / 2]).translate([p[0], p[1], 0])
                        vertex_func = self.get_height_apply_func(path)
                        item = item.vertex_func(vertex_func)
                        item = terrain.terrain_geotiff_elevation_apply(item, self.osm.ddd_proj)
                        item = item.translate([0, 0, -0.8])
                        item.extra['way_2d'] = way
                        item.extra['ddd:bridge:post'] = True
                        self.osm.other_3d.children.append(item)

        elevated_3d = []
        for item in elevated:
            sidewalk_2d, wall_2d, floor_2d = item
            sidewalk_3d = sidewalk_2d.extrude(0.2).translate([0, 0, -0.2])
            wall_3d = wall_2d.extrude(0.6) if wall_2d else None
            floor_3d = floor_2d.extrude(-0.5).translate([0, 0, -0.2])
            # extra_height = way_2d.extra['extra_height']
            # way_3d = way_2d.extrude(-0.2 - extra_height).translate([0, 0, extra_height])  # + layer_height

            sidewalk_3d = ddd.uv.map_cubic(sidewalk_3d)
            wall_3d = ddd.uv.map_cubic(wall_3d) if wall_3d else None
            floor_3d = ddd.uv.map_cubic(floor_3d)

            elevated_3d.append(sidewalk_3d)
            elevated_3d.append(floor_3d)
            if wall_3d:
                elevated_3d.append(wall_3d)

        # Raise items to their way height position
        nitems = []
        for item in elevated_3d:
            # print(item.extra)
            path = item.extra['way_1d']
            vertex_func = self.osm.ways1.get_height_apply_func(path)
            nitem = item.vertex_func(vertex_func)
            nitems.append(nitem)

        result = ddd.group(nitems, empty=3)
        result = terrain.terrain_geotiff_elevation_apply(result, self.osm.ddd_proj)
        self.osm.other_3d.children.append(result)

