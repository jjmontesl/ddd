# ddd - DDD123
# Library for procedural scene modelling.
# Jose Juan Montes 2020

from ddd.ddd import ddd
from ddd.pipeline.decorators import dddtask
from ddd.core.exception import DDDException
from ddd.pack.sketchy import sports
from ddd.util.dddrandom import weighted_choice

#@dddgroupgeocondition(select='osm.center [contains()')
@dddtask(order="10.10.+.+")  # [!contains(["natural"="tree"])]
def osm_config_locale(root, osm, pipeline):
    pass

#@dddcondition
def osm_config_locale_es_salamanca(root, osm, pipeline):
    config = ddd.point([-5.664, 40.965])
    config.extra['osm:tree:type'] = lambda: weighted_choice({'default': 1, 'fir': 0.5})
    #config.extra['ddd:aug:itemfill:types'] = {'default': 1, 'fir': 1}

    pipeline['ddd:config:items'].append(config)


def osm_config_locale_es_vigo(root, osm, pipeline):
    config = ddd.point([-5.664, 40.965])
    config.extra['osm:tree:type'] = lambda: weighted_choice({'default': 1, 'fir': 1, 'palm': 0.25})
    #config.extra['ddd:aug:itemfill:types'] = {'default': 1, 'fir': 1}

    pipeline['ddd:config:items'].append(config)

def osm_config_locale_es_vilanovailageltru(root, osm, pipeline):
    config = ddd.point([-5.664, 40.965])
    config.extra['osm:tree:type'] = lambda: weighted_choice({'default': 0.5, 'fir': 0.25, 'palm': 1})
    #config.extra['ddd:aug:itemfill:types'] = {'default': 1, 'fir': 1}

    pipeline['ddd:config:items'].append(config)


