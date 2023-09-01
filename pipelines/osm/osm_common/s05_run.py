# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020
import datetime
from ddd.osm import osm
from ddd.core import settings

'''
from ddd.core import settings
from ddd.core.cli import D1D2D3Bootstrap
from ddd.core.command import DDDCommand
from ddd.ddd import ddd, D1D2D3
from ddd.geo import terrain
from ddd.osm import osm
from ddd.pipeline.pipeline import DDDPipeline
from ddd.osm.commands import downloader
from ddd.util.common import parse_bool
'''

from functools import partial
import json
import logging
import math
import os
from shapely import ops
from shapely.geometry.geo import shape
import sys

import geojson
from pygeotile.tile import Tile
import pyproj

from ddd.core.cli import D1D2D3Bootstrap
from ddd.ddd import ddd, D1D2D3
from ddd.geo.elevation import ElevationModel
from ddd.geo.sources.osm import OnlineOSMDataSource
from ddd.pipeline.decorators import dddtask
from ddd.util.common import parse_meters, parse_tile, parse_bool


@dddtask(order="5.10.+", init=True)
def osm_init(root, pipeline, logger):
    logger.info("Starting OSM Build pipeline")


#parser.add_argument("--name", type=str, default=None, help="base name for output")
#parser.add_argument("--center", type=str, default=None, help="center of target area (lon, lat)")
#parser.add_argument("--area", type=str, default=None, help="target area polygon GeoJSON")
#parser.add_argument("--radius", type=float, default=None, help="radius of target area (m)")
#parser.add_argument("--size", type=float, default=None, help="tile size or 0 (m)")
#parser.add_argument("--xyztile", type=str, default=None, help="XYZ grid tile")
@dddtask(init=True, params={
             'ddd:osm:output:name': None,
             'ddd:osm:area:name': None,
             'ddd:osm:area:radius': None })
def osm_init_params(root, pipeline, logger):
    """
    Process OSM build parameters.
    """

    if pipeline.data.get('ddd:osm:area', None):
        # Use provided shape
        area_shape = shape(json.loads(pipeline.data.get('ddd:osm:area')))
        pipeline.data['ddd:osm:area:shape'] = area_shape
        pipeline.data['ddd:osm:area:radius'] = None

    if pipeline.data.get('ddd:osm:area:radius', None):
        # Convert radius to meters
        pipeline.data['ddd:osm:area:radius'] = parse_meters(pipeline.data['ddd:osm:area:radius'])
        pipeline.data['ddd:osm:area:shape'] = None

    if pipeline.data.get('ddd:osm:area:chunk_size', None):
        pipeline.data['ddd:osm:area:chunk_size'] = parse_meters(pipeline.data['ddd:osm:area:chunk_size'])

    xyztile = pipeline.data.get('ddd:osm:area:xyztile', None)
    if xyztile:
        if (pipeline.data.get('ddd:osm:area:radius', None) or
            pipeline.data.get('ddd:osm:area:center', None) or
            pipeline.data.get('ddd:osm:area:size', None)):
            logger.error("Option --xyztile cannot be used with --radius, --center or --size .")
            sys.exit(2)

        pipeline.data['ddd:osm:area:xyztile'] = parse_tile(xyztile)

    if pipeline.data.get('ddd:osm:area:center', None):
        center = pipeline.data['ddd:osm:area:center'].split(",")
        center = (float(center[0]), float(center[1]))
        pipeline.data['ddd:osm:area:center'] = center


@dddtask(init=True)
def osm_init_params_xyztile(root, pipeline, logger):

    if not pipeline.data.get('ddd:osm:area:xyztile'): return

    x, y, z = pipeline.data['ddd:osm:area:xyztile']
    tile = Tile.from_google(x, y, zoom=z)
    point_min, point_max = tile.bounds

    min_lat, min_lon = point_min.latitude_longitude
    max_lat, max_lon = point_max.latitude_longitude

    center_lat = (min_lat + max_lat) / 2.0
    center_lon = (min_lon + max_lon) / 2.0

    pipeline.data['ddd:osm:area:center'] = (center_lon, center_lat)
    pipeline.data['ddd:osm:area:shape'] = ddd.rect([min_lon, min_lat, max_lon, max_lat]).geom

@dddtask(init=True)
def osm_init_name(root, pipeline, logger):

    # Name
    name = pipeline.data.get('ddd:osm:output:name', None)
    if name is None:
        center_wgs84 = pipeline.data.get('ddd:osm:area:center')
        name = "ddd-osm-%.3f,%.3f" % center_wgs84
        pipeline.data['ddd:osm:output:name'] = name

    pipeline.data['filenamebase'] = name

@dddtask(order="5.20.+")
def osm_bootstrap(root, pipeline, logger):
    """Starts the build process after evaluating caching and parameters."""
    pass

