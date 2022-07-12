# Jose Juan Montes 2019-2020

from ddd.ddd import ddd
from ddd.materials.atlas import TextureAtlasUtils
from ddd.pipeline.decorators import dddtask
import math


@dddtask()
def example_transforms(pipeline, root):
    """
    """

    sun = ddd.sphere(r=5, name="Sun").material(ddd.mats.orange)
    root.append(sun)

    planet = ddd.sphere(name="Planet").material(ddd.mats.blue)
    planet.transform.translate([10, 0, 0])
    sun.append(planet)

    moon = ddd.sphere(r=0.25, name="Moon").material(ddd.mats.rock)
    moon.transform.translate([2, 0, 0])
    planet.append(moon)


