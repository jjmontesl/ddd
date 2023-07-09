# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging

from ddd.ddd import ddd
from shapely.geometry import shape
from shapely.geometry.polygon import orient

from ddd.math.vector3 import Vector3

# Get instance of logger for this module
logger = logging.getLogger(__name__)

class DDDHelper():

    def all(self, size=20.0, plane_xy=True, grid_yz=True, grid_xz=True, grid_xy=False, grid_space=2.0, center=None, around_center=False):

        objs = ddd.group3(name="Helper grid")

        if grid_yz:
            objs.append(self.grid_yz(size, grid_space))
        if grid_xz:
            objs.append(self.grid_xz(size, grid_space))

        objs = objs.combine()

        # Avoid combining as it has a different texture or are 2D

        if grid_xy:
            objs.append(self.grid_xy(size, grid_space))
        if plane_xy:
            objs.append(self.plane_xy(size))

        if center is None:
            center = [0, 0, 0]
        objs = objs.translate([-center[0], -center[1], -center[2] if len(center) > 2 else 0])

        if around_center:
            objs = objs.translate([-size / 2, -size / 2, 0])

        return objs

    def plane_xy(self, size=10.0):
        obj = ddd.rect([0, 0, size, size], name="Helper plane XY").triangulate()
        obj = obj.material(ddd.MAT_TEST)
        obj = ddd.uv.map_cubic(obj)
        return obj

    def grid_xy(self, size=10.0, grid_space=1.0):
        gw = 0.05
        grid = ddd.group3(name="Helper grid XZ")
        for i in range(int(size / grid_space) + 1):
            line1 = ddd.line([[i * grid_space, 0, 0], [i * grid_space, size, 0]])
            grid.append(line1)
        for j in range(int(size / grid_space) + 1):
            line2 = ddd.line([[0, j * grid_space, 0], [size, j * grid_space, 0]])
            grid.append(line2)
        return grid

    def grid_xy_solid(self, size=10.0, grid_space=1.0):
        grid = self.grid_xz(size, grid_space)
        grid = grid.rotate((ddd.PI_OVER_2, 0, 0)).translate([0, size, 0])
        grid.name = "Helper grid XY (Solid)"
        return grid

    def grid_yz(self, size=10.0, grid_space=1.0):
        gw = 0.05
        grid = ddd.group3(name="Helper grid YZ")
        for i in range(int(size / grid_space) + 1):
            line1 = ddd.box([0, i * grid_space, 0, 0 + gw, i * grid_space + gw, size])
            grid.append(line1)
        for j in range(int(size / grid_space) + 1):
            line2 = ddd.box([0, 0, j * grid_space, 0 + gw, size, j * grid_space + gw])
            grid.append(line2)
        grid = grid.combine()
        return grid

    def grid_xz(self, size=10.0, grid_space=1.0):
        gw = 0.05
        grid = ddd.group3(name="Helper grid XZ")
        for i in range(int(size / grid_space) + 1):
            line1 = ddd.box([i * grid_space, 0, 0, i * grid_space + gw, 0 + gw, size])
            grid.append(line1)
        for j in range(int(size / grid_space) + 1):
            line2 = ddd.box([0, 0, j * grid_space, size, 0 + gw, j * grid_space + gw])
            grid.append(line2)
        grid = grid.combine()
        return grid

    def colorize_objects(self, obj, palette=None):

        if palette is None:
            palette = [ddd.mats.blue, ddd.mats.crimson, ddd.mats.green, ddd.mats.orange, ddd.mats.brown, ddd.mats.pink,
                       ddd.mats.yellow, ddd.mats.cyan, ddd.mats.violet, ddd.mats.coral, ddd.mats.darkblue,
                       ddd.mats.darkslategrey, ddd.mats.darkturquoise]

        result = obj.copy()

        idx = 0
        for (i, o) in enumerate(result.iterate_objects()):
            if o.is_empty(): continue
            o.replace(o.material(palette[idx], include_children=False))
            idx = (idx + 1) % len(palette)

        return result
    
    def offset_objects(self, obj, offset=0.02):
        result = obj.copy()
        for (i, o) in enumerate(result.iterate_objects()):
            if o.is_empty(): continue
            o.transform.translate([0, 0, i * offset])

        return result

    def marker_axis(self, name=None, material=None):
        if name is None: name ="Marker Axis"
        marker = ddd.group3(name=name)
        size = 0.15
        line_x = ddd.path3([[-size, 0, 0], [size, 0, 0]]).material(material if material else ddd.mats.red)
        line_y = ddd.path3([[0, -size, 0], [0, size, 0]]).material(material if material else ddd.mats.green)
        line_z = ddd.path3([[0, 0, -size], [0, 0, size]]).material(material if material else ddd.mats.blue)
        marker.append([line_x, line_y, line_z])
        return marker

    def check_data_refs(self, obj, ignore_keys=None):
        """
        Walk all objects, tracking objects referenced by their metadata, and checks if any of the referenced objects (dicts or lists) is shared by more than one object.

        Currently is not able to check nested structures in metadata, only first level.
        """
            
        refs = {}
        for o in obj.iterate_objects():
            for (k, v) in o.extra.items():
                if isinstance(v, dict) or isinstance(v, list):
                    if ignore_keys is None or k not in ignore_keys:
                        refs.setdefault(id(v), []).append((o, k))

        for (k, v) in refs.items():
            if len(v) > 1:
                objstxt = ", ".join(["'%s'['%s']" % (o, ok) for o, ok in v]) #  if (ignore_keys is None or ok not in ignore_keys)])
                logger.warning("Objects references the same object %s from: %s" % (k, objstxt))    