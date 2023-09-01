# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020


from ddd.pipeline.decorators import dddtask


@dddtask(order="20.90.10", condition=True)
def features_export_2d_condition(pipeline):
    return bool(pipeline.data.get('ddd:test:output:intermediate', False))

@dddtask(order="20.90.10.+")
def features_export_2d(root):

    root.find("/Features2").show()

    root.dump()
    root.save("/tmp/features.json")

    feats = root.find("/Features2").copy().scale([1, -1])
    feats.set('svg:stroke-width', 1.0, children=True)
    feats.save("/tmp/features.svg")


