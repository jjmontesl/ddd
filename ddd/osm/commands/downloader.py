# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

from collections import defaultdict, namedtuple
import logging
import math
import os
import random
import sys
from urllib.error import HTTPError
import urllib.request

import geojson
import noise
import pyproj
from shapely import geometry
from shapely.geometry import shape
from shapely.geometry.geo import shape
from shapely.geometry.linestring import LineString
from shapely.ops import transform
from ddd.util.common import parse_bool
from ddd.core.cli import D1D2D3Bootstrap


# Get instance of logger for this module
logger = logging.getLogger(__name__)


'''
def download_area(bounds, chunk=0.01, filename=None):
    logger.info("Downloading area: %s", bounds)
    posy = math.floor(bounds[1] / chunk) * chunk
    while posy < bounds[3]:
        posx = math.floor(bounds[0] / chunk) * chunk
        while posx < bounds[2]:
            download_block([posx, posy, posx + chunk, posy + chunk], filename=filename)
            posx += chunk
        posy += chunk
'''


'''
# Test
logging.basicConfig(level=logging.DEBUG)
vigo_wgs84 = [-8.723, 42.238]
salamanca_wgs84 = [-5.664100, 40.964999]

km = 0.01
center_wgs84 = salamanca_wgs84
size_km = 20
name = "salamanca"

download_area([center_wgs84[0] - size_km * km, center_wgs84[1] - size_km * km,
               center_wgs84[0] + size_km * km, center_wgs84[1] + size_km * km],
               name=name)
'''


# Using PBFs:
#   osmconvert spain-latest.osm.pbf -b=-5.870,40.760,-5.470,41.160 -o=salamanca-latest.osm.pbf
#   osmconvert spain-latest.osm.pbf -b=-8.980,41.980,-8.480,42.480 -o=vigo-latest.osm.pbf
# Then, geojson:
#   ./osmtogeojson city-latest.osm.pbf > /tmp/city.geojson


# OBSOLETE:
# Converted using:
#   find /tmp -maxdepth 1 -name '*.osm' -exec sh -c './osmtogeojson {} > /tmp/$( basename {} ).geojson' \;
#   find ~/git/ddd/private/data/oms/salamanca -maxdepth 1 -name '*.osm' -exec sh -c './osmtogeojson {} > /tmp/$( basename {} ).geojson' \;
# Merged using osmium:
# The first file needs to be copied to res.osm first.
# If the process breaks, the file res2.osm above needs to be deleted.
#   for a in *.osm ; do osmium merge res.osm $a --overwrite -o res2.osm ; cp res2.osm res.osm ; done
