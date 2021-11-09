# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging

from shapely.errors import TopologicalError
from shapely.geometry.polygon import LinearRing

from ddd.core.exception import DDDException
from ddd.ddd import ddd
from shapely.strtree import STRtree


# Get instance of logger for this module
logger = logging.getLogger(__name__)

class Areas2DOSMBuilder():

    def __init__(self, osmbuilder):

        self.osm = osmbuilder

    def generate_areas_2d_process(self, areas_2d_root, areas_2d, subtract):
        """
        Resolves area containment (ddd:area:container|contained).
        """

        # TODO: Assign area before, it's where it's used. Fail here if not set,
        # Using all children from /Area causes problems (but should not) with repeated surfaces, errors in stairs processing
        #areas = list(areas_2d.children)
        areas = areas_2d.select('["ddd:area:area"]').children

        logger.info("Sorting 2D areas (%d).", len(areas))
        areas.sort(key=lambda a: a.get('ddd:area:area'))  # extra['ddd:area:area'])
        #areas.sort(key=lambda a: a.geom.area)  # extra['ddd:area:area'])

        for idx in range(len(areas)):
            area = areas[idx]
            #area_smaller = area.buffer(-0.05)
            #area.set('ddd:area:original', default=area)
            for larger in areas[idx + 1:]:
                if larger.contains(area):
                    #logger.info("Area %s contains %s.", larger, area)
                    area.extra['ddd:area:container'] = larger
                    larger.extra['ddd:area:contained'].append(area)
                    break   # Using this break causes some area containments to be incorrectly assigned

        # Union all roads in the plane to subtract
        #logger.info("Generating 2D areas subtract.")
        #union = ddd.group([self.osm.ways_2d['0'], self.osm.ways_2d['-1a']]).union()  # , areas_2d
        union = subtract  #.union()

        #union = union.clean()  # In (rare) cases the narea subtract below fails with TopologicalError

        logger.info("Generating 2D areas (%d)", len(areas))
        for area in reversed(areas):

            #feature = area.extra['osm:feature']
            if not area.geom:
                logger.error("Area with no geometry: %s", area)
            if area.geom.type == 'Point': continue

            original_area = area
            area.set('ddd:area:original', default=original_area)  # Before subtracting any internal area

            # Subtract union and areas contained (use contained relationship)
            contained = ddd.group2(area.extra['ddd:area:contained'])
            try:
                narea = area.subtract(union)
                if contained:
                    narea = narea.subtract(contained)
            except TopologicalError as e:
                logger.warn("Could not generate 2D area %s (cleaning): %s", area, e)
                narea = narea.clean(-0.01)
                narea = narea.subtract(union)

            #narea = narea.clean()  #eps=0.0)

            if narea and narea.geom:
                logger.debug("Area: %s", narea)

                areas_2d_root.remove(original_area)
                areas_2d_root.append(narea.individualize(always=True).flatten().children)
                #areas_2d.children.extend(area.individualize().children)
                #ddd.group2([original_area, narea.material(ddd.MAT_HIGHLIGHT)]).show()


    def generate_union_safe(self, groups):
        """
        Unions a series of groups.

        This is used for generation of interways, as the resulting union interiors are the target areas.
        """
        try:
            union = groups.copy().union_replace()
            union = union.clean(eps=0.01)
        except TopologicalError as e:
            logger.debug("Error calculating safe union_safe (1/3): %s", e)
            children_unions = []
            for g in groups.children:
                u = g.clean(eps=0.01).union()
                children_unions.append(u)
            try:
                union = ddd.group2(children_unions)
                union = union.union()
            except TopologicalError as e:
                logger.error("Error calculating union_safe (2/3): %s", e)
                #union = groups.clean(eps=0.05).union()  # causes areas overlap?
                #union = ddd.group2()
        return union

    def generate_areas_2d_ways_interiors(self, union):
        """
        Generates interways areas.
        """

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
                        area.set('ddd:area:interways', True)
                        result.append(area)
                else:
                    logger.warn("Invalid interways area.")

        return result

    def generate_areas_2d_postprocess_cut_outlines(self, areas_2d, ways_2d):
        """
        """

        '''
        areas_2d_original = ddd.group2()
        for a in areas_2d.children:
            if a.extra.get('ddd:area:original', None):
                if a.extra.get('ddd:area:original') not in areas_2d_original.children:
                    areas_2d_original.append(a.extra.get('ddd:area:original'))
        '''
        areas_2d_original = areas_2d.select('["ddd:area:original"]')  # ;["ddd:area:interways"]')

        logger.info("Postprocessing areas and ways (%d areas_2d_original, %d ways).", len(areas_2d_original.children), len(ways_2d.children))

        to_process = ways_2d.children

        # Remove paths from some areas (sidewalks), and reincorporate to them
        #to_remove = []
        while to_process:
            to_process_copy = to_process
            to_append = []
            to_process = []
            for way_2d in to_process_copy:

                if way_2d.is_empty(): continue

                #if way_2d.extra.get('osm:highway', None) not in ('footway', 'path', 'track', None): continue
                if way_2d.extra.get('ddd:area:type', None) == 'water': continue

                if way_2d.geom.type == "MultiPolygon":
                    logger.warn("Skipping way postprocess (multipolygon not supported, should individualize ways2 earlier -introduces way intersection joint errors-?): %s", way_2d)
                    continue

                for area in areas_2d_original.children:  #self.osm.areas_2d.children:  # self.osm.areas_2d.children:

                    area_original = area.get('ddd:area:original', None)
                    if area_original is None: continue

                    if area_original.is_empty(): continue


                    #if area.extra.get('ddd:area:type', None) != 'sidewalk': continue

                    try:
                        intersects = way_2d.buffer(-0.01).intersects(area_original)
                        intersects_outline = way_2d.intersects(area_original.outline())
                    except Exception as e:
                        logger.error("Could not calculate intersections between way and area: %s %s", way_2d, area)
                        raise DDDException("Could not calculate intersections between way and area: %s %s" % (way_2d, area))

                    if intersects and not intersects_outline:
                        way_2d.extra['ddd:area:container'] = area_original
                        continue

                    if intersects and intersects_outline:
                        logger.debug("Path %s intersects area: %s (subtracting and arranging)", way_2d, area)

                        #ddd.group2([way_2d, area_original]).show()

                        intersection = way_2d.intersection(area_original)
                        #intersection.extra['ddd:area:container'].append(area)
                        intersection.name = "Path %s in area %s" % (way_2d.name, area.name)
                        intersection.extra['ddd:area:container'] = area_original

                        remainder = way_2d.subtract(area_original)
                        #remainder = remainder.material(ddd.mats.pavement)
                        #area.extra['ddd:area:type'] = 'sidewalk'
                        remainder.name = "Path %s to area %s" % (way_2d.name, area_original.name)
                        remainder = remainder.clean(eps=0.001)

                        way_2d.replace(intersection)
                        # Delay appending
                        for c in remainder.individualize(always=True).children:
                            to_append.append(c)
                            to_process.append(c)

                        #to_process.append(way_2d)

            if to_append:
                for a in to_append:
                    ways_2d.append(a)

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
        underwater_area.extra['ddd:layer'] = '0'
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


    def link_items_to_areas(self, areas_2d, items_1d):

        logger.info("Linking %d items to %d areas.", len(items_1d.children), len(areas_2d.children))
        # TODO: Link to building parts, inspect facade, etc.

        #logger.debug("Sorting 2D areas (%d).", len(areas_2d))

        #items_1d_query = STRtree(items_1d.)

        for item in items_1d.children:
            if not self.osm.area_crop2.contains(item): continue
            # Find closest building
            #point = feature.copy(name="Point: %s" % (feature.extra.get('name', None)))
            areas = areas_2d.select(func=lambda a: a.contains(item)).children
            if areas:
                areas.sort(key=lambda a: a.geom.area if a.geom else float("inf"))  # extra['ddd:area:area'])
                #logger.debug("Assigning point feature to area: %s -> %s", item, areas[0])
                item.set('ddd:area:container', areas[0])
            else:
                #logger.debug("Point feature with no container area: %s", item)
                pass

