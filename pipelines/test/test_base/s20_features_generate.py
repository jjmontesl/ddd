# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020

import sys

from ddd.ddd import ddd, DDDMaterial
import godot_parser
from scipy.spatial import Voronoi, voronoi_plot_2d
import numpy as np
import shapely.geometry
import shapely.ops


from ddd.pipeline.decorators import dddtask
import random
import math


@dddtask(order="20.1", log=True)
def features_init(pipeline, root, logger):

    features = ddd.group2(name="Features2")
    root.append(features)

    features3 = ddd.group2(name="Features3")
    root.append(features3)

@dddtask(order="20.1", log=True)
def features_gen(pipeline, root, logger):

    area = ddd.disc(r=100.0)

    points_coords = area.random_points(num_points=200)
    points = ddd.group2([ddd.point(c) for c in points_coords], name="Points")
    points.extra['points_coords'] = points_coords

    root.find("/Features2").append(area)
    root.find("/Features2").append(points)

@dddtask(order="20.1", log=True)
def features_points_voronoi(pipeline, root, logger):

    points = root.find("/Features2/Points")
    vor = Voronoi(points.extra['points_coords'])

    #lines = [ddd.line(vor.vertices[line]) for line in vor.ridge_vertices if -1 not in line]
    #lines = ddd.group2(lines)

    #[[], [-1, 0], [-1, 1], [1, -1, 0], [3, -1, 2], [-1, 3], [-1, 2], [0, 1, 3, 2], [2, -1, 0], [3, -1, 1]]
    #print(vor.regions)
    regions = [ddd.polygon( [vor.vertices[i] for i in r ] ) for r in vor.regions if -1 not in r]

    regions = ddd.group2(regions, name="Regions")

    root.find("/Features2").append(regions)

    #regions.show()

@dddtask(order="20.1", log=True)
def features_regions_merge_random(pipeline, root, logger):
    regions = root.find("/Features2/Regions")

    #regions.show()

    #for r in regions_by_area:
    for i in range(int(len(regions.children) * 0.75)):
        regions = regions.clean()
        regions.children.sort(key=lambda r: r.geom.area)
        r = regions.children[0]
        contiguous = [cr for cr in regions.children if cr.touches(r)]
        contiguous.sort(key=lambda cr: cr.geom.area)

        #print("R: %s  Cont: %s" % (r, contiguous))
        #to_join = [c for c in contiguous if random.random() < 0.3]  # Join random neighbours
        to_join = [contiguous[0]]  # Join just the smallest neighbour

        joined_region = ddd.group2([r] + to_join).union()
        #ddd.group2([ddd.group2(to_join).material(ddd.mats.highlight), joined_region]).show()

        regions.remove(r)
        for c in to_join:
            regions.remove(c)

        regions.append(joined_region)

        regions = regions.clean()

    root.find("/Features2/Regions").replace(regions)
    #regions.show()

@dddtask(order="20.1", path="/Features2/Regions/*", log=True)
def features_regions_material_random(pipeline, root, logger, obj):
    materials = [getattr(ddd.mats, an) for an in dir(ddd.mats) if isinstance(getattr(ddd.mats, an), DDDMaterial)]
    obj = obj.material(random.choice(materials))
    return obj

@dddtask(order="20.1", log=True)
def features_regions_init(pipeline, root, logger):
    regions3 = ddd.group3(name="Regions3")
    root.find("/Features3").append(regions3)

@dddtask(order="20.1", path="/Features2/Regions/*", log=True)
def features_regions_random_height(pipeline, root, logger, obj):
    region3 = obj.extrude(random.randrange(1.0, 10.0))
    root.find("/Features3/Regions3").append(region3)

@dddtask(order="20.1", log=True)
def features_regions_show(pipeline, root, logger):
    root.find("/Features3/Regions3").show()



'''
@dddtask(log=True, path="/Features/*")
def osm_features_filter(pipeline, root, obj):
    filter_path = './Main/Scene/TestDevel/ZoneProc/DDDProc/Data'
    if not obj.extra['godot:node:path'].startswith(filter_path):
        return False

@dddtask(order="30.50.90.+", path="/Areas/*", select='[! "ddd:area:type"]')
def osm_groups_areas_remove_ignored(root, obj, logger):
    """Remove ignored areas."""
    return False


@dddtask(log=True)
def osm_features_preprocess(pipeline):
    #pipeline.data['osm'].preprocess_features()
    #pipeline.root.append(osm.features_2d)
    pass
'''



'''
@dddtask(log=True)
def osm_features_test_random(pipeline, root):

    features = ddd.group2(name="Features")

    extents = [3000, 3000]
    sizerange = [400, 1500]
    for i in range(20):
        #feat = ddd.polygon(coords, name=node.name)
        center = [random.uniform(-extents[0], extents[0]), random.uniform(-extents[1], extents[1])]
        size = [random.uniform(sizerange[0], sizerange[1]), random.uniform(sizerange[0], sizerange[1])]

        feat = ddd.rect([center[0] - size[0], center[1] - size[1], center[0] + size[0], center[1] + size[1]], name="Random")
        feat.extra['ddd:polygon:type'] = "hollow"
        feat = feat.rotate(random.uniform(0, math.pi * 2))

        features.append(feat)

    root.find("/Features").replace(features)
'''


'''
@dddtask(path="/Features/*", log=True)  # and o.geom.type in ('Point', 'Polygon', 'MultiPolygon') .. and o.geom.type == 'Polygon' |  ... path="/Features", select=r'["geom:type"="Polygon"]'
def osm_features_crop_extended_area(pipeline, osm, root, obj):
    """Crops to extended area size to avoid working with huge areas."""

    # TODO: Crop centroids of buildings and lines and entire areas...

    #pipeline.data['osm'].preprocess_features()
    #osm.preprocess_features()
    obj.extra['osm:original'] = obj.copy()
    obj = obj.intersection(osm.area_filter2)
    return obj

@dddtask(order="20.95.+", cache=True)
def osm_features_cache(pipeline, osm, root, logger):
    """
    Caches current state to allow for faster reruns.
    """
    return pipeline.data['filenamebase'] + ".s20.cache"
'''

