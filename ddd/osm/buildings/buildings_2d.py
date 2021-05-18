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
import math
import random
import sys
import numpy as np

from ddd.ddd import DDDObject2, DDDObject3
from ddd.ddd import ddd
from ddd.pack.sketchy import plants, urban
from ddd.geo import terrain
from ddd.core.exception import DDDException
from ddd.util.dddrandom import weighted_choice
from ddd.pack.sketchy.buildings import window_with_border, door


# Get instance of logger for this module
logger = logging.getLogger(__name__)



class Buildings2DOSMBuilder():

    def __init__(self, osmbuilder):

        self.osm = osmbuilder

    def preprocess_buildings_features(self, features_2d):

        logger.info("Preprocessing buildings and bulding parts 2D")
        # TODO: create nested buildings them separately, consider them part of the bigger building for subtraction)

        # Assign each building part to a building, or transform it into a building if needed
        #features = sorted(features_2d.children, key=lambda f: f.geom.area)
        features_2d_original = list(features_2d.children)
        for feature in list(features_2d.children):
            if feature.geom.type == 'Point': continue

            if feature.extra.get('osm:building:part', None) is None and feature.extra.get('osm:building', None) is None: continue

            # Find building
            #buildings = features_2d.select(func=lambda o: o.extra.get('osm:building', None) and ddd.polygon(o.geom.exterior.coords).contains(feature))
            buildings = features_2d.select(func=lambda o: o.extra.get('osm:building', None) and o != feature and o.contains(feature) and o in features_2d_original)

            if len(buildings.children) == 0:
                if feature.extra.get('osm:building', None) is None:
                    logger.warn("Building part with no building: %s", feature)
                    building = ddd.shape(feature.geom, name="Building (added): %s" % feature.name)
                    building.extra['osm:building'] = feature.extra.get('osm:building:part', 'yes')
                    building.extra['ddd:building:parts'] = [feature]
                    feature.extra['ddd:building:parent'] = building
                    features_2d.append(building)

            elif len(buildings.children) > 1:
                # Sort by area and get the smaller one
                buildings.children.sort(key=lambda b: b.geom.area, reverse=False)
                logger.warn("Building part with multiple buildings: %s -> %s", feature, buildings.children)

                feature.extra['ddd:building:parent'] = buildings.children[0]
                if 'ddd:building:parts' not in buildings.children[0].extra:
                    buildings.children[0].extra['ddd:building:parts'] = []
                buildings.children[0].extra['ddd:building:parts'].append(feature)

            else:
                logger.debug("Associating building part to building: %s -> %s", feature, buildings.children[0])
                feature.extra['ddd:building:parent'] = buildings.children[0]
                if 'ddd:building:parts' not in buildings.children[0].extra:
                    buildings.children[0].extra['ddd:building:parts'] = []
                buildings.children[0].extra['ddd:building:parts'].append(feature)


    def process_buildings_analyze(self, buildings):
        """
        This is part of the "structured" stage. Buildings have already been selected.
        This phase processes building (parts) and generates floors, segments,
        facades, building contact information, etc...
        """
        for building in buildings.children:
            self.process_building_analyze_building(self, building)


    def process_building_analyze_building(self, building):
        """
        Note that elevation is not yet available at this point.
        """

        # Find contacted building parts

        # Mark each segment with:
        # Segment length, corresponding convex_hull_segment, building + segment contacts (no floor, elevation is not yet) + vertex contacts?, floors spanned...
        # Forward_object ref + distance
        # Segment type (?): interior, detail, facade....

        # Generate convex hull segment,
        # Type of convex hull segment: facade_main, facade_secondary, interior
        # Convex hull forward object: distance + link + type  # not soo significative if taken from center

        # Per floor (ddd:building:floor:N) -> Floor profile (facade elements, windows yes/no, etc) (initialize to defaults, use styling)

        # Floor profiles
        pass



    def process_buildings_link_items_to_buildings(self, buildings_2d, items_1d):

        logger.info("Linking items to buildings.")
        # TODO: Link to building parts, inspect facade, etc.

        for feature in items_1d.children:
            # Find closest building
            #point = feature.copy(name="Point: %s" % (feature.extra.get('name', None)))
            point = feature
            building, distance = self.closest_building(buildings_2d, point)
            if not building:
                continue

            if distance > 10:
                continue

            feature.extra['osm:building'] = building

            if feature.extra.get('osm:amenity', None) or feature.extra.get('osm:shop', None):
                # TODO: Do the opposite, create items we are interested in, avoid this exception
                if point.extra.get('osm:amenity', None) in ('waste_disposal', 'waste_basket', 'recycling', 'bicycle_parking', 'parking_space'):
                    continue

                logger.debug("Associating item %s to building %s.", feature, building)
                #logger.debug("Point: %s  Building: %s  Distance: %s", point, building, distance)
                building.extra['ddd:building:items'].append(feature)

    def process_buildings_link_items_ways_to_buildings(self, buildings_all, items):
        for item in items.children:

            '''
            for building in buildings.children:
                if building.contains(item):
                    logger.info("Associating item %s to building %s.", item, building)
                    item.extra['ddd:building:parent'] = building
                    #building.extra['ddd:building:items_ways'].append(item)
            '''

            buildings = buildings_all.select(func=lambda o: o.extra.get('osm:building', None) and not o.extra.get('ddd:building:parent', None) and o.contains(item))

            if len(buildings.children) > 1:
                logger.warn("Item with multiple buildings: %s -> %s", item, buildings.children)
                # Sort by area
                buildings.children.sort(key=lambda b: b.geom.area, reverse=True)

            if len(buildings.children) > 0:
                building = buildings.children[0]
                logger.info("Associating item (way) %s to building %s.", item, building)
                item.extra['ddd:building:parent'] = building
                #building.extra['ddd:building:items_ways'].append(item)

    def closest_building(self, buildings_2d, point):
        closest_building = None
        closest_distance = math.inf
        for building in buildings_2d.children:
            distance = point.distance(building)
            if distance < closest_distance:
                closest_building = building
                closest_distance = distance
        return closest_building, closest_distance


