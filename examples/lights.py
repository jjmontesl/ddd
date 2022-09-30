# Jose Juan Montes 2019-2020

import math

from ddd.ddd import ddd
from ddd.pack.sketchy import lighting, urban, landscape, plants
from ddd.catalog.catalog import PrefabCatalog


# For clean run, run as:  ddd lights.py --export-meshes --catalog-overwrite

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

item = catalog.instance('prefab-lamp_block_based')
if not item:
    item = lighting.lamp_block_based()
    item = catalog.add('prefab-lamp_block_based', item)
item.extra['ddd:static'] = True
items.append(item)

item = catalog.instance('prefab-lamp_block_based_bevel')
if not item:
    item = lighting.lamp_block_based_bevel()
    item = catalog.add('prefab-lamp_block_based_bevel', item)
item.extra['ddd:static'] = True
items.append(item)

'''
item = catalog.instance('prefab-lamp')
if not item:
    item = lighting.lamp_floor_angled_corner()
    item = catalog.add('prefab-lamp', item)
item.extra['ddd:static'] = True
items.append(item)
'''


# All items
items = ddd.align.grid(items, space=4.0)
items.append(ddd.helper.all())
items.save("lights.json")
items.dump()

#items.save("lights.glb")
#catalog.export("/tmp/catalog.glb")

items.show()


