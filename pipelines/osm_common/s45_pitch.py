# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020

from ddd.ddd import ddd
from ddd.pipeline.decorators import dddtask
from ddd.core.exception import DDDException
from ddd.pack.sketchy import sports


@dddtask(order="45.10.+.+", path="/Areas/*", select='["ddd:area:type" = "pitch"]')  # [!contains(["natural"="tree"])]
def osm_augment_pitch(obj, root):
    pass

@dddtask(path="/Areas/*", select='["ddd:area:type" = "pitch"]')
def osm_augment_pitch_default_sport(obj, root):
    pass

'''
@dddtask(path="/Areas/*", select='["ddd:area:type" = "pitch"](["ddd:sport" = "soccer"]; !["ddd:sport"])')
def osm_augment_pitch_soccer(obj, root):

    area_2d_orig = obj.extra.get('ddd:crop:original')  #, area_2d)

    lines, items = sports.field_lines_area(area_2d_orig, sports.football_field_lines, padding=1.25)

    if lines:
        lines = terrain.terrain_geotiff_elevation_apply(lines, self.osm.ddd_proj).translate([0, 0, 0.15])
        height = area_2d.extra.get('ddd:height', 0.2)
        lines = lines.translate([0, 0, height])

        area_3d = ddd.group3([area_3d, lines])
    else:
        logger.debug("No pitch lines generated.")

def generate_area_3d_pitch(self, area_2d):

    if area_2d.geom is None:
        return None

    area_2d_orig = area_2d.extra.get('ddd:crop:original')  #, area_2d)

    #logger.debug("Pitch: %s", area_2d)
    area_3d = self.generate_area_3d(area_2d)

    # TODO: pass size then adapt to position and orientation, easier to construct and reuse
    # TODO: get area uncropped (create a cropping utility that stores the original area)

    sport = area_2d.extra.get('osm:sport', None)

    if sport == 'tennis':
        lines = sports.field_lines_area(area_2d_orig, sports.tennis_field_lines, padding=3.0)
    elif sport == 'basketball':
        lines = sports.field_lines_area(area_2d_orig, sports.basketball_field_lines, padding=2.0)
    else:
        # TODO: No default (empty), it should be assigned via pipeline props earlier
        lines = sports.field_lines_area(area_2d_orig, sports.football_field_lines, padding=1.25)

    if lines:
        lines = terrain.terrain_geotiff_elevation_apply(lines, self.osm.ddd_proj).translate([0, 0, 0.15])
        height = area_2d.extra.get('ddd:height', 0.2)
        lines = lines.translate([0, 0, height])

        area_3d = ddd.group3([area_3d, lines])
    else:
        logger.debug("No pitch lines generated.")

    return area_3d
'''