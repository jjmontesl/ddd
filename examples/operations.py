# Jose Juan Montes 2019-2020

from ddd.pack.sketchy import urban, landscape
from ddd.ddd import ddd
import math

items = ddd.group3()

# Extrusion to line (empty geometry)
fig1 = ddd.rect([-4, -2, 4, 2])
fig = fig1.extrude_step(fig1.buffer(-2.5), 1.0)
items.append(fig)
#fig.show()

fig1 = ddd.rect([-4, -2, 4, 2])
fig = fig1.extrude_step(fig1.buffer(-2.5), 1.0)
fig = fig.extrude_step(fig1, 1.0)
items.append(fig)
#fig.show()

# Triangulation with hole
fig1 = ddd.rect([-4, -2, 4, 2])
fig2 = ddd.rect([-3, -1, -1, 1])
fig = fig1.subtract(fig2).triangulate()
items.append(fig)
#fig.show()

# Extrusion with hole
fig1 = ddd.rect([-4, -2, 4, 2])
fig2 = ddd.rect([-3, -1, -1, 1])
fig = fig1.subtract(fig2).extrude(1.0)
items.append(fig)
#fig.show()

# Extrusion with steps with hole
fig1 = ddd.rect([-4, -2, 4, 2])
fig2 = ddd.rect([-3, -1, -1, 1])
figh = fig1.subtract(fig2)
fig = figh.extrude_step(figh, 1.0, base=False)
fig = fig.extrude_step(figh.scale([0.8, 0.8, 0.8]), 1.0)
items.append(fig)
#fig.show()

# Simple extrusion
fig = ddd.point([0, 0]).buffer(1.0, cap_style=ddd.CAP_ROUND).extrude(5.0)
items.append(fig)
#fig.show()

# Simple extrusion no caps
fig = ddd.point([0, 0]).buffer(1.0, cap_style=ddd.CAP_ROUND)
fig = fig.extrude_step(fig, 5.0, base=False, cap=False)
items.append(fig)
#fig.show()

# Extrusion between shapes
fig1 = ddd.point([0, 0]).buffer(1.0)
fig2 = ddd.point([0, 0]).buffer(1.0, cap_style=ddd.CAP_ROUND)
fig3 = ddd.point([0, 0]).buffer(1.0)
fig = fig1.extrude_step(fig2, 3.0).extrude_step(fig3, 2.0)
items.append(fig)
#fig.show()

# Extrusion
fig = ddd.point([0, 0]).buffer(1.0)
for i in range(10):
    fign = ddd.point([0, 0]).buffer(1.0).rotate(math.pi / 12 * i)
    fig = fig.extrude_step(fign, 0.5)
items.append(fig)
#fig.show()

# Pointy end
fig = ddd.point().buffer(2.0, cap_style=ddd.CAP_ROUND)
fig = fig.extrude_step(ddd.point(), 5.0)
items.append(fig)

# More strange shapes (ie. roofs that failed)
coords = [[10, 10], [5, 9], [3, 12], [1, 5], [-8, 0], [10, 0]]
#coords.reverse()
fig = ddd.polygon(coords)
fig = fig.extrude_step(fig.buffer(-3), 1)
items.append(fig)
fig.show()


# All items
items = ddd.align.grid(items, width=2, space=10.0)
#items.append(ddd.helper.all())
items.show()


