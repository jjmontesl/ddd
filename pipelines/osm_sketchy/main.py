#



# Mark roundabouts as one way roads by default
        if junction == "roundabout": oneway = True


# DDD style for OSM 3D generation.

STYLES = {}

STYLES.update({

    'scene': {
        'ground-material': material('Ground'),
        'sea-material': material('Sea'),
    },

    'chunk {': {},

    'instances?': {

    }

    'way[highway=*]': {

    },


    # Buildings

    # Add building name as 3D text, snap to main facade
    namedbuildings = s.select(path="/buildings_3d/*", filter=lambda o: o.extra.get('name', None))
    namedbuildings.apply(lambda o: (
        o.extra.facades.main ...
    )))


    # Performance

    # Disable shadow casting for all ways and areas with 0.0 height
    /areas_2d/** ["ddd:height" == 0.0]' {
        ddd:shadows = False
    }

})