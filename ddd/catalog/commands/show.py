# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020


import argparse
import logging
from ddd.core.cli import D1D2D3Bootstrap
from ddd.ddd import ddd
from ddd.catalog.catalog import PrefabCatalog
from ddd.core.command import DDDCommand


#from osm import OSMDDDBootstrap
# Get instance of logger for this module
logger = logging.getLogger(__name__)

class CatalogShowCommand(DDDCommand):

    def parse_args(self, args):

        parser = argparse.ArgumentParser()  # description='', usage = ''
        args = parser.parse_args(args)

    def run(self):

        D1D2D3Bootstrap.export_mesh = True

        catalog = PrefabCatalog()
        catalog.loadall()

        # Show items
        #items = ddd.group3([catalog.instance(c) for c in catalog._cache.values()])
        #items = ddd.align.grid(items, space=10.0)
        #items.append(ddd.helper.all())
        #items.show()
        catalog.show()
