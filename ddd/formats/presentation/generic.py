# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

from builtins import staticmethod
import logging

from trimesh import transformations
import trimesh
from ddd.ddd import ddd


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

        try:

            newchildren = []

            # Convert base DDDNode to DDDNode3
            #if node.__class__ is ddd.DDDNode:
            #    result = ddd.DDDObject3.from_node(node)

            if isinstance(node, ddd.DDDPath3):
                nresult = node.copy()
                result = nresult

            elif isinstance(node, ddd.DDDObject3):
                result = node.copy()
                result.children = []

            elif isinstance(node, ddd.DDDInstance):
                result = node.copy()
                #result.children = []

            elif isinstance(node, ddd.DDDObject2):
                if node.geom:
                    if node.geom.type == 'LineString':
                        result = ddd.path3(node.geom.coords)
                        result = result.copy_from(node, copy_material=True)
                    elif node.geom.type == 'MultiLineString':
                        tnode = node.individualize()
                        result = Generic3DPresentation.present(tnode)
                        newchildren = list(result.children)
                    elif node.geom.type in ('MultiPolygon', ):
                        tnode = node.individualize()
                        result = Generic3DPresentation.present(tnode)
                        newchildren = list(result.children)
                    elif node.geom.type in ('MultiPoint', ):
                        tnode = node.individualize()
                        result = Generic3DPresentation.present(tnode)
                        newchildren = list(result.children)

                    elif node.geom.type in ('Point', ):
                        try:
                            # Attempt to make points stand out
                            #result = node.copy3(copy_children=False)
                            #triangulated = ddd.point().buffer(0.2).triangulate()
                            #triangulated = triangulated.rotate(ddd.ROT_FLOOR_TO_FRONT).translate(node.point_coords())
                            #result.mesh = triangulated.mesh
                            result = ddd.helper.marker_axis(material=node.mat).translate(node.point_coords())
                            result = result.copy_from(node, copy_material=True, copy_children=False)

                            result = Generic3DPresentation.present(result)
                            newchildren = list(result.children)

                        except Exception as e:
                            logger.warn("Could not triangulate 2D object (point) for 3D representation export (%s): %s", node, e)
                        except:
                            logger.warn("ERROR: Could not triangulate 2D object (point) for 3D representation export (%s)", node)
                            raise

                    else:
                        result = node.copy3(copy_children=False)
                        tnode = node
                        if node.geom.type in ('Point', ):  # this was failing silently !?, but there should not be MultiPoints already
                            tnode = node.buffer(0.25)
                        #elif node.geom.type in ('LineString', 'MultiLineString'):
                        #    tnode = node.buffer(0.10)
                        #    #tnode = node.buffer(0.10)
                        try:
                            triangulated = tnode.triangulate(ignore_children=True)
                            result.mesh = triangulated.mesh
                        except Exception as e:
                            logger.warn("Could not triangulate 2D object for 3D representation export (%s): %s", node, e)
                        except:
                            logger.warn("ERROR: Could not triangulate 2D object for 3D representation export (%s)", node)
                            raise
                else:
                    # Fixme: this should be a static constructor in DDDNode3 (and DDDNode2.copy3() may call that, if still needed)
                    #result = node.copy3(copy_children=True)
                    #result = ddd.DDDNode3.from_node(node)  # node.copy3(copy_children=True)
                    result = node.copy3(copy_children=False)

            else:
                # Convert base DDDNode to DDDNode3
                result = node.copy3(copy_children=False)

            for c in node.children:
                nc = Generic3DPresentation.present(c)
                newchildren.append(nc)

            result.children = newchildren

        except Exception as e:
            logger.error("Cannot present node %s: %s", node, e)
            raise

        #ddd.trace(locals())
        return result
