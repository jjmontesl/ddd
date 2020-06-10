# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020


from ddd.pipeline.decorators import dddtask


@dddtask(order="20.90.+")
def osm_features_export_2d(root):

    root = root.copy()
    root.find("/Features").prop_set('svg:stroke-width', 1.0, children=True)
    root.find("/Features").save("/tmp/osm-features.svg")

