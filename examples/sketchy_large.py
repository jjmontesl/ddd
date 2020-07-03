# Jose Juan Montes 2019-2020

from ddd.pack.sketchy import urban, landscape, industrial
from ddd.ddd import ddd
import math

items = ddd.group3()

item = industrial.crane_vertical()
items.append(item)

item = landscape.powertower()
items.append(item)

item = landscape.lighthouse()
items.append(item)
#item.show()



items = ddd.align.grid(items, 10.0)
items.append(ddd.helper.all())
items.show()
