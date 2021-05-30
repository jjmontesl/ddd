# DDD OSM Rendering Pipelines

DDD OSM is an OpenStreetMap 2D and 3D renderer. It has been built
from the ground up with the purpose of building correct city and
landscape 3D models.

It consists of a set of [DDD Pipelines](pipelines.md) that process OSM data and
build a 2D or 3D representation of it. These pipelines can export SVG,
PNG or 3D models of an area of interest with different styles.

In addition, these processes can produce tiled results, which allows to
process and present larger areas in chunks.

## Introduction


## Features

- Ways and intersections processing (both in 1D and 2D)
- Areas processing: containment and layering
- Buildings and bulding parts relationships
- Association and alignment of features to ways/areas/buildings...
- Coastlines and rivers
- Elevation model (2D contours, 3D elevation, stairs, filtering...)
- 3D bridges, tunnels and stairs (WIP, very buggy)
- 3D buildings and roofs (WIP)
- Traffic signs, road marks and traffic lights

- Full metadata traceability across 2D and 3D features (both OSM and internal's)
- 2D and 3D outputs (SVG, PNG and GLTF)
- 3D objects for many different OSM items
- Tiled output generation
- Geometry catalog and object reuse (allows for 3D geometry buffering and instancing)
- Extensible and configurable

## Screenshots





### OSM data import (preprocessing)


Note: latest versions are doing and caching the extraction automatically from country-latest.pbf,
so this step needs not to be done manually.

Using PBFs:

    osmconvert spain-latest.osm.pbf -b=-5.870,40.760,-5.470,41.160 -o=salamanca-latest.osm.pbf
    osmconvert spain-latest.osm.pbf -b=-8.980,41.980,-8.480,42.480 -o=vigo-latest.osm.pbf
    osmconvert spain-latest.osm.pbf -b=-8.600,43.170,-8.200,43.570 -o=acoruna-latest.osm.pbf

Then, geojson (TODO: use osmium directly):

    ./osmtogeojson city-latest.osm.pbf > /tmp/city.geojson



### Converting carto icons to texture atlas


(TODO) ddd has now a command line option to do this... review and document.

Using:

    for a in $(ls *.svg) ; do inkscape -w 64 -h 64 $a --export-filename ../amenity-$a.png ; done

Resize with margin:

    mogrify -path x -resize 120x120 -gravity Center -extent 128x128 *.png


