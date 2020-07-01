# Jose Juan Montes 2020


from ddd.pack.sketchy import urban, landscape, sports
from ddd.ddd import ddd
import math
from csv import DictReader
from ddd.pipeline.pipeline import DDDPipeline
from ddd.pipeline.decorators import dddtask
import logging


"""
An example of a configurable processing pipeline in DDD.

This gets an list of atomic elements and displays them
after several processing and styling steps.
"""


# Get instance of logger for this module
logger = logging.getLogger(__name__)


### wikipedia_articles.py

### wikipedia_elements.py

#@stage("generate_scenario", depends=None)
#@stage("generate_articles", depends="generate_scenario")

@dddtask(order="10")
def start_run(root):
    """
    Run at initial stage, load data.
    """
    # Get features (depends on the process)
    features = ddd.group2()
    with open("../data/periodictable/periodictable.csv") as f:
        csv = DictReader(f)
        for row in csv:
            feature = ddd.point(name="Element: %s" % row['Element'])
            for k in row.keys():
                feature.extra['element:' + k.lower()] = row[k]
            '''
            feature.extra['element:number'] =
            feature.extra['csv:number'] =
            feature.extra['csv:year'] =
            feature.extra['csv:name'] =
            feature.extra['csv:symbol'] =
            '''
            features.append(feature)

    features.name="Elements2"
    root.append(features)
    #root.dump()

@dddtask(parent="generate_scenario")
def generate_scenario_run(root):
    """
    Create a circular platform for articles.
    Hill size according to importance
    """
    elements = root.find("/Elements2")
    num_items = elements.count()
    logger.info("Num elements: %s", num_items)
    distance = (num_items * 10) / (2 * math.pi)
    #result = ddd.align.polar(elements, d=distance)
    result = ddd.align.grid(elements)
    elements.replace(result)

    elements3 = ddd.group3(name="Elements3")
    root.append(elements3)

    #result.buffer(1.0).show()
    #root.dump()

@dddtask(parent="generate_scenario")
def generate_scenario_run_plus(root):
    """
    Create a periodic table platform for articles.
    Block height size according to importance.
    """
    num_articles = root.select(path='/Elements/*').count()
    # Create grid

#@dddtask(select=None, path=None)  # parent=?, after="", before="",
#def decorate_something(root, o):
#    pass

'''
@dddtask(path="/Elements2/*", parent="generate_articles")  # select="wp:article=*",
def each(root, obj):
    pass
'''

@dddtask(path="/Elements2/*", filter=lambda o: 'element:symbol' in o.extra, parent="generate_articles")  # select="wp:article=*",
def each(root, obj):
    """
    Create a pilar for each element.

    - Position according to periodic table.
    - Letter size according to importance
    - Order according to discovery/synthesis

    - Atom on column (same height, must be easy to see)
    - Nucleus and electrons in orbitals / layers (maybe both models, one 2D smaller) - Rotating
    """
    logger.info("Creating: %s", obj)

    if not (obj.extra['element:group'] and obj.extra['element:period']):
        logger.info("Ignoring element (no group or period): %s", obj)
        return

    symbol = urban.sculpture_text(obj.extra['element:symbol'], 1, 3)

    #lamppost = urban.lamppost()
    #tree =

    item = obj.copy3()
    item.append(symbol)
    #item = item.translate((obj.geom.coords[0][0], obj.geom.coords[0][1], 0))

    root.find("/Elements3").append(item)

@dddtask(path="/Elements3/*", filter=lambda o: o.extra.get('element:type', None) == 'Metal')
def each(root, obj):
    obj = obj.material(ddd.mats.steel)
    return obj

@dddtask(path="/Elements3/*", filter=lambda o: o.extra.get('element:type', None) == 'Noble Gas')
def each(root, obj):
    obj = obj.material(ddd.mats.metal_paint_green)
    return obj

@dddtask(path="/Elements3/*", filter=lambda o: o.extra.get('element:type', None) == 'Halogen')
def each(root, obj):
    obj = obj.material(ddd.mats.water)
    return obj

@dddtask(path="/Elements3/*", log=True)
def create_base(root, obj):
    year = int(obj.extra['element:year']) if obj.extra['element:year'] else -10000
    age = 2020 - year
    height = (math.log(age, 2) - 1) * 0.4 + 0.02
    base = ddd.disc(r=1.5, name="Base").material(ddd.mats.stone)
    base = base.extrude(height)

    obj = obj.translate([0, 0, height])
    obj.append(base)

    return obj

@dddtask(path="/Elements3/*")
def position(root, obj):
    element_size = (5, 10)
    pos_x = int(obj.extra['element:group']) * element_size[0]
    pos_y = int(obj.extra['element:period']) * element_size[1]
    obj = obj.translate((pos_x, -pos_y, 0))
    return obj



@dddtask(parent="generate_scenario")
def show(root):
    """
    """
    root.find("/Elements3").save("/tmp/periodictable.glb")
    root.find("/Elements3").show()


