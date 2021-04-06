# DDD(123)

DDD(123) is a library for procedural generation of 2D and 3D geometries and scenes.

DDD purpose is to provide a very expressive API for building and operating with
shapes and models and at the same time closely reflect the hierarchy and metadata
that usually needs to accompany your built 2D or 3D documents.

DDD follows an object graph (or in 3D, a scene graph) approach. Documents (scenes)
are composed by nodes that form a **node tree**. A key concept in DDD is that
operations can be applied to individual nodes, entire branches, or selected
nodes within a hierarchy.

DDD can export entire scenes or branches easily to several 2D and 3D
formats: SVG, PNG, GLTF/GLB, custom JSON structure.

DDD includes an 'object catalog' concept, which allows reusing and caching objects
speeding up the generation process, and allowing render engines to leverage shared
meshes and geometry instancing.

The library is strongly based and relies on the underlying Shapely and Trimesh
packages which provide most of the geometry operations.

Related projects:

- DDD OSM: a build pipeline that generates 2D/3D tiles from OpenStreetMap data (included in this repo).

- DDD OSM Viewer: HTML5 2D and 3D map viewer.


## Features

- Procedurally generate, alter and align 2D and 3D geometry.
- Export 2D to SVG and PNG.
- Export 3D to GLTF, FBX or OBJ.
- TTF based generation of text geometry.
- Object catalog ("prefabs") support (for object and geometry reusing and runtime instancing).
- Handle materials, normals and UV coordinates.
- Basic collider primitives support. Texture atlas support.
- Document generation transformation pipeline support.
- A simple procedural models library (trees, urban props...)
- OpenStreetMap data 2D and 3D generation pipelines.


## Current status notes (Work in progress! Expect changes!)

DDD was built as a series of proof-of-concept scripts and is now slowly being
transformed into a more widely usable tool. If you are using or contributing
to the project, note:

- Treat operations as if they modified the object (many operations currently return
  a copy of the object but this will change for performance and consistency reasons).
- Access to metadata (`extra`, `.get`...) and propagation to children may change.
- Usage will gravitate towards a Node hierarchy where each node has a transform
  (currently only DDDInstance objects have a transform and all other geometries are
  in world space).


## Contributing

Please use the Issue tracker for questions, discussions and pull requests.
If you need some ideas, here are some areas that need help:

- Adding and documenting examples and tutorials.
- Help with OSM the road and roadlines connectity code.
- Improving the OSM generation pipeline.
- Create a simple and flexible tree procedural generator and tree prefabs.
- Adding other model packs and/or improving the aspect of the current assets pack.

Do not hesitate to get in touch if you have any question.


## Installation

Clone the source repository:

    git clone https://github.com/jjmontesl/ddd

Create a virtual environment:

    cd ddd
    python3 -m venv env

Activate the virtualenv (run this on ever new shell in order to use `ddd`):

    . env/bin/activate

Install DDD inside the virtualenv set up to run from the source:

    python setup.py develop

**For Osmium package (reading OSM files)**

    sudo apt-get install build-essential cmake libboost-dev libexpat1-dev zlib1g-dev libbz2-dev

**For GDAL installation (accessing GIS datasources) - Ubuntu 18.04**

The Python package GDAL 2.2.3 matches Ubuntu 18.04 libgdal version (check with `gdal-config --version`). In order
for the pip install to succeed, the path to the GDAL library needs to be defined in environment variables
(from https://gis.stackexchange.com/questions/28966/python-gdal-package-missing-header-file-when-installing-via-pip):

    export CPLUS_INCLUDE_PATH=/usr/include/gdal/
    export C_INCLUDE_PATH=/usr/include/gdal/
    pip install gdal==2.2.3

**Using the Docker image**

There is a Docker image recipe in the [ddd-docker](https://github.com/jjmontesl/ddd-docker) repository.


## Examples

**Included examples**

Examples in the `examples` directory can be run from the same directory by
typing `ddd` followed by the script name:

    cd examples
    ddd operations.py

**Quickly generate 3D from OSM**

This generates a model centered on the given WGS84 coordinates (lat,lon),
using a traverse mercator projection centered on the same point.

    ddd osm-build --name my_osm_model --center=41.224, 1.725 --radius=125

Note that OSM 2D/3D generation requires additional configuration and input
data. See the [OSM Generation Pipeline](doc/osm.md) for further information.


## Documentation

TODO: Introduce doc here and move sections to where appropriate.

- [DDD Guides](doc/)


## Gallery

**Videos**

- [OSM 3D generation pipeline (Lighting talk at OSM SOTM 2020)](https://youtu.be/R_AHn_eLpso)
- [Godot 2D integration example](https://youtu.be/wQVSpBloGj0)

**Images**

![ddd-gallery-salamanca2](doc/gallery/2020062x-salamanca-cathedral-river.png "Salamanca Cathedral generated from OSM data (render by Three.js)")
![ddd-gallery-periodictable](doc/gallery/20200628-periodictable.png "Periodic Table generated from CSV file")
![ddd-gallery-salamanca](doc/gallery/20200628-salamanca-cathedral-from-blender3-night.png "Salamanca Cathedral generated from OSM data (rendered by Blender)")
![ddd-gallery-hercules](doc/gallery/acoruna_hercules_750r_-8.406,43.386.png "Torre de Hercules 2D rendered from OSM data")


## 3rd party assets

Textures from: https://cc0textures.com/
Grass billboards from: https://www.reinerstilesets.de/new-textures-billboard-grass/


## License

DDD(123) - Library for procedural generation of 2D and 3D geometries and scenes
Copyright (C) 2021 Jose Juan Montes

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
