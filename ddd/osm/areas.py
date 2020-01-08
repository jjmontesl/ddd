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
        
        union = ddd.group([self.osm.ways_2d['0'], self.osm.ways_2d['-1a'], self.osm.areas_2d]).union()
        
        #union = union.buffer(0.5)
        #union = union.buffer(-0.5)
        for c in union.geom:
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

    def generate_ground_3d(self, area_crop):
        
        logger.info("Generating terrain (bounds: %s)", area_crop.bounds)
        
        #terr = terrain.terrain_grid(distance=500.0, height=1.0, detail=25.0).translate([0, 0, -0.5]).material(mat_terrain)
        #terr = terrain.terrain_geotiff(area_crop.bounds, detail=10.0, ddd_proj=self.osm.ddd_proj).material(mat_terrain)
        #terr2 = terrain.terrain_grid(distance=60.0, height=10.0, detail=5).translate([0, 0, -20]).material(mat_terrain)
        terr = ddd.rect(area_crop.bounds, name="Ground")
        terr = terr.subtract(self.osm.ways_2d['0'])
        terr = terr.subtract(self.osm.ways_2d['-1a'])
        terr = terr.subtract(self.osm.areas_2d)
        #terr.save("/tmp/test.svg")
        #terr = terr.triangulate()
        terr = terr.extrude(0.3)
        terr = terrain.terrain_geotiff_elevation_apply(terr, self.osm.ddd_proj)
        terr = terr.material(self.osm.mat_terrain)
        
        self.osm.ground_3d = terr

    def generate_ground_3d_old(self, area_crop):
        
        logger.info("Generating terrain (bounds: %s)", area_crop.bounds)
        
        #terr = terrain.terrain_grid(distance=500.0, height=1.0, detail=25.0).translate([0, 0, -0.5]).material(mat_terrain)
        terr = terrain.terrain_geotiff(area_crop.bounds, detail=10.0, ddd_proj=self.osm.ddd_proj).material(self.osm.mat_terrain)
        #terr2 = terrain.terrain_grid(distance=60.0, height=10.0, detail=5).translate([0, 0, -20]).material(mat_terrain)
        
        self.osm.ground_3d = terr 

    def generate_coastline_3d(self, area_crop):
        
        logger.info("Generating water and land areas according to coastline.")
        
        #self.water_3d = terrain.terrain_grid(self.area_crop.bounds, height=0.1, detail=200.0).translate([0, 0, 1]).material(mat_sea)
        
        water = ddd.rect(area_crop.bounds, name="Ground")
        coastlines = []
        for way in self.osm.ways_1d.children:
            if way.extra['feature']['properties'].get('natural', None) == 'coastline':
                coastlines.append(way.buffer(0.1))
        
        if not coastlines:
            return
        
        coastlines = ddd.group(coastlines).union()
        
        coastline_areas = water.subtract(coastlines)
        #coastline_areas.save("/tmp/test.svg")
        #coastline_areas.dump()
        
        areas = []
        for geom in coastline_areas.geom.geoms:
            # Find closest point, closest segment, and angle to closest segment
            if random.uniform(0, 1) < 0.5: continue
            area = ddd.shape(geom).extrude(0.2).material(self.osm.mat_sea)
            areas.append(area)
        areas = ddd.group(areas)
        self.osm.water_3d = areas
            
        
    
