# Jose Juan Montes 2019-2020

from ddd.ddd import ddd
from ddd.materials.atlas import TextureAtlasUtils
from ddd.pipeline.decorators import dddtask
import math


@dddtask(order="10",
         params={
             'ddd:example:catenary:length_ratio_factor': 0.025
        })
def pipeline_start(pipeline, root):
    """
    Draws several catenary cables.
    """

    ddd.mats.traffic_signs = ddd.material(name="TrafficSigns", color="#ffffff", #color="#e01010",
                                      texture_path=ddd.DATA_DIR  + "/materials/traffic-signs-es/traffic_signs_es_0.png",
                                      atlas_path=ddd.DATA_DIR  + "/materials/traffic-signs-es/traffic_signs_es_0.plist",
                                      extra={'ddd:texture:resize': 2048})


    items = ddd.group3()

    # Cube with logo
    fig = ddd.box()
    fig = fig.material(ddd.mats.logo)
    fig = ddd.uv.map_cubic(fig)
    items.append(fig)

    # Sphere with logo
    fig = ddd.sphere()
    fig = fig.material(ddd.mats.logo)
    #fig = fig.merge_vertices()
    #fig = fig.smooth(math.pi*2)
    fig = ddd.uv.map_spherical(fig)
    fig = fig.translate([0, 0, 2])
    items.append(fig)

    fig = ddd.sphere()
    fig = fig.material(ddd.mats.logo)
    #fig = fig.merge_vertices()
    #fig = fig.smooth(math.pi*2)
    fig = ddd.uv.map_spherical(fig, scale=[2.0, 2.0])
    fig = fig.translate([0, 0, 2])
    items.append(fig)

    # Cylinder with logo
    fig = ddd.cylinder(height=2, r=1.0)
    fig = fig.material(ddd.mats.logo)
    fig = ddd.uv.map_cylindrical(fig)
    fig = fig.translate([0, 0, 2])
    items.append(fig)

    fig = ddd.cylinder(height=2, r=1.0)
    fig = fig.material(ddd.mats.logo)
    fig = ddd.uv.map_cylindrical(fig, scale=[2.0, 2.0])
    fig = fig.translate([0, 0, 2])
    items.append(fig)

    # Cube
    fig = ddd.box()
    fig = fig.material(ddd.mats.traffic_signs)
    fig = ddd.uv.map_cubic(fig)
    #fig.show()
    items.append(fig)

    fig = TextureAtlasUtils().create_sprite_rect(ddd.mats.traffic_signs)
    fig = fig.triangulate().rotate(ddd.ROT_FLOOR_TO_FRONT)
    #fig.show()
    items.append(fig)

    fig = TextureAtlasUtils().create_sprite_from_atlas(ddd.mats.traffic_signs, "ES_P6.png")
    fig = fig.triangulate().rotate(ddd.ROT_FLOOR_TO_FRONT)
    #fig.show()
    items.append(fig)


    '''
    ddd.mats.roadmarks = ddd.material(name="Roadmarks", color='#e8e8e8',
                                 texture_path=ddd.DATA_DIR + "/materials/road-marks-es/TexturesCom_Atlas_RoadMarkings2_White_1K_albedo_with_alpha.png",
                                 atlas_path=ddd.DATA_DIR  + "/materials/road-marks-es/RoadMarkings2.plist")

    fig = TextureAtlasUtils().create_sprite_from_atlas(ddd.mats.roadmarks, "give_way")
    fig.show()
    '''

    items = ddd.align.grid(items, width=4)
    items.append(ddd.helper.all(size=40.0, center=[5, 5, 0]).twosided())

    root.append(items)

    root.show()

