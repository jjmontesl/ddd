# ddd - DDD123
# Library for simple scene modelling.
# Jose Juan Montes and Contributors 2019-2021

import noise
import pyproj

from ddd.core.exception import DDDException
from ddd.ddd import ddd
from ddd.geo.elevation import ElevationModel
from ddd.ops.grid import terrain_grid
from trimesh import transformations, transform_points


#dem_file = '/home/jjmontes/git/ddd/data/dem/eudem/eudem_dem_5deg_n40w010.tif'  # Galicia, Salamanca
#dem_file = '/home/jjmontes/git/ddd/data/dem/eudem/eudem_dem_5deg_n40e000.tif'  # Vilanova i la Geltrú
#dem_file = '/home/jjmontes/git/ddd/data/dem/eudem/eudem_dem_5deg_n40w005.tif'  # Madrid, Huesca
#dem_file = '/home/jjmontes/git/ddd/data/dem/eudem11/eu_dem_v11_E30N20.TIF'  # France, La Rochelle
#dem_file = '/home/jjmontes/git/ddd/data/dem/eudem11/eu_dem_v11_E50N30.TIF'  # Riga, Latvia
#dem_file = '/home/jjmontes/git/ddd/data/dem/srtm/srtm_40_19.tif'  # Cape Town, from: https://dwtkns.com/srtm/


transformer = None  # remove globals, move into classes

def transformer_ddd_to_geo(ddd_proj):
    global transformer
    if transformer is None:
        transformer = pyproj.Transformer.from_proj(ddd_proj, 'epsg:4326', always_xy=True)  # for old DEM files
        #transformer = pyproj.Transformer.from_proj(ddd_proj, pyproj.Proj(init='epsg:3035'))  # for EUDEM 1.1 files

    return transformer

def transform_ddd_to_geo(ddd_proj, point):
    x, y = transformer_ddd_to_geo(ddd_proj).transform(point[0], point[1])
    return [x, y]


def terrain_geotiff(bounds, ddd_proj, detail=1.0):
    """
    Generates a square grid and applies terrain elevation to it.
    """
    # TODO: we should load the chunk as a heightmap, and load via terrain_heightmap for reuse
    #elevation = ElevationChunk.load('/home/jjmontes/git/ddd/data/elevation/eudem/eudem_dem_5deg_n40w010.tif')
    #elevation = ElevationChunk.load(dem_file)
    elevation = ElevationModel.instance()

    mesh = terrain_grid(bounds, detail=detail)
    func = lambda x, y, z, i, o: [x, y, elevation.value(transform_ddd_to_geo(ddd_proj, [x, y]))]
    mesh = mesh.vertex_func(func)
    #mesh.mesh.invert()
    return mesh

def terrain_geotiff_elevation_apply(obj, ddd_proj, offset=0):
    
    elevation = ElevationModel.instance()
    #print(transform_ddd_to_geo(ddd_proj, [obj.mesh.vertices[0][ 0], obj.mesh.vertices[0][1]]))

    #func = lambda x, y, z, i, o: [x, y, z + elevation.value(transform_ddd_to_geo(ddd_proj, [x, y]))]
    def vertex_func(x, y, z, i, o):
        _world_matrix = o.get('_world_matrix', None)
        if _world_matrix is not None:
            world_xyz = transform_points([[x, y, z]], _world_matrix)[0]
        else:
            world_xyz = [x, y, z]
        #print([x, y, z], world_xyz)
        return [x, y, z + offset + elevation.value(transform_ddd_to_geo(ddd_proj, [world_xyz[0], world_xyz[1]]))]
    
    obj = obj.vertex_func(vertex_func)

    #mesh.mesh.invert()
    return obj

def terrain_geotiff_min_elevation_apply(obj, ddd_proj):
    elevation = ElevationModel.instance()

    min_h = None
    for v in obj.vertex_iterator():  # obj.vertex_iterator_world()
        v_h = elevation.value(transform_ddd_to_geo(ddd_proj, [v[0], v[1]]))
        if min_h is None:
            min_h = v_h
        if v_h < min_h:
            min_h = v_h

    # FIXME: hack added to allow meshes with no vertices, but this should be better handled with proper world/local coords, parenting, ordering of applying height, etc...
    if min_h is None:
        v = obj.transform.position
        v_h = elevation.value(transform_ddd_to_geo(ddd_proj, [v[0], v[1]]))
        min_h = v_h

    if min_h is None:
        raise DDDException("Cannot calculate min value for elevation: %s" % obj)
    #func = lambda x, y, z, i, o: [x, y, z + min_h]
    
    # FIXME: This translate was changed to transform.translate to account for nodes that have no geometry, but this should be better handled...
    #obj = obj.translate([0, 0, min_h])
    obj.transform.translate([0, 0, min_h])

    obj.extra['_terrain_geotiff_min_elevation_apply:elevation'] = min_h
    #mesh.mesh.invert()
    return obj

def terrain_geotiff_max_elevation_apply(obj, ddd_proj):
    elevation = ElevationModel.instance()

    max_h = None
    for v in obj.vertex_iterator():
        v_h = elevation.value(transform_ddd_to_geo(ddd_proj, [v[0], v[1]]))
        if max_h is None:
            max_h = v_h
        if v_h > max_h:
            max_h = v_h

    if max_h is None:
        raise DDDException("Cannot calculate max value for elevation: %s" % obj)

    #func = lambda x, y, z, i, o: [x, y, z + max_h]
    obj = obj.translate([0, 0, max_h])
    obj.extra['_terrain_geotiff_max_elevation_apply:elevation'] = max_h
    #mesh.mesh.invert()
    return obj

def terrain_geotiff_elevation_value(v, ddd_proj):
    elevation = ElevationModel.instance()
    v_h = elevation.value(transform_ddd_to_geo(ddd_proj, [v[0], v[1]]))
    return v_h



