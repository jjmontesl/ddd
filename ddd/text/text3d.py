# ddd - DDD123
# Library for simple scene modelling.
# Jose Juan Montes and Contributors 2019-2021

import logging
from freetype import Face

from svgpath2mpl import parse_path

from svgpathtools import wsvg, Line, QuadraticBezier, Path

from ddd.ddd import ddd
from svgpathtools.path import CubicBezier


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class Text3D():

    char_size = 48 * 64

    @staticmethod
    def quick_text(value):
        text3 = Text3D()
        return text3.text(value)

    def text(self, text):
        chars = []

        origin_x = 0.0
        origin_y = 0.0
        spacing_y = 1.0

        for idx, c in enumerate(text):
            spacing = 0.85
            if c == " ":
                origin_x += spacing
            elif c == "\n":
                origin_x = 0.0
                origin_y -= spacing_y
            else:

                try:
                    char_2d, face = self.char(c)
                except:
                    logger.error("Failed to generate Text3D char: %r" % (c,))
                    continue

                glyph  = face.glyph
                width  = glyph.bitmap.width / self.char_size
                height = glyph.bitmap.rows / self.char_size
                #pitch  = glyph.bitmap.pitch  # stride
                bitmap_left  = glyph.bitmap_left / self.char_size
                bitmap_top   = glyph.bitmap_top / self.char_size
                horiBearingX = glyph.metrics.horiBearingX / self.char_size
                horiBearingY = glyph.metrics.horiBearingY / self.char_size
                horiAdvance  = glyph.metrics.horiAdvance / self.char_size
                #vertBearingX = glyph.metrics.vertBearingX / self.char_size # vertical writing
                #vertBearingY = glyph.metrics.vertBearingY / self.char_size # vertical writing
                #vertAdvance  = glyph.metrics.vertAdvance / self.char_size # vertical writing

                char_2d = char_2d.translate([origin_x + horiBearingX, origin_y + 1 + horiBearingY, 0])
                chars.append(char_2d)

                origin_x += horiAdvance

        return ddd.group(chars, name="Text: %s" % text)


    def char(self, ch):

        def tuple_to_imag(t):
            return t[0] + t[1] * 1j

        #face = Face('/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf')
        face = Face(ddd.DATA_DIR + '/fonts/OpenSansEmoji.ttf')
        face.set_char_size(self.char_size)
        face.load_char(ch)

        #kerning = face.get_kerning(ch, 'x')  # or from previous, actually?
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
                    paths.append(CubicBezier(start=tuple_to_imag(segment[0]),
                                             control1=tuple_to_imag(segment[1]),
                                             control2=tuple_to_imag(segment[2]),
                                             end=tuple_to_imag(segment[3])))
                    #C = ((segment[1][0] + segment[2][0]) / 2.0,
                    #     (segment[1][1] + segment[2][1]) / 2.0)
                    #paths.append(QuadraticBezier(start=tuple_to_imag(segment[0]),
                    #                             control=tuple_to_imag(segment[1]),
                    #                             end=tuple_to_imag(C)))
                    #paths.append(QuadraticBezier(start=tuple_to_imag(C),
                    #                             control=tuple_to_imag(segment[2]),
                    #                             end=tuple_to_imag(segment[3])))

            start = end + 1

        path = Path(*paths)
        #wsvg(path, filename="/tmp/test.svg")
        path_d = path.d()

        # https://gis.stackexchange.com/questions/301605/how-to-create-shape-in-shapely-from-an-svg-path-element
        # This page also has info about SVG reading!

        #svgpath = 'M10 10 C 20 20, 40 20, 50 10Z'
        mpl_path = parse_path(path_d)

        coords = mpl_path.to_polygons(closed_only=True)

        item = None
        for c in coords:  # coords[1:]:
            if len(c) < 3: continue
            ng = ddd.polygon(c) #.clean(eps=char_size / 100)  #.convex_hull()
            #ng.show()
            if item is None:
                item = ng
            elif item.contains(ng):
                item = item.subtract(ng)
            else:
                item = item.union(ng)
            item = item.clean(eps=self.char_size / 200)  # Note that this is effectively limiting resolution

        #result = ddd.group([ddd.polygon(c) for c in coords], empty=2)
        result = item
        result = result.scale([1.0 / self.char_size, -1.0 / self.char_size])
        result = result.simplify(0.005)  # Note that this is effectively limiting resolution

        return (result, face)


