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


import copy
import json
import logging
import math
import random
import numpy as np

from ddd.ddd import ddd
from ddd.math.vector3 import Vector3
from ddd.math.math import DDDMath
from ddd.ops.height.height import HeightFunction


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class PathHeightFunction(HeightFunction):

    def __init__(self, path):
        assert(isinstance(path, ddd.DDDObject2))
        self.path = path

    def value(self, x, y, z, idx=None, o=None):
        coords_p, segment_idx, segment_coords_a, segment_coords_b, closest_obj, closest_d = self.path.closest_segment(ddd.point([x, y]))
        interp_z = coords_p[2]
        return interp_z


class NodeBisectPathHeightFunction(PathHeightFunction):

    def __init__(self, path, debug_root=None):
        super().__init__(path)
        self._debug_root = debug_root

    def value(self, x, y, z, idx, o):

        # TODO: precalculate the point list and perpendiculars at each node
        path = self.path

        # Find the closest point in the path
        point = ddd.point([x, y, z])

        points = ddd.group2()
        for i, c in enumerate(path.coords_iterator()):
            points.append(ddd.point(c).set('index', i))

        closest, closest_d = points.closest(point)

        # Calculate perpendiculars to their bisecting angles
        index = closest.get('index')

        perpm1 = path.vertex_bisector(max(index - 1, 0), length=10.0)
        perp0 = path.vertex_bisector(index, length=10.0)
        perp1 = path.vertex_bisector(min(index + 1, len(points.children) - 1), length=10.0)

        # Debug
        #if (random.uniform(0, 1) < 0.01):
        #    root.append(perpm0.material(ddd.MAT_HIGHLIGHT))

        # Project point to perpendiculars
        dm1 = point.distance(perpm1)
        d0 = point.distance(perp0)
        d1 = point.distance(perp1)

        # Find which side of perp0 we are at
        perp0norm = (Vector3([perp0.geom.coords[1][0], perp0.geom.coords[1][1], 0]) - Vector3([perp0.geom.coords[0][0], perp0.geom.coords[0][1], 0])).normalized()
        perp0norm = Vector3([-perp0norm[1], perp0norm[0], perp0norm[2]]).normalized()

        perp0side = perp0norm.dot((Vector3(point.geom.coords[0]) - Vector3(closest.geom.coords[0])).normalized())

        interp_z = 0  # closest.geom.coords[0][2]
        try:
            if perp0side < 0:

                if dm1 + d0 > 0:
                    interp_z = (d0 / (dm1 + d0)) * perpm1.geom.coords[0][2] + (dm1 / (dm1 + d0)) * perp0.geom.coords[0][2]
                else:
                    interp_z = perp0.geom.coords[0][2]

                # Debug
                if (self._debug_root and random.uniform(0, 1) < 0.02):
                    #print(dm1, d0, d1, perp0side, perp0.geom.coords[0])
                    coords_p, segment_idx, segment_coords_a, segment_coords_b, closest_obj, closest_d = perp0.closest_segment(ddd.point([x, y, z]))
                    marker = ddd.path3(ddd.line([[x, y, interp_z], coords_p]))
                    if (marker.path3.length > 0): self._debug_root.append(marker.material(ddd.MAT_HIGHLIGHT))
                    coords_p, segment_idx, segment_coords_a, segment_coords_b, closest_obj, closest_d = perpm1.closest_segment(ddd.point([x, y, z]))
                    marker = ddd.path3(ddd.line([[x, y, interp_z], coords_p]))
                    if (marker.path3.length > 0): self._debug_root.append(marker)

            else:
                if d1 + d0 > 0:
                    interp_z = (d0 / (d1 + d0)) * perp1.geom.coords[0][2] + (d1 / (d1 + d0)) * perp0.geom.coords[0][2]
                else:
                    interp_z = perp0.geom.coords[0][2]

        except Exception as e:
            logger.error("Error interpolating height using NodeBisectPathHeightFunction: %s", e)

        #dist_a = math.sqrt( (segment_coords_a[0] - coords_p[0]) ** 2 + (segment_coords_a[1] - coords_p[1]) ** 2 )
        #dist_b = math.sqrt( (segment_coords_b[0] - coords_p[0]) ** 2 + (segment_coords_b[1] - coords_p[1]) ** 2 )
        #factor_b = dist_a / (dist_a + dist_b)
        #factor_a = 1 - factor_b  # dist_b / (dist_a + dist_b) #1 - factor_b  #
        #interp_z = segment_coords_a[2] * factor_a + segment_coords_b[2] * factor_b
        #print(interp_z, closest_d, segment_coords_a, segment_coords_b)

        #print(list(closest.geom.coords))
        #interp_z = closest.geom.coords[0][2]

        return interp_z  # FIXME: z should not be added here, or not by default, as Z coordinates are already local in the path


