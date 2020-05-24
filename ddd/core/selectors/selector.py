# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging
import os
import functools
import inspect
from lark.lark import Lark
from ddd.core.selectors.selector_ebnf import selector_ebnf


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class DDDSelector(object):

    _selector_parser = None

    @staticmethod
    def get_parser():
        if DDDSelector._selector_parser is None:
            DDDSelector._selector_parser = Lark(selector_ebnf, start="selector", parser='lalr')
        return DDDSelector._selector_parser

    def __init__(self, selector):

        self.selector = selector

        parser = DDDSelector.get_parser()
        self._tree = parser.parse(selector)

    def __repr__(self):
        return "Selector(%r)" % self.selector

