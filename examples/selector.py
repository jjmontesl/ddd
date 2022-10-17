# Jose Juan Montes 2020

"""
An example of a configurable processing pipeline in DDD.

This gets an list of atomic elements and displays them
after several processing and styling steps.
"""

import logging

from ddd.pipeline.decorators import dddtask
from ddd.pipeline.pipeline import DDDPipeline


# Get instance of logger for this module
logger = logging.getLogger(__name__)

@dddtask(order="999.1")
def test_selectors_all(root):
    #root.dump()
    pass

@dddtask(select='["element:type" = "Metal"]')
def test_selectors_attr_equals():
    pass

@dddtask(select='["element:type" = "metal"]')
def test_selectors_attr_equals_case():
    pass

@dddtask(select='["element:type" ~ "Metal"]')
def test_selectors_attr_regexp_exact():
    pass

@dddtask(select='["element:type" ~ "Met"]')
def test_selectors_attr_regexp_partial():
    pass

@dddtask(select='["element:type" ~ "metal"]')
def test_selectors_attr_regexp_case():
    pass

@dddtask(select='["element:type" ~ "Metal|Whatever"]')
def test_selectors_attr_regexp_or():
    pass

@dddtask(select='["element:type" ~ "Metal|Noble Gas"]')
def test_selectors_attr_regexp_or2():
    pass

@dddtask(path="/", select='[!"element:type"]')
def test_selectors_attr_undef_root():
    pass

@dddtask(path="/Elements2/*", select='[!"element:type"]')
def test_selectors_attr_undef_set():
    pass

@dddtask(select='["element:type" = "Metal"]["element:phase" = "solid"]')
def test_selectors_and():
    pass

# Test paths, select *...

# Test additions, insertios, funcs...


# Run pipeline. This will run tasks defined here too
pipeline = DDDPipeline(['periodictable_pipeline_base.py'])
pipeline.tasks = pipeline.tasks[:-9]  # TODO: include only loading part of pipeline correctly
pipeline.run()


