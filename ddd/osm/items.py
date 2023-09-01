# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging
import math
import random

import numpy as np

from ddd.ddd import ddd
from ddd.pack.sketchy import plants, sports_fields, urban, landscape, industrial, common
from ddd.geo import terrain
import sys
from ddd.pack.sketchy.urban import patio_table
from collections import defaultdict
from ddd.core.exception import DDDException
from ddd.pack.symbols import iconitems
from ddd.ops import filters
from ddd.geo.terrain import terrain_geotiff_elevation_value


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

    def item_names_all(self, item):
        result = []
        for k, v in item.extra.items():
            if k == "osm:name" or k.startswith('osm:name:'):
                result.append(v)
        return (result if result else None)


    def generate_item_3d(self, item_2d):

        # TODO! Move to pipeline or at least call from pipeline

        #if 'osm:feature' in item_2d.extra:
        #    if ("Julio Verne" in item_2d.extra['osm:feature']['properties'].get('name', "")):
        #        print(item_2d)

        item_3d = None


        if item_2d.extra.get('osm:amenity', None) == 'fountain':
            item_3d = self.generate_item_3d_fountain(item_2d)
        elif item_2d.extra.get('osm:amenity', None) == 'bench':  # not to be confused with seat
            item_3d = self.generate_item_3d_bench(item_2d)
        elif item_2d.extra.get('osm:amenity', None) == 'drinking_water':
            item_3d = self.generate_item_3d_generic(item_2d, urban.drinking_water, "Drinking water")
        elif item_2d.extra.get('osm:amenity', None) == 'post_box':
            #item_3d = self.generate_item_3d_post_box(item_2d)
            operator = item_2d.extra['osm:feature'].get('operator', None)
            item_3d = self.generate_item_3d_generic_catalog("post_box-default-1", item_2d, urban.post_box, "Postbox")
            item_3d.name = 'Postbox (%s): %s' % (operator, item_2d.name)

        elif item_2d.extra.get('osm:amenity', None) == 'table':
            item_3d = self.generate_item_3d_generic(item_2d, urban.patio_table, "Table")
        elif item_2d.extra.get('osm:amenity', None) == 'seat':  # not to be confused with bench
            item_3d = self.generate_item_3d_generic(item_2d, urban.patio_chair, "Seat")
        elif item_2d.extra.get('osmext:amenity', None) == 'umbrella':
            item_3d = self.generate_item_3d_generic(item_2d, urban.patio_umbrella, "Umbrella")
        #elif item_2d.extra.get('osm:amenity', None) == 'taxi':
        #    item_3d = self.generate_item_3d_taxi(item_2d)
        #elif item_2d.extra.get('osm:amenity', None) == 'toilets':
        #    item_3d = self.generate_item_3d_taxi(item_2d)
        elif item_2d.extra.get('osm:amenity', None) == 'waste_basket':
            item_3d = self.generate_item_3d_waste_basket(item_2d)

        elif item_2d.extra.get('osm:amenity', None) == 'waste_disposal':
            if random.choice([1, 2]) == 1:
                item_3d = self.generate_item_3d_generic_catalog("waste-disposal-1", item_2d, urban.waste_container, "Waste Disposal")
            else:
                item_3d = self.generate_item_3d_generic_catalog("waste-disposal-closed-1", item_2d, urban.waste_container_with_lid_closed, "Waste Disposal (C)")
        elif item_2d.extra.get('osm:amenity', None) == 'recycling':
            item_3d = self.generate_item_3d_generic_catalog("waste-container-dome-1", item_2d, urban.waste_container_dome, "Recycling")

        elif item_2d.extra.get('osm:amenity', None) == 'bicycle_parking':
            #item_3d = self.generate_item_3d_waste_disposal(item_2d)
            item_2d.set('ddd:angle', item_2d.get('ddd:angle') + math.pi / 2)
            item_3d = self.generate_item_3d_generic_catalog("bicycle-parking-bar-u", item_2d, common.bar_u, "Bicycle Parking Bar U")

        elif item_2d.extra.get('osm:emergency', None) == 'fire_hydrant':
            item_3d = self.generate_item_3d_generic_catalog("fire_hydrant-default-1", item_2d, urban.fire_hydrant, "Fire Hydrant")

        elif item_2d.extra.get('osm:natural', None) == 'tree':
            # TODO: Do decimations in the pipeline (if at all)
            self.tree_decimate_idx += 1
            if self.tree_decimate <= 1 or self.tree_decimate_idx % self.tree_decimate == 0:
                #item_3d = random.choice(self.pool['tree']).instance()
                #coords = item_2d.geom.coords[0]
                #item_3d = item_3d.translate([coords[0], coords[1], 0.0])
                item_3d = self.generate_item_3d_tree(item_2d)

        elif item_2d.extra.get('osm:natural', None) == 'rock' or item_2d.extra.get('ddd:item', None) == 'natural_rock':
            # TODO: Use a generic metadata-based catalog/instnacing key and arguments (and grouping by arguments for instancing)
            bounds = [random.uniform(2, 4), random.uniform(1, 3), random.uniform(1, 2)]
            variant = random.choice(range(4)) + 1
            item_3d = self.generate_item_3d_generic_catalog("natural-rock-%d" % variant, item_2d, lambda: landscape.rock(bounds), "Rock")
            item_3d = item_3d.translate([0, 0, random.uniform(-0.5, 0.0)])
        elif item_2d.extra.get('osm:natural', None) == 'stone':
            #item_3d = self.generate_item_3d_generic_catalog("natural-stone-1", item_2d, lambda: landscape.rock([4, 4.5, 4.0]), "Stone")
            item_3d = self.generate_item_3d_generic(item_2d, lambda: landscape.rock([4, 4.5, 4.0]), "Stone")
            item_3d = item_3d.translate([0, 0, -random.uniform(0.0, 1.0)])

        elif item_2d.extra.get('osm:tourism', None) == 'artwork' and item_2d.extra.get('osm:artwork_type', None) == 'sculpture':
            item_3d = self.generate_item_3d_sculpture(item_2d)
        elif item_2d.extra.get('osm:tourism', None) == 'artwork' and item_2d.extra.get('osm:artwork_type', None) == 'statue':
            item_3d = self.generate_item_3d_sculpture(item_2d)
        elif item_2d.extra.get('osm:tourism', None) == 'artwork' and item_2d.extra.get('osm:artwork_type', None) == None:
            item_3d = self.generate_item_3d_sculpture(item_2d)
        elif item_2d.extra.get('osm:historic', None) == 'monument':  # Large monument
            item_3d = self.generate_item_3d_monument(item_2d)
        elif item_2d.extra.get('osm:historic', None) == 'memorial':
            item_3d = self.generate_item_3d_monument(item_2d)
        elif item_2d.extra.get('osm:historic', None) == 'wayside_cross':
            item_3d = self.generate_item_3d_wayside_cross(item_2d)
        elif item_2d.extra.get('osm:historic', None) == 'archaeological_site':
            item_3d = self.generate_item_3d_historic_archaeological_site(item_2d)

        elif item_2d.extra.get('osm:man_made', None) == 'crane':
            item_3d = self.generate_item_3d_crane(item_2d)
        elif item_2d.extra.get('osm:man_made', None) == 'lighthouse':
            item_3d = self.generate_item_3d_lighthouse(item_2d)
        elif item_2d.extra.get('osm:man_made', None) == 'tower' and item_2d.extra.get('osm:tower:type', None) == 'communication':
            item_3d = self.generate_item_3d_man_made_tower_communication(item_2d)

        elif item_2d.extra.get('osm:highway', None) == 'bus_stop':
            item_3d = self.generate_item_3d_bus_stop(item_2d)

        elif item_2d.extra.get('osm:power', None) == 'tower':
            item_3d = self.generate_item_3d_powertower(item_2d)
        elif item_2d.extra.get('osm:power', None) == 'pole':
            item_3d = self.generate_item_3d_powerpole(item_2d)
        elif item_2d.extra.get('osm:power', None) == 'catenary_mast':
            logger.warn("Using temporary object: powerpole (for catenary_mast)")
            item_3d = self.generate_item_3d_powerpole(item_2d)

        elif item_2d.extra.get('osm:barrier', None) == 'fence':
            item_3d = self.generate_item_3d_fence(item_2d)
        elif item_2d.extra.get('osm:barrier', None) == 'hedge':
            item_3d = self.generate_item_3d_hedge(item_2d)
        elif item_2d.extra.get('osm:barrier', None) == 'bollard':
            item_3d = self.generate_item_3d_generic(item_2d, urban.bollard, "Bollard")

        #elif item_2d.extra.get('osm:leisure', None) == 'playground':

        elif item_2d.extra.get('osm:playground', None) == 'swing':
            item_3d = self.generate_item_3d_generic(item_2d, urban.childrens_playground_swingset, "Playground Swings")
        elif item_2d.extra.get('osm:playground', None) == 'sandbox':
            item_3d = self.generate_item_3d_generic(item_2d, urban.childrens_playground_sandbox, "Playground Sandbox")
        elif item_2d.extra.get('osm:playground', None) == 'slide':
            item_3d = self.generate_item_3d_generic(item_2d, urban.childrens_playground_slide, "Playground Slide")
        elif item_2d.extra.get('osm:playground', None) == 'monkey_bar':
            item_3d = self.generate_item_3d_generic(item_2d, urban.childrens_playground_arc, "Playground Monkey Bar Arc")

        elif item_2d.extra.get('osm:power', None) in ('line', 'minor_line'):
            # TODO: Tilt objects using a generic tilting mechanism (also, this one may be also based on terrain gradient)
            item_3d = self.generate_item_3d_powerline(item_2d)

        elif item_2d.extra.get('osm:golf', None) == 'hole':
            # TODO: Tilt objects using a generic tilting mechanism (also, this one may be also based on terrain gradient)
            item_3d = self.generate_item_3d_generic(item_2d, sports_fields.golf_flag, "Golf Flag")

        elif item_2d.extra.get('osm:highway', None) == 'street_lamp' and item_2d.get('osm:lamp_mount', None) == 'high_mast':
            item_3d = self.generate_item_3d_street_lamp_high_mast(item_2d)
        elif item_2d.extra.get('osm:highway', None) == 'street_lamp':
            item_3d = self.generate_item_3d_street_lamp(item_2d)
        elif item_2d.extra.get('osm:highway', None) == 'traffic_signals':
            item_3d = self.generate_item_3d_traffic_signals(item_2d)
        elif item_2d.extra.get('osm:traffic_sign', None) is not None or any([k.startswith('osm:traffic_sign:') for k in item_2d.extra.keys()]):
            item_3d = self.generate_item_3d_traffic_sign(item_2d)

        elif item_2d.extra.get('ddd:road_marking', None):
            item_3d = self.generate_item_3d_road_marking(item_2d)

        elif item_2d.get('ddd:item', None) == 'grass_blade':
            item_3d = self.generate_item_3d_grass_blade(item_2d)
        elif item_2d.get('ddd:item', None) == 'flowers':
            item_3d = self.generate_item_3d_flowers(item_2d)

        elif item_2d.get('ddd:ladder', None) == 'swimming_pool':
            item_3d = self.generate_item_3d_generic(item_2d, landscape.ladder_pool, "Swimming Pool Ladder")

        else:
            logger.debug("Unknown item: %s", item_2d.extra)

        # TODO: Apply height via tags, similar approach to areas
        if item_3d:

            # Copy item_2d attributes
            # TODO: shall this be guaranteed by the generators?
            for k, v in item_2d.extra.items():
                item_3d.set(k, default=v, children=True)
            #data = dict(item_2d.extra)
            #data.update(item_3d.extra)
            #item_3d.extra = data


            # Apply height
            # TODO: Rename this property to either ddd:item... or to a common mechanism for areas, items...
            height_mapping = item_3d.get('ddd:item:elevation', item_3d.get('_height_mapping', 'terrain_geotiff_min_elevation_apply'))

            if height_mapping == 'terrain_geotiff_elevation_apply':
                item_3d = terrain.terrain_geotiff_elevation_apply(item_3d, self.osm.ddd_proj)
            elif height_mapping == 'terrain_geotiff_incline_elevation_apply':
                item_3d = terrain.terrain_geotiff_min_elevation_apply(item_3d, self.osm.ddd_proj)
            elif height_mapping == 'terrain_geotiff_and_path_apply':
                path = item_3d.extra['way_1d']
                vertex_func = self.osm.ways.get_height_apply_func(path)
                item_3d = item_3d.vertex_func(vertex_func)
                item_3d = terrain.terrain_geotiff_min_elevation_apply(item_3d, self.osm.ddd_proj)
            elif height_mapping == 'none':  # building...
                pass
            elif height_mapping == 'building':  # building...
                pass
            else:
                item_3d = terrain.terrain_geotiff_min_elevation_apply(item_3d, self.osm.ddd_proj)

            # Apply base height
            base_height = item_2d.get('ddd:height:base', None)
            if base_height:
                item_3d = item_3d.translate([0, 0, base_height])

        return item_3d

    def generate_item_3d_tree(self, item_2d):

        coords = item_2d.geom.coords[0]

        #invalid = ddd.group([self.osm.ways_2d["0"], self.osm.buildings_2d])
        #if not self.osm.osmops.placement_valid(ddd.disc(coords, r=0.4), invalid=invalid):
        #    return None


        numvariants = 5  # 7

        '''
        tree_type = item_2d.extra.get('osm:tree:type')
        if tree_type is None:
            tree_type = random.choice(['default', 'palm'])
        '''

        tree_type = item_2d.get('osm:tree:type')
        if isinstance(tree_type, dict):
            tree_type = ddd.random.weighted_choice(tree_type)

        key = "tree-%s-%d" % (tree_type, random.choice([x + 1 for x in range(numvariants)]))

        item_3d = self.osm.catalog.instance(key)
        if not item_3d:
            plant_height = random.normalvariate(8.0, 3.0)
            if plant_height < 4.0: plant_height=random.uniform(4.0, 6.5)
            if plant_height > 35.0: plant_height=random.uniform(30.0, 35.0)

            if tree_type == 'default':
                plant_height += 3
                item_3d = plants.tree_default(height=plant_height)
            elif tree_type == 'palm':
                plant_height += 6
                item_3d = plants.tree_palm(height=plant_height)
            elif tree_type == 'fir':
                item_3d = plants.tree_fir(height=plant_height)
            elif tree_type == 'bush':
                item_3d = plants.tree_bush(height=plant_height)
            elif tree_type == 'reed':
                item_3d = plants.reed()
            else:
                raise DDDException("Unknown tree type %r for object %s" % (tree_type, item_2d))

            item_3d = self.osm.catalog.add(key, item_3d)

        item_3d = item_3d.rotate([0.0, 0.0, random.uniform(0, math.pi * 2)])
        item_3d = item_3d.translate([coords[0], coords[1], 0.0])
        item_3d.name = 'Tree: %s' % item_2d.name
        return item_3d

    def generate_item_3d_grass_blade(self, item_2d):

        coords = item_2d.geom.coords[0]

        grass_type = item_2d.get('ddd:grass:type', random.choice(['default', 'dry']))

        key = "grassblade" if grass_type == 'default' else ("grassblade-" + grass_type)
        material = ddd.mats.grass_blade if grass_type == 'default' else ddd.mats.grass_blade_dry

        item_3d = self.osm.catalog.instance(key)
        if not item_3d:
            item_3d = plants.grass_blade()
            item_3d = item_3d.material(material)
            item_3d = self.osm.catalog.add(key, item_3d)

        # TODO: Elevation shall come from pipeline
        item_3d.extra['_height_mapping'] = 'terrain_geotiff_incline_elevation_apply'

        item_3d = item_3d.scale([random.uniform(0.9, 1.1), 0.0, random.uniform(0.9, 1.1)])
        item_3d = item_3d.rotate([0.0, 0.0, random.uniform(0, math.pi * 2)])
        item_3d = item_3d.translate([coords[0], coords[1], 0.0])
        #item_3d.name = 'Grass blade: %s' % item_2d.name
        return item_3d

    def generate_item_3d_flowers(self, item_2d):

        flowers_type = item_2d.get('ddd:flowers:type')

        coords = item_2d.geom.coords[0]
        key = "flowers-%s" % flowers_type

        item_3d = self.osm.catalog.instance(key)
        if not item_3d:
            material = None
            if flowers_type == 'blue':
                material = ddd.mats.flowers_blue_blade
            elif flowers_type == 'roses':
                material = ddd.mats.flowers_roses_blade
            item_3d = plants.flowers_blade(material)
            item_3d = self.osm.catalog.add(key, item_3d)

        # TODO: Elevation shall come from pipeline
        item_3d.extra['_height_mapping'] = 'terrain_geotiff_incline_elevation_apply'

        item_3d = item_3d.scale([random.uniform(0.9, 1.1), 0.0, random.uniform(0.9, 1.1)])
        item_3d = item_3d.rotate([0.0, 0.0, random.uniform(0, math.pi * 2)])
        item_3d = item_3d.translate([coords[0], coords[1], 0.0])
        #item_3d.name = 'Grass blade: %s' % item_2d.name
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
        item_3d = item_3d.rotate([0, 0, item_2d.extra['ddd:angle'] - math.pi / 2])
        item_3d = item_3d.translate([coords[0], coords[1], 0.0])
        item_3d.name = 'Bench: %s' % item_2d.name
        item_3d.extra['_height_mapping'] = 'terrain_geotiff_incline_elevation_apply'
        return item_3d

    def generate_item_3d_generic(self, item_2d, gen_func, name):

        coords = item_2d.geom.coords[0]
        angle = item_2d.extra.get('ddd:angle', None)

        item_3d = gen_func()

        if item_3d is None:
            return None

        item_3d = item_3d.rotate([0, 0, angle if angle is not None else item_2d.extra['ddd:angle'] - math.pi / 2])
        item_3d = item_3d.translate([coords[0], coords[1], 0.0])
        #item_3d.prop_set('ddd:static', False, children=True)  # TODO: Make static or not via styling
        item_3d.name = '%s: %s' % (name, item_2d.name)
        return item_3d

    # TODO: Generalize to 'ddd:common'?
    def generate_item_3d_generic_catalog(self, key, item_2d, gen_func, name):

        item_3d = self.osm.catalog.instance(key)
        if not item_3d:
            catalog_item = item_2d.recenter()
            catalog_item.set('ddd:angle', 0)
            item_3d = self.generate_item_3d_generic(catalog_item, gen_func, name)
            item_3d = self.osm.catalog.add(key, item_3d)

        coords = item_2d.geom.coords[0]
        item_3d = item_3d.rotate([0, 0, item_2d.extra['ddd:angle'] - math.pi / 2])
        item_3d = item_3d.translate([coords[0], coords[1], 0.0])
        item_3d.name = '%s: %s' % (name, item_2d.name)
        item_3d.set('_height_mapping', default='terrain_geotiff_incline_elevation_apply')
        return item_3d

    '''
    def generate_item_3d_post_box(self, item_2d):

        coords = item_2d.geom.coords[0]
        item_3d = urban.post_box().translate([coords[0], coords[1], 0.0])
        item_3d.prop_set('ddd:static', False, children=True)  # TODO: Make static or not via styling
        operator = item_2d.extra['osm:feature'].get('operator')
        item_3d.name = 'Postbox (%s): %s' % (operator, item_2d.name)
        return item_3d
    '''

    def generate_item_3d_waste_basket(self, item_2d):
        coords = item_2d.geom.coords[0]

        itemtype = "waste-basket" if random.uniform(0, 1) < 0.5 else "waste-basket-post"

        key = "%s-default-1" % itemtype
        item_3d = self.osm.catalog.instance(key)
        if not item_3d:
            if itemtype == "waste-basket":
                item_3d = urban.trash_bin()
            else:
                item_3d = urban.trash_bin_post()
            item_3d = self.osm.catalog.add(key, item_3d)

        item_3d.prop_set('ddd:static', False, children=False)  # TODO: Make static or not via styling
        item_3d = item_3d.rotate([0, 0, item_2d.extra['ddd:angle'] - math.pi / 2])
        item_3d = item_3d.translate([coords[0], coords[1], 0.0])
        item_3d.name = 'Waste bin (%s): %s' % (itemtype, item_2d.name)
        return item_3d

    def generate_item_3d_taxi(self, item_2d):
        #item_2d = ddd.snap.project(item_2d, areas_2d, penetrate=0.5)
        item_2d = ddd.snap.project(item_2d, self.osm.ways_2d["0"], penetrate=-1)
        coords = item_2d.geom.coords[0]
        item_3d = urban.trafficsign_sign_rect(signtype="info", icon="i", text="TAXI").translate([coords[0], coords[1], 0.0])
        item_3d.name = 'Taxi Stop: %s' % (item_2d.name)
        return item_3d

    def generate_item_3d_sculpture(self, item_2d):
        coords = item_2d.geom.coords[0]
        #oriented_point = ddd.snap.project(ddd.point(coords), self.osm.ways_2d['0'])

        item_name = item_2d.extra['osm:feature']['properties'].get('name', None)
        if item_name:
            if item_2d.extra.get('osm:artwork_type', None) == 'statue':
                item_3d = urban.sculpture_text(item_name[:1], 1.5)
            else:
                # Try
                names = " ".join(self.item_names_all(item_2d))
                item_3d = iconitems.iconitem_auto(names, (2.0, 2.0), 0.4, 0.05)
                if not item_3d:
                    item_3d = urban.sculpture_text(item_name[:1], 1.5)
                else:
                    item_3d = item_3d.translate([0, 0, 0.2])
        else:
            item_3d = urban.sculpture(1.5)

        item_3d = item_3d.rotate([0, 0, item_2d.extra['ddd:angle'] - math.pi / 2])
        item_3d = item_3d.translate([coords[0], coords[1], 0.0]).material(ddd.mats.steel)  # mat_bronze
        item_3d.name = 'Sculpture: %s' % item_2d.name
        return item_3d

    def generate_item_3d_monument(self, item_2d):
        coords = item_2d.geom.coords[0]
        #oriented_point = ddd.snap.project(ddd.point(coords), self.osm.ways_2d['0'])
        item_name = item_2d.extra['osm:feature']['properties'].get('name', None)
        if item_name:
            if item_2d.extra.get('osm:artwork_type', None) == 'statue':
                item_3d = urban.sculpture_text(item_name[:1], 2.0, 5.0)
            else:
                # Try
                names = " ".join(self.item_names_all(item_2d))
                item_3d = iconitems.iconitem_auto(names, (2.0, 4.0), 0.8, 0.1)
                if not item_3d:
                    item_3d = urban.sculpture_text(item_name[:1], 2.0, 5.0)
                else:
                    item_3d = item_3d.translate([0, 0, 0.2])

        else:
            item_3d = urban.sculpture(2.0, 5.0)
        item_3d = urban.pedestal(item_3d, 2.0)
        item_3d = item_3d.rotate([0, 0, item_2d.get('ddd:angle', 0) - math.pi / 2])
        item_3d = item_3d.translate([coords[0], coords[1], 0.0]).material(ddd.mats.bronze)
        item_3d.name = 'Monument: %s' % item_2d.name
        return item_3d

    def generate_item_3d_wayside_cross(self, item_2d):
        coords = item_2d.geom.coords[0]
        item_3d = urban.wayside_cross()
        item_3d = item_3d.rotate([0, 0, item_2d.extra['ddd:angle'] - math.pi / 2])
        item_3d = item_3d.translate([coords[0], coords[1], 0.0]).material(ddd.mats.stone)  # mat_bronze
        item_3d.name = 'Wayside Cross: %s' % item_2d.name
        return item_3d

    def generate_item_3d_historic_archaeological_site(self, item_2d):
        # TODO: Move the actual site generation, given an area, to sketchy

        coords = item_2d.centroid().geom.coords[0]
        if item_2d.geom.geom_type in ("Point", "LineString"):
            points = item_2d.buffer(5.0).random_points(12)
        else:
            points = item_2d.random_points(12)

        line1 = ddd.line(points[0:2])
        line2 = ddd.line(points[2:5])
        line3 = ddd.line(points[5:])
        geomobj = ddd.group2([line1, line2, line3]).buffer(0.5).union()
        #geomobj = filters.noise_random(geomobj, scale=0.075).clean().remove_z()
        #geomobj.show()

        item_3d = geomobj.extrude(0.8)
        #item_3d.copy_from(item_2d)
        item_3d = filters.noise_random(item_3d, scale=0.3)
        item_3d = item_3d.material(ddd.mats.tiles_stones_veg_sparse)
        item_3d = ddd.uv.map_cubic(item_3d)

        # Dont translate ir rotate, item is already in world space (built from item_2d).
        #item_3d = item_3d.rotate([0, 0, item_2d.get('ddd:angle', 0) - math.pi / 2])
        #item_3d = item_3d.translate([coords[0], coords[1], 0.0])  # mat_bronze
        item_3d.name = 'Archaeological Site: %s' % item_2d.name
        return item_3d


    def generate_item_3d_lighthouse(self, item_2d):
        coords = item_2d.geom.coords[0]
        item_3d = landscape.lighthouse().translate([coords[0], coords[1], 0.0])
        item_3d.name = 'Lighthouse: %s' % item_2d.name
        return item_3d

    def generate_item_3d_crane(self, item_2d):
        coords = item_2d.geom.coords[0]
        oriented_point = ddd.point(coords)
        try:
            oriented_point = ddd.snap.project(ddd.point(coords), self.osm.ways_2d['0'])  # FIXME: Align to coastline if any?
        except Exception as e:
            logger.error("Could not orient crane: %s", item_2d)
            oriented_point.extra['ddd:angle'] = 0
        item_3d = industrial.crane_vertical()
        item_3d = item_3d.rotate([0, 0, oriented_point.extra['ddd:angle'] - math.pi / 2])
        item_3d = item_3d.translate([coords[0], coords[1], 0.0])
        item_3d.name = 'Crane: %s' % item_2d.name
        return item_3d


    def generate_item_3d_man_made_tower_communication(self, item_2d):
        # TODO: Unify powertower, post, and maybe other joins, add catenaries using power:line
        # and orient poles
        coords = item_2d.geom.coords[0]
        item_3d = landscape.comm_tower()
        item_3d = item_3d.translate([coords[0], coords[1], 0.0])
        item_3d.name = 'Comm Tower: %s' % item_2d.name
        return item_3d


    def generate_item_3d_bus_stop(self, item_2d):
        coords = item_2d.geom.coords[0]
        text = item_2d.extra.get("osm:name", None)
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
        item_3d = landscape.powertower(14)
        item_3d = item_3d.material(ddd.mats.wood)
        item_3d = item_3d.translate([coords[0], coords[1], 0.0])
        item_3d.name = 'Power Pole: %s' % item_2d.name
        return item_3d

    def generate_item_3d_fence(self, item_2d):
        """
        Expects a line.
        """

        #parse_meters(part.extra.get('osm:height', floors_height + min_height)) - roof_height
        min_height = float(item_2d.extra.get('ddd:min_height', item_2d.extra.get('osm:min_height', 0)))
        max_height = float(item_2d.extra.get('ddd:height', item_2d.extra.get('ddd:item:height', item_2d.extra.get('osm:height', 0))))
        dif_height = max_height - min_height

        item_3d = item_2d.extrude(dif_height)
        item_3d = ddd.uv.map_cubic(item_3d)

        if True:
            topbar = item_2d.buffer(0.1).extrude(0.1).material(ddd.mats.bronze)
            topbar = topbar.translate([0, 0, dif_height])
            topbar = ddd.uv.map_cubic(topbar)
            item_3d = item_3d.append(topbar)

        if min_height:
            item_3d = item_3d.translate([0, 0, min_height])

        item_3d.extra['_height_mapping'] = item_3d.extra.get('ddd:elevation', 'terrain_geotiff_elevation_apply')
        item_3d.name = 'Fence: %s' % item_2d.name

        # Subdivide
        # TODO: Is this the correct place to subdivide fences? ItemWays are also subdivides but in s60_model
        if int(ddd.data.get('ddd:area:subdivide', 0)) > 0:
            item_3d = ddd.meshops.subdivide_to_grid(item_3d, float(ddd.data.get('ddd:area:subdivide')))

        return item_3d

    def generate_item_3d_hedge(self, item_2d):
        """
        Expects a line.
        """
        height = item_2d.extra['ddd:height']
        width = item_2d.extra['ddd:width']
        profile = item_2d.buffer(width - 0.2)
        item_3d = profile.extrude_step(profile.buffer(0.2), 0.4, method=ddd.EXTRUSION_METHOD_SUBTRACT)
        item_3d = item_3d.extrude_step(profile.buffer(0.2), height - 0.6, method=ddd.EXTRUSION_METHOD_SUBTRACT)
        item_3d = item_3d.extrude_step(profile, 0.2, method=ddd.EXTRUSION_METHOD_SUBTRACT)

        # Subdivide
        if int(ddd.data.get('ddd:area:subdivide', 0)) > 0:
            item_3d = ddd.meshops.subdivide_to_grid(item_3d, float(ddd.data.get('ddd:area:subdivide')))

        item_3d = ddd.uv.map_cubic(item_3d)
        item_3d.extra['_height_mapping'] = 'terrain_geotiff_elevation_apply'
        item_3d.name = 'Hedge: %s' % item_2d.name
        return item_3d


    def generate_item_3d_powerline(self, item_2d):

        coords = item_2d.geom.coords

        item_3d = item_2d.copy3(name="Powerline: %s" % item_2d.name)

        for (pa, pb) in zip(coords[:-1], coords[1:]):
            pa = (pa[0], pa[1], 13.8 + terrain_geotiff_elevation_value(pa, self.osm.ddd_proj))
            pb = (pb[0], pb[1], 13.8 + terrain_geotiff_elevation_value(pb, self.osm.ddd_proj))
            dist = np.linalg.norm(np.array(pa) - np.array(pb))
            length_ratio = 1 + (0.05 / (dist / 10))
            item_cable = urban.catenary_cable(pa, pb, length_ratio=length_ratio)
            item_3d.append(item_cable)

        item_3d.extra['_height_mapping'] = 'none'

        return item_3d

    def generate_item_3d_street_lamp(self, item_2d):

        coords = item_2d.geom.coords[0]

        key = "lamppost-default-1"
        item_3d = self.osm.catalog.instance(key)
        if not item_3d:
            item_3d = urban.lamppost(height=5.5)
            item_3d = self.osm.catalog.add(key, item_3d)

        item_3d.extra.update(item_2d.extra)
        item_3d.prop_set('ddd:static', False, children=False)  # TODO: Make static or not via styling
        item_3d.prop_set('yc:layer', 'DynamicObjects')  # TODO: Assign layers via styling
        item_3d = item_3d.translate([coords[0], coords[1], 0.0])
        item_3d.name = 'Lamppost: %s' % item_2d.name

        return item_3d

    def generate_item_3d_street_lamp_high_mast(self, item_2d):

        key = "lamppost-highmast-1"
        item_3d = self.osm.catalog.instance(key)
        if not item_3d:
            item_3d = urban.lamppost_high_mast()
            item_3d = self.osm.catalog.add(key, item_3d)

        coords = item_2d.geom.coords[0]
        item_3d.extra.update(item_2d.extra)
        item_3d = item_3d.translate([coords[0], coords[1], 0.0])
        item_3d.name = 'Lamppost High Mast: %s' % item_2d.name

        return item_3d

    def select_way(self, item_2d):

        #osm_way = item_2d.extra.get('osm:item:way', None)
        osm_ways = item_2d.extra.get('osm:item:ways', [])

        votes = defaultdict(list)
        for way in osm_ways:
            votes[way.extra['ddd:way:weight']].append(way)
        max_voted_ways_weight = list(votes.items())
        max_voted_ways_weight = reversed(sorted(max_voted_ways_weight, key=lambda w: w[0]))
        max_voted_ways_weight = sorted(max_voted_ways_weight, key=lambda w: len(w[1]))

        if len(max_voted_ways_weight) == 0: return None

        max_voted_ways_weight = list(reversed(max_voted_ways_weight))[0][0]
        highest_ways = votes[max_voted_ways_weight]

        osm_way = highest_ways[0]
        return osm_way

    def generate_item_3d_traffic_signals(self, item_2d):

        #logger.debug("Generating traffic signals: %s %s", item_2d, item_2d.extra)

        key = "trafficlights-default-1"
        item_3d = self.osm.catalog.instance(key)
        if not item_3d:
            item_3d = urban.trafficlights()
            item_3d = self.osm.catalog.add(key, item_3d)

        item_3d.extra.update(item_2d.extra)  # TODO: This is agressive

        #osm_way = item_2d.extra.get('osm:item:way', None)
        #osm_ways = item_2d.extra.get('osm:item:ways', None)
        osm_way = self.select_way(item_2d)
        if osm_way:
            item_2d = self.osm.osmops.position_along_way(item_2d, osm_way)
        #    if len(osm_ways) > 1:
        #        logger.error("Node belongs to more than one way (%s): %s", item_2d, osm_ways)
        coords = item_2d.geom.coords[0]

        #if 'osm:direction' in item_2d.extra: item_2d.extra['ddd:angle'] = item_2d.extra['osm:direction'] * (math.pi / 180)

        #if item_2d.extra.get('ddd:angle', None) is None: item_2d.extra['ddd:angle'] = 0
        item_3d = item_3d.rotate([0, 0, item_2d.extra['ddd:angle'] - math.pi / 2])

        item_3d = item_3d.translate([coords[0], coords[1], 0.0])
        item_3d.name = 'Traffic Signals: %s' % item_2d.name
        return item_3d

    def generate_item_3d_traffic_sign(self, item_2d):

        # TODO: Do this in preprocessing (different OSM conventions, also make lowercase)
        for k, v in item_2d.extra.items():
            if k.startswith('osm:traffic_sign:'):
                item_2d.extra['osm:traffic_sign'] = v
                item_2d.extra['osm:direction'] = k[len('osm:traffic_sign:'):]
                break

        signtype = item_2d.extra['osm:traffic_sign'].lower()

        key = "traffic_sign-%s-1" % (signtype)
        item_3d = self.osm.catalog.instance(key)
        if not item_3d:
            item_3d = urban.traffic_sign(signtype)
            if not item_3d:
                logger.warn("Could not generate traffic sign: %s", item_2d)
                return None
            item_3d = self.osm.catalog.add(key, item_3d)

        osm_way = self.select_way(item_2d)
        #osm_way = item_2d.extra.get('osm:item:way', None)
        #osm_ways = item_2d.extra.get('osm:item:ways', None)
        if osm_way:
            offset = 0
            if len(item_2d.extra.get('osm:item:ways', [])) > 3: offset = -5
            item_2d = self.osm.osmops.position_along_way(item_2d, osm_way, offset=offset)
            coords = item_2d.geom.coords[0]
            #if len(osm_ways) > 1:
            #    logger.error("Node belongs to more than one way (%s): %s", item_2d, osm_ways)
        else:
            # Point shall have been projected and have a direction
            coords = item_2d.geom.coords[0]
            item_2d.extra['ddd:angle'] = item_2d.extra['ddd:angle'] + math.pi / 2
            #if angle: item_2d.extra['ddd:angle'] = angle

        item_3d.prop_set('ddd:static', False, children=False)  # TODO: Make static or not via styling
        item_3d.extra['ddd:layer'] = 'DynamicObjects'  # TODO: Assign layers via styling
        item_3d = item_3d.rotate([0, 0, item_2d.extra['ddd:angle'] - math.pi / 2])
        item_3d = item_3d.translate([coords[0], coords[1], 0.0])
        item_3d.extra['_height_mapping'] = 'terrain_geotiff_incline_elevation_apply'
        item_3d.name = 'Traffic Sign: %s' % item_2d.name
        return item_3d

    def generate_item_3d_road_marking(self, item_2d):
        """
        Generate instances or meshes
        If using meshes, they should be combined (see osm_model_generate_ways_road_markings_combine).
        """

        asinstance = False

        # Note that give_way is not a node tag for OSM, but it is used here to represent each individual symbol
        signtype = item_2d.extra['ddd:road_marking'].lower()

        key = "road_marking-%s-1" % (signtype)

        item_3d = None
        if asinstance:
            item_3d = self.osm.catalog.instance(key)

        if not item_3d:
            item_3d = urban.road_marking(signtype)
            if not item_3d:
                logger.warn("Could not generate road-marking: %s", item_2d)
                return None
            if asinstance:
                item_3d = self.osm.catalog.add(key, item_3d)

        '''
        osm_way = self.select_way(item_2d)
        #osm_way = item_2d.extra.get('osm:item:way', None)
        #osm_ways = item_2d.extra.get('osm:item:ways', None)
        if osm_way:
            offset = 0
            if len(item_2d.extra.get('osm:item:ways', [])) > 3: offset = -5
            item_2d = self.osm.osmops.position_along_way(item_2d, osm_way, offset=offset)
            coords = item_2d.geom.coords[0]
            #if len(osm_ways) > 1:
            #    logger.error("Node belongs to more than one way (%s): %s", item_2d, osm_ways)
        else:
        '''
        # Point shall have been projected and have a direction
        coords = item_2d.geom.coords[0]
        item_2d.extra['ddd:angle'] = item_2d.extra['ddd:angle'] + math.pi / 2
        #if angle: item_2d.extra['ddd:angle'] = angle

        item_3d.prop_set('ddd:static', False, children=False)  # TODO: Make static or not via styling
        item_3d.extra['ddd:layer'] = 'DynamicObjects'  # TODO: Assign layers via styling
        item_3d = item_3d.rotate([0, 0, item_2d.extra['ddd:angle']])  # - math.pi / 2])
        item_3d = item_3d.translate([coords[0], coords[1], 0.05])

        if asinstance:
            item_3d.extra['_height_mapping'] = 'terrain_geotiff_incline_elevation_apply'
        else:
            item_3d.extra['_height_mapping'] = 'terrain_geotiff_elevation_apply'

        item_3d.name = 'Road Mark: %s' % item_2d.name
        return item_3d




