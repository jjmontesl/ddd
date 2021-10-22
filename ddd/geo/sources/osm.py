# ddd - DDD123
# Library for simple scene modelling.
# Jose Juan Montes and Contributors 2019-2021
import logging
import os
import subprocess

from ddd.core import settings
from ddd.util.common import parse_bool
from abc import abstractmethod
import urllib
from urllib.error import HTTPError


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class OSMDataSource():
    """
    A source of features from OSM.
    """

    def __init__(self):
        pass

    @abstractmethod
    def get_data(self, datapath, dataname, center_wgs84):
        pass

    def convert_to_geojson(self, source_osm_file, datapath, dataname):
        """Converts OSM or PBF to GeoJSON using 'osm2geojson'."""
        # Run osmtogeojson
        outputgeojsonfile = os.path.join(datapath, "%s.osm.geojson" % dataname)
        osmtogeojson_path = os.path.expanduser(settings.OSMTOGEOJSON_PATH)
        logger.info("Converting to GeoJSON from %s to %s", source_osm_file, outputgeojsonfile)
        # TODO: Use temporary file
        with open(outputgeojsonfile, "w") as outfile:
            command = [osmtogeojson_path, "-m", source_osm_file]
            processresult = subprocess.run(command, stdout=outfile)


class OnlineOSMDataSource(OSMDataSource):

    def download_osm(self, bounds, filename, force_get_data=False):
        """
        Example URL: https://www.openstreetmap.org/api/0.6/map?bbox=12.99765%2C49.75022%2C13.00776%2C49.75531
        """

        osm_download_url = r'https://www.openstreetmap.org/api/0.6/map?bbox=%.5f,%.5f,%.5f,%.5f'

        url = osm_download_url % (bounds[0], bounds[1], bounds[2], bounds[3])
        #url = url.replace('-', r'%2D')
        #url = url.replace('-', r'%2D')
        #filename = "private/data/osm/" + "%s/%s-%.3f,%.3f.osm" % (name, name, bounds[0], bounds[1])

        force_get_data = force_get_data

        if os.path.exists(filename) and not force_get_data:
            logger.debug("Exists: %s (skipping)", filename)
            return

        logger.info("Downloading: %s (%s)", filename, url)

        try:
            request = urllib.request.urlopen(url)
            with open(filename,'wb') as output:
                output.write(request.read())
        except HTTPError as e:
            logger.error("Could not retrieve '%s': %s", url, e)
            raise

    def get_data(self, datapath, dataname, center_wgs84, force_get_data=False):
        """
        """
        #TODO: Use bounds if area is passed?

        selectedosmfile = os.path.join(datapath, "%s.osm" % dataname)

        #sides = 15 * 0.01  # Approximate degrees to km
        sides = 5 * 0.001  # Approximate degrees to km
        bounds = [center_wgs84[0] - sides, center_wgs84[1] - sides, center_wgs84[0] + sides, center_wgs84[1] + sides]
        #bounds = area.bounds()

        # Retrieve
        if not os.path.isfile(selectedosmfile) or force_get_data:
            logger.info("Retrieving data to %s (%s)", selectedosmfile, bounds)
            self.download_osm(bounds, selectedosmfile, force_get_data)

        self.convert_to_geojson(selectedosmfile, datapath, dataname)


class PBFOSMDataSource(OSMDataSource):

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

        self.convert_to_geojson(selectedpbffile, datapath, dataname)

