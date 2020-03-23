# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import random
import numpy as np

from shapely.geometry.polygon import LinearRing

from ddd.ddd import ddd

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

    def map_cubic(self, obj):
        result = obj.copy()
        if result.mesh:
            result.extra['uv'] = [None for idx, v in enumerate(result.mesh.vertices)]
            for face in result.mesh.faces:
                v1 = result.mesh.vertices[face[1]] - result.mesh.vertices[face[0]]
                v2 = result.mesh.vertices[face[2]] - result.mesh.vertices[face[0]]
                v = np.cross(v1, v2)
                v = v / np.linalg.norm(v)

                def setuv(face, idx, uv):
                    if result.extra['uv'][idx] != None:
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

        return result


    def map_spherical(self, obj):
        return self.map_cubic(obj)

    def map_cylindrical(self, obj):
        return self.map_cubic(obj)

    def map_xy(self, obj):
        raise NotImplementedError()

    #def map_wrap(self, obj):
    #    raise NotImplementedError

def map_2d_path(obj, path, line_x_offset=0.0):
    """
    Assigns UV coordinates to a shape for a line along a path.
    This method does not create a copy of objects, affecting the hierarchy.
    """

    def uv_apply_func(x, y, z, idx):
        # Find nearest point in path
        d = path.geom.project(ddd.point([x, y, z]).geom)
        #print(x, y, z, idx, d, path)
        p, segment_idx, segment_coords_a, segment_coords_b = path.interpolate_segment(d)
        pol = LinearRing([segment_coords_a, segment_coords_b, [x, y, z]])
        return (line_x_offset + (0.1 * (-1 if pol.is_ccw else 1)), d)

    result = obj
    if obj.geom:
        result.extra['uv'] = [uv_apply_func(v[0], v[1], 0.0, idx) for idx, v in enumerate(obj.geom.exterior.coords)]

    result.children = [map_2d_path(c, path) for c in obj.children]
    return result


def map_3d_from_2d(obj_3d, obj_2d):
    """
    Apply 2D UV coordinates to 3D shapes (using UV from closest point in 2D space).
    This method does not create a copy of objects.
    """

    def uv_apply_func(x, y, z, idx):
        # Find nearest point in shape, and return its height
        closest_uv = obj_2d.extra['uv'][0]
        closest_distsqr = float('inf')
        for idx, v in enumerate(obj_2d.geom.exterior.coords):
            point_2d = [v[0], v[1], 0]
            diff = [point_2d[0] - x, point_2d[1] - y]
            distsqr = (diff[0] ** 2) + (diff[1] ** 2)
            if (distsqr < closest_distsqr):
                closest_uv = obj_2d.extra['uv'][idx]
                closest_distsqr = distsqr
        #print (closest_uv)
        return closest_uv

    result = obj_3d
    if obj_3d.mesh:
        result.extra['uv'] = [uv_apply_func(v[0], v[1], v[2], idx) for idx, v in enumerate(obj_3d.mesh.vertices)]
    result.children = [map_3d_from_2d(c, obj_2d) for c in result.children]
    return result


