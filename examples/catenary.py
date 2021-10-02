# Jose Juan Montes 2019-2021

from ddd.ddd import ddd
from ddd.pack.sketchy.urban import catenary_cable, post
import math

items = ddd.group3()

post_a = post(6)
items.append(post_a)

pa = [0, 0, 6]
for i in range(12):
    d = 80  # 2 * i
    h = i
    a = math.pi * 2 / 12 * i

    pd = d / 12 * (i + 1)
    pb = [math.cos(a) * pd, math.sin(a) * pd, h]
    obj = catenary_cable(pa, pb, length_ratio=1 + (0.05 / (d/10)))
    #obj.show()
    items.append(obj)

    post_b = post(h + 0.1).translate([pb[0], pb[1], 0])
    items.append(post_b)

# All items
#items = ddd.align.grid(items, space=10.0)
items.append(ddd.helper.all())
items.show()

