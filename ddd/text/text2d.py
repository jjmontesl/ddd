# ddd - DDD123
# Library for simple scene modelling.
# Jose Juan Montes and Contributors 2019-2021

from ddd.ddd import ddd
import logging

# Get instance of logger for this module
logger = logging.getLogger(__name__)


class Text2D():
    """
    Draws text using quads for glyphs, coming form a texture atlas.

    For text as geometry (both 2D and 3D) use Text3D.

    TODO: Better naming for 2D (atlased quads) and 3D (geometry).
    """

    def __init__(self, atlas, fontface=None, material=None):
        self.atlas = atlas
        self.fontface = fontface
        self.material = material

    def text(self, text):
        """
        TODO: Unify text layout between Text3D and Text3D.
        """

        chars = []

        texture_size = 4096
        font_size = 64
        #font_size_norm = font_size / texture_size
        origin_x = 0.0

        for idx, c in enumerate(text):
            spacing = 0.5
            if c is None:
                continue
            elif c == " ":
                origin_x += spacing
            else:

                char_2d, glyph = self.char(c)
                if char_2d is None:
                    continue

                """
                    'font': self.font
                    'codepoint': glyph.codepoint,
                    'x0': glyph.x0,
                    'y0': glyph.y0,
                    'z0': glyph.z0,
                    'width': glyph.width,
                    'height': glyph.height,
                    'depth': glyph.depth,
                    'bitmap_left': glyph.bitmap_left,
                    'bitmap_top': glyph.bitmap_top,
                    'horiBearingX': glyph.horiBearingX,
                    'horiBearingY': glyph.horiBearingY,
                    'horiAdvance': glyph.horiAdvance,
                    'vertBearingX': glyph.vertBearingX,
                    'vertBearingY': glyph.vertBearingY,
                    'vertAdvance': glyph.vertAdvance, }
                """

                width = glyph['width']
                height = glyph['height']
                #pitch  = glyph.bitmap.pitch  # stride
                bitmap_left  = glyph['bitmap_left'] / 64 # ?
                bitmap_top   = glyph['bitmap_top'] / 64  # ?
                horiBearingX = glyph['horiBearingX'] / 64
                horiBearingY = glyph['horiBearingY'] / 64
                horiAdvance  = glyph['horiAdvance'] / 64
                #vertBearingX = glyph.metrics.vertBearingX / 64 # vertical writing
                #vertBearingY = glyph.metrics.vertBearingY / 64 # vertical writing
                #vertAdvance  = glyph.metrics.vertAdvance / 64 # vertical writing

                char_2d = char_2d.translate([origin_x + horiBearingX / font_size, -(height - horiBearingY) / font_size, 0])  #
                chars.append(char_2d)

                origin_x += horiAdvance / font_size

        text = ddd.group3(chars, name="Text: %s" % text)
        #text = text.scale([1, 1, 1]).recenter(onplane=True)
        text = text.combine()

        return text


    def char(self, ch):

        #print(ch)
        try:
            glyph = self.atlas.index['faces'][self.fontface]['glyphs'][str(ord(ch))]
        except KeyError as e:
            logger.error("Could not find font character (font=%s, char=%s)", self.fontface, ch)
            return (None, None)
        #print(glyph)

        quad = ddd.rect().triangulate()
        quad = ddd.uv.map_cubic(quad)

        texture_size = 4096
        font_size = 64
        font_size_norm = font_size / texture_size

        x0 = glyph['x0'] / texture_size
        y0 = glyph['y0'] / texture_size
        width = glyph['width'] / texture_size
        height = glyph['height'] / texture_size

        quad.extra['uv'] = [(x * width + x0, 1.0 - y0 - height + (y * height)) for x, y in quad.extra['uv']]
        #quad.extra['uv'] = [[x * 0.1 + 0.5, y * 0.1 + 0.8] for x, y in quad.extra['uv']]
        #print(quad.extra['uv'])

        #kerning = face.get_kerning(ch, 'x')  # or from previous, actually?
        #print(kerning)

        result = quad
        if width > 0 and height > 0:
            result = result.scale([width / font_size_norm, height / font_size_norm, 1])

        return (result, glyph)


