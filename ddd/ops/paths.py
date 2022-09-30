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
import numpy as np

import trimesh
from ddd.curves.arc import DDDArcCurve
from ddd.curves.bezier import DDDBezierCurve
from ddd.math.vector3 import Vector3
from ddd.nodes.node3 import DDDNode3
from ddd.nodes.path3 import DDDPath3
from ddd.math.math import DDDMath
from ddd.ddd import ddd


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class DDDPathOps():
    """
    """

    def from_points_spline(self, line):
        """
        Uses trimesh.path.simplify.points_to_spline_entity to generate a Spline from the given points.
        The distance between points has an impact on the resulting spline.
        Returns a DDDPath3 object.
        """
        result = DDDPath3()
        entity, control = trimesh.path.simplify.points_to_spline_entity(list(line.geom.coords), smooth=0.5)  # , count=None)
        result.path3 = trimesh.path.path.Path3D([entity], control)
        return result

    def from_points_heuristic(self, line, distance=1.0):
        """
        Generates a DDDPath3 object from the given LineString (which can have Z coordinates).

        The heuristics are:
        - Straight segments (longer than `distance` are kept as Line segments)
        """
        result = DDDPath3()

        entities = []
        vertices = []

        vertices.append(line.geom.coords[0])

        for i in range(len(line.geom.coords) - 1):
            v0 = Vector3(line.geom.coords[i])
            v1 = Vector3(line.geom.coords[i + 1])
            d = v1 - v0
            #print (d.length(), distance)
            if d.length() > distance:
                vertices.append(v1)
                entities.append(trimesh.path.entities.Line((len(vertices) - 2, len(vertices) - 1)))
            else:
                vm1 = Vector3(line.geom.coords[i - 1])
                v2 = Vector3(line.geom.coords[i + 2])
                dm1 = v0 - vm1
                d2 = v2 - v1

                bs0 = (dm1.normalized() + d.normalized()).normalized()
                bs1 = (d.normalized() + d2.normalized()).normalized()

                l = d.length()
                #c0 = v0 + dm1.normalized() * l  * (0.55228 * 0.70710678118)  # 0.55... is the constant for bezier best fit of arcs (see ref)
                #c1 = v1 - d2.normalized() * l * (0.55228 * 0.70710678118)  # 0.55... is the constant for bezier best fit of arcs (see ref)
                c0 = v0 + bs0 * l * (0.55228 * 0.70710678118)  # 0.55... is the constant for bezier best fit of arcs (see ref)
                c1 = v1 - bs1 * l * (0.55228 * 0.70710678118)  # 0.55... is the constant for bezier best fit of arcs (see ref)
                vertices.append(c0)
                vertices.append(c1)
                vertices.append(v1)
                entities.append(trimesh.path.entities.Bezier((len(vertices) - 4, len(vertices) - 3, len(vertices) - 2, len(vertices) - 1)))

        result.path3 = trimesh.path.path.Path3D(entities, vertices)

        return result

    def path_to_arcs(self, path, tolerance=0.01):
        """
        Generates a list of arcs from the given path.
        The arcs are generated by trimesh.path.path.Path3D.arcs.
        """
        result = path.copy()

        coords = []
        entities = []

        for entity in path.path3.entities:
            if not coords:
                last_p = path.path3.vertices[entity.points[0]]
                coords.append(last_p)

            if isinstance(entity, trimesh.path.entities.Line):
                for p in entity.points[1:]:
                    last_p = path.path3.vertices[p]
                    coords.append(last_p)
                entities.append(trimesh.path.entities.Line(range(len(coords) - len(entity.points), len(coords))))

            elif isinstance(entity, trimesh.path.entities.Bezier):

                entity_path_arcs = self.bezier_to_arcs(entity, path.path3.vertices, tolerance=tolerance)

                for arc in entity_path_arcs.entities:
                    for p in arc.points:
                        last_p = entity_path_arcs.vertices[p]
                        coords.append(last_p)
                    entities.append(trimesh.path.entities.Arc(range(len(coords) - len(arc.points), len(coords))))

            else:
                raise NotImplementedError(entity)

        result.path3 = trimesh.path.path.Path3D(entities, coords)
        print(result.path3)
        return result

    def bezier_to_arcs(self, entity, vertices, tolerance=0.01):
        """
        From: https://pomax.github.io/bezierinfo/#arcapproximation
        """

        # Dirty quick:
        #return trimesh.path.path.Path3D([trimesh.path.entities.Arc([0, 1, 2])], [vertices[entity.points[0]], vertices[entity.points[1]], vertices[entity.points[-1]]])

        bezier_curve = DDDBezierCurve([vertices[i] for i in entity.points])

        ts = 0
        te = 0
        n = 1.0

        entities = []
        vertices = []

        while te < 1.0:

            previous_valid = None
            is_valid = False

            while not ((not is_valid and previous_valid) or (is_valid and te >= 1.0)):

                previous_valid = is_valid

                if not is_valid:
                    n = n / 2
                else:
                    n = n + n / 2

                n = DDDMath.clamp(n, 0.0, (1.0 - ts) / 2)

                tm = ts + n
                te = ts + 2 * n

                e1 = ts + n / 2
                e2 = ts + n + n / 2

                ps, pm, pe, pe1, pe2 = bezier_curve.evaluate(np.array([ts, tm, te, e1, e2]))
                arc_curve = DDDArcCurve.from_points((ps, pm, pe))

                error1 = abs(arc_curve.radius - np.linalg.norm(pe1 - arc_curve.center))
                error2 = abs(arc_curve.radius - np.linalg.norm(pe2 - arc_curve.center))
                error = error1 + error2
                #print(ts, te, error, arc_curve.radius)

                is_valid = error < tolerance

            vertices.extend([ps, pm, pe])
            entities.append(trimesh.path.entities.Arc(list(range(len(vertices) - 3, len(vertices)))))

            #print("Next arc")

            ts = te
            n = (1.0 - ts) * 0.5

        arcs = trimesh.path.path.Path3D(entities, vertices)
        return arcs


    def round_corners(self, line, distance=1.0, angle_min=0):
        """
        Generates a DDDPath3 object from the given LineString (which can have Z coordinates),
        rounding corners

        The heuristics are:
        - Straight segments (longer than `distance` are kept as Line segments)
        - Shorter segments are aproximated with a Bezier
        """
        result = DDDPath3()

        entities = []
        vertices = []

        vertices.append(line.geom.coords[0])

        for i in range(1, len(line.geom.coords) - 1):
            v0 = Vector3(line.geom.coords[i - 1])
            v1 = Vector3(line.geom.coords[i])
            v2 = Vector3(line.geom.coords[i + 1])

            s0 = v1 - v0
            s1 = v2 - v1

            angle = s0.angle(s1)

            #print (d.length(), distance)
            if angle < angle_min:
                vertices.append(v1)
                entities.append(trimesh.path.entities.Line((len(vertices) - 2, len(vertices) - 1)))
            else:

                l0 = s0.length()
                l1 = s1.length()

                d0 = s0.normalized()
                d1 = s1.normalized()

                # Redude distance if it's longer
                distance0 = min(distance, l0 / 2)
                distance1 = min(distance, l1 / 2)

                p0 = v1 - d0 * distance0
                p1 = v1 + d1 * distance1

                c0 = p0 + d0 * distance0 * (0.55228 * 0.70710678118)
                c1 = p1 - d1 * distance1 * (0.55228 * 0.70710678118)

                vertices.append(p0)
                entities.append(trimesh.path.entities.Line((len(vertices) - 2, len(vertices) - 1)))

                vertices.append(c0)
                vertices.append(c1)
                vertices.append(p1)
                entities.append(trimesh.path.entities.Bezier((len(vertices) - 4, len(vertices) - 3, len(vertices) - 2, len(vertices) - 1)))

        # Final line segment
        vertices.append(line.geom.coords[-1])
        entities.append(trimesh.path.entities.Line((len(vertices) - 2, len(vertices) - 1)))

        result.path3 = trimesh.path.path.Path3D(entities, vertices)

        return result
