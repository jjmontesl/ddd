# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

from builtins import staticmethod
import logging

from trimesh import transformations
import trimesh


# Get instance of logger for this module
logger = logging.getLogger(__name__)

class Generic3DPresentation():
    """
    Formats a DDD Node and descendants in order to show it (in 3D).

    This adapts 2D nodes to 3D (buffers points and lines, applies materials).
    """

    @staticmethod
    def present(node):
        """
        Formats nodes for presentation.

        This includes transforming 2D to 3D nodes as needed.
        """
        from ddd.ddd import DDDObject2

        if isinstance(node, DDDObject2):
            result = node.copy3()
            if node.geom:
                tnode = node
                if node.geom.type in ('Point', 'MultiPoint'):
                    tnode = node.buffer(0.25)
                elif node.geom.type in ('LineString', 'MultiLineString'):
                    tnode = node.buffer(0.10)
                try:
                    triangulated = tnode.triangulate(ignore_children=True)
                    result.mesh = triangulated.mesh
                except Exception as e:
                    logger.warn("Could not triangulate 2D object for 3D representation export (%s): %s", node, e)
        else:
            result = node.copy()

        # Temporary hack to separate flat elements
        increment = 0.0  # 0.025
        accum = 0.0
        newchildren = []
        for c in node.children:
            nc = Generic3DPresentation.present(c)
            if isinstance(c, DDDObject2):
                accum += increment
                nc = nc.translate([0, 0, accum])
            newchildren.append(nc)

        result.children = newchildren

        return result


