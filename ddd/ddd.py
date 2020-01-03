# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging
import math
import random

from csg import geom as csggeom 
from csg.core import CSG
import numpy
from shapely import geometry, affinity
from shapely.geometry import shape
from trimesh import creation, primitives, boolean, transformations
import trimesh
from trimesh.base import Trimesh
from trimesh.path import segments
from trimesh.path.path import Path
from trimesh.scene.scene import Scene, append_scenes 
from trimesh.visual.material import SimpleMaterial 
import copy


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class D1D2D3():
    
    @staticmethod
    def initialize_logging(debug=True):
        """
        Convenience method for users.
        """

        # In absence of file config
        default_level = logging.INFO if not debug else logging.DEBUG
        #logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=default_level)
        #logging.basicConfig(format='%(asctime)s - %(levelname)s - %(name)s - %(message)s', level=default_level)
        #logging.basicConfig(format='%(asctime)s - %(levelname)s - %(name)s - %(message)s', level=default_level)

        if debug:
            logging.basicConfig(format='%(asctime)s - %(levelname)s - %(module)s - %(message)s', level=default_level)
            #logging.basicConfig(format='%(asctime)s - %(levelname)s - %(name)s - %(message)s', level=default_level)
        else:
            #logging.basicConfig(format='%(asctime)s %(message)s', level=default_level)
            logging.basicConfig(format='%(message)s', level=default_level)

        logging.getLogger("trimesh").setLevel(logging.INFO)
            
        logger.info("DDD logging initialized.")
        logger.debug("DDD debug logging enabled.")

    
    @staticmethod
    def material(color):
        #material = SimpleMaterial(diffuse=color, )
        #return (0.3, 0.9, 0.3)
        color = trimesh.visual.color.hex_to_rgba(color)
        return color

    @staticmethod
    def point(coords):
        if len(coords) == 2: coords = [coords[0], coords[1], 0.0]
        geom = geometry.Point(coords)
        return DDDObject2(geom=geom)
    
    @staticmethod
    def line(points):
        '''
        Expects an array of coordinate tuples.
        '''
        geom = geometry.LineString(points)
        return DDDObject2(geom=geom)
    
    @staticmethod
    def polygon(coords, name=None):
        geom = geometry.Polygon(coords)
        return DDDObject2(geom=geom, name=name)

    @staticmethod
    def shape(geometry, name=None):
        """
        GeoJSON or dict
        """
        geom = shape(geometry)
        return DDDObject2(geom=geom, name=name)
    
    @staticmethod
    def geometry(geometry):
        """
        @deprecate in favour of shape
        """
        geom = shape(geometry)
        return DDDObject2(geom=geom)
    
    @staticmethod
    def rect(bounds, name=None):
        cmin, cmax = ((bounds[0], bounds[1]), (bounds[2], bounds[3]))
        geom = geometry.Polygon([(cmin[0], cmin[1], 0.0), (cmax[0], cmin[1], 0.0),
                                 (cmax[0], cmax[1], 0.0), (cmin[0], cmax[1], 0.0)])
        return DDDObject2(geom=geom, name=None)
    
    @staticmethod
    def disc(center=None, r=None, resolution=8):
        if center is None: center = ddd.point([0, 0, 0])
        if r is None: r = 1.0
        geom = center.geom.buffer(r, resolution=resolution)
        return DDDObject2(geom=geom)
    
    @staticmethod
    def sphere(center=None, r=None, subdivisions=2):
        if center is None: center = ddd.point([0, 0, 0])
        if r is None: r = 1.0
        mesh = primitives.Sphere(center=center.geom.coords[0], radius=r, subdivisions=subdivisions)
        mesh = Trimesh([[v[0], v[1], v[2]] for v in mesh.vertices], list(mesh.faces))
        return DDDObject3(mesh=mesh)
    
    @staticmethod
    def cube(center=None, d=None):
        """
        Cube is sitting on the Z plane defined by the center position
        """
        if center is not None: raise NotImplementedError()  # 
        if center is None: center = ddd.point([0, 0, 0])
        if d is None: d = 1.0
        cube = D1D2D3.rect([-d, -d], [d, d]).extrude(d * 2).translate([0, 0, 0])
        return cube
    
    @staticmethod
    def grid2(bounds, detail=1.0):
        rects = []
        cmin, cmax = bounds[:2], bounds[2:]
        pointsx = list(numpy.linspace(cmin[0], cmax[0], 1 + int((cmax[0] - cmin[0]) / detail)))
        pointsy = list(numpy.linspace(cmin[1], cmax[1], 1 + int((cmax[1] - cmin[1]) / detail)))
        
        for (idi, (i, ni)) in enumerate(zip(pointsx[:-1], pointsx[1:])):
            for (idj, (j, nj)) in enumerate(zip(pointsy[:-1], pointsy[1:])):
                rect = ddd.rect([i, j, ni, nj])
                rects.append(rect.geom)
        geom = geometry.MultiPolygon(rects)
        return DDDObject2(geom=geom)
    
    @staticmethod
    def grid3(bounds2, detail=1.0):
        grid2 = D1D2D3.grid2(bounds2, detail)
        cmin, cmax = bounds2[:2], bounds2[2:]
        #grid2 = D1D2D3.rect(cmin, cmax)
        vertices = []
        faces = []
        idi = 0
        idj = 0
        for geom in grid2.geom:
            flip = ((idi % 2) + (idj % 2)) % 2
            gvs, gfs = creation.triangulate_polygon(geom)
            if flip:
                gfs = numpy.array([[3, 0, 2], [1, 2, 0]])  # Alternate faces
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
        return DDDObject3(mesh=mesh)        
    
    @staticmethod
    def group(children, name=None):
        if not children:
            result = DDDObject(name=name)
        elif isinstance(children[0], DDDObject2):
            result = DDDObject2(children=children, name=name)
        elif isinstance(children[0], DDDObject3):
            result = DDDObject3(children=children, name=name)
        else:
            raise ValueError("Invalid object for ddd.group(): %s", children[0])
        
        if any((c is None for c in children)):
            raise ValueError("Tried to add null to object children list.")
        
        return result
    

