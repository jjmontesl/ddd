import struct
import itertools
import freetype

ENDIAN = '<' # always little endian

# If you make a modified version, please change the URL in the string to
# let people know what generated the file!
# example: Bakefont 3.0.2 (compatible; Acme Inc version 1.3)
ENCODER = "Bakefont 3.0.2 (https://github.com/golightlyb/bakefont3)"


def fp26_6(native_num):
    """
    Encode a number in 26.6 fixed point arithmatic with the lower 6 bytes
    used for the fractional component and the upper 26 bytes used for the
    integer component, returning a native int.

    Freetype uses this encoding to represent floats.
    """
    if isinstance(native_num, int):
        result = native_num * 64
    else:
        result = int(float(native_num) * 64.0)

    return int32(result)


def int8(num):
    assert num < 128
    return struct.pack(ENDIAN+'b', num);

def uint8(num):
    assert num < 256
    return struct.pack(ENDIAN+'B', num);

def int16(num):
    assert num < (128 * 256)
    return struct.pack(ENDIAN+'h', num);

def uint16(num):
    assert num < (256 * 256)
    return struct.pack(ENDIAN+'H', num);

def int32(num):
    return struct.pack(ENDIAN+'i', num);

def uint32(num):
    return struct.pack(ENDIAN+'I', num);

def int64(num):
    return struct.pack(ENDIAN+'q', num);

def uint64(num):
    return struct.pack(ENDIAN+'Q', num);

def cstring(nativeString, encoding="utf-8"):
    """null-terminated C-style string"""
    bytes = nativeString.encode(encoding);
    return bytes + b'\0';

def b8string(nativeString, encoding="utf-8"):
    """uint8 length-prefixed Pascal-style string
    plus a C-style null terminator
    aka a 'bastard string'."""
    bytes = nativeString.encode(encoding);
    length = len(bytes)
    assert length < 256
    return uint8(length) + bytes + b'\0';

def fixedstring(nativeString, bufsize, encoding="utf-8"):
    assert '\0' not in nativeString # can't become a C string
    spare = bufsize - len(nativeString)
    assert spare >= 1
    bytes = nativeString.encode(encoding)
    return bytes + (b'\0' * spare)


def header(result, bytesize):
    width, height, depth = result.size

    # Notation: `offset | size | notes`

    # HEADER - 24 byte block
    yield b"BAKEFONTv3r1"  #  0 | 12 | magic bytes, version 3 revision 1
    yield uint16(width)    # 12 |  2 | texture atlas width
    yield uint16(height)   # 14 |  2 | texture atlas height
    yield uint16(depth)    # 16 |  2 | texture atlas depth (1, 3, 4)
    yield uint16(bytesize) # 18 |  2 | ...
    yield b'\0\0\0\0'      # 20 |  4 | padding (realign to 8 bytes)

    # bytesize is a number of bytes you can read from the start of
    # the file in one go to load all the important indexes. It's going to be
    # only a few hundred bytes.


def fontrelative(face, fsize, value):
    # value is in relative Font Units, so converted into pixels for the
    # given font rasterisation size (given as float)
    return (float(value) * fsize) / float(face.units_per_EM)


def fonts(result):
    # Notation: `offset | size | notes`

    # FONT TABLE HEADER - 6 bytes
    yield b"FONT"                   # 24 | 4 | debugging marker
    yield uint16(len(result.fonts)) # 28 | 2 | number of fonts
    yield b"\0\0"                   # 30 | 2 | padding (realign to 8 bytes)

    # FONT RECORDS - 48 bytes * number of fonts
    # (for n = 0; n => n + 1; each record is at offset 32 + 48n)
    # the FontID is implicit by the order e.g. the first font has FontID 0
    for font in result.fonts:
        name, face = font

        # 32+48n |  4 | attributes
        # 36+48n | 44 | name for font with FontID=n (null terminated string)

        yield b'H' if face.has_horizontal else b'h' # e.g. most Latin languages
        yield b'V' if face.has_vertical   else b'v' # e.g. some East Asian
        yield b'\0' # RESERVED (monospace doesn't detect reliably)
        yield b'\0' # RESERVED (kerning doesn't detect reliably)
        yield fixedstring(name, 44)


