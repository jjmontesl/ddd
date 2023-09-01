# ddd - D1D2D3
# Library for simple scene modelling.


from ddd.catalog.catalog import PrefabCatalog
from ddd.ddd import ddd
from ddd.pack.sketchy import urban
from ddd.pipeline.decorators import dddtask


@dddtask()
def example_catalog(pipeline, root, logger):

    logger.warn("REMEMBER!! This example should usually be run with: --export-meshes")

    catalog = PrefabCatalog()

    catalog.loadall()

    item = catalog.instance('prefab1')  # Preload
    if not item:
        item = urban.lamppost()
        catalog.add('prefab1', item)

    item = catalog.instance('prefab2')  # Preload
    if not item:
        item = urban.trafficlights()
        catalog.add('prefab2', item)

    items = ddd.DDDNode3(name="Items")

    # Rotate elements to test instance rotation works correctly
    for i in range(6):
        item = catalog.instance('prefab1')
        #item = item.rotate([0, 0, i * -ddd.PI_OVER_3])
        item.transform.rotate([0, 0, i * -ddd.PI_OVER_3])
        items.append(item)
    for i in range(6):
        item = catalog.instance('prefab2')
        item = item.rotate([0, 0, i * -ddd.PI_OVER_3])
        #item.transform.rotate([0, 0, i * -ddd.PI_OVER_3])
        items.append(item)

    # All items
    items = ddd.align.grid(items, space=10.0, width=6)
    root.append(items)

    root.append(ddd.helper.all())

    root.save("/tmp/catalog.json")
    root.save("/tmp/catalog.glb")
    root.save("/tmp/catalog.gltf")

    root.dump()
    root.show()


