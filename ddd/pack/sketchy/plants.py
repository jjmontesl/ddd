# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import math
import random

from ddd.ddd import ddd
from ddd.ops import filters, reduction


# TODO: Move tree generation algorithm to a generic "trees pack", and keep here only parameters and other sketchy related stuff

# See: https://chewitt.me/Papers/CTH-Dissertation-2017.pdf (Procedural generation of tree models for use in computer graphics)
#      and its Blender plugin: https://github.com/friggog/tree-gen/blob/master/parametric/gen.py


#def log(height=3.60, r=0.05):
#    pass
# TODO: This is actually the recursive tree builder (not trunk), generalize more, callbacks shall accept level and do their thing, returning followup settings
def recursivetree(height=2.25, r=0.30, fork_height_ratio=1.0, fork_angle=30.0, fork_r_scale=0.8, fork_spawn=3, fork_iters=2, fork_level=0, leaves_callback=None, trunk_callback=None):

    # Create trunk part
    #section = ddd.point([0, 0, 0]).buffer(r, cap_style=ddd.CAP_ROUND, resolution=1).extrude(height * fork_height_ratio)

    branches = []
    if fork_iters > 0:
        section = trunk_callback(height * fork_height_ratio)

        azimuth = 0
        num_items = fork_spawn + random.choice([-1, 0, +1])

        if fork_level > 1:
            stop_prob = 0.1
            if random.uniform(0.0, 1.0) < stop_prob: num_items = 0

        # Only 1 leave in last iter
        if fork_iters == 1: num_items = 1

        offset = random.uniform(0, 360)
        for i in range(num_items):
            azimuth = offset + (360.0 / fork_spawn) * i + (360.0 / fork_spawn) * random.uniform(-0.15, 0.15)
            if fork_iters > 1:
                ssection = recursivetree(height=height * (1 - fork_height_ratio) * random.uniform(0.8, 1.2), r=r * fork_r_scale, fork_height_ratio=fork_height_ratio * random.uniform(0.8, 1.2), fork_r_scale=fork_r_scale,
                                         fork_iters=fork_iters - 1, fork_level=fork_level + 1, leaves_callback=leaves_callback, trunk_callback=trunk_callback)
            elif leaves_callback:
                ssection = leaves_callback(height * (1 - fork_height_ratio))
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


def recursivetree_new(height, spawn=1, levels=1, #fork_height_ratio=2/3,
                  level=0, angle=0,
                  node_callback=None,

                  #, r=0.30, fork_height_ratio=0.66, fork_angle=30.0, fork_r_scale=0.8, fork_spawn=3, fork_iters=2, fork_level=0, leaves_callback=None, trunk_callback=None):
                  ):
    """
    """
    # Generate nodes

    azimuth = 0
    offset = random.uniform(0, 2 * math.pi)

    branches = []
    for i in range(spawn):
        azimuth = offset + (2 * math.pi / spawn) * i + random.uniform(math.pi / 8)
        ssection = node_callback(height, levels, level)

        #ssection = recursivetree(height=height * fork_height_ratio * random.uniform(0.8, 1.2), r=r * fork_r_scale, fork_height_ratio=fork_height_ratio * random.uniform(0.8, 1.2), fork_r_scale=fork_r_scale,
        #                         fork_iters=fork_iters - 1, fork_level=fork_level + 1, leaves_callback=leaves_callback, trunk_callback=trunk_callback)

        ssection = ssection.rotate([(angle * random.uniform(0.80, 1.20)), 0.0, 0.0])
        ssection = ssection.rotate([0.0, 0.0, azimuth])
        #ssection = ssection.translate([0, 0, height * fork_height_ratio])
        ssection.name = "Branch (level %d)" % fork_level
        branches.append(ssection)
    # Call recursively
    if level < levels:
        pass



def treetop(r=1.75, flatness=0.3, subdivisions=1):
    treetop = ddd.sphere(center=ddd.point([random.uniform(-r * 0.2, r * 0.2), random.uniform(-r * 0.2, r * 0.2), 0]), r=r, subdivisions=subdivisions)
    treetop = treetop.scale([1.0, 1.0, (1.0 - flatness) * random.uniform(0.85, 1.15)])
    treetop = filters.noise_random(treetop, scale=0.25)
    treetop = ddd.uv.map_spherical(treetop)
    treetop.extra['ddd:collider'] = False
    treetop.name = "Treetop"
    return treetop

