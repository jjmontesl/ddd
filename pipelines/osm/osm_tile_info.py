# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import datetime
import glob
import os
import re

import geojson
from pygeotile.tile import Tile

from ddd.core import settings
from ddd.ddd import ddd
from ddd.pipeline.decorators import dddtask


@dddtask()
def pipeline_start(pipeline, root, logger):
    """
    Walk a tile directory and report about available tiles.

    Called from local data dir as:

        ddd ~/ddd/pipelines/osm/osm_tile_info.py
    """

    source_dir = settings.DDD_WORKDIR + "/ddd_http/"
    #source_regex = r"output/ddd_http/([0-9]+)/([0-9]+)/([0-9]+)(.*)"
    source_regex = r".*(17)/([0-9]+)/([0-9]+)(.*)"

    logger.info("Finding output results from: %s (%s)" % (source_dir, source_regex))


    #use_file = "/tmp/tiles.txt"
    use_file = None
    if use_file:
        listing = open(use_file, "r").read().split("\n")
    else:
        listing = glob.glob(source_dir + "**/*.glb", recursive=True)
        listing = [f[len(source_dir):] for f in listing]


    features = []
    feature_idx = {}

    for filename in listing:

        #dirname = os.path.dirname(filename)
        #basename = os.path.basename(filename)


        if not filename.endswith(".glb"):
            continue
        if filename.endswith(".uncompressed.glb"):
            continue
        #print(filename)

        #logger.debug(filename)
        matches = re.match(source_regex, filename)

        if matches:

            x, y, z = int(matches.group(2)), int(matches.group(3)), matches.group(1)
            if z == '.':
                z = 17
            else:
                z = int(z)

            data = {"z": z,
                    "x": x,
                    "y": y,
                    "remainder": matches.group(4)}

            #logger.debug(data)
            tile = Tile.from_google(x, y, zoom=z)
            point_min, point_max = tile.bounds

            min_lat, min_lon = point_min.latitude_longitude
            max_lat, max_lon = point_max.latitude_longitude

            center_lat = (min_lat + max_lat) / 2.0
            center_lon = (min_lon + max_lon) / 2.0

            center = (center_lon, center_lat)
            area = ddd.rect([min_lon, min_lat, max_lon, max_lat]).geom

            file_path = os.path.join(source_dir, filename)

            mtime = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
            age = datetime.datetime.now() - mtime

            feature = geojson.Feature(geometry=area,
                                      properties={"available": True, #exists > 0,
                                                  "name": filename,
                                                  "z": z,
                                                  "x": x,
                                                  "y": y,
                                                  "mtime": str(mtime),
                                                  "size": os.stat(file_path).st_size if os.path.exists(file_path) else None} )
            if (z, x ,y) not in feature_idx:
                feature_idx[(z, x, y)] = feature
                features.append(feature)
            else:
                pass


    feature_collection = geojson.FeatureCollection(features)
    dump = geojson.dumps(feature_collection, sort_keys=True, indent=4)
    print(dump + "\n")

    logger.info("Found %d files." % len(features))


'''

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


'''