"""Finds identical English texts that were translated differently.

The game often repeats a line in several maps; each copy should read the
same. With --fix, every copy takes the translation from the first file (in
name order) that has one. Copies are only compared when they share the same
layout limits, so a menu label keeps its own abbreviated form.

usage: python3 tools/consistencia.py [--fix]
"""

import collections
import glob
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(__file__), "..", "traducao")


def load():
    files = {}
    for path in sorted(glob.glob(os.path.join(ROOT, "**", "*.json"), recursive=True)):
        with open(path, encoding="utf-8") as f:
            files[path] = json.load(f)
    return files


if __name__ == "__main__":
    fix = "--fix" in sys.argv
    files = load()
    first = {}
    copies = collections.defaultdict(list)
    for path, entries in files.items():
        for e in entries:
            if not e.get("pt"):
                continue
            key = (e["en"], e.get("max_width"), e.get("max_lines"), e.get("max_bytes"))
            first.setdefault(key, (path, e["pt"]))
            copies[key].append((path, e))
    changed = set()
    divergent = 0
    for en, items in copies.items():
        if len({e["pt"] for _, e in items}) < 2:
            continue
        divergent += 1
        src, pt = first[en]
        print("EN: %s" % en[0][:70])
        for path, e in items:
            mark = "=" if e["pt"] == pt else ("->" if fix else "!=")
            print("  %s %s %s: %s" % (mark, os.path.relpath(path, ROOT), e["offset"], e["pt"][:90]))
            if fix and e["pt"] != pt:
                e["pt"] = pt
                changed.add(path)
    for path in changed:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(files[path], f, ensure_ascii=False, indent=1)
    print("%d textos divergentes%s" % (divergent, ", corrigidos" if fix else ""))
