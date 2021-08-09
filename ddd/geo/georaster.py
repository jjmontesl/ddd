# ddd - DDD123
# Library for simple scene modelling.
# Jose Juan Montes and Contributors 2019-2021

import logging
import math

from geographiclib.geodesic import Geodesic
import numpy
from osgeo import gdal
from osgeo.gdalconst import GA_ReadOnly
import pyproj
from scipy.interpolate.interpolate import interp2d

from ddd.core import settings
from ddd.core.exception import DDDException
import numpy as np


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class GeoRasterTile:

    _cache = {}

    def __init__(self):
        self.geotransform = None
        self.layer = None
        self.crs = None
        self.crs_transformer = None

    @staticmethod
    def load_cached(self, georaster_file, crs):
        if georaster_file not in GeoRasterTile._cache:
            GeoRasterTile._cache[georaster_file] = GeoRasterTile.load(georaster_file, crs)
        return GeoRasterTile._cache[georaster_file]

    @staticmethod
    def load(georaster_file, crs):

        logger.info("Loading georaster file: %s" % georaster_file)

        tile = GeoRasterTile()
        tile.crs = crs.lower()
        tile.crs_transformer = pyproj.Transformer.from_proj('epsg:4326', tile.crs, always_xy=True)

        try:
            tile.layer = gdal.Open(georaster_file, GA_ReadOnly)
            bands = tile.layer.RasterCount

            tile.geotransform = tile.layer.GetGeoTransform()
            logger.debug("Opened georaster [bands=%d, geotransform=%s]" % (bands, tile.geotransform))

            #if (bands != 1):
            #    raise DDDException("Georaster file must have 1 band only.")

        except Exception as e:
            raise DDDException("Could not read georaster file %s: %s", georaster_file, e)

        return tile

    def value(self, point, interpolate=True):

        georaster_offset_wgs84_xy = [0, 0]  # [-0.00004389999, 0.00004389999]  # Arbitrary offset test
        point = (point[0] + georaster_offset_wgs84_xy[0], point[1] + georaster_offset_wgs84_xy[1])

        if interpolate:
            return self.value_interpolated(point)
        else:
            return self.value_simple(point)

    def value_simple(self, point):

        if not self.geotransform:
            # Data is not available
            raise AssertionError

        x, y = (point[0], point[1])
        if self.crs != 'epsg:4326':
            x, y = self.crs_transformer.transform(x, y)

        # Transform to raster point coordinates
        raster_x = int((x - self.geotransform[0]) / self.geotransform[1])
        raster_y = int((y - self.geotransform[3]) / self.geotransform[5])

        height_matrix = self.layer.GetRasterBand(1).ReadAsArray(raster_x, raster_y, 1, 1)

        return float(height_matrix[0][0])

    def value_interpolated(self, point, k=3):
        """
        """
        # FIXME: Current implementation fails across borders (height matrix). Fallback to point.

        if not self.geotransform:
            # Data is not available
            raise AssertionError("No elevation data available for the given point.")

        x, y = (point[0], point[1])
        if self.crs != 'epsg:4326':
            x, y = self.crs_transformer.transform(x, y)

        # Transform to raster point coordinates
        #pixel_is_area = False #if pixel_is_area:
        raster_x = int((x - self.geotransform[0]) / self.geotransform[1])
        raster_y = int((y - self.geotransform[3]) / self.geotransform[5])
        coords_x = ((raster_x * self.geotransform[1])) + self.geotransform[0]
        coords_y = ((raster_y * self.geotransform[5])) + self.geotransform[3]
        offset_x = - (coords_x - x) / self.geotransform[1]
        offset_y = - (coords_y - y) / self.geotransform[5]

        try:
            if k == 1:
                height_matrix = self.layer.GetRasterBand(1).ReadAsArray(raster_x, raster_y, 2, 2)
            elif k == 3:
                height_matrix = self.layer.GetRasterBand(1).ReadAsArray(raster_x - 1, raster_y - 1, 4, 4)
        except Exception as e:
            # TODO: Better support for borders
            return self.value_simple(point)

        # Correct EUDEM11 <10000 values
        try:
            height_matrix = np.maximum(height_matrix, 0)
        except TypeError as e:
            # Fix None values (empty / missing)
            # TODO: Except on sea, this should possibly get the average from surrounding values
            return 0

        if k == 1:
            interpolated = interp2d([0, 1], [0, 1], height_matrix, 'linear')  # , copy=False
        elif k == 3:
            interpolated = interp2d([-1, 0, 1, 2], [-1, 0, 1, 2], height_matrix, 'cubic')  # , copy=False
        else:
            raise AssertionError()

        value = interpolated(offset_x, offset_y)

        return float(value)


