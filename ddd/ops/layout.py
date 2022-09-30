# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

from abc import ABCMeta
import logging
import math

import numpy as np
from ddd.core.exception import DDDException
from ddd.ddd import ddd
from ddd.math.vector3 import Vector3
from ddd.nodes.node2 import DDDNode2
from ddd.math.vector2 import Vector2


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class DDDLayout():
    """
    Distributes 2D space in a similar fashion to what UI layouts do (using
    horizontal and vertical layouts).

    This class lays out a given node and children (which need to have an appropriate structure).

    TODO: Move outside ops? this doesn't really work with DDD objects, but it's a generator
    """

    @staticmethod
    def layout(obj):

        DDDLayout._from_attrs(obj)
        result = obj.get('ddd:layout:impl').layout(obj)
        return result

    @staticmethod
    def _from_attrs(obj):
        layout_type = obj.get('ddd:layout', None)
        if layout_type is None:
            raise DDDException("Object has no layout attribute definition ('ddd:layout'): %s", self)

        layout_impl = None
        if layout_type == 'horizontal':
            layout_impl = HorizontalDDDLayout()
        elif layout_type == 'vertical':
            layout_impl = VerticalDDDLayout()
        elif layout_type == 'element':
            layout_impl = DDDLayoutElement()
        else:
            raise DDDException("Unknown layout type ('ddd:layout'='%s') for object: %s", layout_type, self)

        obj.set('ddd:layout:impl', layout_impl)
        for c in obj.children:
            DDDLayout._from_attrs(c)

    @staticmethod
    def to_rects(obj):
        return obj.get('ddd:layout:impl').to_rects(obj)


class DDDLayoutElement():

    def layout_size(self, obj):

        #size = Vector2((0, 0))

        #if not obj.is_empty():
        #    size = obj.size()

        width = obj.get('ddd:layout:width', None)
        height = obj.get('ddd:layout:height', None)

        return (width, height)

    def layout(self, obj):
        obj = obj.copy()
        #c_size = obj.get('ddd:layout:impl').layout_size(obj)
        #obj.set('ddd:layout:width', 0.8)  # c_size[0]),
        #obj.set('ddd:layout:height', c_size[1])
        return obj

    def to_rects(self, obj):

        result = obj.copy()
        result.geom = None

        result.children = [c.get('ddd:layout:impl').to_rects(c) for c in result.children]

        result.geom = ddd.rect([
            0, 0,
            obj.get('ddd:layout:width'),
            -obj.get('ddd:layout:height')
            ]).geom

        result = result.translate(obj.transform.position)
        result.transform.position = Vector3((0, 0, 0))
        #result.geom = result.subtract(ddd.group2(result.children)).geom
        #result.transform.translate(obj.transform.position)

        result = result.clean()

        return result

class DDDLayoutContainer(DDDLayoutElement):
    pass

class DirectionalDDDLayout(DDDLayoutContainer):

    def __init__(self, direction):
        self.direction = Vector2(direction)

    def layout(self, obj):

        #ref_size = obj.size()

        obj = obj.copy()

        container_margin = obj.get('ddd:layout:margin', 0)
        container_margin = [container_margin] * 4  # trbl
        layout_spacing = obj.get('ddd:layout:spacing', 0)

        width = obj.get('ddd:layout:width', None)
        height = obj.get('ddd:layout:height', 0)
        total_margin_x = container_margin[1] + container_margin[3]
        total_margin_y = container_margin[0] + container_margin[2] + layout_spacing * len(obj.children)

        cursor = Vector2((0, 0))
        cursor = cursor + Vector2((container_margin[3], -container_margin[0]))

        c_height_sum = 0
        c_weight_sum = 0

        for c in obj.children:
            c_width, c_height = c.get('ddd:layout:impl').layout_size(c)
            c_height_sum += c_height if c_height else 0
            c_weight_sum += c.get('ddd:layout:height:flexible', 0)
            #c_width_min = min(c_width_min, c_width)
            #c_width

        for c in obj.children:

            c_width, c_height = c.get('ddd:layout:impl').layout_size(c)

            # Child width
            c_width = width - total_margin_x
            #if container_width is None and c_size[0] is not None: container_width = c_size[0]
            #if c.get('ddd:layout:width:expand', None) and c_size[0] is not None and inner_width > c_size[0]:
            #    c_size = Vector2([inner_width, c_size[1]])

            # Child height
            c_height = c_height #- total_margin_y
            if c_height is None: c_height = 0

            if c.get('ddd:layout:height:flexible', None):
                remaining_height = height - c_height_sum - total_margin_y
                c_height = remaining_height * (c.get('ddd:layout:height:flexible') / c_weight_sum)

            c.set('ddd:layout:width', c_width)
            c.set('ddd:layout:height', c_height)

            new_c = c.get('ddd:layout:impl').layout(c)
            new_c.transform.position = Vector3.array(cursor)

            cursor = cursor + Vector2((c_width, c_height)).scale(self.direction) + Vector2.up * -layout_spacing
            c.replace(new_c)

        obj.set('ddd:layout:width', width)
        obj.set('ddd:layout:height', height)

        return obj

    def layout_size(self, obj):

        ssize = Vector2((0, 0))
        for c in obj.children:
            c_size = c.get('ddd:layout:impl').layout_size(c)
            ssize = (c_size[0], ssize[1] + (c_size[1] or 0))
            '''
            if self.direction[0] == 1:
                ssize = Vector2((max(ssize[0], ref_size[0]), ssize[1]))
            else:
                ssize = Vector2((ssize[0], max(ssize[1], ref_size[1])))
            '''

        #ssize = Vector2((max(ref_size[0], ssize[0]), max(ref_size[1], ssize[1])))

        return ssize


class HorizontalDDDLayout(DirectionalDDDLayout):

    def __init__(self):
        super().__init__([1, 0])

class VerticalDDDLayout(DirectionalDDDLayout):

    def __init__(self):
        super().__init__([0, -1])

