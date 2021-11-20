# DDD(123) - Library for procedural generation of 2D and 3D geometries and scenes
# Copyright (C) 2021 Jose Juan Montes
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from ddd.ddd import ddd
from ddd.pack.sketchy import urban, landscape, industrial, interior, sports, \
    vehicles, common, buildings
from ddd.pipeline.decorators import dddtask
from ddd.pack.sketchy.urban import lamppost, lamp_ball, roundedpost,\
    post_arm_angled


@dddtask()
def pipeline_test(pipeline, root):
    pass


@dddtask()
def pipeline_start(pipeline, root):

    ddd.mats.traffic_signs = ddd.material(name="TrafficSigns", color="#ffffff", #color="#e01010",
                                      texture_path=ddd.DATA_DIR  + "/materials/traffic-signs-es/traffic_signs_es_0.png",
                                      atlas_path=ddd.DATA_DIR  + "/materials/traffic-signs-es/traffic_signs_es_0.plist")


    items = ddd.group3()


    item = urban.lamppost_high_mast()
    items.append(item)

    item = buildings.portal()
    #item = ddd.meshops.batch_by_material(item)
    items.append(item)
    #item.show()

    item = buildings.door()
    items.append(item)
    #item.show()

    item = buildings.window_with_border()
    items.append(item)


    item = common.bar_u()
    items.append(item)


    item = urban.waste_container_dome()
    items.append(item)

    item = urban.waste_container_with_lid_closed()
    items.append(item)

    item = urban.waste_container()
    items.append(item)


    item = landscape.ladder_pool()
    items.append(item)

    item = sports.golf_flag()
    items.append(item)


    item = urban.drinking_water()
    items.append(item)

    item = urban.bollard()
    items.append(item)

    item = urban.bell()
    items.append(item)

    item = urban.fire_hydrant()
    items.append(item)


    item = urban.childrens_playground_swingset()
    items.append(item)

    item = urban.childrens_playground_sandbox()
    items.append(item)

    item = urban.childrens_playground_slide()
    items.append(item)

    item = urban.childrens_playground_arc()
    items.append(item)


    item = urban.patio_table()
    items.append(item)

    item = urban.patio_chair()
    items.append(item)

    item = urban.patio_umbrella()
    items.append(item)

    item = urban.post_box()
    items.append(item)

    item = urban.lamppost()
    items.append(item)

    item = urban.busstop_small(text="Bus Stop")
    items.append(item)

    item = urban.bench()
    items.append(item)

    item = urban.sculpture()
    items.append(item)

    item = urban.sculpture_text("Test")
    item = urban.pedestal(item)
    items.append(item)

    item = urban.sculpture_text("Monumental test string", vertical=True, height=12)
    items.append(item)


    item = urban.trafficlights()
    #item = item.rotate([0, 0, (math.pi / 4) - math.pi / 2])
    items.append(item)

    item = urban.fountain()
    items.append(item)

    item = urban.wayside_cross()
    items.append(item)

    item = urban.trash_bin()
    items.append(item)

    item = urban.trash_bin_post()
    items.append(item)

    # Road signs
    item = urban.traffic_sign('stop')
    items.append(item)
    #item.show()
    item = urban.traffic_sign('give_way')
    items.append(item)
    #item.show()
    item = urban.traffic_sign('es:s13')
    items.append(item)
    #item.show()
    item = urban.traffic_sign('es:p1')
    items.append(item)
    item = urban.traffic_sign('es:r101')
    items.append(item)
    item = urban.traffic_sign('es:r1')
    items.append(item)
    item = urban.traffic_sign('es:r2')
    items.append(item)
    item = urban.traffic_sign('es:r3')
    items.append(item)
    item = urban.traffic_sign('es:r6')
    items.append(item)
    item = urban.traffic_sign('es:r402')
    items.append(item)
    item = urban.traffic_sign('es:r500')
    items.append(item)
    item = urban.traffic_sign('es:r504')
    items.append(item)
    #item = urban.traffic_sign('es:r505-b')
    #items.append(item)
    item = urban.traffic_sign('es:r505')
    items.append(item)
    item = urban.traffic_sign('es:r506')
    items.append(item)


    #item.show()

    '''
    # Reduced
    items_org = items.copy()

    items = ddd.meshops.reduce(items_org)

    items = ddd.align.grid(items)
    items.append(ddd.helper.all())
    items.show()

    items = ddd.meshops.reduce_bounds(items_org)

    items = ddd.align.grid(items)
    items.append(ddd.helper.all())
    items.show()
    '''

    items = ddd.align.grid(items)
    items.append(ddd.helper.all())
    #items.show()
    #items.save("/tmp/test.glb")

    #items = ddd.meshops.batch_by_material(items)
    #items.dump()
    items.show()
    #items.save("/tmp/test.json")

    pipeline.root = items

