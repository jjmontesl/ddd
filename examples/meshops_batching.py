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
from ddd.pack.sketchy import printing, rooftops, sports_fields, urban, landscape, industrial, interior, vehicles, common, buildings
from ddd.pipeline.decorators import dddtask
from ddd.pack.sketchy.urban import lamppost, lamp_ball, roundedpost,\
    post_arm_angled


"""
Show and test batching of objects with children and transforms.
"""


@dddtask()
def pipeline_start(pipeline, root):

    items = ddd.group3()

    # Test batching of objects with children and transforms

    item = rooftops.antenna_mast()
    items.append(item)
    
    item = buildings.door()
    items.append(item)

    item = buildings.portal()
    items.append(item)

    items = ddd.align.grid(items)

    #items = items.apply_transform()
    #items = items.flatten()
    #items = ddd.meshops.batch_group(items)
    items = ddd.meshops.batch_by_material(items)

    items.append(ddd.helper.all())
    #items.show()
    #items.save("/tmp/test.glb")

    #items = ddd.meshops.batch_by_material(items)
    items.dump(data=True)
    items.show()
    #items.save("/tmp/test.json")

    pipeline.root = items

