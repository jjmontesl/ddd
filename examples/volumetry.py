# ddd - DDD123
# Library for simple scene modelling.
# Jose Juan Montes and Contributors 2019-2021

import math
import pyproj
from ddd.ddd import ddd
from ddd.geo import terrain
from ddd.math.vector2 import Vector2
from ddd.pack.sketchy import urban, landscape
from ddd.pipeline.decorators import dddtask
from shapely.geometry import MultiPoint

"""
# Pool volumetry with DDD

In this exercise we'll estimate the water volume of a swimming pool,
from measurements of the water depth made along the contour of the pool.

## Scenario

## Procedure

### Define the samples

### Construct volume (solid, watertight mesh)

### Add the missing area (corresponding to the rounded corners)

### Retrieve volumetric data

### Render a final contextual view
"""

@dddtask(order="10")
def pipeline_start(pipeline, root):
    """
    Pool volume calculation example.
    """

    items = ddd.DDDNode3()

    samples_bottom = [
        [0, 0, 1.82],  # 0
        [1, 0, 1.825],
        [2, 0, 1.78],
        [3, 0, 1.685],
        [4, 0, 1.59],
        [5, 0, 1.48],
        [6, 0, 1.37],
        [7, 0, 1.265],
        [8, 0, 1.155],
        [9, 0, 1.11],  # y0
    ]

    samples_right = [
        [9, 0, 1.11],  # y0
        [9, 1, 1.11],
        [9, 2, 1.10],
        [9, 3, 1.10],
        [9, 4, 1.11],  # z9*
    ]

    samples_top = [
        [9, 4, 1.11], #z9*
        [8, 4, 1.155],
        [7, 4, 1.265],
        [6, 4, 1.37],
        # 3 samples above added copied from opposite side (stairs)
        [5.76, 4, 1.395],  # 3 + 0.7 + 0.68 + 0.68 + 0.7
        [3 + 0.7 + 0.68 + 0.68, 4, 1.465],
        [3 + 0.7 + 0.68, 4, 1.545],
        [3 + 0.7, 4, 1.615],
        [3, 4, 1.69],
        [2, 4, 1.80],
        [1, 4, 1.82],
        [0, 4, 1.83],  # z0
    ]

    samples_left = [
        [0, 0, 1.82],  # x0
        [0, 1, 1.83],  # x1
        [0, 2, 1.83],
        [0, 3, 1.84],
        [0, 4, 1.83],  # z0
    ]

    water_distance = 0.10
    scene_orientation = -85  # in order to match geo terrain
    round_radius = 0.20
    res = 0.2
    use_stairs = False


    all_samples = samples_top + samples_right + samples_bottom + samples_left
    line_top = ddd.line(reversed(samples_top))
    line_right = ddd.line(samples_right)
    line_bottom = ddd.line(samples_bottom)
    line_left = ddd.line(samples_left)

    points = ddd.group([ddd.point(c) for c in all_samples])  # .union()
    points.show()

    multipoints_shape = MultiPoint([p.geom for p in points.children])
    multipoints = ddd.shape(multipoints_shape)
    #multipoints.dump(data='ddd')
    #multipoints.show()

    footprint = ddd.DDDNode2()
    footprint.geom = multipoints.geom.convex_hull
    footprint = footprint.material(ddd.mats.water)

    # Stairs
    if use_stairs:
        stairs_r = 1.5
        stairs = ddd.disc([9 - stairs_r, 4], r=1.5, resolution=8)
        footprint = footprint.union(stairs)
        footprint.show()

    #footprint.show()


    def depth_func(x, y):

        p = Vector2([x, y])

        interp = lambda a, b, da, db: ddd.math.clamp(da / (da + db), 0, 1) * b + ddd.math.clamp(db / (da + db), 0, 1) * a

        # Project to top and bottom (points already interpolated by shapely), interpolate between both based on distance factor
        t_p1, segment_idx, segment_coords_a, segment_coords_b = line_top.interpolate_segment(x)
        b_p1, segment_idx, segment_coords_a, segment_coords_b = line_bottom.interpolate_segment(x)
        d_t = (Vector2(t_p1) - p).length()
        d_b = (Vector2(b_p1) - p).length()

        depth_x = interp(b_p1[2], t_p1[2], d_b, d_t)

        # Project to left and right (points already interpolated by shapely), interpolate between both based on distance factor
        l_p1, segment_idx, segment_coords_a, segment_coords_b = line_left.interpolate_segment(y)
        r_p1, segment_idx, segment_coords_a, segment_coords_b = line_right.interpolate_segment(y)
        d_l = (Vector2(l_p1) - p).length()
        d_r = (Vector2(r_p1) - p).length()

        depth_y = interp(l_p1[2], r_p1[2], d_l, d_r)

        # Interpolate between horizontal and vertical
        if footprint.buffer(0.001).intersects(ddd.point(p)):
            depth = (depth_x + depth_y) / 2.0
            #depth = depth_y
        else:
            distvals = [ (d_t, t_p1), (d_b, b_p1), (d_l, l_p1), (d_r, r_p1)]
            distvals = sorted(distvals, key = lambda o: o[0])
            #depth = distvals[0][1][2]
            #return depth_func(distvals[0][1][0], distvals[0][1][1])

            coords_p, segment_idx, segment_coords_a, segment_coords_b, closest_object, closest_object_d = footprint.closest_segment(ddd.point(p))
            return depth_func(coords_p[0], coords_p[1])

        #print(depth)
        #return 1.0 + x + y
        depth = depth - water_distance
        return depth


    def vertex_func(offset):
        def _vertex_func(x, y, z, i, o):

            if z < (0 - ddd.EPSILON):

                if z > (-res / 2):
                    return [x, y, 0]

                return [x, y, z - depth_func(x, y) + offset]
                #return [x, y, z]
            else:
                return [x, y, z]
        return _vertex_func

    def lowest_point(obj):
        lowest = None
        for v in obj.vertex_iterator():
            if lowest is None or v[2] < lowest[2]:
                lowest = v
        return ddd.sphere(lowest, r=0.05).highlight()

    footprint3 = footprint.copy().extrude(- res / 2)
    footprint3 = ddd.meshops.subdivide_to_grid(footprint3, res)
    #footprint3.show()
    footprint3 = footprint3.vertex_func(vertex_func(res / 2))
    footprint3 = footprint3.merge_vertices()

    ddd.group([footprint3, lowest_point(footprint3)]).show()

    # Rounded edges and corners
    footprint3_r = footprint.copy()
    last_h = 0.0
    for ai in range(1, 9):
        angle = ddd.PI_OVER_2 / 8 * ai
        expand_d = round_radius * (math.sin(angle))
        expand_h = round_radius * (1 - math.cos(angle))
        footprint3_r = footprint3_r.extrude_step(footprint.buffer(expand_d, join_style=ddd.JOIN_ROUND), expand_h - last_h, method=ddd.EXTRUSION_METHOD_SUBTRACT)
        last_h = expand_h
    footprint3_r = footprint3_r.extrude_step(footprint.buffer(expand_d, join_style=ddd.JOIN_ROUND), res / 2, method=ddd.EXTRUSION_METHOD_SUBTRACT)
    footprint2_r = footprint.buffer(expand_d, join_style=ddd.JOIN_ROUND)
    #footprint3_r.show()
    footprint3_r = ddd.meshops.subdivide_to_grid(footprint3_r, res).translate([0, 0, -round_radius - res / 2])
    #footprint3_r.show()
    footprint3_r = footprint3_r.vertex_func(vertex_func(round_radius + res / 2))
    footprint3_r = footprint3_r.merge_vertices()
    footprint3_r = footprint3_r.fix_normals()
    ddd.group([footprint3_r, lowest_point(footprint3_r)]).show()


    # Differences rounded/not rounded
    ddd.group([footprint3, footprint3_r.highlight()]).show()


    #fig = urban.fire_hydrant()
    scenepool = footprint3_r.copy()
    scenepool = scenepool.translate([0, 0, -water_distance])

    # Ladder
    stairs = landscape.ladder_pool(height=1.4, width=0.45)
    stairs = stairs.rotate(ddd.ROT_TOP_HALFTURN).translate([1.5, 0, 0])
    scenepool.append(stairs)

    #border = ddd.rect(footprint2_r.bounds()).buffer(1.0).subtract(footprint2_r)
    border = footprint2_r.buffer(1.5, join_style=ddd.JOIN_BEVEL).subtract(footprint2_r)
    border3 = border.extrude(-0.2)
    border3 = border3.material(ddd.mats.stone).smooth()
    border3 = ddd.uv.map_cubic(border3)
    #border3.show()
    scenepool.append(border3)

    item = urban.patio_chair()
    scenepool.append(item.rotate([0, 0, ddd.PI * 0.187]).translate([4.5, 6.0, 0]))

    item = urban.patio_umbrella()
    scenepool.append(item.translate([5.5, 6.5, 0]))

    scenepool = scenepool.rotate([0, 0, scene_orientation * ddd.DEG_TO_RAD])
    scenepool = scenepool.recenter(onplane=True)

    items.append(scenepool)
    # Lowest point


    # Other deco

    # Terrain
    coords_latlon = pipeline.data.get('coords', "42.23,-8.71")
    coords_latlon = coords_latlon.split(",")
    coords_latlon = (float(coords_latlon[0]), float(coords_latlon[1]))
    # Create a UTM projection centered on the target coordinates
    ddd_proj = pyproj.Proj(proj="tmerc",
                           lon_0=coords_latlon[1], lat_0=coords_latlon[0],
                           k=1,
                           x_0=0., y_0=0.,
                           units="m", datum="WGS84", ellps="WGS84",
                           towgs84="0,0,0,0,0,0,0",
                           no_defs=True)

    item = terrain.terrain_geotiff([[-50, -50, 0], [50, 50, 0]], ddd_proj, detail=15.0)
    #item = item.material(ddd.mats.terrain)
    item = item.material(ddd.MAT_TEST)
    item = item.translate([0, 0, -103])  # TODO: Use elevation
    item = item.smooth(angle=ddd.PI / 12)
    item = ddd.uv.map_cubic(item, scale=[1 / 10, 1 / 10])


    root.append(item)


    # Helper
    #items.append(ddd.helper.all())

    # Volume info
    fig = footprint3
    print("Volume Rect: %s m3  (%s L)" % (fig.mesh.volume, fig.mesh.volume * 1000))
    print("Volume Rounded: %s m3  (%s L)" % (footprint3_r.mesh.volume, footprint3_r.mesh.volume * 1000))

    # Splits

    numparts = 4
    parts = ddd.DDDNode3(name="Parts")
    bounds = footprint2_r.bounds()
    part_l = (bounds[1][0] - bounds[0][0]) / numparts
    for d in range(0, numparts):
        rect = ddd.rect([[bounds[0][0] + part_l * d - 0.001, bounds[0][1] - 1], [bounds[0][0] + part_l * (d + 1) + 0.001, bounds[1][1] + 1]])
        #ddd.trace(locals())
        #ddd.group([footprint2_r, rect.highlight()]).show()
        block = rect.extrude(6).translate([0, 0, -3])
        part3 = footprint3_r.intersection(block)
        print("Portion volume: %s m3 (%s L) (%.1f %%)" % (part3.mesh.volume, part3.mesh.volume * 1000, 100 * part3.mesh.volume / footprint3_r.mesh.volume))
        #ddd.group([footprint3_r, part3.highlight()]).show()
        parts.append(part3)

    parts = ddd.helper.colorize_objects(parts)
    parts = ddd.align.grid(parts, space=0.2, width=10)
    parts.show()

    # Volume per longitudinal section(20%, 40%... on X axis)

    root.append(items)

    root.show()


