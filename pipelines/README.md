# DDD(123)

## OSM Generation pipeline

This are the main pipeline definition files for the OpenStreetMap to 3D
transformation pipeline.

This introduces a complete yet basic transformation process. This can later
extended by further pipeline configuration (like the other OSM related examples show).


## Steps

As this is a complex pipeline, it introduces ad-hoc concepts and stages.
Modifying or extending this pipeline requires understanding these steps.

1) OSM feature loading

   All features are loaded as 2D geometries nder the /Features node.
   Nodes are loaded as Point. Ways are loaded as LineString. Areas are loaded as Polygon.
   All OSM tags are copied with osm: prefix into each node metadata.

2) Separation into /Items /Ways and /Areas

   Features are copied into their respective groups.

TODO (?): Reverse initial metadata ??? items/ways/areas? areas first, then ways with nodes and containment, then items with nodes and containment.

3) Ways processing (splitting, connections...)

   (?) Items are associated to each way (TODO: maybe do this after splitting, which doesn't care about items?)

   Metadata about connections and intersections between ways is generated.
   Ways are split at every intersection with other ways. Each way is therefore a simple line, with no loops.
   For each split way, metadata is copied to the two newly generated

   (?) TODO: Split ways at area intersections in 1D? (seems unnecessary and may introduce cumbersome intersections, or perhaps resolve transitions between kerb/park...

4) Areas processing

   (TODO: NEW)

   Areas containment metadata is generated (parent / children).

