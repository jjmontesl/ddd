# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

from collections import defaultdict, namedtuple
import logging
import math
import random
import sys

from csg import geom as csggeom
from csg.core import CSG
import geojson
import noise
from numpy import angle
import pyproj
from shapely import geometry
from shapely.errors import TopologicalError
from shapely.geometry import shape
from shapely.geometry.geo import shape
from shapely.geometry.linestring import LineString
from shapely.geometry.polygon import LinearRing
from shapely.ops import transform
from trimesh import creation, primitives, boolean
import trimesh
from trimesh.base import Trimesh
from trimesh.path import segments
from trimesh.path.path import Path
from trimesh.scene.scene import Scene, append_scenes
from trimesh.visual.material import SimpleMaterial

from ddd.ddd import DDDObject2, DDDObject3
from ddd.ddd import ddd
from ddd.pack.sketchy import plants, urban, sports
from ddd.geo import terrain
from ddd.core.exception import DDDException
from ddd.util.dddrandom import weighted_choice
from _ast import Or


# Get instance of logger for this module
logger = logging.getLogger(__name__)

class Areas3DOSMBuilder():

    max_trees = None

    def __init__(self, osmbuilder):

        self.osm = osmbuilder


    def generate_coastline_3d(self, area_crop):


        '''
        logger.info("Generating water and land areas according to coastline: %s", (area_crop.bounds))

        #self.water_3d = terrain.terrain_grid(self.area_crop.bounds, height=0.1, detail=200.0).translate([0, 0, 1]).material(mat_sea)

        water = ddd.rect(area_crop.bounds, name="Ground")
        coastlines = []
        coastlines_1d = []

        for way in self.osm.items_1d.children:
            if way.extra.get('osm:natural') == 'coastline':
                coastlines_1d.append(way)
                coastlines.append(way.buffer(0.01))
        #for way in self.osm.features.children:
        #    if way.properties.get('natural') == 'coastline':
        #        coastlines_1d.append(ddd.shape(way.geometry))
        #        coastlines.append(ddd.shape(way.geometry).buffer(0.1))

        logger.debug("Coastlines: %s", (coastlines_1d, ))
        if not coastlines:
            logger.info("No coastlines in the feature set.")
            return

        coastlines = ddd.group(coastlines)
        coastlines_1d = ddd.group(coastlines_1d)
        coastline_areas = water.subtract(coastlines)
        #coastline_areas.save("/tmp/test.svg")
        #coastline_areas.dump()

        # Generate coastline
        if coastlines_1d.children:
            coastlines_3d = coastlines_1d.intersection(water)
            coastlines_3d = coastlines_3d.individualize().extrude(10.0).translate([0, 0, -10.0])
            coastlines_3d = terrain.terrain_geotiff_elevation_apply(coastlines_3d, self.osm.ddd_proj)
            coastlines_3d = ddd.uv.map_cubic(coastlines_3d)
            coastlines_3d.name = 'Coastline: %s' % coastlines_3d.name
            self.osm.other_3d.append(coastlines_3d)


        areas = []
        areas_2d = []
        geoms = coastline_areas.geom.geoms if coastline_areas.geom.type == 'MultiPolygon' else [coastline_areas.geom]
        for water_area_geom in geoms:
            # Find closest point, closest segment, and angle to closest segment
            water_area_geom = ddd.shape(water_area_geom).clean(eps=0.01).geom

            if not water_area_geom.is_simple:
                logger.error("Invalid water area geometry (not simple): %s", water_area_geom)
                continue

            water_area_point = water_area_geom.representative_point()
            p, segment_idx, segment_coords_a, segment_coords_b, closest_obj, closest_d = coastlines_1d.closest_segment(ddd.shape(water_area_point))
            pol = LinearRing([segment_coords_a, segment_coords_b, water_area_point.coords[0]])

            if not pol.is_ccw:
                #area_3d = area_2d.extrude(-0.2)
                area_2d = ddd.shape(water_area_geom).buffer(0.10).clean(eps=0.01)
                area_2d.validate()
                area_2d = area_2d.material(ddd.mats.sea)

                area_3d = area_2d.triangulate().translate([0, 0, -0.5])
                area_3d.extra['ddd:collider'] = False
                area_3d.extra['ddd:shadows'] = False
                area_3d.extra['ddd:occluder'] = False
                areas_2d.append(area_2d)
                areas.append(area_3d)

        if areas:
            self.osm.water_3d = ddd.group(areas)
            self.osm.water_2d = ddd.group(areas_2d)
        else:
            logger.debug("No water areas from coastline generated.")
        '''
        pass

    '''
    def generate_ground_3d(self, area_crop):

        logger.info("Generating 3D terrain (bounds: %s)", area_crop.bounds)

        terr = self.osm.ground_2d

        # The buffer is fixing a core segment violation :/
        #terr.save("/tmp/test.svg")
        #terr.dump()
        #terr.show()
        #terr = ddd.group([DDDObject2(geom=s.buffer(0.5).buffer(-0.5)) for s in terr.geom.geoms if not s.is_empty])

        #terr.save("/tmp/test.svg")
        #terr = terr.triangulate()
        try:
            #terr = terr.individualize()
            #terr.validate()
            logger.warning("There's a buffer(0.000-0.001) operation which shouldn't be here: improve and use 'clean()'.")
            terr = terr.buffer(0.001)
            #terr = terr.buffer(0.0)
            #terr = terr.clean(eps=0.001)

            #terr = terr.extrude(0.3)
            terr = terr.triangulate()
        except ValueError as e:
            logger.error("Cannot generate terrain (FIXME): %s", e)
            raise DDDException("Coould not generate terrain: %s" % e, ddd_obj=terr)

        terr = terrain.terrain_geotiff_elevation_apply(terr, self.osm.ddd_proj)

        self.osm.ground_3d.append(terr)
    '''

    def generate_areas_3d(self, areas_2d):

        logger.info("Generating 3D areas (%d)", len(self.osm.areas_2d.children))

        areas_3d = ddd.group3(name="Areas")

        for area_2d in areas_2d.children:
            try:
                if area_2d.extra.get('ddd:area:type', None) is None:
                    area_3d = self.generate_area_3d(area_2d)
                elif area_2d.extra['ddd:area:type'] == 'sidewalk':
                    area_3d = self.generate_area_3d(area_2d)
                elif area_2d.extra['ddd:area:type'] == 'park':
                    area_3d = self.generate_area_3d(area_2d)
                elif area_2d.extra['ddd:area:type'] == 'steps':
                    area_3d = self.generate_area_3d(area_2d)
                    # TODO: Raise areas to base_height (area.extra['ddd:area:container'] ?)
                elif area_2d.extra['ddd:area:type'] == 'pitch':
                    area_3d = self.generate_area_3d_pitch(area_2d)
                elif area_2d.extra['ddd:area:type'] == 'water':
                    area_3d = self.generate_area_3d_water(area_2d)
                elif area_2d.extra['ddd:area:type'] == 'underwater':
                    area_3d = self.generate_area_3d_underwater(area_2d)
                else:
                    logger.warning("Area type undefined: %s", area_2d.extra.get('ddd:area:type', None))
                    raise AssertionError("Area type undefined: %s" % (area_2d.extra.get('ddd:area:type', None)))

                if area_3d:
                    areas_3d.append(area_3d)

            except ValueError as e:
                logger.error("Could not generate area %s: %s", area_2d, e)
                raise
            except IndexError as e:
                logger.error("Could not generate area %s: %s", area_2d, e)
                raise
            except DDDException as e:
                logger.error("Could not generate area %s: %s", area_2d, e)
                raise

        return areas_3d


    def generate_area_3d(self, area_2d):

        if area_2d.geom is not None and area_2d.geom.type != "LineString":

            if area_2d.geom.type in ('GeometryCollection', 'MultiPolygon'):
                logger.debug("Generating area 3d as separate areas as it is a GeometryCollection: %s", area_2d)
                # FIXME: We might do this in extrude_step, like we do in triangulate and extrude, but difficult as it is in steps.
                # But also, we should have an individualize that work, correct iterators, and a generic cleanup/flatten method
                # to flatten areas, which might solve this.
                areas_3d = []
                for a in area_2d.individualize().children:
                    areas_3d.append(self.generate_area_3d(a))
                return ddd.group(areas_3d, empty=3)

            if area_2d.extra.get('ddd:area:type', None) == 'park':

                area_3d = area_2d.extrude_step(area_2d.buffer(-1.0), 0.1, base=False)
                area_3d = area_3d.extrude_step(area_2d.buffer(-3.0), 0.1)

                # Grass
                if True:
                    # For volumetric grass, as described by: https://www.bruteforce-games.com/post/grass-shader-devblog-04
                    grass_layers = []
                    colors = ['#000000', '#222222', '#444444', '#666666', '#888888', '#aaaaaa', '#cccccc', '#eeeeee']
                    for i in range(8):
                        grass_layer = area_3d.copy(name="Grass %d: %s" % (i, area_3d.name))
                        grass_layer = grass_layer.material(ddd.material(name="VolumetricGrass", color=colors[i], extra={'ddd:export-as-marker': True}))
                        #grass_layer.extra['ddd:vertex_colors'] =
                        grass_layer = grass_layer.translate([0, 0, 0.05 * i])
                        grass_layer = terrain.terrain_geotiff_elevation_apply(grass_layer, self.osm.ddd_proj)
                        grass_layer.extra['ddd:shadows'] = False
                        grass_layer.extra['ddd:collider'] = False
                        grass_layer.extra['ddd:occluder'] = False
                        grass_layers.append(grass_layer)
                    #self.osm.other_3d.append(grass_layers)  #ddd.group3([area_3d, grass_layers])
                    area_3d.children.extend(grass_layers)


                #area_3d = ddd.group([area_2d.triangulate().translate([0, 0, 0.0]),
                #                     area_2d.buffer(-1.0).triangulate().translate([0, 0, 0.2]),
                #                     area_2d.buffer(-3.0).triangulate().translate([0, 0, 0.3])])

                #area_3d = area_3d.translate([0, 0, 0])

            elif area_2d.extra.get('ddd:area:type', None) == 'steps':

                area_3d = area_2d.extrude_step(area_2d, area_2d.extra['ddd:steps:height'], base=False)
                for stepidx in range(1, area_2d.extra['ddd:steps:count'] + 1):
                    area_3d = area_3d.extrude_step(area_2d.buffer(-area_2d.extra['ddd:steps:depth'] * stepidx), 0)
                    area_3d = area_3d.extrude_step(area_2d.buffer(-area_2d.extra['ddd:steps:depth'] * stepidx), area_2d.extra['ddd:steps:height'])

                # TODO: Crop in 3D (or as a workaround fake it as centroid cropping)

            elif area_2d.extra.get('ddd:area:type', None) == 'sidewalk':

                try:
                    height = area_2d.extra.get('ddd:height', 0.2)
                    #area_3d = area_2d.extrude(-0.5 - height).translate([0, 0, height])
                    #area_3d = ddd.uv.map_cubic(area_3d)

                    if True:
                        interior = area_2d.buffer(-0.3)
                        area_3d = interior.extrude(-0.5 - height).translate([0, 0, height])
                        area_3d = ddd.uv.map_cubic(area_3d)
                        kerb_3d = area_2d.subtract(interior).extrude(-0.5 - height).translate([0, 0, height])
                        kerb_3d = ddd.uv.map_cubic(kerb_3d).material(ddd.mats.cement)
                        #if area_3d.mesh:
                        #    area_3d = terrain.terrain_geotiff_elevation_apply(area_3d, self.osm.ddd_proj)
                        #    kerb_3d = terrain.terrain_geotiff_elevation_apply(kerb_3d, self.osm.ddd_proj).material(ddd.mats.cement)
                        #area_3d.append(kerb_3d)
                        kerb_3d = terrain.terrain_geotiff_elevation_apply(kerb_3d, self.osm.ddd_proj)
                        self.osm.areas_3d.children.append(kerb_3d)
                except Exception as e:
                    logger.error("Could not generate area: %s (%s)", e, area_2d)
                    area_3d = DDDObject3()

            else:
                try:
                    height = area_2d.extra.get('ddd:height', 0.2)
                    if height:
                        area_3d = area_2d.extrude(-0.5 - height).translate([0, 0, height])
                    else:
                        area_3d = area_2d.triangulate()
                    area_3d = ddd.uv.map_cubic(area_3d)
                except Exception as e:
                    logger.error("Could not generate area: %s (%s)", e, area_2d)
                    area_3d = DDDObject3()

        else:
            if len(area_2d.children) == 0:
                logger.warning("Null area geometry (children?): %s", area_2d)
            area_3d = DDDObject3()

        if area_3d.mesh or area_3d.children:
            #height = area_2d.extra.get('ddd:height', 0.2)
            area_3d = terrain.terrain_geotiff_elevation_apply(area_3d, self.osm.ddd_proj)

        area_3d.children.extend( [self.generate_area_3d(c) for c in area_2d.children] )

        return area_3d

    def generate_area_3d_pitch(self, area_2d):

        if area_2d.geom is None:
            return None

        logger.debug("Pitch: %s", area_2d)
        area_3d = self.generate_area_3d(area_2d)

        # TODO: pass size then adapt to position and orientation, easier to construct and reuse
        # TODO: get area uncropped (create a cropping utility that stores the original area)

        sport = area_2d.extra.get('osm:sport', None)

        if sport == 'tennis':
            lines = sports.field_lines_area(area_2d, sports.tennis_field_lines, padding=3.0)
        elif sport == 'basketball':
            lines = sports.field_lines_area(area_2d, sports.basketball_field_lines, padding=2.0)
        else:
            lines = sports.field_lines_area(area_2d, sports.football_field_lines, padding=1.25)

        if lines:
            lines = terrain.terrain_geotiff_elevation_apply(lines, self.osm.ddd_proj).translate([0, 0, 0.15])
            height = area_2d.extra.get('ddd:height', 0.2)
            lines = lines.translate([0, 0, height])

            area_3d = ddd.group3([area_3d, lines])
        else:
            logger.debug("No pitch lines generated.")

        return area_3d

    def generate_area_3d_water(self, area_2d):
        area_3d = self.generate_area_3d(area_2d)

        # Move water down, to account for waves
        area_3d = area_3d.translate([0, 0, -0.5])
        return area_3d

    def generate_area_3d_underwater(self, area_2d):
        logger.info ("Generating underwater for: %s", area_2d)
        #area_2d.dump()
        areas_2d = area_2d.individualize().flatten().clean()
        #area_2d.show()

        result = ddd.group3()
        for area_2d in areas_2d.children:

            area_2d = area_2d.clean()
            try:
                area_2d.validate()
            except DDDException as e:
                logger.error("Could not generate underwater area (invalid area %s): %s", area_2d, e)
                continue

            if area_2d.geom.type == "LineString":
                logger.error("Could not generate underwater area (area is line): %s", area_2d)
                continue

            try:
                area_3d = area_2d.extrude_step(area_2d.buffer(-1.0), -0.3, base=False)
                area_3d = area_3d.extrude_step(area_2d.buffer(-2.0), -0.5)
                area_3d = area_3d.extrude_step(area_2d.buffer(-4.0), -1.0)
                area_3d = area_3d.extrude_step(area_2d.buffer(-6.0), -0.5)
                area_3d = area_3d.extrude_step(area_2d.buffer(-9.0), -0.4)
                area_3d = area_3d.extrude_step(area_2d.buffer(-12.0), -0.3)
            except Exception as e:
                logger.warn("Exception extruding underwater area (reduced LinearRings need caring): %s", e)
                print(area_2d.geom)
                print(area_2d.buffer(-1.0).geom)
                area_3d = None

            if area_3d is None or area_3d.extra['_extrusion_steps'] < 2:
                logger.debug("Could not extrude underwater area softly. Extruding abruptly.")
                area_3d = area_2d.extrude_step(area_2d.buffer(-0.05), -1.0, base=False)
                area_3d = area_3d.extrude_step(area_2d.buffer(-0.15), -0.5)
                area_3d = area_3d.extrude_step(area_2d.buffer(-0.3), -0.5)
                area_3d = area_3d.extrude_step(area_2d.buffer(-1.0), -0.5)
            if area_3d.extra['_extrusion_steps'] < 1:
                logger.warn("Could not extrude underwater area: %s", area_3d)
                area_3d = area_3d.translate([0, 0, -1.0])
            if area_3d: result.append(area_3d)

        result = terrain.terrain_geotiff_elevation_apply(result, self.osm.ddd_proj)
        #result.show()

        return result
