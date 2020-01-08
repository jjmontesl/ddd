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


# Get instance of logger for this module
logger = logging.getLogger(__name__)

def download_block(bounds):

    osm_download_url = 'https://www.openstreetmap.org/api/0.6/map?bbox=%.5f%%2C%.5f%%2C%.5f%%2C%.5f'

    url = osm_download_url % (bounds[0], bounds[1], bounds[2], bounds[3])
    filename = "/tmp/" + "osm-%.3f,%.3f.osm" % (bounds[0], bounds[1])
    logger.debug("Downloading: %s", url)
     
    try:
        request = urllib.request.urlopen(url)
        with open(filename,'wb') as output:
            output.write(request.read())
    except HTTPError as e:
        #logger.error("Could not retrieve '%s': %s", url, e)
        raise

def download_area(bounds, chunk=0.02):
    logger.info("Downloading area: %s", bounds)
    posy = math.floor(bounds[1] / chunk) * chunk
    while posy < bounds[3]:
        posx = math.floor(bounds[0] / chunk) * chunk
        while posx < bounds[2]:
            download_block([posx, posy, posx + chunk, posy + chunk])
            posx += chunk
        posy += chunk

# Test
logging.basicConfig(level=logging.DEBUG)
vigo_wgs84 = [-8.723, 42.238]
km = 0.01
download_area([vigo_wgs84[0] - 15 * km, vigo_wgs84[1] - 15 * km, 
               vigo_wgs84[0] + 15 * km, vigo_wgs84[1] + 15 * km])

# Converted using:
# find /tmp -maxdepth 1 -name '*.osm' -exec sh -c './osmtogeojson {} > /tmp/$( basename {} ).geojson' \;
    
    