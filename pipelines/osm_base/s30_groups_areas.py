# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020


from ddd.ddd import ddd
from ddd.pipeline.decorators import dddtask



@dddtask(order="30.50.20.+", log=True)
def osm_groups_areas(root, osm, logger):
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


@dddtask(path="/Areas/*", select='["osm:leisure" = "park"]')
def osm_groups_areas_leisure_park(obj, osm):
    """Define area data."""
    obj.name = "Park: %s" % obj.name
    obj.extra['ddd:area:type'] = "park"
    obj.extra['ddd:aug:itemfill:density'] = 0.0025
    obj.extra['ddd:aug:itemfill:types'] = {'default': 1, 'palm': 0.001}
    obj = obj.material(ddd.mats.park)
    return obj

@dddtask(path="/Areas/*", select='["osm:highway" = "pedestrian"]["osm:area" = "yes"]')
def osm_groups_areas_highway_pedestrian(obj, osm):
    """Define area data."""
    obj.name = "Pedestrian area: %s" % obj.name
    obj.extra['ddd:area:type'] = "default"
    obj = obj.material(ddd.mats.pathwalk)
    return obj

@dddtask(path="/Areas/*", select='["osm:highway" = "footway"]["osm:area" = "yes"]')
def osm_groups_areas_highway_footway(obj, osm):
    """Define area data."""
    obj.name = "Footway area: %s" % obj.name
    obj.extra['ddd:area:type'] = "default"
    obj = obj.material(ddd.mats.pathwalk)  # TODO: Footways/paths are not always dirt
    return obj

@dddtask(path="/Areas/*", select='["osm:leisure" = "garden"]')
def osm_groups_areas_leisure_garden(obj, osm):
    """Define area data."""
    obj.name = "Garden: %s" % obj.name
    obj.extra['ddd:area:type'] = "park"
    obj.extra['ddd:aug:itemfill:density'] = 0.0
    obj.extra['ddd:aug:itemfill:types'] = {'default': 1, 'palm': 0.001}
    obj = obj.material(ddd.mats.garden)
    return obj

@dddtask(path="/Areas/*", select='["osm:landuse" = "forest"]')
def osm_groups_areas_landuse_forest(obj, osm):
    """Define area data."""
    obj.name = "Forest: %s" % obj.name
    obj.extra['ddd:area:type'] = "park"
    obj.extra['ddd:aug:itemfill:density'] = 0.006
    obj.extra['ddd:aug:itemfill:types'] = {'default': 1, 'reed': 0.5}
    obj = obj.material(ddd.mats.forest)
    return obj

@dddtask(path="/Areas/*", select='["osm:landuse" = "vineyard"]')
def osm_groups_areas_landuse_vineyard(obj, osm):
    """Define area data."""
    obj.name = "Vineyard: %s" % obj.name
    obj.extra['ddd:area:type'] = "default"
    obj.extra['ddd:aug:itemfill:density'] = 0.001
    obj.extra['ddd:aug:itemfill:types'] = {'default': 1}
    obj = obj.material(ddd.mats.terrain)
    return obj

@dddtask(path="/Areas/*", select='["osm:landuse" = "grass"]')
def osm_groups_areas_landuse_grass(obj, osm):
    """Define area data."""
    obj.name = "Grass: %s" % obj.name
    obj.extra['ddd:area:type'] = "park"
    obj.extra['ddd:aug:itemfill:density'] = 0.0
    obj = obj.material(ddd.mats.grass)
    return obj

@dddtask(path="/Areas/*", select='["osm:landuse" = "brownfield"]')
def osm_groups_areas_landuse_brownfield(obj, osm):
    """Define area data."""
    obj.name = "Brownfield: %s" % obj.name
    obj.extra['ddd:area:type'] = "park"
    obj = obj.material(ddd.mats.dirt)
    return obj

@dddtask(path="/Areas/*", select='["osm:landuse" = "greenfield"]')
def osm_groups_areas_landuse_greenfield(obj, osm):
    """Define area data."""
    obj.name = "Greenfield: %s" % obj.name
    obj.extra['ddd:area:type'] = "park"
    obj.extra['ddd:aug:itemfill:density'] = 0.001
    obj.extra['ddd:aug:itemfill:types'] = {'default': 1}
    obj = obj.material(ddd.mats.terrain)
    return obj

@dddtask(path="/Areas/*", select='["osm:landuse" = "allotments"]')
def osm_groups_areas_landuse_allotments(obj, osm):
    """Define area data."""
    obj.name = "Allotments: %s" % obj.name
    obj.extra['ddd:area:type'] = "park"
    obj = obj.material(ddd.mats.terrain)

    obj.extra['ddd:aug:itemfill:density'] = 0.001
    obj.extra['ddd:aug:itemfill:types'] = {'reed': 1}

    # Distribute crops
    #ddd.align.matrix_grid(obj.bounds(ddd.point())).intersection(obj)
    return obj

