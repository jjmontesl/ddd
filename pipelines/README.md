# DDD(123)

## OSM Generation pipeline

This are the main pipeline definition files for the OpenStreetMap to 3D
transformation pipeline.

This introduces a complete yet basic transformation process. This can later
extended by further pipeline configuration (like the other OSM related examples show).


## Steps


### TMP NOTE: Current phases

build
- !initialize variables, projs, et (projections will likely be different for OSM/YCR)
- ! chunking [?  in theory, the chunk is what defines data to be gathered... move to first step (and use larger data metatiles to avoid mutiple downloads) chunk externally ]
- data downloading (currently osmconvert + osm2geojson)

-  start pipeline [?  run everything inside a pipeline, call out to helpers, also for loading, move to the very first / externally]
 - osmbuilder.load_geojson(files) -> this loads builder features, but does not touch pipeline root [call from pipeline]
 - osmbuilder.preprocess_features() [? this is actually "create features", may stay in builder - other preprocess, maybe move after remove objects and crop?]

partial_pipeline:main
 - remove objects / raw osm preprocess (empty)
 - crop extended area
 - create root nodes (if they are tracked by builder, do in builder)
 - generate features, ways, buildings, areas

rest
 - osm.ways.generate_ways_1d() [this adds metadata and styles and materials to ways... move to styling file - change name "process_ways...whatever"]
 - osm.ways.split_ways_1d() [this is critical, keep inside OSM builder ways, call (before or after generate_ways?) ]

  ...start making logic and operations work based on metadata...

 - osm.buildings.preprocess_buildings_2d()
 - osm.buildings.generate_buildings_2d()

 - osm.ways.generate_ways_2d()

 - osm.areas.generate_areas_2d()
 - osm.areas.generate_areas_2d_interways()  # and assign types

 - osm.areas.generate_areas_2d_postprocess()
 - osm.areas.generate_areas_2d_postprocess_water()

 - osm.buildings.link_features_2d()

 - osm.areas.generate_coastline_3d(osm.area_crop if osm.area_crop else osm.area_filter)  # must come before ground
 - osm.areas.generate_ground_3d(osm.area_crop if osm.area_crop else osm.area_filter) # separate in 2d + 3d, also subdivide (calculation is huge - core dump-)

 - osm.items2.generate_items_2d()  # Objects related to areas (fountains, playgrounds...)
 - osm.ways.generate_props_2d()  # Objects related to ways

 - # 2D output (before cropping, crop here -so buildings and everything is cropped-)
 - self.save_tile_2d("/tmp/osm2d.png")
 - self.save_tile_2d("/tmp/osm2d.svg")

    # Crop if necessary
    if osm.area_crop:
        logger.info("Cropping to: %s" % (osm.area_crop.bounds, ))
        crop = ddd.shape(osm.area_crop)
        osm.areas_2d = osm.areas_2d.intersection(crop)
        osm.ways_2d = {k: osm.ways_2d[k].intersection(crop) for k in osm.layer_indexes}

        #osm.items_1d = osm.items_1d.intersect(crop)
        osm.items_1d = ddd.group([b for b in osm.items_1d.children if osm.area_crop.contains(b.geom.centroid)], empty=2)
        osm.items_2d = ddd.group([b for b in osm.items_2d.children if osm.area_crop.contains(b.geom.centroid)], empty=2)
        osm.buildings_2d = ddd.group([b for b in osm.buildings_2d.children if osm.area_crop.contains(b.geom.centroid)], empty=2)

    # 3D Build

    # Ways 3D
    osm.ways.generate_ways_3d()
    osm.ways.generate_ways_3d_intersections()
    # Areas 3D
    osm.areas.generate_areas_3d()
    # Buildings 3D
    osm.buildings.generate_buildings_3d()

    # Walls and fences(!) (2D?)

    # Urban decoration (trees, fountains, etc)
    osm.items.generate_items_3d()
    osm.items2.generate_items_3d()

    # Generate custom items
    osm.customs.generate_customs()


    # Final grouping
    scene = [osm.areas_3d, osm.ground_3d, osm.water_3d,
             #osm.sidewalks_3d_lm1, osm.walls_3d_lm1, osm.ceiling_3d_lm1,
             #osm.sidewalks_3d_l1, osm.walls_3d_l1, osm.floor_3d_l1,
             osm.buildings_3d, osm.items_3d,
             osm.other_3d, osm.roadlines_3d]
    scene = ddd.group(scene + list(osm.ways_3d.values()), name="Scene")

    pipeline.root = scene

build [after]
 - save tile 2D (move to the appropriate export site, remove this export logic from within OSMBuilder (it's ad-hoc and should be configurable)



### Summary

10-init

20-load-features
20.10-load-features-load

30-groups + categories / etc... +METADATA
30.10-groups-...

40-structured (2D + areas)
split-ways
ways 1d -> 2d
areas-processing (areas->2d)
areas-stacking...


50-3d-generation




### Description

As this is a complex pipeline, it introduces ad-hoc concepts and stages.
Modifying or extending this pipeline requires understanding these steps.

1) OSM feature loading

   All features are loaded as 2D geometries under the /Features node.
   Nodes are loaded as Point. Ways are loaded as LineString. Areas are loaded as Polygon.
   All OSM tags are copied with osm: prefix into each node metadata.

2) Separation into /Items /Ways /Areas and /Buildings

   Features are copied into their respective groups. These are "major citizens" in the OSM generation process,
   as extra metadata is generated for them and receive special treatment in some processes (road intersections,
   area stacking, item-to-buildings associations...)


TODO (?): Reverse initial metadata ??? items/ways/areas? areas first, then ways with nodes and containment, then items with nodes and containment.

3) Ways processing (splitting, connections...)

   (?) Items are associated to each way (TODO: maybe do this after splitting, which doesn't care about items?)

   Metadata about connections and intersections between ways is generated.
   Ways are split at every intersection with other ways. Each way is therefore a simple line, with no loops.
   For each split way, metadata is copied to the two newly generated

   Requires: X because Y

   (?) TODO: Split ways at area intersections in 1D? (seems unnecessary and may introduce cumbersome intersections, or perhaps resolve transitions between kerb/park...

4) Areas processing

   (TODO: NEW)

   Areas containment metadata is generated (parent / children).

   Requires: X because Y


