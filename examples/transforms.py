# Jose Juan Montes 2019-2020

from ddd.ddd import ddd
from ddd.materials.atlas import TextureAtlasUtils
from ddd.pipeline.decorators import dddtask
from ddd.pack.sketchy import interior
from trimesh import transformations
import math


@dddtask()
def example_transforms(pipeline, root):
    """
    """

    root = ddd.DDDNode3()  # Doesn't seem to impact, but just in case during dev ensure we use only DDDNode3

    sun = ddd.sphere(r=5, name="Sun").material(ddd.mats.orange)
    sun.transform.rotation = transformations.quaternion_from_euler(0, -5 * ddd.DEG_TO_RAD, 45 * ddd.DEG_TO_RAD, "sxyz")
    sun = ddd.uv.map_cubic(sun).material(ddd.MAT_TEST)
    sun.append(interior.furniture_test_out_in())

    planet = ddd.sphere(r=0.38, name="Venus").material(ddd.mats.violet)
    planet.transform.rotation = transformations.quaternion_from_euler(0, 0, 15 * ddd.DEG_TO_RAD, "sxyz")
    planet.transform.position = [0.72 * 10, 0, 0]
    planet.append(interior.furniture_test_out_in())
    sun.append(planet)

    planet = ddd.sphere(r=1, name="Earth").material(ddd.mats.blue)
    planet.transform.rotation = transformations.quaternion_from_euler(0, 0, 30 * ddd.DEG_TO_RAD, "sxyz")
    planet.transform.position = [10, 0, 0]
    planet.append(interior.furniture_test_out_in())
    sun.append(planet)

    moon = ddd.sphere(r=0.25, name="Moon").material(ddd.mats.rock)
    moon.transform.position = [1.4, 0, 0]
    moon.append(interior.furniture_test_out_in())
    planet.append(moon)

    planet = ddd.sphere(r=0.532, name="Mars").material(ddd.mats.red)
    #planet.transform.rotation = transformations.quaternion_from_euler(0, 0, 15 * ddd.DEG_TO_RAD, "sxyz")
    planet.transform.position = [0, 1.53 * 10, 0]
    planet.append(interior.furniture_test_out_in())
    sun.append(planet)

    #wsun = sun.rotate(ddd.ROT_FLOOR_TO_FRONT)
    #sun.transform.rotation = transformations.quaternion_from_euler(ddd.PI_OVER_2, 0, 0, "sxyz")

    root.append(sun)

    #root = root.rotate([ddd.PI_OVER_2, 0, 0])
    #root = root.rotate([-ddd.PI_OVER_2, 0, 0])

    root.append(ddd.helper.grid_xy(40.0).recenter())

    root.dump(data='ddd')
    root.show()
    root.save("/tmp/transforms.glb")
    root.save("/tmp/transforms.fbx")

