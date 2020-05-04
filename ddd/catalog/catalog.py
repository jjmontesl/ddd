# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging
from ddd.ddd import ddd
import pickle
import os


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
    - (??) Inheritance: a catalog can extend or be based on another one
    """

    def __init__(self):
        self._cache = {}
        self.path = "./_catalog"
        self.autosave = True
        self.autoload = True

    def add(self, key, obj):
        """
        This method returns an instance of the added object, like 'instance' does,
        so the result can be directly used as if it was retrieved from the catalog.
        """
        key = key.replace("_", "-").replace(":", "-").replace(".", "-")
        if key in self._cache and self._cache[key]:
            raise ValueError("Object already exists in catalog: %s", key)
        obj.extra['ddd:catalog:key'] = key
        self._cache[key] = obj

        if self.autosave:
            self.save(key)

        obj = self.instance(key)
        return obj

    def instance(self, key):
        key = key.replace("_", "-").replace(":", "-").replace(".", "-")
        obj = self._cache.get(key, None)

        if obj is None and self.autoload:
            obj = self.load(key)

        if obj:
            obj = ddd.instance(obj)
            obj.extra['ddd:instance:key'] = key

        return obj

    def all(self):
        items = [self.instance(k) for k in self._cache.keys() if self._cache[k]]
        return ddd.group3(items, name="Catalog Group")

    def show(self):
        ddd.align.grid(self.all()).show()

    def save(self, key):
        key = key.replace("_", "-").replace(":", "-").replace(".", "-")
        obj = self._cache[key]
        filename = self.path + "/" + key + ".ddd"
        logger.info("Saving catalog object %s to: %s", key, filename)
        data = pickle.dumps(obj)
        with open(filename, "wb") as f:
            f.write(data)

    def load(self, key):
        """
        Returns an instance or None.
        """
        key = key.replace("_", "-").replace(":", "-").replace(".", "-")
        obj = None
        filename = self.path + "/" + key + ".ddd"

        if os.path.exists(filename):
            logger.info("Loading catalog object %s from: %s", key, filename)
            with open(filename, "rb") as f:
                data = pickle.load(f)
                self._cache[key] = data
                obj = self.instance(key)
        else:
            self._cache[key] = None

        return obj

    def loadall(self):
        for p in os.listdir(self.path):
            if p.endswith(".ddd"):
                key = p[:-4]
                self.load(key)

    def export(self, path="catalog.glb"):
        scene = self.all()
        scene.save(path, instance_mesh=True, instance_marker=True)
        scene.save(path + ".json", instance_mesh=True, instance_marker=True)