def modes(result):
    # Notation: `offset | size | notes`
    # offset is relative to r = 24 + 8 + (48 * number of fonts)

    # FONT MODE TABLE HEADER - 8 bytes
    yield b"MODE"                   # r+0 | 4 | debugging marker
    yield uint16(len(result.modes)) # r+4 | 2 | number of modes
    yield b"\0\0"                   # r+6 | 2 | padding (realign to 8 bytes)

    # FONT MODE RECORDS - 32 bytes each
    # the ModeID is implicit by the order e.g. the first mode has ModeID 0
    for mode in result.modes:
        fontID, size, antialias = mode
        _, face = result.fonts[fontID]

        # offset o = r + 8 + (32 * n)
        # o +0 |  2 | font ID
        # o +2 |  1 | flag: 'A' if the font is antialiased, otherwise 'a'
        # o +3 |  1 | RESERVED
        # o +4 |  4 | font size - fixed point 26.6
        #            (divide the signed int32 by 64 to get original float)
        # o +8 |  4 | lineheight aka linespacing - (fixed point 26.6)
        # o+12 |  4 | underline position relative to baseline (fixed point 26.6)
        # o+16 |  4 | underline vertical thickness, centered on position (fp26.6)
        # o+20 | 12 | RESERVED

        yield uint16(fontID)
        yield b'A' if antialias else 'a'
        yield b"\0"
        yield fp26_6(size)

        # lineheight aka linespacing
        yield fp26_6(fontrelative(face, size, face.height))

        # face.underline_position
        # vertical position, relative to the baseline, of the underline bar's
        # center. Negative if it is below the baseline.
        yield fp26_6(fontrelative(face, size, face.underline_position))

        # face.underline_thickness
        # vertical thickness of the underline (remember its centered)
        yield fp26_6(fontrelative(face, size, face.underline_thickness))

        # placeholder for bbox boundary, horizontal advance, vertical advance
        yield b'\0' * (4 + 4 + 4) # RESERVED


def index(result, startingOffset, cb):
    # offset is relative to r = 24 + 8 + (48 * number of fonts)
    #                              + 8 + (32 * number of modes)

    # GLYPH TABLE HEADER - 8 bytes
    yield b"GTBL"                       # r+0 | 4 | debugging marker
    yield uint16(len(result.modeTable)) # r+4 | 2 | number of (modeID, charsetname) pairs
    yield b"\0\0"                       # r+6 | 2 | padding (realign to 8 bytes)

    offset = startingOffset

    # GLYPHSET structures - variable length, located at a dynamic offset
    glyphsets = []
    for modeID, charsetname, glyphs in result.modeTable:
        glyphsets.append(b''.join(glyphset(result, modeID)))

    # KERNING structures - variable length, located at a dynamic offset
    kernings = []
    for modeID, charsetname, glyphs in result.modeTable:
        kernings.append(b''.join(kerning(result, modeID, charsetname, glyphs, cb)))

    # GLYPH TABLE RECORDS - 40 bytes each
    for index, tple in enumerate(result.modeTable):
        modeID, charsetname, glyphs = tple
        # offset o = r + 8 + (40 * number of (modeID, charsetname) pairs)
        # o +0 |  2 | mode ID
        # o +2 |  2 | RESERVED
        # o +4 |  4 | absolute byte offset of glyph metrics data
        # o +8 |  4 | byte size of glyph metrics data
        #             (subtract 4, divide by 40 to get number of entries)
        # o+12 |  4 | absolute byte offset of glyph kerning data
        # o+16 |  4 | byte size of glyph kerning data
        #             (subtract 4, divide by 16 to get number of entries)
        # o+20 | 20 | charset name (string, null terminated)

        yield uint16(modeID)
        yield b"\0\0"

        # absolute byte offset to glyph metrics structure for this font mode
        yield uint32(offset)
        yield uint32(len(glyphsets[index]))
        offset += len(glyphsets[index])

        # absolute byte offset to kerning structure for this font mode
        yield uint32(offset)
        yield uint32(len(kernings[index]))
        offset += len(kernings[index])

        yield fixedstring(charsetname, 20)

    for i in range(len(glyphsets)):
        yield glyphsets[i]
        yield kernings[i]


