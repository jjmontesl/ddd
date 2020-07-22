# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020


from ddd.osm import osm
from ddd.pipeline.decorators import dddtask
from ddd.ddd import ddd
from ddd.util.dddrandom import weighted_choice


@dddtask(order="55.50", condition=True)
def osm_augment_plants_condition(pipeline):
    return bool(pipeline.data.get('ddd:osm:augment:plants', False))


# TODO: implement [!contains(["natural"="tree"])]
@dddtask(order="55.50.+", path="/Areas/*", select='["ddd:area:type" = "park"]')  # [!contains(["natural"="tree"])]
def osm_augment_trees_annotate(obj, root):

    # Select areas only if they do not already contain plants
    trees = root.find("/ItemsNodes").filter(lambda o: o.extra.get('osm:natural') == 'tree')
    has_trees = obj.intersects(trees)
    add_trees = not has_trees # and area.geom.area > 100

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

    if area.geom:

        tree_area = area  # area.intersection(ddd.shape(osm.area_crop)).union()
        if tree_area.geom:
            # Decimation would affect after
            num_trees = int((tree_area.geom.area * tree_density_m2))
            #if num_trees == 0 and random.uniform(0, 1) < 0.5: num_trees = 1  # alone trees
            if max_trees:
                num_trees = min(num_trees, max_trees)

            for p in tree_area.random_points(num_points=num_trees):
                tree_type = weighted_choice(tree_types)
                tree = ddd.point(p, name="Tree")
                tree.extra['ddd:aug:status'] = 'added'
                tree.extra['osm:natural'] = 'tree'
                tree.extra['osm:tree:type'] = tree_type
                trees.append(tree)

    return trees
