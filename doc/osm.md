# DDD OSM Rendering Pipelines

DDD OSM is an OpenStreetMap 2D and 3D renderer. It has been built
from the ground up with the purpose of building correct city and
landscape 3D models.

It consists of a set of [DDD Pipelines]() that process OSM data and
build a 2D or 3D representation of it. These pipelines can export SVG,
PNG or 3D models of an area of interest with different styles.

In addition, these processes can produce tiled results, which allows to
process and present larger areas in chunks.

## Introduction


## Features

- Ways and intersections processing (both in 1D and 2D)
- Areas processing: containment and layering
- Buildings and bulding parts relationships
- (Heuristic) association of features (features/ways/areas/buildings to to ways/areas/buildings...)
- Coastlines and riverbanks
- Elevation model (2D contours, 3D elevation, stairs, filtering...)
- 3D bridges, tunnels and (TODO) stairs
- 3D buildings and roofs
- Traffic signs and traffic lights
- (TODO) Road lines and OSM traffic lanes tag support
- (TODO) Road signs (crossings, marks)

- Full metadata traceability across 2D and 3D features (both OSM and internal's)
- 2D and 3D outputs (SVG, PNG and GLTF)
- 3D objects for many different OSM items
- Tiled output generation
- Geometry catalog and object reuse (allows for 3D geometry buffering and instancing)
- Extensible and configurable

## Currently "under contract only" services

- Unity3D import scripts
- Orthophoto texturing of ways and surface areas (and downloading from WMS)
- Mapillary API queries, image downloading and embedding
- Data augmentation (heuristics)
- Data augmentation (image processing and other datasets) (TODO)
- Server infrastructure stack (TODO)
- Consultancy

## Feature gallery


