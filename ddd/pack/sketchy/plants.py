# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import math
import random

from ddd.ddd import ddd
from ddd.ops import filters


#def log(height=3.60, r=0.05):
#    pass
# TODO: This is actually the recursive tree builder (not trunk), generalize more, callbacks shall accept level and do their thing, returning followup settings
def recursivetree(height=2.25, r=0.30, fork_height_ratio=0.66, fork_angle=30.0, fork_r_scale=0.8, fork_spawn=3, fork_iters=2, fork_level=0, leave_callback=None, trunk_callback=None):

    # Create trunk part
    #section = ddd.point([0, 0, 0]).buffer(r, cap_style=ddd.CAP_ROUND, resolution=1).extrude(height * fork_height_ratio)
    section = trunk_callback()
    branches = []

    if fork_iters > 0:
        azimuth = 0
        num_items = fork_spawn + random.randint(-1, +1)

        if fork_level > 0:
            stop_prob = 0.1
            if random.uniform(0.0, 1.0) < stop_prob: num_items = 0

        # Only 1 leave in last iter
        if fork_iters == 1: num_items = 1

        for i in range(num_items):
            azimuth = (360.0 / fork_spawn) * i + (360.0 / fork_spawn) * random.uniform(-0.15, 0.15)
            if fork_iters > 1:
                ssection = recursivetree(height=height * fork_height_ratio * random.uniform(0.8, 1.2), r=r * fork_r_scale, fork_height_ratio=fork_height_ratio * random.uniform(0.8, 1.2), fork_r_scale=fork_r_scale,
                                         fork_iters=fork_iters - 1, fork_level=fork_level + 1, leave_callback=leave_callback, trunk_callback=trunk_callback)
            elif leave_callback:
                ssection = leave_callback()
            ssection = ssection.rotate([(fork_angle * random.uniform(0.65, 1.35)) / 180.0 * math.pi, 0.0, 0.0])
            ssection = ssection.rotate([0.0, 0.0, azimuth / 180.0 * math.pi])
            ssection = ssection.translate([0, 0, height * fork_height_ratio])
            ssection.name = "Branch (level %d)" % fork_level
            branches.append(ssection)

    #else:

    # Optionally increase fork_spawn each iteration (golden ratio)
    # Optionally randomize number of branches (fork_spawn)  each iteration

    branches = [section] + branches

    return ddd.group(branches)

def treetop(r=1.75, flatness=0.3, subdivisions=1):
    treetop = ddd.sphere(center=ddd.point([random.uniform(-r * 0.2, r * 0.2), random.uniform(-r * 0.2, r * 0.2), 0]), r=r, subdivisions=subdivisions)
    treetop = treetop.scale([1.0, 1.0, (1.0 - flatness) * random.uniform(0.85, 1.15)])
    treetop = filters.noise_random(treetop, scale=0.25)
    treetop = ddd.uv.map_spherical(treetop)
    treetop.extra['foliage'] = True
    treetop.name = "Treetop"
    return treetop

def palm_leaf(length=3.5):
    # Create grid, curve, bend along, bend gravity, make two sided
    obj = ddd.grid2([0, -1, 1, 1], 0.2, name="Palm leaf").triangulate()
    f1 = lambda x: math.sin(x * math.pi)
    f2 = lambda x: f1(x * f1(x)) * 0.1
    leafshape = lambda x, y, z, i: [x, y * (f2(x)), z]

    obj = obj.vertex_func(leafshape)
    obj = obj.scale([length, length, length])
    return obj

def plant(height=3.5, r=0.40, fork_height_ratio=0.7, fork_iters=3):

    def trunk_callback():
        section = ddd.regularpolygon(sides=5, r=r).extrude(height * fork_height_ratio)
        section = ddd.uv.map_cylindrical(section)
        section = section.material(ddd.mats.bark)
        return section
    def leave_callback():
        tt = treetop(r=2.5, subdivisions=0).material(ddd.mats.treetop)
        return tt

    obj = recursivetree(height=height, r=r, leave_callback=leave_callback, trunk_callback=trunk_callback,
                        fork_iters=fork_iters, fork_height_ratio=fork_height_ratio)

    # Booleans and grouping (cut trunk?, merge all)
    '''
    objs = [p for p in ptrunk.recurse_objects() if p.mesh]
    while len(objs) > 1:
        newo = objs[0].union(objs[1])
        newo.mesh.merge_vertices()
        objs = objs[2:] + [newo]
    obj = objs[0]
    obj = obj.material(mat_leaves)
    '''

    obj.name = "Plant"

    return obj

def tree_default(height=3.5, r=0.40):
    obj = plant(height=height, r=r, fork_iters=3)
    return obj

def tree_palm(height=8.5, r=0.50):

    def trunk_callback():
        section = ddd.regularpolygon(sides=5, r=r).extrude_step(ddd.regularpolygon(sides=5, r=r*0.6), height * 0.66)
        section = ddd.uv.map_cylindrical(section)
        section = section.material(ddd.mats.bark)
        return section
    def leave_callback():
        tt = palm_leaf(length=3.5).material(ddd.mats.treetop)
        return tt

    obj = recursivetree(height=height, r=r, fork_iters=1,
                        trunk_callback=trunk_callback, leave_callback=leave_callback)
    return obj

def tree_fir():
    """
    (Abeto)
    """
    pass

def tree_weeping_willow():
    pass



def bush(height=0.8):
    pass

def log(length=0.6):
    pass

def stump(height=0.3, r=0.3):
    """
    (Tocon)
    """
    pass
