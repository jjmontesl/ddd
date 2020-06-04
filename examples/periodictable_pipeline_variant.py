# Jose Juan Montes 2020


from ddd.pack.sketchy import urban, landscape, sports
from ddd.ddd import ddd
import math
from csv import DictReader
from ddd.pipeline.pipeline import DDDPipeline
from ddd.pipeline.decorators import dddtask
import logging


# Get instance of logger for this module
logger = logging.getLogger(__name__)