@dddtask(path="/Areas/*", select='["osm:natural" = "fell"]')
def osm_groups_areas_natural_fell(obj, osm):
    """Define area data."""
    obj.name = "Fell: %s" % obj.name
    obj.extra['ddd:area:type'] = "park"
    obj.extra['ddd:aug:itemfill:density'] = 0
    obj = obj.material(ddd.mats.forest)
    return obj

@dddtask(path="/Areas/*", select='["osm:natural" = "wood"]')
def osm_groups_areas_natural_wood(obj, osm):
    """Define area data."""
    obj.name = "Wood: %s" % obj.name
    obj.extra['ddd:area:type'] = "park"
    obj.extra['ddd:aug:itemfill:density'] = 0.006
    obj.extra['ddd:aug:itemfill:types'] = {'default': 1, 'reed': 0.25}
    obj = obj.material(ddd.mats.forest)
    return obj

@dddtask(path="/Areas/*", select='["osm:natural" = "wetland"]')
def osm_groups_areas_natural_wetland(obj, osm):
    """Define area data."""
    obj.name = "Wetland: %s" % obj.name
    obj.extra['ddd:area:type'] = "park"
    obj.extra['ddd:aug:itemfill:density'] = 0.008
    obj.extra['ddd:aug:itemfill:types'] = {'reed': 1, 'default': 0.01}
    obj = obj.material(ddd.mats.wetland)
    return obj

@dddtask(path="/Areas/*", select='["osm:natural" = "beach"]')
def osm_groups_areas_natural_beach(obj, osm):
    """Define area data."""
    obj.name = "Beach: %s" % obj.name
    obj.extra['ddd:area:type'] = "default"  # sand / dunes
    obj = obj.material(ddd.mats.sand)
    return obj

@dddtask(path="/Areas/*", select='["osm:natural" = "sand"]')
def osm_groups_areas_natural_sand(obj, osm):
    """Define area data."""
    # Note that golf:bunker is also usually marked as natural:sand
    obj.name = "Sand: %s" % obj.name
    obj.extra['ddd:area:type'] = "default"  # sand / dunes
    obj = obj.material(ddd.mats.sand)
    return obj

@dddtask(path="/Areas/*", select='["osm:golf" = "bunker"]')
def osm_groups_areas_golf_bunker(obj, osm):
    """Define area data."""
    # Note that golf:bunker is also usually marked as natural:sand
    obj.name = "Bunker: %s" % obj.name
    obj.extra['ddd:area:type'] = "bunker"  # sand / dunes
    return obj

@dddtask(path="/Areas/*", select='["osm:natural" = "bare_rock"]')
def osm_groups_areas_natural_bare_rock(obj, osm):
    """Define area data."""
    # Note that golf:bunker is also usually marked as natural:sand
    obj.name = "Bare Rock: %s" % obj.name
    obj.extra['ddd:area:type'] = "default"  # sand / dunes
    obj = obj.material(ddd.mats.rock)
    obj.extra['ddd:height'] = 0.40
    return obj


@dddtask(path="/Areas/*", select='["osm:amenity" = "parking"]')
def osm_groups_areas_amenity_parking(obj, osm):
    """Define area data."""
    obj.name = "Parking: %s" % obj.name
    obj.extra['ddd:area:type'] = "default"
    #obj.extra['ddd:height'] = 0.1
    obj = obj.material(ddd.mats.asphalt)
    return obj

@dddtask(path="/Areas/*", select='["osm:leisure" = "pitch"]')
def osm_groups_areas_leisure_pitch(obj, osm):
    """Define area data."""
    obj.name = "Pitch: %s" % obj.name
    obj.extra['ddd:area:type'] = "pitch"
    obj = obj.material(ddd.mats.pitch)
    return obj

@dddtask(path="/Areas/*", select='["osm:leisure" = "playground"]["geom:type" ~ "Polygon|MultiPolygon|GeometryCollection"]')
def osm_groups_items_areas_leisure_playground(obj, root, osm):
    """Define area data. Children game objects are defined in items_areas."""
    print(obj)
    obj.name = "Playground: %s" % obj.name
    obj.extra['ddd:area:type'] = "default"
    obj.extra['ddd:height'] = 0.15
    obj = obj.material(ddd.mats.pitch_blue)
    return obj

@dddtask(path="/Areas/*", select='["osm:leisure" = "track"]')
def osm_groups_areas_leisure_track(obj, osm):
    """Define area data."""
    obj.name = "Track: %s" % obj.name
    obj.extra['ddd:area:type'] = "default"
    obj = obj.material(ddd.mats.pitch_red)
    return obj

@dddtask(path="/Areas/*", select='["osm:leisure" = "golf_course"]')
def osm_groups_areas_leisure_golf_course(obj, osm):
    """Define area data."""
    obj.name = "Golf Course: %s" % obj.name
    #obj.extra['ddd:area:type'] = "default"
    obj.extra['ddd:area:type'] = "park"  # should be default, or golf (for the irregaularity), but currently default is raising height :?
    obj = obj.material(ddd.mats.park)
    return obj

