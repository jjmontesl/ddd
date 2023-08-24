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
from ddd.pack.sketchy import (appliances, buildings, common, industrial,
                              interior, printing, urban,
                              )
from ddd.pack.sketchy.urban import (lamp_ball, lamppost, post_arm_angled,
                                    roundedpost)
from ddd.pipeline.decorators import dddtask


@dddtask()
def pipeline_test(pipeline, root):
    pass


@dddtask()
def pipeline_start(pipeline, root):

    ddd.mats.traffic_signs = ddd.material(name="TrafficSigns", color="#ffffff", #color="#e01010",
                                      texture_path=ddd.DATA_DIR  + "/materials/traffic-signs-es/traffic_signs_es_0.png",
                                      atlas_path=ddd.DATA_DIR  + "/materials/traffic-signs-es/traffic_signs_es_0.plist")


    items = ddd.group3()

    
    item = appliances.clock_wall_round()
    items.append(item)

    item = appliances.clock_wall_round_framed()
    #item.show()
    items.append(item)

    item = interior.plant_pot(earth_height_norm = 0.85)
    #item.show()
    items.append(item)

    item = interior.plant_pot()
    #item.show()
    items.append(item)

    item = printing.poster_ripped()
    #item.show()
    items.append(item)

    item = printing.poster_flat()
    items.append(item)

    item = printing.text_note()
    #item.show()
    items.append(item)

    item = printing.text_note_teared()
    #item.show()
    items.append(item)

    
    item = interior.furniture_test_out_in()
    #item.show()
    items.append(item)

    item = interior.drawer()
    items.append(item)

    item = interior.cabinet_door_raised()
    items.append(item)

    item = industrial.crate()
    items.append(item)

    item = buildings.door()
    #item.show()
    items.append(item)

    #item = buildings.door()
    ##item.show()
    #items.append(item)
    

    item = buildings.window_with_border()
    items.append(item)

    item = buildings.window_with_border_and_grille(grille=(3,2))
    items.append(item)
    #item.show()

    
    item = common.bar_u()
    items.append(item)

    item = urban.patio_table()
    items.append(item)

    item = urban.patio_chair()
    items.append(item)

    item = urban.drinking_water()
    items.append(item)

    
    item = interior.paper_bin_basket()
    items.append(item)

    item = urban.trash_bin()
    items.append(item)

    item = urban.trash_bin_post()
    items.append(item)




    items = ddd.align.grid(items, space=4)
    items.append(ddd.helper.all())
    #items.show()
    #items.save("/tmp/test.glb")

    #items = ddd.meshops.batch_by_material(items)
    #items.dump()
    items.show()
    #items.save("/tmp/test.json")

    pipeline.root = items

