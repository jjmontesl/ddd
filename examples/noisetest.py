# Jose Juan Montes 2019-2020

import math
import random

from PIL import Image
import noise

from ddd.ddd import ddd
import numpy as np


def func_noise(coords):
    val = noise.pnoise2(coords[0] * 0.03, coords[1] * 0.03, octaves=3, persistence=2.2, lacunarity=0.7, repeatx=1024, repeaty=1024, base=0)
    return val

mapsize = 512

noise_matrix = np.zeros([mapsize , mapsize])
for xi in range(mapsize):
    for yi in range(mapsize):
        noise_matrix[yi, xi] = func_noise([xi, yi])

val_max = np.max(noise_matrix)
val_min = np.min(noise_matrix)

im = Image.fromarray(np.uint8((noise_matrix / 2 + 0.5)  * 255), "L")
im.save("/tmp/ddd-noise-test.png", "PNG")

#print(noise_matrix)
print("Noise min=%s, max=%s" % (val_min, val_max))
