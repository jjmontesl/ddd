# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020


from ddd.osm import osm
from ddd.pipeline.decorators import dddtask




# TODO: implement [!contains(["natural"="tree"])]
@dddtask(order="50.50.+", path="/Areas/*", select='["ddd:area:type" = "park"]')  # [!contains(["natural"="tree"])]
def osm_augment_trees_annotate(obj):
    obj.extra["ddd:osm:augment:trees"] = True
    obj.extra["ddd:osm:augment:trees:density"] = True

# Change tree type propabilities according to geographic zone
# Different probabilities for planted trees (urban / beach) than from forest (natural flora)


@dddtask(order="50.50.+", path="/Areas/*", select='["ddd:osm:augment:trees" = True]')
def osm_augment_trees_generate(logger, pipeline, root, obj):
    pass



