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
from ddd.materials.material import DDDMaterial
from ddd.ops import extrusion
from ddd.math.bounds import DDDBounds

# Get instance of logger for this module
logger = logging.getLogger(__name__)


class D1D2D3():

    settings = settings

    # TODO: Remove all usage
    DATA_DIR = settings.DDD_DATADIR

    CAP_ROUND = 1
    CAP_FLAT = 2
    CAP_SQUARE = 3

    JOIN_ROUND = 1
    JOIN_MITRE = 2
    JOIN_BEVEL = 3

    FLOAT_INF_POS = float('inf')
    FLOAT_INF_NEG = float('-inf')
    FLOAT_NAN = float('nan')

    DEG_TO_RAD = (math.pi / 180.0)
    RAD_TO_DEG = (180.0 / math.pi)

    PI = math.pi
    TWO_PI = math.pi * 2.0
    TAU = math.pi * 2.0
    PI_OVER_2 = math.pi / 2.0
    PI_OVER_3 = math.pi / 3.0
    PI_OVER_4 = math.pi / 4.0
    PI_OVER_8 = math.pi / 8.0
    PI_OVER_12 = math.pi / 12.0
    SQRT_2 = math.sqrt(2.0)
    GOLDEN_RATIO = (1 + 5 ** 0.5) / 2  # Golden ratio > 1 (1.618...)

    # Positive rotations are counter-clockwise (from 0, into the first quadrant)
    ROT_FLOOR_TO_FRONT = (PI_OVER_2, 0, 0)
    ROT_FLOOR_TO_BACK = (-PI_OVER_2, 0, 0)
    ROT_TOP_CW = (0, 0, -PI_OVER_2)
    ROT_TOP_CCW = (0, 0, PI_OVER_2)
    ROT_FRONT_CW = (0, -PI_OVER_2, 0)
    ROT_FRONT_CCW = (0, PI_OVER_2, 0)
    ROT_TOP_HALFTURN = (0, 0, PI)

    # Bytes conversion factors
    B_TO_KB = 1 / 1024
    B_TO_MB = 1 / (1024 * 1024)
    MB_TO_B = 1024 * 1024
    MB_TO_KB = 1024

    # Vectors
    # TODO: Use Vector3 or Vector2 members? check if they could be numpy arrays?
    VECTOR_UP = np.array([0.0, 0.0, 1.0])
    VECTOR_DOWN = np.array([0.0, 0.0, -1.0])
    VECTOR_RIGHT = np.array([1.0, 0.0, 0.0])
    VECTOR_LEFT = np.array([-1.0, 0.0, 0.0])
    VECTOR_BACKWARD = np.array([0.0, 1.0, 0.0])
    VECTOR_FORWARD = np.array([0.0, -1.0, 0.0])  # Towards camera

    ANCHOR_CENTER = (0.5, 0.5)
    ANCHOR_BOTTOM_CENTER = (0.5, 0.0)

    # According to numpy.finfo and https://stackoverflow.com/questions/56514892/how-many-digits-can-float8-float16-float32-float64-and-float128-contain
    # float32 can reliably store 6 decimal digits, float64 can reliably store 15 decimal digits
    EPSILON = 1e-6  # Was 1e-8 up to ddd-0.7.0

    EXTRUSION_METHOD_WRAP = extrusion.EXTRUSION_METHOD_WRAP
    EXTRUSION_METHOD_SUBTRACT = extrusion.EXTRUSION_METHOD_SUBTRACT # For internal/external/vertical extrusions

    METADATA_IGNORE_KEYS = ('uv', 'osm:feature')  #, 'ddd:connections')

    _uid_last = 0

    data = {}

    def trace(self, local=None):
        """
        Start an interactive session.
        Intended usage is: `ddd.trace(locals())`
        """
        #import pdb; pdb.set_trace()
        import code
        if local is None: local = {}
        local = dict(globals(), **local)
        logger.info("Debugging console: %s", local)
        code.interact(local=local)

    def material(self, name=None, color=None, extra=None, **kwargs):
        #material = SimpleMaterial(diffuse=color, )
        #return (0.3, 0.9, 0.3)
        material = DDDMaterial(name=name, color=color, extra=extra, **kwargs)
        return material

    def point(self, coords=None, name=None, extra=None):
        """
        Creates a point element as 2D geometryu at the given coordinates.

        The point will be stored as geometry with Z coordinate, even if it's not passed.
        """
        if coords is None:
            coords = [0, 0, 0]
        elif len(coords) == 2:
            coords = [coords[0], coords[1], 0.0]
        geom = geometry.Point(*coords[:3])
        return self.DDDNode2(geom=geom, name=name, extra=extra)

    def line(self, points, name=None):
        '''
        Expects an array of coordinate tuples.
        '''
        geom = geometry.LineString(points)
        return self.DDDNode2(geom=geom, name=name)

    def polygon(self, coords, name=None):
        """
        Build a polygon using the given coordinates. 
        
        Note that this method will not check whether the polygon is defined correctly
        (eg: if it's self-intersecting, or if it's not closed), and also will not orient it in any way (cw / ccw).
        """

        # If coords is a DDDNode2, use its geometry (eg: for a DDDNode2 with a LineString)
        if isinstance(coords, self.DDDNode2):
            coords = coords.geom.coords

        geom = geometry.Polygon(coords)
        return self.DDDNode2(geom=geom, name=name)

    def regularpolygon(self, sides, r=1.0, name=None):
        coords = [[math.cos(-i * math.pi * 2 / sides) * r, math.sin(-i * math.pi * 2 / sides) * r] for i in range(sides)]
        return ddd.polygon(coords, name=name)

    def shape(self, geometry, name=None):
        """
        GeoJSON or dict
        """
        geom = shape(geometry)
        return ddd.DDDNode2(geom=geom, name=name)
    
    def svgpath(self, path, name=None):
        """
        Create a 2D shape from a SVG path description

        TODO: consider if this should also/instead return a DDDPath3
        """
        from ddd.formats.loader.svgloader import DDDSVGLoader

        result = DDDSVGLoader.path_to_node2(path)
        if name: result.setname(name)
        return result

    def geometry(self, geometry):
        """
        @deprecate in favour of shape
        """
        geom = shape(geometry)
        return ddd.DDDNode2(geom=geom)

    def rect(self,  bounds=None, name=None):
        """
        Returns a 2D rectangular polygon for the given bounds [[xmin, ymin, 0], [xmax, ymax, 0]].

        If bounds contains only 2 numbers, they are used as x and y size, starting at the origin.

        If no bounds are provided, returns a unitary square with corner at 0, 0 along the positive axis.
        """

        if bounds is None: bounds = [[0, 0], [1, 1]]
        if len(bounds) == 4: bounds = [[bounds[0], bounds[1]], [bounds[2], bounds[3]]]
        if len(bounds) == 2:
            try:
                assert(float(bounds[0]) is not None)
                assert(float(bounds[1]) is not None)
                bounds = [[0, 0], [bounds[0], bounds[1]]]
            except TypeError as e:
                # Treat as bounds [cmin, cmax]
                pass

        cmin, cmax = bounds #((bounds[0], bounds[1]), (bounds[2], bounds[3]))
        geom = geometry.Polygon([(cmin[0], cmin[1], 0.0), (cmax[0], cmin[1], 0.0),
                                 (cmax[0], cmax[1], 0.0), (cmin[0], cmax[1], 0.0)])
        #geom = polygon.orient(geom, -1)  # Until 2022-10, this line was enabled
        #geom = polygon.orient(geom, 1)  # CCW (this is also how vertices above are defined)
        return self.DDDNode2(geom=geom, name=name)

    def disc(self, center=None, r=None, resolution=4, name=None):
        if isinstance(center, Iterable): center = ddd.point(center, name=name)
        if center is None: center = ddd.point([0, 0, 0], name=name)
        if r is None: r = 1.0
        geom = center.geom.buffer(r, resolution=resolution)
        return self.DDDNode2(geom=geom, name=name)
    

    def sphere(self, center=None, r=None, subdivisions=2, name=None):
        if center is None: center = ddd.point([0, 0, 0])
        if isinstance(center, Iterable): center = ddd.point(center)
        if r is None: r = 1.0
        mesh = primitives.Sphere(center=center.point_coords(), radius=r, subdivisions=subdivisions)
        mesh = Trimesh([[v[0], v[1], v[2]] for v in mesh.vertices], list(mesh.faces))
        return self.DDDNode3(mesh=mesh, name=name)

    def cube(self, center=None, d=None, name=None):
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

    def trimesh(self, mesh, name=None):
        """
        """
        result = self.DDDNode3(name=name, mesh=mesh)
        return result

    def mesh(self, vertices, faces, name=None):
        """
        """
        mesh = Trimesh(vertices=vertices, faces=faces)
        return self.trimesh(mesh=mesh, name=name)
    
    def path3(self, mesh_or_coords=None, name=None):
        if isinstance(mesh_or_coords, self.DDDNode2):
            if mesh_or_coords.geom.geom_type != 'LineString':
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

    def marker(self, pos=None, name=None, extra=None, use_normal_box=False):

        if name is None:
            raise DDDException("Cannot create marker with no name.")

        if use_normal_box:
            marker = ddd.helper.marker_axis(name="Marker: " + name)
            # FIXME: Path3 scale doesn't work (scaled in marker_axis)
        else:
            marker = self.box(name="Marker: " + name).highlight()
            #marker = marker.scale([0.15, 0.15, 0.15])  # normal_boxes may be used for importing, we should not scale them

        if pos: marker = marker.translate(pos)
        if extra:
            marker.extra = extra
        marker.extra['ddd:marker'] = True
        return marker

    def ddd2(self, *args, **kwargs):
        return self.DDDNode2(*args, **kwargs)

    def ddd3(self, *args, **kwargs):
        return self.DDDNode3(*args, **kwargs)

    def grid2(self, bounds: DDDBounds, detail=1.0, name=None, adjust=False):

        if adjust:
            cmin, cmax = [[(math.floor(b / detail) * detail) for b in bounds[0]],
                          [(math.ceil(b / detail) * detail) for b in bounds[1]]]
        else:
            cmin, cmax = bounds[0], bounds[1]

        if isinstance(detail, int): detail= float(detail)
        if isinstance(detail, float): detail = [detail, detail]
        pointsx = list(np.linspace(cmin[0], cmax[0], 1 + int((cmax[0] - cmin[0]) / detail[0])))
        pointsy = list(np.linspace(cmin[1], cmax[1], 1 + int((cmax[1] - cmin[1]) / detail[1])))

        rects = []
        for (idi, (i, ni)) in enumerate(zip(pointsx[:-1], pointsx[1:])):
            for (idj, (j, nj)) in enumerate(zip(pointsy[:-1], pointsy[1:])):
                rect = ddd.rect([i, j, ni, nj])
                rect.geom = orient(rect.geom, 1)
                rects.append(rect.geom)
        geom = geometry.MultiPolygon(rects)
        #DDDNode2(geom=geom).show()
        #geom = geom.buffer(0.0)  # Sanitize, but this destroys the grid
        #DDDNode2(geom=geom).show()
        return self.DDDNode2(name=name, geom=geom)

    def grid3(self, bounds, detail=1.0, name=None):
        """
        FIXME: Try using ops.grid now that it's available? (note that currently that one does not alternate diagonals)
        """
        grid2 = ddd.grid2(bounds, detail, name=name).remove_z()
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
        return self.DDDNode3(name=name, mesh=mesh)

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
                #raise ValueError("Tried to add empty collection to children group and no empty value is set.")
                result = self.DDDNode(name=name)
            elif empty in (2, "2", "2d"):
                result = self.DDDNode2(name=name)
            elif empty in (3, "3", "3d"):
                result = self.DDDNode3(name=name)
            else:
                raise ValueError("Tried to add empty collection to children group and passed invalid empty parameter: %s", empty)

            #logger.debug("Tried to create empty group.")
            #return None
        elif isinstance(children[0], self.DDDNode2):
            result = self.DDDNode2(children=children, name=name)
        elif isinstance(children[0], ddd.DDDNode3) or isinstance(children[0], self.DDDInstance):
            result = self.DDDNode3(children=children, name=name)
        elif isinstance(children[0], self.DDDNode):

            if empty in (2, "2", "2d"):
                result = self.DDDNode2(children=children, name=name)
            elif empty in (3, "3", "3d"):
                result = self.DDDNode3(children=children, name=name)
            else:
                result = self.DDDNode(children=children, name=name)


        else:
            raise ValueError("Invalid object for ddd.group(): %s" % children[0])

        if extra:
            result.extra = dict(extra)

        if any((c is None for c in children)):
            raise ValueError("Tried to add null to object children list.")

        return result

    def node(self, name=None, children=None, extra=None):
        return self.group(children=children, name=name, extra=extra)

    def instance(self, obj, name=None):
        obj = self.DDDInstance(obj, name)
        return obj

    def json_serialize(self, obj):
        if hasattr(obj, 'export'):
            data = obj.export()
        elif isinstance(obj, Image.Image):
            data = "Image (%s %dx%d)" % (obj.mode, obj.size[0], obj.size[1], )
        elif isinstance(obj, ddd.DDDNode):
            data = obj.name
        else:
            data = repr(obj)
            #data = None
        #if data: print(data)
        return data
    
    '''
    class RemoveCircularRefsJSONEncoder(json.JSONEncoder):
        """
        From: https://stackoverflow.com/questions/54873059/what-would-be-the-pythonic-way-to-go-to-prevent-circular-loop-while-writing-json
        """
        def __init__(self, *args, **argv):
            super().__init__(*args, **argv)
            self.proc_objs = []
        def default(self, obj):
            if id(obj) in self.proc_objs:
                return repr(obj)  # short circle the object dumping
            else:
                print("Added: %s" % obj)
                self.proc_objs.append(id(obj))

                try:
                    return super().default(obj)
                except TypeError as e:
                    return ddd.json_serialize(obj)
                except ValueError as e:
                    return ddd.json_serialize(obj)
            #else:
            #    return super().default(obj)
    '''

            
    def load(self, name):

        # TODO: Implement, and move to GLB loader
        def load_glb():
            scene = trimesh.load("some_file.glb")
            #mesh = trimesh.load_mesh('./test.stl',process=False) mesh.is_watertight
            geometries = list(scene.geometry.values())
            geometry = geometries[0]
            return self.mesh(geometry, geometry.name)
            #adjacency_matrix = geometry.edges_sparse

        if (name.endswith(".glb")):
            return load_glb(name)

        elif (name.endswith(".svg")):
            from ddd.formats.loader.svgloader import DDDSVGLoader
            return DDDSVGLoader.load_svg(name)
    
        elif (name.endswith(".fbx")):
            raise NotImplementedError()
        
        elif (name.endswith(".png")):
            raise NotImplementedError()
        elif (name.endswith(".jpg")):
            raise NotImplementedError()
        
        else:
            raise DDDException("Cannot load file (unknown extension): %s" % (name))

    
    def initialize(self):
        """
        Initializes the ddd module and instance.

        Currently, this 'ddd' instance references all modules to make them easily accessible.

        .. note::
            This way of initializing modules and assigning them to ddd is not too pythonic and confuses some code editors.
            Any ideas and suggestions on how to improve this are welcome.
        """

        ddd = self

        from ddd.nodes.node import DDDNode
        from ddd.nodes.node2 import DDDNode2
        from ddd.nodes.node3 import DDDNode3
        from ddd.nodes.path3 import DDDPath3
        from ddd.nodes.instance import DDDInstance

        ddd.DDDNode = DDDNode
        ddd.DDDInstance = DDDInstance
        ddd.DDDNode2 = DDDNode2
        ddd.DDDNode3 = DDDNode3
        ddd.DDDPath3 = DDDPath3

        # NOTE: This way of initializing modules and assigning them to ddd is not too pythonic and confuses some code editors.
        # NOTE: Any ideas and suggestions on how to improve this are welcome.

        from ddd.materials.materials import MaterialsCollection
        from ddd.math.math import DDDMath
        from ddd.ops.align import DDDAlign
        from ddd.ops.collision import DDDCollision
        from ddd.ops.geometry import DDDGeometry
        from ddd.ops.helper import DDDHelper
        from ddd.ops.paths import DDDPathOps
        from ddd.ops.meshops import DDDMeshOps
        from ddd.ops.snap import DDDSnap
        from ddd.ops.uvmapping import DDDUVMapping
        from ddd.pack.mats.defaultmats import DefaultMaterials
        from ddd.util.dddrandom import DDDRandom
        from ddd.util.expressions import DDDExpressions
        from ddd.ext.item.slots import DDDSlots

        ddd.mats = MaterialsCollection()
        ddd.mats.highlight = ddd.material(color='#ff00ff', name="Highlight")
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

        ddd.expr = DDDExpressions()

        ddd.slots = DDDSlots()


# Because 'ddd' is a class and not a module, we are creating a global instance and initialize it here (on import).
# NOTE: This is not ideal, and also confuses some code editors. Any ideas and suggestions on how to improve this are welcome.
ddd : D1D2D3 = D1D2D3()
ddd.initialize()
