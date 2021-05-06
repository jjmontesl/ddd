# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

from collections import defaultdict, namedtuple
import logging
from shapely.geometry.geo import shape
from shapely.ops import transform
import sys

import geojson
import pyproj

from ddd.catalog.catalog import PrefabCatalog
from ddd.ddd import ddd
from ddd.osm.areaitems import AreaItemsOSMBuilder
from ddd.osm.areas_2d import Areas2DOSMBuilder
from ddd.osm.areas_3d import Areas3DOSMBuilder
from ddd.osm.buildings import BuildingOSMBuilder
from ddd.osm.custom import CustomsOSMBuilder
from ddd.osm.items import ItemsOSMBuilder
from ddd.osm.osmops.osmops import OSMBuilderOps
from ddd.osm.ways_1d import Ways1DOSMBuilder
from ddd.osm.ways_2d import Ways2DOSMBuilder
from ddd.osm.ways_3d import Ways3DOSMBuilder


# Get instance of logger for this module
logger = logging.getLogger(__name__)

WayConnection = namedtuple("WayConnection", "other self_idx other_idx")

def project_coordinates(coords, transformer):
    if isinstance(coords[0], float) or isinstance(coords[0], int):
        result = []
        for i in range(0, len(coords), 2):
            x, y = transformer.transform(coords[i], coords[i+1])
            result.extend([x, y])
        #c = _c(coords)
    elif isinstance(coords[0], list):
        result = [project_coordinates(c, transformer) for c in coords]
    else:
        raise AssertionError()

    return result


