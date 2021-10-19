# DDD(123)

## OSM Generation pipeline

This are the main pipeline definition files for the OpenStreetMap to 3D
transformation pipeline.

This introduces a complete yet basic transformation process. This can later
extended by further pipeline configuration (like the other OSM related examples show).


### Summary

As this is a complex pipeline, it introduces ad-hoc concepts and stages.
Modifying or extending this pipeline requires understanding these steps.

1) Init

2) OSM feature loading

   All features are loaded as 2D geometries under the /Features node.
   Nodes are loaded as Point. Ways are loaded as LineString. Areas are loaded as Polygon.
   All OSM tags are copied with osm: prefix into each node metadata.

   All loaded features are put into the /Features node of the pipeline node graph.


3) Selection and grouping

   Features are copied into their respective groups. These are "major citizens" in the OSM generation process,
   as extra metadata is generated for them and receive special treatment in some processes (road intersections,
   area stacking, item-to-buildings associations...)

   Coastlines are processed in this stage.

   Group path used are:

        /Items		 For 1D points
        /Ways		 For 1D ways (lines)
        /Areas  	 For 2D polygons that are not buildings
        /Buildings	 For 2D polygons that are buildings
        /Meta		 For geometry to be used during processing but not in included the output


4) Processing and structured information.

   This is what should be needed to produce a 2D render. Different pipeline variants could use different
   paths in this pipeline. A 2D render may rely on 2D or 1D version of ways, or use the original unsplit
   paths altogether, or ignore generated areas. Data augmentation and interpretation can be done at
   different points within this stage.

   Way and area weighting ordering is resolved. Items are reordered for 2D rendering (z-index),
   but also for later subtraction calculation during iterations.

   Ways are split. Items are linked to ways (eg. traffic lights). Metadata is added for connection
   between ways (TODO: add connections to areas too to allow layering among them).

   Ways are converted to 2D (as areas). 2D intersections are calculated.

   Ways and areas layering is resolved.

   Amenities are linked to buildings.

   Ground is generated, and areas are calculated, sorted and stacked, also subtracted as needed and
   defined by ddd:area: metadata.



6) 3D Generation

   ...



