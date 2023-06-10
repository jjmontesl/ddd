# Jose Juan Montes 2019-2020

import math

from trimesh import transformations

from ddd.ddd import ddd
from ddd.materials.atlas import TextureAtlasUtils
from ddd.pack.sketchy import interior
from ddd.pipeline.decorators import dddtask
from ddd.text.text3d import Text3D


@dddtask()
def example_transforms(pipeline, root):
    """
    """

    root = ddd.DDDNode3()  # Doesn't seem to impact, but just in case during dev ensure we use only DDDNode3

    def create_label(label):
        #return interior.furniture_test_out_in()
        text3d = Text3D()
        result = text3d.text(label)
        result = result.extrude(0.1).recenter().material(ddd.MAT_HIGHLIGHT)
        #result = result.translate([0, 2, 0])
        #result.transform.rotate(ddd.ROT_FLOOR_TO_FRONT)
        result = result.rotate(ddd.ROT_FLOOR_TO_FRONT)
        result.transform.translate([0, 0, 2])
        #return ddd.DDDNode3(name=label).material(ddd.MAT_HIGHLIGHT)
        return result

    sun = ddd.sphere(r=5, name="Sun").material(ddd.mats.orange)
    #sun.transform.rotation = transformations.quaternion_from_euler(0, 0 * ddd.DEG_TO_RAD, 10 * ddd.DEG_TO_RAD, "sxyz")
    sun.transform.rotate([0, -5 * ddd.DEG_TO_RAD, 45 * ddd.DEG_TO_RAD])
    sun = ddd.uv.map_cubic(sun).material(ddd.MAT_TEST)
    sun.append(create_label("Sun"))

    planet = ddd.sphere(r=0.38, name="Venus").material(ddd.mats.violet)
    planet.transform.rotation = transformations.quaternion_from_euler(0, 0, 15 * ddd.DEG_TO_RAD, "sxyz")
    planet.transform.position = [0.72 * 10, 0, 0]
    planet.append(create_label("V"))
    sun.append(planet)

    planet = ddd.sphere(r=1, name="Earth").material(ddd.mats.blue)
    planet.transform.rotation = transformations.quaternion_from_euler(0, 0, 30 * ddd.DEG_TO_RAD, "sxyz")
    planet.transform.position = [10, 0, 0]
    planet.append(create_label("E"))
    sun.append(planet)

    moon = ddd.sphere(r=0.25, name="Moon").material(ddd.mats.rock)
    moon.transform.position = [1.4, 0, 0]
    moon.append(create_label("m"))
    planet.append(moon)

    planet = ddd.sphere(r=0.532, name="Mars").material(ddd.mats.red)
    #planet.transform.rotation = transformations.quaternion_from_euler(0, 0, 15 * ddd.DEG_TO_RAD, "sxyz")
    planet.transform.position = [0, 1.53 * 10, 0]
    planet.append(create_label("M"))
    sun.append(planet)

    # Ground plane
    root.append(sun)
    root.append(ddd.helper.grid_xy(30.0).recenter())

    # Transform (towards back, like when exporting to some formats)
    # This test uses rotate() over the whole hierarchy (thereby changing the "up" vector), then translates the copy in world space to the right using transform.translate().
    sun_front = sun.copy()
    sun_front = sun_front.rotate([-math.pi / 2.0, 0, 0])  # ddd.ROT_FLOOR_TO_FRONT
    #sun_front.transform.rotate([-math.pi / 2.0, 0, 0])  
    #sun_front = sun_front.translate([30, 0, 0])
    sun_front.transform.translate([30, 0, 0]) 
    root.append(sun_front)
    grid_front = ddd.helper.grid_xy(30.0).recenter()
    grid_front.transform.rotate([-math.pi / 2.0, 0, 0])
    grid_front.transform.translate([30, 0, 0])
    root.append(grid_front)

    
    root.dump(data='ddd')
    root.show()
    root.save("/tmp/transforms.glb")
    root.save("/tmp/transforms.fbx")

