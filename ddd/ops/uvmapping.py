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


import random
import numpy as np

from shapely.geometry.polygon import LinearRing

from ddd.ddd import ddd
import logging
from ddd.core.exception import DDDException
import math


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class DDDUVMapping():

    def _setuv(self, face, idx, uv):
        """
        Helper function to set a UV on a mesh vertex
        """
        uv = (uv[0] * scale[0] + offset[0], uv[1] * scale[1] + offset[1])
        if split and result.extra['uv'][idx] != None and (result.extra['uv'][idx] != uv):
            # FIXME: Study and provide for when vertex should be duplicated (regarding UV and normals). Normals shall be calculated
            # before UV mapping as vertex may need to be duplicated (although an adequate mapping would also reduce this)
            newidx = len(result.mesh.vertices)
            result.mesh.vertices = np.array(list(result.mesh.vertices) + [result.mesh.vertices[idx]])
            if face[0] == idx: face[0] = newidx
            if face[1] == idx: face[1] = newidx
            if face[2] == idx: face[2] = newidx
            result.extra['uv'].append(uv)
            #raise ValueError("Cannot map same vertex twice in cubic mapping.")
        else:
            result.extra['uv'][idx] = uv


    def map_random(self, obj_3d):
        """
        Assigns UV coordinates at random.
        This method does not create a copy of objects, affecting the hierarchy.
        """
        result = obj_3d
        result.extra['uv'] = [(random.uniform(0, 1), random.uniform(0, 1)) for v in result.mesh.vertices]
        result.children = [self.map_3d_random(c) for c in result.children]
        return result

    # FIXME: Try to change default mapping of children to false? (seems a more sensible default) and normalize offset, scale order
    def map_cubic(self, obj, offset=None, scale=None, split=True, children=True):
        """
        FIXME: Study and provide for when vertex should be duplicated (regarding UV and normals). Normals shall be calculated
        before UV mapping as vertex may need to be duplicated (although an adequate mapping would also reduce this)
        """

        if offset is None: offset = (0, 0)
        if scale is None: scale = (1, 1)

        result = obj.copy()
        if result.mesh:

            '''
            # Inform/Avoid remapping (?)
            if result.extra.get('uv', None):
                logger.debug("Object already has UV coordinates: %s", result)
                #raise DDDException("Object already has UV coordinates: %s" % result)
            '''

            result.extra['uv'] = [None for idx, v in enumerate(result.mesh.vertices)]
            #logger.debug("UV mapping object: %s", obj)
            for face in result.mesh.faces:
                v1 = result.mesh.vertices[face[1]] - result.mesh.vertices[face[0]]
                v2 = result.mesh.vertices[face[2]] - result.mesh.vertices[face[0]]
                v = np.cross(v1, v2)

                vnorm = np.linalg.norm(v)
                if vnorm == 0:
                    logger.error("Invalid triangle (linear dependent, no normal): %s", obj)
                else:
                    v = v / vnorm

                def setuv(face, idx, uv):
                    uv = (uv[0] * scale[0] + offset[0], uv[1] * scale[1] + offset[1])
                    if split and result.extra['uv'][idx] != None and (result.extra['uv'][idx] != uv):
                        # FIXME: Study and provide for when vertex should be duplicated (regarding UV and normals). Normals shall be calculated
                        # before UV mapping as vertex may need to be duplicated (although an adequate mapping would also reduce this)
                        newidx = len(result.mesh.vertices)
                        result.mesh.vertices = np.array(list(result.mesh.vertices) + [result.mesh.vertices[idx]])
                        if face[0] == idx: face[0] = newidx
                        if face[1] == idx: face[1] = newidx
                        if face[2] == idx: face[2] = newidx
                        result.extra['uv'].append(uv)
                        #raise ValueError("Cannot map same vertex twice in cubic mapping.")
                    else:
                        result.extra['uv'][idx] = uv

                NORM_THRESHOLD = 0.00001

                if abs(v[0]) > (abs(v[1]) - NORM_THRESHOLD) and abs(v[0]) > (abs(v[2]) - NORM_THRESHOLD):
                    # Normal along X, project onto YZ
                    p0, p1, p2 = result.mesh.vertices[face[0]], result.mesh.vertices[face[1]], result.mesh.vertices[face[2]]
                    setuv(face, face[0], (p0[1], p0[2]))
                    setuv(face, face[1], (p1[1], p1[2]))
                    setuv(face, face[2], (p2[1], p2[2]))
                elif abs(v[1]) > (abs(v[0]) - NORM_THRESHOLD) and abs(v[1]) > (abs(v[2]) - NORM_THRESHOLD):
                    p0, p1, p2 = result.mesh.vertices[face[0]], result.mesh.vertices[face[1]], result.mesh.vertices[face[2]]
                    setuv(face, face[0], (p0[0], p0[2]))
                    setuv(face, face[1], (p1[0], p1[2]))
                    setuv(face, face[2], (p2[0], p2[2]))
                else:
                    p0, p1, p2 = result.mesh.vertices[face[0]], result.mesh.vertices[face[1]], result.mesh.vertices[face[2]]
                    setuv(face, face[0], (p0[0], p0[1]))
                    setuv(face, face[1], (p1[0], p1[1]))
                    setuv(face, face[2], (p2[0], p2[1]))

        if children:
            result.children = [self.map_cubic(c, offset, scale, split=split, children=children) for c in result.children]

        return result

    # FIXME: Try to change default mapping of children to false? (seems a more sensible default) and normalize offset, scale order
    def map_spherical(self, obj, offset=None, scale=None, split=True, children=True):
        """
        Uses a vertical cylinder centered on (0, 0).

        TODO: "split" does not apply here, check and remove
        TODO: use numpy for all vertices at once, see https://stackoverflow.com/questions/4116658/faster-numpy-cartesian-to-spherical-coordinate-conversion
        """
        if scale is None: scale = (1, 1)
        if offset is None: offset = (0, 0)

        result = obj.copy()
        if result.mesh:

            result.extra['uv'] = [None for idx, v in enumerate(result.mesh.vertices)]

            #logger.debug("UV mapping object: %s", obj)
            for face in result.mesh.faces:
                v1 = result.mesh.vertices[face[1]] - result.mesh.vertices[face[0]]
                v2 = result.mesh.vertices[face[2]] - result.mesh.vertices[face[0]]
                v = np.cross(v1, v2)

                vnorm = np.linalg.norm(v)
                if vnorm == 0:
                    logger.error("Invalid triangle (linear dependent, no normal): %s", obj)
                else:
                    v = v / vnorm

                def setuv(face, idx, uv):
                    uv = (uv[0] * scale[0] + offset[0], uv[1] * scale[1] + offset[1])
                    if split and result.extra['uv'][idx] != None and (result.extra['uv'][idx] != uv):
                        # FIXME: Study and provide for when vertex should be duplicated (regarding UV and normals). Normals shall be calculated
                        # before UV mapping as vertex may need to be duplicated (although an adequate mapping would also reduce this)
                        newidx = len(result.mesh.vertices)
                        result.mesh.vertices = np.array(list(result.mesh.vertices) + [result.mesh.vertices[idx]])
                        if face[0] == idx: face[0] = newidx
                        if face[1] == idx: face[1] = newidx
                        if face[2] == idx: face[2] = newidx
                        result.extra['uv'].append(uv)
                        #raise ValueError("Cannot map same vertex twice in cubic mapping.")
                    else:
                        result.extra['uv'][idx] = uv

                # From: https://stackoverflow.com/questions/4116658/faster-numpy-cartesian-to-spherical-coordinate-conversion
                def cart2sph(x,y,z):
                    XsqPlusYsq = x**2 + y**2
                    r = math.sqrt(XsqPlusYsq + z**2)               # r
                    elev = math.atan2(z,math.sqrt(XsqPlusYsq))     # theta
                    az = math.atan2(y,x)                           # phi
                    return r, elev, az

                # Map sphere
                p0, p1, p2 = result.mesh.vertices[face[0]], result.mesh.vertices[face[1]], result.mesh.vertices[face[2]]
                r0, theta0, phi0 = cart2sph(*p0)
                r1, theta1, phi1 = cart2sph(*p1)
                r2, theta2, phi2 = cart2sph(*p2)
                setuv(face, face[0], (0.5 + (phi0 / (math.pi * 2)), 0.5 + theta0 / (math.pi * 1)))
                setuv(face, face[1], (0.5 + (phi1 / (math.pi * 2)), 0.5 + theta1 / (math.pi * 1)))
                setuv(face, face[2], (0.5 + (phi2 / (math.pi * 2)), 0.5 + theta2 / (math.pi * 1)))

        if children:
            result.children = [self.map_spherical(c, offset, scale, split=split, children=children) for c in result.children]

        return result

    # FIXME: Try to change default mapping of children to false? (seems a more sensible default) and normalize offset, scale order
    def map_cylindrical(self, obj, scale=None, offset=None, split=True, children=True):
        """
        Uses a vertical cylinder centered on (0, 0).
        """
        if scale is None: scale = (1, 1)
        if offset is None: offset = (0, 0)

        result = obj.copy()
        if result.mesh:

            result.extra['uv'] = [None for idx, v in enumerate(result.mesh.vertices)]
            #logger.debug("UV mapping object: %s", obj)
            for face in result.mesh.faces:
                v1 = result.mesh.vertices[face[1]] - result.mesh.vertices[face[0]]
                v2 = result.mesh.vertices[face[2]] - result.mesh.vertices[face[0]]
                v = np.cross(v1, v2)

                vnorm = np.linalg.norm(v)
                if vnorm == 0:
                    logger.error("Invalid triangle (linear dependent, no normal): %s", obj)
                else:
                    v = v / vnorm

                def setuv(face, idx, uv):
                    uv = (uv[0] * scale[0] + offset[0], uv[1] * scale[1] + offset[1])
                    if split and result.extra['uv'][idx] != None and (result.extra['uv'][idx] != uv):
                        # FIXME: Study and provide for when vertex should be duplicated (regarding UV and normals). Normals shall be calculated
                        # before UV mapping as vertex may need to be duplicated (although an adequate mapping would also reduce this)
                        newidx = len(result.mesh.vertices)
                        result.mesh.vertices = np.array(list(result.mesh.vertices) + [result.mesh.vertices[idx]])
                        if face[0] == idx: face[0] = newidx
                        if face[1] == idx: face[1] = newidx
                        if face[2] == idx: face[2] = newidx
                        result.extra['uv'].append(uv)
                        #raise ValueError("Cannot map same vertex twice in cubic mapping.")
                    else:
                        result.extra['uv'][idx] = uv

                if abs(v[2]) > abs(v[0]) and abs(v[2]) > abs(v[1]):
                    # Normal along Z, project onto X (caps)
                    p0, p1, p2 = result.mesh.vertices[face[0]], result.mesh.vertices[face[1]], result.mesh.vertices[face[2]]
                    setuv(face, face[0], (p0[0], p0[1]))
                    setuv(face, face[1], (p1[0], p1[1]))
                    setuv(face, face[2], (p2[0], p2[1]))
                else:
                    # Map cylinder
                    p0, p1, p2 = result.mesh.vertices[face[0]], result.mesh.vertices[face[1]], result.mesh.vertices[face[2]]
                    angle0, angle1, angle2 = math.atan2(p0[1], p0[0]), math.atan2(p1[1], p1[0]), math.atan2(p2[1], p2[0])
                    setuv(face, face[0], (angle0 / (math.pi * 2), p0[2]))
                    setuv(face, face[1], (angle1 / (math.pi * 2), p1[2]))
                    setuv(face, face[2], (angle2 / (math.pi * 2), p2[2]))

        if children:
            result.children = [self.map_cylindrical(c, scale, offset, split=split, children=children) for c in result.children]
            
        return result

    def map_xy(self, obj):
        raise NotImplementedError()

    #def map_wrap(self, obj):
    #    raise NotImplementedError


    def map_2d_linear(self, obj):
        """
        Maps UV coordinates on a DDDObject2 geometry (eg. polygons).
        """

        def uv_apply_func(x, y, z, idx):
            return (x, y)

        result = obj
        if obj.geom:
            if obj.geom.geom_type == "MultiPolygon":
                logger.error("Geometry to map 2D path to does not have exterior coordinates: %s" % obj)
            elif obj.geom.exterior:
                result.extra['uv'] = [uv_apply_func(v[0], v[1], 0.0, idx) for idx, v in enumerate(obj.geom.exterior.coords)]
            else:
                logger.error("Geometry to map 2D path to does not have exterior coordinates: %s" % obj)

        result.children = [self.map_2d_linear(c) for c in obj.children]
        return result


