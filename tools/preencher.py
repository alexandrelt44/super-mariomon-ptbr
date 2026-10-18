"""Fills the "pt" fields of a translation file from {offset: pt} JSON.

Offsets missing from the translation file are reported, so a typo in an
offset does not silently drop a line.

usage: python3 tools/preencher.py traducao/mapas/01_casa_mario.json pt.json
"""

import json
import sys

path, source = sys.argv[1], sys.argv[2]
with open(path, encoding="utf-8") as f:
    entries = json.load(f)
with open(source, encoding="utf-8") as f:
    pt = json.load(f)

by_offset = {e["offset"]: e for e in entries}
unknown = sorted(set(pt) - set(by_offset))
if unknown:
    sys.exit("offsets que não estão no lote: " + ", ".join(unknown))
for off, text in pt.items():
    by_offset[off]["pt"] = text
with open(path, "w", encoding="utf-8") as f:
    json.dump(entries, f, ensure_ascii=False, indent=1)
missing = [e["offset"] for e in entries if not e["pt"]]
print("%d preenchidos, %d faltando%s" % (len(entries) - len(missing), len(missing),
                                        (": " + ", ".join(missing)) if missing else ""))
