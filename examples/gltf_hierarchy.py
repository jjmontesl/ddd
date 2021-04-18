# Jose Juan Montes 2019-2021

"""
This example simply tests GLTF/GLB export, in order to check that node names,
hierarchy, transforms, properties and metadata are preserved.
"""


import json

from trimesh import primitives, transformations
from trimesh.scene import scene
import trimesh

from ddd.ddd import ddd


test_metadata = {'test_key_str': 'test_value',
                 'test_key_int': 1,
                 'test_key_float': 0.123456789,
                 'test_key_bool': True,
                 'test_array': [1, 2, 3],
                 'test_dict': {'a': 1, 'b': 2},
                 }


# Export using Trimesh
def gltf_trimesh():
    sphere1 = primitives.Sphere(radius=1.0)
    sphere2 = primitives.Sphere(radius=2.0)

    # transformations.euler_from_quaternion(obj.transform.rotation, axes='sxyz')
    node1_transform = transformations.translation_matrix([0, 0, -2])
    node2_transform = transformations.translation_matrix([5, 5, 5])

    scene1 = scene.Scene()
    scene1.add_geometry(sphere1, node_name="Sphere1", geom_name="Geom Sphere1", transform=node1_transform, extras=test_metadata)
    scene1.add_geometry(sphere2, node_name="Sphere2", geom_name="Geom Sphere2", parent_node_name="Sphere1", transform=node2_transform, extras=test_metadata)

    scene1.metadata['extras'] = test_metadata

    files = scene1.export(None, "gltf")  #, extras=test_metadata)
    print(files["model.gltf"].decode('utf8'))
    #for k, v in files.items():
    #    print(k, v)
    #"gltf-hierarchy-trimesh.gltf"
    #scene1.show()

    # Save scene with extras
    scene1.export("gltf-hierarchy-trimesh.glb")  #, extras=test_metadata)

    '''
    # Check metadata survives a roundtrip
    # export as GLB then re-load
    r = trimesh.load(
        trimesh.util.wrap_as_stream(
            scene1.export(file_type='glb')),
        file_type='glb')
    #r.show()
    files = r.export(None, "gltf")
    print(files["model.gltf"].decode('utf8'))
    print(r.graph.transforms.get_edge_data("world", "Sphere1")['extras'])
    '''


# Export using DDD
def gltf_ddd():
    sphere1 = ddd.sphere(r=1.0, name="Sphere1").translate([0, 0, -2])
    sphere2 = ddd.sphere(r=2.0, name="Sphere2").translate([5, 5, 5])
    sphere1.append(sphere2)
    sphere1.extra['testSphere1'] = 'MyTest'
    sphere2.extra.update(test_metadata)
    sphere2.extra['test_obj'] = test_metadata

    root = ddd.group([sphere1], name="Spheres Root")

    scene1 = ddd.group([root], name="Scene")
    scene1.extra['test'] = test_metadata

    scene1.dump()
    scene1.save("gltf-hierarchy-ddd.glb")
    scene1.show()


#gltf_trimesh()
gltf_ddd()




