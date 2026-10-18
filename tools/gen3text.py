"""Gen 3 (Pokémon Emerald, western) text encoding.

Decodes ROM bytes into an editable form and encodes it back. Control codes
are written as {TAGS} so the round trip is lossless:
  \\n  = FE (new line)      \\l = FA (scroll)      \\p = FB (new box)
  {PLAYER}, {STR_VAR_1}…   = FD xx placeholders
  {COLOR 02}, {PAUSE 10}…  = FC xx [args] extended codes
  {FD 0E}, {F9 05}, {XX}   = raw codes with no friendly name
"""

import re

CHARS = {
    0x00: " ",
    0x01: "À", 0x02: "Á", 0x03: "Â", 0x04: "Ç", 0x05: "È", 0x06: "É", 0x07: "Ê",
    0x08: "Ë", 0x09: "Ì", 0x0B: "Î", 0x0C: "Ï", 0x0D: "Ò", 0x0E: "Ó", 0x0F: "Ô",
    0x10: "Œ", 0x11: "Ù", 0x12: "Ú", 0x13: "Û", 0x14: "Ñ", 0x15: "ß", 0x16: "à",
    0x17: "á", 0x19: "ç", 0x1A: "è", 0x1B: "é", 0x1C: "ê", 0x1D: "ë", 0x1E: "ì",
    0x20: "î", 0x21: "ï", 0x22: "ò", 0x23: "ó", 0x24: "ô", 0x25: "œ", 0x26: "ù",
    0x27: "ú", 0x28: "û", 0x29: "ñ", 0x2A: "º", 0x2B: "ª", 0x2D: "&", 0x2E: "+",
    0x35: "=", 0x36: ";",
    0x51: "¿", 0x52: "¡", 0x5A: "Í", 0x5B: "%", 0x5C: "(", 0x5D: ")",
    0x68: "â", 0x6F: "í",
    0x79: "↑", 0x7A: "↓", 0x7B: "←", 0x7C: "→", 0x85: "<", 0x86: ">",
    0xAB: "!", 0xAC: "?", 0xAD: ".", 0xAE: "-", 0xAF: "·",
    0xB0: "…", 0xB1: "“", 0xB2: "”", 0xB3: "‘", 0xB4: "'", 0xB5: "♂", 0xB6: "♀",
    0xB7: "¥", 0xB8: ",", 0xB9: "×", 0xBA: "/",
    0xEF: "▶", 0xF0: ":", 0xF1: "Ä", 0xF2: "Ö", 0xF3: "Ü", 0xF4: "ä", 0xF5: "ö",
    0xF6: "ü",
}
for i, c in enumerate("0123456789"):
    CHARS[0xA1 + i] = c
for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
    CHARS[0xBB + i] = c
for i, c in enumerate("abcdefghijklmnopqrstuvwxyz"):
    CHARS[0xD5 + i] = c

# Characters the vanilla font lacks. The build step draws them into free
# glyph slots (see font.py); the slot numbers are fixed here so the encoding
# is stable.
EXTRA_CHARS = {0x2F: "ã", 0x30: "õ", 0x31: "Ã", 0x32: "Õ"}

SPECIAL = {0x2C: "{ER}", 0x34: "{LV}", 0x53: "{PK}", 0x54: "{MN}", 0x84: "{SUPER_E}",
           0xA0: "{SUPER_RE}"}

NEWLINES = {0xFE: "\\n", 0xFA: "\\l", 0xFB: "\\p"}

PLACEHOLDERS = {0x01: "PLAYER", 0x02: "STR_VAR_1", 0x03: "STR_VAR_2", 0x04: "STR_VAR_3",
                0x05: "KUN", 0x06: "RIVAL", 0x07: "VERSION", 0x08: "AQUA", 0x09: "MAGMA",
                0x0A: "ARCHIE", 0x0B: "MAXIE", 0x0C: "KYOGRE", 0x0D: "GROUDON"}

