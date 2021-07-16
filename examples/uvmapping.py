# Jose Juan Montes 2019-2020

from ddd.pack.sketchy import urban, landscape
from ddd.ddd import ddd
import math
import random
from ddd.materials.atlas import TextureAtlasUtils

ddd.mats.traffic_signs = ddd.material(name="TrafficSigns", color="#ffffff", #color="#e01010",
                                  texture_path=ddd.DATA_DIR  + "/materials/traffic-signs-es/traffic_signs_es_0.png",
                                  atlas_path=ddd.DATA_DIR  + "/materials/traffic-signs-es/traffic_signs_es_0.plist",
                                  extra={'ddd:texture:resize': 2048})


# Cube
fig = ddd.box()
fig = fig.material(ddd.mats.traffic_signs)
fig = ddd.uv.map_cubic(fig)
fig.show()

fig = TextureAtlasUtils().create_sprite_rect(ddd.mats.traffic_signs)
fig.show()

fig = TextureAtlasUtils().create_sprite_from_atlas(ddd.mats.traffic_signs, "ES_P6.png")
fig.show()


'''
ddd.mats.roadmarks = ddd.material(name="Roadmarks", color='#e8e8e8',
                             texture_path=ddd.DATA_DIR + "/materials/road-marks-es/TexturesCom_Atlas_RoadMarkings2_White_1K_albedo_with_alpha.png",
                             atlas_path=ddd.DATA_DIR  + "/materials/road-marks-es/RoadMarkings2.plist")

fig = TextureAtlasUtils().create_sprite_from_atlas(ddd.mats.roadmarks, "give_way")
fig.show()
'''