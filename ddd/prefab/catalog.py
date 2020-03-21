# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging
from ddd.ddd import ddd


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class PrefabCatalog():
    """
    Pre-made object catalog, to ease creation o shared instances.

    Features:

    - Expandible: catalog doesn't need to be initialized, it is filled on-demand. Works as a cache.
    - Preseedeable + Readonly option: for cases where the catalog needs to be shared among processes.
    - Loadable: reimport/load catalog to continue generation of related scenes.
    - Export: export in a GLB format that Unity importer understands.
    - Reproducible: NOT IMPLEMENTED (requires random seeding / reproducible packs)
    - Dummy Catalog: allows for generation without instancing/sharing.
    - Inheritance: a catalog can extend or be based on another one.
    """

    def __init__(self):
        self._cache = {}

    def show(self):
        ddd.distribute.grid(ddd.group(self._cache.values())).show()

    def add(self, key, obj):
        """
        This method returns an instance of the added object, like 'instance' does,
        so the result can be directly used as if it was retrieved from the catalog.
        """
        if key in self._cache:
            raise ValueError("Object already exists in catalog: %s", key)
        obj.extra['ddd:catalog:key'] = key
        self._cache[key] = obj
        obj = ddd.instance(obj)
        return obj

    def instance(self, key):
        obj = self._cache.get(key, None)
        if obj:
            obj = ddd.instance(obj)
        return obj

