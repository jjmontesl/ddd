# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import numpy as np
import logging
from ddd.ddd import ddd, DDDInstance, DDDObject2
import math
from trimesh.base import Trimesh
from trimesh import creation
from scipy import interpolate
from shapely.geometry import Polygon, polygon

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


    def subdivide_to_grid(self, obj, grid_size=2.0):  #, min_distance=0.1):
        """
        Subdivides a mesh ensuring that every face has vertices in the grid.

        TODO: optionally and by default flip in checkerboard (like grid3 does)
        TODO: Update UVs / normals.
        TODO: mention this method in the doc for DDDObject3.subdivide
        """
        result = obj.copy()

        result.children = [self.subdivide_to_grid(c, grid_size) for c in result.children]

        if result.mesh:
            newverts = []
            newfaces = []
            vertices, faces = result.mesh.vertices, result.mesh.faces

            for face in faces:

                vn1 = vertices[face[1]] - vertices[face[0]]
                vn2 = vertices[face[2]] - vertices[face[0]]
                # TODO: check trimesh.triangles.cross(triangles) as it may improve performance for the whole mesh
                vn = np.cross(vn1, vn2)

                vnorm = np.linalg.norm(vn)
                if vnorm == 0:
                    logger.error("Invalid triangle (linear dependent, no normal), in subdivide_to_grid(): %s", obj)
                    continue
                else:
                    vn = vn / vnorm

                # This is here even if only for debugging (core dumps have been observed when using this method, this may avoid some? -> no)
                planar_only = False
                if (planar_only and (abs(vn[0]) > abs(vn[1]) and abs(vn[0]) > abs(vn[2]) or
                    abs(vn[1]) > abs(vn[0]) and abs(vn[1]) > abs(vn[2]) or
                    vn[2] < 0.)):
                    newfaces.append([len(newverts), len(newverts) + 1, len(newverts) + 2])
                    newverts.extend([vertices[face[0]], vertices[face[1]], vertices[face[2]]])
                    continue

                v1 = vertices[face[0]]
                v2 = vertices[face[1]]
                v3 = vertices[face[2]]
                vnp = None

                # Project onto the XY plane (for shape operations) on a triplanar fashion
                if abs(vn[0]) > abs(vn[1]) and abs(vn[0]) > abs(vn[2]):
                    # Normal along X, project onto YZ (YZ onto XY)
                    v1 = v1[[1, 2, 0]]
                    v2 = v2[[1, 2, 0]]
                    v3 = v3[[1, 2, 0]]
                    vnp = vn[[1, 2, 0]]
                elif abs(vn[1]) > abs(vn[0]) and abs(vn[1]) > abs(vn[2]):
                    # Normal along Y, project onto XZ (XZ onto XY)
                    v1 = v1[[2, 0, 1]]
                    v2 = v2[[2, 0, 1]]
                    v3 = v3[[2, 0, 1]]
                    vnp = vn[[2, 0, 1]]
                else:
                    # Normal along Z, project onto XY (planar default)
                    vnp = vn

                # Get footprint
                triangle = ddd.polygon([v1, v2, v3]).remove_z()
                try:
                    triangle.validate()
                except Exception as e:
                    logger.warn("Invalid projected triangle face %s: %s", obj, e)
                    newfaces.append([len(newverts), len(newverts) + 1, len(newverts) + 2])
                    newverts.extend([vertices[face[0]], vertices[face[1]], vertices[face[2]]])
                    continue

                bounds = triangle.bounds()

                # Function of the plane to interpolate third axis
                # See: https://math.stackexchange.com/questions/753113/how-to-find-an-equation-of-the-plane-given-its-normal-vector-and-a-point-on-the
                oan = vnp.dot(v1)
                zfunc = lambda x, y: (oan - vnp[0] * x - vnp[1] * y) / vnp[2]

                # FIXME: this happens a lot
                #if vnp[2] < ddd.EPSILON:
                #    #logger.error("Cannot calculate z projection function for triangle subdivision: %s", obj)
                #    continue

                # Generate grid squares
                #bounds = [min(bounds[0], bounds[2]), min(bounds[1], bounds[3]), max(bounds[0], bounds[2]), max(bounds[1], bounds[3])]
                bounds = [grid_size * (int(bounds[0] / grid_size) - 1), grid_size * (int(bounds[1] / grid_size) - 1),
                          grid_size * (int(bounds[2] / grid_size) + 1), grid_size * (int(bounds[3] / grid_size) + 1)]
                grid2 = ddd.grid2(bounds, detail=grid_size, name=None)

                for geom in grid2.geom:
                    #flip = ((idi % 2) + (idj % 2)) % 2
                    geom = geom.intersection(triangle.geom)
                    if geom.type == 'Point' or geom.type == 'LineString' or geom.is_empty:
                        continue

                    # May be unnecessary, didn't solve the core dump issue
                    try:
                        ogeom = DDDObject2(geom=geom)
                        ogeom = ogeom.clean(eps=0)
                        ogeom.validate()
                        geom = ogeom.geom
                    except Exception as e:
                        continue

                    if geom is None:
                        # Was removed by cleaning or validation
                        continue

                    try:
                        geom = polygon.orient(geom, 1)  # orient polygon

                        #print(geom)
                        gvs, gfs = creation.triangulate_polygon(geom)

                        if len(gfs) == 0: continue

                        # Reproject to the original plane
                        if abs(vn[0]) > abs(vn[1]) and abs(vn[0]) > abs(vn[2]):
                            gvs = [[zfunc(v[0], v[1]), v[0], v[1]] for v in gvs]
                        elif abs(vn[1]) > abs(vn[0]) and abs(vn[1]) > abs(vn[2]):
                            gvs = [[v[1], zfunc(v[0], v[1]), v[0]] for v in gvs]
                        else:
                            gvs = [[v[0], v[1], zfunc(v[0], v[1])] for v in gvs]

                        flip = vnp[2] < 0
                        if flip:
                            gfs = np.flip(gfs)

                        gfs = gfs + len(newverts)

                        newfaces.extend(gfs)
                        newverts.extend(gvs)

                    except Exception as e:
                        logger.error("Could not triangulate triangle grid cell while subdividing to grid: %s", e)


            # Note: adding an empty mesh will cause export errors and failure to load in Babylon
            if (len(newfaces) > 0):
                result.mesh = Trimesh(newverts, newfaces)
                result.mesh.merge_vertices()
                #result.mesh.fix_normals()
            else:
                result.mesh = None

        return result

    def combine_group(self, root, key_func):
        """
        Note that this modifies the node tree.

        This maybe could be better done with a custom recursive function, maintaining
        strucure as much as possible (instead of flattening before combining as currently done).
        """

        # Flatten all objects. If this is not done, some objects are combined with children
        # incoprrectly before being processed.
        root.replace(root.flatten())

        # Retrieve keys
        keys = set()
        for o in root.recurse_objects()[1:]:
            key = key_func(o)
            if key:
                keys.add(key)

        # Combine objects by key
        added_objects = []

        for key in sorted(keys):
            objs = root.select(func=lambda o: key_func(o) == key)
            #root.select_remove(func=lambda o: key_func(o) == key)
            logger.debug("Combining %d objects by key: %s", len(objs.children), keys)

            instances = objs.select(func=lambda o: isinstance(o, DDDInstance), recurse=False)
            if len(instances.children) > 0:
                instances.name = "Combined instances: %s" % key
                objs.select_remove(func=lambda o: isinstance(o, DDDInstance))
                root.append(instances)
                added_objects.append(instances)

            for o in objs.recurse_objects()[1:]: o.children = []
            if len(objs.children) > 0:
                combined = objs.combine()
                combined.name = "Combined objects: %s" % key
                root.append(combined)
                added_objects.append(combined)

        # Remove objects
        for key in keys:
            root.select_remove(func=lambda o: key_func(o) == key and o not in added_objects)

        return root

    def combine_materials(self, root):
        """
        A convenience method to call `combine_group()` grouping by material name.
        """
        result = self.combine_group(root, lambda o: o.mat.name if o.mat else None)
        return result

