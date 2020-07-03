# Jose Juan Montes 2019-2020

from ddd.pack.sketchy import urban, landscape
from ddd.ddd import ddd
import math
import sys
from ddd.text import fonts

items = ddd.group3()


# Extrusion to line (explicit)
fig1 = ddd.rect().extrude(1)
fig1 = fig1.subdivide_to_size(0.5)
items.append(fig1)
#fig1.show()


# All items
items = ddd.align.grid(items, space=10.0)
items.append(ddd.helper.all())
items.show()


