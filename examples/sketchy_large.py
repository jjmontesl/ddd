# Jose Juan Montes 2019-2020

from ddd.pack.sketchy import urban, landscape, industrial
from ddd.ddd import ddd
from ddd.osm import items as osmitems
import math

items = ddd.group3()

item = industrial.crane_vertical()
items.append(item)

item = landscape.powertower()
items.append(item)

item = landscape.lighthouse()
items.append(item)
#item.show()

# TODO: Move generate_item_3d_historic_archaeological_site site generation to sketchy (?)
'''
item = osmitems.ItemsOSMBuilder(None).generate_item_3d_historic_archaeological_site(ddd.point())
items.append(item)
item.show()
'''

item = landscape.comm_tower()
items.append(item)


items = ddd.align.grid(items, 10.0)
items.append(ddd.helper.all())
items.show()