def glyphset(result, modeID):
    glyphset = result.modeGlyphs[modeID]
    _, size, _ = result.modes[modeID]

    # GLYPH SET HEADER - 4 bytes
    yield b"GSET"                       # r+0 | 4 | debugging marker

    # record - 40 bytes
    for codepoint, glyph in sorted(glyphset.items()):
        # Unicode code point
        yield uint32(codepoint)  # 4 bytes

        # pixel position in texture atlas
        yield uint16(glyph.x0)  # 2 bytes
        yield uint16(glyph.y0)  # 2 bytes
        yield uint8(glyph.z0)   # 1 byte

        # pixel width in texture atlas
        yield uint8(glyph.width)  # 1 byte
        yield uint8(glyph.height) # 1 byte
        yield uint8(glyph.depth)  # 1 byte (always 0 or 1)
        assert 0 <= glyph.depth <= 1

        yield int16(glyph.bitmap_left); # 2 byte
        yield int16(glyph.bitmap_top);  # 2 byte

        # horizontal left side bearing and top side bearing
        # positioning information relative to baseline
        # NOTE!!! These are already FP26.6!!!
        yield int32(glyph.horiBearingX)  # 4 bytes
        yield int32(glyph.horiBearingY)  # 4 bytes
        # advance - how much to advance the pen by horizontally after drawing
        yield int32(glyph.horiAdvance)  # 4 bytes

        yield int32(glyph.vertBearingX)  # 4 bytes
        yield int32(glyph.vertBearingY)  # 4 bytes
        # advance - how much to advance the pen by vertically after drawing
        yield int32(glyph.vertAdvance)  # 4 bytes


def kerning(result, modeID, setname, glyphset, cb):
    fontID, size, antialias = result.modes[modeID]
    font, face = result.fonts[fontID]

    size_fp = int(size * 64.0)  # convert to fixed point 26.6 format
    dpi = 72  # typographic DPI where 1pt = 1px
    face.set_char_size(size_fp, 0, dpi, 0)

    if not face.has_kerning:
        yield b'KERN'
        raise StopIteration

    # GLYPH SET HEADER - 4 bytes
    yield b"KERN"                       # r+0 | 4 | debugging marker

    cb.stage("Gathering kerning data for font %s %s %s, table %s" \
        % (repr(font), size, 'AA' if antialias else 'noAA', repr(setname)))

    combinations = list(itertools.permutations(glyphset, 2))
    num = 0; count = len(combinations)

    # record - 16 bytes
    for codepointL, codepointR in sorted(combinations):
        num += 1; cb.step(num, count)

        #  0 | 4 | uint32 Unicode Codepoint of left glyph in kerning pair
        #  4 | 4 | uint32 Unicode Codepoint of right glyph in kerning pair
        #  8 | 4 | (floating point 26.6; divide by 64.0) grid-fitted offset x (pixels)
        # 12 | 4 | (floating point 26.6; divide by 64.0) non-grid-fitted offset x (pixels)

        indexL = face.get_char_index(codepointL)
        indexR = face.get_char_index(codepointR)
        kerning = face.get_kerning(indexL, indexR)
        kerning_fine = face.get_kerning(indexL, indexR, freetype.FT_KERNING_UNFITTED)
        if kerning.x or kerning_fine.x:
            yield uint32(indexL)
            yield uint32(indexR)
            yield int32(kerning.x) # NOTE already in FP26.6
            yield int32(kerning_fine.x) # NOTE already in FP26.6

            # TODO could probably use only one of these


def notes(result):
    # GLYPH SET HEADER - 8 bytes
    yield b"INFO"                       # 0 | 4 | debugging marker

    # some info about the fonts, in case the author forgets and wants to go
    # back and generate the same file again.

    def font_notes(font):
        name, face = font
        return "    %s: %s," % (repr(name), repr(face.family_name.decode("ascii", "replace")))

    def mode_notes(mode):
        fontID, size, antialias = mode
        name, face = result.fonts[fontID]
        return "    (%s, %s, %s)," % (repr(name), size, "True" if antialias else "False")

    notes = """

encoder = """ + repr(ENCODER) + """;

fonts = {
"""\
    +'\n'.join(map(font_notes, result.fonts))+\
"""
};

modes = [
"""\
    +'\n'.join(map(mode_notes, result.modes))+\
"""
];

"""

    yield uint32(len(notes))
    yield notes.encode("utf-8")



def all(result, cb):
    preambleBytesize = 24 + \
                       8 + (48 * len(result.fonts)) + \
                       8 + (32 * len(result.modes)) + \
                       8 + (40 * len(result.modeTable))

    _header  = b''.join(header(result, preambleBytesize))
    _fonts   = b''.join(fonts(result))
    _modes   = b''.join(modes(result))
    _index   = b''.join(index(result, preambleBytesize, cb))
    _notes   = b''.join(notes(result))

    yield _header
    yield _fonts
    yield _modes
    yield _index
    yield _notes
