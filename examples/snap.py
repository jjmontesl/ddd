# Jose Juan Montes 2019-2020

from ddd.pack.sketchy import urban, landscape
from ddd.ddd import ddd
import math
import random

# Snap point to object
point = ddd.point()
obj = ddd.point([3, 0]).buffer(1.0, cap_style=ddd.CAP_ROUND)
result = ddd.snap.project(point, obj).material(ddd.mats.highlight)
fig = ddd.group([point, obj, result])
fig.buffer(0.1).show()

# Snap with penetration
point = ddd.point()
obj = ddd.point([5, 0]).buffer(1.0, cap_style=ddd.CAP_ROUND)
result = ddd.snap.project(point, obj, penetrate=0.5).material(ddd.mats.highlight)
fig = ddd.group([point, obj, result])
fig.buffer(0.1).show()

# Irregular object
fig = ddd.group2()
coords = [[10, 10], [5, 9], [3, 12], [1, 5], [-8, 0], [10, 0]]
obj = ddd.polygon(coords)
fig.append(obj)
for i in range(10):
    point = ddd.point([random.uniform(-10, 10), random.uniform(-10, 10)])
    result = ddd.snap.project(point, obj, penetrate=0).material(ddd.mats.highlight)
    fig.append(point)
    fig.append(result)
fig.buffer(0.1).show()

# Irregular object
fig = ddd.group2()
coords = [[10, 10], [5, 9], [3, 12], [1, 5], [-8, 0], [10, 0]]
obj = ddd.polygon(coords)
fig.append(obj)
for i in range(10):
    point = ddd.point([random.uniform(-10, 10), random.uniform(-10, 10)])
    result = ddd.snap.project(point, obj, penetrate=1).material(ddd.mats.highlight)
    fig.append(point)
    fig.append(result)
fig.buffer(0.1).show()




