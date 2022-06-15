# ddd - DDD123
# Library for simple scene modelling.
# Jose Juan Montes and Contributors 2019-2021


from ddd.ddd import ddd


def dddlogo(thick = 0.125, margin = 0.4):
    """
    DDD Logo.

    Original parameters are: thick = 0.125, margin = 0.4
    """

    logo = ddd.group3(name="DDD Logo")

    line_out = ddd.line([
        (1.0, 0.0, 0.4),
        (1.0, 0.0, 0.0),
        (0.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
        (0.0, 1.0, 1.0),
        (1.0, 1.0, 1.0),
        (1.0, 0.0, 1.0),
        (1.0, 0.0, 0.6),
        ])

    base = ddd.rect([thick, thick], name="Logo exterior").recenter()

    item = base.extrude_along(line_out)
    item = item.material(ddd.mats.steel)
    #item = item.rotate([0, 0, 0.2])
    item = ddd.uv.map_cubic(item)  # FIXME: One of the corner vertices are not being split (but they are if slightly rotated)
    logo.append(item)

    line_in = ddd.line([
        (1.0 - margin, 1.0 - margin - 0.1, 1),
        (1.0 - margin, 1.0 - margin, 1),
        (0.0, 1.0 - margin, 1),
        (0.0, 0.0, 1),
        (1.0 - margin, 0.0, 1),
        (1.0 - margin, 0.0, margin),
        (0.0, 0.0, margin),
        (0.0, 1.0 - margin, margin),
        (0.0, 1.0 - margin, 1.0 - margin),
        (0.0, 1.0 - margin - 0.1, 1.0 - margin),
        ])

    item = base.extrude_along(line_in)
    item = item.material(ddd.mats.green)
    item = ddd.uv.map_cubic(item)
    logo.append(item)

    return logo

