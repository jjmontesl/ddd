# Jose Juan Montes 2019-2020

from ddd.pack.sketchy import urban, landscape
from ddd.ddd import ddd
import math
import sys
from ddd.text import fonts
from trimesh.grouping import merge_vertices

items = ddd.group3()



# Subdivision to grid
fig1 = ddd.rect([-4, -2, 4, 2])
fig2 = ddd.rect([-3, -1, -1, 1])
figh = fig1.subtract(fig2)
fig = figh.extrude_step(figh, 1.0, base=False, method=ddd.EXTRUSION_METHOD_SUBTRACT)
fig = fig.extrude_step(figh.buffer(-0.25), 1.0, method=ddd.EXTRUSION_METHOD_SUBTRACT)
fig = ddd.meshops.subdivide_to_grid(fig, 0.5)
fig.show()
items.append(fig)

# Test slicing with plane
figa = ddd.meshops.slice_plane(fig, [-1, -1, -1], [0.3, 0.3, 0.3])
figb = ddd.meshops.slice_plane(fig, [1, 1, 1], [0.3, 0.3, 0.3])
ddd.group([figa, figb.material(ddd.MAT_HIGHLIGHT)]).show()


# Subdivide to grid
coords = [[10, 10], [5, 9], [3, 12], [1, 5], [-8, 0], [10, 0]]
ref = ddd.polygon(coords).subtract(ddd.rect([1,1,2,2]))
obj = ref.triangulate()
obj = ddd.meshops.subdivide_to_grid(obj, 2.0)
#obj= obj.subdivide_to_size(2.0)
#ddd.group3([obj, ref.triangulate().material(ddd.MAT_HIGHLIGHT).translate([0, 0, -1])]).show()
items.append(obj.scale([0.1, 0.1, 1]).translate([0, 0, 1]))


# Subdivide to grid (cube)
obj = ddd.cube(d=2)
obj = obj.material(ddd.mats.dirt)
obj = ddd.uv.map_cubic(obj)
obj = ddd.meshops.subdivide_to_grid(obj, 0.5)
#obj.show()
items.append(obj)

# Subdivide
fig1 = ddd.rect().extrude(1)
fig1 = fig1.subdivide_to_size(0.5)
items.append(fig1)
#fig1.show()


fig1 = ddd.rect([1, 3]).extrude(1)
fig1 = fig1.subdivide_to_size(0.5)
items.append(fig1)

# Pointy end
fig = ddd.point().buffer(0.5, cap_style=ddd.CAP_ROUND)
fig = fig.extrude_step(ddd.point(), 2)
fig = fig.subdivide_to_size(0.5)
items.append(fig)


# Remove bottom test
fig = ddd.cube(d=2)
fig = fig.subdivide_to_size(1.0)
fig = ddd.meshops.remove_faces_pointing(fig, ddd.VECTOR_DOWN)
items.append(fig)


# All items
items = ddd.align.grid(items, space=10.0)
items.append(ddd.helper.all())
items.show()


