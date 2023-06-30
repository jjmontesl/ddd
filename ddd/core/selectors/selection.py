# DDD(123) - Library for procedural generation of 2D and 3D geometries and scenes
# Copyright (C) 2021 Jose Juan Montes
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import logging
import sys
import time
from typing import Iterable
import numpy as np
from ddd.core.exception import DDDException
from ddd.core.selectors.selector import DDDSelector
from ddd.formats.presentation.generic import Generic3DPresentation
from ddd.math.transform import DDDTransform
from trimesh import transformations
from ddd.ddd import ddd

# Get instance of logger for this module
logger = logging.getLogger(__name__)


#class DDDSelection()
class DDDQuery():  # (DDDNode)
    """
    Represents the result of the evaluation of a selector. 
    
    Holds a list of DDDNodes which may be contained in a hierarchy, and keeps track of additional information of the selection
    context (such as the parenting in the originally queried hierarchy, full path, the selector used, etc.), in order to allow
    for **removal and change operations and selection using expresions using path**.

    It should (TODO) also handle recursiveness and cases where a node and some of its children are selected, and how
    the different operations are applied to the selected nodes and in which order.

    It should also be clear how to handle cases when the list of nodes changes during evaluation. When is the list
    of nodes evaluated? is it a snapshot? is it a live list? is it a copy?...

    TODO: See query/query.py, as it overlaps with the intent of this class.
    TODO: Name choice for this class (DDDGroup could make sense now?). It may need to be used often via constructor (e.g. DDDGroup(node))?
    TODO: Can this handle grouping? (e.g. select="/Root/{group:.*}/Subnode/Item") or via regexp / xml selectors?...?
    TODO: Can selectors handle dictionary access, including referenced nodes?, and select strings or other arbitrary expresions (e.g. select="/Root/Item[attr1=1].name" )
          This would allow to select based on attributes on referenced nodes (also, meanwhile/workaround) ddd could auto-include some references (configurable), such ddd:*:ref or ddd:source or ddd:parent)
          This would be useful to avoid copying metadata around, thus maybe metadata could be changed and the process re-run only from a later stage or only for changed nodes and their dependencies 8-)~ 
    TODO: Can selectors handle parallelism, or information about it for tasks? are they related or does parallelism need to be handled at task level or elsewhere?
    TODO: This class is a draft, currently, DDDNodes are used for results.
    TODO: How to implement, to provide access to dddnode operations? (extend classes/wrap classes/metaprogramming...?)
    """

    def __init__(self):

        #self.name = name
        self.children = children if children is not None else []
        #self.extra = extra if extra is not None else {}

        #self.mat = material
        #self.transform = transform if transform is not None else DDDTransform()

        # TODO: FIXME: Adding A) parenting + full-blown hierarchy  and  B) per-function copy/alter semantics,  consider impact... triple think and...
        #self.parent = None

        self._uid = None

        #self.geom = None
        #self.mesh = None

        '''
        for c in self.children:
            if not isinstance(c, self.__class__) and not (isinstance(c, DDDInstance) and isinstance(self, DDDNode3)):
                #raise DDDException("Invalid children type on %s (not %s): %s" % (self, self.__class__, c), ddd_obj=self)
                pass
        '''

    def __repr__(self):
        #return "DDDObject(name=%r, children=%d)" % (self.name, len(self.children) if self.children else 0)
        return "%s (%s %dc)" % (self.name, self.__class__.__name__, len(self.children) if self.children else 0)

