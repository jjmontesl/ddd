# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging


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

    def put(self, key, obj):
        return None

    def get(self, key):
        return None

