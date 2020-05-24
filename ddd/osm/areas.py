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

class AreasOSMBuilder():

    max_trees = None

    def __init__(self, osmbuilder):

        self.osm = osmbuilder

    def generate_areas_2d(self):
        logger.info("Generating 2D areas.")

        areas = []
        for feature in self.osm.features_2d.children:
            if feature.geom.type not in ('Polygon', 'MultiPolygon', 'GeometryCollection'):
                continue
            if feature.extra.get('osm:building', None) is not None:
                # FIXME: better filter which features we are interested in
                continue

            area = feature.copy(name="Area: %s" % feature.name)
            area.extra['ddd:area:type'] = area.extra.get('ddd:area:type', None)
            area.extra['ddd:area:container'] = None
            area.extra['ddd:area:contained'] = []
            area.extra['ddd:baseheight'] = 0.0

            try:
                area = area.individualize().flatten()
                area.validate()
            except DDDException as e:
                logger.warn("Invalid geometry (cropping area) for area %s (%s): %s", area, area.extra, e)
                try:
                    area = area.clean(eps=0.001).intersection(ddd.shape(self.osm.area_crop))
                    area = area.individualize().flatten()
                    area.validate()
                except DDDException as e:
                    logger.warn("Invalid geometry (ignoring area) for area %s (%s): %s", area, area.extra, e)
                    continue

            for a in area.children:
                if a.geom:
                    a.extra['ddd:area:area'] = a.geom.area
                    areas.append(a)

        logger.info("Sorting 2D areas  (%d).", len(areas))
        areas.sort(key=lambda a: a.extra['ddd:area:area'])

        for idx in range(len(areas)):
            area = areas[idx]
            for larger in areas[idx + 1:]:
                if larger.contains(area):
                    #logger.debug("Area %s contains %s.", larger, area)
                    area.extra['ddd:area:container'] = larger
                    larger.extra['ddd:area:contained'].append(area)
                    break

        # Union all roads in the plane to subtract
        logger.info("Generating 2D areas subtract.")
        union = ddd.group([self.osm.ways_2d['0'], self.osm.ways_2d['-1a']]).union()  # , self.osm.areas_2d
        #union = ddd.group([self.osm.ways_2d['0'], self.osm.ways_2d['-1a']])

        logger.info("Generating 2D areas (%d)", len(areas))
        for narea in areas:
        #for feature in self.osm.features:
            feature = narea.extra['osm:feature']

            if narea.geom.type == 'Point': continue

            narea.extra['ddd:area:original'] = narea  # Before subtracting any internal area

            '''
            # Subtract areas contained (use contained relationship)
            for contained in narea.extra['ddd:area:contained']:
                narea = narea.subtract(contained)
            '''

            area = None
            if narea.extra.get('osm:leisure', None) in ('park', 'garden'):
                narea = narea.subtract(ddd.group2(narea.extra['ddd:area:contained']))
                narea = narea.subtract(union)
                area = self.generate_area_2d_park(narea)

            elif narea.extra.get('osm:landuse', None) in ('forest', ):
                narea = narea.subtract(ddd.group2(narea.extra['ddd:area:contained']))
                narea = narea.subtract(union)
                area = self.generate_area_2d_forest(narea)
            elif narea.extra.get('osm:landuse', None) in ('vineyard', ):
                narea = narea.subtract(ddd.group2(narea.extra['ddd:area:contained']))
                narea = narea.subtract(union)
                area = self.generate_area_2d_vineyard(narea)

            elif narea.extra.get('osm:natural', None) in ('wood', ):
                narea = narea.subtract(ddd.group2(narea.extra['ddd:area:contained']))
                narea = narea.subtract(union)
                area = self.generate_area_2d_forest(narea)
            elif narea.extra.get('osm:natural', None) in ('wetland', ):
                narea = narea.subtract(ddd.group2(narea.extra['ddd:area:contained']))
                narea = narea.subtract(union)
                area = self.generate_area_2d_wetland(narea)
            elif narea.extra.get('osm:natural', None) in ('beach', ):
                narea = narea.subtract(ddd.group2(narea.extra['ddd:area:contained']))
                narea = narea.subtract(union)
                area = self.generate_area_2d_beach(narea)
            elif narea.extra.get('osm:landuse', None) in ('grass', ):
                narea = narea.subtract(ddd.group2(narea.extra['ddd:area:contained']))
                narea = narea.subtract(union)
                area = self.generate_area_2d_park(narea)

            elif narea.extra.get('osm:amenity', None) in ('parking', ):
                narea = narea.subtract(ddd.group2(narea.extra['ddd:area:contained']))
                narea = narea.subtract(union)
                area = self.generate_area_2d_parking(narea)

            elif (narea.extra.get('osm:public_transport', None) in ('platform', ) or
                  narea.extra.get('osm:railway', None) in ('platform', )):
                narea = narea.subtract(ddd.group2(narea.extra['ddd:area:contained']))
                narea = narea.subtract(union)
                area = self.generate_area_2d_platform(narea)

            elif narea.extra.get('osm:tourism', None) in ('artwork', ):
                narea = narea.subtract(ddd.group2(narea.extra['ddd:area:contained']))
                narea = narea.subtract(union)
                area = self.generate_area_2d_artwork(narea)

            elif narea.extra.get('osm:leisure', None) in ('pitch', ):  # Cancha
                narea = narea.subtract(ddd.group2(narea.extra['ddd:area:contained']))
                area = self.generate_area_2d_pitch(narea)
            elif narea.extra.get('osm:landuse', None) in ('railway', ):
                narea = narea.subtract(ddd.group2(narea.extra['ddd:area:contained']))
                area = self.generate_area_2d_railway(narea)
            elif narea.extra.get('osm:landuse', None) in ('brownfield', ):
                narea = narea.subtract(ddd.group2(narea.extra['ddd:area:contained']))
                area = self.generate_area_2d_unused(narea)
                narea = narea.subtract(union)
            elif narea.extra.get('osm:amenity', None) in ('school', ):
                narea = narea.subtract(ddd.group2(narea.extra['ddd:area:contained']))
                narea = narea.subtract(union)
                area = self.generate_area_2d_school(narea)
            elif (narea.extra.get('osm:waterway', None) in ('riverbank', 'stream') or
                  narea.extra.get('osm:natural', None) in ('water', ) or
                  narea.extra.get('osm:water', None) in ('river', )):
                #narea = narea.subtract(ddd.group2(narea.extra['ddd:area:contained']))
                #narea = narea.subtract(union)
                area = self.generate_area_2d_riverbank(narea)
            else:
                logger.debug("Unknown area: %s", feature)

            #elif feature['properties'].get('amenity', None) in ('fountain', ):
            #    area = self.generate_area_2d_school(feature)

            if area:
                logger.debug("Area: %s", area)
                area = area.subtract(union)

                self.osm.areas_2d.append(area)
                #self.osm.areas_2d.children.extend(area.individualize().children)

    def generate_area_2d_park(self, area, tree_density_m2=0.0025, tree_types=None):

        if tree_types is None:
            tree_types = {'default': 1, 'palm': 0.001}

        #area = ddd.shape(feature["geometry"], name="Park: %s" % feature['properties'].get('name', None))
        feature = area.extra['osm:feature']
        area = area.material(ddd.mats.park)
        area.name = "Park: %s" % feature['properties'].get('name', None)
        area.extra['ddd:area:type'] = 'park'

        # Add trees if necesary
        # FIXME: should not check for None in intersects, filter shall not return None (empty group)
        trees = self.osm.items_1d.filter(lambda o: o.extra.get('osm:natural') == 'tree')
        has_trees = area.intersects(trees)
        add_trees = not has_trees # and area.geom.area > 100

        if add_trees and area.geom:

            tree_area = area.intersection(ddd.shape(self.osm.area_crop)).union()
            tree_type = weighted_choice(tree_types)

            if tree_area.geom:
                # Decimation would affect after
                num_trees = int((tree_area.geom.area * tree_density_m2))
                #if num_trees == 0 and random.uniform(0, 1) < 0.5: num_trees = 1  # alone trees
                if self.max_trees:
                    num_trees = min(num_trees, self.max_trees)
                logger.debug("Adding %d trees to %s", num_trees, area)
                #logger.warning("Should be adding items_1d or items_2d, not 3D directly")
                for p in tree_area.random_points(num_points=num_trees):
                    #plant = plants.plant().translate([p[0], p[1], 0.0])
                    #self.osm.items_3d.children.append(plant)
                    tree = ddd.point(p, name="Tree")
                    tree.extra['osm:natural'] = 'tree'
                    tree.extra['osm:tree:type'] = tree_type
                    self.osm.items_1d.children.append(tree)

        return area

    def generate_area_2d_artwork(self, area):

        feature = area.extra['osm:feature']
        item = area.extra['osm:feature_2d'].centroid()    # area.centroid()
        item.extra['osm:historic'] = "monument"

        area.name = "Artwork: %s" % feature['properties'].get('name', None)
        area.extra['ddd:area:type'] = 'steps'
        area.extra['ddd:steps:count'] = 2
        area.extra['ddd:steps:height'] = 0.16
        area.extra['ddd:steps:depth'] = 0.38
        area = area.material(ddd.mats.stone)

        # Add artwork in center as point
        if item.geom:
            self.osm.items_1d.append(item)
        else:
            logger.warn("Cannot generate area 2D artwork item: %s", area)

        return area

    def generate_area_2d_forest(self, area):
        return self.generate_area_2d_park(area, tree_density_m2=0.004, tree_types={'default': 1})

    def generate_area_2d_wetland(self, area):
        # TODO: put smaller trees and juncos
        return self.generate_area_2d_park(area, tree_density_m2=0.0010)

    def generate_area_2d_beach(self, area):
        area.name = "Beach: %s" % area.name
        area = area.material(ddd.mats.sand)
        return area

    def generate_area_2d_parking(self, area):
        area.name = "Parking: %s" % area.name
        area = area.material(ddd.mats.asphalt)
        return area

    def generate_area_2d_platform(self, area):
        area.name = "Platform: %s" % area.name
        area = area.material(ddd.mats.pavement)
        area.extra['ddd:height'] = 0.3
        return area

    def generate_area_2d_vineyard(self, area):
        area.name = "Vineyard: %s" % area.name
        area = self.generate_area_2d_park(area, tree_density_m2=0.001, tree_types={'default': 1})
        # Generate crops
        return area

    def generate_area_2d_pitch(self, area):
        feature = area.extra['osm:feature']
        area.name = "Pitch: %s" % feature['properties'].get('name', None)
        area.extra['ddd:area:type'] = 'pitch'
        area = area.material(ddd.mats.pitch)
        return area

    def generate_area_2d_railway(self, area):
        feature = area.extra['osm:feature']
        area.name = "Railway area: %s" % feature['properties'].get('name', None)
        area = area.material(ddd.mats.dirt)
        area = self.generate_wallfence_2d(area)
        return area

    def generate_area_2d_school(self, area):
        feature = area.extra['osm:feature']
        area.name = "School: %s" % feature['properties'].get('name', None)
        area = area.material(ddd.mats.dirt)
        area.extra['ddd:height'] = 0.0

        area = self.generate_wallfence_2d(area, doors=2)

        return area

    def generate_area_2d_riverbank(self, area):
        feature = area.extra['osm:feature']
        area.name = "Riverbank: %s" % feature['properties'].get('name', None)
        area.extra['ddd:height'] = 0.0
        area.extra['ddd:area:type'] = 'water'
        area = area.individualize().flatten()
        area = area.material(ddd.mats.sea)
        return area

    def generate_area_2d_unused(self, area, wallfence=True):
        feature = area.extra['osm:feature']
        area.name = "Unused land: %s" % feature['properties'].get('name', None)
        area.extra['ddd:height'] = 0.0
        area = area.material(ddd.mats.dirt)

        if wallfence:
            area = self.generate_wallfence_2d(area)
        #if ruins:
        #if construction
        #if ...

        return area

    def generate_wallfence_2d(self, area, fence_ratio=0.0, wall_thick=0.3, doors=1):

        area_original = area.extra['ddd:area:original']
        reduced_area = area_original.buffer(-wall_thick).clean(eps=0.01)

        wall = area.subtract(reduced_area).material(ddd.mats.bricks)
        try:
            wall = wall.subtract(self.osm.buildings_2d)
        except Exception as e:
            logger.error("Could not subtract buildings from wall: %s", e)

        wall.extra['ddd:height'] = 1.8

        #ddd.uv.map_2d_polygon(wall, area.linearize())
        area = ddd.group2([area, wall])

        return area

    def generate_areas_2d_interways(self):

        logger.info("Generating 2D areas between ways.")

        #self.osm.ways_2d['0'].dump()
        #self.osm.ways_2d['-1a'].dump()
        #self.osm.areas_2d.dump()

        areas_2d = self.osm.areas_2d
        #areas_2d_unsubtracted = ddd.group2()
        #for a in self.osm.areas_2d.children:
        #    if a.extra.get('ddd:area:original', None):
        #        areas_2d.append(a.extra.get('ddd:area:original'))

        try:
            #ways_2d_0 = self.osm.ways_2d["0"].flatten().filter(lambda i: i.extra.get('highway', None) not in ('path', 'track', 'footway', None))
            ways_2d_0 = self.osm.ways_2d["0"]
            union = ddd.group([ways_2d_0, self.osm.ways_2d['-1a'], areas_2d]).union()
        except TopologicalError as e:
            logger.error("Error calculating interways: %s", e)
            l0 = ways_2d_0.union()
            lm1a = self.osm.ways_2d['-1a'].union()
            #l0a = self.osm.ways_2d['0a'].union()  # shall be trimmed  # added to avoid height conflicts but leaves holes
            c = areas_2d.clean(eps=0.01).union()
            try:
                union = ddd.group2([c, l0, lm1a])
                #union = union.buffer(eps, 1, join_style=ddd.JOIN_MITRE).buffer(-eps, 1, join_style=ddd.JOIN_MITRE)
                union = union.clean(eps=0.01)
                union = union.union()
            except TopologicalError as e:
                logger.error("Error calculating interways (2): %s", e)
                union = ddd.group2()
                #union = ddd.group([self.osm.ways_2d['0'], self.osm.ways_2d['-1a'], areas_2d]).union()

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
                    area = area.clean(eps=0.01)
                    area = area.material(ddd.mats.pavement)
                    area.extra['ddd:area:type'] = 'sidewalk'
                    self.osm.areas_2d.children.append(area)
                else:
                    logger.warn("Invalid interways area.")

    '''
    def generate_areas_ways_relations(self):
        logger.info("Areas - Ways relations (%d areas, %d ways['0']).", len(self.osm.areas_2d.children), len(self.osm.ways_2d['0'].children))
        for area in self.osm.areas_2d.children:
            if area.extra.get('ddd:area:type', None) != 'sidewalk': continue
    '''

    def generate_areas_2d_postprocess(self):

        logger.info("Postprocessing areas and ways (%d areas, %d ways['0']).", len(self.osm.areas_2d.children), len(self.osm.ways_2d['0'].children))

        #
        areas_2d_original = ddd.group2()
        for a in self.osm.areas_2d.children:
            if a.extra.get('ddd:area:original', None):
                if a.extra.get('ddd:area:original') not in areas_2d_original.children:
                    areas_2d_original.append(a.extra.get('ddd:area:original'))

        # Remove paths from some areas (sidewalks), and reincorporate to them
        #to_remove = []
        for way_2d in self.osm.ways_2d['0'].children:
            if way_2d.extra.get('osm:highway', None) not in ('footway', 'path', 'track', None): continue
            if way_2d.extra.get('ddd:area:type', None) == 'water': continue

            for area in areas_2d_original.children:  #self.osm.areas_2d.children:  # self.osm.areas_2d.children:

                #area_original = area.extra.get('ddd:area:original', None)
                #if area_original is None: continue

                area_original = area

                #if area.extra.get('ddd:area:type', None) != 'sidewalk': continue

                intersects = False
                try:
                    intersects = area_original.intersects(way_2d)
                except Exception as e:
                    logger.error("Could not calculate intersections between way and area: %s %s", way_2d, area)
                    raise DDDException("Could not calculate intersections between way and area: %s %s" % (way_2d, area))

                if intersects:
                    logger.debug("Path %s intersects area: %s (subtracting and arranging)", way_2d, area)
                    way_2d.extra['ddd:area:container'] = area_original
                    #to_remove.append(area

                    intersection = way_2d.intersection(area_original)
                    remainder = way_2d.subtract(area_original)

                    way_2d.replace(intersection)  # way_2d.subtract(intersection))

                    remainder = remainder.material(ddd.mats.pavement)
                    area.extra['ddd:area:type'] = 'sidewalk'
                    remainder.name = "Path to interways: %s" % way_2d.name
                    remainder.clean(eps=0.001)
                    self.osm.areas_2d.append(remainder)
                    #area = area.union().clean(eps=0.001)

        #self.osm.areas_2d.children = [c for c in self.osm.areas_2d.children if c not in to_remove]

    def generate_areas_2d_postprocess_water(self):
        logger.info("Postprocessing water areas and ways")

        # Get all water areas ('ddd:water')
        water_areas = self.osm.areas_2d.select(ddd.sel.extra('ddd:area:type', 'water'))

        river_areas = self.osm.ways_2d["0"].select(ddd.sel.extra('ddd:area:type', 'water'))
        self.osm.ways_2d["0"].children = [c for c in self.osm.ways_2d["0"].children if c not in river_areas.children]

        all_water_areas = ddd.group2(water_areas.children + river_areas.children)

        # Move river areas to areas
        self.osm.areas_2d.children.extend(river_areas.children)

        # Create ground area
        underwater_area = all_water_areas.union().material(ddd.mats.terrain)
        underwater_area.extra['ddd:area:type'] = 'underwater'
        #underwater_area = underwater_area.individualize()
        #underwater_area.show()
        self.osm.areas_2d.append(underwater_area)


    def generate_coastline_3d(self, area_crop):

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
    def generate_ground_3d_old(self, area_crop):

        logger.info("Generating terrain (bounds: %s)", area_crop.bounds)

        #terr = terrain.terrain_grid(distance=500.0, height=1.0, detail=25.0).translate([0, 0, -0.5]).material(mat_terrain)
        terr = terrain.terrain_geotiff(area_crop.bounds, detail=10.0, ddd_proj=self.osm.ddd_proj).material(ddd.mats.terrain)
        #terr2 = terrain.terrain_grid(distance=60.0, height=10.0, detail=5).translate([0, 0, -20]).material(mat_terrain)

        self.osm.ground_3d = terr
    '''

    def generate_ground_3d(self, area_crop):

        logger.info("Generating terrain (bounds: %s)", area_crop.bounds)

        #terr = terrain.terrain_grid(distance=500.0, height=1.0, detail=25.0).translate([0, 0, -0.5]).material(mat_terrain)
        #terr = terrain.terrain_geotiff(area_crop.bounds, detail=10.0, ddd_proj=self.osm.ddd_proj).material(mat_terrain)
        #terr2 = terrain.terrain_grid(distance=60.0, height=10.0, detail=5).translate([0, 0, -20]).material(mat_terrain)
        #terr = ddd.grid2(area_crop.bounds, detail=10.0).buffer(0.0)  # useless, shapely does not keep triangles when operating
        terr = ddd.rect(area_crop.bounds, name="Ground")

        terr = terr.subtract(self.osm.ways_2d['0'].clean(eps=0.01))
        terr = terr.clean(eps=0.01)

        terr = terr.subtract(self.osm.ways_2d['-1a'].clean(eps=0.01))
        terr = terr.clean(eps=0.01)

        #terr = terr.subtract(self.osm.ways_2d['0a'])  # added to avoid floor, but shall be done better, by layers spawn and base_height,e tc
        #terr = terr.clean(eps=0.01)

        try:
            terr = terr.subtract(self.osm.areas_2d.clean(eps=0.01))
            terr = terr.clean(eps=0.01)
        except Exception as e:
            logger.error("Could not subtract areas_2d from terrain.")
            return

        terr = terr.subtract(self.osm.water_2d)
        terr = terr.clean(eps=0.01)
        terr = terr.material(ddd.mats.terrain)

        self.osm.ground_2d.append(terr)

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

    def generate_areas_3d(self):
        logger.info("Generating 3D areas (%d)", len(self.osm.areas_2d.children))
        for area_2d in self.osm.areas_2d.children:
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
                    self.osm.areas_3d.children.append(area_3d)
            except ValueError as e:
                logger.error("Could not generate area %s: %s", area_2d, e)
                raise
            except IndexError as e:
                logger.error("Could not generate area %s: %s", area_2d, e)
                raise
            except DDDException as e:
                logger.error("Could not generate area %s: %s", area_2d, e)
                raise

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
                    grass_layers = ddd.group3()
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
                    self.osm.other_3d.append(grass_layers)  #ddd.group3([area_3d, grass_layers])


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
