# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020-2023

import logging

from ddd.core.exception import DDDException
from ddd.ddd import ddd
from ddd.util.common import parse_symbol, func_map_args


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class DDDItemBuilder():
    """
    """

    def build(self, builder_desc, obj=None):
        """
        #obj3 = itembuilder.build(builder_desc, obj)
        """

        # Resolve build function
        build_func_name = builder_desc['item:func']
        build_func = parse_symbol(build_func_name)

        # Resolve arguments
        build_func_kwargs = func_map_args(build_func, maps=(obj.extra, builder_desc))
        result = build_func(**build_func_kwargs)

        # Build and connect slots recursively
        build_slots = builder_desc.get('item:slots', {})
        for slot_key, slot_desc in build_slots.items():

            slot = self._get_slot(result, slot_key)

            # Build slot object
            slot_obj = self.build(slot_desc, obj)
            slot_obj.transform = slot  #.transform
            
            # Connect object to slot
            result.append(slot_obj)

        return result


    def _get_slot(self, obj, slot_key):
        """
        #slot = obj.get_slot(slot_key)
        """

        obj_slots = obj.get('ddd:slots')
        slot = obj_slots[slot_key]

        return slot