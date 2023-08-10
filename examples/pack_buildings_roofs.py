# Jose Juan Montes 2019-2023

from ddd.ddd import ddd
from ddd.pack.sketchy import urban, landscape, industrial
from ddd.pack.buildings.roof import roof_common
from ddd.pipeline.decorators import dddtask


@dddtask()
def pipeline_start(pipeline, root):

    items = ddd.group3()

    footprint_rect = ddd.rect([[0, 0], [4, 7]], name="Footprint Rect")
    footprint_l = ddd.rect([[0, 0], [4, 9]]).union(ddd.rect([[0, 0], [7, 4]])).clean(eps=0.01).setname("Footprint L")

    heights = (3.0, )  # 8.0)

    for height in heights:

        for footprint in (footprint_rect, footprint_l):

            walls = footprint.subtract(footprint.buffer(-0.2))

            roof_func_kwargs = [
                {},
                {"roof_buffer": 0.5}
            ]

            for func_kwargs in roof_func_kwargs:

                #footprint.show()
                building = walls.extrude(height)
                building = building.material(ddd.mats.bricks)
                building = ddd.uv.map_cubic(building)
                
                roof = roof_common.roof_gabled(footprint, **func_kwargs)
                roof = roof.material(ddd.mats.roof_tiles)
                #roof = ddd.uv.map_cubic(roof)
                
                base = footprint.triangulate()
                base = base.material(ddd.mats.cement)

                building.append(roof.translate([0, 0, height]))
                building.append(base)

                items.append(building)
    
    items = ddd.align.grid(items, 10.0)
    items.append(ddd.helper.all())

    root.append(items)

    root.show()
