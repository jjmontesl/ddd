# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging
from ddd.ddd import ddd, DDDInstance
import math
from trimesh.base import Trimesh

# Get instance of logger for this module
logger = logging.getLogger(__name__)


class DDDMeshOps():
    """
    TODO: This module shall not be called "reduction", as it shall gather all meshops.
    """

    def reduce(self, obj):
        """
        Reduces an object to its convex hull.
        """
        result = obj.copy()
        # Currently reducing very simply
        if not result.children:
            try:
                result = result.convex_hull()
            except Exception as e:
                logger.error("Could not calculate convex hull for: %s", result)
        result.children = [self.reduce(c) for c in result.children]
        return result

    def reduce_bounds(self, obj):
        result = obj.copy()
        if not result.children:
            try:
                bounds = result.bounds()
                bounds = list(bounds[0]) + list(bounds[1])
                result.mesh = ddd.box(bounds).mesh
            except Exception as e:
                logger.error("Could not calculate bounding box for: %s", result)
                result.mesh = None
        result.children = [self.reduce_bounds(c) for c in result.children]
        return result

    def reduce_billboard(self, obj):
        raise NotImplementedError()


    def reduce_quadric_decimation(self, obj, target_ratio=None, target_faces=None):
        """
        Simplifies the mesh using quadratic decimation.

        This method modifies the current mesh.

        Currently implemented using Open3D (requires the dependency installed).
        """

        # TODO: Resolve the issue in docker:  OSError: libGL.so.1: cannot open shared object file: No such file or directory
        # or alternative try importing on load and store the result.
        import open3d

        if isinstance(obj, DDDInstance):
            logger.warn("Quadrid decimation of DDDInstance objects is not implemented. Ignoring object.")
            return obj

        elif obj.mesh:
            o3d_mesh = open3d.geometry.TriangleMesh()
            o3d_mesh.vertices = open3d.utility.Vector3dVector(obj.mesh.vertices)
            o3d_mesh.triangles = open3d.utility.Vector3iVector(obj.mesh.faces)
            #o3d_mesh.compute_vertex_normals()

            if target_ratio:
                target_faces = int(len(o3d_mesh.triangles) * target_ratio)

            o3d_result = o3d_mesh.simplify_quadric_decimation(target_number_of_triangles=target_faces)
            logger.info("Simplified object from %d to %d faces", len(o3d_mesh.triangles), len(o3d_result.triangles))
            obj.mesh.vertices  = o3d_result.vertices
            obj.mesh.faces = o3d_result.triangles

        obj.children = [self.reduce_quadric_decimation(c, target_ratio=target_ratio, target_faces=target_faces) for c in obj.children]

        return obj


    '''
        def subdivide_to_size_ind(self, vertices, faces, max_edge, max_iter=10):
            """
            Subdivide a mesh until every edge is shorter than a
            specified length.

            Will return a triangle soup, not a nicely structured mesh.

            Parameters
            ------------
            vertices : (n, 3) float
              Vertices in space
            faces : (m, 3) int
              Indices of vertices which make up triangles
            max_edge : float
              Maximum length of any edge in the result
            max_iter : int
              The maximum number of times to run subdivision

            Returns
            ------------
            vertices : (j, 3) float
              Vertices in space
            faces : (q, 3) int
              Indices of vertices
            """
            # store completed
            done_face = []
            done_vert = []

            # copy inputs and make sure dtype is correct
            current_faces = np.array(faces,
                                     dtype=np.int64,
                                     copy=True)
            current_vertices = np.array(vertices,
                                        dtype=np.float64,
                                        copy=True)

            # loop through iteration cap
            for i in range(max_iter + 1):
                # (n, 3, 3) float triangle soup
                triangles = current_vertices[current_faces]

                # compute the length of every triangle edge
                edge_lengths = (np.diff(triangles[:, [0, 1, 2, 0]],
                                        axis=1) ** 2).sum(axis=2) ** .5
                too_long = (edge_lengths > max_edge).any(axis=1)

                # clean up the faces a little bit so we don't
                # store a ton of unused vertices
                unique, inverse = np.unique(
                    current_faces[np.logical_not(too_long)],
                    return_inverse=True)

                # store vertices and faces meeting criteria
                done_vert.append(current_vertices[unique])
                done_face.append(inverse.reshape((-1, 3)))

                # met our goals so abort
                if not too_long.any():
                    break

                # run subdivision again
                (current_vertices,
                 current_faces) = subdivide(current_vertices,
                                            current_faces[too_long])

            # stack sequence into nice (n, 3) arrays
            vertices, faces = util.append_faces(done_vert,
                                                done_face)

            return vertices, faces
    '''

    def remove_faces_pointing(self, obj, direction, threshold=ddd.EPSILON):  #
        """
        Removes faces pointing in a given direction.

        This method modifies the object, and is applied to children recursively.
        """
        if obj.mesh:
            face_mask = [direction.dot(normal) < (1.0 - threshold) for normal in obj.mesh.face_normals]
            #print(obj.mesh.vertices.shape)
            obj.mesh.update_faces(face_mask)
            #print(obj.mesh.vertices.shape)
            obj = obj.clean()
            #obj.mesh.remove_degenerate_faces()
            #print(obj.mesh.vertices.shape)

        obj.children = [self.remove_faces_pointing(c, direction, threshold) for c in obj.children]

        return obj


    def subdivide_to_grid(self, grid_size=2.0, min_distance=0.1):
        """
        TODO: Not working. Not implemented.
        """
        result = self.copy()

        result.children = [c.subdivide_to_grid(max_edge, max_iter) for c in result.children]

        if result.mesh:
            vertices, faces = result.mesh.vertices, result.mesh.faces

            # For each face, calculate orientation and gridded triangles. Interpolate UVs and normals. Generalize.

            rvertices, rfaces = remesh.subdivide_to_size(vertices, faces, max_edge, max_iter=max_iter)

            result.mesh = Trimesh(rvertices, rfaces)

        return result


