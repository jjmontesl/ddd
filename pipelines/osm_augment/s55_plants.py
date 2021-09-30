# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020


from ddd.osm import osm
from ddd.pipeline.decorators import dddtask
from ddd.ddd import ddd
from ddd.util.dddrandom import weighted_choice
import random
import noise
from ddd.util.common import parse_bool
from ddd.core.exception import DDDException
import math


# Generate grass
@dddtask(order="55.49", path="/Areas/*", select='["ddd:material" ~ "Park|Grass|Garden|Forest"]["osm:golf" != "green"]')
def osm_augment_plants_generate_grass_blades(obj, osm, root):
    """
    Generates grass blades.
    """
    blade_density_m2 = 1.0 / 20.0
    num_blades = int((obj.area() * blade_density_m2))

    def filter_func_noise(coords):
        val = noise.pnoise2(coords[0], coords[1], octaves=2, persistence=0.5, lacunarity=2, repeatx=1024, repeaty=1024, base=0)
        return (val > random.uniform(-0.5, 0.5))

    blades = ddd.group2(name='Grass Blades: %s' % obj.name)
    for p in obj.random_points(num_points=num_blades, filter_func=filter_func_noise):
        blade = ddd.point(p, name="Grass Blade")
        #blade.extra['ddd:aug:status'] = 'added'
        blade.extra['ddd:item'] = 'grass_blade'  # TODO: Change to DDD
        blades.append(blade)

    root.find("/ItemsNodes").append(blades.children)


@dddtask(path="/Areas/*", select='["osm:leisure" ~ "garden"]')
def osm_augment_plants_generate_flowers(obj, osm, root):
    blade_density_m2 = 1.0 / 20.0
    num_blades = int((obj.area() * blade_density_m2))

    def filter_func_noise(coords):
        val = noise.pnoise2(coords[0], coords[1], octaves=2, persistence=0.5, lacunarity=2, repeatx=1024, repeaty=1024, base=0)
        return (val > random.uniform(-0.5, 0.5))

    blades = ddd.group2(name='Flowers: %s' % obj.name)
    for p in obj.random_points(num_points=num_blades, filter_func=filter_func_noise):
        blade = ddd.point(p, name="Flowers")
        #blade.extra['ddd:aug:status'] = 'added'
        blade.extra['ddd:item'] = 'flowers'
        blade.extra['ddd:flowers:type'] = random.choice(('blue', 'roses'))
        blades.append(blade)

    root.find("/ItemsNodes").append(blades.children)



@dddtask(order="55.50", condition=True)
def osm_augment_plants_condition(pipeline):
    """
    Run plant augmentation only if so configured (ddd:osm:augment:plants=True).
    """
    return parse_bool(pipeline.data.get('ddd:osm:augment:plants', False))


# TODO: implement [!contains(["natural"="tree"])]
@dddtask(order="55.50.+", path="/Areas/*", select='["ddd:area:type" = "park"]')  # [!contains(["natural"="tree"])]
def osm_augment_trees_annotate(obj, root):

    # Select areas only if they do not already contain plants
    trees = root.find("/Features").filter(lambda o: o.extra.get('osm:natural') in ('tree', 'tree_row'))  # search trees in original features, before crop
    has_trees = obj.get('ddd:area:original', obj).intersects(trees.buffer(0.1))   # Points need to be buffered for intersection with areas
    add_trees = not has_trees # and area.geom.area > 100

    #print(add_trees)
    #ddd.group2([trees.buffer(0.1), obj.material(ddd.MAT_HIGHLIGHT), obj.get('ddd:area:original', obj)]).show()

    if add_trees:
        obj.extra["ddd:aug:itemfill"] = True
        obj.prop_set("ddd:aug:itemfill:density", default=0.0025)
        # TODO: Change tree type propabilities according to geographic zone
        # ...Different probabilities for planted trees (urban / beach) than from forest (natural flora)


