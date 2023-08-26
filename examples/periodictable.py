# Jose Juan Montes 2020-2023


import logging
import math
from csv import DictReader

from ddd.ddd import ddd
from ddd.pack.sketchy import urban
from ddd.pipeline.decorators import dddtask
from ddd.pipeline.pipeline import DDDPipeline
from ddd.text.font import DDDFontAtlas
from ddd.text.text2d import Text2D

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
    with open("../data/various/periodictable.csv") as f:
        csv = DictReader(f)
        for row in csv:
            feature = ddd.point(name="Element: %s" % row['Element'])
            for k in row.keys():
                feature.extra['element:' + k.lower()] = row[k]
            features.append(feature)

    features.name="Elements2"
    root.append(features)
    #root.dump()

@dddtask()
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
    #result = ddd.align.grid(elements)
    #elements.replace(result)

    elements3 = ddd.group3(name="Elements3")
    root.append(elements3)

    #result.buffer(1.0).show()
    #root.dump()

@dddtask()
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

@dddtask(path="/Elements2/*", filter=lambda o: 'element:symbol' in o.extra)  # select="wp:article=*",
def periodictable_pilars2(root, obj):
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

    symbol = urban.sculpture_text(obj.extra['element:symbol'], 1.75, 3)

    #lamppost = urban.lamppost()
    #tree =

    item = obj.copy3()
    item.append(symbol)
    #item = item.translate((obj.geom.coords[0][0], obj.geom.coords[0][1], 0))

    root.find("/Elements3").append(item)

@dddtask(cache=True)
def cache(pipeline, root, logger):
    """
    Caches current state to allow for faster reruns.
    """
    return "/tmp/ddd.cache"

@dddtask(path="/Elements3/*", filter=lambda o: o.extra.get('element:type', None) == 'Metal')
def type_metal(root, obj):
    obj = obj.material(ddd.mats.steel)
    return obj

@dddtask(path="/Elements3/*", filter=lambda o: o.extra.get('element:type', None) == 'Noble Gas')
def type_noble_gas(root, obj):
    obj = obj.material(ddd.mats.metal_paint_green)
    return obj

@dddtask(path="/Elements3/*", filter=lambda o: o.extra.get('element:type', None) == 'Halogen')
def type_halogen(root, obj):
    obj = obj.material(ddd.mats.water)
    return obj

@dddtask(path="/Elements3/*", log=True)
def create_base(root, obj):
    year = int(obj.extra['element:year']) if obj.extra['element:year'] else -10000
    age = 2021 - year
    height = 1 + (math.log(age, 2) - 1) * 0.4 + 0.02
    obj.set('baseheight', height)
    disc = ddd.disc(r=1.5, name="Base").material(ddd.mats.marble_white)
    base = disc.extrude_step(disc, 0.5)
    base = base.extrude_step(disc.buffer(-0.2), 0.0)
    base = base.extrude_step(disc.buffer(-0.2), height - 0.5 - 0.2)
    base = base.extrude_step(disc.buffer(0.2), 0.0)
    base = base.extrude_step(disc.buffer(0.2), 0.2)

    #base = ddd.uv.map_cylindrical(base)
    #base = base.merge_vertices()
    base = base.smooth(angle=math.pi * 0.40)
    base = ddd.uv.map_cylindrical(base, split=False)

    obj = obj.translate([0, 0, height])
    obj.append(base)

    return obj

@dddtask()
def fonts(pipeline, root, logger):
    """
    Test 2D text generation.
    """
    #pipeline.data['font'] = Font()
    pipeline.data['font:atlas:dddfonts_01_64'] = ddd.material(name="DDDFonts-01-64", color='#f88888',
                                                texture_path=ddd.DATA_DIR + "/fontatlas/dddfonts_01_64.greyscale.png",
                                                #texture_normal_path=ddd.DATA_DIR + "/materials/road-marks-es/TexturesCom_Atlas_RoadMarkings2_1K_normal.png",
                                                #atlas_path="/materials/road-marks-es/RoadMarkings2.plist",
                                                alpha_cutoff=0.5, metallic_factor=0.0, roughness_factor=1.0,
                                                extra={'ddd:material:type': 'font', 'ddd:collider': False, 'ddd:shadows': False,
                                                       'uv:scale': 1.00, 'zoffset': -5.0, 'ddd:texture:resize': 4096})

@dddtask(path="/Elements3/*")
def font(root, pipeline, obj):
    atlas = DDDFontAtlas.load_atlas(ddd.DATA_DIR + "/fontatlas/dddfonts_01_64.dddfont.json")
    text2d = Text2D(atlas, "Oliciy-default-64", pipeline.data['font:atlas:dddfonts_01_64'])
    pipeline.data['text2d'] = text2d

'''
@dddtask(path="/Elements3/*")
def texts(root, pipeline, obj):

    text2d = pipeline.data['text2d']

    result = text2d.text(obj.extra['element:element'])
    result = result.material(pipeline.data['font:material'])
    #result = result.material(ddd.MAT_HIGHLIGHT)

    result = result.recenter()
    result = result.scale([0.5, 0.5, 1])
    result = result.translate([0, -1, obj.get('baseheight')])

    obj.append(result)
'''

@dddtask(path="/Elements3/*")
def texts_front(root, pipeline, obj):

    text2d = pipeline.data['text2d']

    result = text2d.text(obj.extra['element:element'])
    result = result.material(text2d.material)
    result = result.scale([0.5, 0.5, 0.5])
    result = result.recenter()
    #result = result.material(ddd.MAT_HIGHLIGHT)

    textdata = f"{obj.extra['element:year']}"
    result2 = text2d.text(textdata)
    if result2 and not result2.is_empty():
        result2 = result2.recenter()
        result2 = result2.scale([0.25, 0.25, 0.25]).translate([0, 1])
        result.append(result2)

    result = result.combine()

    result = result.rotate(ddd.ROT_FLOOR_TO_FRONT)

    def flat_to_curve(x, y, z, idx, o):
        source_span = 2.0 / 2.0  # centered on 0
        p = x / source_span  # normalized -1, 1
        angle = p * (math.pi * 0.3)
        r = 1.3
        return (math.sin(angle) * r, -math.cos(angle) * r, z)

    result = result.vertex_func(flat_to_curve)

    result = result.translate([0, 0, 1.4])

    obj.append(result)


@dddtask(path="/Elements3/*")
def position(root, obj):
    element_size = (5, 10)
    pos_x = int(obj.extra['element:group']) * element_size[0]
    pos_y = int(obj.extra['element:period']) * element_size[1]
    obj = obj.translate((pos_x, -pos_y, 0))
    obj.set("test", "test")
    return obj


@dddtask()
def show(root, logger):
    """
    """
    root.find("/Elements3").save("/tmp/periodictable.glb")
    root.find("/Elements3").show()
    logger.warn("This pipeline uses stage caching! use --cache-clear to force a full rebuild.")


