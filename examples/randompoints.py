# Jose Juan Montes 2019-2020

from ddd.ddd import ddd
import math
import random
import noise

# Irregular object
fig = ddd.group2()
coords = [[10, 10], [5, 9], [3, 12], [1, 5], [-8, 0], [10, 0]]
obj = ddd.polygon(coords)
fig.append(obj)

def filter_func_noise(coords):
    val = noise.pnoise2(coords[0] * 0.1, coords[1] * 0.1, octaves=2, persistence=0.5, lacunarity=2, repeatx=1024, repeaty=1024, base=0)
    return (val > random.uniform(-0.5, 0.5))

points = obj.random_points(200, filter_func=filter_func_noise)
for coords in points:
    point = ddd.point(coords).material(ddd.MAT_HIGHLIGHT)
    fig.append(point)

fig.buffer(0.1).show()


