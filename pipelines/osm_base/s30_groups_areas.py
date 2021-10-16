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
    obj.extra['ddd:aug:itemfill:types'] = {'default': 1, 'bush': 0.1, 'palm': 0.001}
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

@dddtask(path="/Areas/*", select='["osm:landuse" = "farmland"]')
def osm_groups_areas_landuse_farmland(obj, osm):
    """Define area data."""
    obj.name = "Farmland: %s" % obj.name
    obj.extra['ddd:area:type'] = "park"
    obj.extra['ddd:aug:itemfill:density'] = 0.01
    obj.extra['ddd:aug:itemfill:types'] = {'reed': 1}
    obj = obj.material(ddd.mats.terrain_ground)
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

@dddtask(path="/Areas/*", select='["osm:landuse" = "greenhouse_horticulture"]')
def osm_groups_areas_landuse_greenhouse_horticulture(obj, osm):
    """Define area data."""
    obj.name = "Greenhouse Hort: %s" % obj.name
    obj.extra['ddd:area:type'] = "bunker"
    obj.extra['ddd:aug:itemfill:density'] = 0.01
    obj.extra['ddd:aug:itemfill:types'] = {'reed': 1}
    obj = obj.material(ddd.mats.terrain_ground)
    # TODO: Add plastic covering / build greenshouse
    return obj

@dddtask(path="/Areas/*", select='["osm:landuse" = "industrial"]')
def osm_groups_areas_landuse_industrial(obj, osm):
    """Define area data."""
    obj.name = "Industrial: %s" % obj.name
    obj.extra['ddd:area:type'] = "default"
    #obj.extra['ddd:aug:itemfill:density'] = 0.006
    #obj.extra['ddd:aug:itemfill:types'] = {'default': 1, 'reed': 0.5}
    obj = obj.material(ddd.mats.asphalt)
    return obj

@dddtask(path="/Areas/*", select='["osm:landuse" = "vineyard"]')
def osm_groups_areas_landuse_vineyard(obj, osm):
    """Define area data."""
    obj.name = "Vineyard: %s" % obj.name
    obj.extra['ddd:area:type'] = "park"
    obj.extra['ddd:aug:itemfill'] = True
    obj.extra['ddd:aug:itemfill:align'] = "grid"
    obj.extra['ddd:aug:itemfill:density'] = 0.002
    obj.extra['ddd:aug:itemfill:types'] = {'bush': 1}  # Should be small trees
    obj = obj.material(ddd.mats.terrain_ground)
    return obj

@dddtask(path="/Areas/*", select='["osm:landuse" = "orchard"]')
def osm_groups_areas_landuse_orchard(obj, osm):
    """Define area data."""
    obj.name = "Orchard: %s" % obj.name
    obj.extra['ddd:area:type'] = "bunker"
    obj.extra['ddd:aug:itemfill'] = True
    obj.extra['ddd:aug:itemfill:align'] = "grid"
    obj.extra['ddd:aug:itemfill:density'] = 0.01
    obj.extra['ddd:aug:itemfill:types'] = {'bush': 1}
    obj = obj.material(ddd.mats.park)
    return obj

@dddtask(path="/Areas/*", select='["osm:landuse" = "plant_nursery"]')
def osm_groups_areas_landuse_plant_nursery(obj, osm):
    """Land that is used solely for plant nurseries, which grow live plants for sale."""
    obj.name = "Plant Nursery: %s" % obj.name
    obj.extra['ddd:area:type'] = "park"
    obj.extra['ddd:aug:itemfill'] = True
    obj.extra['ddd:aug:itemfill:density'] = 0.01
    obj.extra['ddd:aug:itemfill:types'] = {'bush': 1}
    obj = obj.material(ddd.mats.terrain_ground)
    return obj

@dddtask(path="/Areas/*", select='["osm:landuse" = "quarry"]')
def osm_groups_areas_landuse_quarry(obj, osm):
    """Area of land used for surface extraction (open-pit mining)."""
    obj.name = "Quarry: %s" % obj.name
    obj.extra['ddd:area:type'] = "bunker"
    #obj.extra['ddd:aug:itemfill:density'] = 0.01
    #obj.extra['ddd:aug:itemfill:types'] = {'reed': 1}
    obj = obj.material(ddd.mats.terrain_rock)
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

@dddtask(path="/Areas/*", select='["osm:natural" = "grassland"]')
def osm_groups_areas_natural_grassland(obj, osm):
    """Define area data."""
    obj.name = "Grassland: %s" % obj.name
    obj.extra['ddd:area:type'] = "park"
    obj.extra['ddd:aug:itemfill:density'] = 0.0
    obj = obj.material(ddd.mats.grass)
    return obj

