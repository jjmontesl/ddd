# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020


from ddd.ddd import ddd
from ddd.catalog.catalog import PrefabCatalog

catalog = PrefabCatalog()
catalog.loadall()

# Save
catalog.export()
catalog.export("/tmp/catalog.json")

# Show items
#items = ddd.group3([catalog.instance(c) for c in catalog._cache.values()])
#items = ddd.align.grid(items, space=10.0)
#items.append(ddd.helper.all())
#items.show()
catalog.show()