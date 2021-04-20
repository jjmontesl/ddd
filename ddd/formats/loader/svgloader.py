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
import base64
from ddd.ddd import ddd
from svgpathtools import svg2paths
from svgpath2mpl import parse_path
from ddd.formats.loader import parse_svg_path
from shapely.ops import polygonize
from shapely.geometry.multipolygon import MultiPolygon
import matplotlib


# Get instance of logger for this module
logger = logging.getLogger(__name__)

class DDDSVGLoader():

    @staticmethod
    def load_svg(path):
        """
        """
        #paths = parse_svg_path.parse_svg_path(path)
        #print(paths)
        #return

        paths, attributes = svg2paths(path)

        result = ddd.group2()

        for k, v in enumerate(attributes):
            #print(v)  # v['d']  # print d-string of k-th path in SVG

            # Ex svgpath = 'M10 10 C 20 20, 40 20, 50 10Z'
            mpl_path = parse_path(v['d'])

            '''
            import matplotlib.pyplot as plt
            fig = plt.figure(figsize=(200, 200))
            ax = fig.add_subplot(111)
            ax.axis([0, 0, 200, 200])
            collection = matplotlib.collections.PathCollection([mpl_path])
            collection.set_transform(ax.transData)
            #patch = matplotlib.patches.PathPatch(mpl_path, facecolor="red", lw=2)
            ax.add_artist(collection)
            #ax.add_patch(patch)
            ax.set_xlim([0, 200])
            ax.set_ylim([200, 0])
            plt.show()
            '''

            coords = mpl_path.to_polygons(closed_only=True)

            item = ddd.polygon(coords[0]).clean()  #.convex_hull()

            for c in coords[1:]:
                ng = ddd.polygon(c).clean()  #.convex_hull()
                #ng.show()
                #print (ng.geom.is_valid)
                #if not ng.geom.is_valid: continue
                if item.contains(ng):
                    item = item.subtract(ng)
                else:
                    item = item.union(ng)

            #result = ddd.group([ddd.polygon(c) for c in coords], empty=2)
            result.append(item)

        #result = result.scale([1.0 / (48 * 64), -1.0 / (48 * 64)])
        #result = result.simplify(0.005)  #
        #result.show()

        result = result.union().scale([1, -1]).clean(0)
        xmin, ymin, xmax, ymax = result.bounds()
        result = result.translate([0, - (ymin + ymax)])
        #result = ddd.align.anchor(result, ddd.ANCHOR_CENTER)

        return result