class OSMBuilder():

    def __init__(self, features=None, area_filter=None, area_crop=None, osm_proj=None, ddd_proj=None):

        self.catalog = PrefabCatalog()

        self.items = ItemsOSMBuilder(self)
        self.items2 = AreaItemsOSMBuilder(self)
        self.ways1 = Ways1DOSMBuilder(self)
        self.ways2 = Ways2DOSMBuilder(self)
        self.ways3 = Ways3DOSMBuilder(self)
        self.areas2 = Areas2DOSMBuilder(self)
        self.areas3 = Areas3DOSMBuilder(self)
        self.buildings = BuildingOSMBuilder(self)
        self.customs = CustomsOSMBuilder(self)

        self.osmops = OSMBuilderOps(self)

        self.area_filter = area_filter
        self.area_crop = area_crop

        self.area_filter2 = ddd.shape(self.area_filter)
        self.area_crop2 = ddd.shape(self.area_crop)

        #self.simplify_tolerance = 0.01

        self.layer_indexes = ('-2', '-1', '0', '1', '2', '3', '-2a', '-1a', '0a', '1a')

        self.layer_heights = {'-2': -12.0,
                              '-1': -6.0,
                              '0': 0.0,
                              '1': 6.0,
                              '2': 12.0,
                              '3': 18.0,
                              #'-2a': -9.0, '-1a': -2.5, '0a': 3.0, '1a': 9.0}
                              #'-2a': -12.0, '-1a': -5.0, '0a': 0.0, '1a': 6.0}
                              '-2a': 0.0, '-1a': 0.0, '0a': 0.0, '1a': 0.0}

        self.webmercator_proj = pyproj.Proj(init='epsg:3857')
        self.osm_proj = osm_proj  # 4326
        self.ddd_proj = ddd_proj

        self.features = features if features else []
        self.features_2d = ddd.group2(name="Features")


    def project_coordinates(self, obj, proj_from, proj_to, _transformer=None):
        """
        Note: Modifies coordinates in-place.
        """

        if _transformer is None:
            _transformer = pyproj.Transformer.from_proj(proj_from, proj_to)

        if obj.geom:
            obj.geom = transform(_transformer.transform, obj.geom)

        obj.children = [self.project_coordinates(c, proj_from, proj_to, _transformer) for c in obj.children]

        return obj


    def load_osmium(self, file):
        # See: Examples: https://github.com/osmcode/pyosmium/blob/master/examples/convert.py
        # See: https://osmcode.org/libosmium/manual.html (there's a GeoJSON factory, but possibly...)
        # Also in ddd example for osmium processing
        pass

    def load_geojson(self, files):

        features = []
        for f in files:
            fs = geojson.load(open(f, 'r'))
            features.extend(fs['features'])

        seen = set()
        dedup = []
        features_custom = []
        for f in features:
            #oid = hash(str(f))  # f['properties']['osm_id']

            # TODO: better way to distinguish custom features
            if 'id' not in f:
                features_custom.append(f)
                continue

            oid = f['id']
            if oid not in seen:
                seen.add(oid)
                dedup.append(f)

        logger.info("Loaded %d features (%d unique)" % (len(features), len(dedup)))
        features = dedup

        # Project to local
        # TODO: Do this with self.project coordinates after creating shapes (TEST!)
        transformer = pyproj.Transformer.from_proj(self.osm_proj, self.ddd_proj)
        for f in features:
            if not f['geometry']['coordinates']:
                logger.info("Feature with no coordinates: %s", f)
            else:
                try:
                    f['geometry']['coordinates'] = project_coordinates(f['geometry']['coordinates'], transformer)
                except Exception as e:
                    logger.error("Cannot project coordinates for: %s", f)

        # Filter "supertile"
        filtered = []
        for f in features:

            if not f['geometry']['coordinates']: continue

            try:
                geom = shape(f['geometry'])

            except Exception as e:
                logger.warn("Could not load feature with invalid geometry (%s): %s", str(f.properties)[:240], e)
                continue

            #geom = make_valid(geom)

            #if self.area_filter.contains(geom.centroid):
            try:
                if self.area_filter.intersects(geom):
                    filtered.append(f)
            except Exception as e:
                logger.debug("Could not load feature (1/2) with invalid geometry (%s): %s", str(f.properties)[:240], e)
                # Attempt intersection first
                try:
                    geom = geom.intersection(self.area_filter)
                    if self.area_filter.intersects(geom):
                        filtered.append(f)
                except Exception as e:
                    logger.warn("Could not load feature (2/2) with invalid geometry (%s): %s", f.properties, e)
                    continue


        features = filtered
        logger.info("Using %d features after filtering to %s" % (len(features), self.area_filter.bounds))

        self.features = features
        self.features_custom = features_custom

        #logger.debug("Custom features: %s", self.custom)

    def preprocess_features(self):
        """
        Corrects inconsistencies and adapts OSM data for generation.
        """

        # Correct layers
        for f in self.features:
            f.properties['id'] = f.properties['id'].replace("/", "-")
            if f.properties.get('tunnel', None) == 'yes' and f.properties.get('layer', None) is None:
                f.properties['layer'] = "-1"
            if f.properties.get('brige', None) == 'yes' and f.properties.get('layer', None) is None:
                f.properties['layer'] = "1"
            if f.properties.get('layer', None) is None:
                f.properties['layer'] = "0"

            # Create feature objects
            defaultname = f.geometry.type  # "Feature"
            name = f.properties.get('name', defaultname)
            osmid = f.properties.get('id', None)
            if osmid is not None:
                name = "%s_(%s)" % (name, osmid)

            feature_2d = ddd.shape(f.geometry, name=name)
            feature_2d.extra['osm:feature'] = f
            feature_2d.extra['osm:feature_2d'] = feature_2d
            feature_2d.extra['osm:element'] = f.properties['id'].split("-")[0]
            for k, v in f.properties.items():
                feature_2d.extra['osm:' + k] = v

            # We do not validate or clean here as linestrings may crose themselves. Simply remove empty geometries.

            # Crop to area filter
            try:
                feature_2d.validate()
            except Exception as e:
                logger.debug("Invalid feature (1/2 - fixing) '%s': %s", name, e)
                try:
                    #feature_2d = feature_2d.intersection(self.area_filter2)
                    feature_2d = feature_2d.clean(fix_invalid=True)
                    feature_2d.counter('dddosm:feature:fixed')
                    feature_2d.validate()
                except Exception as e:
                    logger.warn("Invalid feature (2/2) '%s' %s: %s", name, feature_2d.metadata("", ""), e)
                    continue

            if feature_2d.geom is None:
                logger.warn("Invalid feature (no geom or geom removed): '%s' %s", name, feature_2d.metadata("", ""))
                continue

            # Separate GeometryCollection geometries
            if feature_2d.geom.type == "GeometryCollection":
                logger.info("Splitting GeometryCollection: %s", feature_2d)
                for f in feature_2d.individualize().children:
                    f.extra['osm:feature_2d'] = f
                    f = f.intersection(self.area_filter2)
                    #f = f.clean(eps=0.0)
                    f.validate()
                    self.features_2d.append(f)
            else:
                self.features_2d.append(feature_2d)


        #self.features_2d.save("/tmp/dddosm2d.json")

        # Coastlines?
        #for f in self.features_2d.children:
        #    if f.extra.get('osm:tourism', None) != None:
        #        print(f)
        #sys.exit(1)

