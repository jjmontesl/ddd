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


from pint import UnitRegistry
ureg = UnitRegistry()


# TODO: Move to a quantity parsing library (also check quantity3, but it doesn't seem to make conversions)
def parse_meters(expr):
    quantity = ureg.parse_expression(str(expr))
    if not isinstance(quantity, float) and not isinstance(quantity, int):
        quantity = quantity.to(ureg.meter).magnitude
    return float(quantity)

def parse_material(name, color):
    material = None
    if hasattr(ddd.mats, name):
        material = getattr(ddd.mats, name)
    else:
        material = ddd.material(name, color)
    return material


class BuildingOSMBuilder():

    def __init__(self, osmbuilder):

        self.osm = osmbuilder

    def preprocess_buildings_features(self, features_2d):

        logger.info("Preprocessing buildings and bulding parts (2D)")
        # TODO: create nested buildings them separately, consider them part of the bigger building for subtraction)

        # Assign each building part to a building, or transform it into a building if needed
        #features = sorted(features_2d.children, key=lambda f: f.geom.area)
        features_2d_original = list(features_2d.children)
        for feature in list(features_2d.children):
            if feature.geom.type == 'Point': continue

            if feature.extra.get('osm:building:part', None) is None and feature.extra.get('osm:building', None) is None: continue

            # Find building
            #buildings = features_2d.select(func=lambda o: o.extra.get('osm:building', None) and ddd.polygon(o.geom.exterior.coords).contains(feature))
            buildings = features_2d.select(func=lambda o: o.extra.get('osm:building', None) and o != feature and o.contains(feature) and o in features_2d_original)

            if len(buildings.children) == 0:
                if feature.extra.get('osm:building', None) is None:
                    logger.warn("Building part with no building: %s", feature)
                    building = ddd.shape(feature.geom, name="Building (added): %s" % feature.name)
                    building.extra['osm:building'] = feature.extra.get('osm:building:part', 'yes')
                    building.extra['ddd:building:parts'] = [feature]
                    feature.extra['ddd:building:parent'] = building
                    features_2d.append(building)

            elif len(buildings.children) > 1:
                # Sort by area and get the smaller one
                buildings.children.sort(key=lambda b: b.geom.area, reverse=False)
                logger.warn("Building part with multiple buildings: %s -> %s", feature, buildings.children)

                feature.extra['ddd:building:parent'] = buildings.children[0]
                if 'ddd:building:parts' not in buildings.children[0].extra:
                    buildings.children[0].extra['ddd:building:parts'] = []
                buildings.children[0].extra['ddd:building:parts'].append(feature)

            else:
                logger.debug("Associating building part to building: %s -> %s", feature, buildings.children[0])
                feature.extra['ddd:building:parent'] = buildings.children[0]
                if 'ddd:building:parts' not in buildings.children[0].extra:
                    buildings.children[0].extra['ddd:building:parts'] = []
                buildings.children[0].extra['ddd:building:parts'].append(feature)


    def link_items_to_buildings(self, buildings_2d, items_1d):

        logger.info("Linking items to buildings.")
        # TODO: Link to building parts, inspect facade, etc.

        for feature in items_1d.children:
            # Find closest building
            #point = feature.copy(name="Point: %s" % (feature.extra.get('name', None)))
            point = feature
            building, distance = self.closest_building(buildings_2d, point)
            if not building:
                continue

            if distance > 10:
                continue

            feature.extra['osm:building'] = building

            if feature.extra.get('osm:amenity', None) or feature.extra.get('osm:shop', None):
                # TODO: Do the opposite, create items we are interested in, avoid this exception
                if point.extra.get('osm:amenity', None) in ('waste_disposal', 'waste_basket', 'recycling', 'bicycle_parking'):
                    continue

                logger.debug("Associating item %s to building %s.", feature, building)
                #logger.debug("Point: %s  Building: %s  Distance: %s", point, building, distance)
                building.extra['ddd:building:items'].append(feature)

    def link_items_ways_to_buildings(self, buildings_all, items):
        for item in items.children:

            '''
            for building in buildings.children:
                if building.contains(item):
                    logger.info("Associating item %s to building %s.", item, building)
                    item.extra['ddd:building:parent'] = building
                    #building.extra['ddd:building:items_ways'].append(item)
            '''

            buildings = buildings_all.select(func=lambda o: o.extra.get('osm:building', None) and not o.extra.get('ddd:building:parent', None) and o.contains(item))

            if len(buildings.children) > 1:
                logger.warn("Item with multiple buildings: %s -> %s", item, buildings.children)
                # Sort by area
                buildings.children.sort(key=lambda b: b.geom.area, reverse=True)

            if len(buildings.children) > 0:
                building = buildings.children[0]
                logger.info("Associating item (way) %s to building %s.", item, building)
                item.extra['ddd:building:parent'] = building
                #building.extra['ddd:building:items_ways'].append(item)

    def closest_building(self, buildings_2d, point):
        closest_building = None
        closest_distance = math.inf
        for building in buildings_2d.children:
            distance = point.distance(building)
            if distance < closest_distance:
                closest_building = building
                closest_distance = distance
        return closest_building, closest_distance

    def generate_buildings_3d(self, buildings_2d):
        logger.info("Generating 3D buildings (%d)", len(buildings_2d.children))

        buildings_3d = ddd.group3(name="Buildings")
        for building_2d in buildings_2d.children:
            if building_2d.extra.get('ddd:building:parent', None) in (None, building_2d):
                logger.debug("Generating building: %s", building_2d)
                building_3d = self.generate_building_3d_generic(building_2d)
                if building_3d and len(list(building_3d.vertex_iterator())) > 0:
                    self.generate_building_3d_amenities(building_3d)
                    building_3d = self.generate_building_3d_elevation(building_3d)
                    buildings_3d.append(building_3d)
        return buildings_3d


    def generate_building_3d_generic(self, building_2d):
        """
        Buildings 2D may contain references to building parts.

        TODO: Do a lot more in tags in 2D and here, and generalize tasks to pipelines and tags.
        Support buildings recursively earlier.
        """

        floors = building_2d.extra.get('osm:building:levels', None)
        floors_min = building_2d.extra.get('osm:building:min_level', 0)
        if not floors:
            floors = random.randint(2, 8)

        floors = int(float(floors))
        floors_min = int(float(floors_min))
        base_floors = floors
        base_floors_min = floors_min

        random.seed(hash(building_2d.name))
        building_material = random.choice([ddd.mats.building_1, ddd.mats.building_2, ddd.mats.building_3])

        if building_2d.extra.get('osm:building:material', None):
            material_name = building_2d.extra.get('osm:building:material')
            if hasattr(ddd.mats, material_name):
                building_material = getattr(ddd.mats, material_name)

        entire_building_2d = ddd.group2()
        entire_building_3d = building_2d.copy3(name="Building: %s" % (building_2d.name))

        roof_type = weighted_choice({'none': 2,
                                     'flat': 1,
                                     'pyramidal': 0.5,
                                     'attic': 0.5,
                                     'terrace': 1})
        roof_buffered = weighted_choice({True: 1, False: 5})
        roof_buffer = random.uniform(0.5, 1.2)
        roof_wall_material = weighted_choice({"stone": 3, "bricks": 1})

        for part in (building_2d.extra.get('ddd:building:parts', []) + [building_2d]):

            # Process subbuildings recursively (non standard, but improves support and compatibility with other renderers)
            if part != building_2d and part.extra.get('osm:building', None) is not None:
                subbuilding = self.generate_building_3d_generic(part)
                entire_building_2d.append(part)
                entire_building_3d.append(subbuilding)
                continue

            building_3d = None
            try:

                floors = int(float(part.extra.get('osm:building:levels', base_floors)))
                if floors == 0:
                    logger.warn("Building part with 0 floors (setting to 1): %s", floors)
                    floors = 1
                floors_min = int(float(part.extra.get('osm:building:min_level', base_floors_min)))

                # Remove the rest of the building
                if part == building_2d:
                    part = part.subtract(entire_building_2d)
                if part.geom.is_empty:
                    continue

                material = building_material
                if part.extra.get('osm:building:material', None):
                    material_name = part.extra.get('osm:building:material')
                    if hasattr(ddd.mats, material_name):
                        material = getattr(ddd.mats, material_name)
                if part.extra.get('osm:building:facade:material', None):
                    material_name = part.extra.get('osm:building:facade:material')
                    if hasattr(ddd.mats, material_name):
                        material = getattr(ddd.mats, material_name)

                # Roof: default
                pbuffered = roof_buffered
                roof_shape = roof_type
                if floors < 2:
                    roof_shape = 'none'
                if floors < base_floors:
                    pbuffered = False
                    if (random.uniform(0, 1) < 0.5): roof_shape = random.choice(['terrace', 'none'])
                    if (floors <= 2):
                        if (random.uniform(0, 1) < 0.8): roof_shape = random.choice(['terrace', 'terrace', 'terrace', 'none'])
                if 'osm:building:part' in part.extra:
                    roof_shape = 'none'
                    pbuffered = 0

                # Roof: info
                roof_shape = part.extra.get('osm:roof:shape', roof_shape)
                roof_height = float(part.extra.get('osm:roof:height', 0))

                roof_material = ddd.mats.roof_tiles
                if part.extra.get('osm:roof:material', None):
                    material_name = part.extra.get('osm:roof:material')
                    if hasattr(ddd.mats, material_name):
                        roof_material = getattr(ddd.mats, material_name)

                floors_height = floors * 3.00
                floors_min_height = floors_min * 3.00
                min_height = float(part.extra.get('osm:min_height', floors_min_height))
                #max_height = parse_meters(part.extra.get('osm:height', floors_height + min_height)) - roof_height
                max_height = parse_meters(part.extra.get('osm:height', floors_height)) - roof_height
                dif_height = max_height - min_height

                # Generate building procedurally (use library)
                try:
                    building_3d = part.extrude(dif_height)
                except ValueError as e:
                    logger.error("Could not generate building (%s): %s", part, e)
                    continue
                except DDDException as e:
                    logger.error("Could not generate building (%s): %s", part, e)
                    continue

                if min_height == 0:
                    building_3d = ddd.meshops.remove_faces_pointing(building_3d, ddd.VECTOR_DOWN)

                if min_height: building_3d = building_3d.translate([0, 0, min_height])
                building_3d = building_3d.material(material)

                # Building solid post processing
                if part.extra.get('osm:tower:type', None) == 'bell_tower':  # and dif_height > 6:
                    # Cut
                    center_pos = part.centroid().geom.coords[0]
                    (axis_major, axis_minor, axis_rot) = ddd.geomops.oriented_axis(part)
                    cut1 = ddd.rect([-axis_major.length(), -axis_minor.length() * 0.20, +axis_major.length(), +axis_minor.length() * 0.20])
                    cut2 = ddd.rect([-axis_major.length() * 0.20, -axis_minor.length(), +axis_major.length() * 0.20, +axis_minor.length()])
                    cuts = ddd.group2([cut1, cut2]).union().rotate(axis_rot).extrude(-6.0).translate([center_pos[0], center_pos[1], max_height - 2])
                    #ddd.group3([building_3d, cuts]).show()
                    building_3d = building_3d.subtract(cuts)
                    #building_3d.show()

                    # TODO: Create 1D items
                    (axis_major, axis_minor, axis_rot) = ddd.geomops.oriented_axis(part.buffer(-0.80))
                    for coords in (axis_major.geom.coords[0], axis_major.geom.coords[1], axis_minor.geom.coords[0], axis_minor.geom.coords[1]):
                        bell = urban.bell().translate([coords[0], coords[1], max_height - 3.0])
                        entire_building_3d.append(bell)



                # Base
                if 'osm:building:part' not in part.extra:
                    if random.uniform(0, 1) < 0.2:
                        base = part.buffer(0.3, cap_style=2, join_style=2).extrude(1.00)
                        base = base.material(random.choice([ddd.mats.building_1, ddd.mats.building_2, ddd.mats.building_3, ddd.mats.stone, ddd.mats.cement]))
                        building_3d.children.append(base)

                # Roof
                try:
                    roof = None

                    if roof_shape == 'flat':
                        # Flat
                        default_height = 0.75
                        roof_height = roof_height if roof_height else default_height
                        roof = part.buffer(roof_buffer if pbuffered else 0, cap_style=2, join_style=2).extrude(roof_height).translate([0, 0, max_height]).material(roof_material)

                    elif roof_shape == 'terrace':
                        # Flat
                        usefence = random.uniform(0, 1) < 0.8
                        if usefence:
                            terrace = part.subtract(part.buffer(-0.4)).extrude(0.6).translate([0, 0, max_height]).material(getattr(ddd.mats, roof_wall_material))
                            fence = part.buffer(-0.2).outline().extrude(0.7).twosided().translate([0, 0, max_height + 0.6]).material(ddd.mats.railing)
                            roof = ddd.group3([terrace, fence], name="Roof")
                        else:
                            terrace = part.subtract(part.buffer(-0.4)).extrude(random.uniform(0.40, 1.20)).translate([0, 0, max_height]).material(ddd.mats.stone)
                            roof = ddd.group3([terrace], name="Roof")

                    elif roof_shape == 'pyramidal':
                        # Pointy
                        default_height = floors * 0.2 + random.uniform(2.0, 5.0)
                        roof_height = roof_height if roof_height else default_height
                        roof = part.buffer(roof_buffer if pbuffered else 0, cap_style=2, join_style=2).extrude_step(part.centroid(), roof_height)
                        roof = roof.translate([0, 0, max_height]).material(roof_material)

                    elif roof_shape == 'attic':
                        # Attic
                        height = random.uniform(3.0, 4.0)
                        roof = part.buffer(roof_buffer if pbuffered else 0, cap_style=2, join_style=2).extrude_step(part.buffer(-2), height, method=ddd.EXTRUSION_METHOD_SUBTRACT).translate([0, 0, max_height]).material(roof_material)

                    elif roof_shape == 'gabled':
                        # Attic
                        base = part.buffer(roof_buffer if pbuffered else 0)
                        orientation = "major"
                        if part.extra.get("osm:roof:orientation", "along") == "across": orientation = "minor"
                        (axis_major, axis_minor, axis_rot) = ddd.geomops.oriented_axis(base)
                        axis_line = axis_major if orientation == "major" else axis_minor
                        default_height = random.uniform(3.0, 4.0)
                        roof_height = roof_height if roof_height else default_height
                        roof = base.extrude_step(axis_line, roof_height).translate([0, 0, max_height]).material(roof_material)

                        '''
                        #elif roof_shape == 'round':
                        # Attic
                        base = part.buffer(roof_buffer if pbuffered else 0)
                        orientation = "major"
                        if part.extra.get("osm:roof:orientation", "along") == "across": orientation = "minor"
                        (axis_major, axis_minor, axis_rot) = ddd.geomops.oriented_axis(base)
                        axis_line = axis_major if orientation == "major" else axis_minor

                        major_seg_plus = ((axis_major.coords[0][0] + (axis_minor.coords[0][0] - axis_minor.coords[1][0]) * 0.5, axis_major.coords[0][1] + (axis_minor.coords[0][1] - axis_minor.coords[1][1]) * 0.5),
                                          (axis_major.coords[1][0] + (axis_minor.coords[0][0] - axis_minor.coords[1][0]) * 0.5, axis_major.coords[1][1] + (axis_minor.coords[0][1] - axis_minor.coords[1][1]) * 0.5))
                        minor_seg_plus = ((axis_minor.coords[0][0] + (axis_major.coords[0][0] - axis_major.coords[1][0]) * 0.5, axis_minor.coords[0][1] + (axis_major.coords[0][1] - axis_major.coords[1][1]) * 0.5),
                                          (axis_minor.coords[1][0] + (axis_major.coords[0][0] - axis_major.coords[1][0]) * 0.5, axis_minor.coords[1][1] + (axis_major.coords[0][1] - axis_major.coords[1][1]) * 0.5))



                        default_height = random.uniform(3.0, 4.0)
                        roof_height = roof_height if roof_height else default_height
                        roof = base.extrude_step(axis_line, roof_height).translate([0, 0, max_height]).material(roof_material)
                        '''

                    elif roof_shape == 'skillion':
                        # Attic
                        base = part.buffer(roof_buffer if pbuffered else 0)
                        orientation = "major"
                        if part.extra.get("osm:roof:orientation", "along") == "across": orientation = "minor"
                        (axis_major, axis_minor, axis_rot) = ddd.geomops.oriented_axis(base)

                        axis_major = axis_major.geom
                        axis_minor = axis_minor.geom

                        major_seg_plus = ((axis_major.coords[0][0] + (axis_minor.coords[0][0] - axis_minor.coords[1][0]) * 0.5, axis_major.coords[0][1] + (axis_minor.coords[0][1] - axis_minor.coords[1][1]) * 0.5),
                                          (axis_major.coords[1][0] + (axis_minor.coords[0][0] - axis_minor.coords[1][0]) * 0.5, axis_major.coords[1][1] + (axis_minor.coords[0][1] - axis_minor.coords[1][1]) * 0.5))
                        minor_seg_plus = ((axis_minor.coords[0][0] + (axis_major.coords[0][0] - axis_major.coords[1][0]) * 0.5, axis_minor.coords[0][1] + (axis_major.coords[0][1] - axis_major.coords[1][1]) * 0.5),
                                          (axis_minor.coords[1][0] + (axis_major.coords[0][0] - axis_major.coords[1][0]) * 0.5, axis_minor.coords[1][1] + (axis_major.coords[0][1] - axis_major.coords[1][1]) * 0.5))

                        skillion_line = major_seg_plus if orientation == "major" else minor_seg_plus
                        default_height = random.uniform(1.0, 2.0)
                        roof_height = roof_height if roof_height else default_height
                        roof = base.extrude_step(ddd.line(skillion_line), roof_height).translate([0, 0, max_height]).material(roof_material)

                    elif roof_shape == 'hipped':
                        # Attic
                        base = part.buffer(roof_buffer if pbuffered else 0)
                        orientation = "major"
                        if part.extra.get("osm:roof:orientation", "along") == "across": orientation = "minor"
                        (axis_major, axis_minor, axis_rot) = ddd.geomops.oriented_axis(base)
                        axis_line = axis_major if orientation == "major" else axis_minor
                        #other_axis_line = axis_minor if orientation == "major" else axis_major

                        axis_line = axis_line.intersection(axis_line.centroid().buffer(axis_minor.geom.length / 2, cap_style=ddd.CAP_ROUND, resolution=8))

                        default_height = random.uniform(1.0, 2.0)
                        roof_height = roof_height if roof_height else default_height
                        roof = base.extrude_step(axis_line, roof_height).translate([0, 0, max_height]).material(roof_material)

                    elif roof_shape == 'dome':
                        default_height = random.uniform(2.0, 4.0)
                        roof_height = roof_height if roof_height else default_height

                        roofbase = part.buffer(roof_buffer if pbuffered else 0, cap_style=2, join_style=2)
                        roof = roofbase.copy()

                        steps = 6
                        stepheight = 1.0 / steps
                        for i in range(steps):
                            stepy = (i + 1) * stepheight
                            stepx = math.sqrt(1 - (stepy ** 2))
                            stepbuffer = -(1 - stepx)
                            roof = roof.extrude_step(roofbase.buffer(stepbuffer * roof_height), stepheight * roof_height)
                        roof = roof.translate([0, 0, max_height]).material(roof_material)

                    elif roof_shape == 'none':
                        pass

                    else:
                        logger.warning("Unknown roof shape: %s", roof_shape)

                    if roof: building_3d.children.append(roof)

                except Exception as e:
                    logger.warning("Cannot generate roof: %s (geom: %s)" % (e, part.geom))

                # UV Mapping
                building_3d = ddd.uv.map_cubic(building_3d)

                entire_building_2d.append(part)
                entire_building_3d.append(building_3d)

            except ValueError as e:
                logger.error("Cannot generate building part %s: %s (geom: %s)" % (part, e, part.geom))
                raise
                #return None
            except IndexError as e:
                logger.error("Cannot generate building part %s: %s (geom: %s)" % (part, e, part.geom))
                raise
                #return None
            except Exception as e:
                logger.error("Cannot generate building part %s: %s (geom: %s)" % (part, e, part.geom))
                raise

        entire_building_3d.extra['building_2d'] = building_2d
        entire_building_3d.extra['ddd:building:feature'] = building_2d

        return entire_building_3d

    def generate_building_3d_elevation(self, building_3d):
        building_3d = terrain.terrain_geotiff_min_elevation_apply(building_3d, self.osm.ddd_proj)
        building_3d.extra['ddd:building:feature'].extra['ddd:building:elevation'] = building_3d.extra['_terrain_geotiff_min_elevation_apply:elevation']
        #logger.info("Assigning elevation %s to building: %s -> %s", building_3d.extra['_terrain_geotiff_min_elevation_apply:elevation'], building_3d, building_3d.extra['ddd:building:feature'])
        building_3d = building_3d.translate([0, 0, -0.20])  # temporary hack floor snapping
        return building_3d

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
        item_3d = item_3d.rotate([0, 0, angle + math.pi])  # + math.pi / 2.0
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
                #item = terrain.terrain_geotiff_min_elevation_apply(item, self.osm.ddd_proj)
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
                    #item = terrain.terrain_geotiff_min_elevation_apply(item, self.osm.ddd_proj)
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
                    #item = terrain.terrain_geotiff_min_elevation_apply(item, self.osm.ddd_proj)
                    building_3d.children.append(item)
                else:
                    logger.info("Could not snap item to building (skipping item): %s", item)

            else:
                logger.debug("Unknown building-related item: %s", item_1d)



