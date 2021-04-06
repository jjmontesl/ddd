# Jose Juan Montes 2019-2020

from ddd.pack.sketchy import urban, landscape
from ddd.ddd import ddd
import math
import sys
from ddd.text import fonts
from trimesh.grouping import merge_vertices

items = ddd.group3()


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


