# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging
from ddd.ddd import ddd
import math

# Get instance of logger for this module
logger = logging.getLogger(__name__)


class DDDMeshOps():

    def reduce(self, obj):
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
