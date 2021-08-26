# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import argparse
from functools import partial
import json
import logging
import math
import os
import subprocess
import sys

import geojson
from pygeotile.tile import Tile
import pyproj
from shapely import ops
from shapely.geometry.geo import shape

from ddd.core import settings
from ddd.core.cli import D1D2D3Bootstrap
from ddd.core.command import DDDCommand
from ddd.ddd import ddd, D1D2D3
from ddd.geo import terrain
from ddd.osm import osm
from ddd.pipeline.pipeline import DDDPipeline
from ddd.osm.commands import downloader
from ddd.geo.elevation import ElevationModel
import datetime
from ddd.util.common import parse_bool


#from osm import OSMDDDBootstrap
# Get instance of logger for this module
logger = logging.getLogger(__name__)


def range_around(bounds, center=None):
    if center is None:
        center = [0, 0]
    pairs = []
    for x in range(bounds[0], bounds[2]):
        for y in range(bounds[1], bounds[3]):
            pairs.append((x, y))
    pairs.sort(key=lambda p: (abs(p[0]- center[0])) + abs(p[1] - center[1]))

    return pairs



class OSMBuildCommand(DDDCommand):

    chunk_size = 250  # 500: 4/km2,  250: 16/km2,  200: 25/km2,  125: 64/km2
    chunk_size_extra_filter = 250  # salamanca: 250  # vigo: 500

    def parse_args(self, args):

        #program_name = os.path.basename(sys.argv[0])
        parser = argparse.ArgumentParser()  # description='', usage = ''

        #parser.add_argument("-w", "--worker", default=None, help="worker (i/n)")
        parser.add_argument("-l", "--limit", type=int, default=None, help="tasks limit")

        parser.add_argument("--name", type=str, default=None, help="base name for output")
        parser.add_argument("--center", type=str, default=None, help="center of target area (lon, lat)")
        parser.add_argument("--area", type=str, default=None, help="target area polygon GeoJSON")
        parser.add_argument("--radius", type=float, default=None, help="radius of target area (m)")
        parser.add_argument("--size", type=float, default=None, help="tile size or 0 (m)")
        parser.add_argument("--xyztile", type=str, default=None, help="XYZ grid tile")

        args = parser.parse_args(args)

        self.limit = args.limit

        self.name = args.name

        if args.area:
            self.area = shape(json.loads(args.area))
            self._radius = None
        else:
            self.area = None
            self._radius = args.radius

        self.chunk_size = args.size

        self.xyztile = None
        if (args.xyztile):
            if (args.radius or args.center or args.size):
                logger.error("Option --xyztile cannot be used with --radius, --center or --size .")
                sys.exit(2)

            x, y, z = args.xyztile.split(",")
            self.xyztile = int(x), int(y), int(z)

        else:
            center = args.center.split(",")
            self.center = (float(center[0]), float(center[1]))


    def get_data(self, datapath, dataname, center_wgs84):

        # Extract area from PBF
        mainpbffile = os.path.join(datapath, "spain-latest.osm.pbf")
        #mainpbffile = os.path.join(datapath, "latvia-latest.osm.pbf")
        #mainpbffile = os.path.join(datapath, "france-latest.osm.pbf")
        #mainpbffile = os.path.join(datapath, "south-africa-latest.osm.pbf")

        selectedpbffile = os.path.join(datapath, "%s.pbf" % dataname)

        # TODO: Use area bounds!
        sides = 15 * 0.01  # Approximate degrees to km
        #sides = 5 * 0.001  # Approximate degrees to km
        bounds = [center_wgs84[0] - sides, center_wgs84[1] - sides, center_wgs84[0] + sides, center_wgs84[1] + sides]

        # Run osmconvert to select the area of interes
        #osmconvert spain-latest.osm.pbf -b=-5.870,40.760,-5.470,41.160 -o=salamanca-latest.osm.pbf
        if not os.path.isfile(selectedpbffile):
            logger.info("Extracting data from %s to %s (%s)", mainpbffile, selectedpbffile, bounds)
            subprocess.check_output(['osmconvert', mainpbffile, "-b=%.3f,%.3f,%.3f,%.3f" % (bounds[0], bounds[1], bounds[2], bounds[3]),
                                     '-o=%s' % selectedpbffile])

        # Run osmtogeojson
        outputgeojsonfile = os.path.join(datapath, "%s.osm.geojson" % dataname)
        osmtogeojson_path = os.path.expanduser(settings.OSMTOGEOJSON_PATH)
        logger.info("Converting to GeoJSON from %s to %s", selectedpbffile, outputgeojsonfile)
        # TODO: Use temporary file
        with open(outputgeojsonfile, "w") as outfile:
            command = [osmtogeojson_path, "-m", selectedpbffile]
            processresult = subprocess.run(command, stdout=outfile)


    def get_data_osm(self, datapath, dataname, center_wgs84):
        """
        """
        #TODO: Use bounds if area is passed?

        selectedosmfile = os.path.join(datapath, "%s.osm" % dataname)
        force_get_data = parse_bool(D1D2D3Bootstrap.data.get('ddd:osm:datasource:force_refresh', False))

        #sides = 15 * 0.01  # Approximate degrees to km
        sides = 5 * 0.001  # Approximate degrees to km
        bounds = [center_wgs84[0] - sides, center_wgs84[1] - sides, center_wgs84[0] + sides, center_wgs84[1] + sides]
        #bounds = area.bounds()

        # Retrieve
        if not os.path.isfile(selectedosmfile) or force_get_data:
            logger.info("Retrieving data to %s (%s)", selectedosmfile, bounds)
            downloader.download_block(bounds, selectedosmfile)

        # Run osmtogeojson
        outputgeojsonfile = os.path.join(datapath, "%s.osm.geojson" % dataname)
        osmtogeojson_path = os.path.expanduser(settings.OSMTOGEOJSON_PATH)
        logger.info("Converting to GeoJSON from %s to %s", selectedosmfile, outputgeojsonfile)
        # TODO: Use temporary file
        with open(outputgeojsonfile, "w") as outfile:
            command = [osmtogeojson_path, "-m", selectedosmfile]
            processresult = subprocess.run(command, stdout=outfile)


    def process_xyztile(self):
        x, y, z = self.xyztile
        tile = Tile.from_google(x, y, zoom=z)
        point_min, point_max = tile.bounds

        min_lat, min_lon = point_min.latitude_longitude
        max_lat, max_lon = point_max.latitude_longitude

        center_lat = (min_lat + max_lat) / 2.0
        center_lon = (min_lon + max_lon) / 2.0

        self.center = (center_lon, center_lat)
        self.area = ddd.rect([min_lon, min_lat, max_lon, max_lat]).geom

    def run(self):

        # TODO: Move to pipelined builder
        logger.warn("Move to builder")

        logger.info("Running DDD123 OSM build command.")

        D1D2D3Bootstrap._instance._unparsed_args = None

        tasks_count = 0

        if self.xyztile:
            self.process_xyztile()

        #name = "vigo"
        #center_wgs84 = vigo_wgs84
        #area = area_vigo_huge_rande
        center_wgs84 = self.center


        # Name
        if self.name is None:
            self.name = "ddd-osm-%.3f,%.3f" % center_wgs84
        name = self.name

        path = "data/osm/"

        # Prepare data
        # Check if geojson file is available
        #sides = 15 * 0.01  # Approximate degrees to km
        sides = 5 * 0.001
        roundto = sides / 3
        datacenter = int(self.center[0] / roundto) * roundto, int(self.center[1] / roundto) * roundto
        dataname = name + "_%.4f_%.4f" % datacenter
        datafile = os.path.join(path, "%s.osm.geojson" % dataname)

        # Get data if needed or forced
        force_get_data = parse_bool(D1D2D3Bootstrap.data.get('ddd:osm:datasource:force_refresh', False))
        file_exists = os.path.isfile(datafile)

        if force_get_data or not file_exists:
            logger.info("Data file '%s' not found or datasource:force_refresh is True. Trying to produce data." % datafile)
            #self.get_data(path, dataname, datacenter)
            self.get_data_osm(path, dataname, datacenter)

        # Read data
        files = [os.path.join(path, f) for f in [dataname + '.osm.geojson'] if os.path.isfile(os.path.join(path, f)) and f.endswith(".geojson")]
        logger.info("Reading %d files from %s: %s" % (len(files), path, files))

        osm_proj = pyproj.Proj(init='epsg:4326')  # FIXME: API reocmends using only 'epsg:4326' but seems to give weird coordinates? (always_xy=Tre?)
        ddd_proj = pyproj.Proj(proj="tmerc",
                               lon_0=center_wgs84[0], lat_0=center_wgs84[1],
                               k=1,
                               x_0=0., y_0=0.,
                               units="m", datum="WGS84", ellps="WGS84",
                               towgs84="0,0,0,0,0,0,0",
                               no_defs=True)

        # TODO: Move area resolution outside this method and resolve after processing args
        area_ddd = None
        if self.area is not None:
            trans_func = partial(pyproj.transform, osm_proj, ddd_proj)
            area_ddd = ops.transform(trans_func, self.area)
        elif not self.chunk_size:
            resolution = 8
            if resolution > 1:
                area_ddd = ddd.point().buffer(self._radius, cap_style=ddd.CAP_ROUND, resolution=resolution).geom
            else:
                area_ddd = ddd.rect([-self._radius, -self._radius, self._radius, self._radius]).geom

        logger.info("Area meters/coords=%s", area_ddd)
        if area_ddd:
            logger.info("Complete polygon area: %.1f km2 (%d at 500, %d at 250, %d at 200)", area_ddd.area / (1000 * 1000), math.ceil(area_ddd.area / (500 * 500)), math.ceil(area_ddd.area / (250 * 250)), math.ceil(area_ddd.area / (200 * 200)))

        # TODO: organise tasks and locks in pipeline, not here
        skipped = 0
        existed = 0

        tiles = [(0, 0)] if not self.chunk_size else range_around([-64, -64, 64, 64])

        for (idx, (x, y)) in enumerate(tiles):
        #for x, y in range_around([-8, -8, 8, 8]):  # -8, 3

            if self.limit and tasks_count >= self.limit:
                logger.info("Limit of %d tiles hit.", self.limit)
                break


            if self.chunk_size:

                logger.info("Chunk size: %s", self.chunk_size)

                bbox_crop = [x * self.chunk_size, y * self.chunk_size, (x + 1) * self.chunk_size, (y + 1) * self.chunk_size]
                bbox_filter = [bbox_crop[0] - self.chunk_size_extra_filter, bbox_crop[1] - self.chunk_size_extra_filter,
                               bbox_crop[2] + self.chunk_size_extra_filter, bbox_crop[3] + self.chunk_size_extra_filter]

                area_crop = ddd.rect(bbox_crop).geom
                area_filter = ddd.rect(bbox_filter).geom

                #area_ddd = ddd.rect(bbox_crop)
                trans_func = partial(pyproj.transform, ddd_proj, osm_proj)
                self.area = ops.transform(trans_func, area_crop)

                shortname = '%s_%d_%d,%d' % (name, abs(x) + abs(y), bbox_crop[0], bbox_crop[1])
                filenamebase = 'output/%s/%s' % (name, shortname)
                filename = filenamebase + ".glb"

            elif self.xyztile:
                area_crop = area_ddd
                area_filter = area_ddd.buffer(self.chunk_size_extra_filter, join_style=ddd.JOIN_MITRE)

                shortname = '%s_%d_%d_%d' % (name, self.xyztile[2], self.xyztile[0], self.xyztile[1])
                filenamebase = 'output/%s/%s' % (name, shortname)
                filename = filenamebase + ".glb"

            else:

                #logger.info("No chunk size defined (area was given)")

                area_crop = area_ddd
                #print(area_crop)
                area_filter = area_ddd.buffer(self.chunk_size_extra_filter, join_style=ddd.JOIN_MITRE)

                shortname = '%s_%dr_%.3f,%.3f' % (name, self._radius if self._radius else 0, self.center[0], self.center[1])
                filenamebase = 'output/%s/%s' % (name, shortname)
                filename = filenamebase + ".glb"

            if area_ddd and not area_ddd.intersects(area_crop):
                skipped += 1
                #logger.debug("Skipping: %s (cropped area not contained in greater filtering area)", filename)
                #if os.path.exists(filename):
                #    logger.info("Deleting: %s", filename)
                #    os.unlink(filename)
                continue

            if not D1D2D3Bootstrap._instance.overwrite and os.path.exists(filename):
                #logger.debug("Skipping: %s (already exists)", filename)
                existed += 1
                continue


            # Try to lock
            lockfilename = filename + ".lock"
            try:
                with open(lockfilename, "x") as _:

                    old_formatters = {hdlr: hdlr.formatter for hdlr in logging.getLogger().handlers}
                    if D1D2D3Bootstrap._instance.debug:
                        new_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(module)s [' + shortname + '] %(message)s')
                    else:
                        new_formatter = logging.Formatter('%(asctime)s [' + shortname + '] %(message)s')

                    # Apply formatter to existing loggers
                    for hdlr in logging.getLogger().handlers:
                        hdlr.setFormatter(new_formatter)

                    # Create a file handler for this process log
                    # TODO: Support this at pipeline level / ddd command (?)
                    build_log_file = False
                    if build_log_file:
                        fh = logging.FileHandler('/tmp/%s.log' % (shortname, ))
                        fh.setLevel(level=logging.DEBUG)
                        fh.setFormatter(new_formatter)
                        logging.getLogger().addHandler(fh)

                    # Check elevation is available
                    elevation = ElevationModel.instance()
                    center_elevation = elevation.value(center_wgs84)
                    logger.info("Center point elevation: %s", center_elevation)



                    logger.info("Generating: %s", filename)
                    pipeline = DDDPipeline(['pipelines.osm_base.s10_init.py',
                                            'pipelines.osm_common.s10_locale_config.py',

                                            'pipelines.osm_base.s20_osm_features.py',
                                            'pipelines.osm_base.s20_osm_features_export_2d.py',
                                            'pipelines.osm_base.s30_groups.py',
                                            'pipelines.osm_base.s30_groups_ways.py',
                                            'pipelines.osm_base.s30_groups_buildings.py',
                                            'pipelines.osm_base.s30_groups_areas.py',
                                            'pipelines.osm_base.s30_groups_items_nodes.py',
                                            'pipelines.osm_base.s30_groups_items_ways.py',
                                            'pipelines.osm_base.s30_groups_items_areas.py',
                                            'pipelines.osm_base.s30_groups_export_2d.py',

                                            'pipelines.osm_base.s40_structured.py',
                                            'pipelines.osm_base.s40_structured_export_2d.py',

                                            'pipelines.osm_augment.s45_pitch.py',

                                            'pipelines.osm_base.s50_stairs.py',
                                            'pipelines.osm_base.s50_positioning.py',
                                            'pipelines.osm_base.s50_crop.py',
                                            'pipelines.osm_base.s50_90_export_2d.py',

                                            'pipelines.osm_augment.s50_ways.py',
                                            'pipelines.osm_augment.s55_plants.py',
                                            'pipelines.osm_augment.s55_rocks.py',

                                            'pipelines.osm_base.s60_model.py',
                                            'pipelines.osm_base.s65_model_metadata_clean.py',
                                            'pipelines.osm_base.s65_model_post_opt.py',
                                            'pipelines.osm_base.s69_model_export_3d.py',

                                            'pipelines.osm_base.s70_metadata.py',

                                            'pipelines.osm_gdterrain.s60_heightmap_export.py',
                                            'pipelines.osm_gdterrain.s60_splatmap_export.py',

                                            'pipelines.osm_extras.s30_icons.py',

                                            'pipelines.osm_extras.s80_model_compress.py',

                                            #'pipelines.osm_extras.mapillary.py',
                                            #'pipelines.osm_extras.ortho.py',

                                            ], name="OSM Build Pipeline")
                    pipeline.data['osmfiles'] = files
                    pipeline.data['filenamebase'] = filenamebase

                    pipeline.data['ddd:pipeline:start_date'] = datetime.datetime.now()

                    pipeline.data['tile:bounds_wgs84'] = self.area.bounds
                    pipeline.data['tile:bounds_m'] = area_crop.bounds


                    # Fusion DDD data with pipeline data, so changes to the later affect the former
                    # TODO: better way to do this without globals and merging data?
                    D1D2D3.data.update(pipeline.data)
                    D1D2D3.data = pipeline.data

                    try:

                        osmbuilder = osm.OSMBuilder(area_crop=area_crop, area_filter=area_filter, osm_proj=osm_proj, ddd_proj=ddd_proj)
                        pipeline.data['osm'] = osmbuilder

                        pipeline.run()
                        #scene = osmbuilder.generate()

                        tasks_count += 1

                    finally:

                        # Ensure lock file is removed
                        try:
                            os.unlink(lockfilename)
                        except Exception as e:
                            pass

                    for hdlr in logging.getLogger().handlers:
                        hdlr.setFormatter(old_formatters[hdlr])

            except FileExistsError as e:
                logger.info("Skipping: %s (lock file exists)", filename)

        if existed > 0:
            logger.info("Skipped %d files that already existed.", existed)
        if skipped > 0:
            logger.info("Skipped %d files not contained in greater filtering area.", skipped)


#self = OSMDDDBootstrap()
#self.parse_args(D1D2D3Bootstrap._instance._unparsed_args)
#D1D2D3Bootstrap._instance._unparsed_args = None

