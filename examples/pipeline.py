# Jose Juan Montes 2020


from ddd.pack.sketchy import urban, landscape, sports
from ddd.ddd import ddd
import math
from csv import DictReader

"""
An example of a PSP (Processing and Styling Pipeline) in DDD.

This example avoids using OSM or map related topics to show pipeline
generalization.

This gets an ordered series of articles from wikipedia and displays them
after several processing and styling steps. Since these features do not
have an intrinsic positioning in space, they are distributed according to
an axis (eg. time).
"""

# From https://en.wikipedia.org/wiki/List_of_chemical_elements
# Process features
pipeline = Pipeline.load(['wikipedia_elements.py'])
pipeline.process(features)
# Show an alternative styling
pipeline = Pipeline.load(['wikipedia_elements.py', 'wkipedia_elements_variant.py'])
pipeline.process(features)


pipeline.show()


### WIKIPEDIA-ARTICLES

class WikipediaPipeline(DDDConfigurablePipeline):

    steps = [generate_scenario, generate_articles, distribute articles, create cameras]
    rules = []

    def process(self, features):
        self.applyrules(features)
        pass

#@stage("generate_scenario", depends=None)
#@stage("generate_articles", depends="generate_scenario")

@dddrule(selector=None, stage="start")
def start_run(s):
    """
    Run at initial stage, load data.
    """
    # Get features (depends on the process)
    features = ddd.group2()
    csv = DictReader("data/wikipedia-elements.csv")
    for row in csv:
        feature = ddd.point(name="Element: %s" % row['symbol'])
        feature.extra['element:' + k] = v
        feature.extra['element:number'] =
        feature.extra['csv:number'] =
        feature.extra['csv:year'] =
        feature.extra['csv:name'] =
        feature.extra['csv:symbol'] =
        features.append(feature)

    features.name="elements"
    s.append(features)

@dddrule(select=None, stage="generate_scenario")
def generate_scenario_run(root):
    """
    Create a circular platform for articles.
    Hill size according to importance
    """
    num_articles = root.select(path='/elements/*').count()
    distance = (num_articles * 10) / (2 * math.pi)
    root = ddd.align.polar(root, d=distance)

@dddrule(select=None, stage="generate_scenario")
def generate_scenario_run_plus(root):
    """
    Create a periodic table platform for articles.
    Block height size according to importance.
    """
    num_articles = s.select(path='/elements/*').count()
    # Create grid

@dddtask(name="", parent=?, after="", before="", select=None, path=None)
def decorate_something(root, o):
    pass

@dddrule(path="/articles/*", select="wp:article=*", stage="generate_articles")
def each(s, o):
    """
    Create a pilar for each element.

    - Position according to periodic table.
    - Letter size according to importance
    - Order according to discovery/synthesis

    - Atom on column (same height, must be easy to see)
    - Nucleus and electrons in orbitals / layers (maybe both models, one 2D smaller) - Rotating
    """
    pilar = urban.sculpture_text(o.extra['csv:symbol'], d, height)

    lamppost = urban.lamppost()
    #tree =

    pass


