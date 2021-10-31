# ddd - DDD123
# Library for simple scene modelling.
# Jose Juan Montes and Contributors 2019-2021

import json
import logging
import sys

import argparse
import freetype

from ddd.core.command import DDDCommand
from ddd.core.exception import DDDException
from ddd.ddd import ddd
from ddd.text import bakefont3
import os


# Get instance of logger for this module
logger = logging.getLogger(__name__)


class FontAtlasGenerateCommand(DDDCommand):
    """
    Usage:

    ddd font-generate --atlasname opensansemoji64 --outputdir data/fontatlas/
    """

    def parse_args(self, args):

        #program_name = os.path.basename(sys.argv[0])
        parser = argparse.ArgumentParser()  # description='', usage = ''

        parser.add_argument("--atlasname", type=str, default="test", help="name of the atlas font pack")
        parser.add_argument("--outputdir", type=str, default="", help="output dir")
        #parser.add_argument("--tile", type=float, help="tile size in meters (0 for entire area)")

        args = parser.parse_args(args)

        self.atlasname = args.atlasname
        self.outputdir = args.outputdir

    def run(self):

        logger.info("DDD123 Generate a Raster Font Atlas.")

        self.font_generate()

    def font_generate(self):
        """
        """

        #codepage = 'latin1'
        #font = ''
        #font_size = ''

        dddfonts = [
            {'name': 'OpenSansEmoji', 'mode': 'default', 'size': 64, 'path': ddd.DATA_DIR + '/fonts/OpenSansEmoji.ttf'},
            {'name': 'Oliciy', 'mode': 'default', 'size': 64, 'path': ddd.DATA_DIR + '/fonts/extra/Oliciy.ttf'},
            #{'name': 'LinBiolinum', 'mode': 'default', 'size': 64, 'path': ddd.DATA_DIR + '/fonts/extra/LinBiolinum_RB.ttf'},
            {'name': 'TechnaSans', 'mode': 'default', 'size': 64, 'path': ddd.DATA_DIR + '/fonts/extra/TechnaSans-Regular.ttf'},
            {'name': 'Adolphus', 'mode': 'default', 'size': 64, 'path': ddd.DATA_DIR + '/fonts/extra/Adolphus.ttf'},
        ]

        def allchars(fontface):
            for charcode, index in fontface.get_chars():
                yield chr(charcode)


        fonts = {}
        tasks = []
        for font in dddfonts:
            logger.info("Loading font: %s", font['path'])
            font['fontface'] = freetype.Face(font['path'])
            font['antialias'] = True
            fontname = font['name'] + "-" + font['mode'] + "-" + str(font['size'])
            font['fontname'] = fontname
            fonts[fontname] = font['fontface']
            fontmode = (fontname, font['size'], font['antialias']) # ("Mono",      64, True)
            glyph_set_index_name = "ALL"
            tasks.append((fontmode, glyph_set_index_name, allchars(font['fontface'])))

        '''
        fontmode_mono14   = ("Mono",      96, True)
        fonts = {
            "Mono":      fontface_mono,
            #"Mono Bold": fontface_mono_bold,
            #"Sans":      fontface_sans,
            #"Sans Bold": fontface_sans_bold,
            #"Serif":     fontface_serif,
            #"Serif Bold":fontface_serif_bold,
        }
        tasks = [
            # quick version for testing
            # (fontmode_sans14,  "ALL", "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"),
            (fontmode_mono14,   "ALL", allchars(fontface_mono)),
            # a small character set we want a separate efficient lookup table for
            #(fontmode_sans14b,  "FPS", "FPS: 0123456789"),
            # and just to test some characters that the font probably won't support
            # Like the Welsh Ll ligatures: U+1EFA and U+1EFB.
            #(fontmode_sans14,   "EXTRA", (0x1EFA, 0x1EFB))
        ]
        # Notice that one fontmode is used twice. This is so that it can be used to
        # generate two lookup tables as an optimisation. The first ("ALL") has any
        # character. The second only contains characters for efficiently showing a FPS
        # display. (This is only worth doing for extremely small sets). No extra video
        # texture memory is used.
        '''


        # suitable sizes for our texture atlas, in order of prefence
        # as any (possibly infinite) sequence of (width, height, depth) tuples
        # width, height - pixels
        # depth - 4 to use Red, Green, Blue, Alpha channels individually
        #       - 3 to just use Red, Green, Blue, with full alpha
        #       - 1 to make a single channel greyscale image

        # e.g. the finite sequence (64, 64) (128, 128), (256, 256), ... (64k, 64k)
        depth = 1  # 4
        suitable_texture_sizes = [(2**x, 2**x, depth) for x in range(6, 17)]


        # a callback for getting progress
        class progress:
            STEP = 5.0

            def __init__(self):
                self.percent = 0.0
            def stage(self, msg):
                print("%s..." % msg)
                self.percent = 0.0
            def step(self, current, total):
                percent = 100 * current / total
                if (percent - self.percent) > self.STEP:
                    self.percent = percent
                    print("    %d of %d (%d%%)" % (current, total, percent))
            def info(self, msg):
                print("    (%s)" % msg)


        # Use bakefont3 to rasterise the glyphs, tightly pack them, and collect
        # kerning data
        result = bakefont3.pack(fonts, tasks, suitable_texture_sizes, cb=progress())

        if not result.image:
            print("No fit :-(")
            sys.exit(0)

        # result.image => a PIL (Pillow) image with the method:
        #   * result.image.save(filename) - saves to a file
        #   * result.image.split() - splits a RGB or RGBA image into channels

        # result.data  => a bakefont3.saveable object with the methods:
        #   * result.data.bytes - raw bytes of the data file
        #   * result.data.save(filename) - saves to a file

        # Original BF3 atlas index output binary format (currently unused)
        #result.data.save(os.path.join(self.outputdir, "test.bf3"))

        width, height, depth = result.size
        if depth == 4:
            result.image.save(os.path.join(self.outputdir, "%s.rgba.png" % self.atlasname))
            red,green,blue,alpha = result.image.split()
            red.save(os.path.join(self.outputdir, "%s.4r.png" % self.atlasname))
            green.save(os.path.join(self.outputdir, "%s.4g.png" % self.atlasname))
            blue.save(os.path.join(self.outputdir, "%s.4b.png" % self.atlasname))
            alpha.save(os.path.join(self.outputdir, "%s.4a.png" % self.atlasname))
        elif depth == 3:
            result.image.save(os.path.join(self.outputdir, "%s.rgb.png" % self.atlasname))
            red,green,blue = result.image.split()
            red.save(os.path.join(self.outputdir, "%s.3r.png" % self.atlasname))
            green.save(os.path.join(self.outputdir, "%s.3g.png" % self.atlasname))
            blue.save(os.path.join(self.outputdir, "%s.3b.png" % self.atlasname))
        elif depth == 1:
            result.image.save(os.path.join(self.outputdir, "%s.greyscale.png" % self.atlasname))

        # DDD JSON Index Encoding
        atlasdata = {
            'faces': {}
        }

        for modeID, charsetname, glyphs in result.modeTable:
            glyphset = result.modeGlyphs[modeID]
            fontID, size, _ = result.modes[modeID]
            fontname, font = result.fonts[fontID]

            glyphs = {}
            atlasdata['faces'][fontname] = {'glyphs': glyphs}

            for codepoint, glyph in sorted(glyphset.items()):

                assert 0 <= glyph.depth <= 1

                glyphs[glyph.codepoint] = {
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


        # Write JSON atlas index file (for DDD udsage)
        font_json_path = os.path.join(self.outputdir, "%s.dddfont.json" % self.atlasname)
        logger.info("Writing font JSON data to: %s", font_json_path)
        jsondata = json.dumps(atlasdata)
        with open(font_json_path, "w") as f:
            f.write(jsondata)
        #print(jsondata)
