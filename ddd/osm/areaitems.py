# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging
import math
import random

from ddd.ddd import ddd
from ddd.geo import terrain


# Get instance of logger for this module
logger = logging.getLogger(__name__)

class AreaItemsOSMBuilder():

    def __init__(self, osmbuilder):
        self.osm = osmbuilder

    def generate_item_2d_outdoor_seating(self, feature):

        # Distribute centers for seating (ideally, grid if shape is almost square, sampled if not)
        # For now, using center:

        center = feature.centroid()

        table = center.copy(name="Outdoor seating table: %s" % feature.name)
        table.extra['osm:amenity'] = 'table'
        table.extra['osm:seats'] = random.randint(0, 4)

        umbrella = ddd.group2()
        if random.uniform(0, 1) < 0.8:
            umbrella = center.copy(name="Outdoor seating umbrella: %s" % feature.name)
            umbrella.extra['osmext:amenity'] = 'umbrella'

        chairs = ddd.group2(name="Outdoor seating seats")
        ang_offset = random.choice([0, math.pi / 2, math.pi, math.pi * 3/4])
        for i in range(table.extra['osm:seats']):
            ang = ang_offset + (2 * math.pi / table.extra['osm:seats']) * i + random.uniform(-0.1, 0.1)
            chair = ddd.point([0, random.uniform(0.7, 1.1)], name="Outdoor seating seat %d: %s" % (i, feature.name))
            chair = chair.rotate(ang).translate(center.geom.coords[0])
            chair.extra['osm:amenity'] = 'seat'
            chair.extra['ddd:angle'] = ang + random.uniform(-0.1, 0.1) # * (180 / math.pi)
            chairs.append(chair)

        item = ddd.group2([table, umbrella, chairs], "Outdoor seating: %s" % feature.name)

        return item

        '''
        for i in item.flatten().children:
            if i.geom: self.osm.items_1d.append(i)
        return None
        '''

    def generate_item_2d_childrens_playground(self, feature):

        # Distribute centers for seating (ideally, grid if shape is almost square, sampled if not)
        # For now, using center:

        center = feature.centroid()
        #if center.geom.is_empty: return ddd.group2()

        items = [ddd.point(name="Swingset Swing", extra={'osm:playground': 'swing'}),
                 ddd.point(name="Swingset Monkey Bar", extra={'osm:playground': 'monkey_bar'})]
        if random.uniform(0, 1) < 0.8:
            items.append(ddd.point(name="Swingset Sandbox", extra={'osm:playground': 'sandbox'}))
        if random.uniform(0, 1) < 0.8:
            items.append(ddd.point(name="Swingset Slide", extra={'osm:playground': 'slide'}))
        if random.uniform(0, 1) < 0.8:
            items.append(ddd.point(name="Swingset Swing 2", extra={'osm:playground': 'swing'}))

        items = ddd.group2(items, name="Childrens Playground: %s" % feature.name)

        items = ddd.align.polar(items, 3, offset=random.uniform(0, math.pi * 2))
        items = items.translate(center.geom.coords[0])

        return items


    def generate_item_3d(self, item_2d):
        item_3d = None
        if item_2d.extra.get('osm:amenity', None) == 'fountain':
            item_3d = self.generate_item_3d_fountain(item_2d)
        if item_2d.extra.get('osm:leisure', None) == 'swimming_pool':
            item_3d = self.generate_item_3d_swimming_pool(item_2d)
        if item_2d.extra.get('osm:water', None) == 'pond':
            item_3d = self.generate_item_3d_pond(item_2d)

        if item_3d:
            item_3d.name = item_2d.name
            #item_3d.extra['ddd:elevation'] = "geotiff"
            #item_3d = terrain.terrain_geotiff_elevation_apply(item_3d, self.osm.ddd_proj)
            #self.osm.items_3d.children.append(item_3d)
            #logger.debug("Generated area item: %s", item_3d)

        return item_3d

    def generate_item_3d_fountain(self, item_2d):
        
        # TODO: Call fountain builder(s)...

        border_width = 0.3
        exterior = item_2d
        interior = item_2d.buffer(-border_width)
        
        fountain = exterior.extrude_step(exterior, 1.0, base=False, method=ddd.EXTRUSION_METHOD_WRAP)
        fountain = fountain.extrude_step(interior, 0.0, method=ddd.EXTRUSION_METHOD_SUBTRACT)
        fountain = fountain.extrude_step(interior, -1.4, cap=True, method=ddd.EXTRUSION_METHOD_WRAP)
        
        fountain = fountain.material(ddd.mats.stone)
        fountain = ddd.uv.map_cubic(fountain)

        water =  item_2d.buffer(-border_width / 2).triangulate().material(ddd.mats.water).translate([0, 0, 0.4])
        water = water.smooth()
        water = ddd.uv.map_xy(water)

        #coords = item_2d.geom.centroid.coords[0]
        #insidefountain = urban.fountain(r=item_2d.geom).translate([coords[0], coords[1], 0.0])

        item_3d = ddd.group([fountain, water])

        item_3d.name = 'Fountain: %s' % item_2d.name
        return item_3d

    def generate_item_3d_pond(self, item_2d):
        # Todo: Use fountain shape if available, instead of centroid
        exterior = item_2d.subtract(item_2d.buffer(-0.4)).extrude(0.4).material(ddd.mats.dirt)
        exterior = ddd.uv.map_cubic(exterior)

        water = item_2d.buffer(-0.2).triangulate().material(ddd.mats.water)
        water = ddd.uv.map_xy(water)  # map_2d_linear

        #coords = item_2d.geom.centroid.coords[0]
        #insidefountain = urban.fountain(r=item_2d.geom).translate([coords[0], coords[1], 0.0])

        item_3d = ddd.group([exterior, water])  # .translate([0, 0, 0.3])

        item_3d.name = 'Pond: %s' % item_2d.name
        return item_3d

    def generate_item_3d_swimming_pool(self, item_2d):
        """
        This swimming pool generates a border _outside_ its shape (note this is unusual for shape-based builders).
        """

        # TODO: Move pool building to pack.buildings.pools (variety: border overhang, or smooth, rounded corners, rounded bottom...)
        vase_materials = [ddd.mats.porcelain_blue_tiles, ddd.mats.porcelain_blue_tiles_round]
        vase_material = ddd.random.choice(vase_materials, seed=item_2d.get('osm:id'))
        exterior_materials = [ddd.mats.tiles_stones, ddd.mats.wood_planks]
        exterior_material = ddd.random.choice(exterior_materials + [vase_material], seed=item_2d.get('osm:id'))

        # TODO: This should be an area, so stuff can be positioned on top and etc.
        border_exterior_width = 1.0
        border_interior_width = random.choice([0.0, 0.05, 0.1])  # for hanging borders
        border_height = 0.2
        pool_depth = 2.2  # relative to base, not to border
        water_level = -0.35  # relative to base, not to border
        height_margin = pool_depth + 0.2  # because the elevation positioning will account only for the interior, we need a safety margin
        bevel = 0.015
        
        interior = item_2d
        if border_interior_width > 0: interior = item_2d.buffer(-border_interior_width)
        exterior = item_2d.buffer(border_exterior_width)
        exterior = exterior.extrude_step(exterior, border_height + height_margin)
        if bevel:
            exterior = exterior.extrude_step(interior.buffer(bevel), 0.0, method=ddd.EXTRUSION_METHOD_SUBTRACT)
            exterior = exterior.extrude_step(interior, -bevel, method=ddd.EXTRUSION_METHOD_SUBTRACT)
        else:
            exterior = exterior.extrude_step(interior, 0.0, method=ddd.EXTRUSION_METHOD_SUBTRACT)
        exterior = exterior.extrude_step(interior, -(border_height - bevel), method=ddd.EXTRUSION_METHOD_WRAP)
        if border_interior_width > 0:
            exterior = exterior.extrude_step(item_2d, 0.0, method=ddd.EXTRUSION_METHOD_SUBTRACT)

        exterior = exterior.translate([0, 0, -height_margin])
        exterior = exterior.material(exterior_material)
        exterior = exterior.smooth(ddd.PI_OVER_8)
        exterior = ddd.uv.map_cubic(exterior)

        vase = item_2d.extrude_step(item_2d, -pool_depth, base=False)
        vase = vase.material(vase_material)
        vase = ddd.uv.map_cubic(vase)

        water = item_2d.triangulate().material(ddd.mats.water)
        #water = ddd.meshops.subdivide_to_grid(water, float(ddd.data.get('ddd:area:subdivide')) * 2)
        water = water.smooth()
        water = ddd.uv.map_xy(water)
        
        water = water.translate([0, 0, water_level])

        #coords = item_2d.geom.centroid.coords[0]
        #insidefountain = urban.fountain(r=item_2d.geom).translate([coords[0], coords[1], 0.0])

        item_3d = ddd.group([exterior, water, vase])  # .translate([0, 0, 0.3])

        item_3d.name = 'Swimming Pool: %s' % item_2d.name
        return item_3d
