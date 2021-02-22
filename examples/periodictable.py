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

# From https://en.wikipedia.org/wiki/List_of_chemical_elements
# Process features
pipeline = DDDPipeline(['periodictable_pipeline_base.py', 'periodictable_pipeline_simple.py'])
pipeline.run()

# Show an alternative styling
#pipeline = DDDPipeline(['periodictable_pipeline_base.py', 'periodictable_pipeline_variant.py'])
#pipeline.run()

# Style via generation of OSM elements and processing through the OSM pipeline
#pipeline = DDDPipeline.load(['periodictable_pipeline_base.py', 'periodictable_pipeline_osm.py', '../osm/osm_sketchy/*.py'])
#pipeline.run()


#pipeline.root.show()


