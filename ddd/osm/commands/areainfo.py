# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

from ddd.osm.commands.build import OSMBuildCommand
from shapely.geometry.geo import shape
import logging
import argparse
import json


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class OSMDataInfoCommand(OSMBuildCommand):

    chunk_size = 250  # 500: 4/km2,  250: 16/km2,  200: 25/km2,  125: 64/km2
    chunk_size_extra_filter = 250  # salamanca: 250  # vigo: 500

    def parse_args(self, args):

        #program_name = os.path.basename(sys.argv[0])
        parser = argparse.ArgumentParser()  # description='', usage = ''

        #parser.add_argument("-w", "--worker", default=None, help="worker (i/n)")
        parser.add_argument("--name", type=str, default=None, help="base name for output")
        parser.add_argument("--center", type=str, default=None, help="center of target area")
        parser.add_argument("--area", type=str, default=None, help="target area polygon GeoJSON")
        #parser.add_argument("--radius", type=float, default=None, help="radius of target area")
        #parser.add_argument("--area", type=str, help="GeoJSON polygon of target area")
        #parser.add_argument("--tile", type=float, help="tile size in meters (0 for entire area)")

        args = parser.parse_args(args)

        center = args.center.split(",")
        self.center = (float(center[0]), float(center[1]))

        self.name = args.name
        self.area = shape(json.loads(args.area))

    def run(self):

        logger.info("DDD123 OSM data information.")

        self.areainfo()

    def areainfo(self):

        # Name
        if self.name is None:
            self.name = "ddd-osm-%.3f,%.3f" % self.center
        name = self.name

        osm_proj = pyproj.Proj(init='epsg:4326')  # FIXME: API reocmends using only 'epsg:4326' but seems to give weird coordinates?
        ddd_proj = pyproj.Proj(proj="tmerc",
                               lon_0=self.center[0], lat_0=self.center[1],
                               k=1,
                               x_0=0., y_0=0.,
                               units="m", datum="WGS84", ellps="WGS84",
                               towgs84="0,0,0,0,0,0,0",
                               no_defs=True)

        # TODO: Move area resolution outside this method and resolve after processing args
        area_ddd = None
        if self.area:
            trans_func = partial(pyproj.transform, osm_proj, ddd_proj)
            area_ddd = ops.transform(trans_func, self.area)
        else:
            area_ddd = ddd.point().buffer(self._radius, cap_style=ddd.CAP_ROUND, resolution=8).geom

        # GeoJSON with info
        # TODO: Move to OSM generation
        # python osm.py > ~/Documentos/DrivingGame/QGISProj/salamanca-availability.geojson
        features = []
        for (idx, (x, y)) in enumerate(range_around([-64, -64, 64, 64])):

            bbox_crop = [x * self.chunk_size, y * self.chunk_size, (x + 1) * self.chunk_size, (y + 1) * self.chunk_size]
            bbox_filter = [bbox_crop[0] - self.chunk_size_extra_filter, bbox_crop[1] - self.chunk_size_extra_filter,
                           bbox_crop[2] + self.chunk_size_extra_filter, bbox_crop[3] + self.chunk_size_extra_filter]
            shortname = '%s_%d_%d,%d' % (name, abs(x) + abs(y), bbox_crop[0], bbox_crop[1])
            filenamebase = 'output/%s/%s' % (name, shortname)
            filename = filenamebase + ".glb"

            area_crop = ddd.rect(bbox_crop).geom
            area_filter = ddd.rect(bbox_filter).geom

            if not area_ddd.intersects(area_crop):
                continue

            exists = os.path.exists(filename) and os.stat(filename).st_size > 0

            p1 = terrain.transform_ddd_to_geo(ddd_proj, [bbox_crop[0], bbox_crop[1]])
            p2 = terrain.transform_ddd_to_geo(ddd_proj, [bbox_crop[2], bbox_crop[1]])
            p3 = terrain.transform_ddd_to_geo(ddd_proj, [bbox_crop[2], bbox_crop[3]])
            p4 = terrain.transform_ddd_to_geo(ddd_proj, [bbox_crop[0], bbox_crop[3]])
            rect = geojson.Polygon([ [p1, p2, p3, p4] ])
            feature = geojson.Feature(geometry=rect,
                                      properties={"available": exists > 0,
                                                  "name": filename,
                                                  "size": os.stat(filename).st_size if os.path.exists(filename) else 0} )
            features.append(feature)
        feature_collection = geojson.FeatureCollection(features)
        dump = geojson.dumps(feature_collection, sort_keys=True, indent=4)
        print(dump + "\n")