@dddtask()
def osm_bootstrap_data_fetch(root, pipeline, logger):
    """Fetches data in OSM format to extract features."""

    name = pipeline.data.get('ddd:osm:output:name')
    center = pipeline.data['ddd:osm:area:center']

    # Prepare data
    # Check if geojson file is available
    #sides = 15 * 0.01  # Approximate degrees to km

    path = pipeline.data.get('ddd:osm:datasource:path', os.path.join(settings.DDD_WORKDIR, "data/osm/"))
    logger.info("OSM source data path: %s", path)

    sides = 5 * 0.001
    roundto = sides / 3
    datacenter = int(center[0] / roundto) * roundto, int(center[1] / roundto) * roundto
    dataname = name + "_%.4f_%.4f" % datacenter
    datafile = os.path.join(path, "%s.osm.geojson" % dataname)

    # Get data if needed or forced
    file_exists = os.path.isfile(datafile)
    force_get_data = parse_bool(pipeline.data.get('ddd:osm:datasource:force_refresh', False))

    if force_get_data or not file_exists:
        logger.info("Data file '%s' not found or datasource:force_refresh is True. Trying to produce data." % datafile)
        osmdatasource = OnlineOSMDataSource()
        osmdatasource.get_data(path, dataname, datacenter, force_get_data)

    # Set input files
    files = [os.path.join(path, f) for f in [dataname + '.osm.geojson'] if os.path.isfile(os.path.join(path, f)) and f.endswith(".geojson")]
    pipeline.data['osmfiles'] = files
    logger.info("Reading %d files from %s: %s" % (len(files), path, files))


@dddtask()
def osm_bootstrap_projection(root, pipeline, logger):
    """
    Bootstraps OSM Build process.
    """
    logger.info("Running DDD123 OSM build command.")

    center_wgs84 = pipeline.data.get('ddd:osm:area:center')

    osm_proj = pyproj.Proj(init='epsg:4326')  # FIXME: API reocmends using only 'epsg:4326' but seems to give weird coordinates? (always_xy=Tre?)
    ddd_proj = pyproj.Proj(proj="tmerc",
                           lon_0=center_wgs84[0], lat_0=center_wgs84[1],
                           k=1,
                           x_0=0., y_0=0.,
                           units="m", datum="WGS84", ellps="WGS84",
                           towgs84="0,0,0,0,0,0,0",
                           no_defs=True)

    pipeline.data['ddd:osm:proj:osm'] = osm_proj
    pipeline.data['ddd:osm:proj:ddd'] = ddd_proj

@dddtask()
def osm_bootstrap_areas(root, pipeline, logger):

    chunk_size = None  # 250  # 500: 4/km2,  250: 16/km2,  200: 25/km2,  125: 64/km2
    chunk_size_extra_filter = 250  # salamanca: 250  # vigo: 500 # rivers...

    pipeline.data['ddd:osm:area:chunk_size'] = chunk_size
    pipeline.data['ddd:osm:area:chunk_size_extra_filter'] = chunk_size_extra_filter

    osm_proj = pipeline.data['ddd:osm:proj:osm']
    ddd_proj = pipeline.data['ddd:osm:proj:ddd']
    area_shape = pipeline.data['ddd:osm:area:shape']

    if area_shape is not None:
        trans_func = partial(pyproj.transform, osm_proj, ddd_proj)
        area_ddd = ops.transform(trans_func, area_shape)
    elif not chunk_size:
        resolution = 8
        radius = pipeline.data.get('ddd:osm:area:radius')
        if resolution > 1:
            area_ddd = ddd.point().buffer(radius, cap_style=ddd.CAP_ROUND, resolution=resolution).geom
        else:
            area_ddd = ddd.rect([-radius, -radius, radius, radius]).geom

    pipeline.data['ddd:osm:area:ddd'] = area_ddd

    logger.info("Area meters/coords=%s", area_ddd)
    if area_ddd:
        logger.info("Complete polygon area: %.3f km2 (%d at 500, %d at 250, %d at 200)", area_ddd.area / (1000 * 1000), math.ceil(area_ddd.area / (500 * 500)), math.ceil(area_ddd.area / (250 * 250)), math.ceil(area_ddd.area / (200 * 200)))


