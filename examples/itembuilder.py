# Jose Juan Montes 2019-2020

import math

from ddd.ddd import ddd
from ddd.pack.sketchy import lighting, urban, landscape, plants
from ddd.catalog.catalog import PrefabCatalog

from ddd.ext.item.itembuilder import DDDItemBuilder


# Demostrates the ItemBuilder class, which builds nested chains of objects from a description of their parts.

itembuilder = DDDItemBuilder()

items = ddd.group3()

builder_desc = {
    'item:func': 'ddd.pack.sketchy.support.fixture_round_wall',
    'item:slots': {
        'default': {
            'item:func': 'ddd.pack.sketchy.support.pole_arm_forge' ,
            'item:slots': {
                'below': {
                    'item:func': 'ddd.pack.sketchy.lighting.lamp_lantern'
                }
            }
        }
    }
}

obj = ddd.DDDNode3()
item = itembuilder.build(builder_desc, obj)
items.append(item)
item.show()


# All items
items = ddd.align.grid(items, space=4.0)
items.append(ddd.helper.all(grid_xy=True, plane_xy=False))

#items.save("itembuilder.json")

items.dump()
items.show()


