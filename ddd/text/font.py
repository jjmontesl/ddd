# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020


from shapely import geometry
from trimesh.path import segments
from trimesh.scene.scene import Scene, append_scenes
from trimesh.base import Trimesh
from trimesh.path.path import Path
from trimesh.visual.material import SimpleMaterial
from trimesh import creation, primitives, boolean
from shapely.geometry import Polygon, LineString
import trimesh
from csg.core import CSG
from csg import geom as csggeom
import random
import noise
import pyproj


from svgpathtools import wsvg, Line, QuadraticBezier, Path
from ddd.ddd import ddd, DDDObject2
import json


class DDDFont():
    pass


class DDDFontAtlas():
    """
    TODO: This should extend and reuse atlas, which should ideally also allow a JSON format.
    """

    def __init__(self):
        self.index = {}
        self.texture_width = None
        self.texture_height = None

    @staticmethod
    def load_atlas(filepath):
        """
        Process a Texture Atlas definition file, in
        PropertyList file (plistlib) format generated by PyTexturePack.
        """
        atlas = DDDFontAtlas()
        with open(filepath, "r") as f:
            atlas.index = json.load(f)
        return atlas