@dddtask(order="55.50.+", path="/Areas/*", select='["ddd:aug:itemfill" = True]')
def osm_augment_trees_generate(logger, pipeline, root, obj):
    tree_density_m2 = obj.extra.get("ddd:aug:itemfill:density", 0.0025)
    tree_types = {'default': 1, 'palm': 0.001}
    tree_types = obj.extra.get("ddd:aug:itemfill:types", tree_types)

    trees = generate_area_2d_park(obj, tree_density_m2, tree_types)
    root.find("/ItemsNodes").children.extend(trees.children)


def generate_area_2d_park(area, tree_density_m2=0.0025, tree_types=None):

    max_trees = None

    if tree_types is None:
        tree_types = {'default': 1}  #, 'palm': 0.001}

    #area = ddd.shape(feature["geometry"], name="Park: %s" % feature['properties'].get('name', None))
    feature = area.extra['osm:feature']
    area = area.material(ddd.mats.park)
    area.name = "Park: %s" % feature['properties'].get('name', None)
    area.extra['ddd:area:type'] = 'park'

    # Add trees if necesary
    # FIXME: should not check for None in intersects, filter shall not return None (empty group)

    trees = ddd.group2(name="Trees (Aug): %s" % area.name)

    align = area.get('ddd:aug:itemfill:align', 'noise')

    if area.geom:

        tree_area = area  # area.intersection(ddd.shape(osm.area_crop)).union()
        if tree_area.geom:

            if align == 'noise':

                # Decimation would affect after
                num_trees = int((tree_area.geom.area * tree_density_m2))
                #if num_trees == 0 and random.uniform(0, 1) < 0.5: num_trees = 1  # alone trees
                if max_trees:
                    num_trees = min(num_trees, max_trees)

                def filter_func_noise(coords):
                    val = noise.pnoise2(coords[0] * 0.1, coords[1] * 0.1, octaves=2, persistence=0.5, lacunarity=2, repeatx=1024, repeaty=1024, base=0)
                    return (val > random.uniform(-0.5, 0.5))

                for p in tree_area.random_points(num_points=num_trees):
                    tree_type = weighted_choice(tree_types)
                    tree = ddd.point(p, name="Tree")
                    tree.extra['ddd:aug:status'] = 'added'
                    tree.extra['osm:natural'] = 'tree'  # TODO: Change to DDD
                    tree.extra['osm:tree:type'] = tree_type  # TODO: Change to DDD
                    trees.append(tree)

            elif align == 'grid':

                # Decimation would affect after
                (major_seg, minor_seg, angle) = ddd.geomops.oriented_axis(tree_area)

                num_trees = int((tree_area.geom.minimum_rotated_rectangle.area * tree_density_m2))
                major_minor_ratio = major_seg.geom.length / minor_seg.geom.length
                trees_major = int(max(1, math.sqrt(num_trees) * major_minor_ratio))
                trees_minor = int(max(1, math.sqrt(num_trees) * (1 / major_minor_ratio)))

                minor_seg_centered = minor_seg.recenter()
                for i in range(trees_major):
                    p_major = major_seg.geom.interpolate(i * major_seg.geom.length / trees_major)
                    for j in range(trees_minor):
                        p_minor_offset = minor_seg_centered.geom.interpolate(j * minor_seg_centered.geom.length / trees_minor)
                        p = (p_major.coords[0][0] + p_minor_offset.coords[0][0], p_major.coords[0][1] + p_minor_offset.coords[0][1])

                        if not tree_area.contains(ddd.point(p)):
                            continue

                        tree_type = weighted_choice(tree_types)
                        tree = ddd.point(p, name="Tree")
                        tree.extra['ddd:aug:status'] = 'added'
                        tree.extra['osm:natural'] = 'tree'  # TODO: Change to DDD
                        tree.extra['osm:tree:type'] = tree_type  # TODO: Change to DDD
                        trees.append(tree)

            else:
                raise DDDException("Invalid item align type: %s", align)



    return trees