@dddtask(path="/Areas/*", select='["osm:natural" = "heath"]')
def osm_groups_areas_natural_heath(obj, osm):
    """A dwarf-shrub habitat, characterized by open, low-growing woody vegetation."""
    obj.name = "Heath: %s" % obj.name
    obj.extra['ddd:area:type'] = "park"
    obj.extra['ddd:aug:itemfill:types'] = {'reed': 1, 'bush': 1}
    obj.extra['ddd:aug:itemfill:density'] = 0.00075
    obj = obj.material(ddd.mats.terrain_ground)
    return obj

@dddtask(path="/Areas/*", select='["osm:natural" = "wood"]')
def osm_groups_areas_natural_wood(obj, osm):
    """Define area data."""
    obj.name = "Wood: %s" % obj.name
    obj.extra['ddd:area:type'] = "park"
    obj.extra['ddd:aug:itemfill:density'] = 0.006
    obj.extra['ddd:aug:itemfill:types'] = {'default': 1, 'bush': 0.2, 'reed': 0.05}
    obj = obj.material(ddd.mats.forest)
    return obj

@dddtask(path="/Areas/*", select='["osm:natural" = "wetland"]')
def osm_groups_areas_natural_wetland(obj, osm):
    """Define area data."""
    obj.name = "Wetland: %s" % obj.name
    obj.extra['ddd:area:type'] = "park"
    obj.extra['ddd:aug:itemfill:density'] = 0.008
    obj.extra['ddd:aug:itemfill:types'] = {'reed': 0.8, 'bush': 0.2, 'default': 0.01}
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

@dddtask(path="/Areas/*", select='["osm:natural" = "scrub"]')
def osm_groups_areas_natural_scrub(obj, osm):
    """Define area data."""
    obj.name = "Scrub: %s" % obj.name
    obj.extra['ddd:area:type'] = "bunker"
    obj.extra['ddd:aug:itemfill:density'] = 0.008
    obj.extra['ddd:aug:itemfill:types'] = {'reed': 0.2, 'bush': 0.7, 'default': 0.1}  # bushes, depending on biome
    obj = obj.material(ddd.mats.forest)  # wetland
    return obj

@dddtask(path="/Areas/*", select='["osm:natural" = "shingle"]')
def osm_groups_areas_natural_shingle(obj, osm):
    """An accumulation of rounded rock fragments, usually pebbles and gravel, but sometimes larger, deposited and shaped by movement of water."""
    obj.name = "Shingle: %s" % obj.name
    obj.extra['ddd:area:type'] = "raised"
    obj = obj.material(ddd.mats.terrain_pebbles_sparse)  # wetland
    return obj


@dddtask(path="/Areas/*", select='["osm:golf" = "bunker"]')
def osm_groups_areas_golf_bunker(obj, osm):
    """Define area data."""
    # Note that golf:bunker is also usually marked as natural:sand
    obj.name = "Bunker: %s" % obj.name
    obj.extra['ddd:area:type'] = "bunker"  # sand / dunes
    return obj

@dddtask(path="/Areas/*", select='["osm:golf" = "fairway"]')
def osm_groups_areas_golf_fairway(obj, osm):
    """Define area data."""
    # Note that golf:bunker is also usually marked as natural:sand
    obj.name = "Fairway: %s" % obj.name
    #obj.extra['ddd:area:type'] = "defau"  # sand / dunes
    obj = obj.material(ddd.mats.garden)  # There's also an exception for this in surface:grass
    obj.extra['ddd:area:type'] = "default"
    return obj

@dddtask(path="/Areas/*", select='["osm:golf" = "rough"]')
def osm_groups_areas_golf_rough(obj, osm):
    """Define area data."""
    # Note that golf:bunker is also usually marked as natural:sand
    obj.name = "Rough: %s" % obj.name
    #obj.extra['ddd:area:type'] = "defau"  # sand / dunes
    obj = obj.material(ddd.mats.park)  # There's also an exception for this in surface:grass
    obj.extra['ddd:area:type'] = "default"
    return obj

@dddtask(path="/Areas/*", select='["osm:golf" = "green"]')
def osm_groups_areas_leisure_golf_green(obj, osm):
    """Define area data."""
    obj.name = "Golf Green: %s" % obj.name
    obj.extra['ddd:area:type'] = "park"  # should be default, or golf (for the irregaularity), but currently default is raising height :?
    # TODO: Disable grass blades generation here using augmentation metadata (grass blades are currently hard coded in s55_plants)
    obj = obj.material(ddd.mats.grass)
    return obj


