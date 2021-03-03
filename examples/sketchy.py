# Jose Juan Montes 2019-2020

from ddd.pack.sketchy import urban, landscape, industrial, interior
from ddd.ddd import ddd
import math


ddd.mats.traffic_signs = ddd.material(name="TrafficSigns", color="#ffffff", #color="#e01010",
                                  texture_path=ddd.DATA_DIR  + "/materials/traffic_signs/traffic_signs_es_0.png",
                                  atlas_path=ddd.DATA_DIR  + "/materials/traffic_signs/traffic_signs_es_0.plist")


items = ddd.group3()


item = urban.drinking_water()
items.append(item)
#item.show()


item = urban.bollard()
items.append(item)

item = urban.bell()
items.append(item)

item = urban.fire_hydrant()
items.append(item)


item = urban.childrens_playground_swingset()
items.append(item)

item = urban.childrens_playground_sandbox()
items.append(item)

item = urban.childrens_playground_slide()
items.append(item)

item = urban.childrens_playground_arc()
items.append(item)


item = urban.patio_table()
items.append(item)

item = urban.patio_chair()
items.append(item)

item = urban.patio_umbrella()
items.append(item)

item = urban.post_box()
items.append(item)

item = urban.lamppost()
items.append(item)

item = urban.busstop_small(text="Bus Stop")
items.append(item)

item = urban.bench()
items.append(item)

item = urban.sculpture()
items.append(item)

item = urban.sculpture_text("Test")
item = urban.pedestal(item)
items.append(item)

item = urban.sculpture_text("Monumental test string", vertical=True, height=12)
items.append(item)


item = urban.trafficlights()
#item = item.rotate([0, 0, (math.pi / 4) - math.pi / 2])
items.append(item)

item = urban.fountain()
items.append(item)

item = urban.wayside_cross()
items.append(item)

item = urban.trash_bin()
items.append(item)

item = urban.trash_bin_post()
items.append(item)

# Road signs
item = urban.traffic_sign('stop')
items.append(item)
#item.show()
item = urban.traffic_sign('give_way')
items.append(item)
#item.show()
item = urban.traffic_sign('es:s13')
items.append(item)
#item.show()
item = urban.traffic_sign('es:p1')
items.append(item)
item = urban.traffic_sign('es:r101')
items.append(item)
item = urban.traffic_sign('es:r1')
items.append(item)
item = urban.traffic_sign('es:r2')
items.append(item)
item = urban.traffic_sign('es:r3')
items.append(item)
item = urban.traffic_sign('es:r6')
items.append(item)
item = urban.traffic_sign('es:r402')
items.append(item)
item = urban.traffic_sign('es:r500')
items.append(item)
item = urban.traffic_sign('es:r504')
items.append(item)
#item = urban.traffic_sign('es:r505-b')
#items.append(item)
item = urban.traffic_sign('es:r505')
items.append(item)
item = urban.traffic_sign('es:r506')
items.append(item)


#item.show()

'''
# Reduced
items_org = items.copy()

items = ddd.meshops.reduce(items_org)

items = ddd.align.grid(items)
items.append(ddd.helper.all())
items.show()

items = ddd.meshops.reduce_bounds(items_org)

items = ddd.align.grid(items)
items.append(ddd.helper.all())
items.show()
'''

items = ddd.align.grid(items)
items.append(ddd.helper.all())
items.show()
items.save("/tmp/test.glb")

