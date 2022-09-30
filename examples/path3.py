# ddd - D1D2D3
# Library for simple scene modelling.

import math

from ddd.ddd import ddd
from ddd.pack.sketchy.urban import catenary_cable, post
from ddd.pipeline.decorators import dddtask
from trimesh.path import entities
import trimesh

import numpy as np

"""
Tests of DDDPath3 objects.
"""

@dddtask()
def pipeline_start(pipeline, root):


    os = 0
    path2 = ddd.path3()  # [[0, 0, 0], [2, 2, 2], [4, 4, 4]])
    #print(path2.path3.entities)
    #path2.path3.entities = [ entities.Arc([0, 1, 2]) ]
    path2.path3 = trimesh.path.path.Path3D([entities.Arc([0, 1, 2])], [[0, os, 0], [4, os, 0], [4, os, 4]])
    print(path2.path3.entities)
    root.append(path2)

    os += 2
    path = ddd.path3()  # [[0, 0, 0], [2, 2, 2], [4, 4, 4]])
    path.path3 = trimesh.path.path.Path3D([entities.Bezier([0, 1, 2, 3])], [[0, os, 0], [4, os, 0], [4, os, 4], [8, os, 4]])
    print(path.path3.entities)
    root.append(path)
    root.append(ddd.path3(ddd.line([[0, os, 4], [12, os, 4]])).material(ddd.MAT_HIGHLIGHT))

    os += 2
    path = ddd.path3()  # [[0, 0, 0], [2, 2, 2], [4, 4, 4]])
    path.path3 = trimesh.path.path.Path3D([entities.BSpline([0, 1, 2, 3], [0, 0, 0, 1, 2, 2, 2])], [[0, os, 0], [4, os, 0], [4, os, 4], [8, os, 4]])
    print(path.path3.entities)
    root.append(path)
    root.append(ddd.path3(ddd.line([[0, os, 4], [12, os, 4]])).material(ddd.MAT_HIGHLIGHT))

    os += 2
    path = ddd.path3()
    path.path3 = trimesh.path.path.Path3D([entities.Bezier([0, 1, 2])], [[0, os, 0], [4, os, 0], [4, os, 4]])
    root.append(path)
    path = ddd.path3()
    path.path3 = trimesh.path.path.Path3D([entities.Bezier([0, 1, 2])], [[4, os, 4], [4, os, 8], [0, os, 8]])
    root.append(path)
    path = ddd.path3().material(ddd.MAT_HIGHLIGHT)
    path.path3 = trimesh.path.path.Path3D([entities.Arc([0, 1, 2])], [[0, os, 0], [4, os, 4], [0, os, 8]])
    root.append(path)

    os += 2
    path = ddd.path3()
    path.path3 = trimesh.path.path.Path3D([entities.BSpline([0, 1, 2, 3], [0, 0, 0, 1, 2, 2, 2])], [[0, os, 0], [2, os, 0], [4, os, 2], [4, os, 4]])
    root.append(path)
    path = ddd.path3()
    path.path3 = trimesh.path.path.Path3D([entities.BSpline([0, 1, 2, 3], [0, 0, 0, 1, 2, 2, 2])], [[4, os, 4], [4, os, 6], [2, os, 8], [0, os, 8]])
    root.append(path)
    path = ddd.path3().material(ddd.MAT_HIGHLIGHT)
    path.path3 = trimesh.path.path.Path3D([entities.Arc([0, 1, 2])], [[0, os, 0], [4, os, 4], [0, os, 8]])
    root.append(path)

    # 5 points "going down"
    os += 2
    path = ddd.path3()  # [[0, 0, 0], [2, 2, 2], [4, 4, 4]])
    path.path3 = trimesh.path.path.Path3D([entities.Bezier([0, 1, 2, 3, 4])], [[0, os, 0], [4, os, 0], [4, os, 4], [8, os, 4], [8, os, 0]])
    print(path.path3.entities)
    root.append(path)

    os += 2
    path = ddd.path3()  # [[0, 0, 0], [2, 2, 2], [4, 4, 4]])
    path.path3 = trimesh.path.path.Path3D([entities.BSpline([0, 1, 2, 3, 4], [0, 0, 0, 1, 2, 3, 3, 3])], [[0, os, 0], [4, os, 0], [4, os, 4], [8, os, 4], [8, os, 0]])
    print(path.path3.entities)
    root.append(path)

    # 4 points semicircle
    os += 2
    path = ddd.path3()  # [[0, 0, 0], [2, 2, 2], [4, 4, 4]])
    path.path3 = trimesh.path.path.Path3D([entities.Bezier([0, 1, 2, 3])], [[0, os, 0], [4, os, 0], [4, os, 8], [0, os, 8]])
    print(path.path3.entities)
    root.append(path)

    # 5 points circles
    os += 2
    path = ddd.path3()  # [[0, 0, 0], [2, 2, 2], [4, 4, 4]])
    path.path3 = trimesh.path.path.Path3D([entities.Bezier([0, 1, 2, 3, 4])], [[0, os, 0], [4, os, 0], [4, os, 4], [4, os, 8], [0, os, 8]])
    print(path.path3.entities)
    root.append(path)

    os += 2
    path = ddd.path3()  # [[0, 0, 0], [2, 2, 2], [4, 4, 4]])
    path.path3 = trimesh.path.path.Path3D([entities.BSpline([0, 1, 2, 3, 4], [0, 0, 0, 1, 2, 3, 3, 3])], [[0, os, 0], [4, os, 0], [4, os, 4], [4, os, 8], [0, os, 8]])
    print(path.path3.entities)
    root.append(path)

    '''
    os += 2
    path = ddd.path3()  # [[0, 0, 0], [2, 2, 2], [4, 4, 4]])
    path.path3 = trimesh.path.path.Path3D([
        entities.Line([0, 1, 2]),
        entities.Bezier([2, 3, 4]),
        entities.Line([4, 5]),
    ], [
        [0, os, 4], [4, os, 4], [8, os, 2],
        [12, os, 1], [12, os + 4, 0],
        [12, os + 8, 0]
    ])
    print(path.path3.entities)
    root.append(path)
    '''


    os += 2
    path = ddd.path3()  # [[0, 0, 0], [2, 2, 2], [4, 4, 4]])
    path.path3 = trimesh.path.path.Path3D([
        entities.Line([0, 1, 2]),
        entities.Bezier([2, 3, 4, 5]),
        #entities.BSpline([2, 3, 4, 5], [0, 0, 0, 1, 2, 3, 3, 3]),
        entities.Line([5, 6]),
    ], [
        [0, os, 4], [4, os, 4], [8, os, 2],
        #[12, os, 1], [12, os + 4, 0],
        [10, os, 1], [12, os + 2, 0], [12, os + 4, 0],
        [12, os + 8, 0]
    ])
    print(path.path3.entities)
    root.append(path)

    #line = ddd.point([0, os, 4]).line_to([4, os, 4]).line_to([14, 14, 2]).arc_to([14, 6, 0], [10, 10], False, 8).line_to([4, -4])
    #path3 = ddd.path3(line)
    #root.append(path3)

    os += 2
    line = ddd.line([[0, os, 0], [4, os, 0], [4, os, 4], [8, os, 4]])
    path = ddd.paths.round_corners(line, distance=1.0)
    root.append(path)

    os += 2
    line = ddd.line([[0, os, 0], [4, os, 0], [4, os, 4], [8, os, 4]])
    path = ddd.paths.round_corners(line, distance=3.0)
    root.append(path)


    root.append(ddd.helper.all())

    root.show()