class GeoRasterLayer:
    """
    Groups several GeoRasterTile configurations.
    """

    def __init__(self, tiles_config):
        self.tiles_config = tiles_config

        self._last_tile = None
        self._last_tile_config = None

        # Cache of transformers for different georaster tile CRS
        self._transformers = {}

    def _get_transformer(self, crs):
        crs = crs.lower()
        transformer = self._transformers.get(crs, None)
        if transformer is None:
            transformer = pyproj.Transformer.from_proj('epsg:4326', crs, always_xy=True)
            self._transformers[crs] = transformer
        return transformer

    def _transform_wgs84_to(self, point, crs):
        projected_point = point
        if crs != 'epsg:4326':
            tile_crs_transformer = self._get_transformer(crs)
            projected_point = tile_crs_transformer.transform(point[0], point[1])
        return projected_point

    def tile_from_point(self, point):
        """
        Returns the GeoRasterTile for the given point.

        This method caches the last accessed tile, as it is more likely to be hit next.
        """

        if self._last_tile:
            projected_point = self._transform_wgs84_to(point, self._last_tile.crs)
            if (projected_point[0] >= self._last_tile_config['bounds'][0] and projected_point[0] < self._last_tile_config['bounds'][2] and
                projected_point[1] >= self._last_tile_config['bounds'][1] and projected_point[1] < self._last_tile_config['bounds'][3]):
                return self._last_tile

        for cc in self.tiles_config:

            projected_point = self._transform_wgs84_to(point, cc['crs'])

            #if (point[0] >= cc['bounds_wgs84_xy'][0] and point[0] < cc['bounds_wgs84_xy'][2] and
            #    point[1] >= cc['bounds_wgs84_xy'][1] and point[1] < cc['bounds_wgs84_xy'][3]):
            if (projected_point[0] >= cc['bounds'][0] and projected_point[0] < cc['bounds'][2] and
                projected_point[1] >= cc['bounds'][1] and projected_point[1] < cc['bounds'][3]):
                self._last_tile_config = cc
                self._last_tile = GeoRasterTile.load(cc['path'], cc['crs'])
                return self._last_tile

        return None

    def value(self, point, interpolate=True):
        tile = self.tile_from_point(point)
        if tile is None:
            raise DDDException("No raster tile found for point: %s" % (point, ))
        return tile.value(point, interpolate)

    def area(self, bounds):
        """
        Returns a height matrix for the area defined by the given bounds in WGS84 coordinates.
        """

        # FIXME: Fails if multiple chunks are touched
        minx, miny, maxx, maxy = bounds

        tile = self.tile_from_point([minx, miny])

        if not tile or not tile.geotransform:
            raise DDDException("No elevation data available for the given point.")

        if tile.crs != 'epsg:4326':
            minx, miny = self.crs_transformer.transform(minx, miny)
            maxx, maxy = self.crs_transformer.transform(maxx, maxy)

        # Transform to raster point coordinates
        raster_min_x = int((minx - tile.geotransform[0]) / tile.geotransform[1])
        raster_min_y = int((miny - tile.geotransform[3]) / tile.geotransform[5])
        raster_max_x = int((maxx - tile.geotransform[0]) / tile.geotransform[1])
        raster_max_y = int((maxy - tile.geotransform[3]) / tile.geotransform[5])

        # Check if limits are hit
        if (raster_max_x > tile.layer.RasterXSize - 1) or raster_max_y < 0:
            logger.error("Raster area [%d, %d, %d, %d] requested exceeds tile bounds [%d, %d] (not implemented).",
                         raster_min_x, raster_min_y, raster_max_x, raster_max_y, tile.layer.RasterXSize, tile.layer.RasterYSize)
            raise NotImplementedError()
        if raster_max_x > tile.layer.RasterXSize - 1:
            raster_max_x = tile.layer.RasterXSize - 1
        if raster_max_y < 0:
            raster_max_y = 0

        # Note that readasarray is positive south, whereas bounds are positive up
        height_matrix = tile.layer.GetRasterBand(1).ReadAsArray(raster_min_x,
                                                                raster_max_y,
                                                                raster_max_x - raster_min_x + 1,
                                                                raster_min_y - raster_max_y + 1)

        return height_matrix


    '''
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
    '''
