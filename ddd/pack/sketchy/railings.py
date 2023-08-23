# DDD(123) - Library for procedural generation of 2D and 3D geometries and scenes
# Copyright (C) 2021 Jose Juan Montes
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import logging
import math
import random
import numpy as np


from ddd.ddd import ddd
from ddd.core.exception import DDDException
from ddd.pack.sketchy import buildings
from shapely.geometry.multilinestring import MultiLineString


# Get instance of logger for this module
logger = logging.getLogger(__name__)


"""
"""



# Create as component / builder? extend Builder? extend Surface/Line Builder?
def railing_builder_tiled_x(obj, height=1.0, 
                            edge_builder=None, edge_tile_spacing=0.0, edge_tile_height=None,
                            node_builder=None, node_height=None,  # node_add_length=None,
                            name=None):
    """
    TODO: Take a LineString as input (or perhaps MultiLineString), instead of a polygon.
    """

    base = obj
    shape1 = base.centerline()
    shape1.geom = MultiLineString([g for g in shape1.geom.geoms if g.length >= 0.2])  # FIXME: hard-coded min length
    # Alt: shape.individualize().select(lambda g: g.length <= 0.2).remove()

    result = base.copy3(copy_children=False, name="Railing")
    
    # Iterate line vertices, creating a post on each node and filling the surface a repeated pattern

    # Node items (e.g. columns)
    for coords in shape1.coords_iterator():
        # TODO: Tag nodes with their index and other attributes, in order to support adding objects
        post = buildings.column(height=height)
        post = post.translate(coords)
        result.append(post)

    # Edges
    for segment in shape1.iterate_segments():
        edge = segment.buffer(0.05).extrude(height - 0.2)
        edge = edge.material(ddd.mats.stone)
        edge = ddd.uv.map_cubic(edge)
        result.append(edge)
        
    return result