# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging
import os
import functools
import inspect
from lark.lark import Lark
from ddd.core.selectors.selector_ebnf import selector_ebnf
from lark.visitors import Transformer


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class TreeToSelector(Transformer):
    """
    Helper class for Lark that transforms Selector grammar into
    python types.
    """

    def string(self, s):
        (s,) = s
        return s[1:-1]
    def number(self, n):
        (n,) = n
        return float(n)

    list = list
    pair = tuple
    dict = dict

    null = lambda self, _: None
    true = lambda self, _: True
    false = lambda self, _: False


class DDDSelector(object):

    _selector_parser = None
    _tree_to_selector = None

    @staticmethod
    def init_parser():
        if DDDSelector._selector_parser is None:
            DDDSelector._selector_parser = Lark(selector_ebnf, start="selector", parser='lalr')
            DDDSelector._tree_to_selector = TreeToSelector()

    def __init__(self, selector):

        self.selector = selector

        DDDSelector.init_parser()
        self._tree = self._selector_parser.parse(selector)
        self._tree = self._tree_to_selector.transform(self._tree)

    def __repr__(self):
        return "Selector(%r)" % self.selector

