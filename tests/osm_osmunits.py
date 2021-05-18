from ddd.osm.osmunits import parse_meters


def test_parse_meters():

    assert parse_meters("1") == 1
    assert parse_meters("1m") == 1
    assert parse_meters("1 m") == 1
    assert parse_meters("1.5 m") == 1.5
    assert parse_meters("-1.5 m") == -1.5
    assert parse_meters("-1.5 meter") == -1.5
    assert parse_meters("-1.5 meters") == -1.5

    assert parse_meters("1 km") == 1000
    assert parse_meters("1km.") == 1000

    assert parse_meters("-1.5 inches") == -0.038099999999999995
    assert parse_meters("-1.5 inch") == -0.038099999999999995




test_parse_meters()
