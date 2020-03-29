# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020
import logging
import os
import sys
import argparse



# Get instance of logger for this module
logger = logging.getLogger(__name__)


class DDDException(Exception):

    def __init__(self, message, ddd_obj=None, *args, **kwargs):
        super().__init__(message, *args, **kwargs)
        self.ddd_obj = ddd_obj
