# Jose Juan Montes 2019-2020

'''
from ddd.ddd import ddd

ddd.initialize_logging()

obj = ddd.point([0, 0]).line_rel([0, 20]).line_rel([20, -5, -3]).line_rel([0, -15])
obj = obj.buffer(4.0).extrude(3.0)

obj2 = ddd.group([obj])
scene = ddd.group([obj2])

#scene.save()
scene.show()
scene.dump()
scene.save('gltf_hierarchy.glb')
#scene.save('golf01.dae')
'''

from trimesh import primitives
from trimesh.scene import scene

sphere = primitives.Sphere(radius=1.0)
scene1 = scene.Scene(sphere)
scene2 = scene.Scene(scene1)

print(scene1.dump())

#scene1.export("scene1.glb")  # Works
#scene1.show() # Works

#scene2.export("scene2.glb")  # Provides an invalid file
#scene2.show()  # Throws: ValueError: Geometry passed is not a viewable type!

