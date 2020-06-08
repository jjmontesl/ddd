# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import json
import logging
import math

from shapely import geometry, affinity, ops
from trimesh import transformations

from ddd.core.exception import DDDException
from ddd.core.cli import D1D2D3Bootstrap
from builtins import staticmethod
from abc import abstractstaticmethod
from shapely.geometry.base import BaseMultipartGeometry


# Get instance of logger for this module
logger = logging.getLogger(__name__)

class DDDSVG():

    @staticmethod
    def export_svg(obj, instance_mesh=True, instance_marker=False, size_min=1.0, scale=10.0, margin=0.00):
        """
        Produces a complete SVG document.

        By default, no margin is produced (margin=0). 0.04 is the
        default for R plots.

        If scale is specified, size is multiplied. This is done after calculating size from bounds and applying min/max sizes.
        """

        #size_min = 1
        size_max = 4096

        # TODO: we don't need to recurse geometry here, we can get bounds directly from object
        geoms = obj.geom_recursive()
        geom = geometry.GeometryCollection(geoms)

        svg_top = '<svg xmlns="http://www.w3.org/2000/svg" ' \
            'xmlns:xlink="http://www.w3.org/1999/xlink" '
        if geom.is_empty:
            return svg_top + '/>'
        else:
            # Establish SVG canvas that will fit all the data + small space
            xmin, ymin, xmax, ymax = geom.bounds
            if xmin == xmax and ymin == ymax:
                # This is a point; buffer using an arbitrary size
                xmin, ymin, xmax, ymax = geom.buffer(1).bounds
            else:
                # Expand bounds by a fraction of the data ranges
                expand = margin  # 0.04 or 4%, same as R plots
                widest_part = max([xmax - xmin, ymax - ymin])
                expand_amount = widest_part * expand
                xmin -= expand_amount
                ymin -= expand_amount
                xmax += expand_amount
                ymax += expand_amount
            dx = xmax - xmin
            dy = ymax - ymin
            width = min([max([size_min, dx]), size_max])
            height = min([max([size_min, dy]), size_max])
            width = width * scale
            height = height * scale

            '''
            try:
                scale_factor = max([dx, dy]) / max([width, height])
            except ZeroDivisionError:
                scale_factor = 1.
            '''

            view_box = "{} {} {} {}".format(xmin, ymin, dx, dy)
            transform = "matrix(1,0,0,-1,0,{})".format(ymax + ymin)

            return svg_top + (
                'width="{1}" height="{2}" viewBox="{0}" '
                'preserveAspectRatio="xMinYMin meet">'
                '<g transform="{3}">{4}</g></svg>'
                ).format(view_box, width, height, transform,
                         DDDSVG.svg_obj(obj, instance_mesh=instance_mesh, instance_marker=instance_marker))

    @staticmethod
    def svg_obj(obj, path_prefix="", name_suffix="", instance_mesh=True, instance_marker=False):
        #geoms = self.geom_recursive()
        #geom = geometry.GeometryCollection(geoms)

        node_name = obj.uniquename() + name_suffix

        extra = obj.metadata(path_prefix, name_suffix)
        metadata = {'_name': node_name,
                '_path': extra['ddd:path'],
                '_str': str(obj),
                '_extra': extra,
                '_material': str(obj.mat)}

        color = None
        fill_opacity = 0.7
        if obj.mat:
            color = obj.mat.color
            fill_opacity = extra.get('svg:fill-opacity', 1.0)

        data = ""

        if obj.children:
            data = data + '<g>'
            for idx, c in enumerate(obj.children):
                data = data + DDDSVG.svg_obj(c, path_prefix=path_prefix + node_name + "/", name_suffix="#%d" % (idx), instance_mesh=instance_mesh, instance_marker=instance_marker)
            data = data + '</g>'

        if obj.geom:
            geom = geometry.GeometryCollection([obj.geom])
            data = data + DDDSVG.svg_geom(geom, data=metadata, color=color, fill_opacity=fill_opacity)

        '''
        # FIXME: This code is duplicated from DDDInstance: normalize export / generation
        from ddd.ddd import DDDInstance
        if isinstance(obj, DDDInstance):

            data['_transform'] = obj.transform

            if instance_mesh:
                # Export mesh if object instance has a referenced object (it may not, eg lights)
                if obj.ref:
                    ref = obj.ref.copy()

                    if obj.transform.scale != [1, 1, 1]:
                        raise DDDException("Invalid scale for an instance object (%s): %s", obj.transform.scale, obj)

                    #ref = ref.rotate(transformations.euler_from_quaternion(obj.transform.rotation, axes='sxyz'))
                    #ref = ref.translate(self.transform.position)

                    # Export complete references? (too verbose)
                    refdata = DDDJSON.export_data(ref, path_prefix="", name_suffix="#ref", instance_mesh=instance_mesh, instance_marker=instance_marker)  #, instance_mesh=instance_mesh, instance_marker=instance_marker)
                    data['_ref'] = refdata

            if instance_marker:
                ref = obj.marker()
                refdata = DDDJSON.export_data(ref, path_prefix="", name_suffix="#marker", instance_mesh=instance_mesh, instance_marker=instance_marker)
                data['_marker'] = refdata

        '''

        if not data:
            data = '<g />'

        return data

    @staticmethod
    def svg_geom(geom, data, **kwargs):
        """
        Wraps Shapely export methods to allow finer control of styling and metadata.
        """

        if geom.type == 'Polygon':
            return DDDSVG.svg_polygon(geom, data, **kwargs)
        elif isinstance(geom, BaseMultipartGeometry):
            return DDDSVG.svg_multipart(geom, data, **kwargs)
        else:
            #return geom.svg(scale_factor=1.00, color=color)
            return geom.svg(scale_factor=1.00)  #, color=kwargs.get('color'))
            #return geom.svg(stroke_width=0.01, color=kwargs.get('color'))

    @staticmethod
    def svg_polygon(geom, data, **kwargs):
        fill_color = kwargs.get('color')
        fill_opacity = kwargs.get('fill_opacity', 0.6)
        stroke_width = kwargs.get('stroke_width', 0.01)
        if geom.is_empty:
            return '<g />'
        if fill_color is None:
            fill_color = "#66cc99" if geom.is_valid else "#ff3333"
        exterior_coords = [["{0},{1}".format(*c) for c in geom.exterior.coords]]
        interior_coords = [["{0},{1}".format(*c) for c in interior.coords] for interior in geom.interiors]
        path = " ".join(["M {0} L {1} z".format(coords[0], " L ".join(coords[1:]))
                         for coords in exterior_coords + interior_coords])
        return ('<path fill-rule="evenodd" fill="{2}" stroke="#555555" '
                'stroke-width="{0}" opacity="{3}" d="{1}" />'
                ).format(2. * stroke_width, path, fill_color, fill_opacity)

    @staticmethod
    def svg_multipart(geom, data, **kwargs):

        if geom.is_empty:
            return '<g />'
        return '<g>' + \
            ''.join(DDDSVG.svg_geom(p, data, **kwargs) for p in geom) + \
            '</g>'


