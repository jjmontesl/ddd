# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020


from ddd.pipeline.decorators import dddtask
from godot_parser import GDScene, GDObject, Node
from godot_parser.files import GDResource

def coords_to_godot_vector2array(coords):
    # TODO: Return the actual GDObject("..."=
    v = []
    for c in coords:
        v.append(c[0])
        v.append(c[1])
    return v

def color_to_godot_color(value):
    #TODO: Support hex notation
    value = [x / 255.0 for x in value]
    return GDObject("Color", *value)


@dddtask(order="69.90.+")
def godot_export_scene(root, pipeline, logger):

    root.dump()

    scene = GDScene()

    extresources = {}

    with scene.use_tree() as tree:
        tree.root = Node("Scene", type="Node2D")
        idx = 0

        rooms = root.find("/Rooms")
        rooms = rooms.individualize().flatten().clean()
        for obj in rooms.children:
            idx += 1
            nodename = obj.name.replace(":", "_")

            # TODO: Resolve material and extra properties earlier, as this is copied in every place it's used.
            # TODO: Moreover, in this case, this is modifying object metadata directly.
            if obj.mat and obj.mat.extra:
                obj.extra.update({k: v for k, v in obj.mat.extra.items()})


            if obj.extra.get('ddd:sprite', False):
                gdnode = Node(nodename + "_" + str(idx),
                              type="Sprite",
                              properties={'position': GDObject("Vector2", *obj.centroid().geom.coords[0]) } )
                tree.root.add_child(gdnode)

                if obj.extra.get('ddd:sprite:bounds', None):
                    gdnode['region_enabled'] = True
                    gdnode['region_rect'] = GDObject("Rect2", obj.extra['ddd:sprite:bounds'][0],
                                                              obj.extra['ddd:sprite:bounds'][1],
                                                              obj.extra['ddd:sprite:bounds'][2] - obj.extra['ddd:sprite:bounds'][0],
                                                              obj.extra['ddd:sprite:bounds'][3] - obj.extra['ddd:sprite:bounds'][1])

            else:
                polygon = GDObject("PoolVector2Array", *coords_to_godot_vector2array(obj.geom.exterior.coords))
                gdnode = Node(nodename + "_" + str(idx),
                              type="Polygon2D",
                              properties={'polygon': polygon})
                tree.root.add_child(gdnode)

                if obj.get('uv', None):
                    uvs = obj.get('uv')
                    # TODO: Do not transpose here! transpose when assigining UVs (this was done to overcome uvmapping.path_2d working on Y not X)
                    uvs = [(uv[1], uv[0]) for uv in uvs]
                    uvs = GDObject("PoolVector2Array", *coords_to_godot_vector2array(uvs))
                    gdnode['uv'] = uvs


            if obj.extra.get('ddd:collider', False):
                gdstaticbody = Node("StaticBody2D",
                                    type="StaticBody2D",
                                    properties={'collision_layer': 16})
                gdnode.add_child(gdstaticbody)

                gdcollider = Node("CollisionPolygon2D",
                                  type="CollisionPolygon2D",
                                  properties={'polygon': polygon})
                gdstaticbody.add_child(gdcollider)

            if obj.extra.get('ddd:occluder', False):

                occluderpolygon_res = scene.add_sub_resource("OccluderPolygon2D",
                                                             polygon = polygon)

                gdstaticbody = Node("LightOccluder2D",
                                    type="LightOccluder2D",
                                    properties={'occluder': occluderpolygon_res.reference})
                gdnode.add_child(gdstaticbody)

            if obj.mat:
                if obj.mat.color:
                    gdnode['self_modulate'] = GDObject("Color", *[x / 255.0 for x in obj.mat.color_rgba])

                if obj.mat.texture:
                    if obj.mat.texture not in extresources:
                        extresources[obj.mat.texture] = scene.add_ext_resource("res://" + obj.mat.texture, "Texture")
                    texture_res = extresources[obj.mat.texture]
                    gdnode['texture'] = texture_res.reference

                    if obj.mat.texture_normal:
                        if obj.mat.texture_normal not in extresources:
                            extresources[obj.mat.texture_normal] = scene.add_ext_resource("res://" + obj.mat.texture_normal, "Texture")
                        texture_res = extresources[obj.mat.texture_normal]
                        gdnode['normal_map'] = texture_res.reference

                    #gdnode['texture_scale'] = GDObject("Vector2", 2.0, 1.0)  # TODO: this is temp For grass tests

                if obj.get('godot:material:resource', None):
                    mat_res_path = obj.get('godot:material:resource')
                    if mat_res_path not in extresources:
                        extresources[mat_res_path] = scene.add_ext_resource(mat_res_path, "Material")
                    mat_res = extresources[mat_res_path]
                    gdnode['material'] = mat_res.reference


            if 'ddd:z_index' in obj.extra:
                gdnode['z_index'] = obj.extra['ddd:z_index']
                gdnode['z_as_relative'] = False

            if 'ddd:angle' in obj.extra:
                gdnode['rotation'] = obj.extra['ddd:angle']
            if 'godot:scale' in obj.extra:
                gdnode['scale'] = GDObject("Vector2", *obj.extra['godot:scale'])

            if 'godot:texture_rotation' in obj.extra:
                gdnode['texture_rotation'] = obj.extra['godot:texture_rotation']
            if 'godot:texture_scale' in obj.extra:
                gdnode['texture_scale'] = GDObject("Vector2", *obj.extra['godot:texture_scale'])

            if 'godot:self_modulate' in obj.extra:
                gdnode['self_modulate'] = color_to_godot_color(obj.extra['godot:self_modulate'])
            if 'godot:light_mask' in obj.extra:
                gdnode['light_mask'] = obj.extra['godot:light_mask']


        nodes = root.find("/Items")
        #nodes = nodes.individualize().flatten().clean()
        for obj in nodes.children:
            idx += 1
            nodename = obj.name.replace(":", "_")

            gdnode = None

            if obj.extra.get('godot:instance', False):

                if obj.extra['godot:instance'] not in extresources:
                    extresources[obj.extra['godot:instance']] = scene.add_ext_resource(obj.extra['godot:instance'], "PackedScene")
                packedscene = extresources[obj.extra['godot:instance']]

                gdnode = Node(nodename + "_" + str(idx),
                              instance=packedscene.id,
                              properties={'position': GDObject("Vector2", obj.geom.coords[0][0], obj.geom.coords[0][1])})
                tree.root.add_child(gdnode)

            #if obj.mat and obj.mat.color:
            #    gdnode['self_modulate'] = GDObject("Color", *[x / 255.0 for x in obj.mat.color_rgba])

            if 'ddd:z_index' in obj.extra:
                gdnode['z_index'] = obj.extra['ddd:z_index']
                gdnode['z_as_relative'] = False

            if 'ddd:angle' in obj.extra:
                gdnode['rotation'] = obj.extra['ddd:angle']
            if 'godot:scale' in obj.extra:
                gdnode['scale'] = GDObject("Vector2", *obj.extra['godot:scale'])

            if 'godot:self_modulate' in obj.extra:
                gdnode['self_modulate'] = color_to_godot_color(obj.extra['godot:self_modulate'])
            if 'godot:light_mask' in obj.extra:
                gdnode['light_mask'] = obj.extra['godot:light_mask']


    output_path = "/tmp/ddd-godot.tscn"
    logger.info("Writing to: %s" % (output_path,))
    scene.write(output_path)




    """
    #root = root.copy()
    #root.find("/Areas").replace(root.find("/Areas").material(ddd.mats.park).prop_set('svg:fill-opacity', 0.6, True))
    #root.find("/Ways").replace(root.find("/Ways").buffer(1.0).material(ddd.mats.asphalt).prop_set('svg:fill-opacity', 0.8, True))
    #root.find("/Buildings").replace(root.find("/Buildings").material(ddd.mats.stone).prop_set('svg:fill-opacity', 0.7, True))
    #root.find("/Items").replace(root.find("/Items").buffer(1.0).material(ddd.mats.highlight))

    if bool(pipeline.data.get('ddd:osm:output:json', False)):
        root.save("/tmp/osm-model.json")

    #if bool(pipeline.data.get('ddd:osm:output:intermediate', False)):
    root.save("/tmp/osm-model.glb")

    root.save(pipeline.data['filenamebase'] + ".glb")

    #scene.dump()
    """

