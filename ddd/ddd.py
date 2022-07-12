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
import sys

import numpy as np
import trimesh
from _collections_abc import Iterable
from PIL import Image
from shapely import affinity, geometry, ops
from shapely.geometry import polygon, shape
from shapely.geometry.polygon import Polygon, orient
from trimesh import boolean, creation, primitives, remesh, transformations
from trimesh.base import Trimesh

from ddd.core import settings
from ddd.core.cli import D1D2D3Bootstrap
from ddd.core.exception import DDDException
from ddd.core.selectors.selector_ebnf import selector_ebnf
from ddd.materials.material import DDDMaterial
from ddd.ops import extrusion

# Get instance of logger for this module
logger = logging.getLogger(__name__)


class D1D2D3():

    #BASE_DIR = os.path.join(os.getenv('PWD'), "..") if os.getenv('PWD') else "../"
    #DATA_DIR = os.path.join(BASE_DIR, "/data")
    settings = settings

    # TODO: Remove all usage
    DATA_DIR = settings.DDD_DATADIR

    CAP_ROUND = 1
    CAP_FLAT = 2
    CAP_SQUARE = 3

    JOIN_ROUND = 1
    JOIN_MITRE = 2
    JOIN_BEVEL = 3

    ROT_FLOOR_TO_FRONT = (math.pi / 2.0, 0, 0)
    ROT_TOP_CW = (0, 0, -math.pi / 2.0)
    ROT_TOP_CCW = (0, 0, math.pi / 2.0)
    ROT_TOP_HALFTURN = (0, 0, math.pi)

    DEG_TO_RAD = (math.pi / 180.0)
    RAD_TO_DEG = (180.0 / math.pi)

    PI = math.pi
    TWO_PI = math.pi * 2.0
    TAU = math.pi * 2.0
    PI_OVER_2 = math.pi / 2.0
    PI_OVER_4 = math.pi / 4.0
    PI_OVER_8 = math.pi / 8.0
    PI_OVER_3 = math.pi / 3.0

    VECTOR_UP = np.array([0.0, 0.0, 1.0])
    VECTOR_DOWN = np.array([0.0, 0.0, -1.0])
    VECTOR_BACKWARD = np.array([0.0, 1.0, 0.0])
    VECTOR_FORWARD = np.array([0.0, -1.0, 0.0])  # Towards camera

    ANCHOR_CENTER = (0.5, 0.5)
    ANCHOR_BOTTOM_CENTER = (0.5, 0.0)

    EPSILON = 1e-8

    EXTRUSION_METHOD_WRAP = extrusion.EXTRUSION_METHOD_WRAP
    EXTRUSION_METHOD_SUBTRACT = extrusion.EXTRUSION_METHOD_SUBTRACT # For internal/external/vertical extrusions

    _uid_last = 0

    data = {}

    #@staticmethod
    def initialize_logging(self, debug=True):
        """
        Convenience method for users.
        """
        D1D2D3Bootstrap.initialize_logging(debug)

    #@staticmethod
    def trace(self, local=None):
        """
        Start an interactive session.
        Normally, users will use: "ddd.trace(locals())"
        """
        #import pdb; pdb.set_trace()
        import code
        if local is None: local = {}
        local = dict(globals(), **local)
        logger.info("Debugging console: %s", local)
        code.interact(local=local)

    #@staticmethod
    def material(self, name=None, color=None, extra=None, **kwargs):
        #material = SimpleMaterial(diffuse=color, )
        #return (0.3, 0.9, 0.3)
        material = DDDMaterial(name=name, color=color, extra=extra, **kwargs)
        return material

    #@staticmethod
    def point(self, coords=None, name=None, extra=None):
        if coords is None:
            coords = [0, 0, 0]
        elif len(coords) == 2:
            coords = [coords[0], coords[1], 0.0]
        geom = geometry.Point(coords)
        return self.DDDObject2(geom=geom, name=name, extra=extra)

    #@staticmethod
    def line(self, points, name=None):
        '''
        Expects an array of coordinate tuples.
        '''
        geom = geometry.LineString(points)
        return self.DDDObject2(geom=geom, name=name)

    #@staticmethod
    def polygon(self, coords, name=None):
        geom = geometry.Polygon(coords)
        return self.DDDObject2(geom=geom, name=name)

    #@staticmethod
    def regularpolygon(self, sides, r=1.0, name=None):
        coords = [[math.cos(-i * math.pi * 2 / sides) * r, math.sin(-i * math.pi * 2 / sides) * r] for i in range(sides)]
        return ddd.polygon(coords, name=name)

    #@staticmethod
    def shape(self, geometry, name=None):
        """
        GeoJSON or dict
        """
        geom = shape(geometry)
        return ddd.DDDObject2(geom=geom, name=name)

    #@staticmethod
    def geometry(self, geometry):
        """
        @deprecate in favour of shape
        """
        geom = shape(geometry)
        return DDDObject2(geom=geom)

    #@staticmethod
    def rect(self,  bounds=None, name=None):
        """
        Returns a 2D rectangular polygon for the given bounds [xmin, ymin, xmax, ymax].

        If bounds contains only 2 elements, they are used as x and y size, starting at the origin.

        If no bounds are provided, returns a unitary square with corner at 0, 0 along the positive axis.
        """

        if bounds is None: bounds = [0, 0, 1, 1]
        if len(bounds) == 2: bounds = [0, 0, bounds[0], bounds[1]]
        cmin, cmax = ((bounds[0], bounds[1]), (bounds[2], bounds[3]))
        geom = geometry.Polygon([(cmin[0], cmin[1], 0.0), (cmax[0], cmin[1], 0.0),
                                 (cmax[0], cmax[1], 0.0), (cmin[0], cmax[1], 0.0)])
        geom = polygon.orient(geom, -1)
        return self.DDDObject2(geom=geom, name=name)

    #@staticmethod
    def disc(self, center=None, r=None, resolution=4, name=None):
        if isinstance(center, Iterable): center = ddd.point(center, name=name)
        if center is None: center = ddd.point([0, 0, 0], name=name)
        if r is None: r = 1.0
        geom = center.geom.buffer(r, resolution=resolution)
        return self.DDDObject2(geom=geom, name=name)

    #@staticmethod
    def sphere(self, center=None, r=None, subdivisions=2, name=None):
        if center is None: center = ddd.point([0, 0, 0])
        if r is None: r = 1.0
        mesh = primitives.Sphere(center=center.geom.coords[0], radius=r, subdivisions=subdivisions)
        mesh = Trimesh([[v[0], v[1], v[2]] for v in mesh.vertices], list(mesh.faces))
        return self.DDDObject3(mesh=mesh, name=name)

    @staticmethod
    def cube(center=None, d=None, name=None):
        """
        Cube is sitting on the Z plane defined by the center position.
        `d` is the distance to the side, so cube side length will be twice that value.

        @see :func:`box`
        """
        #if center is not None: raise NotImplementedError()  #
        if center is None: center = [0, 0, 0]
        if d is None: d = 1.0
        cube = ddd.rect([-d, -d, d, d], name=name).extrude(d * 2).translate(center)
        return cube

    def box(self, bounds=None, name=None):
        """
        """
        if bounds is None:
            bounds = [0, 0, 0, 1, 1, 1]
        cube = self.rect([bounds[0], bounds[1], bounds[3], bounds[4]], name=name)
        cube = cube.extrude(bounds[5] - bounds[2]).translate([0, 0, bounds[2]])
        return cube

    def cylinder(self, height, r, center=True, resolution=3, name=None):
        obj = ddd.disc(r=r, resolution=resolution, name=name)
        obj = obj.extrude(height, center=center)
        return obj

    def torus(self, r, ri, resolution=4, name=None):
        circle = ddd.regularpolygon(sides=resolution * 4, r=ri, name=name)
        circle = circle.translate([r, 0])
        obj = circle.revolve()
        return obj

    def trimesh(self, mesh=None, name=None):
        """
        """
        result = self.DDDObject3(name=name, mesh=mesh)
        return result

    def mesh(self, mesh=None, name=None):
        """
        """
        return self.trimesh(mesh=mesh, name=name)

    def path3(self, mesh_or_coords=None, name=None):
        if isinstance(mesh_or_coords, self.DDDObject2):
            if mesh_or_coords.geom.type != 'LineString':
                raise ValueError('Expected a LineString geometry: %s', mesh_or_coords)
            coords = mesh_or_coords.geom.coords
        else:
            coords = mesh_or_coords

        if coords:
            if len(coords[0]) < 3:
                coords = [(c[0], c[1], c[2] if len(c) > 2 else 0.0) for c in coords]
            path3 = trimesh.load_path(coords)
        else:
            path3 = None

        from ddd.nodes.path3 import DDDPath3
        return DDDPath3(name=name, path3=path3)

    def marker(self, pos=None, name=None, extra=None):
        marker = self.box(name=name)
        if pos: marker = marker.translate(pos)
        if extra:
            marker.extra = extra
        marker.extra['ddd:marker'] = True
        return marker

    def ddd2(self, *args, **kwargs):
        return self.DDDObject2(*args, **kwargs)

    def ddd3(self, *args, **kwargs):
        return self.DDDObject3(*args, **kwargs)

    def grid2(self, bounds, detail=1.0, name=None):
        rects = []

        cmin, cmax = bounds[0], bounds[1]

        # FIXME: This needs normalizing so all bounds have same format, and/or use DDDBounds
        if len(bounds) == 2:
            cmin, cmax = bounds

        if isinstance(detail, int): detail= float(detail)
        if isinstance(detail, float): detail = [detail, detail]
        pointsx = list(np.linspace(cmin[0], cmax[0], 1 + int((cmax[0] - cmin[0]) / detail[0])))
        pointsy = list(np.linspace(cmin[1], cmax[1], 1 + int((cmax[1] - cmin[1]) / detail[1])))

        for (idi, (i, ni)) in enumerate(zip(pointsx[:-1], pointsx[1:])):
            for (idj, (j, nj)) in enumerate(zip(pointsy[:-1], pointsy[1:])):
                rect = ddd.rect([i, j, ni, nj])
                rect.geom = orient(rect.geom, 1)
                rects.append(rect.geom)
        geom = geometry.MultiPolygon(rects)
        #DDDObject2(geom=geom).show()
        #geom = geom.buffer(0.0)  # Sanitize, but this destroys the grid
        #DDDObject2(geom=geom).show()
        return self.DDDObject2(name=name, geom=geom)

    def grid3(self, bounds, detail=1.0, name=None):
        """
        FIXME: Try using ops.grid now that it's available? (note that currently that one does not alternate diagonals)
        """
        grid2 = ddd.grid2(bounds, detail, name=name)
        cmin, cmax = bounds[0], bounds[1]
        #grid2 = D1D2D3.rect(cmin, cmax)
        vertices = []
        faces = []
        idi = 0
        idj = 0
        for geom in grid2.geom.geoms:
            flip = ((idi % 2) + (idj % 2)) % 2
            gvs, gfs = creation.triangulate_polygon(geom)
            if flip:
                gfs = np.array([[3, 0, 2], [1, 2, 0]])  # Alternate faces
            gfs = [gf + len(vertices) for gf in gfs]
            faces.extend(gfs)
            vertices.extend(gvs)

            hitmax = False
            for v in gvs:
                if v[0] >= cmax[0] or v[1] >= cmax[1]:
                    hitmax = True

            idi += 1
            if hitmax:
                idi = 0
                idj += 1

        vertices = [[v[0], v[1], 0.0] for v in vertices]
        mesh = Trimesh(vertices, faces)
        #mesh.fix_normals()
        mesh.merge_vertices()
        return self.DDDObject3(name=name, mesh=mesh)

    #@staticmethod
    def group2(self, children=None, name=None, empty=None, extra=None):
        return self.group(children, name, empty=2, extra=extra)

    #@staticmethod
    def group3(self, children=None, name=None, empty=None, extra=None):
        return self.group(children, name, empty=3, extra=extra)

    #@staticmethod
    def group(self, children=None, name=None, empty=None, extra=None):
        """
        """

        if children is None:
            children = []

        if not isinstance(children, list):
            raise ValueError("Tried to add a non-list as children of a group.")

        if not children:
            if empty is None:
                raise ValueError("Tried to add empty collection to children group and no empty value is set.")
            elif empty in (2, "2", "2d"):
                result = self.DDDObject2(name=name)
            elif empty in (3, "3", "3d"):
                result = self.DDDObject3(name=name)
            else:
                raise ValueError("Tried to add empty collection to children group and passed invalid empty parameter: %s", empty)

            #logger.debug("Tried to create empty group.")
            #return None
        elif isinstance(children[0], self.DDDObject2):
            result = self.DDDObject2(children=children, name=name)
        elif isinstance(children[0], ddd.DDDObject3) or isinstance(children[0], self.DDDInstance):
            result = self.DDDObject3(children=children, name=name)
        else:
            raise ValueError("Invalid object for ddd.group(): %s" % children[0])

        if extra:
            result.extra = dict(extra)

        if any((c is None for c in children)):
            raise ValueError("Tried to add null to object children list.")

        return result

    def node(self, name=None, children=None, extra=None):
        return self.group(children=children, name=name, extra=extra, empty=2)

    def instance(self, obj, name=None):
        obj = self.DDDInstance(obj, name)
        return obj

    #@staticmethod
    def json_serialize(self, obj):
        if hasattr(obj, 'export'):
            data = obj.export()
        elif isinstance(obj, Image.Image):
            data = "Image (%s %dx%d)" % (obj.mode, obj.size[0], obj.size[1], )
        else:
            data = repr(obj)
            #data = None
        #if data: print(data)
        return data

    def load(self, name):

        def load_glb():
            scene = trimesh.load("some_file.glb")
            #mesh = trimesh.load_mesh('./test.stl',process=False) mesh.is_watertight
            geometries = list(scene.geometry.values())
            geometry = geometries[0]
            return self.mesh(geometry, geometry.name)
            #adjacency_matrix = geometry.edges_sparse

        if (name.endswith(".glb")):
            return load_glb(name)

        if (name.endswith(".svg")):
            from ddd.formats.loader.svgloader import DDDSVGLoader
            return DDDSVGLoader.load_svg(name)
        else:
            raise DDDException("Cannot load file (unknown extension): %s" % (name))

    #@staticmethod
    def initialize(self):
        #Node = DDDObject
        #Geometry2D = DDDObject2
        #Mesh = DDDObject3

        ddd = self

        from ddd.nodes.instance import DDDInstance
        from ddd.nodes.node2 import DDDNode2
        from ddd.nodes.node3 import DDDNode3

        ddd.DDDInstance = DDDInstance
        ddd.DDDNode2 = DDDNode2
        ddd.DDDNode3 = DDDNode3

        ddd.DDDObject2 = DDDNode2
        ddd.DDDObject3 = DDDNode3

        from ddd.materials.materials import MaterialsCollection
        from ddd.math.math import DDDMath
        from ddd.ops.align import DDDAlign
        from ddd.ops.collision import DDDCollision
        from ddd.ops.geometry import DDDGeometry
        from ddd.ops.helper import DDDHelper
        from ddd.ops.paths import DDDPathOps
        from ddd.ops.reduction import DDDMeshOps
        from ddd.ops.snap import DDDSnap
        from ddd.ops.uvmapping import DDDUVMapping
        from ddd.pack.mats.defaultmats import DefaultMaterials
        from ddd.util.dddrandom import DDDRandom

        ddd.mats = MaterialsCollection()
        ddd.mats.highlight = ddd.material(color='#ff00ff')
        ddd.mats.test = ddd.material(color='#808080', name="Test Material", texture_path=ddd.DATA_DIR + "/materials/util/test_squares_bw.png")
        ddd.MAT_HIGHLIGHT = ddd.mats.highlight
        ddd.MAT_TEST = ddd.mats.test
        ddd.mats.load_from(DefaultMaterials())

        ddd.math = DDDMath()

        ddd.geomops = DDDGeometry()

        ddd.meshops = DDDMeshOps()

        ddd.align = DDDAlign()

        ddd.snap = DDDSnap()

        ddd.collision = DDDCollision()

        ddd.uv = DDDUVMapping()

        ddd.helper = DDDHelper()

        ddd.random = DDDRandom()

        ddd.paths = DDDPathOps()

ddd = D1D2D3()
ddd.initialize()
