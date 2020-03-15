# Jose Juan Montes 2019-2020

from ddd.pack.sketchy import urban, landscape
from ddd.ddd import ddd

items = []

busstop_small = urban.busstop_small(text="15")
busstop_small.show()

lighthouse = landscape.lighthouse()
lighthouse.show()

bench = urban.bench()
bench.show()

sculpture_text = urban.sculpture_text("Test")
sculpture_text.show()

trafficlight = urban.trafficlights()
items.append(trafficlight)
trafficlight.show()

lamppost = urban.lamppost()
items.append(lamppost)
lamppost.show()

items = ddd.group(items)
#items = items.align_distribute([1, 1])
items.show()