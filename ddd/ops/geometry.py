# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging
from ddd.ddd import ddd, DDDObject2
import math
from ddd.core.exception import DDDException
import shapely

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
        Returns (major, minor, rotation)
        """

        rectangle = obj.geom.minimum_rotated_rectangle

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

        # Generate lines, rotate and translate to area
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
        xmin, ymin, xmax, ymax = resized.bounds()

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

