# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020


from ddd.pipeline.decorators import dddtask
from ddd.ddd import ddd


@dddtask(order="40.90", condition=True)
def osm_structured_export_2d_condition(pipeline):
    return bool(pipeline.data.get('ddd:godot:output:intermediate', False))


@dddtask(order="40.90.+")
def osm_structured_export_2d(root, pipeline):

    root = root.copy()
    root = root.remove(root.find("/Features"))  # !Altering
    root.set('svg:stroke-width', 0.1, children=True)
    root.set('svg:fill-opacity', 0.7, children=True)

    #root.find("/Areas").replace(root.find("/Areas").material(ddd.mats.park).set('svg:fill-opacity', 0.6, True))
    #root.find("/Ways").replace(root.find("/Ways").buffer(1.0).material(ddd.mats.asphalt).set('svg:fill-opacity', 0.8, True))
    #root.find("/Buildings").replace(root.find("/Buildings").material(ddd.mats.stone).set('svg:fill-opacity', 0.7, True))
    #root.find("/Items").replace(root.find("/Items").buffer(1.0).material(ddd.mats.highlight))

    if bool(pipeline.data.get('ddd:osm:output:json', False)):
        root.save("/tmp/osm-structured.json")

    root.save("/tmp/osm-structured.svg")


@dddtask(order="40.90.+")
def osm_structured_export_2d_tile(root, osm, pipeline):
    """Save a cropped tileable 2D image of the scene."""

    tile = ddd.group2([
        ddd.shape(osm.area_crop).material(ddd.material(color='#ffffff')),  # White background (?)
        #self.ground_2d,
        root.select(path="/Water", recurse=False),
        root.select(path="/Areas", recurse=False),
        root.select(path="/Ways", recurse=False),  #, select="")  self.ways_2d['-1a'], self.ways_2d['0'], self.ways_2d['0a'], self.ways_2d['1'],
        root.select(path="/Roadlines2", recurse=False),
        root.select(path="/Buildings", recurse=False),
        #self.areas_2d_objects, self.buildings_2d.material(ddd.material(color='#8a857f')),
        root.select(path="/ItemsAreas", recurse=False),  #self.items_2d,
        root.select(path="/ItemsWays", recurse=False),  #self.items_2d,
        root.select(path="/ItemsNodes", recurse=False).buffer(0.5).material(ddd.mats.red),

    ]).flatten().select(func=lambda o: o.extra.get('ddd:area:type') != 'underwater')

    tile = tile.intersection(ddd.shape(osm.area_crop))
    tile = tile.clean()
    tile.set('svg:stroke-width', 0.01, children=True)

    path = pipeline.data['filenamebase'] + ".png"
    tile.save(path)

    tile.save("/tmp/osm-structured.png")

