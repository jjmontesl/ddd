from unittest import TestCase

from ddd.util.common import parse_meters

class UnitsTestCase(TestCase):

    def test_parse_meters(self):
        """
        Parse different length expressions.

        Some of these are extracted from OSM data, in order to try and support the different formattings OSM uses.
        """

        assert parse_meters("1") == 1
        assert parse_meters("1m") == 1
        assert parse_meters("1 m") == 1
        assert parse_meters("1.5 m") == 1.5
        assert parse_meters("-1.5 m") == -1.5
        assert parse_meters("-1.5 meter") == -1.5
        assert parse_meters("-1.5 meters") == -1.5

        assert parse_meters("1 km") == 1000
        assert parse_meters("1km.") == 1000

        #assert parse_meters("1 Km") == 1000  # Currently fails (support/enforce capitalization or replace Km with km in parse_meters?)
        #assert parse_meters("1 KM") == 1000  # Currently fails (support/enforce capitalization or replace Km with km in parse_meters?)

    def test_parse_meters_inches(self):

        assert parse_meters("-1.5 inches") == -0.038099999999999995
        assert parse_meters("-1.5 inch") == -0.038099999999999995

