"""Creates a translation file for one or more maps.

Lists every text of the given maps (from build/mapas.json) that no file in
traducao/ covers yet, with an empty "pt" to fill in. Short all-caps labels
get a "max_width" close to the original, since menus have fixed widths.

usage: python3 tools/novo_lote.py ROM.gba build/textos.json build/mapas.json \
           traducao/mapas/01_casa_mario.json 1.0 1.1 1.2
"""

import glob
import json
import os
import re
import sys

from build import line_width

ROOT = os.path.join(os.path.dirname(__file__), "..")
MENU_SLACK = 6


def menu_like(en):
    """Short all-caps labels with no line breaks are usually menu entries."""
    plain = re.sub(r"\{[^}]*\}", "", en)
    return len(plain) <= 16 and "\\" not in en and plain == plain.upper()


def translated_offsets():
    done = set()
    for path in glob.glob(os.path.join(ROOT, "traducao", "**", "*.json"), recursive=True):
        with open(path, encoding="utf-8") as f:
            done.update(e["offset"] for e in json.load(f))
    return done


if __name__ == "__main__":
    rom = open(sys.argv[1], "rb").read()
    catalogue = {e["offset"]: e for e in json.load(open(sys.argv[2], encoding="utf-8"))}
    maps = json.load(open(sys.argv[3], encoding="utf-8"))["maps"]
    out_path = sys.argv[4]
    wanted = [tuple(int(x) for x in arg.split(".")) for arg in sys.argv[5:]]
    done = translated_offsets()
    entries = []
    for g, n in wanted:
        m = next(m for m in maps if (m["group"], m["num"]) == (g, n))
        for off in m["texts"]:
            if off in done:
                continue
            done.add(off)
            en = catalogue[off]["en"]
            e = {"map": "%d.%d %s" % (g, n, m["name"]), "offset": off, "en": en, "pt": ""}
            if menu_like(en):
                e["max_width"] = line_width(rom, en) + MENU_SLACK
            entries.append(e)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=1)
    print("%s: %d textos, %d caracteres"
          % (out_path, len(entries), sum(len(e["en"]) for e in entries)))
