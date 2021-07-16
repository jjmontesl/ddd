# Metadata

Every node in DDD can contain metadata. Metadata is a free set of key=value pairs, which
can be used freely to describe the element.

Metadata can also be used for filtering the objects to which operations apply, being a key
piece of DDD generation pipelines.

Attributes starting by `_` are considered private, and some of these are used internally by DDD.
These attributes are not exported with metadata when the output is saved.

### OSM Notes

OSM uses `height` as the "max height" at which a feature exists. For building and other features
which also have a `min_height`, the actual height is calculated as `height - min_height`.
Other objects, like `roof:height`, do instead acually contain the height of that part.

DDD uses "height" for actual object height, regardless of the "min_height" (called `base_height`
in DDD).

For instance, a fence on the top of a building may be tagged as "height=51" and "min_height=50"
in OSM. In DDD the same fence would be described with "height=1" and "base_height=50".


## Metadata usage reference


### SVG

svg:image:data
svg:image:height
svg:image:width

    Used by the SVG exporter. When a node contains `svg:image:data`, a SVG Image element
    is created in place of the node, using the given image.



### OSM Areas

ddd:elevation = geotiff |
ddd:area:elevation

    Defines which 3D elevation strategy will be used to position the object/vertices in 3D.

    Values:
        - geotiff
        - water (s30_groups_ways)
        - path (used by ways)
        - (also seen 'max' in ddd:area:elevation)

ddd:area:height
ddd:height

    Defines area height (over base ground elevation).

    Currently this is used for "raised" areas, those that have a kerb or an abrupt
    transition of height, but interpretation may vary by area type.


### OSM Items

ddd:item:elevation
ddd:elevation
_height_mapping

    Defines which 3D elevation strategy will be used to position the object/vertices in 3D.

    Values:
    - terrain_geotiff_min_elevation_apply
    - terrain_geotiff_elevation_apply
    - building

ddd:elevation:base_ref

    Values:
    - container


ddd:height:base

    Item vertical offset.

ddd:min_height
osm:min_height
+
ddd:height
ddd:item:height
osm:height

    Used for fences min_height and max_height. TODO: Normalize! but note Torre de Hercules fence uses min_height=50


### OSM Buildings

ddd:building:elevation
_terrain_geotiff_min_elevation_apply:elevation

    Defines which 3D elevation strategy will be used to position the object/vertices in 3D.
    (TODO: check, usage not confirmed)

ddd:building:elevation:min
ddd:building:elevation:max

    Stores min and max ground elevation values for a building footprint.


ddd:building:level:0:height

    Defines the height of a building's base level (floor 0). This level is deemed
    special as the footprint of the building will usually touch the ground at different
    elevations, burying part of the building into the ground.

    This level 0 height is floor 0 height plus the elevation difference of the footprint.

    TODO (review)

osm:height

    Used as max_height (note this is MAX height) of a building or building part.

ddd:roof:height
osm:roof:height

    Building roof part height, in meters.


### OSM Ways

ddd:extra_height
ddd:height
ddd:way:height
osm:height

    Used during way metadata processing. Represents the thickness of the road over
    the ground terrain.

    For historical reasons, this is obtained from osm:height if available, then managed
    as ddd:way:height during the s30_ways phase, then finally copied to ddd:height
    and ddd:extra_height.

    TODO: Normalize and review usages!


### Elevation

_terrain_geotiff_min_elevation_apply:elevation
_terrain_geotiff_max_elevation_apply:elevation

    (Internal) Set by the terrain module when applying max or min elevation to an object.








### Old notes (DELETE)



_*		Used internally? (not exported?)
    _last_extr?		Extrusion info... etc?



osm:*		OpenStreetMap schema metadata
    osm:item:*	Item
    osm:way:*	Way
    osm:area:*	Area
    + layer + area/way raised vs base + base_height (osm, ddd...)

**

    ddd:map:way:width ??

**Properties understood by... (?)**

ddd:*	DDD metadata
    ddd:crop:*			Cropping
    ddd:elevation:*		Elevation applying
    ddd:align:*			Align type
    ddd:area:raising?	?