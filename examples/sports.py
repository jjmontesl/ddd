# Jose Juan Montes 2019-2020

from ddd.pack.sketchy import sports_fields, urban, landscape
from ddd.ddd import ddd
import math
import random


'''
area = ddd.polygon([[0, 0], [10, 0], [10, 5], [0, 5]])
lines = sports.football_field_lines_area(area).translate([0, 0, 0.05])
area = area.triangulate().material(ddd.mats.pitch)
item = ddd.group2([area, lines])
items.append(item)
item.show()
'''

functions = (sports_fields.handball_field_lines, sports_fields.basketball_field_lines,
             sports_fields.tennis_field_lines, sports_fields.football_field_lines)

count = 3
for m in functions:
    items = ddd.group3()
    for i in range(count):
        area = ddd.polygon([[0, 0], [10, 0], [10, 5], [0, 5]]).scale(1 + i * 3).rotate(i * 2 * math.pi / count)
        lines = sports_fields.field_lines_area(area, m).translate([0, 0, 0.05])
        area = area.triangulate().material(ddd.mats.pitch)
        item = ddd.group2([area, lines])
        items.append(item)
    items.show()

    area = ddd.regularpolygon(7, r=random.uniform(12, 20)).scale([random.uniform(0.5, 1.5), random.uniform(0.5, 1.5)]).rotate(random.uniform(0, math.pi * 2))
    lines = sports_fields.field_lines_area(area, m).translate([0, 0, 0.05])
    area = area.triangulate().material(ddd.mats.pitch)
    item = ddd.group2([area, lines])
    item.show()




'''
area = ddd.polygon([[0, 0], [10, 0], [10, 5], [0, 5]])
lines = sports.tennis_field_lines(area).translate([0, 0, 0.05])
area = area.triangulate().material(ddd.mats.pitch)
item = ddd.group2([area, lines])
items.append(item)
item.show()
'''


#items = ddd.align.grid(items)
#items.append(ddd.helper.all())
#items.show()
