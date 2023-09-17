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
from ddd.pack.sketchy import (appliances, bathroom, buildings, common, industrial,
                              interior, printing, urban, toys
                              )
from ddd.pipeline.decorators import dddtask


@dddtask()
def pipeline_test(pipeline, root):
    pass


@dddtask()
def pipeline_start(pipeline, root):

    items = ddd.group3()

    
    item = toys.ball_soccer()
    items.append(item)

    item = toys.ball_basketball()
    items.append(item)

    item = toys.ball_golf()
    items.append(item)

    item = toys.ball_american_football()
    item.show()
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

