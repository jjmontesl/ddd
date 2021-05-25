# DDD(123) - Library for procedural generation of 2D and 3D geometries and scenes
# Copyright (C) 2021 Jose Juan Montes
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import logging
import math
import random
import sys
import numpy as np

from ddd.ddd import DDDObject2, DDDObject3
from ddd.ddd import ddd
from ddd.pack.sketchy import plants, urban
from ddd.geo import terrain
from ddd.core.exception import DDDException
from ddd.util.dddrandom import weighted_choice
from ddd.pack.sketchy.buildings import window_with_border, door, portal
from ddd.osm.osmunits import parse_meters


# Get instance of logger for this module
logger = logging.getLogger(__name__)



class Buildings3DOSMBuilder():

    def __init__(self, osmbuilder):

        self.osm = osmbuilder

    def preprocess_buildings_3d(self, buildings_2d):
        """
        """
        logger.info("Preprocessing buildings and bulding parts (3D): %d objects", len(buildings_2d.children))

        for building_2d in buildings_2d.children:
            self.preprocess_building_3d(building_2d)

    def preprocess_building_3d(self, building_2d):
        """
        """

        # TODO: account for floor 0 only

        # Find minimum and maximum elevation of building footprint
        elevation_min, elevation_max = float('inf'), float('-inf')
        points = building_2d.vertex_list()

        for p in points:
            pe = terrain.terrain_geotiff_elevation_value(p, self.osm.ddd_proj)
            if pe < elevation_min: elevation_min = pe
            if pe > elevation_max: elevation_max = pe

        building_2d.set('ddd:building:elevation:min', elevation_min)
        building_2d.set('ddd:building:elevation:max', elevation_max)
        #building_2d.set('ddd:building:floors:0:height', elevation_max - elevation_min)
        #building_3d = terrain.terrain_geotiff_min_elevation_apply(building_3d, self.osm.ddd_proj)

        # Calculate contact / intersection / with other buildings
        #  1. do this in 2D preprocess?
        #  2. do this using area containment / contact system?

        # Calculate for each segment
        #   contact with segments of other/self buildings


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

        floors = building_2d.extra.get('ddd:building:levels', building_2d.extra.get('osm:building:levels', None))
        floors_min = floors = building_2d.extra.get('ddd:building:min_level', building_2d.extra.get('osm:building:min_level', 0))

        # TODO: Do this in the pipeline or fail here if ddd:building:levels not set
        if not floors:
            floors = random.randint(2, 8)

        floors = int(float(floors))
        floors_min = int(float(floors_min))
        base_floors = floors
        base_floors_min = floors_min

        elevation_min = building_2d.get('ddd:building:elevation:min')
        elevation_max = building_2d.get('ddd:building:elevation:max')
        elevation_diff = elevation_max - elevation_min
        floor_0_height = 3 + elevation_diff # TODO: temporary for test, but loors and segments need to be resolved in advance

        random.seed(hash(building_2d.name))
        building_material = random.choice([ddd.mats.building_1, ddd.mats.building_2, ddd.mats.building_3, ddd.mats.building_4, ddd.mats.building_5])

        material_name = building_2d.get('ddd:building:material', building_2d.get('osm:building:material', None))
        if material_name:
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
                part.set('ddd:building:elevation:min', default=elevation_min)
                part.set('ddd:building:elevation:max', default=elevation_max)
                subbuilding = self.generate_building_3d_generic(part)
                entire_building_2d.append(part)
                entire_building_3d.append(subbuilding)
                continue

            building_3d = None
            try:

                floors = int(float(part.extra.get('ddd:building:levels', part.extra.get('osm:building:levels', base_floors))))
                floors_min = int(float(part.extra.get('ddd:building:min_level', part.extra.get('osm:building:min_level', base_floors_min))))

                if floors == 0:
                    logger.warn("Building part with 0 floors (setting to 1): %s", floors)
                    floors = 1

                # Remove the rest of the building
                if part == building_2d:
                    part = part.subtract(entire_building_2d)
                    part.validate()
                if part.geom.is_empty:
                    continue

                material = building_material
                material_name = part.get('ddd:building:material', part.get('osm:building:material', None))
                if material_name:
                    if hasattr(ddd.mats, material_name):
                        material = getattr(ddd.mats, material_name)
                material_name = part.get('ddd:building:facade:material', part.get('osm:building:facade:material', None))
                if material_name:
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
                roof_shape = part.get('ddd:roof:shape', part.get('osm:roof:shape', roof_shape))
                roof_height = float(part.extra.get('osm:roof:height', 0))

                roof_material = ddd.mats.roof_tiles
                material_name = part.get('ddd:roof:material', part.get('osm:roof:material', None))
                if material_name:
                    if hasattr(ddd.mats, material_name):
                        roof_material = getattr(ddd.mats, material_name)

                # Calculate part height
                # FIXME: this code is duplicated inside building_part, but also used by roofs and for initial checks here
                floors_height = floor_0_height + (floors - 1) * 3.00  # Note that different floor heights
                floors_min_height = floors_min * 3.00  # TODO: account for variabe floors + interfloors height
                min_height = float(part.extra.get('osm:min_height', floors_min_height))
                #max_height = parse_meters(part.extra.get('osm:height', floors_height + min_height)) - roof_height
                max_height = parse_meters(part.extra.get('osm:height', floors_height)) - roof_height
                dif_height = max_height - min_height

                if dif_height <= 0:
                    logger.warn("Building with <= 0 height: %s (skipping)", part)
                    continue


                # Generate building procedurally (use library)
                try:
                    #building_3d = part.extrude(dif_height)
                    building_3d = self.generate_building_3d_part_body(part, material,
                                                                      floor_0_height, floors, floors_min,
                                                                      roof_height, entire_building_3d)
                #except ValueError as e:
                #    logger.error("Could not generate building (%s): %s", part, e)
                #    continue
                except DDDException as e:
                    logger.error("Could not generate building (%s): %s", part, e)
                    continue

                '''
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
                '''

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

                        # Create a 1 unit height flat roof and then calculate height along the skillion direction line for the top half vertices
                        roof = base.extrude(1.0)
                        #skillion_line = ddd.line(skillion_line)
                        #roof = base.extrude_step(skillion_line, roof_height).translate([0, 0, max_height]).material(roof_material)
                        default_height = random.uniform(1.0, 2.0)
                        roof_height = roof_height if roof_height else default_height
                        roof = roof.translate([0, 0, max_height]).material(roof_material)

                    elif roof_shape == 'hipped':

                        # TODO:
                        #  https://gis.stackexchange.com/questions/136143/how-to-compute-straight-skeletons-using-python
                        #  https://scikit-geometry.github.io/scikit-geometry/skeleton.html

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

                    #elif
                    # Reminder: https://scikit-geometry.github.io/scikit-geometry/skeleton.html
                    #  https://gis.stackexchange.com/questions/136143/how-to-compute-straight-skeletons-using-python

                    elif roof_shape == 'none':
                        pass

                    else:
                        logger.warning("Unknown roof shape: %s", roof_shape)

                    if roof:
                        roof = ddd.uv.map_cubic(roof)
                        building_3d.children.append(roof)

                except Exception as e:
                    logger.warning("Cannot generate roof: %s (geom: %s)" % (e, part.geom))

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

    def generate_building_3d_part_body(self, part, material,
                                       floor_0_height, floors, floors_min,
                                       roof_height, entire_building_3d):  # temporarily, should be in metadata

        floors_height = floor_0_height + (floors - 1) * 3.00
        floors_min_height = floors_min * 3.00
        min_height = float(part.extra.get('osm:min_height', floors_min_height))
        #max_height = parse_meters(part.extra.get('osm:height', floors_height + min_height)) - roof_height
        max_height = parse_meters(part.extra.get('osm:height', floors_height)) - roof_height
        dif_height = max_height - min_height

        if dif_height == 0:
            #logger.warn("Building with 0 height: %s (skipping)", part)
            raise DDDException("Building with 0 height: %s (skipping)" % part)

        # Generate building procedurally

        floor_type = 'default'
        if part.get('osm:building', None) == 'roof':
            floor_type = 'columns'

        if floor_type == 'default':
            try:
                building_3d = part.extrude(dif_height)
                #self.generate_building_3d_part_body_hull(part)

            except ValueError as e:
                raise DDDException("Could not generate building part body (%s): %s" % (part, e))
        elif floor_type == 'columns':
            return part.copy3()
        else:
            raise DDDException("Cannot generate building body, invalid floor_type=%s: %s" % (floor_type, part))

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
                base = base.material(random.choice([ddd.mats.building_1, ddd.mats.building_2, ddd.mats.building_3, ddd.mats.building_4, ddd.mats.building_5]))
                building_3d.children.append(base)

        building_3d = ddd.uv.map_cubic(building_3d)

        # Items processing (per floor)
        min_height_accum = 0
        for floor_num in range(floors):
            floor_height = floor_0_height if floor_num == 0 else 3.0
            for parti in part.individualize(always=True).children:  # Individualizing to allow for outline afterwards, not needed if floor metada nodes were already created by this time
                self.generate_building_3d_part_body_items_floor(building_3d, parti, floor_num, min_height_accum, floor_height)
            min_height_accum = min_height_accum + floor_height

        return building_3d


    def generate_building_3d_part_body_hull(self, part):
        pass

    def generate_building_3d_part_body_items_floor(self, building_3d, part, floor_num, min_height, height):
        """
        Windows, doors, etc... currently as a testing approach.
        Should use pre-created items (nodes, metadata...) or a building schema.
        """

        part_outline = part.outline()
        vertices = part_outline.vertex_list()  # This will fail if part had no geometry (eg. it was empty or children-only)
        segments_verts = list(zip(vertices[:-1], vertices[1:]))
        segments = part.get('ddd:building:segments')

        item_width = 3
        min_seg_width = 4.0

        # TODO: Temporary, add doors earlier
        doors = 0
        if floor_num == 0: doors = 1

        if len(segments) != len(segments_verts):
            logger.warn("Cannot generate body items floor for building (no segment analysis available): %s", building_3d)
            return

        for idx, (v0, v1) in enumerate(segments_verts):

            segment = segments[idx]
            if segment.facade_type in ('contact'):  # , 'lateral'):
                continue

            v0, v1 = (np.array(v0), np.array(v1))
            dir_vec = v1 - v0
            dir_angle = math.atan2(dir_vec[1], dir_vec[0])
            seg_length = np.sqrt(dir_vec.dot(dir_vec))

            num_items = int(seg_length / item_width) if seg_length > min_seg_width else 0

            for d in np.linspace(0.0, seg_length, num_items + 2, endpoint=True)[1:-1]:
                p = v0 + dir_vec * (d / seg_length)
                #p, segment_idx, segment_coords_a, segment_coords_b = part_outline.interpolate_segment(d)

                object_min_height = 0.0

                if doors > 0 and segment.facade_type in ('main'):
                    doors -= 1

                    portal_type = random.choice(['door', 'portal'])
                    if portal_type == 'door':
                        obj = door()
                    else:
                        obj = portal()

                    obj = ddd.meshops.remove_faces_pointing(obj, ddd.VECTOR_BACKWARD)
                    obj = ddd.uv.map_cubic(obj)  # FIXME: Meshops "remove_faces_pointing" should fix UVs / normals
                    point_elevation = terrain.terrain_geotiff_elevation_value(p, self.osm.ddd_proj)
                    object_min_height = point_elevation - float(part.get('ddd:building:elevation:min', 0))

                else:
                    key = "building-window"
                    object_min_height = min_height + height - 3.0 + 1.0
                    obj  = self.osm.catalog.instance(key)
                    if not obj:
                        obj = window_with_border()
                        obj = ddd.meshops.remove_faces_pointing(obj, ddd.VECTOR_BACKWARD)
                        obj = ddd.uv.map_cubic(obj) # FIXME: Meshops "remove_faces_pointing" should fix UVs / normals
                        obj = self.osm.catalog.add(key, obj)

                obj = obj.rotate([0, 0, dir_angle + math.pi])
                obj = obj.translate([p[0], p[1], object_min_height])
                building_3d.append(obj)


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
                item.copy_from(item_1d)

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
                item.copy_from(item_1d)
                item.extra['ddd:item'] = item_1d
                item.name = "Panel: %s %s" % (item_1d.extra['osm:amenity'], item_1d.extra.get('osm:name', None))
                item = self.snap_to_building(item, building_3d)
                if item:
                    item = item.translate([0, 0, 3.2])  # no post
                    color = random.choice(["#d41b8d", "#a7d42a", "#e2de9f", "#9f80e2"])
                    item.children[0] = item.children[0].material(ddd.material(color=color), include_children=False)
                    #item = terrain.terrain_geotiff_min_elevation_apply(item, self.osm.ddd_proj)
                    building_3d.children.append(item)
                else:
                    logger.info("Could not snap item to building (skipping item): %s", item)
                #building_3d.show()

            elif item_1d.extra.get('osm:shop', None):
                #coords = item_1d.geom.centroid.coords[0]
                panel_text = (item_1d.extra['osm:name'] if item_1d.extra.get('osm:name', None) else item_1d.extra['osm:shop'])
                item = urban.panel(width=2.5, height=0.8, text=panel_text)
                item.copy_from(item_1d)
                item.extra['ddd:item'] = item_1d
                item.name = "Shop Panel: %s %s" % (item_1d.extra['osm:shop'], item_1d.extra.get('osm:name', None))
                item = self.snap_to_building(item, building_3d)
                if item:
                    item = item.translate([0, 0, 2.8])  # no post
                    color = random.choice(["#c41a7d", "#97c41a", "#f2ee0f", "#0f90f2"])
                    item.children[0] = item.children[0].material(ddd.material(color=color), include_children=False)
                    #item = terrain.terrain_geotiff_min_elevation_apply(item, self.osm.ddd_proj)
                    building_3d.children.append(item)
                else:
                    logger.info("Could not snap item to building (skipping item): %s", item)

            else:
                logger.debug("Unknown building-related item: %s", item_1d)



