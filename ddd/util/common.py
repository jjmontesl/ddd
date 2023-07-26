# ddd - DDD123
# Library for simple scene modelling.
# Jose Juan Montes and Contributors 2019-2021

import logging
import math
import random
import importlib
from ddd.core.exception import DDDException


# Get instance of logger for this module
logger = logging.getLogger(__name__)


from pint import UnitRegistry
ureg = UnitRegistry()


def parse_bool(value):

    if value in (True, "True", "true", "Yes", "yes", "1", 1):
        return True
    if value in (False, "False", "false", "No", "no", "0", 0):
        return False
    raise DDDException("Could not parse boolean value: %r", value)

def parse_xyztile(value):
    x, y, z = value.split(",")
    xyztile = int(x), int(y), int(z)
    return xyztile

def parse_tile(value):
    return parse_xyztile(value)

def parse_meters(expr):
    """
    Parse meters from a string expression that can contain a unit label. Unit conversion is performed automatically to meters if needed.
    """
    quantity = ureg.parse_expression(str(expr))
    if not isinstance(quantity, float) and not isinstance(quantity, int):
        quantity = quantity.to(ureg.meter).magnitude
    return float(quantity)

def parse_symbol(fqn):
    """
    Parses a python symbol (e.g. a function) from a fully qualified name, trying to import modules as needed to find the symbol.
    """

    # Try to import as module
    modulename = ".".join(fqn.split(".")[:-1])
    symbolname = fqn.split(".")[-1]
    if modulename:
        modul = importlib.import_module(modulename)
        if hasattr(modul, symbolname):
            symb = getattr(modul, symbolname)
            #cliobj = clazz()
            #cliobj.parse_args(self._unparsed_args)
            #cliobj.run()
            return symb
    
    raise DDDException("Could not parse symbol: %r" % fqn)