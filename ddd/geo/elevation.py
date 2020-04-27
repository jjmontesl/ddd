# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging
import math
import numpy
from osgeo import gdal
from osgeo.gdalconst import GA_ReadOnly
from scipy.interpolate.interpolate import interp2d
from shapely.geometry.linestring import LineString

from geographiclib.geodesic import Geodesic
import numpy as np


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class ElevationChunk(object):

    _chunk = None

    def __init__(self):

        self.geotransform = None
        self.layer = None

    def value(self, point, interpolate=True):
        if interpolate:
            return self.value_interpolated(point)
        else:
            return self.value_simple(point)

    def value_simple(self, point):

        if not self.geotransform:
            # Data is not available
            raise AssertionError

        x, y = (point[0], point[1])

        # Transform to raster point coordinates
        raster_x = int((x - self.geotransform[0]) / self.geotransform[1])
        raster_y = int((y - self.geotransform[3]) / self.geotransform[5])

        height_matrix = self.layer.GetRasterBand(1).ReadAsArray(raster_x, raster_y, 1, 1)

        return float(height_matrix[0][0])

    def value_interpolated(self, point):
        """
        """
        # FIXME: Current implementation fails across borders (height matrix). Fallback to point.

        if not self.geotransform:
            # Data is not available
            raise AssertionError("No elevation data available for the given point.")

        x, y = (point[0], point[1])

        # Transform to raster point coordinates
        pixel_is_area = True  # in Vigo, True seems more accurate
        if pixel_is_area:
            raster_x = int(round((x - self.geotransform[0]) / self.geotransform[1]))
            raster_y = int(round((y - self.geotransform[3]) / self.geotransform[5]))
            coords_x = ((raster_x * self.geotransform[1])) + self.geotransform[0]
            coords_y = ((raster_y * self.geotransform[5])) + self.geotransform[3]
            # Pixel offset, centerted on 0, from the point to the pixel center
            offset_x = - (coords_x - x) / self.geotransform[1]
            offset_y = - (coords_y - y) / self.geotransform[5]
        else:
            raster_x = int(round((x - self.geotransform[0]) / self.geotransform[1]))
            raster_y = int(round((y - self.geotransform[3]) / self.geotransform[5]))
            coords_x = (((0.5 + raster_x) * self.geotransform[1])) + self.geotransform[0]
            coords_y = (((0.5 + raster_y) * self.geotransform[5])) + self.geotransform[3]
            # Pixel offset, centerted on 0, from the point to the pixel center
            offset_x = - (coords_x - x) / self.geotransform[1]
            offset_y = - (coords_y - y) / self.geotransform[5]

        try:
            height_matrix = self.layer.GetRasterBand(1).ReadAsArray(raster_x - 1, raster_y - 1, 3, 3)
        except Exception as e:
            # Safeguard
            #logger.exception("Exception obtaining 3x3 height matrix around point %s", point)
            return self.value_simple(point)

        interpolated = interp2d([-1, 0, 1], [-1, 0, 1], height_matrix, 'linear')  # , copy=False
        value = interpolated(offset_x, offset_y)

        #logger.debug("Elevation: point=%.1f,%.1f, offset=%.8f,%.8f, value=%.1f", x, y, offset_x, offset_y, value)

        return float(value)

    @staticmethod
    def load(geotiff_file):

        if ElevationChunk._chunk:
            return ElevationChunk._chunk

        logger.info("Loading GeoTIFF with elevation data: %s" % geotiff_file)

        chunk = ElevationChunk()

        try:
            chunk.layer = gdal.Open(geotiff_file, GA_ReadOnly)

            bands = chunk.layer.RasterCount
            if (bands != 1):
                raise AssertionError("DEM GeoTIFF file must have 1 band only.")

            chunk.geotransform = chunk.layer.GetGeoTransform()

            logger.debug("Opened GeoTIFF with %d bands [geotransform=%s]" % (bands, chunk.geotransform))

        except Exception as e:
            logger.error("Could not read elevation data file: %s" % geotiff_file)

        ElevationChunk._chunk = chunk
        return chunk


