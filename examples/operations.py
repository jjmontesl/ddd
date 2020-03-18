# Jose Juan Montes 2019-2020

from ddd.pack.sketchy import urban, landscape
from ddd.ddd import ddd
import math

items = []

# Extrusion
fig = ddd.point([0, 0]).buffer(1.0, cap_style=ddd.CAP_ROUND).extrude(5.0).material(ddd.material(color='#00ff00'))
items.append(fig)
#fig.show()

# Triangulation with hole
fig1 = ddd.rect([-4, -2, 4, 2])
fig2 = ddd.rect([-3, -1, -1, 1])
fig = fig1.subtract(fig2).triangulate()
fig.show()

# Extrusion with hole
fig1 = ddd.rect([-4, -2, 4, 2])
fig2 = ddd.rect([-3, -1, -1, 1])
fig = fig1.subtract(fig2).extrude(1.0)
fig.show()

# Extrusion between shapes
fig1 = ddd.point([0, 0]).buffer(1.0)
fig2 = ddd.point([0, 0]).buffer(1.0, cap_style=ddd.CAP_ROUND)
fig3 = ddd.point([0, 0]).buffer(1.0)
fig = fig1.extrude_step(fig2, 3.0).extrude_step(fig3, 2.0)
fig.show()
items.append(fig)

# Extrusion
fig = ddd.point([0, 0]).buffer(1.0)
for i in range(10):
    fign = ddd.point([0, 0]).buffer(1.0).rotate(math.pi / 12 * i)
    fig = fig.extrude_step(fign, 0.5)
fig.show()
items.append(fig)

# Extrusion with steps with hole
fig1 = ddd.rect([-4, -2, 4, 2])
fig2 = ddd.rect([-3, -1, -1, 1])
figh = fig1.subtract(fig2)
fig = figh.extrude_step(figh, 1.0, cap=False)
fig = fig.extrude_step(figh.scale([0.8, 0.8, 0.8]), 1.0)
fig.show()

# All items
items = ddd.group(items)
#items = ddd.align.distribute(items)
#items.show()