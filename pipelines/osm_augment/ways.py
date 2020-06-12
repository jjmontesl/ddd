# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020


from ddd.ddd import ddd
from ddd.geo import terrain
from ddd.osm import osm
from ddd.pipeline.decorators import dddtask

# Lamps, signs, traffic signals, road signs, roadlines...

@dddtask(order="40.80.+.+")
def osm_augment_ways2_generate_props(root, osm, pipeline, logger):
    # TODO: This shall be moved to augmentation, etc... and not pass root around
    # Separate different things: roadlines, etc...
    # Road props (traffic lights, lampposts, fountains, football fields...) - needs. roads, areas, coastline, etc... and buildings
    pass
