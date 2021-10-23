# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020


import logging

import argparse

from ddd.catalog.catalog import PrefabCatalog
from ddd.core.command import DDDCommand


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class CatalogExportCommand(DDDCommand):

    def parse_args(self, args):

        parser = argparse.ArgumentParser()  # description='', usage = ''
        args = parser.parse_args(args)

    def run(self):

        catalog = PrefabCatalog()
        catalog.loadall()

        # Save
        #catalog.export("/tmp/catalog.glb")
        catalog.export()

        # Show items
        #items = ddd.group3([catalog.instance(c) for c in catalog._cache.values()])
        #items = ddd.align.grid(items, space=10.0)
        #items.append(ddd.helper.all())
        #items.show()
        catalog.show()
