from ddd.text import bakefont3 as bf3
from ddd.text.bakefont3 import encode
import unicodedata
from PIL import Image
import numpy as np


class Saveable:
    def __init__(self, data):
        self.data = data

    def bytes(self):
        return self.data

    def save(self, filename):
        with open(filename, 'wb') as fp:
            fp.write(self.data)


class _default_cb:
    def __init__(self):
        pass
    def stage(self, msg):
        pass
    def step(self, current, total):
        pass
    def info(self, msg):
        pass


class pack:

    def getFontID(self, name):
        for index, font in enumerate(self.fonts):
            if name == font[0]: return index
        raise ValueError

    def getModeID(self, fontmode):
        name, size, antialias = fontmode
        if isinstance(name, str): name = self.getFontID(name)
        for index, mode in enumerate(self.modes):
            if (name, size, antialias) == mode: return index
        raise ValueError

    def __init__(self, fonts, tasks, sizes, cb=_default_cb()):
        self.data = None
        self.image = None
        self.size = (0, 0, 0)

        """
        :param fonts: a mapping font name => font face
        :param tasks: a list of (mode, charset name, charset) tuples, where
                      mode is a tuple (font name, size, antialias?)
        :param sizes: a (possibly infinite) sequence of sizes to try
        :param cb:    a callback object with methods `stage(self, msg)` and
                      `step(self, current, total)`, `info(self, msg)`.
        """

        # capture args just once if they're generated
        fonts = dict(fonts)
        tasks = list(tasks)

        # ---------------------------------------------------------------------
        cb.stage("Processing Parameters")
        # ---------------------------------------------------------------------

        seen = set()
        for name in fonts:
            assert isinstance(name, str)
            # implements freetype-py interface
            assert hasattr(fonts[name], "family_name")
            assert fonts[name].is_scalable
            if fonts[name] in seen:
                print("warning: two different font names share the same font face object")
            else:
                seen.add(fonts[name])
        del seen

        for fontmode, setname, charset in tasks:
            # don't clobber charset in case its a generator
            assert isinstance(fontmode, tuple)
            assert isinstance(setname, str)

            name, size, antialias = fontmode
            assert isinstance(name, str)
            assert 1 < size < 255
            assert name in fonts, "font mode references a missing font name"


        # convert parameters for use in lookup tables

        # construct a mapping font ID => (font name, font face)
        fontlist = []
        for name in fonts:
            fontlist.append((name, fonts[name]))
        self.fonts = fontlist

        # construct a mapping fontmode ID => (font ID, size, antialias?)
        modelist = []
        for mode, _, _ in tasks:
            name, size, antialias = mode
            fontID = self.getFontID(name)
            mode = (fontID, size, antialias)
            if mode not in modelist:
                modelist.append(mode)
        modelist = sorted(modelist) # by ascending fontID, size
        self.modes = modelist

        # construct a concrete list of tasks
        # (modeID, name, set(characters))
        _tasks = []
        seen = set()
        for mode, name, charset in tasks:
            modeID = self.getModeID(mode)
            pair = (modeID, name)
            task = (modeID, name, set(charset))
            _tasks.append(task)
            if pair in seen:
                raise KeyError("task contains a duplicate (mode, charname) pair (%d, %s)" % (modeID, name))
            else:
                seen.add((modeID, name))
        tasks = _tasks

        # construct a mapping fontmode ID => superset of characters
        # used by *all* tasks sharing that fontmode
        modeChars = {}
        # and a table (fontmode ID, charsetname, charset)
        modeTable = []
        for modeID, name, charset in tasks:
            assert (modeID, name, charset) not in modeTable
            modeTable.append((modeID, name, charset))

            if not modeChars.get(modeID):
                modeChars[modeID] = set()
            modeChars[modeID] = modeChars[modeID].union(charset)

        self.modeTable = modeTable

        # for each modeChars charset, create a mapping codepoint => rendered glyph
        # ---------------------------------------------------------------------
        cb.stage("Rendering Glyphs")
        # ---------------------------------------------------------------------
        count = 0
        numglyphs = 0
        for modeID, charset in modeChars.items():
            numglyphs += len(charset)

        modeGlyphs = dict()
        for modeID, charset in modeChars.items():
            glyphset = dict()

            fontID, size, antialias = self.modes[modeID]
            fontname, face = self.fonts[fontID]

            size_fp = int(size * 64.0) # convert to fixed point 26.6 format
            dpi = 72 # typographic DPI where 1pt = 1px
            face.set_char_size(size_fp, 0, dpi, 0)

            for char in charset:
                cb.step(count, numglyphs); count += 1

                if isinstance(char, str) and len(char) == 1:
                    codepoint = ord(char)
                elif isinstance(char, int) and 0 <= char <= 2**32:
                    codepoint = char
                else:
                    raise TypeError("Invalid codepoint in charset")

                if face.get_char_index(codepoint):
                    render = bf3.Render(face, codepoint, antialias)
                    glyphset[codepoint] = bf3.Glyph(codepoint, render)
                else:
                    print("notice: font %s doesn't include codepoint %#x / %s (%s)" %
                          (repr(fontname), codepoint, repr(chr(codepoint)), unicodedata.name(chr(codepoint), "unknown name")))

            modeGlyphs[modeID] = glyphset

        self.modeGlyphs = modeGlyphs

        # make a list of all glyph objects, for fitting
        allGlyphs = []
        for _, glyphset in modeGlyphs.items():
            for _, glyph in glyphset.items():
                allGlyphs.append(glyph)
        self.allGlyphs = allGlyphs

        # ---------------------------------------------------------------------
        cb.stage("Fitting Glyphs")
        # ---------------------------------------------------------------------

        # sort by height for packing - good heuristic
        allGlyphs.sort(key=lambda glyph: glyph.render.height, reverse=True)

        # estimate area for best-case smallest area with 100% packing efficiency
        minVolume = 0
        for glyph in allGlyphs:
            minVolume += glyph.render.width * glyph.render.height;

        # attempt a fit for each size
        count = 0
        for size in sizes:
            cb.step(0, len(allGlyphs))

            width, height, depth = size
            volume = width * height * depth
            if minVolume > volume:
                cb.info("Early discard for size %s" % repr(size))
                continue # skip this size

            if _fit(size, allGlyphs, cb):
                self.size = size
                break
            else:
                cb.info("No fit for size %s" % repr(size))
                continue

        # ---------------------------------------------------------------------
        cb.stage("Composing Texture Atlas")
        # ---------------------------------------------------------------------

        if self.size[0]:
            self.image = _image(self.size, allGlyphs)

        # ---------------------------------------------------------------------
        cb.stage("Generating binary")
        # ---------------------------------------------------------------------

        if self.size[0]:
            self.data = Saveable(b''.join(bf3.encode.all(self, cb)))

        # ---------------------------------------------------------------------
        cb.stage("Done")
        # ---------------------------------------------------------------------


