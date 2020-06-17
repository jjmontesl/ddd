# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import random
import numpy as np

from shapely.geometry.polygon import LinearRing

from ddd.ddd import ddd
import logging
from ddd.core.exception import DDDException


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class DDDUVMapping():

    def map_random(self, obj_3d):
        """
        Assigns UV coordinates at random.
        This method does not create a copy of objects, affecting the hierarchy.
        """
        result = obj_3d
        result.extra['uv'] = [(random.uniform(0, 1), random.uniform(0, 1)) for v in result.mesh.vertices]
        result.children = [self.map_3d_random(c) for c in result.children]
        return result

    def map_cubic(self, obj, offset=None, scale=None):
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
            for face in result.mesh.faces:
                v1 = result.mesh.vertices[face[1]] - result.mesh.vertices[face[0]]
                v2 = result.mesh.vertices[face[2]] - result.mesh.vertices[face[0]]
                v = np.cross(v1, v2)
                v = v / np.linalg.norm(v)

                def setuv(face, idx, uv):
                    uv = (uv[0] * scale[0] + offset[0], uv[1] * scale[1] + offset[1])
                    if result.extra['uv'][idx] != None:
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

                if abs(v[0]) > abs(v[1]) and abs(v[0]) > abs(v[2]):
                    p0, p1, p2 = result.mesh.vertices[face[0]], result.mesh.vertices[face[1]], result.mesh.vertices[face[2]]
                    setuv(face, face[0], (p0[1], p0[2]))
                    setuv(face, face[1], (p1[1], p1[2]))
                    setuv(face, face[2], (p2[1], p2[2]))
                elif abs(v[1]) > abs(v[0]) and abs(v[1]) > abs(v[2]):
                    p0, p1, p2 = result.mesh.vertices[face[0]], result.mesh.vertices[face[1]], result.mesh.vertices[face[2]]
                    setuv(face, face[0], (p0[0], p0[2]))
                    setuv(face, face[1], (p1[0], p1[2]))
                    setuv(face, face[2], (p2[0], p2[2]))
                else:
                    p0, p1, p2 = result.mesh.vertices[face[0]], result.mesh.vertices[face[1]], result.mesh.vertices[face[2]]
                    setuv(face, face[0], (p0[0], p0[1]))
                    setuv(face, face[1], (p1[0], p1[1]))
                    setuv(face, face[2], (p2[0], p2[1]))

        result.children = [self.map_cubic(c, offset, scale) for c in result.children]
        return result

    def map_spherical(self, obj):
        return self.map_cubic(obj)

    def map_cylindrical(self, obj):
        return self.map_cubic(obj)

    def map_xy(self, obj):
        raise NotImplementedError()

    #def map_wrap(self, obj):
    #    raise NotImplementedError

def map_2d_path(obj, path, line_x_offset=0.0, line_x_width=0.1):
    """
    Assigns UV coordinates to a shape for a line along a path.
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
            return (line_x_offset + (line_x_width * (-1 if pol.is_ccw else 1)), d)
        else:
            logger.error("Cannot interpolate segment: %s", path)
            return (line_x_offset, d)

    result = obj
    if obj.geom:
        if obj.geom.type == "MultiPolygon":
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


