# ddd - DDD123
# Library for simple scene modelling.
# Jose Juan Montes and Contributors 2019-2021

import glob
import json
import logging
import math
import os
from pathlib import Path
from shapely.geometry.geo import shape

import argparse
from geographiclib.geodesic import Geodesic
import pyproj
from pyproj.proj import Proj

from ddd.core.command import DDDCommand
from ddd.geo.georaster import GeoRasterTile


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class GeoRasterCollectCommand(DDDCommand):
    """
    """

    def parse_args(self, args):

        #program_name = os.path.basename(sys.argv[0])
        parser = argparse.ArgumentParser()  # description='', usage = ''

        #parser.add_argument("--radius", type=float, default=None, help="radius of target area")
        #parser.add_argument("--area", type=str, help="GeoJSON polygon of target area")
        #parser.add_argument("--tile", type=float, help="tile size in meters (0 for entire area)")

        args = parser.parse_args(args)

    def run(self):

        logger.info("DDD123 Geo Raster files config collect.")

        self.georaster_collect()

    def georaster_collect(self):

        # Walk dir

        basedir = "."
        pathstr = basedir + "/" + "%(filename)s"

        extensions = ['.tif', '.tiff']

        configs = []

        outProj = pyproj.Proj('EPSG:4326')
        projs = {'EPSG:4326': outProj}

        for root, dirs, files in os.walk(basedir, followlinks=True):
            for name in sorted(files):

                path = str(os.path.join(root, name))
                extension = "." + path.split(".")[-1]
                if extension.lower() not in extensions:
                    continue

                crs = 'EPSG:4326'
                if 'eudem11/' in path or 'eu_dem_v11' in path: crs = 'EPSG:3035'
                if 'etrs89-hu29' in path.lower().replace("_", "-"): crs = 'EPSG:25829'
                if 'etrs89-hu30' in path.lower().replace("_", "-"): crs = 'EPSG:25830'
                if 'etrs89-hu31' in path.lower().replace("_", "-"): crs = 'EPSG:25831'

                tile = GeoRasterTile.load(str(path), crs)
                #print("File: %s  Transform: %s" % (str(path), tile.geotransform))

                layer = tile.layer

                geotransform = layer.GetGeoTransform()
                #print("file: %s  geotransform: %s" % (path, geotransform))

                minx = geotransform[0]
                maxx = geotransform[0] + layer.RasterXSize * geotransform[1]
                miny = geotransform[3]
                maxy = geotransform[3] + layer.RasterYSize * geotransform[5]
                bounds = [minx, min(miny, maxy), maxx, max(miny, maxy)]

                # Transform bounds to WGS84
                inProj = projs.get(crs, None)
                if not inProj:
                    inProj = pyproj.Proj(crs)
                    projs[crs] = inProj
                minx_wgs84, miny_wgs84 = pyproj.transform(inProj, outProj, minx, miny, always_xy=True)
                maxx_wgs84, maxy_wgs84 = pyproj.transform(inProj, outProj, maxx, maxy, always_xy=True)
                bounds_wgs84 = [minx_wgs84, min(miny_wgs84, maxy_wgs84), maxx_wgs84, max(miny_wgs84, maxy_wgs84)]
                #bounds_wgs84 = [minx_wgs84, miny_wgs84, maxx_wgs84, maxy_wgs84]

                diagonal_m = Geodesic.WGS84.Inverse(miny_wgs84, minx_wgs84, maxy_wgs84, maxx_wgs84)['s12']
                resolution_m = diagonal_m / (math.hypot(layer.RasterXSize, layer.RasterYSize))


                config = {'path': pathstr % {'filename': path},
                          'crs': crs,
                          'transform': geotransform,
                          'bounds': bounds,
                          'bounds_wgs84_xy': bounds_wgs84,
                          'resolution_m': resolution_m,
                          'geotransform': geotransform }
                configs.append(config)

        #configs.sort(key=lambda f: int(f['resolution_m']) if not math.isnan(f['resolution_m']) else 0)

        text = ""
        last_dir = None
        for f in configs:

            # Add newlines between groups
            file_dir = f['path'].split("/")[:-1]
            if file_dir != last_dir:
                last_dir = file_dir
                text += "\n"

            text += ("    {'path': '%s',\n" % f['path'])
            text += ("     'crs': '%s',\n" % f['crs'])
            text += ("     'resolution_m': '%s',\n" % f['resolution_m'])
            #text += ("     'transform': %s,\n" % (f['transform'], ))
            text += ("     'bounds': %s,\n" % f['bounds'])
            text += ("     'bounds_wgs84_xy': %s},  # (%.3f m/pixel)\n" % (f['bounds_wgs84_xy'], f['resolution_m']))

        #text += ("]\n")

        print(text)

        logger.info("Found %d georaster files.", len(configs))