class ElevationModel(object):

    def _chunk_config(self, point):
        """
        Return the chunk configuration entry for the DEM file that contains
        the given point, using ELEVATION_DEM_GEOTIFF_FILES setting.
        """
        if self._lastchunk and (point[0] >= self._lastchunk['bounds'][0] and point[0] < self._lastchunk['bounds'][2] and
           point[1] >= self._lastchunk['bounds'][1] and point[1] < self._lastchunk['bounds'][3]):
            return self._lastchunk

        for cc in settings.ELEVATION_DEM_GEOTIFF_FILES:
            if ( point[0] >= cc['bounds'][0] and point[0] < cc['bounds'][2] and
                 point[1] >= cc['bounds'][1] and point[1] < cc['bounds'][3] ):
                self._lastchunk = cc
                return cc

        return None


    def area(self, bounds):
        # FIXME: This won't  work if area crosses chunks.
        # TODO: This method should do stitching if necessary.

        minx, miny, maxx, maxy = bounds

        chunk = self.chunk([minx, miny])

        if not chunk or not chunk.geotransform:
            # Data is not available
            raise AssertionError("No elevation data available for the given point.")

        # Transform to raster point coordinates
        raster_min_x = int((minx - chunk.geotransform[0]) / chunk.geotransform[1])
        raster_min_y = int((miny - chunk.geotransform[3]) / chunk.geotransform[5])
        raster_max_x = int((maxx - chunk.geotransform[0]) / chunk.geotransform[1])
        raster_max_y = int((maxy - chunk.geotransform[3]) / chunk.geotransform[5])

        # Check if limits are hit
        if (raster_max_x > chunk.layer.RasterXSize - 1) or raster_max_y < 0:
            logger.error("Raster area [%d, %d, %d, %d] requested exceeds tile bounds [%d, %d] (not implemented).",
                         raster_min_x, raster_min_y, raster_max_x, raster_max_y, chunk.layer.RasterXSize, chunk.layer.RasterYSize)
            raise NotImplementedError()
        if raster_max_x > chunk.layer.RasterXSize - 1:
            raster_max_x = chunk.layer.RasterXSize - 1
        if raster_max_y < 0:
            raster_max_y = 0

        # Note that readasarray is positive south, whereas bounds are positive up
        height_matrix = chunk.layer.GetRasterBand(1).ReadAsArray(raster_min_x,
                                                                 raster_max_y,
                                                                 raster_max_x - raster_min_x + 1,
                                                                 raster_min_y - raster_max_y + 1)

        return height_matrix

    def profile(self, pointA, pointB, steps):
        # Consider: skimage.draw.line(r0, c0, r1, c1) (also antialiased version available)
        # https://scikit-image.org/docs/dev/api/skimage.draw.html#skimage.draw.line
        line = LineString([pointA, pointB])
        return self.profile_line(line, steps)

    def profile_line(self, line_shape, steps):

        length = line_shape.length

        result_line = []

        for d in np.linspace(0, length, steps):
            point = line_shape.interpolate(d)
            (point_x, point_y) = (point.x, point.y)
            height = self.elevation((point_x, point_y))
            result_line.append((point_x, point_y, height))

        #print "Length: %s" % length

        return result_line

    def elevation(self, point):

        # FIXME: Note that the chunk may exist (is defined) but the geotransform may be not available
        # (file is not available). This is currently not correctly handled by this module, and zeros
        # are returned without appropriate tracking of the fact that data was not available.

        chunk = self.chunk(point)

        if not chunk:
            return 0.0

        try:
            value = chunk.value(point)
        except Exception as e:
            value = 0.0
            if self._log_throttler.throttle():
                logger.exception("Error obtaining elevation for point (%s) (silenced for %.1fs): %s", point, self._log_throttler.seconds, e)

        return value

    def elevation_info(self, longitude, latitude, altitude, alt_type):
        """
        Calculates elevation related information (ground altitude, terrain altitude...).
        """

        # TODO: This method should return information about whether elevation information is valid

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

        data = ElevationInfo(longitude, latitude, altitude, alt_wgs84, alt_msl, alt_grnd, terrain_alt_msl, alt_egm, alt_type, valid_alt, None)

        return data

    def circle_func(self, point, radius, func=numpy.sum):
        # Calculate square coordinartes to retrieve raster area
        dst = Geodesic.WGS84.Direct(point[1], point[0], 0, radius)
        dst_north = (dst['lon2'], dst['lat2'])
        dst = Geodesic.WGS84.Direct(point[1], point[0], 90, radius)
        dst_east = (dst['lon2'], dst['lat2'])

        point1 = ((point[0] - (dst_east[0] - point[0])), (point[1] - (dst_north[1] - point[1])))
        point2 = ((point[0] + (dst_east[0] - point[0])), (point[1] + (dst_north[1] - point[1])))

        data = self.area([point1[0], point1[1], point2[0], point2[1]])

        # TODO: Review this ellipse is correctly aligned (rows/cols vs lat/lon: draw this)
        size = data.shape
        rr, cc = ellipse(size[0] / 2, size[1] / 2, size[0] / 2, size[1] / 2)
        values = data[rr, cc]
        value = float(func(values))

        return value

