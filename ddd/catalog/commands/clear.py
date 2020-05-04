# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020


from ddd.ddd import ddd
import os
import logging
from ddd.catalog.catalog import PrefabCatalog

# Get instance of logger for this module
logger = logging.getLogger(__name__)


catalog = PrefabCatalog()

for file in os.listdir(catalog.path):
    if file.endswith(".ddd"):
        logger.info("Deleting: %s", file)
        os.unlink(os.path.join(catalog.path, file))

