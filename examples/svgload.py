# Jose Juan Montes 2019-2020

from ddd.ddd import ddd
from ddd.core import settings
from ddd.pack.symbols import iconitems


from ddd.pipeline.decorators import dddtask


@dddtask(order="10")
def pipeline_start(pipeline, root):
    """
    Tests subdivision on several geometries (check wireframe).
    """


    items = ddd.group3()

    item = iconitems.iconitem_auto("Menhir pentacefálico", (2.0, 2.0), 0.4, 0.05)
    #item.show()

    item = ddd.load(settings.DDD_DATADIR + "/vector/various/menhir.svg")
    item = ddd.align.anchor(item, ddd.ANCHOR_BOTTOM_CENTER)
    item = ddd.geomops.resize(item)
    item = item.extrude(0.1)
    item = item.rotate(ddd.ROT_FLOOR_TO_FRONT)
    items.append(item)

    item = ddd.load(settings.DDD_DATADIR + "/vector/fontawesome-free-5-solid/ice-cream.svg")
    item = ddd.align.anchor(item, ddd.ANCHOR_BOTTOM_CENTER)
    item = ddd.geomops.resize(item)
    item = item.extrude(0.1)
    item = item.rotate(ddd.ROT_FLOOR_TO_FRONT)
    items.append(item)

    item = ddd.load(settings.DDD_DATADIR + "/vector/fontawesome-free-5-solid/bell.svg")
    item = ddd.align.anchor(item, ddd.ANCHOR_BOTTOM_CENTER)
    item = ddd.geomops.resize(item)
    item = item.extrude(0.1)
    item = item.rotate(ddd.ROT_FLOOR_TO_FRONT)
    items.append(item)

    #print(iconitems.iconitem_catalog_list())
    #icon_path = iconitems.iconitem_catalog_search("Menhir")
    #print(icon_path)

    item = iconitems.iconitem_auto("Combate entre Hércules e Xerión", (2.0, 2.0), 0.4, 0.05)
    items.append(item)

    item = iconitems.iconitem_auto("Bell", (2.0, 2.0), 0.4, 0.05)
    items.append(item)

    item = iconitems.iconitem_auto("Guitarra", (2.0, 2.0), 0.4, 0.05)
    items.append(item)

    item = iconitems.iconitem_auto("Menhir pentacefálico", (2.0, 2.0), 0.4, 0.05)
    items.append(item)

    item = iconitems.iconitem_auto("Monumento a la lira", (2.0, 2.0), 0.4, 0.05)
    items.append(item)

    item = iconitems.iconitem_auto("Image", (2.0, 2.0), 0.4, 0.05)
    items.append(item)

    #item = iconitems.iconitem_auto("Cruz del Juramento", (2.0, 2.0), 0.4, 0.05)
    #items.append(item)

    #item = iconitems.iconitem_auto("Los caballos", (2.0, 2.0), 0.4, 0.05)
    #items.append(item)

    #item = iconitems.iconitem_auto("Fuente de Híspalis, Puerta de Jerez", (2.0, 2.0), 0.4, 0.05)
    #items.append(item)


    items = ddd.align.grid(items)
    items.append(ddd.helper.all())
    items.show()
    #items.save("/tmp/test.glb")

    root.append(items)