def _fit(size, glyphs, cb):
    if not glyphs: return True
    width, height, depth = size

    cube = bf3.Cube(0, 0, 0, width, height, depth)
    spaces = bf3.TernaryTree(cube)

    count = 0
    num = len(glyphs)

    for glyph in glyphs:
        cb.step(count, num); count+=1

        if glyph.render.width and glyph.render.height:
            fit = spaces.fit(glyph.render)

            if not fit: return False

            glyph.x0 = fit.x0
            glyph.y0 = fit.y0
            glyph.z0 = fit.z0
            glyph.x1 = fit.x0 + glyph.render.width
            glyph.y1 = fit.y0 + glyph.render.height
            glyph.z1 = fit.z0 + glyph.render.depth

            # because we don't want people to think their image is broken,
            # make sure the alpha channel has the most information
            # by swapping red and alpha
            if depth == 4 and glyph.z0 == 0:
                glyph.z0 = 3
                glyph.z1 = 4
            elif depth == 4 and glyph.z0 == 3:
                glyph.z0 = 0
                glyph.z1 = 1

    return True



def _image(size, glyphs):
    width, height, depth = size

    # create a greyscale image for each channel i.e. z-layer
    if depth == 4:
        mode = 'RGBA'
        channels = [
            Image.new("L", (width, height), 0),
            Image.new("L", (width, height), 0),
            Image.new("L", (width, height), 0),
            Image.new("L", (width, height), 0),
        ]
    elif depth == 3:
        mode = 'RGB'
        channels = [
            Image.new("L", (width, height), 0),
            Image.new("L", (width, height), 0),
            Image.new("L", (width, height), 0),
        ]
    elif depth == 1:
        # greyscale
        channels = [
            Image.new("L", (width, height), 0),
        ]
    else:
        raise ValueError("Invalid depth for image (expected 1, 3, 4) got %d" % depth)

    for g in glyphs:
        if not g.render.image: continue
        channels[g.z0].paste(g.render.image, (g.x0, g.y0, g.x1, g.y1))

    if depth == 1:
        return channels[0]

    # merge into a RGB or RGBA image
    # convert each channel to a numpy array
    img8 = [None] * depth
    for i in range(0, depth):
        data = channels[i].getdata()
        img = np.fromiter(data, np.uint8)
        img = np.reshape(img, (channels[i].height, channels[i].width))
        img8[i] = img

    # merge each channel into a RGBA image
    if depth == 4:
        image = np.stack((img8[0], img8[1], img8[2], img8[3]), axis=-1)
    elif depth == 3:
        image = np.stack((img8[0], img8[1], img8[2]), axis=-1)

    return Image.fromarray(image, mode=mode)