@dddtask(path="/Areas/*", select='["osm:natural" = "bare_rock"]')
def osm_groups_areas_natural_bare_rock(obj, osm):
    """Define area data."""
    obj.name = "Bare Rock: %s" % obj.name
    obj.extra['ddd:area:type'] = "default"
    obj = obj.material(ddd.mats.rock)
    obj.extra['ddd:height'] = 0.40
    return obj

@dddtask(path="/Areas/*", select='["osm:natural" = "scree"]')  # scree: pedregal
def osm_groups_areas_natural_scree(obj, osm):
    """Define area data."""
    obj.name = "Scree: %s" % obj.name
    obj.extra['ddd:area:type'] = "default"
    obj = obj.material(ddd.mats.rock)
    #obj.extra['ddd:height'] = 0.40
    # TODO: Customize rock augmentation and splatting mix (rock / ground)
    return obj


@dddtask(path="/Areas/*", select='["osm:natural" = "bare_rock"]["osm:geological" = "volcanic_lava_field"]')
def osm_groups_areas_geological_volcanic_lava_field(obj, osm):
    """Define area data."""
    obj.name = "Lava: %s" % obj.name
    obj.set('ddd:area:type', "rocky")  # should be rocky
    obj.set('ddd:height', 0.05)  # height raises the surface causing it to have ground below, good in this case, but should fit floor (height 0.0) (so, how were kerbs made? they don't have ground)
    obj.set('ddd:layer', "0")  # forces layer 0
    obj = obj.material(ddd.mats.lava)
    return obj


@dddtask(path="/Areas/*", select='["osm:amenity" = "parking"]')
def osm_groups_areas_amenity_parking(obj, osm):
    """Define area data."""
    obj.name = "Parking: %s" % obj.name
    obj.extra['ddd:area:type'] = "default"
    #obj.extra['ddd:height'] = 0.1
    obj = obj.material(ddd.mats.asphalt)
    return obj

@dddtask(path="/Areas/*", select='["osm:amenity" = "school"]')
def osm_groups_areas_amenity_school(obj, osm):
    """Define area data."""
    obj.name = "School: %s" % obj.name
    obj.extra['ddd:area:type'] = "default"
    #obj.extra['ddd:height'] = 0.1
    obj = obj.material(ddd.mats.dirt)
    # TODO (decoration, in separate group of pipeline): Add fence, if there's no fence or wall estimated
    return obj


@dddtask(path="/Areas/*", select='["osm:historic" = "archaeological_site"]')
def osm_groups_areas_historic_archaeological_site(obj, osm):
    """Define area data."""
    obj.name = "Archaeological Site: %s" % obj.name
    obj.extra['ddd:area:type'] = "bunker"
    # TODO: Disable grass blades generation here using augmentation metadata (grass blades are currently hard coded in s55_plants)
    obj = obj.material(ddd.mats.terrain_ground)  # terrain_rock
    return obj

@dddtask(path="/Areas/*", select='["osm:landuse" = "railway"]')
def osm_groups_areas_landuse_railway(obj, osm):
    """Define area data."""
    obj.name = "Railway Area: %s" % obj.name
    obj.extra['ddd:area:type'] = "default"
    obj = obj.material(ddd.mats.dirt)

    # TODO: Generate fence or wall?

    return obj

@dddtask(path="/Areas/*", select='["osm:leisure" = "pitch"]')
def osm_groups_areas_leisure_pitch(obj, osm):
    """Define area data."""
    obj.name = "Pitch: %s" % obj.name
    obj.extra['ddd:area:type'] = "pitch"
    obj = obj.material(ddd.mats.pitch)
    return obj

@dddtask(path="/Areas/*", select='["osm:leisure" = "playground"]["geom:type" ~ "Polygon|MultiPolygon|GeometryCollection"]')
def osm_groups_areas_leisure_playground(obj, root, osm):
    """Define area data. Children game objects are defined in items_areas."""
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
    obj = obj.material(ddd.mats.stones)
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


# Areas attributes
# TODO: Move to separate file (?)

@dddtask(path="/Areas/*", select='["osm:trees" = "banana_plants"]')
def osm_groups_trees_banana_plants(obj, osm):
    """Specifies that an orchard is a banana plantation."""
    obj.set('ddd:aug:itemfill:types', {'palm': 1})


