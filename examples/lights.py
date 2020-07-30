# Jose Juan Montes 2019-2020

import math

from ddd.ddd import ddd
from ddd.pack.sketchy import urban, landscape, plants
from ddd.catalog.catalog import PrefabCatalog


items = ddd.group3()

catalog = PrefabCatalog()

#catalog.loadall()

item = catalog.instance('prefab-lamppost')
if not item:
    item = urban.lamppost()
    #item = plants.plant(height=10)
    #item = urban.trafficlights()
    item = catalog.add('prefab-lamppost', item)
item.extra['ddd:static'] = False
items.append(item)


item = catalog.instance('prefab-bench')
if not item:
    item = urban.bench()
    #item = plants.plant(height=10)
    #item = urban.trafficlights()
    item = catalog.add('prefab-bench', item)
item.extra['ddd:static'] = True
items.append(item)

# All items
items = ddd.align.grid(items, space=10.0)
items.append(ddd.helper.all())
items.save("/tmp/lights.json")
items.save("/tmp/lights.glb")
catalog.export("/tmp/catalog.glb")
items.show()


