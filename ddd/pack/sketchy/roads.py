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

def road_way(path):
    """
    This shall serve for asphalt but also dirt roads, country walks, etc.
    """
    pass

def road_crosswalk():
    pass

def road_lined():
    # Lined islands (with perimeter lines)
    pass

def road_sidewalk():
    # How to conjugate this with squareas and buildings
    # This can also be used for islands
    pass

def road_rail():
    pass

def road(path):
    pass

def bridge(path):
    pass

def lines_line(path, line_distance = 0.0):
    # Create line
    pathline = path.copy()
    if abs(line_distance) > 0.01:
        pathline.geom = pathline.geom.parallel_offset(line_distance, "left")
    line = pathline.buffer(0.15).material(ddd.mats.roadline)
    line.extra['way_1d'] = pathline

    # FIXME: Move cropping to generic site, use itermediate osm.something for storage
    # Also, cropping shall interpolate UVs
    crop = ddd.shape(self.osm.area_crop)
    line = line.intersect(crop)
    line = line.intersect(way_2d)
    line = line.individualize()

    #if line.geom and not line.geom.is_empty:
    #try:
    uvmapping.map_2d_path(line, pathline, line_x_offset / 0.05)

    #except Exception as e:
    #    logger.error("Could not UV map Way 2D from path: %s %s %s: %s", line, line.geom, pathline.geom, e)
    #    continue
    line_3d = line.triangulate().translate([0, 0, 0.05])  # Temporary hack until fitting lines properly
    vertex_func = self.get_height_apply_func(path)
    line_3d = line_3d.vertex_func(vertex_func)
    line_3d = terrain.terrain_geotiff_elevation_apply(line_3d, self.osm.ddd_proj)
    line_3d.extra['ddd:collider'] = False
    line_3d.extra['ddd:shadows'] = False
    #print(line)
    #print(line.geom)
    uvmapping.map_3d_from_2d(line_3d, line)
    #uvmapping.map_2d_path(line_3d, path)

    self.osm.roadlines_3d.children.append(line_3d)
