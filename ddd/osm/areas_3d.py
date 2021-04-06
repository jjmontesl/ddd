# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging

from ddd.core.exception import DDDException
from ddd.ddd import DDDObject2, DDDObject3
from ddd.ddd import ddd
from ddd.geo import terrain
from ddd.pack.sketchy import plants, urban, sports


# Get instance of logger for this module
logger = logging.getLogger(__name__)

class Areas3DOSMBuilder():

    max_trees = None

    def __init__(self, osmbuilder):

        self.osm = osmbuilder


    '''
    def generate_coastline_3d(self, area_crop):


        logger.info("Generating water and land areas according to coastline: %s", (area_crop.bounds))

        #self.water_3d = terrain.terrain_grid(self.area_crop.bounds, height=0.1, detail=200.0).translate([0, 0, 1]).material(mat_sea)

        water = ddd.rect(area_crop.bounds, name="Ground")
        coastlines = []
        coastlines_1d = []

        for way in self.osm.items_1d.children:
            if way.extra.get('osm:natural') == 'coastline':
                coastlines_1d.append(way)
                coastlines.append(way.buffer(0.01))
        #for way in self.osm.features.children:
        #    if way.properties.get('natural') == 'coastline':
        #        coastlines_1d.append(ddd.shape(way.geometry))
        #        coastlines.append(ddd.shape(way.geometry).buffer(0.1))

        logger.debug("Coastlines: %s", (coastlines_1d, ))
        if not coastlines:
            logger.info("No coastlines in the feature set.")
            return

        coastlines = ddd.group(coastlines)
        coastlines_1d = ddd.group(coastlines_1d)
        coastline_areas = water.subtract(coastlines)
        #coastline_areas.save("/tmp/test.svg")
        #coastline_areas.dump()

        # Generate coastline
        if coastlines_1d.children:
            coastlines_3d = coastlines_1d.intersection(water)
            coastlines_3d = coastlines_3d.individualize().extrude(10.0).translate([0, 0, -10.0])
            coastlines_3d = terrain.terrain_geotiff_elevation_apply(coastlines_3d, self.osm.ddd_proj)
            coastlines_3d = ddd.uv.map_cubic(coastlines_3d)
            coastlines_3d.name = 'Coastline: %s' % coastlines_3d.name
            self.osm.other_3d.append(coastlines_3d)


        areas = []
        areas_2d = []
        geoms = coastline_areas.geom.geoms if coastline_areas.geom.type == 'MultiPolygon' else [coastline_areas.geom]
        for water_area_geom in geoms:
            # Find closest point, closest segment, and angle to closest segment
            water_area_geom = ddd.shape(water_area_geom).clean(eps=0.01).geom

            if not water_area_geom.is_simple:
                logger.error("Invalid water area geometry (not simple): %s", water_area_geom)
                continue

            water_area_point = water_area_geom.representative_point()
            p, segment_idx, segment_coords_a, segment_coords_b, closest_obj, closest_d = coastlines_1d.closest_segment(ddd.shape(water_area_point))
            pol = LinearRing([segment_coords_a, segment_coords_b, water_area_point.coords[0]])

            if not pol.is_ccw:
                #area_3d = area_2d.extrude(-0.2)
                area_2d = ddd.shape(water_area_geom).buffer(0.10).clean(eps=0.01)
                area_2d.validate()
                area_2d = area_2d.material(ddd.mats.sea)

                area_3d = area_2d.triangulate().translate([0, 0, -0.5])
                area_3d.extra['ddd:collider'] = False
                area_3d.extra['ddd:shadows'] = False
                area_3d.extra['ddd:occluder'] = False
                areas_2d.append(area_2d)
                areas.append(area_3d)

        if areas:
            self.osm.water_3d = ddd.group(areas)
            self.osm.water_2d = ddd.group(areas_2d)
        else:
            logger.debug("No water areas from coastline generated.")
        pass
    '''

    '''
    def generate_ground_3d(self, area_crop):

        logger.info("Generating 3D terrain (bounds: %s)", area_crop.bounds)

        terr = self.osm.ground_2d

        # The buffer is fixing a core segment violation :/
        #terr.save("/tmp/test.svg")
        #terr.dump()
        #terr.show()
        #terr = ddd.group([DDDObject2(geom=s.buffer(0.5).buffer(-0.5)) for s in terr.geom.geoms if not s.is_empty])

        #terr.save("/tmp/test.svg")
        #terr = terr.triangulate()
        try:
            #terr = terr.individualize()
            #terr.validate()
            logger.warning("There's a buffer(0.000-0.001) operation which shouldn't be here: improve and use 'clean()'.")
            terr = terr.buffer(0.001)
            #terr = terr.buffer(0.0)
            #terr = terr.clean(eps=0.001)

            #terr = terr.extrude(0.3)
            terr = terr.triangulate()
        except ValueError as e:
            logger.error("Cannot generate terrain (FIXME): %s", e)
            raise DDDException("Coould not generate terrain: %s" % e, ddd_obj=terr)

        terr = terrain.terrain_geotiff_elevation_apply(terr, self.osm.ddd_proj)

        self.osm.ground_3d.append(terr)
    '''

    '''
    def generate_areas_3d(self, areas_2d):

        # TODO: Move to pipeline
        logger.info("Generating 3D areas (%d)", len(areas_2d.children))

        areas_3d = ddd.group3(name="Areas")

        for area_2d in areas_2d.children:

            #area_2d = area_2d.clean_replace(eps=0.0)
            #if (not area_2d or not area_2d.geom): continue

            try:
                area_2d.validate()
            except Exception as e:
                logger.error("Could not generate invalid area %s: %s", area_2d, e)
                continue

            try:
                if area_2d.extra.get('ddd:area:type', 'default') == 'default':
                    area_3d = self.generate_area_3d(area_2d)
                elif area_2d.extra.get('ddd:area:type', 'default') == 'stairs':
                    area_3d = self.generate_area_3d(area_2d)
                elif area_2d.extra['ddd:area:type'] == 'sidewalk':
                    area_3d = self.generate_area_3d(area_2d)
                elif area_2d.extra['ddd:area:type'] == 'park':
                    area_3d = self.generate_area_3d(area_2d)
                elif area_2d.extra['ddd:area:type'] == 'steps':
                    area_3d = self.generate_area_3d(area_2d)
                    # TODO: Raise areas to base_height (area.extra['ddd:area:container'] ?)
                elif area_2d.extra['ddd:area:type'] == 'pitch':
                    area_3d = self.generate_area_3d_pitch(area_2d)
                elif area_2d.extra['ddd:area:type'] == 'water':
                    area_3d = self.generate_area_3d_water(area_2d)
                elif area_2d.extra['ddd:area:type'] == 'sea':
                    area_3d = self.generate_area_3d_water(area_2d)
                elif area_2d.extra['ddd:area:type'] == 'underwater':
                    area_3d = self.generate_area_3d_underwater(area_2d)
                else:
                    logger.warning("Area type undefined: %s", area_2d.extra.get('ddd:area:type', None))
                    raise AssertionError("Area type undefined: %s" % (area_2d.extra.get('ddd:area:type', None)))

                if area_3d:
                    areas_3d.append(area_3d)

            except ValueError as e:
                logger.error("Could not generate area %s: %s", area_2d, e)
                raise
            except IndexError as e:
                logger.error("Could not generate area %s: %s", area_2d, e)
                raise
            except DDDException as e:
                logger.error("Could not generate area %s: %s", area_2d, e)
                raise

        return areas_3d
    '''

    def generate_area_3d(self, area_2d):

        if area_2d.get('ddd:area:type', None) == 'pitch':
            return self.generate_area_3d_pitch(area_2d)
        elif area_2d.get('ddd:area:type', None) == 'water':
            return self.generate_area_3d_water(area_2d)
        elif area_2d.get('ddd:area:type', None) == 'sea':
            return self.generate_area_3d_water(area_2d)
        elif area_2d.get('ddd:area:type', None) == 'underwater':
            return self.generate_area_3d_underwater(area_2d)
        elif area_2d.get('ddd:area:type', None) == 'railway':
            return self.osm.ways3.generate_way_3d_railway(area_2d)
        elif area_2d.get('ddd:area:type', None) == 'ignore':
            return None
        else:
            return self.generate_area_3d_gen(area_2d)

    def generate_area_3d_gen(self, area_2d):

        if area_2d.geom is not None and area_2d.geom.type != "LineString" and area_2d.geom.type:

            if area_2d.geom.type in ('GeometryCollection', 'MultiPolygon'):
                logger.debug("Generating area 3d as separate areas as it is a GeometryCollection: %s", area_2d)
                # FIXME: We might do this in extrude_step, like we do in triangulate and extrude, but difficult as it is in steps.
                # But also, we should have an individualize that work, correct iterators, and a generic cleanup/flatten method
                # to flatten areas, which might solve this.
                areas_3d = []
                for a in area_2d.individualize().clean_replace().children:
                    areas_3d.append(self.generate_area_3d(a))
                return ddd.group3(areas_3d, extra=area_2d.extra)

            if area_2d.extra.get('ddd:area:type', None) == 'park':

                area_3d = area_2d.extrude_step(area_2d.buffer(-1.0), 0.1, base=False, method=ddd.EXTRUSION_METHOD_SUBTRACT)
                area_3d = area_3d.extrude_step(area_2d.buffer(-3.0), 0.1, method=ddd.EXTRUSION_METHOD_SUBTRACT)

                # Grass
                # TODO: Add in a separate (optional) pass
                if False:
                    # For volumetric grass, as described by: https://www.bruteforce-games.com/post/grass-shader-devblog-04
                    grass_layers = []
                    colors = ['#000000', '#222222', '#444444', '#666666', '#888888', '#aaaaaa', '#cccccc', '#eeeeee']
                    for i in range(8):
                        grass_layer = area_3d.copy(name="Grass %d: %s" % (i, area_3d.name))
                        grass_layer = grass_layer.material(ddd.material(name="VolumetricGrass", color=colors[i], extra={'ddd:export-as-marker': True}))
                        #grass_layer.extra['ddd:vertex_colors'] =
                        grass_layer = grass_layer.translate([0, 0, 0.05 * i])
                        #grass_layer = terrain.terrain_geotiff_elevation_apply(grass_layer, self.osm.ddd_proj)
                        grass_layer.extra['ddd:shadows'] = False
                        grass_layer.extra['ddd:collider'] = False
                        grass_layer.extra['ddd:occluder'] = False
                        grass_layers.append(grass_layer)
                    #self.osm.other_3d.append(grass_layers)  #ddd.group3([area_3d, grass_layers])
                    area_3d.children.extend(grass_layers)


                #area_3d = ddd.group([area_2d.triangulate().translate([0, 0, 0.0]),
                #                     area_2d.buffer(-1.0).triangulate().translate([0, 0, 0.2]),
                #                     area_2d.buffer(-3.0).triangulate().translate([0, 0, 0.3])])

                #area_3d = area_3d.translate([0, 0, 0])

            elif area_2d.extra.get('ddd:area:type', None) == 'steps':

                area_3d = area_2d.extrude_step(area_2d, area_2d.extra['ddd:steps:height'], base=False)
                for stepidx in range(1, area_2d.extra['ddd:steps:count'] + 1):
                    area_3d = area_3d.extrude_step(area_2d.buffer(-area_2d.extra['ddd:steps:depth'] * stepidx), 0, method=ddd.EXTRUSION_METHOD_SUBTRACT)
                    area_3d = area_3d.extrude_step(area_2d.buffer(-area_2d.extra['ddd:steps:depth'] * stepidx), area_2d.extra['ddd:steps:height'], method=ddd.EXTRUSION_METHOD_SUBTRACT)

                # TODO: Crop in 3D (or as a workaround fake it as centroid cropping)

            elif area_2d.extra.get('ddd:area:type', None) == 'sidewalk':

                area_3d = None

                try:
                    height = area_2d.extra.get('ddd:height', 0.2)
                    #area_3d = area_2d.extrude(-0.5 - height).translate([0, 0, height])
                    #area_3d = ddd.uv.map_cubic(area_3d)

                    if True:
                        try:
                            interior = area_2d.get('ddd:crop:original').buffer(-0.3).intersection(self.osm.area_crop2)
                            if not interior.is_empty():
                                area_3d = interior.extrude(-0.5 - height).translate([0, 0, height])
                                area_3d = ddd.uv.map_cubic(area_3d)
                                kerb_3d = area_2d.get('ddd:crop:original').subtract(interior).intersection(self.osm.area_crop2).extrude(-0.5 - height).translate([0, 0, height])
                                kerb_3d = ddd.uv.map_cubic(kerb_3d).material(ddd.mats.cement)
                                #if area_3d.mesh:
                                #    area_3d = terrain.terrain_geotiff_elevation_apply(area_3d, self.osm.ddd_proj)
                                #    kerb_3d = terrain.terrain_geotiff_elevation_apply(kerb_3d, self.osm.ddd_proj).material(ddd.mats.cement)
                                #area_3d.append(kerb_3d)
                                #kerb_3d = terrain.terrain_geotiff_elevation_apply(kerb_3d, self.osm.ddd_proj)
                                area_3d.append(kerb_3d)
                            else:
                                logger.info("Cannot create kerb (empty interior) for area: %s", area_2d)
                                area_3d = None
                        except Exception as e:
                            logger.info("Error creating kerb for area %s: %s", area_2d, e)
                            area_3d = None

                    # If no kerb or kerb could not be generated, just generate the area:
                    if area_3d is None:
                        area_3d = area_2d.extrude(-0.5 - height).translate([0, 0, height])
                        area_3d = ddd.uv.map_cubic(area_3d)

                except Exception as e:
                    logger.error("Could not generate area: %s (%s)", e, area_2d)
                    area_3d = DDDObject3()

            else:
                try:
                    height = area_2d.extra.get('ddd:height', 0.2)
                    if height:
                        area_3d = area_2d.extrude(-0.5 - height).translate([0, 0, height])
                    else:
                        area_3d = area_2d.triangulate()
                    area_3d = ddd.uv.map_cubic(area_3d)
                except Exception as e:
                    logger.error("Could not generate area: %s (%s)", e, area_2d)
                    area_3d = DDDObject3()

        else:
            if len(area_2d.children) == 0:
                logger.warning("Null area geometry (children?): %s", area_2d)
            area_3d = DDDObject3()

        # Test (doesn't work, subdividing causes bad behavior in large trams):
        area_3d = area_3d.subdivide_to_size(20.0)
        area_3d = ddd.uv.map_cubic(area_3d)

        # Apply elevation
        area_3d = self.generate_area_3d_apply_elevation(area_2d, area_3d)

        area_3d.extra = dict(area_2d.extra)
        area_3d.children.extend( [self.generate_area_3d(c) for c in area_2d.children] )

        return area_3d

    def generate_area_3d_apply_elevation(self, area_2d, area_3d):

        apply_layer_height = True

        if area_3d.mesh or area_3d.children:
            #height = area_2d.extra.get('ddd:height', 0.2)
            area_elevation = area_2d.extra.get('ddd:area:elevation', 'geotiff')
            if area_elevation == 'geotiff':
                area_3d = terrain.terrain_geotiff_elevation_apply(area_3d, self.osm.ddd_proj)
            elif area_elevation == 'min':
                area_3d = terrain.terrain_geotiff_min_elevation_apply(area_3d, self.osm.ddd_proj)
            elif area_elevation == 'max':
                area_3d = terrain.terrain_geotiff_max_elevation_apply(area_3d, self.osm.ddd_proj)
            elif area_elevation == 'path':
                # logger.debug("3D layer transition: %s", way)
                # if way.extra['ddd:layer_transition']:
                if ('way_1d' in area_3d.extra):
                    path = area_3d.extra['way_1d']
                    vertex_func = self.osm.ways1.get_height_apply_func(path)
                    area_3d = area_3d.vertex_func(vertex_func)
                    apply_layer_height = False

                area_3d = terrain.terrain_geotiff_elevation_apply(area_3d, self.osm.ddd_proj)

            elif area_elevation == 'water':
                apply_layer_height = False
                pass
            elif area_elevation == 'none':
                pass
            else:
                raise AssertionError()

        if apply_layer_height:
            layer = str(area_3d.extra.get('ddd:layer', area_3d.extra.get('osm:layer', 0)))
            base_height = float(area_3d.extra.get('ddd:base_height', self.osm.ways1.layer_height(layer)))
            area_3d = area_3d.translate([0, 0, base_height])

        return area_3d


    def generate_area_3d_pitch(self, area_2d):

        if area_2d.geom is None or area_2d.geom.is_empty:
            return None

        area_2d_orig = area_2d.extra.get('ddd:crop:original')  #, area_2d)

        #logger.debug("Pitch: %s", area_2d)
        area_3d = self.generate_area_3d_gen(area_2d)

        # TODO: pass size then adapt to position and orientation, easier to construct and reuse
        # TODO: get area uncropped (create a cropping utility that stores the original area)

        sport = area_2d.extra.get('ddd:sport', None)

        lines = None
        if sport == 'tennis':
            lines = sports.field_lines_area(area_2d_orig, sports.tennis_field_lines, padding=3.0)
        elif sport == 'basketball':
            lines = sports.field_lines_area(area_2d_orig, sports.basketball_field_lines, padding=2.0)
        elif sport == 'gymnastics':
            #lines = sports.field_lines_area(area_2d_orig, sports.basketball_field_lines, padding=2.0)
            lines = ddd.group3()
        elif sport in ('soccer', 'futsal'):
            lines = sports.field_lines_area(area_2d_orig, sports.football_field_lines, padding=1.25)
        else:
            # No sport assigned
            lines = ddd.group3()

        if lines:
            lines = terrain.terrain_geotiff_elevation_apply(lines, self.osm.ddd_proj).translate([0, 0, 0.15])
            height = area_2d.extra.get('ddd:height', 0.2)
            lines = lines.translate([0, 0, height])

            area_3d = ddd.group3([area_3d, lines])
        else:
            logger.debug("No pitch lines generated.")

        return area_3d

    def generate_area_3d_water(self, area_2d):
        area_3d = self.generate_area_3d_gen(area_2d)

        # Move water down, to account for waves
        area_3d = area_3d.translate([0, 0, -0.5])
        return area_3d

    def generate_area_3d_underwater(self, area_2d):
        logger.info ("Generating underwater for: %s", area_2d)
        #area_2d.dump()
        areas_2d = area_2d.individualize().flatten().clean()
        #area_2d.show()

        result = ddd.group3()
        for area_2d in areas_2d.children:

            area_2d = area_2d.clean()
            try:
                area_2d.validate()
            except DDDException as e:
                logger.error("Could not generate underwater area (invalid area %s): %s", area_2d, e)
                continue

            if area_2d.geom.type == "LineString":
                logger.error("Could not generate underwater area (area is line): %s", area_2d)
                continue

            try:
                area_3d = area_2d.extrude_step(area_2d.buffer(-1.0), -0.3, base=False, method=ddd.EXTRUSION_METHOD_SUBTRACT)
                area_3d = area_3d.extrude_step(area_2d.buffer(-2.0), -0.5, method=ddd.EXTRUSION_METHOD_SUBTRACT)
                area_3d = area_3d.extrude_step(area_2d.buffer(-4.0), -1.0, method=ddd.EXTRUSION_METHOD_SUBTRACT)
                area_3d = area_3d.extrude_step(area_2d.buffer(-6.0), -0.5, method=ddd.EXTRUSION_METHOD_SUBTRACT)
                area_3d = area_3d.extrude_step(area_2d.buffer(-9.0), -0.4, method=ddd.EXTRUSION_METHOD_SUBTRACT)
                area_3d = area_3d.extrude_step(area_2d.buffer(-12.0), -0.3, method=ddd.EXTRUSION_METHOD_SUBTRACT)
            except Exception as e:
                logger.warn("Exception extruding underwater area (reduced LinearRings need caring): %s", e)
                print(area_2d.geom)
                print(area_2d.buffer(-1.0).geom)
                area_3d = None

            if area_3d is None or area_3d.extra['_extrusion_steps'] < 3:
                logger.debug("Could not extrude underwater area softly. Extruding abruptly.")
                area_3d = area_2d.extrude_step(area_2d.buffer(-0.05), -1.0, base=False, method=ddd.EXTRUSION_METHOD_SUBTRACT)
                area_3d = area_3d.extrude_step(area_2d.buffer(-0.15), -0.5, method=ddd.EXTRUSION_METHOD_SUBTRACT)
                area_3d = area_3d.extrude_step(area_2d.buffer(-0.3), -0.5, method=ddd.EXTRUSION_METHOD_SUBTRACT)
                area_3d = area_3d.extrude_step(area_2d.buffer(-1.0), -0.5, method=ddd.EXTRUSION_METHOD_SUBTRACT)
            if area_3d.extra['_extrusion_steps'] < 1:
                logger.warn("Could not extrude underwater area: %s", area_3d)
                area_3d = area_3d.translate([0, 0, -1.0])
            if area_3d: result.append(area_3d)

        result = terrain.terrain_geotiff_elevation_apply(result, self.osm.ddd_proj)
        #result.show()

        return result
