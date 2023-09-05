# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging

from ddd.materials.material import DDDMaterial


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class MaterialsCollection():
    """
    A convenience list of materials that can be used by packs, in order to attempt to
    unify material usage.

    Materials can be added by modules.
    """

    def load_from(self, collection):

        count = 0
        for name, value in collection.__dict__.items():
            if isinstance(value, DDDMaterial):
                count += 1
                self.__dict__[name] = value

        logger.info("Loaded %d materials.", count)

    def find(self, key):
        """
        Returns a material by its attribute name (not its Material name, so 'wood_planks' instead of 'Wood Planks'.
        TODO: Rename method to 'get'
        """
        return getattr(self, key)


class MaterialMapper():

    # TODO: Not un use, made for OSM material searches

    def __init__(self):
        #self.mappings = []
        pass

    def fuzzysearch_list(self, text, color):  # , mappings=None):
        """
        Return an ordered list of materials that match requirements.
        """

        # Refine by tags

        # Refine by color proximity

        # Refine by name / fuzzy

        # Refine by overrided mappings

        raise NotImplementedError()

    def fuzzysearch(self, text, color):
        results = self.fuzzysearch_list(text, color)
        if results:
            return results[0]
        
        return None