@dddtask()
def osm_bootstrap_bbox_crop_filter(root, pipeline, logger):

    name = pipeline.data.get('ddd:osm:output:name', None)
    xyztile = pipeline.data.get('ddd:osm:area:xyztile', None)
    area_ddd = pipeline.data.get('ddd:osm:area:ddd', None)
    center = pipeline.data.get('ddd:osm:area:center', None)
    radius = pipeline.data.get('ddd:osm:area:radius', None)
    chunk_size = pipeline.data.get('ddd:osm:area:chunk_size', None)
    chunk_size_extra_filter = pipeline.data.get('ddd:osm:area:chunk_size_extra_filter', None)

    path = pipeline.data.get('ddd:osm:output:dir', settings.DDD_WORKDIR)

    '''
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
    elif
    '''

    if xyztile:
        area_crop = area_ddd
        area_filter = area_ddd.buffer(chunk_size_extra_filter, join_style=ddd.JOIN_MITRE)

        shortname = '%s_%d_%d_%d' % (name, xyztile[2], xyztile[0], xyztile[1])
        filenamebase = '%s/%s/%s' % (path, name, shortname)
        filename = filenamebase + ".glb"

    else:
        #logger.info("No chunk size defined (area was given)")
        area_crop = area_ddd
        area_filter = area_ddd.buffer(chunk_size_extra_filter, join_style=ddd.JOIN_MITRE)
        radius = pipeline.data.get('ddd:osm:area:radius')

        shortname = '%s_%dr_%.3f,%.3f' % (name, radius if radius else 0, center[0], center[1])
        filenamebase = '%s/%s/%s' % (path, name, shortname)
        filename = filenamebase + ".glb"

    if area_ddd and not area_ddd.intersects(area_crop):
        logger.info("Skipping: %s (cropped area not contained in greater filtering area)", filename)
        #if os.path.exists(filename):
        #    logger.info("Deleting: %s", filename)
        #    os.unlink(filename)
        return

    pipeline.data['ddd:osm:area:crop'] = area_crop
    pipeline.data['ddd:osm:area:filter'] = area_filter
    pipeline.data['ddd:osm:output:shortname'] = shortname  # Canonical filename
    pipeline.data['ddd:osm:output:filename'] = filename  # Full path and canonical name and extension for default .glb file
    pipeline.data['ddd:osm:output:filenamebase'] = filenamebase  # Full path and canonical name with no extension or variants
    pipeline.data['filenamebase'] = filenamebase  # Legacy compatibility (instead of ddd:osm:output:filenamebase)


@dddtask()
def osm_bootstrap_skip_existing(root, pipeline, logger):
    filename = pipeline.data['ddd:osm:output:filename']
    if not D1D2D3Bootstrap._instance.overwrite and os.path.exists(filename):
        logger.warn("Skipping: %s (already exists)", filename)
        sys.exit(0)

@dddtask()
def osm_bootstrap_configure_logging(root, pipeline, logger):

    shortname = pipeline.data['ddd:osm:output:shortname']

    #old_formatters = {hdlr: hdlr.formatter for hdlr in logging.getLogger().handlers}

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

'''
@dddtask()
def osm_bootstrap_lock(root, pipeline, logger):

    shortname = pipeline.data['ddd:osm:output:shortname']
    filename = pipeline.data['ddd:osm:output:filename']

    lockfilename = filename + ".lock"
    logger.info("Trying to get lock file for: %s", lockfilename)

    # Try to lock
    try:
        #with open(lockfilename, "x") as _:
        open(lockfilename, "x")

    except FileExistsError as e:
        logger.info("Stopping execution: %s (lock file exists)", filename)
        pipeline.stop()
'''

@dddtask()
def osm_bootstrap_check_elevation(root, pipeline, logger):
    # Check elevation is available
    center_wgs84 = pipeline.data.get('ddd:osm:area:center')
    elevation = ElevationModel.instance()
    center_elevation = elevation.value(center_wgs84)
    logger.info("Center point elevation: %s", center_elevation)

@dddtask()
def osm_bootstrap_generate(root, pipeline, logger):

    shortname = pipeline.data['ddd:osm:output:shortname']
    filename = pipeline.data['ddd:osm:output:filename']
    filenamebase = pipeline.data['ddd:osm:output:filenamebase']
    area_ddd = pipeline.data.get('ddd:osm:area:ddd', None)
    osm_proj = pipeline.data['ddd:osm:proj:osm']
    ddd_proj = pipeline.data['ddd:osm:proj:ddd']
    area_shape = pipeline.data['ddd:osm:area:shape']
    center = pipeline.data.get('ddd:osm:area:center', None)
    radius = pipeline.data.get('ddd:osm:area:radius', None)
    area_crop = pipeline.data['ddd:osm:area:crop']
    area_filter = pipeline.data['ddd:osm:area:filter']

    logger.info("Generating: %s", filename)
    pipeline.name = "OSM Build Pipeline"

    pipeline.data['ddd:pipeline:start_date'] = datetime.datetime.now()

    pipeline.data['tile:bounds_wgs84'] = area_ddd.bounds
    pipeline.data['tile:bounds_m'] = area_crop.bounds


    # Fusion DDD data with pipeline data, so changes to the later affect the former
    # TODO: better way to do this without globals and merging data?
    D1D2D3.data.update(pipeline.data)
    D1D2D3.data = pipeline.data


    osmbuilder = osm.OSMBuilder(area_crop=area_crop, area_filter=area_filter, osm_proj=osm_proj, ddd_proj=ddd_proj)
    pipeline.data['osm'] = osmbuilder


'''
@dddtask(order="9999.99")
def osm_bootstrap_unlock(root, pipeline, logger):

    filename = pipeline.data['ddd:osm:output:filename']
    lockfilename = filename + ".lock"

    # Ensure lock file is removed
    try:
        os.unlink(lockfilename)
    except Exception as e:
        logger.warn("Could not delete pipeline lock: %s", lockfilename)

    #for hdlr in logging.getLogger().handlers:
    #    hdlr.setFormatter(old_formatters[hdlr])
'''
