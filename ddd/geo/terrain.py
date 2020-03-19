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
from ddd.ddd import ddd
import noise
from ddd.geo.georaster import ElevationChunk
import pyproj


def terrain_grid(bounds, detail=1.0, height=1.0, scale=0.025):
    '''
    If bounds is a single number, it's used as L1 distance.
    '''

    if isinstance(bounds, float):
        distance = bounds
        bounds = [-distance, -distance, distance, distance]

    mesh = ddd.grid3(bounds, detail=detail)

    #func = lambda x, y: 2.0 * noise.pnoise2(x, y, octaves=3, persistence=0.5, lacunarity=2.0, repeatx=1024, repeaty=1024)
    def func(x, y):
        val = height * noise.pnoise2(x * scale, y * scale, octaves=2, persistence=0.5, lacunarity=2.0, repeatx=1024, repeaty=1024, base=0)
        #print("%s, %s = %s" % (x, y, val))
        return val
    #func = lambda x, y: random.uniform(0, 2)
    mesh = mesh.elevation_func(func)

    return mesh

'''
def _cr(p):
    offset_x = -8.723
    offset_y = 42.238
    return [offset_x + p[0] / 100000, offset_y + p[1] / 100000, 0.0]
'''

transformer = None  # rmeove globals, move into classes

def transformer_ddd_to_geo(ddd_proj):
    global transformer
    if transformer is None:
        transformer = pyproj.Transformer.from_proj(ddd_proj, pyproj.Proj(init='epsg:4326'))
    return transformer

def transform_ddd_to_geo(ddd_proj, point):
    x, y = transformer_ddd_to_geo(ddd_proj).transform(point[0], point[1])
    return [x, y]

def terrain_geotiff(bounds, ddd_proj, detail=1.0):
    # TODO: we should load the chunk as a heightmap, and load via terrain_heightmap for reuse
    #elevation = ElevationChunk.load('/home/jjmontes/git/ddd-baseline/data/elevation/eudem/eudem_dem_5deg_n40w010.tif')
    elevation = ElevationChunk.load('/home/jjmontes/git/ddd-baseline/data/elevation/eudem/eudem_dem_5deg_n40w010.tif')

    mesh = terrain_grid(bounds, detail=detail)
    func = lambda x, y, z, i: [x, y, elevation.value(transform_ddd_to_geo(ddd_proj, [x, y]))]
    mesh = mesh.vertex_func(func)
    #mesh.mesh.invert()
    return mesh

def terrain_geotiff_elevation_apply(obj, ddd_proj):
    elevation = ElevationChunk.load('/home/jjmontes/git/ddd-baseline/data/elevation/eudem/eudem_dem_5deg_n40w010.tif')
    func = lambda x, y, z, i: [x, y, z + elevation.value(transform_ddd_to_geo(ddd_proj, [x, y]))]
    obj = obj.vertex_func(func)
    #mesh.mesh.invert()
    return obj

def terrain_geotiff_min_elevation_apply(obj, ddd_proj):
    elevation = ElevationChunk.load('/home/jjmontes/git/ddd-baseline/data/elevation/eudem/eudem_dem_5deg_n40w010.tif')

    min_h = None
    for v in obj.vertex_iterator():
        v_h = elevation.value(transform_ddd_to_geo(ddd_proj, [v[0], v[1]]))
        if min_h is None:
            min_h = v_h
        if v_h < min_h:
            min_h = v_h

    func = lambda x, y, z, i: [x, y, z + min_h]
    obj = obj.vertex_func(func)
    #mesh.mesh.invert()
    return obj
