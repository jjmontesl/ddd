# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020


from ddd.osm import osm
from ddd.pipeline.decorators import dddtask
from ddd.ddd import ddd
import random
import noise
from ddd.util import dddrandom




@dddtask(order="55.52", condition=True)
def osm_augment_rocks_condition(pipeline):
    """
    Run rock augmentation only if so configured (ddd:osm:augment:rocks=True).
    """
    return bool(pipeline.data.get('ddd:osm:augment:rocks', True))


# Generate grass
# TODO: Do this per area type, separate augment tagging like for plants, so it can be set earlier
@dddtask(order="55.52.+", path="/Areas/*", select='["ddd:material" ~ "Park|Forest|Rock|Ground|Dirt|Ground Clear"];["osm:natural" = "scree"]')
def osm_augment_rocks_generate_rocks(obj, osm, root):
    """
    """
    item_density_m2 = 0.5 / 1000.0
    num_items = int((obj.area() * item_density_m2))

    def filter_func_noise(coords):
        val = noise.pnoise2(coords[0], coords[1], octaves=2, persistence=0.5, lacunarity=2, repeatx=1024, repeaty=1024, base=0)
        return (val > random.uniform(-0.5, 0.5))

    items = ddd.group2(name='Rocks: %s' % obj.name)
    for p in obj.random_points(num_points=num_items, filter_func=filter_func_noise):
        item = ddd.point(p, name="Rock")
        #item.extra['ddd:aug:status'] = 'added'
        item.extra['ddd:item'] = 'natural_rock'
        item.extra['ddd:angle'] = ddd.random.angle()
        items.append(item)

    root.find("/ItemsNodes").append(items.children)