class DDDObject():
    
    def __init__(self, name=None, children=None, extra=None, material=None):
        self.name = name
        self.children = children if children is not None else []
        self.extra = extra if extra is not None else {}
        self.mat = material
        
        self.geom = None
        self.mesh = None
        
        for c in self.children:
            if not isinstance(c, self.__class__):
                raise ValueError("Invalid children type (not %s): %s" % (self.__class__, c))

class DDDObject2(DDDObject):
    
    def __init__(self, name=None, children=None, geom=None, extra=None, material=None):
        super().__init__(name, children, extra, material)
        self.geom = geom

    def __repr__(self):
        return "<DDDObject2 (name=%s, geom=%s (%s verts), children=%d)>" % (self.name, self.geom.type if self.geom else None, self.vertex_count(), len(self.children) if self.children else 0)

    def vertex_count(self):
        if not self.geom:
            return 0
        if self.geom.type == 'MultiPolygon':
            return sum([len(p.exterior.coords) for p in self.geom.geoms])
        if self.geom.type == 'Polygon':
            if self.geom.is_empty: return 0
            return len(self.geom.exterior.coords) + sum([len(i.coords) for i in self.geom.interiors])
        else:
            return len(self.geom.coords)
        return None
    
    def copy(self):
        obj = DDDObject2(name=self.name, children=list(self.children), geom=copy.deepcopy(self.geom) if self.geom else None, extra=dict(self.extra), material=self.mat)
        return obj
    
    def material(self, material):
        obj = self.copy()
        obj.mat = material
        #mesh.visuals = visuals
        obj.children = [c.material(material) for c in obj.children]
        return obj
    
    def end(self):
        coords = self.geom.coords[-1]
        return D1D2D3.point(coords)
    
    def line_rel(self, coords):
        if len(coords) == 2: coords = [coords[0], coords[1], 0.0]
        linecoords = [p for p in self.geom.coords]
        nextpoint = [linecoords[-1][0] + coords[0], linecoords[-1][1] + coords[1], linecoords[-1][2] + coords[2]]
        linecoords.append(nextpoint)

        geom = geometry.LineString(linecoords)
        return DDDObject2(geom=geom)
    
    def line_to(self, coords):
        if len(coords) == 2: coords = [coords[0], coords[1], 0.0]
        linecoords = [p for p in self.geom.coords]
        linecoords.append(coords)

        geom = geometry.LineString(linecoords)
        return DDDObject2(geom=geom)
    
    def buffer(self, distance, resolution=8, cap_style=1, join_style=1, mitre_limit=5.0):
        '''
        shapely.geometry.CAP_STYLE
            round    1
            flat    2
            square    3
        shapely.geometry.JOIN_STYLE
            round    1
            mitre    2
            bevel    3
        '''
        result = self.copy()
        result.geom = self.geom.buffer(distance, resolution=resolution,
                                       cap_style=cap_style, join_style=join_style,
                                       mitre_limit=5.0)
        return result
    
    def subtract(self, other):
        
        result = self.copy()
        if self.geom and other.geom:
            result.geom = result.geom.difference(other.geom)
        for c in other.children:
            result = result.subtract(c)
        
        return result
    
    def union(self, other=None):
        """
        Returns a copy of this object to which geometry from other object has been unioned.
        If the second object has children, they are also unioned recursively.
        
        If the second object is None, all children of this are unioned. 
        """
        result = self.copy()
        result.children = []
        
        # If other has children, union them too            
        objs = self.children
        while len(objs) > 1:
            #print(objs[0], objs[1])
            newo = objs[0].union().union(objs[1].union())
            objs = objs[2:] + [newo]
        if objs:
            if result.geom:
                result.geom = result.geom.union(objs[0].geom)
            else:
                result.geom = objs[0].geom
        
        if other:
            if result.geom:
                result.geom = result.geom.union(other.union().geom)
            else:
                result.geom = other.geom

        return result

    def triangulate(self):
        """
        Returns a triangulated mesh (3D) from this 2D shape.
        """
        if self.geom.type == 'MultiPolygon':
            meshes = []
            for geom in self.geom.geoms:
                pol = DDDObject2(geom=geom)
                mesh = pol.triangulate()
                meshes.append(mesh)
            result = ddd.group(children=meshes, name=self.name)
        else:
            # Triangulation mode is critical for the resulting quality and triangle count.
            #mesh = creation.extrude_polygon(self.geom, height)
            #vertices, faces = creation.triangulate_polygon(self.geom)  # , min_angle=math.pi / 180.0)
            vertices, faces = creation.triangulate_polygon(self.geom, triangle_args="p", engine='triangle')  # Flat, minimal, non corner-detailing ('pq30' produces more detailed triangulations)
            mesh = Trimesh([(v[0], v[1], 0.0) for v in vertices], faces)
            #mesh = creation.extrude_triangulation(vertices=vertices, faces=faces, height=0.2)
            mesh.merge_vertices()
            result = DDDObject3(mesh=mesh, name=self.name)
            
        return result

    def extrude(self, height):
        
        #logger.debug("Extruding: %s", self)
        
        # Extrude exterior line(s)
        '''
        coords = self.geom.exterior.coords
        segs = []
        for i in range(len(coords) - 1):
            segs.append([coords[i], coords[i + 1]])
            
        v, f = segments.extrude(segs, abs(height), False)
        mesh = Trimesh(v, f)
        mesh.invert()  # mesh normals face polygon interior, invert it
        
        # Triangulate polygon and create caps
        if caps:
            v, f = creation.triangulate_polygon(self.geom)
            mesh_cap_top = Trimesh(v, f)
            v, f = creation.triangulate_polygon(self.geom)
            mesh_cap_bottom = Trimesh(v, f)
        '''

        if self.geom:
            if self.geom.type == 'MultiPolygon':
                meshes = []
                for geom in self.geom.geoms:
                    pol = DDDObject2(geom=geom, material=self.mat)
                    try:
                        mesh = pol.extrude(height)
                        meshes.append(mesh)
                    except ValueError as e:
                        logger.error("Could not extrude Polygon in MultiPolygon: %s", e)
                    except IndexError as e:
                        logger.error("Could not extrude Polygon in MultiPolygon: %s", e)
                result = DDDObject3(children=meshes, name=self.name)
            elif not self.geom.is_empty:
                # Triangulation mode is critical for the resulting quality and triangle count.
                #mesh = creation.extrude_polygon(self.geom, height)
                #vertices, faces = creation.triangulate_polygon(self.geom, engine="meshpy")  # , min_angle=math.pi / 180.0)
                #vertices, faces = creation.triangulate_polygon(self.geom, triangle_args="p30", engine='triangle')
                vertices, faces = creation.triangulate_polygon(self.geom, triangle_args="p", engine='triangle')  # Flat, minimal, non corner-detailing ('pq30' produces more detailed triangulations)
                mesh = creation.extrude_triangulation(vertices=vertices,
                                                      faces=faces,
                                                      height=abs(height))
                mesh.merge_vertices()
                result = DDDObject3(mesh=mesh)
            
                if height < 0:
                    result = result.translate([0, 0, -height])
            else:
                #logger.warn("Cannot extrude (empty polygon)")
                result = DDDObject3()
        else:
            result = DDDObject3()
        
        result.children.extend([c.extrude(height) for c in self.children])
        
        # Copy extra information from original object 
        result.name = self.name
        result.extra = dict(self.extra)
        result.extra['extruded_shape'] = self 
        result = result.material(self.mat)
        
        return result

    def simplify(self, distance):
        result = self.copy()
        result.geom = self.geom.simplify(distance, preserve_topology=True)
        result.children = [c.simplify(distance) for c in self.children]
        return result

    def random_points(self, num_points=1, density=None):
        # TODO: use density or count, accoridng to poligon area :?
        result = []
        minx, miny, maxx, maxy = self.geom.bounds
        while len(result) < num_points:
            pnt = geometry.Point(random.uniform(minx, maxx), random.uniform(miny, maxy))
            if self.geom.contains(pnt):
                result.append(pnt.coords[0])

        return result

    def geom_recursive(self):
        geoms = []
        if self.geom: geoms = [self.geom]
        if self.children:
            for c in self.children:
                cgems = c.geom_recursive()
                geoms.extend(cgems)
        return geoms
    
    def save(self, path):
        
        # $$('path').forEach(function(p) {console.log(p); p.setAttribute('stroke-width', 1.0)});
        
        geoms = self.geom_recursive()
        with open(path, 'w') as f:
            geom = geometry.GeometryCollection(geoms)
            f.write(geom._repr_svg_())

            
