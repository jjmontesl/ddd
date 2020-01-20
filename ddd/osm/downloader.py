# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

from collections import defaultdict, namedtuple
import logging
import math
import random
import sys

import geojson
import noise
import pyproj
from shapely import geometry
from shapely.geometry import shape
from shapely.geometry.geo import shape
from shapely.geometry.linestring import LineString
from shapely.ops import transform

import urllib.request
from urllib.error import HTTPError
import os


# Get instance of logger for this module
logger = logging.getLogger(__name__)

def download_block(bounds, name):

    osm_download_url = 'https://www.openstreetmap.org/api/0.6/map?bbox=%.5f%%2C%.5f%%2C%.5f%%2C%.5f'

    url = osm_download_url % (bounds[0], bounds[1], bounds[2], bounds[3])
    filename = "private/data/osm/" + "%s-%.3f,%.3f.osm" % (name, bounds[0], bounds[1])

    if os.path.exists(filename):
        logger.debug("Exists: %s (skipping)", filename)
        return

    logger.debug("Downloading: %s (%s)", filename, url)

    try:
        request = urllib.request.urlopen(url)
        with open(filename,'wb') as output:
            output.write(request.read())
    except HTTPError as e:
        #logger.error("Could not retrieve '%s': %s", url, e)
        raise

def download_area(bounds, chunk=0.01, name="osm"):
    logger.info("Downloading area: %s", bounds)
    posy = math.floor(bounds[1] / chunk) * chunk
    while posy < bounds[3]:
        posx = math.floor(bounds[0] / chunk) * chunk
        while posx < bounds[2]:
            download_block([posx, posy, posx + chunk, posy + chunk], name=name)
            posx += chunk
        posy += chunk

# Test
logging.basicConfig(level=logging.DEBUG)
vigo_wgs84 = [-8.723, 42.238]
salamanca_wgs84 = [-5.664100, 40.964999]

km = 0.01
center_wgs84 = salamanca_wgs84
size_km = 5
name = "salamanca"

download_area([center_wgs84[0] - size_km * km, center_wgs84[1] - size_km * km,
               center_wgs84[0] + size_km * km, center_wgs84[1] + size_km * km],
               name=name)

# Converted using:
# find /tmp -maxdepth 1 -name '*.osm' -exec sh -c './osmtogeojson {} > /tmp/$( basename {} ).geojson' \;
# find ~/git/ddd/private/data/oms/ -maxdepth 1 -name '*.osm' -exec sh -c './osmtogeojson {} > /tmp/$( basename {} ).geojson' \;

