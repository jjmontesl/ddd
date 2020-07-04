# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging

from shapely.errors import TopologicalError
from shapely.geometry.polygon import LinearRing

from ddd.core.exception import DDDException
from ddd.ddd import ddd


# Get instance of logger for this module
logger = logging.getLogger(__name__)

class Areas2DOSMBuilder():

    def __init__(self, osmbuilder):

        self.osm = osmbuilder

    def generate_areas_2d_process(self, areas_2d_group, areas_2d, subtract):

        # TODO: Assign area here, it's where it's used
        areas = areas_2d.select('["ddd:area:area"]').children

        logger.info("Sorting 2D areas (%d).", len(areas))
        areas.sort(key=lambda a: a.extra['ddd:area:area'])

        for idx in range(len(areas)):
            area = areas[idx]
            for larger in areas[idx + 1:]:
                if larger.contains(area):
                    #logger.info("Area %s contains %s.", larger, area)
                    area.extra['ddd:area:container'] = larger
                    larger.extra['ddd:area:contained'].append(area)
                    break

        # Union all roads in the plane to subtract
        logger.info("Generating 2D areas subtract.")
        #union = ddd.group([self.osm.ways_2d['0'], self.osm.ways_2d['-1a']]).union()  # , areas_2d
        union = subtract.union()

        logger.info("Generating 2D areas (%d)", len(areas))
        for area in reversed(areas):

            #feature = area.extra['osm:feature']
            if not area.geom:
                logger.error("Area with no geometry: %s", area)
            if area.geom.type == 'Point': continue

            original_area = area
            area.extra['ddd:area:original'] = original_area  # Before subtracting any internal area

            '''
            # Subtract areas contained (use contained relationship)
            for contained in narea.extra['ddd:area:contained']:
                narea = narea.subtract(contained)
            '''

            narea = area.subtract(ddd.group2(area.extra['ddd:area:contained']))
            narea = narea.subtract(union)
            #narea = narea.clean()  #eps=0.0)

            if narea and narea.geom:
                logger.debug("Area: %s", narea)
                #area = area.subtract(union)

                areas_2d_group.remove(original_area)
                areas_2d_group.append(narea)
                #areas_2d.children.extend(area.individualize().children)


    def generate_union_safe(self, groups):
        """
        Unions a series of groups.

        This is used for generation of interways, as the resulting union interiors are the target areas.
        """
        try:
            union = groups.union()
            union = union.clean(eps=0.01)
        except TopologicalError as e:
            logger.debug("Error calculating safe union_safe (1/2): %s", e)
            children_unions = []
            for g in groups.children:
                u = g.clean(eps=0.01).union()
                children_unions.append(u)
            try:
                union = ddd.group2(children_unions)
                #union = union.buffer(eps, 1, join_style=ddd.JOIN_MITRE).buffer(-eps, 1, join_style=ddd.JOIN_MITRE)
                union = union.union()
            except TopologicalError as e:
                logger.error("Error calculating union_safe (2/2): %s", e)
                union = ddd.group2()
                #union = ddd.group([self.osm.ways_2d['0'], self.osm.ways_2d['-1a'], areas_2d]).union()
        return union

    def generate_areas_2d_ways_interiors(self, union):

        result = ddd.group2()
        if not union.geom: return result

        for c in ([union.geom] if union.geom.type == "Polygon" else union.geom):
            if c.type == "LineString":
                logger.warning("Interways areas union resulted in LineString geometry. Skipping.")
                continue
            if len(c.interiors) == 0:
                continue

            logger.info("Generating %d interiors.", len(c.interiors))
            for interior in c.interiors:
                area = ddd.polygon(interior.coords, name="Interways area")
                if area:
                    area = area.subtract(union)
                    area = area.clean(eps=0.01)
                    #area = area.clean()
                    if area.geom:
                        result.append(area)
                else:
                    logger.warn("Invalid interways area.")

        return result

    '''
    def generate_areas_ways_relations(self):
        logger.info("Areas - Ways relations (%d areas, %d ways['0']).", len(self.osm.areas_2d.children), len(self.osm.ways_2d['0'].children))
        for area in self.osm.areas_2d.children:
            if area.extra.get('ddd:area:type', None) != 'sidewalk': continue
    '''

    def generate_areas_2d_postprocess(self):
        """
        """

        logger.info("Postprocessing areas and ways (%d areas, %d ways['0']).", len(self.osm.areas_2d.children), len(self.osm.ways_2d['0'].children))

        #
        areas_2d_original = ddd.group2()
        for a in self.osm.areas_2d.children:
            if a.extra.get('ddd:area:original', None):
                if a.extra.get('ddd:area:original') not in areas_2d_original.children:
                    areas_2d_original.append(a.extra.get('ddd:area:original'))

        # Remove paths from some areas (sidewalks), and reincorporate to them
        #to_remove = []
        for way_2d in self.osm.ways_2d['0'].children:
            if way_2d.extra.get('osm:highway', None) not in ('footway', 'path', 'track', None): continue
            if way_2d.extra.get('ddd:area:type', None) == 'water': continue

            for area in areas_2d_original.children:  #self.osm.areas_2d.children:  # self.osm.areas_2d.children:

                #area_original = area.extra.get('ddd:area:original', None)
                #if area_original is None: continue

                area_original = area

                #if area.extra.get('ddd:area:type', None) != 'sidewalk': continue

                intersects = False
                try:
                    intersects = area_original.intersects(way_2d)
                except Exception as e:
                    logger.error("Could not calculate intersections between way and area: %s %s", way_2d, area)
                    raise DDDException("Could not calculate intersections between way and area: %s %s" % (way_2d, area))

                if intersects:
                    logger.debug("Path %s intersects area: %s (subtracting and arranging)", way_2d, area)
                    way_2d.extra['ddd:area:container'] = area_original
                    #to_remove.append(area

                    intersection = way_2d.intersection(area_original)
                    remainder = way_2d.subtract(area_original)

                    way_2d.replace(intersection)  # way_2d.subtract(intersection))

                    remainder = remainder.material(ddd.mats.pavement)
                    area.extra['ddd:area:type'] = 'sidewalk'
                    remainder.name = "Path to interways: %s" % way_2d.name
                    remainder.clean(eps=0.001)
                    self.osm.areas_2d.append(remainder)
                    #area = area.union().clean(eps=0.001)

        #self.osm.areas_2d.children = [c for c in self.osm.areas_2d.children if c not in to_remove]

    def generate_areas_2d_postprocess_water(self, areas_2d, ways_2d):
        logger.info("Postprocessing water areas and ways")

        # Get all water areas ('ddd:water')
        water_areas = areas_2d.select('["ddd:area:type" = "water"]', recurse=False).union().clean(eps=0.05)
        #water_areas.show()

        river_areas = ways_2d.select('["ddd:area:type" = "water"]', recurse=False)
        #river_areas.show()

        #all_water_areas = ddd.group2(water_areas.children)

        # Move river areas to areas
        #for c in river_areas.children:
        #    ways_2d.remove(c)
        #    areas_2d.children.extend(river_areas.children)
        # Subtract water areas to ways
        # TODO: Might be done via generic mechanism (assign ways to areas, etc)
        for r in river_areas.children:
            new_river = r.intersection(self.osm.area_filter2)
            if new_river.intersects(water_areas):
                new_river = new_river.subtract(water_areas)
            r.replace(new_river)
        #river_areas.show()

        all_water_areas = ddd.group2([water_areas, river_areas])

        # Create ground area
        underwater_area = all_water_areas.union().clean(eps=0.05)
        #underwater_area.show()
        underwater_area = underwater_area.material(ddd.mats.terrain)
        underwater_area.extra['ddd:area:type'] = 'underwater'
        underwater_area.extra['svg:ignore'] = True
        #underwater_area.show()
        areas_2d.append(underwater_area)


    def generate_coastline_2d(self, area_crop):
        logger.info("Generating water and land areas according to coastline: %s", (area_crop.bounds))

        #self.water_3d = terrain.terrain_grid(self.area_crop.bounds, height=0.1, detail=200.0).translate([0, 0, 1]).material(mat_sea)

        water = ddd.rect(area_crop.bounds, name="Coastline Water")

        coastlines = []
        coastlines_1d = []

        for way in self.osm.features_2d.children:
            if way.extra.get('osm:natural') == 'coastline':
                original = way.extra['osm:original']  # Original has not been cropped (cropped verison is not valid for this)
                coastlines_1d.append(original)
                coastlines.append(original.buffer(0.01))

        #for way in self.osm.features.children:
        #    if way.properties.get('natural') == 'coastline':
        #        coastlines_1d.append(ddd.shape(way.geometry))
        #        coastlines.append(ddd.shape(way.geometry).buffer(0.1))

        if not coastlines:
            logger.info("No coastlines in the feature set.")
            return

        coastlines_1d = ddd.group(coastlines_1d)  #.individualize().flatten()
        coastlines = ddd.group(coastlines)  # .individualize().flatten()
        coastline_areas = water.subtract(coastlines)

        logger.info("Coastlines: %s", (coastlines_1d, ))
        logger.info("Coastline areas: %s", (coastline_areas, ))

        # Generate coastline edge
        if coastlines_1d.children:
            coastlines_2d = coastlines_1d.intersection(water)
            coastlines_2d = coastlines_2d.individualize()
            #coastlines_3d = coastlines_2d.extrude(10.0).translate([0, 0, -10.0])
            #coastlines_3d = terrain.terrain_geotiff_elevation_apply(coastlines_3d, self.osm.ddd_proj)
            #coastlines_3d = ddd.uv.map_cubic(coastlines_3d)
            #coastlines_3d.name = 'Coastline: %s' % coastlines_3d.name
            #self.osm.other_3d.append(coastlines_3d)


        areas_2d = []
        #geoms = coastline_areas.geom.geoms if coastline_areas.geom.type == 'MultiPolygon' else [coastline_areas.geom]
        for water_area_geom in coastline_areas.individualize().flatten().clean().children:
            # Find closest point, closest segment, and angle to closest segment
            #water_area_geom = ddd.shape(water_area_geom).clean(eps=0.01).geom

            #if not water_area_geom.is_simple:
            #    logger.error("Invalid water area geometry (not simple): %s", water_area_geom)
            #    continue

            if not water_area_geom.geom: continue

            #water_area_geom.dump()
            coastlines_1d = coastlines_1d.outline().clean()

            water_area_point = water_area_geom.geom.representative_point()
            p, segment_idx, segment_coords_a, segment_coords_b, closest_obj, closest_d = coastlines_1d.closest_segment(ddd.shape(water_area_point))
            pol = LinearRing([segment_coords_a, segment_coords_b, (water_area_point.coords[0][0], water_area_point.coords[0][1], 0)])

            if not pol.is_ccw:
                #area_3d = area_2d.extrude(-0.2)
                area_2d = ddd.shape(water_area_geom.geom).buffer(0.10).clean(eps=0.01)
                area_2d.validate()
                area_2d = area_2d.material(ddd.mats.sea)
                area_2d.extra['ddd:area:type'] = 'sea'  # not treated as sea
                area_2d.extra['ddd:area:elevation'] = 'none'
                area_2d.extra['ddd:height'] = 0
                area_2d.extra['ddd:collider'] = False
                area_2d.extra['ddd:shadows'] = False
                area_2d.extra['ddd:occluder'] = False

                #area_3d = area_2d.triangulate().translate([0, 0, -0.5])
                areas_2d.append(area_2d)
                #areas.append(area_3d)

        return ddd.group2(areas_2d, name="Water")

        #if areas:
        #    self.osm.water_3d = ddd.group(areas)
        #else:
        #    logger.debug("No water areas from coastline generated.")

