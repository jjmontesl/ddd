
# Check ddstyle_osm_sketchy first, this one should inherit a lot from it

STYLES = {}

STYLES.update({


})

stage('ways').steps.extend([

])

# Schools with no wall/fence contained or in border -> generate_wall_fence
area["amenity"="school"] & (! contains(any["barrier"] & !contains(any[""])) {
    o = utils.area_add_wallfence(o, fence_ratio, gates=x)
}

# Apply static modifiers and enable colliders (OSM doesn't need this)


# Add lights (to lamp cases, etc, tag them earlier though)
light = ddd.light_point([0, 0, height * 0.8], name="Lamp Light", color="#e4e520", range=18, intensity=1.25)