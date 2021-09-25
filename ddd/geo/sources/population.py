# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes and contributors 2020-2021

import logging

from ddd.ddd import ddd
from ddd.core import settings
from ddd.geo.georaster import GeoRasterTile, GeoRasterLayer


# Get instance of logger for this module
logger = logging.getLogger(__name__)

class PopulationModel():
    """
    """

    _instance = None

    def __init__(self):
        self.population_layer_conf = settings.DDD_GEO_POPULATION_GEOTIFF_TILES
        self.source = GeoRasterLayer(self.population_layer_conf)

    @staticmethod
    def instance():
        if PopulationModel._instance is None:
            PopulationModel._instance = PopulationModel()
        return PopulationModel._instance

    def population_km2(self, coords):
        """
        Currently fakes the calculation assuming that underlying cells in source dataset are 1km2.
        """
        return self._population(coords)

    def _population(self, coords):
        """
        Returns the popùlation for the source data area corresponding to the given coords.
        Note that this is the population in that area as per the source database, which can have different
        sizes and shapes. A possibly more accurate data point is to account for the actual cell area as well
        (which this method does not).
        """

        #outProj = pyproj.Proj('EPSG:4326')
        #projs = {'EPSG:4326': outProj}
        #crs = 'PROJCS["unnamed",GEOGCS["WGS 84",DATUM["unknown",SPHEROID["WGS84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]],PROJECTION["Mollweide"],PARAMETER["central_meridian",0],PARAMETER["false_easting",0],PARAMETER["false_northing",0],UNIT["Meter",1]]'
        #crs = 'EPSG:4326'

        value = self.source.value(coords, interpolate=True)

        return value

