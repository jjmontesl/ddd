# Jose Juan Montes 2019-2020

from ddd.pack.sketchy import urban, landscape
from ddd.ddd import ddd
import math

items = ddd.group3()

item = landscape.lighthouse()
items.append(item)
#item.show()

item = urban.post_box()
items.append(item)

item = urban.lamppost()
items.append(item)

item = landscape.powertower()
items.append(item)

item = urban.busstop_small(text="15")
items.append(item)

item = urban.bench()
items.append(item)

item = urban.sculpture_text("Test")
items.append(item)

item = urban.trafficlights()
item = item.rotate([0, 0, (math.pi / 4) - math.pi / 2])
items.append(item)

item = urban.fountain()
items.append(item)

items = ddd.distribute.grid(items)
items.append(ddd.helper.all())
items.show()
