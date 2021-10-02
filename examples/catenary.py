# Jose Juan Montes 2019-2021

from ddd.ddd import ddd
from ddd.pack.sketchy.urban import catenary_cable

items = ddd.group3()

pa = [0, 0, 5]
pb = [15, 2, 9]
obj = catenary_cable(pa, pb)
#obj.show()
items.append(obj)

# All items
items = ddd.align.grid(items, space=10.0)
items.append(ddd.helper.all())
items.show()

