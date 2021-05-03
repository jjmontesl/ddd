# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020


from ddd.ddd import ddd
from ddd.geo import terrain
from ddd.osm import osm
from ddd.pipeline.decorators import dddtask
import math
import random


"""
Lamps, signs, traffic signals, road signs, roadlines...
"""

#@dddtask(order="45.20.+.+")
@dddtask(order="55.10.+.+")
def osm_augment_ways2(root, osm, pipeline, logger):
    """
    Standard augmentation for OSM ways. This includes lamps (according to osm:lit and config) and
    traffic lights (if not present).
    """
    pipeline.data['_lamps'] = root.select('["osm:highway" = "street_lamp"]')

@dddtask(path="/Ways/*", select='["ddd:way:lamps" = True]')  # shall be osm:lit?
def osm_augment_ways_2d_lamps(root, osm, pipeline, logger, obj):
    """
    """
    #lamps = root.select('["osm:highway" = "street_lamp"]')
    if not obj.extra['osm:feature_2d'].buffer(35.0, cap_style=ddd.CAP_ROUND).intersects(pipeline.data['_lamps']):
        osm.ways2.generate_lamps(pipeline, obj)

@dddtask(path="/Ways/*", select='["ddd:way:traffic_signals"]')
def osm_augment_ways_2d_traffic_signals(root, osm, pipeline, obj):
    """
    Traffic lights.
    """
    osm.ways2.generate_traffic_signals(pipeline, obj)

@dddtask(path="/Ways/*", select='["ddd:way:traffic_signs"]')
def osm_augment_ways_2d_traffic_signs(root, osm, pipeline, obj):
    """
    """
    osm.ways2.generate_traffic_signs(pipeline, obj)



@dddtask(path="/Ways/*")  # , select='["ddd:way:road_marks"]')
def osm_augment_ways_2d_road_marks(root, osm, pipeline, obj):
    """
    """
    pass

@dddtask(path="/Ways/*", select='["ddd:way:roadlines" = true]["osm:highway" != "cycleway"]')  # , select='["ddd:way:road_marks"]')
def osm_augment_ways_2d_road_marks_give_way(root, osm, pipeline, obj):
    """
    """
    way_2d = obj
    path = way_2d.extra['way_1d']
    length = path.geom.length

    # Generate road signs
    if not (True and path.geom.length > 20.0 and path.extra['ddd:layer'] in (0, "0")):
        return

    # TODO: Do this with the informed road model

    numlanes = way_2d.extra['ddd:way:lanes']
    for laneind in range(numlanes):

        width = path.extra['ddd:width']
        lane_width = path.extra['ddd:way:lane_width']  # lanes_width / lanes
        lane_width_left = path.extra['ddd:way:lane_width_left']
        lane_width_right = path.extra['ddd:way:lane_width_right']
        oneway = path.extra.get('osm:oneway', False)
        if (oneway in ("no", "false")): oneway = False

        lane_0_distance = -(width / 2) + lane_width_right + lane_width / 2
        lane_distance = lane_0_distance + lane_width * laneind

        for end in (1, -1):

            if end == -1 and path.extra.get('osm:oneway', None): continue

            mark_end_distance = 7.0  # TODO: Depends on the width of the traversed road, or we shall use the trimmed path

            if end == 1:
                p, segment_idx, segment_coords_a, segment_coords_b = path.interpolate_segment(path.geom.length - mark_end_distance)
            else:
                p, segment_idx, segment_coords_a, segment_coords_b = path.interpolate_segment(mark_end_distance)

            # Only for the correct part of the line (since path is not adjusted by intersections)
            if not way_2d.intersects(ddd.point(p)): continue

            dir_vec = (segment_coords_b[0] - segment_coords_a[0], segment_coords_b[1] - segment_coords_a[1])
            dir_vec_length = math.sqrt(dir_vec[0] ** 2 + dir_vec[1] ** 2)
            dir_vec = (dir_vec[0] / dir_vec_length, dir_vec[1] / dir_vec_length)
            perpendicular_vec = (-dir_vec[1], dir_vec[0])
            left = (p[0] + perpendicular_vec[0] * lane_distance, p[1] + perpendicular_vec[1] * lane_distance)
            right = (p[0] - perpendicular_vec[0] * lane_distance, p[1] - perpendicular_vec[1] * lane_distance)
            #left = p
            #right = p

            if end == 1:
                item = ddd.point(right, name="Road Mark: %s" % way_2d.name)
                angle = math.atan2(dir_vec[1], dir_vec[0]) + math.pi
            else:
                item = ddd.point(left, name="Road Mark: %s" % way_2d.name)
                angle = math.atan2(dir_vec[1], dir_vec[0])


            # area = self.osm.areas_2d.intersect(item)
            # Check type of area point is on
            # Note that give_way is not a node tag for OSM, but it is used here to represent each individual symbol
            signtype = random.choice(['give_way', 'left', 'through', 'right', 'left_through', 'right_through', 'left_right'])
            item.extra['way_2d'] = way_2d
            item.extra['ddd:aug:status'] = 'added'
            item.extra['ddd:road_marking'] = signtype  # 'give_way'
            item.extra['ddd:angle'] = angle # + math.pi / 2
            pipeline.root.find("/ItemsNodes").append(item)







