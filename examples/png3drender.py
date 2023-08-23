# Jose Juan Montes 2019-2020

from ddd.pack.sketchy import urban, landscape, industrial
from ddd.ddd import ddd
import math

items = ddd.group3()


'''
item = industrial.barrel_metal()
items.append(item)

item = industrial.pipe_segment()
items.append(item)

item = industrial.crate()
items.append(item)

item = landscape.powertower()
items.append(item)

item = landscape.lighthouse()
items.append(item)
'''

item = industrial.crane_vertical()
items.append(item)

#item.show()

items = ddd.align.grid(items, 8.0)
#items.append(ddd.helper.all())
#items.show()

camera = ddd.DDDNode3()
camera.transform.position = (0, -20, 0)  # currently not working as trimesh will center the object on screen and fix distance
#camera.transform.look_at(items.center())
camera.transform.rotate([-30 * ddd.DEG_TO_RAD, 0, 45 * ddd.DEG_TO_RAD])

root = ddd.DDDNode3()
root.append(items)

items.transform = camera.transform.copy()
items.transform.invert()  # FIXME: here using the child node to invert the camera view, as cameras are not yet supported and neither root node transforms
#items.transform.rotate([0, 45, 180])

root.save("/tmp/ddd-image-3d.png")


'''
"""
Adapted from trimesh example raytrace.py
----------------
Install `pyembree` for a speedup (600k+ rays per second)
"""
import PIL.Image
import trimesh
import numpy as np
from typing import List

# test on a simple mesh
mesh = item.combine().mesh

# scene will have automatically generated camera and lights
scene = mesh.scene()

# any of the automatically generated values can be overridden
# set resolution, in pixels
scene.camera.resolution = [640, 480]
# set field of view, in degrees
# make it relative to resolution so pixels per degree is same
scene.camera.fov = 60 * (scene.camera.resolution /
                         scene.camera.resolution.max())

# convert the camera to rays with one ray per pixel
origins, vectors, pixels = scene.camera_rays()

# do the actual ray- mesh queries
points, index_ray, index_tri = mesh.ray.intersects_location(
    origins, vectors, multiple_hits=False)

# for each hit, find the distance along its vector
depth = trimesh.util.diagonal_dot(points - origins[0],
                                  vectors[index_ray])
# find pixel locations of actual hits
pixel_ray = pixels[index_ray]

# create a numpy array we can turn into an image
# doing it with uint8 creates an `L` mode greyscale image
a = np.zeros(scene.camera.resolution, dtype=np.uint8)

# scale depth against range (0.0 - 1.0)
depth_float = ((depth - depth.min()) / depth.ptp())

# convert depth into 0 - 255 uint8
depth_int = (depth_float * 255).round().astype(np.uint8)
# assign depth to correct pixel locations
a[pixel_ray[:, 0], pixel_ray[:, 1]] = depth_int
# create a PIL image from the depth queries
img = PIL.Image.fromarray(a)

# show the resulting image
img.show()
'''