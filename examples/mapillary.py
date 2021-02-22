# Jose Juan Montes 2019-2020

from ddd.pack.sketchy import urban, landscape, industrial, plants
from ddd.ddd import ddd
import math
from ddd.geo.sources.mapillary import MapillaryClient

items = ddd.group3()

mc = MapillaryClient("WFBxUUhWTlFhOGNhanZXUWFFTVNpNzoyMmM5OTUyMWQwOTZhMDYw")
data = mc.images_list([-3.693955, 40.400690], limit=35)

for feature in data['features'][:]:

    key = feature['properties']['key']
    pano = feature['properties']['pano']
    camera_angle = feature['properties']['ca']
    geom = feature['geometry']
    coords = geom['coordinates']
    coords = (float(coords[0]) * 111000.0, float(coords[1]) * 111000.0)

    print("Image: %s  CameraAngle: %s  Pano: %s  Coords: %s" % (key, camera_angle, pano, coords))


    mc.request_image(key)
    image = mc.image_textured(feature)
    image_height = 1.5
    image = image.translate([0, 1, 0])
    image = image.rotate([0, 0, (-camera_angle + 180) * ddd.DEG_TO_RAD])
    image = image.translate([coords[0], coords[1], image_height])

    cam = ddd.cube(d=0.1).translate([coords[0], coords[1], image_height]).material(ddd.mats.highlight)

    obj = ddd.group([image, cam], name="Image")

    items.append(obj)



#item.show()

#items = ddd.align.grid(items)
items = items.recenter(onplane=True)
items.append(ddd.helper.all())
items.save("/tmp/test.json")
items.save("/tmp/test.glb")
items.show()