@dddtask(path="/Areas/*", select='["osm:golf" = "green"]')
def osm_groups_areas_leisure_golf_green(obj, osm):
    """Define area data."""
    obj.name = "Golf Green: %s" % obj.name
    obj.extra['ddd:area:type'] = "park"  # should be default, or golf (for the irregaularity), but currently default is raising height :?
    # TODO: Disable grass blades generation here using augmentation metadata (grass blades are currently hard coded in s55_plants)
    obj = obj.material(ddd.mats.grass)
    return obj

@dddtask(path="/Areas/*", select='["osm:public_transport" = "platform"];["osm:railway" = "platform"]')
def osm_groups_areas_transport_platform(obj, osm):
    """Define area data."""
    obj.name = "Platform: %s" % obj.name
    obj.extra['ddd:area:type'] = "default"
    obj.extra['ddd:height'] = 0.65
    obj = obj.material(ddd.mats.pavement)
    return obj


@dddtask(path="/Areas/*", select='["osm:tourism" = "artwork"]')
def osm_groups_areas_tourism_artwork(obj, osm):
    """Define area data."""
    obj.name = "Artwork: %s" % obj.name
    obj.extra['ddd:area:type'] = "steps"
    obj.extra['ddd:steps:count'] = 2
    obj.extra['ddd:steps:height'] = 0.16
    obj.extra['ddd:steps:depth'] = 0.38
    #obj.extra['ddd:height'] = 0.35
    obj = obj.material(ddd.mats.stone)
    return obj

# Move this to "s30_interpretations" (not raw OSM)
@dddtask(path="/Areas/*", select='["osm:artwork_type" = "sculpture"]["osm:man_made" != "compass_rose"]')  # [!contains(["osm:artwork_type" == "sculpture"])]
def osm_groups_areas_artwork_sculpture(root, obj):
    """Adds a sculpture item to sculpture areas."""
    obj.name = "Sculpture: %s" % obj.name
    # Add artwork as node
    item = obj.centroid()    # area.centroid()
    root.find("/ItemsNodes").append(item)


@dddtask(path="/Areas/*",
         select='(["osm:waterway" ~ "riverbank|stream"];["osm:natural" = "water"];["osm:water" = "river"])["osm:amenity" != "fountain"]')
def osm_groups_areas_riverbank(obj, root):
    """Define area data."""

    #obj.dump()
    obj.name = "Riverbank: %s" % obj.name
    obj.extra['ddd:area:type'] = "water"
    obj.extra['ddd:height'] = 0.0
    obj = obj.material(ddd.mats.sea)
    obj = obj.individualize().clean(eps=0.01).flatten()
    #root.find("/Areas").children.extend(obj.children)
    #return False
    #return obj
    #obj.prefixchildren()  # "Riverbank: %s" % obj.name)  # Add name to children
    return obj.children  # return array, so the original object is replaced by children


@dddtask(path="/Areas/*", select='["osm:man_made" = "bridge"]')
def osm_groups_areas_man_made_bridge(obj, root):
    """Define area data."""
    obj.name = "Bridge Area: %s" % obj.name
    obj.extra['ddd:area:type'] = "default"
    #obj.extra['ddd:area:barrier:width'] = 0.2
    #obj.extra['ddd:area:barrier:height'] = 0.2
    #obj.extra['ddd:height'] = 0.0
    obj = obj.material(ddd.mats.cement)
    obj = obj.individualize().clean(eps=0.01).flatten()
    root.find("/Areas").children.extend(obj.children)
    return False
    #return obj


"""

            elif narea.extra.get('osm:landuse', None) in ('railway', ):
                narea = narea.subtract(ddd.group2(narea.extra['ddd:area:contained']))
                area = self.generate_area_2d_railway(narea)

            elif narea.extra.get('osm:amenity', None) in ('school', ):
                narea = narea.subtract(ddd.group2(narea.extra['ddd:area:contained']))
                narea = narea.subtract(union)
                area = self.generate_area_2d_school(narea)


    def generate_area_2d_railway(self, area):
        feature = area.extra['osm:feature']
        area.name = "Railway area: %s" % feature['properties'].get('name', None)
        area = area.material(ddd.mats.dirt)
        area = self.generate_wallfence_2d(area)
        return area

    def generate_area_2d_unused(self, area, wallfence=True):
        feature = area.extra['osm:feature']
        area.name = "Unused land: %s" % feature['properties'].get('name', None)
        area.extra['ddd:height'] = 0.0
        area = area.material(ddd.mats.dirt)

        if wallfence:
            area = self.generate_wallfence_2d(area)
        #if ruins:
        #if construction
        #if ...

        return area

    def generate_wallfence_2d(self, area, fence_ratio=0.0, wall_thick=0.3, doors=1):

        area_original = area.extra['ddd:area:original']
        reduced_area = area_original.buffer(-wall_thick).clean(eps=0.01)

        wall = area.subtract(reduced_area).material(ddd.mats.bricks)
        try:
            wall = wall.subtract(self.osm.buildings_2d)
        except Exception as e:
            logger.error("Could not subtract buildings from wall: %s", e)

        wall.extra['ddd:height'] = 1.8

        #ddd.uv.map_2d_polygon(wall, area.linearize())
        area = ddd.group2([area, wall])

        return area
"""


