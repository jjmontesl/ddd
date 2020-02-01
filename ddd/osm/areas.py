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
import pyproj
from shapely import geometry
from shapely.geometry import shape
from shapely.geometry.geo import shape
from shapely.ops import transform

from ddd.ddd import DDDObject2, DDDObject3
from ddd.ddd import ddd
from ddd.pack.sketchy import terrain, plants, urban
from trimesh import creation, primitives, boolean
import trimesh
from trimesh.base import Trimesh
from trimesh.path import segments
from trimesh.path.path import Path
from trimesh.scene.scene import Scene, append_scenes
from trimesh.visual.material import SimpleMaterial
from shapely.geometry.linestring import LineString
from numpy import angle
from shapely.geometry.polygon import LinearRing
from shapely.errors import TopologicalError


# Get instance of logger for this module
logger = logging.getLogger(__name__)

class AreasOSMBuilder():

    def __init__(self, osmbuilder):

        self.osm = osmbuilder

    def generate_areas_2d(self):
        logger.info("Generating 2D areas")
        logger.warn("FIXME: Use DDD, not features, and preprocess Points to areas, and so we can sort by area size, etc")

        # Union all roads in the plane to subtract
        union = ddd.group([self.osm.ways_2d['0'], self.osm.ways_2d['-1a'], self.osm.areas_2d]).union()

        for feature in self.osm.features:
            area = None

            if feature['geometry']['type'] == 'Point':
                continue

            if feature['properties'].get('leisure', None) in ('park', 'garden'):
                area = self.generate_area_2d_park(feature)
            if feature['properties'].get('leisure', None) in ('pitch', ):  # Cancha
                area = self.generate_area_2d_park(feature).material(self.osm.mat_pitch)
            elif feature['properties'].get('landuse', None) in ('grass', ):
                area = self.generate_area_2d_park(feature)
            elif feature['properties'].get('landuse', None) in ('railway', ):
                area = self.generate_area_2d_railway(feature)
            elif feature['properties'].get('landuse', None) in ('brownfield', ):
                area = self.generate_area_2d_unused(feature)
            elif feature['properties'].get('amenity', None) in ('school', ):
                area = self.generate_area_2d_school(feature)

            #elif feature['properties'].get('amenity', None) in ('fountain', ):
            #    area = self.generate_area_2d_school(feature)

            if area:
                logger.debug("Area: %s", area)
                area = area.subtract(union)
                #union = union.union(area)
                self.osm.areas_2d.children.append(area)

    def generate_areas_2d_interways(self):

        logger.info("Generating 2D areas between ways")

        #self.osm.ways_2d['0'].dump()
        #self.osm.ways_2d['-1a'].dump()
        #self.osm.areas_2d.dump()
        try:
            union = ddd.group([self.osm.ways_2d['0'], self.osm.ways_2d['-1a'], self.osm.areas_2d]).union()
        except TopologicalError as e:
            logger.error("Error calculating interways: %s", e)
            l0 = self.osm.ways_2d['0'].union()
            lm1a = self.osm.ways_2d['-1a'].union()
            #l0a = self.osm.ways_2d['0a'].union()  # shall be trimmed  # added to avoid height conflicts but leaves holes
            c = self.osm.areas_2d.union()
            union = ddd.group([c, l0, lm1a]).union()
            #union = ddd.group([self.osm.ways_2d['0'], self.osm.ways_2d['-1a'], self.osm.areas_2d]).union()

        #union = union.buffer(0.5)
        #union = union.buffer(-0.5)
        if not union.geom: return

        for c in ([union.geom] if union.geom.type == "Polygon" else union.geom):
            if c.type == "LineString":
                logger.warning("Interways areas union resulted in LineString geometry. Skipping.")
                continue
            for interior in c.interiors:
                area = ddd.polygon(interior.coords, name="Interways area")
                if area:
                    area = area.subtract(union)
                    area = area.material(self.osm.mat_pavement)
                    self.osm.areas_2d.children.append(area)
                else:
                    logger.warn("Invalid square.")

    def generate_area_2d_park(self, feature):
        area = ddd.shape(feature["geometry"], name="Park: %s" % feature['properties'].get('name', None))
        area = area.material(self.osm.mat_park)

        # Add trees if necesary
        # FIXME: should not check for None in intersects, filter shall not return None (empty group)
        trees = self.osm.items_1d.filter(lambda o: o.extra.get('natural') == 'tree')
        has_trees = area.intersects(trees)
        add_trees = not has_trees and area.geom.area > 100

        if add_trees:
            tree_density_m2 = 0.0025
            num_trees = int((area.geom.area * tree_density_m2) + 1)
            num_trees = min(num_trees, 20)
            logger.debug("Adding %d trees to %s", num_trees, area)
            logger.warning("Should be adding items_1d or items_2d, not 3D directly")
            for p in area.random_points(num_points=num_trees):
                #plant = plants.plant().translate([p[0], p[1], 0.0])
                #self.osm.items_3d.children.append(plant)
                tree = ddd.point(p, name="Tree")
                tree.extra['natural'] = 'tree'
                self.osm.items_1d.children.append(tree)

        return area

    def generate_area_2d_railway(self, feature):
        area = ddd.shape(feature["geometry"], name="Railway area: %s" % feature['properties'].get('name', None))
        area = area.material(self.osm.mat_dirt)
        return area

    def generate_area_2d_school(self, feature):
        area = ddd.shape(feature["geometry"], name="School: %s" % feature['properties'].get('name', None))
        area = area.material(self.osm.mat_dirt)
        return area

    def generate_area_2d_unused(self, feature):
        area = ddd.shape(feature["geometry"], name="Unused: %s" % feature['properties'].get('name', None))
        area = area.material(self.osm.mat_dirt)
        return area

    def generate_areas_3d(self):
        logger.info("Generating 3D areas (%d)", len(self.osm.areas_2d.children))
        for area_2d in self.osm.areas_2d.children:
            try:
                area_3d = self.generate_area_3d(area_2d)
                self.osm.areas_3d.children.append(area_3d)
            except ValueError as e:
                logger.warn("Could not generate area %s: %s", area_2d, e)
            except IndexError as e:
                logger.warn("Could not generate area %s: %s", area_2d, e)

    def generate_area_3d(self, area_2d):
        area_3d = area_2d.extrude(-0.5).translate([0, 0, 0.3])
        area_3d = terrain.terrain_geotiff_elevation_apply(area_3d, self.osm.ddd_proj)
        return area_3d

    '''
    def generate_ground_3d_old(self, area_crop):

        logger.info("Generating terrain (bounds: %s)", area_crop.bounds)

        #terr = terrain.terrain_grid(distance=500.0, height=1.0, detail=25.0).translate([0, 0, -0.5]).material(mat_terrain)
        terr = terrain.terrain_geotiff(area_crop.bounds, detail=10.0, ddd_proj=self.osm.ddd_proj).material(self.osm.mat_terrain)
        #terr2 = terrain.terrain_grid(distance=60.0, height=10.0, detail=5).translate([0, 0, -20]).material(mat_terrain)

        self.osm.ground_3d = terr
    '''

    def generate_coastline_3d(self, area_crop):

        logger.info("Generating water and land areas according to coastline: %s", (area_crop.bounds))

        #self.water_3d = terrain.terrain_grid(self.area_crop.bounds, height=0.1, detail=200.0).translate([0, 0, 1]).material(mat_sea)

        water = ddd.rect(area_crop.bounds, name="Ground")
        coastlines = []
        coastlines_1d = []
        for way in self.osm.ways_1d.children:
            if way.extra['natural'] == 'coastline':
                coastlines_1d.append(way)
                coastlines.append(way.buffer(0.1))

        logger.debug("Coastlines: %s", (coastlines_1d, ))
        if not coastlines:
            logger.info("No coastlines in the feature set.")
            return

        coastlines = ddd.group(coastlines)
        coastlines_1d = ddd.group(coastlines_1d)

        coastline_areas = water.subtract(coastlines)
        #coastline_areas.save("/tmp/test.svg")
        #coastline_areas.dump()

        areas = []
        areas_2d = []
        geoms = coastline_areas.geom.geoms if coastline_areas.geom.type == 'MultiPolygon' else [coastline_areas.geom]
        for water_area_geom in geoms:
            # Find closest point, closest segment, and angle to closest segment
            water_area_point = water_area_geom.representative_point()
            p, segment_idx, segment_coords_a, segment_coords_b = coastlines_1d.closest_segment(ddd.shape(water_area_point))
            pol = LinearRing([segment_coords_a, segment_coords_b, water_area_point.coords[0]])

            if not pol.is_ccw:
                area_2d = ddd.shape(water_area_geom)
                #area_3d = area_2d.extrude(-0.2)
                area_3d = area_2d.triangulate()
                area_3d = area_3d.material(self.osm.mat_sea)
                areas_2d.append(area_2d)
                areas.append(area_3d)

        if areas:
            self.osm.water_3d = ddd.group(areas)
            self.osm.water_2d = ddd.group(areas_2d)
        else:
            logger.warning("No coastline water areas generated!")

    def generate_ground_3d(self, area_crop):

        logger.info("Generating terrain (bounds: %s)", area_crop.bounds)

        #terr = terrain.terrain_grid(distance=500.0, height=1.0, detail=25.0).translate([0, 0, -0.5]).material(mat_terrain)
        #terr = terrain.terrain_geotiff(area_crop.bounds, detail=10.0, ddd_proj=self.osm.ddd_proj).material(mat_terrain)
        #terr2 = terrain.terrain_grid(distance=60.0, height=10.0, detail=5).translate([0, 0, -20]).material(mat_terrain)
        #terr = ddd.grid2(area_crop.bounds, detail=10.0).buffer(0.0)  # useless, shapely does not keep triangles when operating
        terr = ddd.rect(area_crop.bounds, name="Ground")

        terr = terr.subtract(self.osm.ways_2d['0'])
        terr = terr.subtract(self.osm.ways_2d['-1a'])
        #terr = terr.subtract(self.osm.ways_2d['0a'])  # added to avoid floor, but shall be done better, by layers spawn and base_height,e tc
        terr = terr.subtract(self.osm.areas_2d)
        terr = terr.subtract(self.osm.water_2d)

        # The buffer is fixing a core segment violation :/
        #terr.save("/tmp/test.svg")
        #terr.dump()
        #terr.show()
        #terr = ddd.group([DDDObject2(geom=s.buffer(0.5).buffer(-0.5)) for s in terr.geom.geoms if not s.is_empty])

        #terr.save("/tmp/test.svg")
        #terr = terr.triangulate()
        try:
            terr = terr.buffer(0.001).extrude(0.3)
        except ValueError as e:
            logger.error("Cannot generate terrain (FIXME): %s", e)
            raise
        terr = terrain.terrain_geotiff_elevation_apply(terr, self.osm.ddd_proj)
        terr = terr.material(self.osm.mat_terrain)

        self.osm.ground_3d = terr


