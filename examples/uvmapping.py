# Jose Juan Montes 2019-2020

from ddd.pack.sketchy import urban, landscape
from ddd.ddd import ddd
import math
import random

ddd.mats.traffic_signs = ddd.material(name="TrafficSigns", color="#ffffff", #color="#e01010",
                                  texture_path=ddd.DATA_DIR  + "/materials/traffic_signs/traffic_signs_es_0.png",
                                  atlas_path=ddd.DATA_DIR  + "/materials/traffic_signs/traffic_signs_es_0.plist")

# Cube
fig = ddd.box()
fig = fig.material(ddd.mats.traffic_signs)
fig = ddd.uv.map_cubic(fig)
fig.show()

