# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020


from ddd.pipeline.decorators import dddtask


@dddtask(order="20.90.10", condition=True)
def features_export_2d_condition(pipeline):
    return bool(pipeline.data.get('ddd:godot:output:intermediate', False))

@dddtask(order="20.90.10.+")
def features_export_2d(root):

    root.dump()
    root.save("/tmp/godot-features.json")

    root = root.copy().scale([1, -1])
    root.find("/Features").prop_set('svg:stroke-width', 1.0, children=True)
    root.find("/Features").save("/tmp/godot-features.svg")


