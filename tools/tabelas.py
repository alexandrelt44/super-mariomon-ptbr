"""Extracts the fixed-size name tables (items, moves, abilities, types).

These names live in fixed-length fields with no pointer to them, so they
never show up in the pointer-based catalogue and a translation must fit the
field ("max_bytes", terminator included). Species names are left out on
purpose: CAPTURE names stay as in the original.

usage: python3 tools/tabelas.py ROM.gba build/tabelas.json
"""

import json
import sys

from gen3text import decode

# name: (first entry, stride, field size, count) for Super Mariomon
# v1.5.1-Anniversary. Items are 40-byte structs with the name first.
TABLES = {
    "itens": (0x80C8DC, 40, 20, 722),
    "golpes": (0x426E24, 17, 17, 840),  # Z-moves after this are pointer strings
    "habilidades": (0x42CB86, 17, 17, 299),
    "tipos": (0x42ADD4, 7, 7, 19),
}


# Species names (11-byte fields) are not translated, but false pointers into
# that table must not be either.
UNTRANSLATED = [(0x420000, 0x426E24)]


def table_ranges():
    return [(start, start + stride * count)
            for start, stride, _, count in TABLES.values()] + UNTRANSLATED


def extract(rom):
    entries = []
    for name, (start, stride, size, count) in TABLES.items():
        for i in range(count):
            off = start + i * stride
            res = decode(rom, off)
            if res is None or res[1] - off > size:
                raise ValueError("%s[%d] em %07X não é um nome" % (name, i, off))
            entries.append({"tabela": name, "index": i, "offset": "%07X" % off,
                            "en": res[0], "max_bytes": size})
    return entries


if __name__ == "__main__":
    rom = open(sys.argv[1], "rb").read()
    entries = extract(rom)
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=1)
    for name in TABLES:
        print(name, sum(e["tabela"] == name for e in entries))
