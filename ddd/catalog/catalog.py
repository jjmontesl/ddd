# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging
from ddd.ddd import ddd
import pickle
import os
from ddd.core.cli import D1D2D3Bootstrap
from ddd.core import settings


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
        self.path = settings.DDD_WORKDIR + "/_catalog"
        self.autosave = True
        self.autoload = True

        self.catalog_overwrite = D1D2D3Bootstrap.catalog_overwrite
        self.catalog_ignore = D1D2D3Bootstrap.catalog_ignore

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

        if self.autosave and not self.catalog_ignore:
            self.save(key)

        obj = self.instance(key)

        if self.catalog_ignore:
            del(self._cache[key])

        return obj

    def instance(self, key, name=None):
        key = key.replace("_", "-").replace(":", "-").replace(".", "-")
        obj = self._cache.get(key, None)

        if obj is None and self.autoload:
            obj = self.load(key)

        if obj:
            if not name:
                name = obj.name # + " Instance"
            obj = ddd.instance(obj)
            obj.extra['ddd:instance:key'] = key
            obj.name = name

        return obj

    def all(self, name="Root"):  # "Catalog"
        """
        Returns a group with all the items in the catalog, all at origin.

        Note: name of the root must be "Root" for DDD Importer to work (TODO: fix that and use a better root name)
        """
        items = [self.instance(k) for k in self._cache.keys() if self._cache[k]]
        
        return ddd.group3(items, name=name)

    def show(self):
        ddd.align.grid(self.all()).show3(instance_mesh=True)

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

        # If catalog_overwrite, return None on load to force creation of items
        if self.catalog_overwrite: return None

        key = key.replace("_", "-").replace(":", "-").replace(".", "-")
        obj = None
        filename = os.path.normpath(os.path.join(self.path, key + ".ddd"))

        def _clean_loaded(obj):
            obj._trimesh_material_cached = None

        if os.path.exists(filename):
            logger.info("Loading catalog object '%s' from: %s", key, filename)
            with open(filename, "rb") as f:
                data = pickle.load(f)
                data.extra['ddd:catalog:key'] = key  # Replace, in case file was renamed in the filesystem
                data.select(apply_func=_clean_loaded)
                self._cache[key] = data
                obj = self.instance(key)
        else:
            self._cache[key] = None

        return obj

    def loadall(self):
        if self.catalog_overwrite: return
        logger.info("Loading catalog from: %s", self.path)
        for p in os.listdir(self.path):
            if p.endswith(".ddd"):
                key = p[:-4]
                self.load(key)

    def export(self, path="catalog.glb"):
        scene = self.all()

        # Expand instances, so their children and content are included in the export
        scene = scene.expanded_instances()

        # Currently this is needed to avoid name clashing when importing from side-loaded JSON file (e.g. DDD -> Unity)
        scene.rename_unique()

        path_wo_ext = os.path.splitext(path)[0]

        scene.save(path_wo_ext + ".json", instance_mesh=True, instance_marker=True)
        scene.save(path, instance_mesh=True, instance_marker=True)

