# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020


import math

from ddd.ddd import ddd
from ddd.pack.sketchy import urban, landscape, plants
from ddd.catalog.catalog import PrefabCatalog


items = ddd.group3()

catalog = PrefabCatalog()

catalog.loadall()

item = catalog.instance('prefab1')  # Preload
if not item:
    item = urban.lamppost()
    #item = plants.plant(height=10)
    #item = urban.trafficlights()
    catalog.add('prefab1', item)

item = catalog.instance('prefab2')  # Preload
if not item:
    item = urban.trafficlights()
    #item = plants.plant(fork_iters=3, height=7)
    catalog.add('prefab2', item)

items = ddd.group3()

for i in range(6):
    item = catalog.instance('prefab1')
    items.append(item)
for i in range(6):
    item = catalog.instance('prefab2')
    item = item.rotate([0, 0, (math.pi / 4) - math.pi / 2])
    items.append(item)

# All items
items = ddd.align.grid(items, space=10.0)
items.append(ddd.helper.all())
items.save("/tmp/catalog.json")
items.save("/tmp/catalog.glb")
items.show()