def tree_default(height=3.5, r=0.40, fork_iters=2, fork_height_ratio=0.35):

    height = height * (1 + fork_height_ratio)

    def trunk_callback(height):
        section = ddd.regularpolygon(sides=5, r=r).extrude(height)
        section = ddd.uv.map_cylindrical(section)
        section = section.material(ddd.mats.bark)
        return section
    def leaves_callback(height):
        tt = treetop(r=0.5 + 0.4 * height, subdivisions=0).material(ddd.mats.treetop)
        return tt

    obj = recursivetree(height=height, r=r, leaves_callback=leaves_callback, trunk_callback=trunk_callback,
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

    obj.name = "Tree Default"

    objtrunk = obj.select(func=lambda o: o.mat == ddd.mats.bark).combine()
    objleaves = obj.select(func=lambda o: o.mat == ddd.mats.treetop).combine()
    obj = ddd.group3([objtrunk, objleaves], name="Tree Default")

    return obj

def palm_leaf(length=3, fallfactor=1):
    """
    Length is length in X axis. Fall factor will stretch the leaf longer.

        Fallfactor of 2 is too heavy. Shall be between 0.7 - 1.x.
        Fallfactor of 0.7 is 0.1 raised over the ground (unit leaf)
        Fallfactor of 1.65 is -0.5 below the ground (unit leaf) and makes the leaf much longer.
    """

    # Create grid, top down palm shape, bend across (V shape), bend along with gravity, make two sided
    obj = ddd.grid3([0, -1, 1, 1], [0.2, 0.5], name="Palm leaf")

    f1 = lambda x: math.sin(x * math.pi)
    f2 = lambda x: f1(x * f1(x)) * 0.1
    leafshape = lambda x, y, z, i: [x, y * (f2(1 - x)), z]
    obj = obj.vertex_func(leafshape)

    f1 = lambda x: math.log(abs(x) + 1) * 0.25
    leafshape = lambda x, y, z, i: [x, y, f1(y)]
    obj = obj.vertex_func(leafshape)

    f1 = lambda x: 1 - math.gamma((x + 1) * fallfactor)
    leafshape = lambda x, y, z, i: [x, y, z + f1(x)]
    obj = obj.vertex_func(leafshape)

    obj = obj.scale([length, length, length]).twosided()
    obj = obj.clean()

    #if 'uv' in obj.extra: del(obj.extra['uv'])
    obj = ddd.uv.map_cubic(obj)
    obj.extra['ddd:collider'] = False

    return obj

def tree_palm(height=14, r=0.30):
    """
    Arecaceae. Currently 181 genera with around 2,600 species are known.

    Different species of palm trees attain different heights. The Queen Palm, for instance,
    can reach 20 m in height, while the Majesty Palm grows to a maximum height of 12m and
    the Black Trunk Palm can reach a towering height of 28 m.

    The palms can reach a height of over 25 m, with trunks between 9 cm and 16 cm in diameter.
    The palms generally grow with 4–9 stems per clump, but up to 25 stems is possible.
    """

    def trunk_callback(height):
        section = ddd.regularpolygon(sides=5, r=r).extrude_step(ddd.regularpolygon(sides=5, r=r*0.8), height * 0.15)
        section = section.extrude_step(ddd.regularpolygon(sides=5, r=r*0.8).translate([random.uniform(-0.4, 0.4), random.uniform(-0.4, 0.4)]), height * 0.35)
        section = section.extrude_step(ddd.regularpolygon(sides=5, r=r*0.7).translate([random.uniform(-0.3, 0.3), random.uniform(-0.3, 0.3)]), height * 0.5)
        section = ddd.uv.map_cylindrical(section)
        section = section.material(ddd.mats.bark)
        return section

    def leaves_callback(sheight):
        golden = (1 + 5 ** 0.5) / 2
        leaf = ddd.group3(name="Leaf group")

        tt = palm_leaf(length=0.5 + height / 5, fallfactor=1.45).material(ddd.mats.treetop)
        tt = ddd.align.matrix_polar(tt, 5)
        leaf.append(tt)
        tt = palm_leaf(length=1.1 + height / 5, fallfactor=1.2).rotate([0, -math.pi * 0.1, math.pi * 2 * (golden)]).material(ddd.mats.treetop)
        tt = ddd.align.matrix_polar(tt, 3)
        leaf.append(tt)
        tt = palm_leaf(length=0.5 + height / 6, fallfactor=1).rotate([0, -math.pi * 0.3, math.pi * 2 * (golden * 2)]).material(ddd.mats.treetop)
        tt = ddd.align.matrix_polar(tt, 2)
        leaf.append(tt)

        return leaf

    obj = recursivetree(height=height, r=r, fork_iters=1, fork_angle=10.0, fork_height_ratio=1.0,
                        trunk_callback=trunk_callback, leaves_callback=leaves_callback)
    obj.name = "Tree Palm"

    objtrunk = obj.select(func=lambda o: o.mat == ddd.mats.bark).combine()
    objleaves = obj.select(func=lambda o: o.mat == ddd.mats.treetop).combine()
    #objleaves.mesh.merge_vertices()
    obj = ddd.group3([objtrunk, objleaves], name="Tree Palm")

    #obj.show()
    return obj


def tree_fir(height=20, r=0.2):
    """
    (Abeto) They are large trees, reaching heights of 10–80 m (33–262 ft) tall with trunk diameters
    of 0.5–4 m (1 ft 8 in–13 ft 1 in) when mature.
    """
    top_r = (height / 4) * random.uniform(0.9, 1.1)
    top_base_h = height / 10

    section = ddd.regularpolygon(sides=5, r=r).extrude_step(ddd.regularpolygon(sides=5, r=r*0.1), height)
    section = ddd.uv.map_cylindrical(section)
    section = section.material(ddd.mats.bark)

    #pol = ddd.regularpolygon(sides=9, r=1)
    #layer = pol.extrude_step(pol.scale(0.5), -0.4, base=False, cap=False)
    #layer = layer.extrude_step(ddd.point(), -0.2, cap=False)
    #layer = layer.material(ddd.mats.treetop).twosided().translate([0, 0, 0.6])
    layer = ddd.sphere(subdivisions=1).scale([1, 1, 0.5])
    #layer = ddd.uv.map_spherical(layer)
    layer = layer.vertex_func(lambda x, y, z, i: [x, y, z + ((x*x + y*y) * 0.7)])
    layer = layer.material(ddd.mats.treetop)

    numlayers = 8
    leaves = ddd.group3(name="Fir leaves group")
    for i in range(numlayers):
        lh = top_base_h + ((height - top_base_h) / (numlayers - 1)) * i
        lobj = layer.copy(name="Fir leaves %d" % i)
        lscale = top_r * (1 / numlayers) * (numlayers - i)
        lobj = layer.scale([lscale, lscale, lscale]).translate([0, 0, lh])
        lobj = ddd.uv.map_cubic(lobj)
        leaves.append(lobj)


    obj = ddd.group3([section.combine(), leaves.combine()], name="Fir")
    #obj.show()
    return obj


def tree_bush(height=1.0, r=0.30):

    #height = height * (1 + fork_height_ratio)

    def trunk_callback(height):
        return ddd.group3()
        #section = ddd.regularpolygon(sides=5, r=r).extrude(height)
        #section = ddd.uv.map_cylindrical(section)
        #section = section.material(ddd.mats.bark)
        #return section
    def leaves_callback(height):
        tt = treetop(r=0.5 + 0.4 * height, subdivisions=0).material(ddd.mats.treetop)
        return tt

    obj = recursivetree(height=height, r=r, leaves_callback=leaves_callback, trunk_callback=trunk_callback,
                        fork_iters=2, fork_height_ratio=0.2)

    '''
    result = ddd.group3()
    for o in obj.recurse_objects():
        result = result.union(o)
    obj = result
    obj = ddd.meshops.reduce_quadric_decimation(obj, target_ratio=0.5)
    '''
    obj = ddd.meshops.reduce(obj)


    obj.name = "Tree Busgh"

    #objtrunk = obj.select(func=lambda o: o.mat == ddd.mats.bark).combine()
    objleaves = obj.select(func=lambda o: o.mat == ddd.mats.treetop).combine()
    obj = ddd.group3([objleaves], name="Tree Default")

    return obj

def tree_weeping_willow():
    pass


def reed(height=None, leaves=None):

    if leaves is None:
        leaves = random.randint(4, 7)
    if height is None:
        height = random.uniform(1.3, 1.9)

    reed = ddd.group3(name="Reed")
    for i in range(leaves):
        lh = height + random.uniform(-0.4, 0.4)
        lb = 0.02 * lh
        item = ddd.polygon([[-lb, 0.0], [lb, 0.0], [0, lh]], name="Reed leaf").triangulate().twosided().material(ddd.mats.treetop)
        item = item.rotate(ddd.ROT_FLOOR_TO_FRONT)
        item = ddd.group([item, item.rotate(ddd.ROT_TOP_CW)], name="Reed leaf")
        item = ddd.uv.map_cubic(item, scale=(0.2, 2.0))
        item = item.rotate([0, 0, random.uniform(0, math.pi)])
        item = item.rotate([random.uniform(0.1, 0.3), 0, 0])
        torsion_advance = math.pi / 4
        item = item.rotate([0, 0, torsion_advance])
        rt = 0.15
        item = item.translate([random.uniform(-rt, rt), random.uniform(-rt, rt), 0])
        reed.append(item)

    reed = ddd.align.polar(reed, 0.1, rotate=True)

    reed = reed.combine()
    return reed

def bush(height=0.8):
    pass

def log(length=0.6):
    pass

def stump(height=0.3, r=0.3):
    """
    (Tocon)
    """
    pass


def grass_blade():
    """
    Creates a grass blade quad (meant to be used through instancing).
    """
    blade = ddd.rect()
    blade = blade.material(ddd.mats.grass_blade)
    blade = blade.triangulate()
    blade = ddd.uv.map_cubic(blade)

    blade = blade.translate([-0.5, 0, 0])
    #blade = blade.scale([0.85, 0.85, 0.85])
    blade = blade.rotate(ddd.ROT_FLOOR_TO_FRONT)

    return blade

def flowers_blade(material):
    """
    Creates a grass blade quad (meant to be used through instancing).
    """
    blade = ddd.rect()
    blade = blade.material(material)
    blade = blade.triangulate()
    blade = ddd.uv.map_cubic(blade)

    blade = blade.translate([-0.5, 0, 0])
    blade = blade.scale([0.85, 1.0, 1.0])
    blade = blade.rotate(ddd.ROT_FLOOR_TO_FRONT)

    return blade


