# ddd - D1D2D3
# Library for simple scene modelling.

import math

from ddd.ddd import ddd
from ddd.pack.sketchy.urban import catenary_cable, post
from ddd.pipeline.decorators import dddtask


@dddtask(order="10",
         params={
             'ddd:example:catenary:length_ratio_factor': 0.025
        })
def pipeline_start(pipeline, root):
    """
    Draws several catenary cables.
    """

    items = ddd.group3(name="Catenary test")


    length_ratio_factor = pipeline.data.get('ddd:example:catenary:length_ratio_factor', 0.025)
    pipeline.data['ddd:example:catenary:length_ratio_factor'] = length_ratio_factor

    post_a = post(6)
    items.append(post_a)

    pa = [0, 0, 6]
    for i in range(12):
        d = 80  # 2 * i
        h = i
        a = math.pi * 2 / 12 * i

        pd = d / 12 * (i + 1)
        pb = [math.cos(a) * pd, math.sin(a) * pd, h]
        obj = catenary_cable(pa, pb, length_ratio=1 + (length_ratio_factor / (d/10)))
        #obj.show()
        items.append(obj)

        post_b = post(h + 0.1, r=0.2)
        post_b = post_b.rotate(ddd.VECTOR_UP * a)
        post_b = post_b.translate([pb[0], pb[1], 0])
        items.append(post_b)

    # All items
    #items = ddd.align.grid(items, space=10.0)
    items.append(ddd.helper.all())
    items.show()

    root.append(items)