# FC sub-code -> (name, number of argument bytes)
EXT_CODES = {
    0x00: ("FC_00", 0), 0x01: ("COLOR", 1), 0x02: ("HIGHLIGHT", 1), 0x03: ("SHADOW", 1),
    0x04: ("COLOR_HIGHLIGHT_SHADOW", 3), 0x05: ("PALETTE", 1), 0x06: ("FONT", 1),
    0x07: ("RESET_FONT", 0), 0x08: ("PAUSE", 1), 0x09: ("PAUSE_UNTIL_PRESS", 0),
    0x0A: ("WAIT_SE", 0), 0x0B: ("PLAY_BGM", 2), 0x0C: ("ESCAPE", 1),
    0x0D: ("SHIFT_RIGHT", 1), 0x0E: ("SHIFT_DOWN", 1), 0x0F: ("FILL_WINDOW", 0),
    0x10: ("PLAY_SE", 2), 0x11: ("CLEAR", 1), 0x12: ("SKIP", 1), 0x13: ("CLEAR_TO", 1),
    0x14: ("MIN_LETTER_SPACING", 1), 0x15: ("JPN", 0), 0x16: ("ENG", 0),
    0x17: ("PAUSE_MUSIC", 0), 0x18: ("RESUME_MUSIC", 0),
}

DECODE = {**CHARS, **EXTRA_CHARS}
ENCODE = {c: b for b, c in DECODE.items()}
ENCODE_TAGS = {name.strip("{}"): b for b, name in SPECIAL.items()}
PLACEHOLDER_CODES = {name: b for b, name in PLACEHOLDERS.items()}
EXT_BY_NAME = {name: (b, n) for b, (name, n) in EXT_CODES.items()}


def decode(data, start):
    """Decode the string at data[start]. Returns (text, end) where end is the
    offset just past the FF terminator, or None if the bytes are not text."""
    out = []
    i = start
    n = len(data)
    while i < n:
        b = data[i]
        if b == 0xFF:
            return "".join(out), i + 1
        if b in DECODE:
            out.append(DECODE[b])
            i += 1
        elif b in NEWLINES:
            out.append(NEWLINES[b])
            i += 1
        elif b in SPECIAL:
            out.append(SPECIAL[b])
            i += 1
        elif b == 0xFD and i + 1 < n:
            a = data[i + 1]
            out.append("{%s}" % PLACEHOLDERS[a] if a in PLACEHOLDERS else "{FD %02X}" % a)
            i += 2
        elif b == 0xFC and i + 1 < n and data[i + 1] in EXT_CODES:
            name, nargs = EXT_CODES[data[i + 1]]
            args = data[i + 2:i + 2 + nargs]
            out.append("{%s}" % " ".join([name] + ["%02X" % a for a in args]))
            i += 2 + nargs
        elif b in (0xF7, 0xF8, 0xF9) and i + 1 < n:
            out.append("{%02X %02X}" % (b, data[i + 1]))
            i += 2
        else:
            return None
    return None


TOKEN = re.compile(r"\{([^}]*)\}|\\([nlp])|(.)", re.S)


def encode(text):
    """Encode editable text back to ROM bytes, FF terminator included."""
    out = bytearray()
    for tag, esc, ch in TOKEN.findall(text):
        if esc:
            out.append({"n": 0xFE, "l": 0xFA, "p": 0xFB}[esc])
        elif ch:
            if ch not in ENCODE:
                raise ValueError("caractere sem glifo na fonte: %r em %r" % (ch, text))
            out.append(ENCODE[ch])
        else:
            parts = tag.split()
            name, args = parts[0], [int(a, 16) for a in parts[1:]]
            if name in ENCODE_TAGS and not args:
                out.append(ENCODE_TAGS[name])
            elif name in PLACEHOLDER_CODES and not args:
                out += bytes([0xFD, PLACEHOLDER_CODES[name]])
            elif name in EXT_BY_NAME:
                code, nargs = EXT_BY_NAME[name]
                if len(args) != nargs:
                    raise ValueError("{%s} espera %d argumento(s)" % (name, nargs))
                out += bytes([0xFC, code] + args)
            elif re.fullmatch(r"[0-9A-F]{2}", name):
                out += bytes([int(name, 16)] + args)
            else:
                raise ValueError("tag desconhecida: {%s}" % tag)
    out.append(0xFF)
    return bytes(out)
