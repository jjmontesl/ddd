# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging
import math
import random

from ddd.ddd import ddd
from ddd.pack.sketchy import plants, urban, landscape
from ddd.geo import terrain
import sys


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class ItemsOSMBuilder():

    def __init__(self, osmbuilder):
        self.osm = osmbuilder

        #logger.info("Generating item pools")
        self.pool = {}
        #self.pool['tree'] = [self.generate_item_3d_tree(ddd.point([0, 0, 0])) for i in range(8)]

        self.tree_decimate = 1
        self.tree_decimate_idx = 0

    def generate_items_1d(self):
        logger.info("Generating 1D items")

        for feature in self.osm.features:

            if feature['geometry']['type'] == 'Point':
                item = self.generate_item_1d(feature)
                if item:
                    #logger.debug("Item: %s", item)
                    self.osm.items_1d.children.append(item)
            else:
                #logger.warn("Unknown item geometry type: %s", feature['geometry']['type'])
                pass

    def generate_item_1d(self, feature):
        item = ddd.shape(feature['geometry'], name="Item: %s" % feature['properties'].get('name', feature['properties'].get('id', None)))
        item.extra['osm:feature'] = feature
        item.extra['name'] = feature['properties'].get('name', None)
        item.extra['amenity'] = feature['properties'].get('amenity', None)
        item.extra['barrier'] = feature['properties'].get('barrier', None)
        item.extra['natural'] = feature['properties'].get('natural', None)
        item.extra['tourism'] = feature['properties'].get('tourism', None)
        item.extra['highway'] = feature['properties'].get('highway', None)
        item.extra['historic'] = feature['properties'].get('historic', None)
        item.extra['artwork_type'] = feature['properties'].get('artwork_type', None)
        item.extra['man_made'] = feature['properties'].get('man_made', None)
        item.extra['power'] = feature['properties'].get('power', None)
        item.extra['traffic_sign'] = feature['properties'].get('traffic_sign', None)
        return item

    def generate_items_3d(self):
        logger.info("Generating 3D items (from %d items_1d)", len(self.osm.items_1d.children))

        for item_2d in self.osm.items_1d.children:
            #if item_2d.geom.empty: continue
            item_3d = self.generate_item_3d(item_2d)
            if item_3d:
                item_3d.name = item_3d.name if item_3d.name else item_2d.name
                logger.debug("Generated item: %s", item_3d)
                self.osm.items_3d.children.append(item_3d)

        # FIXME: Do not alter every vertex, move the entire object instead
        #self.osm.items_3d = terrain.terrain_geotiff_elevation_apply(self.osm.items_3d, self.osm.ddd_proj)
        #self.osm.items_3d = self.osm.items_3d.translate([0, 0, -0.20])  # temporary fix snapping

    def generate_item_3d(self, item_2d):

        #if 'osm:feature' in item_2d.extra:
        #    if ("Julio Verne" in item_2d.extra['osm:feature']['properties'].get('name', "")):
        #        print(item_2d)

        item_3d = None
        if item_2d.extra.get('amenity', None) == 'fountain':
            item_3d = self.generate_item_3d_fountain(item_2d)
        elif item_2d.extra.get('amenity', None) == 'bench':
            item_3d = self.generate_item_3d_bench(item_2d)
        elif item_2d.extra.get('amenity', None) == 'post_box':
            item_3d = self.generate_item_3d_post_box(item_2d)
        #elif item_2d.extra.get('amenity', None) == 'taxi':
        #    item_3d = self.generate_item_3d_taxi(item_2d)
        #elif item_2d.extra.get('amenity', None) == 'toilets':
        #    item_3d = self.generate_item_3d_taxi(item_2d)
        elif item_2d.extra.get('amenity', None) == 'waste_basket':
            item_3d = self.generate_item_3d_waste_basket(item_2d)
        #elif item_2d.extra.get('amenity', None) == 'waste_disposal':
        #    item_3d = self.generate_item_3d_waste_disposal(item_2d)
        #elif item_2d.extra.get('amenity', None) == 'recycling':
        #    item_3d = self.generate_item_3d_waste_disposal(item_2d)
        #elif item_2d.extra.get('amenity', None) == 'bicycle_parking':
        #    item_3d = self.generate_item_3d_waste_disposal(item_2d)

        elif item_2d.extra.get('natural', None) == 'tree':
            self.tree_decimate_idx += 1
            if self.tree_decimate <= 1 or self.tree_decimate_idx % self.tree_decimate == 0:
                #item_3d = random.choice(self.pool['tree']).instance()
                #coords = item_2d.geom.coords[0]
                #item_3d = item_3d.translate([coords[0], coords[1], 0.0])

                item_3d = self.generate_item_3d_tree(item_2d)

        elif item_2d.extra.get('tourism', None) == 'artwork' and item_2d.extra.get('artwork_type', None) == 'sculpture':
            item_3d = self.generate_item_3d_sculpture(item_2d)
        elif item_2d.extra.get('historic', None) == 'monument':  # Large monument
            item_3d = self.generate_item_3d_monument(item_2d)
        elif item_2d.extra.get('historic', None) == 'memorial':
            item_3d = self.generate_item_3d_monument(item_2d)
        elif item_2d.extra.get('historic', None) == 'wayside_cross':
            item_3d = self.generate_item_3d_wayside_cross(item_2d)
        elif item_2d.extra.get('man_made', None) == 'lighthouse':
            item_3d = self.generate_item_3d_lighthouse(item_2d)

        elif item_2d.extra.get('highway', None) == 'bus_stop':
            item_3d = self.generate_item_3d_bus_stop(item_2d)

        elif item_2d.extra.get('power', None) == 'tower':
            item_3d = self.generate_item_3d_powertower(item_2d)
        elif item_2d.extra.get('power', None) == 'pole':
            item_3d = self.generate_item_3d_powerpole(item_2d)

        elif item_2d.extra.get('barrier', None) == 'fence':
            item_3d = self.generate_item_3d_fence(item_2d)
        elif item_2d.extra.get('barrier', None) == 'hedge':
            item_3d = self.generate_item_3d_hedge(item_2d)

        elif item_2d.extra.get('ddd_osm', None) == 'way_lamppost':
            item_3d = self.generate_item_3d_lamppost(item_2d)
        elif item_2d.extra.get('ddd_osm', None) == 'way_trafficlights':
            item_3d = self.generate_item_3d_trafficlights(item_2d)

        elif item_2d.extra.get('traffic_sign', None) is not None:
            item_3d = self.generate_item_3d_traffic_sign(item_2d)

        else:
            logger.debug("Unknown item: %s", item_2d.extra)

        # FIXME: This shuld not be done here, but by each element (some are snapped at their center, some min_vertex...)
        if item_3d:
            height_mapping = item_3d.extra.get('_height_mapping', 'terrain_geotiff_min_elevation_apply')
            if height_mapping == 'terrain_geotiff_elevation_apply':
                item_3d = terrain.terrain_geotiff_elevation_apply(item_3d, self.osm.ddd_proj)
            elif height_mapping == 'terrain_geotiff_incline_elevation_apply':
                item_3d = terrain.terrain_geotiff_min_elevation_apply(item_3d, self.osm.ddd_proj)
            elif height_mapping == 'terrain_geotiff_and_path_apply':
                path = item_3d.extra['way_1d']
                vertex_func = self.osm.ways.get_height_apply_func(path)
                item_3d = item_3d.vertex_func(vertex_func)
                item_3d = terrain.terrain_geotiff_min_elevation_apply(item_3d, self.osm.ddd_proj)
            else:
                item_3d = terrain.terrain_geotiff_min_elevation_apply(item_3d, self.osm.ddd_proj)

            #if ("Julio Verne" in item_3d.name):
            #    print(item_3d.show())

        return item_3d

    def generate_item_3d_tree(self, item_2d):

        coords = item_2d.geom.coords[0]

        #invalid = ddd.group([self.osm.ways_2d["0"], self.osm.buildings_2d])
        #if not self.osm.osmops.placement_valid(ddd.disc(coords, r=0.4), invalid=invalid):
        #    return None

        key = "tree-default-%d" % (random.choice([1, 2, 3, 4, 5, 6, 7, 8]))
        item_3d = self.osm.catalog.instance(key)
        if not item_3d:
            plant_height = random.normalvariate(8.0, 3.0)
            if plant_height < 3.0: plant_height=random.uniform(3.0, 5.5)
            if plant_height > 15.0: plant_height=random.uniform(12.0, 15.0)
            item_3d = plants.plant(height=plant_height)
            for i in item_3d.filter(lambda o: o.extra.get('foliage', None)).children:
                i.extra['ddd:collider'] = False  # TODO: generation details shall be optional
            item_3d = self.osm.catalog.add(key, item_3d)

        item_3d = item_3d.rotate([0.0, 0.0, random.uniform(0, math.pi * 2)])
        item_3d = item_3d.translate([coords[0], coords[1], 0.0])
        item_3d.name = 'Tree: %s' % item_2d.name
        return item_3d

    def generate_item_3d_fountain(self, item_2d):
        # Todo: Use fountain shape if available, instead of centroid

        key = "fountain-default-1"
        item_3d = self.osm.catalog.instance(key)
        if not item_3d:
            item_3d = urban.fountain(r=1.85)
            item_3d = self.osm.catalog.add(key, item_3d)

        coords = item_2d.geom.coords[0]
        item_3d = item_3d.translate([coords[0], coords[1], 0.0])
        item_3d.name = 'Fountain: %s' % item_2d.name
        return item_3d

    def generate_item_3d_bench(self, item_2d):
        key = "bench-default-1"
        item_3d = self.osm.catalog.instance(key)

        if not item_3d:
            item_3d = urban.bench(length=2.0)
            item_3d = self.osm.catalog.add(key, item_3d)

        coords = item_2d.geom.coords[0]
        oriented_point = ddd.snap.project(ddd.point(coords), self.osm.ways_2d['0'])
        item_3d = item_3d.rotate([0, 0, oriented_point.extra['ddd:angle'] - math.pi / 2])
        item_3d = item_3d.translate([coords[0], coords[1], 0.0])
        item_3d.name = 'Bench: %s' % item_2d.name
        item_3d.extra['_height_mapping'] = 'terrain_geotiff_incline_elevation_apply'
        return item_3d

    def generate_item_3d_post_box(self, item_2d):

        logger.warn("TODO: move items outside buldings and consider ground too (possibly making ground an area")
        #item_2d = ddd.snap.project(item_2d, self.osm.areas_2d, penetrate=0.5)
        item_2d = ddd.snap.project(item_2d, self.osm.ways_2d["0"], penetrate=-1)

        coords = item_2d.geom.coords[0]
        item_3d = urban.post_box().translate([coords[0], coords[1], 0.0])
        operator = item_2d.extra['osm:feature'].get('operator')
        item_3d.name = 'Postbox (%s): %s' % (operator, item_2d.name)
        return item_3d

    def generate_item_3d_waste_basket(self, item_2d):
        coords = item_2d.geom.coords[0]
        invalid = ddd.group([self.osm.ways_2d["0"], self.osm.buildings_2d]).clean(eps=0.01)

        item_2d = ddd.snap.project(item_2d, self.osm.ways_2d["0"], penetrate=-1)
        if not self.osm.osmops.placement_valid(item_2d.buffer(0.2), invalid=invalid): return None

        itemtype = "waste-basket" if random.uniform(0, 1) < 0.5 else "waste-basket-post"

        key = "%s-default-1" % itemtype
        item_3d = self.osm.catalog.instance(key)
        if not item_3d:
            if itemtype == "waste-basket":
                item_3d = urban.trash_bin()
            else:
                item_3d = urban.trash_bin_post()
            item_3d = self.osm.catalog.add(key, item_3d)

        item_3d = item_3d.rotate([0, 0, item_2d.extra['ddd:angle'] - math.pi / 2])
        item_3d = item_3d.translate([coords[0], coords[1], 0.0])
        item_3d.name = 'Waste bin (%s): %s' % (itemtype, item_2d.name)
        return item_3d

    def generate_item_3d_taxi(self, item_2d):
        #item_2d = ddd.snap.project(item_2d, self.osm.areas_2d, penetrate=0.5)
        item_2d = ddd.snap.project(item_2d, self.osm.ways_2d["0"], penetrate=-1)
        coords = item_2d.geom.coords[0]
        item_3d = urban.trafficsign_sign_rect(signtype="info", icon="i", text="TAXI").translate([coords[0], coords[1], 0.0])
        item_3d.name = 'Taxi Stop: %s' % (item_2d.name)
        return item_3d

    def generate_item_3d_sculpture(self, item_2d):
        # Todo: Use fountain shape if available, instead of centroid
        coords = item_2d.geom.coords[0]
        oriented_point = ddd.snap.project(ddd.point(coords), self.osm.ways_2d['0'])
        item_3d = urban.sculpture(1.5)
        item_3d = item_3d.rotate([0, 0, oriented_point.extra['ddd:angle'] - math.pi / 2])
        item_3d = item_3d.translate([coords[0], coords[1], 0.0]).material(ddd.mats.steel)  # mat_bronze
        item_3d.name = 'Sculpture: %s' % item_2d.name
        return item_3d

    def generate_item_3d_monument(self, item_2d):
        # Todo: Use fountain shape if available, instead of centroid
        coords = item_2d.geom.coords[0]
        oriented_point = ddd.snap.project(ddd.point(coords), self.osm.ways_2d['0'])
        item_name = item_2d.extra['osm:feature']['properties'].get('name', None)
        if item_name:
            item_3d = urban.sculpture_text(item_name[:1], 2.0, 5.0)
        else:
            item_3d = urban.sculpture(2.0, 5.0)
        item_3d = item_3d.rotate([0, 0, oriented_point.extra['ddd:angle'] - math.pi / 2])
        item_3d = item_3d.translate([coords[0], coords[1], 0.0]).material(ddd.mats.bronze)
        item_3d.name = 'Monument: %s' % item_2d.name
        return item_3d

    def generate_item_3d_wayside_cross(self, item_2d):
        coords = item_2d.geom.coords[0]
        oriented_point = ddd.snap.project(ddd.point(coords), self.osm.ways_2d['0'])
        item_3d = urban.wayside_cross()
        item_3d = item_3d.rotate([0, 0, oriented_point.extra['ddd:angle'] - math.pi / 2])
        item_3d = item_3d.translate([coords[0], coords[1], 0.0]).material(ddd.mats.stone)  # mat_bronze
        item_3d.name = 'Wayside Cross: %s' % item_2d.name
        return item_3d

    def generate_item_3d_lighthouse(self, item_2d):
        coords = item_2d.geom.coords[0]
        item_3d = landscape.lighthouse().translate([coords[0], coords[1], 0.0])
        item_3d.name = 'Lighthouse: %s' % item_2d.name
        return item_3d

    def generate_item_3d_bus_stop(self, item_2d):
        busways = self.osm.ways_2d["0"].flatten().filter(lambda i: i.extra.get('highway', None) not in ('path', 'track', 'footway', None))
        item_2d = ddd.snap.project(item_2d, busways, penetrate=-0.5)
        coords = item_2d.geom.coords[0]
        text = item_2d.extra.get("name", None)
        item_3d = urban.busstop_small(text=text)
        item_3d = item_3d.rotate([0, 0, item_2d.extra['ddd:angle'] - math.pi])
        item_3d = item_3d.translate([coords[0], coords[1], 0.0])
        item_3d.name = 'Bus Stop: %s' % item_2d.name
        return item_3d

    def generate_item_3d_powertower(self, item_2d):
        # TODO: Unify powertower, post, and maybe other joins, add catenaries using power:line
        # and orient poles
        coords = item_2d.geom.coords[0]
        item_3d = landscape.powertower(18)
        item_3d = item_3d.translate([coords[0], coords[1], 0.0])
        item_3d.name = 'Power Tower: %s' % item_2d.name
        return item_3d

    def generate_item_3d_powerpole(self, item_2d):
        coords = item_2d.geom.coords[0]
        item_3d = landscape.powertower(18)
        item_3d = item_3d.translate([coords[0], coords[1], 0.0])
        item_3d.name = 'Power Pole: %s' % item_2d.name
        return item_3d

    def generate_item_3d_fence(self, item_2d):
        """
        Expects a line.
        """
        height = item_2d.extra['ddd:item:height']
        item_3d = item_2d.extrude(height)
        item_3d = ddd.uv.map_cubic(item_3d)

        if True:
            topbar = item_2d.buffer(0.1).extrude(0.1).material(ddd.mats.bronze)
            topbar = topbar.translate([0, 0, height])
            topbar = ddd.uv.map_cubic(topbar)
            item_3d = item_3d.append(topbar)

        item_3d.extra['_height_mapping'] = item_3d.extra.get('_height_mapping', 'terrain_geotiff_elevation_apply')
        item_3d.name = 'Fence: %s' % item_2d.name

        return item_3d

    def generate_item_3d_hedge(self, item_2d):
        """
        Expects a line.
        """
        height = item_2d.extra['ddd:item:height']
        width = item_2d.extra['ddd:width']
        profile = item_2d.buffer(width - 0.2)
        item_3d = profile.extrude_step(profile.buffer(0.2), 0.4)
        item_3d = item_3d.extrude_step(profile.buffer(0.2), height - 0.6)
        item_3d = item_3d.extrude_step(profile, 0.2)
        item_3d = ddd.uv.map_cubic(item_3d)
        item_3d.extra['_height_mapping'] = 'terrain_geotiff_elevation_apply'
        item_3d.name = 'Hedge: %s' % item_2d.name
        return item_3d

    def generate_item_3d_lamppost(self, item_2d):

        coords = item_2d.geom.coords[0]

        # Check if item can be placed
        invalid = ddd.group([self.osm.ways_2d["0"], self.osm.buildings_2d]).clean(eps=0.01)
        if not self.osm.osmops.placement_valid(ddd.disc(coords, r=0.2, resolution=0, name=item_2d.name), invalid=invalid):
            return None

        key = "lamppost-default-1"
        item_3d = self.osm.catalog.instance(key)
        if not item_3d:
            item_3d = urban.lamppost(height=5.5, r=0.35)
            item_3d = self.osm.catalog.add(key, item_3d)

        item_3d = item_3d.translate([coords[0], coords[1], 0.0])
        item_3d.name = 'Lamppost: %s' % item_2d.name
        return item_3d

    def generate_item_3d_trafficlights(self, item_2d):

        key = "trafficlights-default-1"
        item_3d = self.osm.catalog.instance(key)
        if not item_3d:
            item_3d = urban.trafficlights()
            item_3d = self.osm.catalog.add(key, item_3d)

        coords = item_2d.geom.coords[0]
        item_3d = item_3d.rotate([0, 0, item_2d.extra['ddd:angle'] - math.pi / 2])
        item_3d = item_3d.translate([coords[0], coords[1], 0.0])
        item_3d.extra['_height_mapping'] = 'terrain_geotiff_min_elevation_apply'
        return item_3d

    def generate_item_3d_traffic_sign(self, item_2d):

        signtype = item_2d.extra['traffic_sign']

        key = "traffic_sign-%s-1" % (signtype)
        item_3d = self.osm.catalog.instance(key)
        if not item_3d:
            item_3d = urban.traffic_sign(signtype)
            item_3d = self.osm.catalog.add(key, item_3d)

        coords = item_2d.geom.coords[0]
        item_3d = item_3d.rotate([0, 0, item_2d.extra['ddd:angle'] - math.pi / 2])
        item_3d = item_3d.translate([coords[0], coords[1], 0.0])
        item_3d.extra['_height_mapping'] = 'terrain_geotiff_incline_elevation_apply'
        return item_3d


