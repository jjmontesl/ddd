# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020-2023

import logging

from ddd.core.exception import DDDException
from ddd.ddd import ddd
from ddd.util.common import parse_symbol, func_map_args


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class DDDSlots():

    def slot_add(self, obj, slot_key, position, rotation=None):
        """
        """
        #obj_slots = obj.get('ddd:slots', {})
        #obj_slots[slot_key] = slot_transform
        #obj.set('ddd:slots', obj_slots)
        
        # Create slot as node
        slot = ddd.DDDNode3(name=slot_key)
        slot.set('ddd:slot', slot_key)
        slot.set('ddd:slot:parent:ref', obj)

        slot.transform.translate(position)
        if rotation is not None: slot.transform.rotate(rotation)

        obj.append(slot)
        
        # Return slot
        #return slot

    def slot_get(self, obj, slot_key):
        """
        """
        
        # Find slot node
        slot = obj.select(func=lambda o: o.get('ddd:slot', None) == slot_key).one()
        
        # Return slot
        return slot
    
    def slot_connect(self, obj, slot_key, obj2, slot2_key=None):
        """
        """
        
        # Find slot node
        slot = self.slot_get(obj, slot_key)
        
        # Set transform of obj2 to make its origin aligned with the slot2_key slot if defined
        if slot2_key is not None:
            slot2 = self.slot_get(obj2, slot2_key)
            obj2.transform = slot2.transform.inverted().compose(slot.transform)
            
            # Mark slot as used
            slot2.set('ddd:slot:used', True)

        # Connect object to slot
        slot.append(obj2)

        # Mark slot as used
        slot.set('ddd:slot:used', True)

        
        # Return slot
        return slot
