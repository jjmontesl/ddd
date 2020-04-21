
# Check ddstyle_osm_sketchy first, this one should inherit a lot from it

STYLES = {}

STYLES.update({


})

# Schools with no wall/fence contained or in border -> generate_wall_fence
area["amenity"="school"] & (! contains(any["barrier"] & !contains(any[""])) {
    o = utils.area_add_wallfence(o, fence_ratio, gates=x)
}

# Apply static modifiers and enable colliders (OSM doesn't need this)

