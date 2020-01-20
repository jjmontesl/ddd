# Jose Juan Montes 2019-2020

from ddd.pack.sketchy import urban
from ddd.ddd import ddd

items = []

trafficlight = urban.trafficlights()
items.append(trafficlight)
trafficlight.show()

lamppost = urban.lamppost()
items.append(lamppost)
lamppost.show()

items = ddd.group(items)
#items = items.align_distribute([1, 1])
items.show()