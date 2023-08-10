'''
'''

'''
'''

from shapely import geometry
from trimesh.path import segments
from trimesh.scene.scene import Scene, append_scenes
from trimesh.base import Trimesh
from trimesh.path.path import Path
from trimesh.visual.material import SimpleMaterial
from trimesh import creation, primitives, boolean
import trimesh
from csg.core import CSG
from csg import geom as csggeom
import random
from ddd import ddd
import noise


# TODO: Move DDDConnector to 'ext.diagram' leave here only symbols and simple arrows

class DDDConnector(ddd.DDDNode3):
    
    LINE_TYPE_SOLID = "solid"
    LINE_TYPE_DASHED = "dashed"
    LINE_TYPE_DOTTED = "dotted"

    ARROW_TYPE_NONE = "none"
    ARROW_TYPE_SIMPLE = "simple"
    ARROW_TYPE_FILLED = "filled"

    ARROW_SHAPE_TRIANGLE = "triangle"
    ARROW_SHAPE_ARROW = "arrow"
    ARROW_SHAPE_VEE = "vee"
    ARROW_SHAPE_CIRCLE = "circle"
    ARROW_SHAPE_DIAMOND = "diamond"
    ARROW_SHAPE_TEE = "tee"
    ARROW_SHAPE_SQUARE = "square"
    ARROW_SHAPE_BUTT = "butt"

    ARROW_DIRECTION_FORWARD = "forward"
    ARROW_DIRECTION_BACKWARD = "backward"


    def __init__(self):
        
        super().__init__()

        self.start_coords = None
        self.end_coords = None

        self.symbol_start = None
        self.symbol_end = None
        
        self.line_type = DDDConnector.LINE_TYPE_SOLID

        self.path = None

        self.label = None
        self.label_start = None
        self.label_end = None


    def from_to(self, start, end):
        self.start_coords = start
        self.end_coords = end
        self.path = None
        return self
    
    def from_dir_dist(self, start, direction, distance):
        self.start_coords = start
        self.end_coords = start + direction * distance
        self.path = None
        return self
    
    def from_path(self, path):
        self.path = path
        self.start_coords = path.coords[0]
        self.end_coords = path.coords[-1]
        return self
    
    def render_2d():
        raise NotImplementedError()

    def render_3d_flat():
        raise NotImplementedError()
    
    def render_3d_solid():
        raise NotImplementedError()




def symbol_arrow_default_2d(length, angle):
    """
    """
    pass

def symbol_arrow_triangle_2d(length, angle):
    """
    """
    pass

def symbol_arrow_vee_2d(length, angle):
    """
    """
    pass


def symbol_arrow_default_3d():
    pass

