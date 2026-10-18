"""Adds ã õ Ã Õ to the ROM's latin fonts.

Each font is 0x200 glyphs of 16x16 pixels at 2bpp (64 bytes, four 8x8 tiles:
top-left, top-right, bottom-left, bottom-right), followed by a 0x200-byte
width table. Pixel values 1 and 2 are ink and shadow; 0 and 3 are background.

The new glyphs are composed from existing ones: the tilde rows come from ñ/Ñ
and the letter body from á/ó/Á/Ó, so they match each font's style.
"""

from gen3text import EXTRA_CHARS, ENCODE

# (glyphs offset, widths offset) for Super Mariomon v1.5.1-Anniversary.
FONTS = [
    (0x8F0260, 0x8F8260),
    (0x8F8460, 0x900460),
    (0x900660, 0x908660),
    (0x908860, 0x910860),
]

GLYPH = 0x40
TILES = [(0, 0), (8, 0), (0, 8), (8, 8)]

# new char -> (char providing the tilde, char providing the body)
RECIPES = {"ã": ("ñ", "á"), "õ": ("ñ", "ó"), "Ã": ("Ñ", "Á"), "Õ": ("Ñ", "Ó")}


def read_glyph(rom, base, code):
    raw = rom[base + code * GLYPH:base + (code + 1) * GLYPH]
    px = [[0] * 16 for _ in range(16)]
    for t, (tx, ty) in enumerate(TILES):
        for r in range(8):
            v = raw[t * 16 + r * 2] | raw[t * 16 + r * 2 + 1] << 8
            for p in range(8):
                px[ty + r][tx + p] = (v >> ((7 - p) * 2)) & 3
    return px


def write_glyph(rom, base, code, px):
    raw = bytearray(GLYPH)
    for t, (tx, ty) in enumerate(TILES):
        for r in range(8):
            v = 0
            for p in range(8):
                v |= px[ty + r][tx + p] << ((7 - p) * 2)
            raw[t * 16 + r * 2] = v & 0xFF
            raw[t * 16 + r * 2 + 1] = v >> 8
    rom[base + code * GLYPH:base + (code + 1) * GLYPH] = raw


def accent_rows(px):
    """Number of top rows holding the diacritic: everything above the first
    blank row that follows ink."""
    seen_ink = False
    for y, row in enumerate(px):
        ink = any(v in (1, 2) for v in row)
        if ink:
            seen_ink = True
        elif seen_ink:
            return y
    raise ValueError("glifo sem diacrítico separado do corpo")


def add_glyphs(rom):
    for glyphs, widths in FONTS:
        for code, ch in EXTRA_CHARS.items():
            tilde_src, body_src = RECIPES[ch]
            tilde = read_glyph(rom, glyphs, ENCODE[tilde_src])
            body = read_glyph(rom, glyphs, ENCODE[body_src])
            n = accent_rows(body)
            if accent_rows(tilde) != n:
                raise ValueError("til e acento com alturas diferentes em %#x" % glyphs)
            write_glyph(rom, glyphs, code, tilde[:n] + body[n:])
            rom[widths + code] = rom[widths + ENCODE[body_src]]
