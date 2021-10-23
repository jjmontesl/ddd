# ddd - DDD123
# Library for simple scene modelling.
# Jose Juan Montes and Contributors 2019-2021

import logging
import math

from ddd.geo.georaster import GeoRasterLayer
from ddd.core import settings
from ddd.core.exception import DDDException
from ddd.util.common import parse_bool


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class ElevationModel:

    _instance = None

    def __init__(self):

        self.dem = GeoRasterLayer(settings.DDD_GEO_DEM_TILES)
        self.egm = None

        self.dummy = parse_bool(settings.DDD_SETTINGS_GET("DDD_GEO_ELEVATION_DUMMY", False))

    @staticmethod
    def instance():
        if ElevationModel._instance is None:
            ElevationModel._instance = ElevationModel()
        return ElevationModel._instance

    def value(self, point):
        return self.elevation(point)

    def elevation(self, point):
        if self.dummy: return 1
        value = self.dem.value(point)

        if not math.isfinite(value):
            logger.warn("Non finite elevation value found at %s: %s", point, value)
            value = 0  # - 0.01

        if value < -1000.0 or value > 10000.0:
            #raise DDDException("Suspicious value for elevation: %s. Aborting." % value)
            # (Sea values in EUDEM11 are found to be -3.573423841207179e+38)
            value = 0

        if value is None:
            value = 0

        return value

    '''
    def elevation_info(self, longitude, latitude, altitude):
        """
        Calculates elevation related information (ground altitude, terrain altitude...).
        """
        terrain_alt_msl = self.elevation([longitude, latitude])
        alt_egm = self.egm([longitude, latitude])

        if alt_type == ElevationInfo.ALTITUDE_WGS84:
            alt_wgs84 = altitude
            alt_msl = alt_wgs84 - alt_egm
        elif alt_type == ElevationInfo.ALTITUDE_MSL:
            alt_msl = altitude
            alt_wgs84 = alt_msl + alt_egm
        elif alt_type == ElevationInfo.ALTITUDE_GROUND:
            alt_msl = terrain_alt_msl + altitude
            alt_wgs84 = alt_msl + alt_egm
        else:
            raise NotImplementedError("Elevation type not supported: %s" % (alt_type))

        alt_grnd = alt_msl - terrain_alt_msl

        valid_alt = self._egm is not None
        # valid_terrain =

        return (longitude, latitude, altitude, alt_wgs84, alt_msl, alt_grnd, terrain_alt_msl, alt_egm, alt_type, valid_alt, None)
    '''