class DDDObject3(DDDObject):            

    def __init__(self, name=None, children=None, mesh=None, extra=None, material=None):
        super().__init__(name, children, extra, material)
        self.mesh = mesh
        
    def __repr__(self):
        return "<DDDObject3 (name=%s, faces=%d, children=%d)>" % (self.name, len(self.mesh.faces) if self.mesh else 0, len(self.children) if self.children else 0)

    def copy(self):
        obj = DDDObject3(name=self.name, children=list(self.children), mesh=self.mesh.copy() if self.mesh else None, material=self.mat, extra=dict(self.extra))
        return obj

    def translate(self, v):
        obj = self.copy()
        if obj.mesh:
            obj.mesh.apply_translation(v)
        obj.children = [c.translate(v) for c in self.children]
        return obj
    
    def rotate(self, v):
        obj = self.copy()
        if obj.mesh:
            rot = transformations.euler_matrix(v[0], v[1], v[2], 'rxyz')
            obj.mesh.vertices = trimesh.transform_points(obj.mesh.vertices, rot)
        obj.children = [c.rotate(v) for c in self.children]
        return obj
    
    def scale(self, v):
        obj = self.copy()
        if obj.mesh:
            sca = numpy.array([[v[0], 0.0, 0.0, 0.0],
                               [0.0, v[1], 0.0, 0.0],
                               [0.0, 0.0, v[2], 0.0],
                               [0.0, 0.0, 0.0, 1.0]])
            obj.mesh.vertices = trimesh.transform_points(obj.mesh.vertices, sca)
        obj.children = [c.scale(v) for c in self.children]
        return obj

    def material(self, material):
        obj = self.copy()
        obj.mat = material
        if obj.mesh and material is not None:
            obj.mesh.visual.face_colors = material
        #visuals = mesh.visuatrimesh.visual.ColorVisuals(mesh=mesh, face_colors=[material])  # , material=material
        #mesh.visuals = visuals
        obj.children = [c.material(material) for c in obj.children]
        return obj
    
    def elevation_func(self, func):
        obj = self.copy()
        for v in obj.mesh.vertices:
            dz = func(v[0], v[1])
            v[2] += dz
        obj.children = [c.elevation_func(func) for c in obj.children]
        return obj 
    
    def vertex_func(self, func):
        obj = self.copy()
        if obj.mesh:
            for iv, v in enumerate(obj.mesh.vertices):
                res = func(v[0], v[1], v[2], iv)
                v[0] = res[0]
                v[1] = res[1]
                v[2] = res[2]
        obj.children = [c.vertex_func(func) for c in self.children]
        return obj

    def _csg(self, other, operation):
        
        if not other or not other.mesh:
            return self.copy()

        if not self.mesh and operation == 'union':
            return other.copy()
        
        print("%s %s %s" % (self, operation, other))
        
        pols1 = []
        for f in self.mesh.faces:
            verts = [self.mesh.vertices[f[0]], self.mesh.vertices[f[1]], self.mesh.vertices[f[2]]]
            pols1.append(csggeom.Polygon([csggeom.Vertex(verts[0]), csggeom.Vertex(verts[1]), csggeom.Vertex(verts[2])]))

        pols2 = []
        for f in other.mesh.faces:
            verts = [other.mesh.vertices[f[0]], other.mesh.vertices[f[1]], other.mesh.vertices[f[2]]]
            pols2.append(csggeom.Polygon([csggeom.Vertex(verts[0]), csggeom.Vertex(verts[1]), csggeom.Vertex(verts[2])]))
        
        csg1 = CSG.fromPolygons(pols1)
        csg2 = CSG.fromPolygons(pols2)

        if operation == 'subtract':
            pols = csg1.subtract(csg2).toPolygons()
        elif operation == 'union':
            pols = csg1.union(csg2).toPolygons()
        else:
            raise AssertionError()
        
        #mesh = boolean.difference([self.mesh, other.mesh], 'blender')
        v = []
        f = []
        i = 0
        for p in pols:
            for vi in range(len(p.vertices) - 2):
                v.extend([[p.vertices[0].pos[0], p.vertices[0].pos[1], p.vertices[0].pos[2]], 
                          [p.vertices[vi + 1].pos[0], p.vertices[vi + 1].pos[1], p.vertices[vi + 1].pos[2]], 
                          [p.vertices[vi + 2].pos[0], p.vertices[vi + 2].pos[1], p.vertices[vi + 2].pos[2]]])
                f.append([i, i+1, i+2])
                i += 3
        
        mesh = Trimesh(v, f)
        mesh.fix_normals()
        mesh.merge_vertices()
        
        obj = DDDObject3(mesh=mesh, children=self.children, material=self.material)
        return obj

    def subtract(self, other):
        return self._csg(other, operation='subtract')

    def union(self, other):
        return self._csg(other, operation='union')

    '''
    def _recurse_scene(self):
        cscenes = []
        if self.children:
            cscenes = [c._recurse_scene() for c in self.children] 
        #if self.mesh:
        scene = Scene()
        scene.add_geometry(geometry=self.mesh, node_name="node_%s_%s" % (id(self), self.mat.replace(" ", "_")))
        cscenes = [scene] + cscenes
        
        scene = append_scenes(cscenes)
        return scene
    '''
    def _recurse_scene(self):
        
        scene = Scene()
        scene.add_geometry(geometry=self.mesh, node_name="node_%s_%s" % (id(self), str(self.mat).replace(" ", "_")))
        
        cscenes = []
        if self.children:
            for c in self.children:
                cscene = c._recurse_scene()
                cscenes.append(cscene) 
        
        scene = append_scenes([scene] + cscenes)
        
        return scene
    
    def recurse_meshes(self):
        cmeshes = []
        if self.mesh:
            cmeshes = [self.mesh]
        if self.children:
            for c in self.children:
                cmeshes.extend(c.recurse_meshes())
        return cmeshes
    
    def recurse_objects(self):
        cobjs = [self]
        for c in self.children:
            cobjs.extend(c.recurse_objects())
        return cobjs

    def show(self):
        rotated = self.rotate([-math.pi / 2.0, 0, 0])
        scene = rotated._recurse_scene()
        #scene.show('gl')

        # Example code light
        #light = trimesh.scene.lighting.DirectionalLight()
        #light.intensity = 10
        #scene.lights = [light]
        
        import pyrender
        #pr_scene = pyrender.Scene.from_trimesh_scene(rotated)
        meshes = self.recurse_meshes()
        pr_scene = pyrender.Scene()
        for m in meshes:
            prm = pyrender.Mesh.from_trimesh(m, smooth=False) #, wireframe=True)
            pr_scene.add(prm)
        pyrender.Viewer(pr_scene, lighting="direct")  #, viewport_size=resolution)

    def dump(self, indent_level=0):
        print("  " * indent_level + str(self))
        for c in self.children:
            c.dump(indent_level=indent_level + 1)

    def save(self, path):
        logger.info("Saving to: %s (%s)", path, self)
    
        if path.endswith('.obj'):
            # Exporting just first mesh
            logger.warning("NOTE: Exporting just first object to .obj.")
            meshes = self.recurse_meshes()
            data = trimesh.exchange.obj.export_obj(self.meshes[0])
            
        elif path.endswith('.dae'):
            meshes = self.recurse_meshes()
            data = trimesh.exchange.dae.export_collada(meshes)
        
        elif path.endswith('.glb'):
            rotated = self.rotate([-math.pi / 2.0, 0, 0])
            scene = rotated._recurse_scene()
            data = trimesh.exchange.gltf.export_glb(scene)
            
        else:
            raise ValueError()
        
        #scene.export(path)
        with open(path, 'wb') as f:
            f.write(data)
            
ddd = D1D2D3
    