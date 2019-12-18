'''
'''

from shapely import geometry, affinity
from trimesh.path import segments
from trimesh.scene.scene import Scene, append_scenes 
from trimesh.base import Trimesh
from trimesh.path.path import Path
from trimesh.visual.material import SimpleMaterial 
from trimesh import creation, primitives, boolean, transformations
import trimesh
from csg.core import CSG
from csg import geom as csggeom 
import random
import numpy
import math


class D1D2D3():
    
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
    def polygon(coords):
        geom = geometry.Polygon(coords)
        return DDDObject2(geom=geom)
    
    @staticmethod
    def rect(cmin, cmax):
        geom = geometry.Polygon([(cmin[0], cmin[1]), (cmax[0], cmin[1]),
                                 (cmax[0], cmax[1]), (cmin[0], cmax[1])])
        return DDDObject2(geom=geom)
    
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
    def grid2(cmin, cmax, detail=1.0):
        rects = []
        pointsx = list(numpy.linspace(cmin[0], cmax[0], 1 + int((cmax[0] - cmin[0]) / detail)))
        pointsy = list(numpy.linspace(cmin[1], cmax[1], 1 + int((cmax[1] - cmin[1]) / detail)))
        
        for (idi, (i, ni)) in enumerate(zip(pointsx[:-1], pointsx[1:])):
            for (idj, (j, nj)) in enumerate(zip(pointsy[:-1], pointsy[1:])):
                rect = ddd.rect([i, j], [ni, nj])
                rects.append(rect.geom)
        geom = geometry.MultiPolygon(rects)
        return DDDObject2(geom=geom)
    
    @staticmethod
    def grid3(cmin, cmax, detail=1.0):
        grid2 = D1D2D3.grid2(cmin, cmax, detail)
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
    def group(children):
        if isinstance(children[0], DDDObject2):
            result = DDDObject2(children=children)
        elif isinstance(children[0], DDDObject3):
            result = DDDObject3(children=children)
        else:
            raise AssertionError()
        return result
    

class DDDObject():
    
    def __init__(self, name=None, children=None):
        self.name = name
        #self.geom = geom
        #self.mesh = mesh
        self.children = children


class DDDObject2():
    
    def __init__(self, name=None, children=None, geom=None):
        self.name = name
        self.geom = geom
        self.children = children
    
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
        geom = self.geom.buffer(distance, resolution=resolution,
                                cap_style=cap_style, join_style=join_style,
                                mitre_limit=5.0)
        return DDDObject2(geom=geom)
    
    def subtract(self, other):
        geom = self.geom.difference(other.geom)
        return DDDObject2(geom=geom)
    
    def union(self, other):
        geom = self.geom.union(other.geom)
        return DDDObject2(geom=geom)

    def extrude(self, height):
        
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

        if self.geom.type == 'MultiPolygon':
            meshes = []
            for geom in self.geom.geoms:
                pol = DDDObject2(geom=geom)
                mesh = pol.extrude(height)
                meshes.append(mesh)
            result = DDDObject3(children=meshes)
        else:
            #mesh = creation.extrude_polygon(self.geom, height)
            vertices, faces = creation.triangulate_polygon(self.geom)
            mesh = creation.extrude_triangulation(vertices=vertices,
                                                  faces=faces,
                                                  height=abs(height))
            
            mesh.merge_vertices()
            result = DDDObject3(mesh=mesh)
        
            if height < 0:
                result = result.translate([0, 0, height])
        
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
        
        geoms = self.geom_recursive()
        with open(path, 'w') as f:
            geom = geometry.GeometryCollection(geoms)
            f.write(geom._repr_svg_())

            
class DDDObject3():            

    def __init__(self, name=None, children=None, mesh=None, material=None):
        self.name = name
        self.mesh = mesh
        self.children = children or []
        self.mat = material
        
    def __str__(self):
        return "<DDDObject3 (faces=%d, children=%d)>" % (len(self.mesh.faces) if self.mesh else 0, len(self.children) if self.children else 0)

    def copy(self):
        obj = DDDObject3(name=self.name, children=list(self.children), mesh=self.mesh.copy() if self.mesh else None, material=self.mat)
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
        if obj.mesh:
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
        obj.children = [c.vertex_func(func) for c in obj.children]
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

    def _recurse_scene(self):
        cscenes = []
        if self.children:
            cscenes = [c._recurse_scene() for c in self.children] 
        #if self.mesh:
        scene = Scene()
        scene.add_geometry(geometry=self.mesh, node_name="node_%s_%s" % (id(self), self.mat))
        cscenes = [scene] + cscenes
        
        scene = append_scenes(cscenes)
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
        scene.show()

    def save(self, path):
        meshes = self.recurse_meshes()
        
        if path.endswith('.obj'):
            # Exporting just first mesh
            print("NOTE: Exporting just first object to .obj.")
            data = trimesh.exchange.obj.export_obj(self.meshes[0])
            
        if path.endswith('.dae'):
            data = trimesh.exchange.dae.export_collada(meshes)
        
        elif path.endswith('.gltf'):
            rotated = self.rotate([-math.pi / 2.0, 0, 0])
            scene = rotated._recurse_scene()
            data = trimesh.exchange.gltf.export_glb(scene)
        
        #scene.export(path)
        with open(path, 'wb') as f:
            f.write(data)
            
ddd = D1D2D3
    