# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging
import re

from lark.lark import Lark
from lark.visitors import Transformer

from ddd.core.exception import DDDException
from ddd.core.selectors.selector_ebnf import selector_ebnf


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class TreeToSelector(Transformer):
    """
    Helper class for Lark that transforms DDD Selector grammar into python types and selector evaluation functions.
    """

    def TAG_KEY_STRING(self, s):
        return str(s)

    def string(self, s):
        (s,) = s
        return s[1:-1]

    def number(self, n):
        (n,) = n
        return float(n)

    def tagkeystring(self, s):
        (s,) = s
        return s

    list = list
    pair = tuple
    dict = dict

    null = lambda self, _: None
    true = lambda self, _: True
    false = lambda self, _: False

    '''
    def selector(self, t):
        def selector_func(obj):
            print(t[0])
            selected = t[0](obj)
            return selected
        return selector_func
    '''

    def datafilterand(self, t):
        def datafilterand_func(obj):
            for df in t:
                selected = df(obj)
                if not selected: return False
            return True
        return datafilterand_func

    def datafilterkeyexprname(self, t):
        return t[0]

    def datafilterkeyexprvalue(self, t):
        return t[0]

    def datafiltervalueexpr(self, t):
        return t[0]

    def datafilter_attr_eq(self, t):
        datakey = t[0]
        datavalue = t[1]
        def datafilter_attr_eq_func(obj):
            metadata = obj.metadata("", "")  #TODO: Pass path {'geom:type': obj.geom.type if obj.geom else None}
            return (datakey in metadata and metadata[datakey] == datavalue)
        return datafilter_attr_eq_func

    def datafilter_attr_neq(self, t):
        datakey = t[0]
        datavalue = t[1]
        def datafilter_attr_neq_func(obj):
            metadata = obj.metadata("", "")  #TODO: Pass path {'geom:type': obj.geom.type if obj.geom else None}
            return (datakey in metadata and metadata[datakey] != datavalue)
        return datafilter_attr_neq_func

    def datafilter_attr_def(self, t):
        datakey = t[0]
        def datafilter_attr_def_func(obj):
            metadata = obj.metadata("", "")  #TODO: Pass path {'geom:type': obj.geom.type if obj.geom else None}
            return (datakey in metadata)
        return datafilter_attr_def_func

    def datafilter_attr_undef(self, t):
        datakey = t[0]
        def datafilter_attr_undef_func(obj):
            metadata = obj.metadata("", "")  #TODO: Pass path {'geom:type': obj.geom.type if obj.geom else None}
            return (datakey not in metadata)
        return datafilter_attr_undef_func

    def datafilter_attr_def_re(self, t):
        datakey = t[0]
        regexp = re.compile(datakey)
        def datafilter_attr_def_re_func(obj):
            metadata = obj.metadata("", "")  #TODO: Pass path {'geom:type': obj.geom.type if obj.geom else None}
            for datakey in metadata:
                matches = bool(regexp.match(datakey))
                if matches: return True
            return False
        return datafilter_attr_def_re_func

    def datafilter_attr_regexp(self, t):
        datakey = t[0]
        datavalue = t[1]
        regexp = re.compile(datavalue)
        def datafilter_attr_regexp_func(obj):
            metadata = obj.metadata("", "")  #TODO: Pass path {'geom:type': obj.geom.type if obj.geom else None}
            if datakey in metadata:
                return regexp.match(metadata[datakey])
            return False
        return datafilter_attr_regexp_func

    def datafilter(self, t):
        def datafilter_func(obj):
            #logger.info("Datafilter: %s", t)
            return t[0](obj)
        return datafilter_func

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

    def evaluate(self, obj):

        tree = self._tree
        #print(tree)
        #print(tree.pretty())

        logger.debug("Evaluate: %s", tree)
        selected = tree.children[0](obj)

        '''
        selected = False
        for datafilter in tree.children:

            print(datafilter)

            dfselected = False

            datakey = datafilter.children[0].children[0].children[0]
            #print(datakey)
            dataop = datafilter.children[1].data
            #print(dataop)
            datavalue = datafilter.children[2].children[0]
            #print(datavalue)
            #logger.info("Eval select: %s %s %s", datakey, dataop, datavalue)

            extrameta = {'geom:type': obj.geom.type if obj.geom else None}

            for k, v in (list(obj.extra.items()) + list(extrameta.items())):
                if datakey != k: continue
                if dataop == 'equals':
                    dfselected = (v == datavalue)
                else:
                    raise DDDException("Unknown selector operation: %s", dataop)

            if not dfselected: return False

            selected = dfselected
        '''

        return selected

