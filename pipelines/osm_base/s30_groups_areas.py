# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020


from ddd.ddd import ddd
from ddd.pipeline.decorators import dddtask




@dddtask(order="30.50.20.+", log=True)
def osm_groups_areas(root, osm, logger):

    logger.info("Processing 2D areas.")

    # Split and junctions first?
    # Possibly: metadata can depend on that, and it needs to be done if it will be done anyway

    # Otherwise: do a pre and post step, and do most things in post (everything not needed for splitting)

    pass

@dddtask(path="/Areas/*")
def osm_groups_areas_default_name(obj, osm):
    """Set default name."""
    name = "Area: " + (obj.extra.get('osm:name', obj.extra.get('osm:id')))
    obj.name = name
    #obj.extra['ddd:ignore'] = True

@dddtask(path="/Areas/*")
def osm_groups_areas_default_material(obj, osm):
    """Assign default material."""
    obj = obj.material(ddd.mats.terrain)
    return obj

@dddtask(path="/Areas/*")
def osm_groups_areas_default_data(obj, osm):
    """Sets default data."""
    obj.extra['ddd:area:weight'] = 100  # Lowest
    obj.extra['ddd:area:height'] = 0  # Lowest
    obj.extra['ddd:area:container'] = None
    obj.extra['ddd:area:contained'] = []
    obj.prop_set('ddd:area:type', default=None)


@dddtask(path="/Areas/*", select='["osm:leisure" ~ "park|garden"]')
def osm_groups_areas_leisure_park(obj, osm):
    """Define area data."""
    obj.extra['ddd:area:type'] = "park"
    obj.extra['ddd:aug:itemfill:density'] = 0.0025
    obj.extra['ddd:aug:itemfill:types'] = {'default': 1, 'palm': 0.001}
    obj = obj.material(ddd.mats.park)
    return obj



"""
def generate_areas_2d(self):



        logger.info("Sorting 2D areas  (%d).", len(areas))
        areas.sort(key=lambda a: a.extra['ddd:area:area'])

        for idx in range(len(areas)):
            area = areas[idx]
            for larger in areas[idx + 1:]:
                if larger.contains(area):
                    #logger.debug("Area %s contains %s.", larger, area)
                    area.extra['ddd:area:container'] = larger
                    larger.extra['ddd:area:contained'].append(area)
                    break

        # Union all roads in the plane to subtract
        logger.info("Generating 2D areas subtract.")
        union = ddd.group([self.osm.ways_2d['0'], self.osm.ways_2d['-1a']]).union()  # , self.osm.areas_2d
        #union = ddd.group([self.osm.ways_2d['0'], self.osm.ways_2d['-1a']])

        logger.info("Generating 2D areas (%d)", len(areas))
        for narea in areas:
        #for feature in self.osm.features:
            feature = narea.extra['osm:feature']

            if narea.geom.type == 'Point': continue

            narea.extra['ddd:area:original'] = narea  # Before subtracting any internal area

            '''
            # Subtract areas contained (use contained relationship)
            for contained in narea.extra['ddd:area:contained']:
                narea = narea.subtract(contained)
            '''

            area = None
            if narea.extra.get('osm:leisure', None) in ('park', 'garden'):
                narea = narea.subtract(ddd.group2(narea.extra['ddd:area:contained']))
                narea = narea.subtract(union)
                area = self.generate_area_2d_park(narea)

            elif narea.extra.get('osm:landuse', None) in ('forest', ):
                narea = narea.subtract(ddd.group2(narea.extra['ddd:area:contained']))
                narea = narea.subtract(union)
                area = self.generate_area_2d_forest(narea)
            elif narea.extra.get('osm:landuse', None) in ('vineyard', ):
                narea = narea.subtract(ddd.group2(narea.extra['ddd:area:contained']))
                narea = narea.subtract(union)
                area = self.generate_area_2d_vineyard(narea)

            elif narea.extra.get('osm:natural', None) in ('wood', ):
                narea = narea.subtract(ddd.group2(narea.extra['ddd:area:contained']))
                narea = narea.subtract(union)
                area = self.generate_area_2d_forest(narea)
            elif narea.extra.get('osm:natural', None) in ('wetland', ):
                narea = narea.subtract(ddd.group2(narea.extra['ddd:area:contained']))
                narea = narea.subtract(union)
                area = self.generate_area_2d_wetland(narea)
            elif narea.extra.get('osm:natural', None) in ('beach', ):
                narea = narea.subtract(ddd.group2(narea.extra['ddd:area:contained']))
                narea = narea.subtract(union)
                area = self.generate_area_2d_beach(narea)
            elif narea.extra.get('osm:landuse', None) in ('grass', ):
                narea = narea.subtract(ddd.group2(narea.extra['ddd:area:contained']))
                narea = narea.subtract(union)
                area = self.generate_area_2d_park(narea)

            elif narea.extra.get('osm:amenity', None) in ('parking', ):
                narea = narea.subtract(ddd.group2(narea.extra['ddd:area:contained']))
                narea = narea.subtract(union)
                area = self.generate_area_2d_parking(narea)

            elif (narea.extra.get('osm:public_transport', None) in ('platform', ) or
                  narea.extra.get('osm:railway', None) in ('platform', )):
                narea = narea.subtract(ddd.group2(narea.extra['ddd:area:contained']))
                narea = narea.subtract(union)
                area = self.generate_area_2d_platform(narea)

            elif narea.extra.get('osm:tourism', None) in ('artwork', ):
                narea = narea.subtract(ddd.group2(narea.extra['ddd:area:contained']))
                narea = narea.subtract(union)
                area = self.generate_area_2d_artwork(narea)

            elif narea.extra.get('osm:leisure', None) in ('pitch', ):  # Cancha
                narea = narea.subtract(ddd.group2(narea.extra['ddd:area:contained']))
                area = self.generate_area_2d_pitch(narea)
            elif narea.extra.get('osm:landuse', None) in ('railway', ):
                narea = narea.subtract(ddd.group2(narea.extra['ddd:area:contained']))
                area = self.generate_area_2d_railway(narea)
            elif narea.extra.get('osm:landuse', None) in ('brownfield', ):
                narea = narea.subtract(ddd.group2(narea.extra['ddd:area:contained']))
                area = self.generate_area_2d_unused(narea)
                narea = narea.subtract(union)
            elif narea.extra.get('osm:amenity', None) in ('school', ):
                narea = narea.subtract(ddd.group2(narea.extra['ddd:area:contained']))
                narea = narea.subtract(union)
                area = self.generate_area_2d_school(narea)
            elif (narea.extra.get('osm:waterway', None) in ('riverbank', 'stream') or
                  narea.extra.get('osm:natural', None) in ('water', ) or
                  narea.extra.get('osm:water', None) in ('river', )):
                #narea = narea.subtract(ddd.group2(narea.extra['ddd:area:contained']))
                #narea = narea.subtract(union)
                area = self.generate_area_2d_riverbank(narea)
            else:
                logger.debug("Unknown area: %s", feature)

            #elif feature['properties'].get('amenity', None) in ('fountain', ):
            #    area = self.generate_area_2d_school(feature)

            if area:
                logger.debug("Area: %s", area)
                area = area.subtract(union)

                self.osm.areas_2d.append(area)
                #self.osm.areas_2d.children.extend(area.individualize().children)
"""

