# Jose Juan Montes 2019-2020

import math
import random

import trimesh

from ddd.ddd import ddd
from ddd.pipeline.decorators import dddtask


@dddtask()
def pipeline_start(pipeline, root):
    """
    """

    # TODO: second point is colinear if we use [6.0, 0.0], and the division gets removed in the buffer operation, which is sometimes not desired
    line = ddd.point([0, 0, 4]).line_to([6, 0.01, 4]).line_to([18, 0, 2]).arc_to([24, -6, 0], [18, -6], False, 8).line_to([24, -18, 0])

    #line2 = ddd.point([3, 25, 4]).line_to([7.01, 21.01, 4]).line_to([14, 14, 2]).arc_to([14, 6, 0], [10, 10], False, 8).line_to([4, -4])
    #line2 = line2.rotate(math.pi / 4).translate([14, 6])
    #line.append(line2)

    buffered = ddd.group([
        line.buffer(2.0, cap_style=ddd.CAP_ROUND),
        line.buffer(2.5, cap_style=ddd.CAP_ROUND),
    ])

    # For each point in the border, calculate closest
    for c in buffered.coords_iterator():
        coords_p, segment_idx, segment_coords_a, segment_coords_b, closest_obj, closest_d = line.closest_segment(ddd.point(c))
        marker = ddd.line([(c[0], c[1], coords_p[2]), coords_p])
        marker = ddd.path3(marker).material(ddd.mats.highlight)
        root.append(marker)

    root.append(line.flatten())
    root.append(buffered.outline().flatten())

    root.show()
