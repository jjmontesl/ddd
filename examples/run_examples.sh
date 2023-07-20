#!/bin/bash

DDD_OPTS=${DDD_OPTS:-""}

# Run all examples
ddd $DDD_OPTS catalog.py --export-meshes
ddd $DDD_OPTS catalog_lights.py --export-meshes
ddd $DDD_OPTS catenary.py
ddd $DDD_OPTS closestsegment.py
ddd $DDD_OPTS csgtest.py
ddd $DDD_OPTS export_fbx.py
ddd $DDD_OPTS geomops.py
ddd $DDD_OPTS geoterrain.py
ddd $DDD_OPTS gltf_hierarchy.py
ddd $DDD_OPTS lod.py
ddd $DDD_OPTS logo.py
#ddd $DDD_OPTS mapillary.py
ddd $DDD_OPTS noisetest.py
ddd $DDD_OPTS operations.py
ddd $DDD_OPTS path3.py
ddd $DDD_OPTS pathheight.py
ddd $DDD_OPTS periodictable.py
ddd $DDD_OPTS plants.py
ddd $DDD_OPTS png3drender.py
ddd $DDD_OPTS randompoints.py
#ddd $DDD_OPTS selector.py  # Incomplete
ddd $DDD_OPTS shapes.py
ddd $DDD_OPTS sketchy.py
ddd $DDD_OPTS sketchy_interior.py
ddd $DDD_OPTS sketchy_industrial.py
ddd $DDD_OPTS sketchy_landscape.py
ddd $DDD_OPTS sketchy_lighting.py
ddd $DDD_OPTS sketchy__large_objects.py
ddd $DDD_OPTS snap.py
ddd $DDD_OPTS sports.py
ddd $DDD_OPTS subdivide.py
ddd $DDD_OPTS svgload.py
ddd $DDD_OPTS svg.py
ddd $DDD_OPTS text2d.py
ddd $DDD_OPTS text3d.py
#ddd $DDD_OPTS traffic_signs.py  # Takes long to display
ddd $DDD_OPTS transforms.py
ddd $DDD_OPTS uvmapping.py
#ddd $DDD_OPTS volume.py



