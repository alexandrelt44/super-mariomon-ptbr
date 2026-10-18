"""Extracts every pointed-to string from the ROM into a JSON catalogue.

A string is listed when some pointer in the ROM refers to it. Pointers are
accepted when they are 4-byte aligned (tables, code literal pools) or follow
a script opcode that takes a text pointer (loadword 0 = 0F 00, message = 67),
which keeps random byte patterns out of the repoint list.

usage: python3 tools/extract.py ROM.gba build/textos.json
"""

import json
import re
import sys

from gen3text import decode

ROM_BASE = 0x08000000
SCRIPT_PREFIXES = (b"\x0f\x00", b"\x67")
POINTER = re.compile(rb"(?=([\x00-\xff]{3}[\x08\x09]))", re.S)


def plausible(text):
    plain = re.sub(r"\{[^}]*\}|\\[nlp]", " ", text)
    letters = sum(c.isascii() and c.isalpha() for c in plain)
    visible = sum(not c.isspace() for c in plain)
    return (letters >= 2 and letters / max(visible, 1) >= 0.6
            and letters / max(len(plain), 1) >= 0.3)


PLAIN = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 ,.'!?-…é")


def is_padding(rom, at):
    """True if rom[at] ends a string or pads after one. 0x00 is also the
    space character, so a lone 0x00 between letters is text, not padding."""
    b = rom[at]
    return b == 0xFF or (b == 0x00 and rom[at - 1] in (0x00, 0xFF))


def fragment_of(rom, off):
    """If off points into the middle of a longer string (a false pointer),
    returns where that string starts; otherwise None. The text before off
    must end in plain characters, so script or graphics bytes that happen
    to decode as letters are not mistaken for text."""
    if is_padding(rom, off - 1):
        return None
    res = decode(rom, off)
    if res is None:
        return None
    start = off - 1
    while start > 1 and not is_padding(rom, start - 1) and off - start < 1000:
        start -= 1
    for st in range(start, off):
        d = decode(rom, st)
        if d is not None and d[1] == res[1]:
            prefix = d[0][:len(d[0]) - len(res[0])]
            run = ""
            for c in reversed(prefix):
                if c not in PLAIN:
                    break
                run = c + run
            letters = {c for c in run if c.isalpha()}
            # a whole-text prefix needs one letter; a run after junk bytes
            # needs two distinct letters, so "aaaa" padding is not text
            if letters and (run == prefix or (len(run) >= 2 and len(letters) >= 2)):
                return st
            return None
    return None


def find_pointers(rom):
    refs = {}
    for m in POINTER.finditer(rom):
        at = m.start()
        target = int.from_bytes(m.group(1), "little") - ROM_BASE
        if not 0 <= target < len(rom):
            continue
        if at % 4 and not any(rom[at - len(p):at] == p for p in SCRIPT_PREFIXES):
            continue
        refs.setdefault(target, []).append(at)
    return refs


def extract(rom):
    entries = []
    for target, sites in sorted(find_pointers(rom).items()):
        res = decode(rom, target)
        if res is None:
            continue
        text, end = res
        if not plausible(text) or fragment_of(rom, target) is not None:
            continue
        entries.append({"offset": "%07X" % target, "size": end - target,
                        "pointers": ["%07X" % s for s in sites], "en": text})
    return entries


if __name__ == "__main__":
    rom = open(sys.argv[1], "rb").read()
    entries = extract(rom)
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=1)
    print("%d strings, %d chars" % (len(entries), sum(len(e["en"]) for e in entries)))
