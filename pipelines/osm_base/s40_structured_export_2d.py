# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020


from ddd.pipeline.decorators import dddtask


@dddtask(order="40.90.+")
def osm_structured_export_2d(root, osm):

    osm.save_tile_2d("/tmp/osm-structured.png")

    root = root.copy()
    root = root.remove(root.find("/Features"))  # !Altering
    root.prop_set('svg:fill-opacity', 0.7, children=True)

    #root.find("/Areas").replace(root.find("/Areas").material(ddd.mats.park).prop_set('svg:fill-opacity', 0.6, True))
    #root.find("/Ways").replace(root.find("/Ways").buffer(1.0).material(ddd.mats.asphalt).prop_set('svg:fill-opacity', 0.8, True))
    #root.find("/Buildings").replace(root.find("/Buildings").material(ddd.mats.stone).prop_set('svg:fill-opacity', 0.7, True))
    #root.find("/Items").replace(root.find("/Items").buffer(1.0).material(ddd.mats.highlight))

    root.save("/tmp/osm-structured.json")
    root.save("/tmp/osm-structured.svg")
