# Jose Juan Montes 2019-2020

from ddd.pack.sketchy import urban, landscape, industrial, plants
from ddd.ddd import ddd
import math

items = ddd.group3()

item = plants.tree_default()
items.append(item)

item = plants.tree_palm()
items.append(item)

#item.show()

items = ddd.align.grid(items)
items.append(ddd.helper.all())
items.show()
items.save("/tmp/test.glb")

