# Jose Juan Montes 2019-2020

from ddd.pack.sketchy import urban, landscape, industrial
from ddd.ddd import ddd
import math

items = ddd.group3()

item = industrial.crane_vertical()
items.append(item)
item.show()

#items = ddd.align.grid(items)
#items.append(ddd.helper.all())
#items.show()