class PathProfileHeightFunction(PathHeightFunction):
    pass

class BankingPathProfileHeightFunction(PathProfileHeightFunction):

    def __init__(self, path, conf):
        super().__init__(path)
        self.path = path
        self.conf = conf

    def value(self, x, y, z, idx, o):

        # TODO: precalculate the point list and perpendiculars at each node
        path = self.path

        # Find the closest point in the path
        point = ddd.point([x, y, z])

        points = ddd.group2()
        pathd = 0
        prev = None
        for i, c in enumerate(path.coords_iterator()):
            p = ddd.point(c)

            if prev:
                pathd += prev.distance(p)
            p.set('index', i)
            p.set('path_d', pathd)

            prev = p
            points.append(p)

        closest, closest_d = points.closest(point)

        # Calculate perpendiculars to their bisecting angles
        index = closest.get('index')

        perp_l = 20.0
        perpm1 = path.vertex_bisector(max(index - 1, 0), length=perp_l)
        perp0 = path.vertex_bisector(index, length=perp_l)
        perp1 = path.vertex_bisector(min(index + 1, len(points.children) - 1), length=perp_l)

        # Debug
        #if (random.uniform(0, 1) < 0.01):
        #    root.append(perpm0.material(ddd.MAT_HIGHLIGHT))

        # Project point to perpendiculars
        dm1 = point.distance(perpm1)
        d0 = point.distance(perp0)
        d1 = point.distance(perp1)

        # Find which side of perp0 we are at
        perp0norm = (Vector3([perp0.geom.coords[1][0], perp0.geom.coords[1][1], 0]) - Vector3([perp0.geom.coords[0][0], perp0.geom.coords[0][1], 0])).normalized()
        perp0norm = Vector3([-perp0norm[1], perp0norm[0], perp0norm[2]]).normalized()

        perp0side = perp0norm.dot((Vector3(point.geom.coords[0]) - Vector3(closest.geom.coords[0])).normalized())


        path_d = None
        #interp_z = 0  # closest.geom.coords[0][2]
        try:
            if (perp0side < 0):
                pm1 = points.children[max(index - 1, 0)]
                p0 = points.children[index]

                if dm1 + d0 > 0:
                    path_d = (d0 / (dm1 + d0)) * pm1.get('path_d') + (dm1 / (dm1 + d0)) * p0.get('path_d')
                else:
                    path_d = p0.get('path_d')

                center = perpm1.intersection(perp0)
                d = point.distance(center)
                rm1 = center.distance(pm1)
                r0 = center.distance(p0)
                r = (rm1 + r0) / 2
            else:
                p1 = points.children[min(index + 1, len(points.children) - 1)]
                p0 = points.children[index]

                if d1 + d0 > 0:
                    path_d = (d0 / (d1 + d0)) * p1.get('path_d') + (d1 / (d1 + d0)) * p0.get('path_d')
                else:
                    path_d = p0.get('path_d')

                center = perp1.intersection(perp0)
                d = point.distance(center)
                r1 = center.distance(p1)
                r0 = center.distance(p0)
                r = (r1 + r0) / 2

        except Exception as e:
            logger.error("Error interpolating height using BankingPathProfileHeightFunction: %s", e)
            return (x, y, z)

        signed_d = d - r

        # For straight segments, path_d and d are calculated projecting to the segment
        # TODO: improve this case
        if r == 0 or r > 10.0:
            coords_p, segment_idx, segment_coords_a, segment_coords_b, closest_obj, closest_d = self.path.closest_segment(ddd.point([x, y]))
            d = ((Vector3([x, y, z]) - Vector3(coords_p)) * Vector3([1, 1, 0]))  # make Z 0 in order to get the correct length
            #print(d)
            d = d.length()
            # Side of the segment
            segment_d = (Vector3(segment_coords_b) - Vector3(segment_coords_a)).normalized()
            segment_d_perp = Vector3([-segment_d[1], segment_d[0], segment_d[2]])
            side = segment_d_perp.dot((Vector3([x, y, z]) - Vector3(coords_p)).normalized())
            signed_d = d * DDDMath.sign(side)
            path_d = closest_d

        #Example
        #halfw = 2.5
        #bank_h = 2.0
        #bank_offset = 0.5

        #Golf
        halfw = 2.0
        bank_h = 2.0
        bank_offset = 0.5  # 0.5

        profile_path_factor = DDDMath.smoothstep_pulse(path_d, 14.0, 21.0, 22.0, 26.0)

        signed_d = DDDMath.clamp(signed_d, -halfw, halfw)

        d_norm = ((signed_d + (profile_path_factor * bank_offset)) / halfw)
        d_norm = d_norm ** 2
        h = d_norm * bank_h

        #print(signed_d, d, r, d_norm, h)
        h = h * profile_path_factor

        #return (x, y, z + h)
        return h