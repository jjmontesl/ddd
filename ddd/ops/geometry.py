# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging
import math

import numpy as np
import shapely
from ddd.core.exception import DDDException
from ddd.ddd import ddd
from ddd.math.vector2 import Vector2
from ddd.math.vector3 import Vector3
from shapely.geometry.polygon import LineString, LinearRing, Polygon, orient

# Get instance of logger for this module
logger = logging.getLogger(__name__)

class DDDGeometry():

    def inscribed_rectangle(self, obj, padding=0.5, search_erode=1.5):
        """
        Generates an inscribed rectangle from the oriented bounding box of the shape,
        searching an downscaled inscribed rectangle from it. Note that
        this is nt guaranteed to be the largest inscribed rectangle possible.
        """

        rect = obj.copy()
        rect.geom = obj.geom.minimum_rotated_rectangle

        iters = 60
        candidate_rect = rect.copy()
        # TODO: do this by bipartition
        for i in range(iters):
            #scale = 1.0 - (1.0 / iters) * i
            candidate_rect = rect.buffer(-search_erode * i)
            if obj.contains(candidate_rect.buffer(padding)):
                break

        return candidate_rect

    def oriented_axis(self, obj):
        """
        Calculates the oriented axis to box the object (based on the minimum rotated rectangle)

        Returns (major, minor, rotation)
        """

        rectangle = obj.union().geom.minimum_rotated_rectangle
        logger.debug("Calculating oriented axis for: %s min_rotated: %s", obj, rectangle)

        coords = rectangle.exterior.coords[:-1]

        min_point = 0
        for i in range(len(coords)):
            if (coords[i][0] + coords[i][1]) < (coords[min_point][0] + coords[min_point][1]):
                min_point = i
        coords = coords[i:] + coords[:i]

        width_seg = ddd.line([coords[0], coords[1]])
        length_seg = ddd.line([coords[0], coords[-1]])

        width_l = width_seg.geom.length
        length_l = length_seg.geom.length

        if width_l > length_l:
            (width_l, length_l) = (length_l, width_l)
            (width_seg, length_seg) = (length_seg, width_seg)

        vec_dir_major = (length_seg.geom.coords[1][0] - length_seg.geom.coords[0][0], length_seg.geom.coords[1][1] - length_seg.geom.coords[0][1])
        vec_dir_minor = (width_seg.geom.coords[1][0] - width_seg.geom.coords[0][0], width_seg.geom.coords[1][1] - width_seg.geom.coords[0][1])
        midpoint_major = length_seg.centroid().geom.coords[0]
        midpoint_minor = width_seg.centroid().geom.coords[0]
        major_seg = ddd.line([midpoint_minor, [midpoint_minor[0] + vec_dir_major[0], midpoint_minor[1] + vec_dir_major[1]]])
        minor_seg = ddd.line([midpoint_major, [midpoint_major[0] + vec_dir_minor[0], midpoint_major[1] + vec_dir_minor[1]]])

        # Calculate angle
        angle = math.atan2(length_seg.geom.coords[1][1] - length_seg.geom.coords[0][1],
                           length_seg.geom.coords[1][0] - length_seg.geom.coords[0][0])

        return (major_seg, minor_seg, angle)  #, length_seg, width_seg)

    def remove_holes_split(self, obj):
        """
        Splits a polygon with holes generating several polygons with no holes.
        Returns the same object if it has no interior holes.
        """
        result = obj.copy()
        if result.geom and result.geom.type == "MultiPolygon":
            result = result.individualize()

        if result.geom:
            if result.geom.type == "Polygon":
                # Walk inner holes
                if len(result.geom.interiors) > 0:
                    splitter_coords = [result.geom.interiors[0].centroid.coords[0], result.geom.interiors[0].centroid.coords[0]]
                    splitter_coords[0] = (splitter_coords[0][0], splitter_coords[0][1] - 99999999.0)
                    splitter_coords[1] = (splitter_coords[1][0], splitter_coords[1][1] + 99999999.0)
                    splitter = ddd.line(splitter_coords)
                    splitgeoms = shapely.ops.split(result.geom, splitter.geom)
                    result.geom = None
                    for splitgeom in splitgeoms:
                        splitobj = result.copy()
                        splitobj.geom = splitgeom
                        splitobj.children = []
                        result.children.extend(splitobj.individualize().flatten().children)
            else:
                raise DDDException("Unknown geometry for removing holes: %s" % obj)

        result.children = [self.remove_holes_split(c) for c in result.children]

        #ddd.group2([obj, result]).dump()
        #ddd.group2([obj, result]).extrude(10.0).show()
        result = result.flatten()

        return result

    def resize(self, obj, size=(1, 1), keep_aspect=True):
        """
        Resizes an object to the given size.
        If `keep_aspect` is True, aspect ratio is maintained and max width or height limited to the given width or height size.

        Modifies the object in place.
        """
        resized = obj  # ddd.align.anchor(obj, ddd.ANCHOR_CENTER)
        bounds = resized.bounds()
        xmin, ymin, _ = bounds[0]
        xmax, ymax, _ = bounds[1]

        width = xmax - xmin
        height = ymax - ymin
        aspect_ratio = width / height

        scale_x = size[0] / width
        scale_y = size[1] / height

        if keep_aspect:
            if aspect_ratio >= 1:
                scale_y = scale_x
            else:
                scale_x = scale_y

        resized = resized.scale((scale_x, scale_y))

        obj.replace(resized)

        return obj

    def subdivide_to_size(self, obj, max_edge):
        """
        Subdivide a 1D geometry so segments have a maximum size.

        Currently works for LineStrings and Polygons.

        Modifies the object in place. Subdivides children recursively.
        """

        if obj.geom.type == 'Polygon':
            return self._subdivide_to_size_polygon(obj, max_edge)

        if obj.geom.type != 'LineString':
            raise DDDException("Cannot subdivide geometry of type: %s" % obj)

        sqr_max_edge = max_edge ** 2
        newcoords = [obj.geom.coords[0]]

        for (pa, pb) in zip(obj.geom.coords[:-1], obj.geom.coords[1:]):
            use_z = (len(pb) > 2 and len(pa) > 2)
            sqrdist = ((pb[0] - pa[0]) ** 2) + ((pb[1] - pa[1]) ** 2) + (((pb[2] - pa[2]) ** 2) if use_z else 0)
            if (sqrdist > sqr_max_edge):
                numpoints = int(math.sqrt(sqrdist) / max_edge)
                pointsx = list(np.linspace(pa[0], pb[0], numpoints + 2, endpoint=True))[1:-1]
                pointsy = list(np.linspace(pa[1], pb[1], numpoints + 2, endpoint=True))[1:-1]

                if use_z:
                    pointsz = list(np.linspace(pa[2], pb[2], numpoints + 2, endpoint=True))[1:-1]
                else:
                    pointsz = None

                for i in range(numpoints):
                    newcoords.append((pointsx[i], pointsy[i], pointsz[i] if use_z else 0))
            newcoords.append(pb)

        obj.geom = LineString(newcoords)

        obj.children = [self.subdivide_to_size(c, max_edge) for c in obj.children]

        return obj

    def _subdivide_to_size_polygon(self, obj, max_edge):

        # Subdivide exterior ring
        polygon_edge = obj.outline()
        polygon_edge = self.subdivide_to_size(polygon_edge, max_edge)

        # FIXME: We are ignoring holes
        obj.geom = Polygon(polygon_edge.geom.coords)

        obj.children = [self.subdivide_to_size(c, max_edge) for c in obj.children]

        return obj

    def vertex_order_align_snap(self, obj, ref):  #, offset, base_height):
        """
        Reindex an object (linear ring) coordinates so it has the same winding and
        starts in the same point (or closest possible) as the reference.
        """

        geom_a = ref.geom
        geom_b = obj.geom

        # Ensure winding
        if (geom_a.type == "Polygon" and geom_b.type == "Polygon"):
            if (geom_a.exterior.is_ccw != geom_b.exterior.is_ccw):
                #logger.debug("Cannot extrude between polygons with different winding. Orienting polygons.")
                #geom_a = orient(geom_a, -1)
                geom_b = orient(geom_b, -1 if geom_a.exterior.is_ccw else 1)
        else:
            raise NotImplementedError()

        coords_a = geom_a.coords if geom_a.type == 'Point' else geom_a.exterior.coords[:-1]  # Linearrings repeat first/last point
        coords_b = geom_b.coords if geom_b.type == 'Point' else geom_b.exterior.coords[:-1]  # Linearrings repeat first/last point

        # Find closest to coords_a[0] in b, and shift coords in b to match 0
        closest_idx = 0
        closest_dist = float("inf")
        for idx, v in enumerate(coords_b):
            dist = ((v[0] - coords_a[0][0]) ** 2) + ((v[1] - coords_a[0][1]) ** 2)
            if dist < closest_dist:
                closest_idx = idx
                closest_dist = dist
        #if closest_idx != 0: print("Closest Idx: %s" % closest_idx)
        coords_b = coords_b[closest_idx:] + coords_b[:closest_idx]

        #coords_a = coords_a[:] + [coords_a[0]]
        coords_b = coords_b[:] + [coords_b[0]]

        if obj.children:
            raise NotImplementedError()

        geom_b.exterior.coords = LinearRing(coords_b)
        obj.geom = Polygon(coords_b, obj.geom.interiors)
        return obj

    def line_extend(self, obj, start_l=1.0, end_l=1.0):
        """
        Extends a line continuing start and/or end.

        Start and end points are changed.

        If a length is negative, it tries to blindly move that point backwards.

        TODO: Add flag to add new segments instead of altering?

        Returns a new object.
        """
        if obj.geom.type != 'LineString':
            raise DDDException("Cannot line_extend %s (not a LineString)" % obj)

        dir_start = (Vector3(obj.geom.coords[1]) - Vector3(obj.geom.coords[0])).normalized()
        dir_end = (Vector3(obj.geom.coords[-2]) - Vector3(obj.geom.coords[-1])).normalized()

        p_start = Vector3(obj.geom.coords[0]) - ((dir_start * start_l) if start_l > 0 else obj.geom.coords[0])
        p_end = Vector3(obj.geom.coords[-1]) - ((dir_end * end_l) if end_l > 0 else obj.geom.coords[1])

        coords = [p_start] + obj.geom.coords[1:-1] + [p_end]

        result = obj.copy()
        result.geom = LineString(coords)

        return result
