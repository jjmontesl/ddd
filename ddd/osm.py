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
from ddd_osm import osm
import pyproj
import subprocess as s

random.seed(0)


center_wgs84 = [-8.723, 42.238]
osm_proj = pyproj.Proj(init='epsg:4326')
'''
#ddd_proj = pyproj.Proj(init='epsg:3857')
ddd_proj = pyproj.Proj(proj="ortho", 
                       lon_0=center_wgs84[0], lat_0=center_wgs84[1],
                       x_0=0., y_0=0.) 
                       #units="m", datum="WGS84", ellps="WGS84")
''' 
ddd_proj = pyproj.Proj(proj="tmerc", 
                       lon_0=center_wgs84[0], lat_0=center_wgs84[1],
                       k=1,
                       x_0=0., y_0=0.,
                       units="m", datum="WGS84", ellps="WGS84",
                       towgs84="0,0,0,0,0,0,0",
                       no_defs=True)

#trans_func = partial(pyproj.transform, pyproj.Proj(init='EPSG:4326'), aea_proj)
#geom_aea = ops.transform(trans_func, geometry)
                

osmscene = osm.generate_geojson(['../private/vigo-lines.geojson',
                                 '../private/vigo-polygons.geojson',
                                 '../private/vigo-points.geojson',
                                 '../private/vigo-lines-2.geojson',
                                 '../private/vigo-polygons-2.geojson',
                                 '../private/vigo-points-2.geojson',
                                 ], osm_proj=osm_proj, ddd_proj=ddd_proj)

scene = osmscene

scene.save('osm.gltf')
#scene.show()
#scene.save('osm.dae')


s.call(['notify-send','OSM MapGen','Finished generating OSM map.'])