def map_2d_path(obj, path, line_x_offset=0.0, line_x_width=0.1, line_d_offset=0.0, line_d_scale=1.0):
    """
    Assigns UV coordinates to a 2D shape for a line along a 2D path.
    This method does not create a copy of objects, affecting the hierarchy.
    """

    def uv_apply_func(x, y, z, idx):
        # Find nearest point in path
        d = path.geom.project(ddd.point([x, y, z]).geom)
        #print(x, y, z, idx, d, path)
        interpolate_result = path.interpolate_segment(d)
        if interpolate_result:
            p, segment_idx, segment_coords_a, segment_coords_b = interpolate_result
            pol = LinearRing([segment_coords_a, segment_coords_b, [x, y, z]])
            return (line_x_offset + (line_x_width * (-1 if pol.is_ccw else 1)), (d * line_d_scale) + line_d_offset)
        else:
            logger.error("Cannot interpolate segment: %s", path)
            return (line_x_offset, d)

    result = obj
    if obj.geom:
        if obj.geom.geom_type == "MultiPolygon":
            logger.error("Geometry to map 2D path to does not have exterior coordinates: %s" % obj)
        elif obj.geom.exterior:
            result.extra['uv'] = [uv_apply_func(v[0], v[1], 0.0, idx) for idx, v in enumerate(obj.geom.exterior.coords)]
        else:
            logger.error("Geometry to map 2D path to does not have exterior coordinates: %s" % obj)

    result.children = [map_2d_path(c, path) for c in obj.children]
    return result



