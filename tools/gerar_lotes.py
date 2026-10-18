"""Splits everything still untranslated into batch files.

- traducao/nomes/<tabela>.json: the fixed-size name tables from
  build/tabelas.json, each entry limited by its field ("max_bytes") and by
  the widest original name of the table ("max_width").
- traducao/lotes/NNN_*.json: catalogue strings of about BATCH_CHARS
  characters each. Map texts come first, in map order, so a batch holds
  whole maps; texts no map uses come after, in ROM order. Those are system
  texts (descriptions, battle and menu messages) drawn in fixed boxes, so
  they keep the original number of lines and roughly the original width.

usage: python3 tools/gerar_lotes.py ROM.gba build/textos.json build/mapas.json build/tabelas.json
"""

import json
import os
import re
import sys

from build import BOX_WIDTH, line_width
from novo_lote import MENU_SLACK, menu_like, translated_offsets

ROOT = os.path.join(os.path.dirname(__file__), "..", "traducao")
BATCH_CHARS = 25000
SYSTEM_SLACK = 10
SHORT_LINE_SLACK = 24
# map and common event scripts: their texts are ordinary dialogue boxes
SCRIPT_REGION = (0x200000, 0x390000)


def system_limits(rom, off, en):
    """Layout limits for a text outside map scripts."""
    if SCRIPT_REGION[0] <= off < SCRIPT_REGION[1]:
        return {"max_width": line_width(rom, en) + MENU_SLACK} if menu_like(en) else {}
    if "\\p" in en:
        return {}
    lines = re.split(r"\\[nl]", en)
    widest = max(line_width(rom, l) for l in lines)
    if len(lines) > 1:
        return {"max_lines": len(lines), "max_width": min(BOX_WIDTH, widest + SYSTEM_SLACK)}
    if menu_like(en):
        return {"max_width": widest + MENU_SLACK}
    if widest < 150:
        return {"max_width": min(BOX_WIDTH, widest + SHORT_LINE_SLACK)}
    return {}


def write(path, entries):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=1)


def name_tables(rom, tables, done):
    by_table = {}
    for e in tables:
        by_table.setdefault(e["tabela"], []).append(e)
    for name, entries in by_table.items():
        path = os.path.join(ROOT, "nomes", name + ".json")
        if os.path.exists(path):
            continue
        widest = max(line_width(rom, e["en"]) for e in entries)
        out = [{"offset": e["offset"], "en": e["en"], "pt": "", "max_bytes": e["max_bytes"],
                "max_width": widest} for e in entries if e["offset"] not in done]
        write(path, out)
        print("%s: %d nomes" % (os.path.relpath(path, ROOT), len(out)))


def batches(rom, catalogue, maps, done):
    by_off = {e["offset"]: e for e in catalogue}
    groups, cur, size = [], [], 0

    def flush(kind):
        nonlocal cur, size
        if cur:
            groups.append((kind, cur))
        cur, size = [], 0

    seen = set(done)
    for m in sorted(maps, key=lambda m: (m["group"], m["num"])):
        for off in m["texts"]:
            if off in seen:
                continue
            seen.add(off)
            en = by_off[off]["en"]
            cur.append({"map": "%d.%d %s" % (m["group"], m["num"], m["name"]),
                        "offset": off, "en": en, "pt": ""})
            if menu_like(en):
                cur[-1]["max_width"] = line_width(rom, en) + MENU_SLACK
            size += len(en)
        if size >= BATCH_CHARS:
            flush("mapas")
    flush("mapas")
    for e in sorted(catalogue, key=lambda e: int(e["offset"], 16)):
        if e["offset"] in seen:
            continue
        seen.add(e["offset"])
        entry = {"offset": e["offset"], "en": e["en"], "pt": ""}
        entry.update(system_limits(rom, int(e["offset"], 16), e["en"]))
        cur.append(entry)
        size += len(e["en"])
        if size >= BATCH_CHARS:
            flush("sistema")
    flush("sistema")
    for i, (kind, entries) in enumerate(groups, 1):
        tag = entries[0]["map"].split(" ", 1)[0] if kind == "mapas" else entries[0]["offset"]
        write(os.path.join(ROOT, "lotes", "%03d_%s_%s.json" % (i, kind, tag)), entries)
    print("%d lotes, %d textos, %d caracteres"
          % (len(groups), sum(len(g) for _, g in groups),
             sum(len(e["en"]) for _, g in groups for e in g)))


if __name__ == "__main__":
    rom = open(sys.argv[1], "rb").read()
    catalogue = json.load(open(sys.argv[2], encoding="utf-8"))
    maps = json.load(open(sys.argv[3], encoding="utf-8"))["maps"]
    tables = json.load(open(sys.argv[4], encoding="utf-8"))
    done = translated_offsets()
    name_tables(rom, tables, done)
    batches(rom, catalogue, maps, done)
