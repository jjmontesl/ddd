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

class Areas2DOSMBuilder():

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


    def generate_coastline_2d(self, area_crop):
        logger.info("Generating water and land areas according to coastline: %s", (area_crop.bounds))

        #self.water_3d = terrain.terrain_grid(self.area_crop.bounds, height=0.1, detail=200.0).translate([0, 0, 1]).material(mat_sea)

        water = ddd.rect(area_crop.bounds, name="Coastline Water")

        coastlines = []
        coastlines_1d = []

        for way in self.osm.features_2d.children:
            if way.extra.get('osm:natural') == 'coastline':
                coastlines_1d.append(way)
                coastlines.append(way.buffer(0.01))

        #for way in self.osm.features.children:
        #    if way.properties.get('natural') == 'coastline':
        #        coastlines_1d.append(ddd.shape(way.geometry))
        #        coastlines.append(ddd.shape(way.geometry).buffer(0.1))

        if not coastlines:
            logger.info("No coastlines in the feature set.")
            return

        coastlines_1d = ddd.group(coastlines_1d).individualize().flatten()
        coastlines = ddd.group(coastlines)  # .individualize().flatten()
        coastline_areas = water.subtract(coastlines)

        logger.info("Coastlines: %s", (coastlines_1d, ))
        logger.info("Coastline areas: %s", (coastline_areas, ))

        #coastline_areas.show()
        #coastline_areas.save("/tmp/test.svg")
        #coastline_areas.dump()

        # Generate coastline edge
        if coastlines_1d.children:
            coastlines_2d = coastlines_1d.intersection(water)
            coastlines_2d = coastlines_2d.individualize()
            #coastlines_3d = coastlines_2d.extrude(10.0).translate([0, 0, -10.0])
            #coastlines_3d = terrain.terrain_geotiff_elevation_apply(coastlines_3d, self.osm.ddd_proj)
            #coastlines_3d = ddd.uv.map_cubic(coastlines_3d)
            #coastlines_3d.name = 'Coastline: %s' % coastlines_3d.name
            #self.osm.other_3d.append(coastlines_3d)


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
            pol = LinearRing([segment_coords_a, segment_coords_b, (water_area_point.coords[0][0], water_area_point.coords[0][1], 0)])

            if not pol.is_ccw:
                #area_3d = area_2d.extrude(-0.2)
                area_2d = ddd.shape(water_area_geom).buffer(0.10).clean(eps=0.01)
                area_2d.validate()
                area_2d = area_2d.material(ddd.mats.sea)
                area_2d.extra['ddd:collider'] = False
                area_2d.extra['ddd:shadows'] = False
                area_2d.extra['ddd:occluder'] = False

                #area_3d = area_2d.triangulate().translate([0, 0, -0.5])
                areas_2d.append(area_2d)
                #areas.append(area_3d)

        self.osm.water_2d = ddd.group(areas_2d)


        #if areas:
        #    self.osm.water_3d = ddd.group(areas)
        #else:
        #    logger.debug("No water areas from coastline generated.")

