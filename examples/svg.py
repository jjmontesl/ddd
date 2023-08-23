# Jose Juan Montes 2019-2023

import math
import webbrowser

from ddd.ddd import ddd

row = ddd.group2()
for i in range(3, 12 + 1):
    area = ddd.regularpolygon(i, 1.0, name="%d-Polygon" % i)
    area.extra['sides'] = i
    area.extra['text'] = "Sample text to test SVG metadata export (áéíóúñç)"
    row.append(area)
row = ddd.align.grid(row, 2.5, 1)
row = row.rotate(math.pi/2)

items = ddd.group2()

top_row = row
items.append(top_row)

mat_red = ddd.material(color="#ff0000", extra={'svg:fill-opacity': 1.0})
row_r = row.material(mat_red)
row_g = row.material(ddd.mats.green).translate([-0.2, -0.2])
row_b = row.material(ddd.mats.blue).translate([0.2, -0.2])
colors = ddd.group2([row_r, row_g, row_b], name="Mixed colors")
items.append(colors)

items = ddd.align.grid(items, 2.5, 1)


items.save('/tmp/test.svg')
webbrowser.open("file:///tmp/test.svg")
#items.show()


