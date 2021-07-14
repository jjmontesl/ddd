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



class BuildingsRoofs3DOSMBuilder():

    def __init__(self, osmbuilder):

        self.osm = osmbuilder

    def generate_building_3d_part_roof(self, part):

        roof = None

        roof_shape = part.get('ddd:roof:shape')
        roof_height = parse_meters(part.get('ddd:roof:height'))

        floors = int(float(part.get('ddd:building:levels')))
        floors_min = int(float(part.get('ddd:building:min_level')))
        floor_0_height = part.get('ddd:building:level:0:height')

        roof_buffered = weighted_choice({True: 1, False: 5})
        roof_buffer = random.uniform(0.5, 1.2)
        roof_wall_material = weighted_choice({"stone": 3, "bricks": 1})
        pbuffered = roof_buffered

        floors_height = floor_0_height + (floors - 1) * 3.00
        floors_min_height = floors_min * 3.00
        min_height = float(part.extra.get('osm:min_height', floors_min_height))
        #max_height = parse_meters(part.extra.get('osm:height', floors_height + min_height)) - roof_height
        max_height = parse_meters(part.extra.get('osm:height', floors_height)) - roof_height
        dif_height = max_height - min_height

        roof_material = ddd.mats.roof_tiles
        material_name = part.get('ddd:roof:material', part.get('osm:roof:material', None))
        if material_name:
            if hasattr(ddd.mats, material_name):
                roof_material = getattr(ddd.mats, material_name)

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

        return roof

