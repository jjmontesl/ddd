# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging
import math
import random
import sys

from ddd.ddd import DDDObject2, DDDObject3
from ddd.ddd import ddd
from ddd.pack.sketchy import plants, urban
from ddd.geo import terrain
from ddd.core.exception import DDDException


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
                self.osm.buildings_2d.append(building_2d)

    def generate_building_2d(self, feature):
        building_2d = ddd.shape(feature["geometry"], name="Building (%s)" % (feature['properties'].get("name", None)))

        try:
            building_2d.validate()
        except DDDException as e:
            logger.warn("Invalid geometry for building: %s", e)
            return None

        building_2d.extra['osm:feature'] = feature
        building_2d.extra['building'] = feature['properties'].get('building', None)
        building_2d.extra['amenities'] = []

        # Generate info: segment_facing_way + sidewalk, pricipal facade, secondary (if any) facades, portal entry...

        # Augment building (roof type, facade type, portals ?)

        if building_2d.extra['building'] == 'church':
            building_2d = self.generate_building_2d_church(building_2d)

        return building_2d

    def generate_building_2d_church(self, building_2d):

        # Add cross to principal and secondary facades if all building is church

        return building_2d

    def generate_buildings_3d(self):
        logger.info("Generating 3D buildings (%d)", len(self.osm.buildings_2d.children))

        buildings = []
        for building_2d in self.osm.buildings_2d.children:

            if building_2d.extra['building'] == 'church':
                building_3d = self.generate_building_3d_church(building_2d)
            else:
                building_3d = self.generate_building_3d_basic(building_2d)

            if building_3d:
                self.osm.buildings_3d.append(building_3d)

    def generate_building_3d_basic(self, building_2d):

        feature = building_2d.extra['osm:feature']

        floors = feature.properties.get('building:levels', None)
        if not floors:
            floors = random.randint(2, 8)
        floors = int(floors)

        if floors == 0:
            logger.error("Building with 0 floors (setting to 1): %s", floors)
            floors = 1

        building_3d = None
        try:

            # Generate building procedurally (use library)
            building_3d = building_2d.extrude(floors * 3.00)
            building_3d = building_3d.material(random.choice([ddd.mats.building_1, ddd.mats.building_2, ddd.mats.building_3]))
            if random.uniform(0, 1) < 0.2:
                base = building_2d.buffer(0.3, cap_style=2, join_style=2).extrude(1.00)
                base = base.material(random.choice([ddd.mats.building_1, ddd.mats.building_2, ddd.mats.building_3, ddd.mats.roof_tiles]))
                building_3d.children.append(base)
            if random.uniform(0, 1) < 0.4:
                roof = None
                roof_type = random.choice([1, 2, 3])
                roof_buffer = random.uniform(0.5, 1.5) if random.uniform(0, 1) < 0.5 else 0.0
                if roof_type == 1:
                    # Flat
                    roof = building_2d.buffer(roof_buffer, cap_style=2, join_style=2).extrude(0.75).translate([0, 0, floors * 3.00]).material(ddd.mats.roof_tiles)
                elif roof_type == 2:
                    # Pointy
                    height = floors * 0.2 + random.uniform(2.0, 5.0)
                    try:
                        roof = building_2d.buffer(roof_buffer, cap_style=2, join_style=2).extrude_step(building_2d.buffer(-10), height).translate([0, 0, floors * 3.00]).material(ddd.mats.roof_tiles)
                    except DDDException as e:
                        logger.debug("Could not generate roof: %s", e)
                elif roof_type == 3:
                    # Attic
                    height = random.uniform(3.0, 4.0)
                    try:
                        roof = building_2d.buffer(roof_buffer, cap_style=2, join_style=2).extrude_step(building_2d.buffer(-2), height).translate([0, 0, floors * 3.00]).material(ddd.mats.roof_tiles)
                    except DDDException as e:
                        logger.debug("Could not generate roof: %s", e)

                if roof: building_3d.children.append(roof)

        except ValueError as e:
            logger.warning("Cannot generate building: %s (geom: %s)" % (e, building_2d.geom))
            return None

        # UV Mapping
        building_3d = ddd.uv.map_cubic(building_3d)

        building_3d.extra['building_2d'] = building_2d
        building_3d = terrain.terrain_geotiff_min_elevation_apply(building_3d, self.osm.ddd_proj)
        building_3d = building_3d.translate([0, 0, -0.20])  # temporary hack floor snapping

        self.generate_building_3d_amenities(building_3d)

        return building_3d

    def generate_building_3d_church(self, building_2d):

        building_3d = self.generate_building_3d_basic(building_2d)
        return building_3d

    def link_features_2d(self):

        logger.info("Linking features to buildings.")

        for feature in self.osm.features:
            if feature['geometry']['type'] != "Point": continue
            # Find closest building
            point = ddd.shape(feature['geometry'], name="Point: %s" % (feature['properties'].get('name', None)))
            point.extra['osm:feature'] = feature
            point.extra['amenity'] = feature['properties'].get('amenity', None)
            point.extra['shop'] = feature['properties'].get('shop', None)
            point.extra['name'] = feature['properties'].get('name', None)

            building, distance = self.closest_building(point)
            if not building:
                continue

            point.extra['osm:building'] = building

            if point.extra['amenity'] or point.extra['shop']:
                #logger.debug("Point: %s  Building: %s  Distance: %s", point, building, distance)

                # TODO: Do the opposite, create items we are interested in
                if point.extra['amenity'] in ('waste_disposal', 'waste_basket',
                                              'recycling', 'bicycle_parking'):
                    continue

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

    def snap_to_building(self, item_3d, building_3d):

        # Find building segment to snap
        amenity = item_3d.extra['amenity']
        building_2d = building_3d.extra['building_2d']

        if building_2d.geom.type == "MultiPolygon":
            logger.warn("Cannot snap to MultiPolygon building (ignoring item_3d)  TODO: usecommon snap functions which should support MultiPolygon")
            return None

        line = building_2d.geom.exterior
        closest_distance_to_closest_point_in_exterior = line.project(amenity.geom.centroid)
        #closest_point, closest_segment = self.closest_building_2d_segment(amenity, building_2d)
        #closest_point = line.interpolate(closest_distance_to_closest_point_in_exterior)
        closest_point, segment_idx, segment_coords_a, segment_coords_b = DDDObject2(geom=line).interpolate_segment(closest_distance_to_closest_point_in_exterior)

        dir_ver = (segment_coords_b[0] - segment_coords_a[0], segment_coords_b[1] - segment_coords_a[1])
        dir_ver_length = math.sqrt(dir_ver[0] ** 2 + dir_ver[1] ** 2)
        dir_ver = (dir_ver[0] / dir_ver_length, dir_ver[1] / dir_ver_length)
        angle = math.atan2(dir_ver[1], dir_ver[0])

        #if not building_2d.geom.contains(amenity.geom):
        #    angle = -angle

        #if not building_2d.geom.exterior.is_ccw:
        #    angle = -angle
        #logger.debug("Amenity: %s Closest point: %s Closest Segment: %s Angle: %s" % (amenity.geom.centroid, closest_point, closest_segment, angle))

        # Align rotation
        item_3d = item_3d.rotate([0, 0, angle])  # + math.pi / 2.0
        item_3d = item_3d.translate([closest_point[0], closest_point[1], 0])

        return item_3d

    def generate_building_3d_amenities(self, building_3d):

        for item_1d in building_3d.extra['amenities']:

            if item_1d.extra['amenity'] == 'pharmacy':

                coords = item_1d.geom.centroid.coords[0]

                # Side sign
                item = urban.sign_pharmacy_side(size=1.0)
                '''
                # Plain sign (front view on facade)
                item = urban.sign_pharmacy(size=1.2)
                item = item.translate([0, -0.25, 2.0])  # no post
                '''
                item.extra['amenity'] = item_1d
                item = self.snap_to_building(item, building_3d)
                item = item.translate([0, 0, 3.0])  # no post
                item = terrain.terrain_geotiff_min_elevation_apply(item, self.osm.ddd_proj)
                building_3d.children.append(item)

            elif item_1d.extra['amenity'] and item_1d.extra['amenity'] not in ('fountain', 'taxi', 'post_box', 'bench', 'toilets', 'parking_entrance'):
                # Except parking?

                #coords = amenity.geom.centroid.coords[0]
                #panel_text = amenity.extra['amenity'] if amenity.extra['amenity'] else None
                panel_text = item_1d.extra['name'] if item_1d.extra['name'] else (item_1d.extra['amenity'].upper() if item_1d.extra['amenity'] else None)
                item = urban.panel(width=3.2, height=0.9, text=panel_text)
                item.extra['amenity'] = item_1d
                item.extra['text'] = panel_text
                item.name = "Panel: %s %s" % (item_1d.extra['amenity'], item_1d.extra['name'])
                item = self.snap_to_building(item, building_3d)
                if item:
                    item = item.translate([0, 0, 3.2])  # no post
                    color = random.choice(["#d41b8d", "#a7d42a", "#e2de9f", "#9f80e2"])
                    item = terrain.terrain_geotiff_min_elevation_apply(item, self.osm.ddd_proj)
                    building_3d.children.append(item)
                else:
                    logger.info("Could not snap item to building (skipping item): %s", item)
                #building_3d.show()

            elif item_1d.extra['shop']:
                #coords = item_1d.geom.centroid.coords[0]
                panel_text = ((item_1d.extra['name']) if item_1d.extra['name'] else item_1d.extra['shop'])
                item = urban.panel(width=2.5, height=0.8, text=panel_text)
                item.extra['amenity'] = item_1d
                item.extra['text'] = panel_text
                item.name = "Panel: %s %s" % (item_1d.extra['shop'], item_1d.extra['name'])
                item = self.snap_to_building(item, building_3d)
                if item:
                    item = item.translate([0, 0, 2.8])  # no post
                    color = random.choice(["#c41a7d", "#97c41a", "#f2ee0f", "#0f90f2"])
                    item = item.material(ddd.material(color=color))
                    item = terrain.terrain_geotiff_min_elevation_apply(item, self.osm.ddd_proj)
                    building_3d.children.append(item)
                else:
                    logger.info("Could not snap item to building (skipping item): %s", item)

            else:
                logger.debug("Unknown building-related item (%s): %s", item_1d.extra['amenity'], item_1d)



