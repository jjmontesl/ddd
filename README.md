# DDD (1D-2D-3D)

DDD is a library for procedural generation of 2D and 3D geometries.


## Features

- Procedurally generate and alter 2D and 3D geometry
- Object catalog ("prefabs") management
- Export 2D to SVG
- Export 3D to GLTF, FBX or OBJ
- Builtin viewer based on Trimesh/...?
- TTF based generation of text geometry
- Procedural objects library and examples

- Scenegraph approach? (not yet there, in refactoring)

## Introduction

(TODO)
DDD was built

Allow easy programatic definition of 1D, 2D and 3D objects.
Workflow oriented to scenegraph, manipulate entire hierarchies.

Solve Anastutia Minigolf minigame needs and possibly others (snake 3D, tanks, boxes / voxels, karts?).

Based on Shapely and Trimesh

(Screenshots)


## Initial wishlist of features (to be removed from this readme, or added to Features)

- Provide functions for procedurally generating varied geometry (extensible).
- Provide functions for procedurally generating and aligning materials (extensible).
- Procedurally populating trees, grass, etc... as needed.

- Handle materials, which will ultimately generate textures and materials.
- Read SVGs as inputs, and other filters (ie. text files with square encodigs).
- Export to format(s) supported by Unity (and export extra metadata as needed, colliders, etc).
- Favour geometry reuse (ie. trees, golf holes, can be reused).
- Support hierarchies and transformations.
- Support marked "gameobjects" and/or repeated geometry, and export them separately or as needed (ie. trees).

- Procedurally generating characters and animations?
- Supporting 2D scenes generation too? what for? tiles / scenes? graphic adventures?...
- Some minimium animation standards (as properties maybe?) for using in Unity


## Installation

(TODO)

**GDAL installation on Ubuntu 18.04**

For 18.04, installed gdal==2.2.3 (matches libgdal version, gdal-config --version):
Exported C and CPLUS_LIBRARY_PATH as per https://gis.stackexchange.com/questions/28966/python-gdal-package-missing-header-file-when-installing-via-pip
export CPLUS_INCLUDE_PATH=/usr/include/gdal/
export C_INCLUDE_PATH=/usr/include/gdal/


## Example

## Documentation

### OSM data import

Using PBFs:
  osmconvert spain-latest.osm.pbf -b=-5.870,40.760,-5.470,41.160 -o=salamanca-latest.osm.pbf
  osmconvert spain-latest.osm.pbf -b=-8.980,41.980,-8.480,42.480 -o=vigo-latest.osm.pbf
  osmconvert spain-latest.osm.pbf -b=-8.600,43.170,-8.200,43.570 -o=acoruna-latest.osm.pbf
Then, geojson:
  ./osmtogeojson city-latest.osm.pbf > /tmp/city.geojson



## License




