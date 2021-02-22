
# Jose Juan Montes 2019-2020

from ddd.pack.sketchy import urban, landscape, industrial
from ddd.ddd import ddd
import math

ddd.mats.traffic_signs = ddd.material(name="TrafficSigns", color="#ffffff", #color="#e01010",
                                  texture_path=ddd.DATA_DIR  + "/materials/traffic_signs/traffic_signs_es_0.png",
                                  atlas_path=ddd.DATA_DIR  + "/materials/traffic_signs/traffic_signs_es_0.plist")


items = ddd.group3()

for key in ddd.mats.traffic_signs.atlas.keys():
    key = 'es:' + key [3:-4]  # Ugly way of removing .png. This shouldn't be needed (remove extension on atlas keys!)
    item = urban.traffic_sign(key)
    if item:
        items.append(item)


items = ddd.align.grid(items)
items.append(ddd.helper.all())
items.save("/tmp/test.glb")
#items.show()  # Hangs PC with software renderer
