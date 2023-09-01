# Jose Juan Montes 2019-2020

import math

from ddd.ddd import ddd
from ddd.pack.sketchy import lighting, urban, landscape, plants
from ddd.catalog.catalog import PrefabCatalog


# For clean run, run as:  ddd lights.py --export-meshes --catalog-overwrite

# Todo: rename this as a catalog example, and put light examples in sketchy_lighting.py

items = ddd.group3()


item = urban.lamppost()
#item = plants.plant(height=10)
#item = urban.trafficlights()
#item.extra['ddd:static'] = False
items.append(item)


item = lighting.lamp_lantern()
#item.extra['ddd:static'] = True
items.append(item)


item = lighting.lamp_block_based()
#item.extra['ddd:static'] = True
items.append(item)

item = lighting.lamp_block_based_bevel()
#item.extra['ddd:static'] = True
items.append(item)

item = lighting.lamp_lantern_grid()
#item.extra['ddd:static'] = True
items.append(item)

item = lighting.skylight_grid()
#item.extra['ddd:static'] = True
items.append(item)

item = lighting.skylight_grid(round=0)
#item.extra['ddd:static'] = True
items.append(item)


# All items
items = ddd.align.grid(items, space=4.0)
items.append(ddd.helper.all(grid_xy=True, plane_xy=False))

#items.save("lights.glb")
#items.save("lights.json")

items.dump()
items.show()


