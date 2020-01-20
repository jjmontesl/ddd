# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020


from shapely import geometry
from trimesh.path import segments
from trimesh.scene.scene import Scene, append_scenes
from trimesh.base import Trimesh
from trimesh.path.path import Path
from trimesh.visual.material import SimpleMaterial
from trimesh import creation, primitives, boolean
import trimesh
from csg.core import CSG
from csg import geom as csggeom
import random
import noise
import pyproj


from svgpathtools import wsvg, Line, QuadraticBezier, Path
from ddd.ddd import ddd, DDDObject2

class DDDText():
    pass

class DDDFont():
    pass

###

def text(text):
    chars = []
    for idx, c in enumerate(text):
        spacing = 2000
        char_2d = char(c)
        char_2d = char_2d.translate([idx * spacing, 0, 0])
        chars.append(char_2d)
    return ddd.group(chars)

def char(ch):

    def tuple_to_imag(t):
        return t[0] + t[1] * 1j

    from freetype import Face
    #face = Face('/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf')
    face = Face('data/fonts/OpenSansEmoji.ttf')
    face.set_char_size(48 * 64)
    face.load_char(ch)

    #kerning = face.get_kerning(ch, 'x')
    #print(kerning)

    outline = face.glyph.outline
    y = [t[1] for t in outline.points]
    # flip the points
    outline_points = [(p[0], max(y) - p[1]) for p in outline.points]

    start, end = 0, 0
    paths = []

    for i in range(len(outline.contours)):
        end = outline.contours[i]
        points = outline_points[start:end + 1]
        points.append(points[0])
        tags = outline.tags[start:end + 1]
        tags.append(tags[0])

        segments = [[points[0], ], ]
        for j in range(1, len(points)):
            segments[-1].append(points[j])
            if tags[j] and j < (len(points) - 1):
                segments.append([points[j], ])

        for segment in segments:
            if len(segment) == 2:
                paths.append(Line(start=tuple_to_imag(segment[0]),
                                  end=tuple_to_imag(segment[1])))
            elif len(segment) == 3:
                paths.append(QuadraticBezier(start=tuple_to_imag(segment[0]),
                                             control=tuple_to_imag(segment[1]),
                                             end=tuple_to_imag(segment[2])))
            elif len(segment) == 4:
                C = ((segment[1][0] + segment[2][0]) / 2.0,
                     (segment[1][1] + segment[2][1]) / 2.0)

                paths.append(QuadraticBezier(start=tuple_to_imag(segment[0]),
                                             control=tuple_to_imag(segment[1]),
                                             end=tuple_to_imag(C)))
                paths.append(QuadraticBezier(start=tuple_to_imag(C),
                                             control=tuple_to_imag(segment[2]),
                                             end=tuple_to_imag(segment[3])))

        start = end + 1

    path = Path(*paths)
    wsvg(path, filename="/tmp/test.svg")
    path_d = path.d()

    # https://gis.stackexchange.com/questions/301605/how-to-create-shape-in-shapely-from-an-svg-path-element
    # This page also has info about SVG reading!

    from svgpath2mpl import parse_path
    #svgpath = 'M10 10 C 20 20, 40 20, 50 10Z'
    mpl_path = parse_path(path_d)
    coords = mpl_path.to_polygons()
    from shapely.geometry import Polygon, LineString
    result = ddd.group([ddd.polygon(c) for c in coords])

    return result

#result = char("🌟")
#result = char("Ñ")
result = text("En_un_lugar-🌟")

print(result)
result.extrude(0.2).show()


