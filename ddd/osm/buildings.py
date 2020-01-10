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


class BuildingOSMBuilder():

    def __init__(self, osmbuilder):

        self.osm = osmbuilder

    def generate_buildings_2d(self):

        logger.info("Generating buildings (2D)")

        buildings = []
        for feature in self.osm.features:
            building = feature['properties'].get('building', None)
            if building is None: continue
            if feature['geometry']['type'] == 'Point': continue
            building_2d = self.generate_building_2d(feature)

            if building_2d:
                buildings.append(building_2d)

        self.osm.buildings_2d = ddd.group(buildings, name="Buildings")  #translate([0, 0, 50])

    def generate_building_2d(self, feature):
        building_2d = ddd.shape(feature["geometry"], name="Building (%s)" % (feature['properties'].get("name", None)))
        building_2d.extra['building'] = feature['properties'].get('building', None)
        building_2d.extra['feature'] = feature
        building_2d.extra['amenities'] = []
        return building_2d

    def generate_buildings_3d(self):
        logger.info("Generating 3D buildings (%d)", len(self.osm.buildings_2d.children))

        buildings = []
        for building_2d in self.osm.buildings_2d.children:
            building_3d = self.generate_building_3d(building_2d)
            if building_3d:
                buildings.append(building_3d)

        self.osm.buildings_3d = ddd.group(buildings)

    def generate_building_3d(self, building_2d):

        feature = building_2d.extra['feature']

        floors = feature.properties.get('building:levels', None)
        if not floors:
            floors = random.randint(2, 8)
        floors = int(floors)

        building_3d = None
        try:

            # Generate building procedurally (use library)
            building_3d = building_2d.extrude(floors * 3.00)
            building_3d = building_3d.material(random.choice([self.osm.mat_building_1, self.osm.mat_building_2, self.osm.mat_building_3]))
            if random.uniform(0, 1) < 0.2:
                base = building_2d.buffer(0.3, cap_style=2, join_style=2).extrude(1.00)
                base = base.material(random.choice([self.osm.mat_building_1, self.osm.mat_building_2, self.osm.mat_building_3, self.osm.mat_roof_tile]))
                building_3d.children.append(base)
            if random.uniform(0, 1) < 0.4:
                roof = building_2d.buffer(random.uniform(0.5, 1.5), cap_style=2, join_style=2).extrude(0.75).translate([0, 0, floors * 3.00]).material(self.osm.mat_roof_tile)
                building_3d.children.append(roof)

        except ValueError as e:
            logger.warning("Cannot generate building: %s (geom: %s)" % (e, building_2d.geom))
            return None

        building_3d.extra['building_2d'] = building_2d

        self.generate_building_3d_amenities(building_3d)

        building_3d = terrain.terrain_geotiff_elevation_apply(building_3d, self.osm.ddd_proj)
        building_3d = building_3d.translate([0, 0, -0.20])  # temporary fix snapping

        return building_3d

    def link_features_2d(self):

        logger.info("Linking features to buildings.")

        for feature in self.osm.features:
            if feature['geometry']['type'] != "Point": continue
            # Find closest building
            point = ddd.shape(feature['geometry'], name="Point: %s" % (feature['properties'].get('name', None)))
            point.extra['amenity'] = feature['properties'].get('amenity', None)
            point.extra['name'] = feature['properties'].get('name', None)

            building, distance = self.closest_building(point)
            #logger.debug("Point: %s  Building: %s  Distance: %s", point, building, distance)

            if point.extra['amenity']:
                building.extra['amenities'].append(point)
                #logger.debug("Amenity: %s" % point)

    def closest_building(self, point):
        closest_building = None
        closest_distance = math.inf
        for building in self.osm.buildings_2d.children:
            distance = point.distance(building)
            if distance < closest_distance:
                closest_building = building
                closest_distance = distance
        return closest_building, closest_distance

    def closest_building_2d_segment(self, item, building_2d):

        line = building_2d.geom.exterior
        closest_distance_to_closest_point_in_exterior = line.project(item.geom.centroid)
        closest_point = line.interpolate(closest_distance_to_closest_point_in_exterior)

        closest_segment = None
        for s1, s2 in zip(line.coords[:], line.coords[1:] + line.coords[:1]):
            segment = LineString([s1, s2])
            if segment.contains(closest_point):
                closest_segment = segment

        return closest_point, closest_segment

    def snap_to_building(self, item_3d, building_3d):

        # Find building segment to snap
        amenity = item_3d.extra['amenity']
        building_2d = building_3d.extra['building_2d']

        closest_point, closest_segment = self.closest_building_2d_segment(amenity, building_2d)
        vector = LineString([amenity.geom.centroid.coords[0], closest_point])
        angle = math.atan2(vector.coords[1][1] - vector.coords[0][1],
                           vector.coords[1][0] - vector.coords[0][0])
        if not building_2d.geom.contains(amenity.geom):
            angle = -angle
        #if not building_2d.geom.exterior.is_ccw:
        #    angle = -angle
        #logger.debug("Amenity: %s Closest point: %s Closest Segment: %s Angle: %s" % (amenity.geom.centroid, closest_point, closest_segment, angle))

        # Align rotation
        item_3d = item_3d.rotate([0, 0, angle + math.pi / 2.0])
        item_3d = item_3d.translate([closest_point.coords[0][0], closest_point.coords[0][1], 0])

        return item_3d

    def generate_building_3d_amenities(self, building_3d):

        for amenity in building_3d.extra['amenities']:

            if amenity.extra['amenity'] == 'pharmacy':

                coords = amenity.geom.centroid.coords[0]

                # Side sign
                item = urban.sign_pharmacy_side(size=1.0)
                '''
                # Plain sign (front view on facade)
                item = urban.sign_pharmacy(size=1.2)
                item = item.translate([0, -0.25, 2.0])  # no post
                '''
                item.extra['amenity'] = amenity
                item = self.snap_to_building(item, building_3d)
                item = item.translate([0, 0, 3.0])  # no post
                building_3d.children.append(item)

            else:
                logger.warn("Unknown amenity (%s): %s", amenity.extra['amenity'], amenity)