def map_3d_from_2d(obj_3d, obj_2d):
    """
    Apply 2D UV coordinates to 3D shapes (using UV from closest point in 2D space).
    This method does not create a copy of objects.
    """

    def uv_apply_func(x, y, z, idx):
        # Find nearest point in shape (or children), and return its height
        closest_o, closest_d = obj_2d.closest(ddd.point([x, y]))
        closest_uv = None
        closest_distsqr = float('inf')
        if closest_o.extra.get('uv', None):
            for idx, v in enumerate(closest_o.geom.exterior.coords):
                point_2d = [v[0], v[1], 0]
                diff = [point_2d[0] - x, point_2d[1] - y]
                distsqr = (diff[0] ** 2) + (diff[1] ** 2)
                if (distsqr < closest_distsqr):
                    closest_uv = closest_o.extra['uv'][idx]
                    closest_distsqr = distsqr
        else:
            logger.error("Closest object has no UV mapping: %s (%s) (obj_2d=%s, obj_3d=%s)", closest_o, closest_o.extra.get('uv', None), obj_2d, obj_3d)
            raise DDDException("Closest object has no UV mapping: %s (%s)" % (closest_o, closest_o.extra.get('uv', None)), ddd_obj=obj_3d)

        if closest_uv is None:
            logger.error("Error mapping 3D from 2D (3d=%s, 2d=%s %s %s)", obj_3d, obj_2d, obj_2d.geom, [x.geom for x in obj_2d.children])
            raise DDDException("Could not map 3D from 2D (no closest vertex found): %s" % obj_3d, ddd_obj=obj_3d)

        return closest_uv

    result = obj_3d
    if result.mesh:
        result.extra['uv'] = [uv_apply_func(v[0], v[1], v[2], idx) for idx, v in enumerate(result.mesh.vertices)]
    result.children = [map_3d_from_2d(c, obj_2d) for c in result.children]
    return result


