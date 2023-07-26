# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging

import numpy as np
from ddd.ddd import ddd
from shapely.geometry import Polygon, polygon
from trimesh import creation, intersections

from ddd.nodes.node2 import DDDObject2
from ddd.nodes.instance import DDDInstance

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


    def remove_faces_pointing(self, obj, direction, threshold=ddd.EPSILON):  #
        """
        Removes faces pointing in a given direction.

        Threshold of 1.0 means a dot product up to 180 degrees.

        This method modifies the object, and is applied to children recursively.
        """
        if obj.mesh:
            face_mask = [direction.dot(normal) < (1.0 - threshold) for normal in obj.mesh.face_normals]
            #print(obj.mesh.vertices.shape)
            obj.mesh.update_faces(face_mask)
            #print(obj.mesh.vertices.shape)
            obj = obj.merge_vertices().clean()
            #obj.mesh.remove_degenerate_faces()
            #print(obj.mesh.vertices.shape)

        obj.children = [self.remove_faces_pointing(c, direction, threshold) for c in obj.children]

        return obj

    def filter_faces_func(self, obj, func):
        if obj.mesh:
            face_mask = [func(idx, face, obj.mesh.face_normals[idx]) for idx, face in enumerate(obj.mesh.faces)]
            #print(obj.mesh.vertices.shape)
            obj.mesh.update_faces(face_mask)
            #print(obj.mesh.vertices.shape)
            obj = obj.merge_vertices().clean()
            #obj.mesh.remove_degenerate_faces()
            #print(obj.mesh.vertices.shape)

        obj.children = [self.remove_faces_pointing(c, obj, func) for c in obj.children]

        return obj

    def interpolate_uv(self, f, p1, p2, p3, uv1, uv2, uv3):
        # From: https://answers.unity.com/questions/383804/calculate-uv-coordinates-of-3d-point-on-plane-of-m.html
        # Calculate vectors from point f to vertices p1, p2 and p3:

        #ddd.trace(locals())

        f1 = p1 - f
        f2 = p2 - f
        f3 = p3 - f

        # Calculate the areas and factors (order of parameters doesn't matter):
        a = np.linalg.norm(np.cross(p1-p2, p1-p3))  # main triangle area a
        a1 = np.linalg.norm(np.cross(f2, f3)) / a  # p1's triangle area / a
        a2 = np.linalg.norm(np.cross(f3, f1)) / a  # p2's triangle area / a
        a3 = np.linalg.norm(np.cross(f1, f2)) / a  # p3's triangle area / a

        # Find the uv corresponding to point f (uv1/uv2/uv3 are associated to p1/p2/p3):
        uv = np.array(uv1) * a1 + np.array(uv2) * a2 + np.array(uv3) * a3;

        return uv

    def subdivide_to_grid(self, obj, grid_size=2.0):  #, min_distance=0.1):
        """
        Subdivides a mesh ensuring that every face has vertices in the grid.

        TODO: Update UVs / normals.
        TODO: mention this method in the doc for DDDObject3.subdivide
        TODO: optionally and by default flip in checkerboard (like grid3 does)
        """
        result = obj.copy()

        result.children = [self.subdivide_to_grid(c, grid_size) for c in result.children]

        if result.mesh:
            newverts = []
            newfaces = []
            newuvs = []
            vertices, faces = result.mesh.vertices, result.mesh.faces
            uvs = result.get('uv', None)

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
                PROJECT_NORM_THRESHOLD = 0.00001

                if abs(vn[0]) > (abs(vn[1]) - PROJECT_NORM_THRESHOLD) and abs(vn[0]) > (abs(vn[2]) - PROJECT_NORM_THRESHOLD):
                    # Normal along X, project onto YZ (YZ onto XY)
                    v1 = v1[[1, 2, 0]]
                    v2 = v2[[1, 2, 0]]
                    v3 = v3[[1, 2, 0]]
                    vnp = vn[[1, 2, 0]]
                elif abs(vn[1]) > (abs(vn[0]) - PROJECT_NORM_THRESHOLD) and abs(vn[1]) > (abs(vn[2]) - PROJECT_NORM_THRESHOLD):
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
                bounds = [[grid_size * (int(bounds[0][0] / grid_size) - 1), grid_size * (int(bounds[0][1] / grid_size) - 1), 0],
                          [grid_size * (int(bounds[1][0] / grid_size) + 1), grid_size * (int(bounds[1][1] / grid_size) + 1), 0]]
                grid2 = ddd.grid2(bounds, detail=grid_size, name=None)

                for geom in grid2.geom.geoms:
                    #flip = ((idi % 2) + (idj % 2)) % 2
                    geom = geom.intersection(triangle.geom)
                    if geom.geom_type == 'Point' or geom.geom_type == 'LineString' or geom.is_empty:
                        continue

                    # May be unnecessary, didn't solve the core dump issue
                    try:
                        ogeom = DDDObject2(geom=geom)
                        ogeom = ogeom.clean(eps=0)
                        ogeom.validate()
                        geom = ogeom.geom
                    except Exception as e:
                        logger.info("Invlaid geometry produced while subdividing to grid: %s", obj)
                        continue

                    if geom is None:
                        # Was removed by cleaning or validation
                        continue

                    try:
                        geom = ddd.shape(geom).remove_z().geom
                        geom = polygon.orient(geom, 1)  # orient polygon

                        #print(geom)
                        gvs, gfs = creation.triangulate_polygon(geom)

                        if len(gfs) == 0: continue

                        # Reproject to the original plane
                        if abs(vn[0]) > (abs(vn[1]) - PROJECT_NORM_THRESHOLD) and abs(vn[0]) > (abs(vn[2]) - PROJECT_NORM_THRESHOLD):
                            gvs = [[zfunc(v[0], v[1]), v[0], v[1]] for v in gvs]
                        elif abs(vn[1]) > (abs(vn[0]) - PROJECT_NORM_THRESHOLD) and abs(vn[1]) > (abs(vn[2]) - PROJECT_NORM_THRESHOLD):
                            gvs = [[v[1], zfunc(v[0], v[1]), v[0]] for v in gvs]
                        else:
                            gvs = [[v[0], v[1], zfunc(v[0], v[1])] for v in gvs]

                        flip = vnp[2] < 0
                        if flip:
                            gfs = np.flip(gfs)

                        gfs = gfs + len(newverts)

                        newfaces.extend(gfs)
                        newverts.extend(gvs)

                        if uvs:
                            (uv1, uv2, uv3) = (uvs[face[0]], uvs[face[1]], uvs[face[2]])
                            (p1, p2, p3) = (vertices[face[0]], vertices[face[1]], vertices[face[2]])
                            for gv in gvs:
                                nuv = self.interpolate_uv(gv, p1, p2, p3, uv1, uv2, uv3)
                                newuvs.append(nuv)

                    except Exception as e:
                        logger.error("Could not triangulate triangle grid cell while subdividing to grid: %s", e)
                        continue


            # Note: adding an empty mesh will cause export errors and failure to load in Babylon
            if (len(newfaces) > 0):
                #result.mesh = Trimesh(newverts, newfaces)  # removed as this was merging vertices
                result.mesh.vertices = newverts
                result.mesh.faces = newfaces

                if uvs:
                    result.set('uv', newuvs)

                result.mesh.merge_vertices()  # This may need to be optional, by I think it's a sane default

                #result.mesh.fix_normals()
            else:
                result.mesh = None

        return result

    def slice_plane(self, obj, plane_normal, plane_origin):
        """
        Slices a mesh using a plane, and keeps the half on the positive side.

        TODO: This is not considering UVs and normals.
        """

        result = obj.copy()

        result.children = [self.slice_plane(c) for c in result.children]

        if result.mesh:
            mesh = intersections.slice_mesh_plane(
                result.mesh, plane_normal, plane_origin, cap=False, cached_dots=None)
            result.mesh = mesh

        return result

    def batch_group(self, root, key_func):
        """
        Walks a node tree grouping nodes using the provided "key_function" callback,
        then combines each group.

        WARN: this has been seen to fail (leave repeated geometry) when the root object contains geometry, while this is not
              fixed, client code is advised to create a group and to doublecheck for repeated/unbatched geometry.
              This has seen to happen when the root node (even if with no geometry) has a material.

        Note that this modifies the node tree.

        This maybe could be better done with a custom recursive function, maintaining
        structure as much as possible (instead of flattening before combining as currently done) ?
        """

        # Flatten all objects. If this is not done, some objects are batched with children
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

            # Selects obejcts to combine by group key (ignores objects with children, as root was flattened and targets should have no children)
            objs = root.select(func=lambda o: o != root and not o.children and key_func(o) == key)

            #root.select_remove(func=lambda o: key_func(o) == key)
            logger.debug("Combining %d objects by key: %s", len(objs.children), key)

            instances = objs.select(func=lambda o: isinstance(o, DDDInstance), recurse=False)
            if len(instances.children) > 0:
                instances.name = "Batched Inst: %s" % key
                objs.select_remove(func=lambda o: isinstance(o, DDDInstance))
                root.append(instances)
                added_objects.append(instances)

            # Dangerous: this clears the batched root when processing the key "None_False" (which selects the root node and clears it)
            # FIXME: why is this line here at all?
            for o in objs.recurse_objects()[1:]: o.children = []

            if len(objs.children) > 0:
                batched = objs.combine(indexes=True)
                batched.name = "Batched Objs: %s" % key
                root.append(batched)
                added_objects.append(batched)

            logger.debug("Batched objects result for key %s: %s", key, batched)

        # Remove objects
        for key in keys:
            root.select_remove(func=lambda o: key_func(o) == key and o not in added_objects)

        return root


    def batch_empty(self, root):
        """
        Walks nodes and recursively (leaf first) collapses empty nodes to metadata in root.

        Metadata is added to a ddd:batch:metadata dictionary, indexed by path.
        """
        batched_metadata = {}
        root.set('ddd:batch:metadata', batched_metadata)
        def batch_empty_recursive(root, obj, path_prefix, name_suffix):
            for idx, c in enumerate(obj.children):
                batch_empty_recursive(root, c, path_prefix + obj.uniquename() + "/", name_suffix)
                if not c.children and c.is_empty() and 'ddd:rpath' in c.extra:
                    batched_metadata[c.get('ddd:rpath')] = c.metadata("", "")
            obj.children = [c for c in obj.children if c.children or not c.is_empty()]

        batch_empty_recursive(root, root, "", "")
        return root

    def batch_by_material(self, root):
        """
        """
        mat_layer_function = lambda o: (str(o.mat.name if o.mat else None))
        root = ddd.meshops.batch_group(root, key_func=mat_layer_function)
        return root

    def freeze_metadata(self, obj):
        """
        This method modifies objects metadata in place.
        """

        def freeze_metadata_recursive(obj, path_prefix, name_suffix):
            metadata = obj.metadata(path_prefix, name_suffix)
            obj.set('ddd:rpath', metadata.get('ddd:path'))

            node_name = obj.uniquename()  # obj.name  # obj.uniquename()
            if node_name is None:
                node_name = "None"
            for idx, c in enumerate(obj.children):
                name_suffix = "#%d" % (idx)
                freeze_metadata_recursive(c, path_prefix + node_name + "/", name_suffix)

        freeze_metadata_recursive(obj, "", "")

        return obj


