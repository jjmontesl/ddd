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
from ddd.util.dddrandom import weighted_choice


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class BuildingOSMBuilder():

    def __init__(self, osmbuilder):

        self.osm = osmbuilder

    def preprocess_buildings_2d(self):

        logger.info("Preprocessing buildings and bulding parts (2D)")

        # Assign each building part to a building, or transform it into a building if needed
        for feature in list(self.osm.features_2d.children):
            if feature.geom.type == 'Point': continue
            if feature.extra.get('osm:building:part', None) is None: continue

            # Find building
            buildings = self.osm.features_2d.select(lambda o: o.extra.get('osm:building', None) and o.contains(feature))
            if len(buildings.children) == 0:
                logger.warn("Building part with no building: %s", feature)
                building = feature.copy()
                building.extra['osm:building'] = feature.extra.get('osm:building:part', 'yes')
                building.extra['ddd:building:parts'] = [feature]
                self.osm.features_2d.append(building)
                feature.extra['ddd:building:feature'] = building

            elif len(buildings.children) > 1:
                logger.warn("Building part with multiple buildings: %s -> %s", feature, buildings.children)

            else:
                #logger.debug("Associating building part to building: %s -> %s", feature, buildings.children[0])
                feature.extra['ddd:building:feature'] = buildings.children[0]
                if 'ddd:building:parts' not in buildings.children[0].extra:
                    buildings.children[0].extra['ddd:building:parts'] = []
                buildings.children[0].extra['ddd:building:parts'].append(feature)

    def generate_buildings_2d(self):

        logger.info("Generating buildings (2D)")

        for feature in self.osm.features_2d.children:
            if feature.geom.type == 'Point': continue

            building_2d = None

            if feature.extra.get('osm:building', None) is not None:
                building_2d = self.generate_building_2d(feature)
            #if feature.extra.get('osm:building:part', None) is not None:
            #    building_2d = self.generate_building_2d(feature)

            if building_2d:
                self.osm.buildings_2d.append(building_2d)

        #self.osm.buildings_2d.show()

    def generate_building_2d(self, feature):
        building_2d = feature.copy(name="Building (%s)" % (feature.extra.get("name", None)))

        '''
        try:
            building_2d.validate()
        except DDDException as e:
            logger.warn("Invalid geometry for building: %s", e)
            return None
        '''

        building_2d.extra['ddd:building:items'] = []
        if 'ddd:building:parts' not in building_2d.extra:
            building_2d.extra['ddd:building:parts'] = []

        # Generate info: segment_facing_way + sidewalk, pricipal facade, secondary (if any) facades, portal entry...

        # Augment building (roof type, facade type, portals ?)


        return building_2d

    def link_features_2d(self):

        logger.info("Linking features to buildings.")
        logger.warn("SHOULD LINK FEATURES TO BUILDING PARTS.")

        for feature in self.osm.features_2d.children:
            if feature.geom.type != "Point": continue
            # Find closest building
            point = feature.copy(name="Point: %s" % (feature.extra.get('name', None)))
            building, distance = self.closest_building(point)
            if not building:
                continue

            point.extra['osm:building'] = building

            if point.extra.get('osm:amenity', None) or point.extra.get('osm:shop', None):
                #logger.debug("Point: %s  Building: %s  Distance: %s", point, building, distance)

                # TODO: Do the opposite, create items we are interested in
                if point.extra.get('osm:amenity', None) in ('waste_disposal', 'waste_basket',
                                                            'recycling', 'bicycle_parking'):
                    continue

                building.extra['ddd:building:items'].append(point)
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

    def generate_buildings_3d(self):
        logger.info("Generating 3D buildings (%d)", len(self.osm.buildings_2d.children))

        for building_2d in self.osm.buildings_2d.children:
            building_3d = self.generate_building_3d_generic(building_2d)
            if building_3d:
                self.osm.buildings_3d.append(building_3d)

    def generate_building_3d_generic(self, building_2d):
        """
        Buildings 2D may contain references to building parts.

        TODO: Do a lot more in tags in 2D and here, and generalize tasks to pipelines and tags.
        """

        floors = building_2d.extra.get('osm:building:levels', None)
        if not floors:
            floors = random.randint(2, 8)
        floors = int(floors)
        base_floors = floors

        material = random.choice([ddd.mats.building_1, ddd.mats.building_2, ddd.mats.building_3])

        entire_building_2d = ddd.group2()
        entire_building_3d = building_2d.copy3(name="Building: %s" % (building_2d.name))

        roof_type = weighted_choice({'none': 2,
                                     'flat': 1,
                                     'pointy': 0.5,
                                     'attic': 0.5,
                                     'terrace': 1})
        roof_buffered = weighted_choice({True: 1, False: 5})
        roof_buffer = random.uniform(0.5, 1.2)
        roof_wall_material = weighted_choice({"stone": 3, "bricks": 1})

        for part in (building_2d.extra['ddd:building:parts'] + [building_2d]):

            building_3d = None
            try:

                floors = int(part.extra.get('osm:building:levels', base_floors))
                if floors == 0:
                    logger.warn("Building part with 0 floors (setting to 1): %s", floors)
                    floors = 1

                # Remove building so far
                part = part.subtract(entire_building_2d)
                if part.geom.is_empty:
                    continue

                # Generate building procedurally (use library)
                building_3d = part.extrude(floors * 3.00)
                building_3d = building_3d.material(material)

                pbuffered = roof_buffered
                ptype = roof_type
                if floors < 2:
                    ptype = 'none'
                if floors < base_floors:
                    pbuffered = False
                    if (random.uniform(0, 1) < 0.5): ptype = random.choice(['terrace', 'none'])
                    if (floors <= 2):
                        if (random.uniform(0, 1) < 0.8): ptype = random.choice(['terrace', 'terrace', 'terrace', 'none'])

                # Base
                if random.uniform(0, 1) < 0.2:
                    base = part.buffer(0.3, cap_style=2, join_style=2).extrude(1.00)
                    base = base.material(random.choice([ddd.mats.building_1, ddd.mats.building_2, ddd.mats.building_3, ddd.mats.roof_tiles]))
                    building_3d.children.append(base)

                # Roof
                try:
                    roof = None
                    if ptype == 'flat':
                        # Flat
                        roof = part.buffer(roof_buffer if pbuffered else 0, cap_style=2, join_style=2).extrude(0.75).translate([0, 0, floors * 3.00]).material(ddd.mats.roof_tiles)
                    if ptype == 'terrace':
                        # Flat
                        usefence = random.uniform(0, 1) < 0.8
                        if usefence:
                            terrace = part.subtract(part.buffer(-0.4)).extrude(0.6).translate([0, 0, floors * 3.00]).material(getattr(ddd.mats, roof_wall_material))
                            fence = part.buffer(-0.2).outline().extrude(0.7).twosided().translate([0, 0, floors * 3.00 + 0.6]).material(ddd.mats.railing)
                            roof = ddd.group3([terrace, fence], name="Roof")
                        else:
                            terrace = part.subtract(part.buffer(-0.4)).extrude(random.uniform(0.40, 1.20)).translate([0, 0, floors * 3.00]).material(ddd.mats.stone)
                            roof = ddd.group3([terrace], name="Roof")

                    elif ptype == 'pointy':
                        # Pointy
                        height = floors * 0.2 + random.uniform(2.0, 5.0)
                        try:
                            roof = part.buffer(roof_buffer if pbuffered else 0, cap_style=2, join_style=2).extrude_step(part.buffer(-10), height).translate([0, 0, floors * 3.00]).material(ddd.mats.roof_tiles)
                        except DDDException as e:
                            logger.debug("Could not generate roof: %s", e)
                    elif ptype == 'attic':
                        # Attic
                        height = random.uniform(3.0, 4.0)
                        try:
                            roof = part.buffer(roof_buffer if pbuffered else 0, cap_style=2, join_style=2).extrude_step(part.buffer(-2), height).translate([0, 0, floors * 3.00]).material(ddd.mats.roof_tiles)
                        except DDDException as e:
                            logger.debug("Could not generate roof: %s", e)

                    if roof: building_3d.children.append(roof)
                except Exception as e:
                    logger.warning("Cannot generate roof: %s (geom: %s)" % (e, part.geom))

                # UV Mapping
                building_3d = ddd.uv.map_cubic(building_3d)

                entire_building_2d.append(part)
                entire_building_3d.append(building_3d)

            except ValueError as e:
                logger.warning("Cannot generate building: %s (geom: %s)" % (e, part.geom))
                return None

        entire_building_3d = terrain.terrain_geotiff_min_elevation_apply(entire_building_3d, self.osm.ddd_proj)
        entire_building_3d = entire_building_3d.translate([0, 0, -0.20])  # temporary hack floor snapping
        entire_building_3d.extra['building_2d'] = building_2d

        self.generate_building_3d_amenities(entire_building_3d)

        return entire_building_3d

    def snap_to_building(self, item_3d, building_3d):

        # Find building segment to snap
        item_1d = item_3d.extra.get('ddd:item', None)
        building_2d = building_3d.extra['building_2d']

        if building_2d.geom.type == "MultiPolygon":
            logger.warn("Cannot snap to MultiPolygon building (ignoring item_3d)  TODO: usecommon snap functions which should support MultiPolygon")
            return None

        line = building_2d.geom.exterior
        closest_distance_to_closest_point_in_exterior = line.project(item_1d.geom.centroid)
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

        for item_1d in building_3d.extra['ddd:building:items']:

            if item_1d.extra.get('osm:amenity', None) == 'pharmacy':

                coords = item_1d.geom.centroid.coords[0]

                # Side sign
                item = urban.sign_pharmacy_side(size=1.0)
                '''
                # Plain sign (front view on facade)
                item = urban.sign_pharmacy(size=1.2)
                item = item.translate([0, -0.25, 2.0])  # no post
                '''
                item.extra['ddd:item'] = item_1d
                item = self.snap_to_building(item, building_3d)
                item = item.translate([0, 0, 3.0])  # no post
                item = terrain.terrain_geotiff_min_elevation_apply(item, self.osm.ddd_proj)
                building_3d.children.append(item)

            elif item_1d.extra.get('osm:amenity', None) and item_1d.extra.get('osm:amenity', None) not in ('fountain', 'taxi', 'post_box', 'bench', 'toilets', 'parking_entrance'):
                # Except parking?

                #coords = amenity.geom.centroid.coords[0]
                #panel_text = amenity.extra['amenity'] if amenity.extra['amenity'] else None
                panel_text = item_1d.extra['osm:name'] if item_1d.extra.get('osm:name', None) else (item_1d.extra['osm:amenity'].upper() if item_1d.extra['osm:amenity'] else None)
                item = urban.panel(width=3.2, height=0.9, text=panel_text)
                item.extra['ddd:item'] = item_1d
                item.name = "Panel: %s %s" % (item_1d.extra['osm:amenity'], item_1d.extra.get('osm:name', None))
                item = self.snap_to_building(item, building_3d)
                if item:
                    item = item.translate([0, 0, 3.2])  # no post
                    color = random.choice(["#d41b8d", "#a7d42a", "#e2de9f", "#9f80e2"])
                    item = terrain.terrain_geotiff_min_elevation_apply(item, self.osm.ddd_proj)
                    building_3d.children.append(item)
                else:
                    logger.info("Could not snap item to building (skipping item): %s", item)
                #building_3d.show()

            elif item_1d.extra.get('osm:shop', None):
                #coords = item_1d.geom.centroid.coords[0]
                panel_text = (item_1d.extra['osm:name'] if item_1d.extra.get('osm:name', None) else item_1d.extra['osm:shop'])
                item = urban.panel(width=2.5, height=0.8, text=panel_text)
                item.extra['ddd:item'] = item_1d
                item.name = "Panel: %s %s" % (item_1d.extra['osm:shop'], item_1d.extra.get('osm:name', None))
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
                logger.debug("Unknown building-related item: %s", item_1d)



