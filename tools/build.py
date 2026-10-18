"""Builds the PT-BR ROM and BPS patch from traducao/*.json.

Each translation file is a JSON list of {"offset", "en", "pt"} entries, plus
optional "max_width" (pixels per line, default 208 = one dialogue box line)
and "max_lines" (for fixed-size boxes such as menu descriptions). Entries
from fixed-size name tables carry "max_bytes" and are rewritten in place.
"en" must match the ROM, which guards against applying to another version.
Paragraphs (split on \\p) written without \\n or \\l are wrapped
automatically.

usage: python3 tools/build.py ROM.gba [build/]
       python3 tools/build.py ROM.gba --check   (validates, writes nothing)
"""

import glob
import json
import os
import re
import sys

import bps
import font
import tabelas
from extract import find_pointers, fragment_of, ROM_BASE
from gen3text import decode, encode

BOX_WIDTH = 208
PLAYER_NAME_WIDTH = 7 * 6
NORMAL_WIDTHS = font.FONTS[-1][1]
FREE_SPACE_MIN = 0x10000
EXT_ARGS = {0x04: 3, 0x0B: 2, 0x10: 2}
EXT_NO_ARG = {0x00, 0x07, 0x09, 0x0A, 0x0F, 0x15, 0x16, 0x17, 0x18}


def line_width(rom, line):
    b = encode(line)[:-1]
    w = i = 0
    while i < len(b):
        c = b[i]
        if c == 0xFD:
            w += PLAYER_NAME_WIDTH
            i += 2
        elif c == 0xFC:
            sub = b[i + 1]
            i += 2 + (0 if sub in EXT_NO_ARG else EXT_ARGS.get(sub, 1))
        elif c in (0xF7, 0xF8, 0xF9):
            w += 12
            i += 2
        else:
            w += rom[NORMAL_WIDTHS + c]
            i += 1
    return w


def wrap(rom, text, limit, newline_only=False):
    """Breaks paragraphs written without \\n/\\l into lines of at most
    limit pixels. Dialogue boxes use \\n then \\l (scroll); fixed boxes
    (newline_only) use \\n for every line."""
    paragraphs = text.split("\\p")
    out = []
    for para in paragraphs:
        if "\\n" in para or "\\l" in para or line_width(rom, para) <= limit:
            out.append(para)
            continue
        lines, cur = [], ""
        for word in re.split(r" (?![^{]*\})", para):
            cand = word if not cur else cur + " " + word
            if line_width(rom, cand) <= limit or not cur:
                cur = cand
            else:
                lines.append(cur)
                cur = word
        lines.append(cur)
        out.append(lines[0] + "".join(("\\n" if k == 1 or newline_only else "\\l") + l
                                      for k, l in enumerate(lines[1:], 1)))
    return "\\p".join(out)


def find_free_space(rom):
    """Largest run of FF bytes; translated strings that grew go there."""
    best = (0, 0)
    for m in re.finditer(rb"\xff{%d,}" % FREE_SPACE_MIN, rom):
        if m.end() - m.start() > best[1] - best[0]:
            best = (m.start(), m.end())
    if not best[1]:
        raise RuntimeError("sem espaço livre no ROM")
    start = (best[0] + 0x100 + 3) & ~3
    return start, best[1]


def load_translations():
    entries = []
    root = os.path.join(os.path.dirname(__file__), "..", "traducao")
    for path in sorted(glob.glob(os.path.join(root, "**", "*.json"), recursive=True)):
        with open(path, encoding="utf-8") as f:
            for e in json.load(f):
                if e.get("pt"):
                    e["file"] = os.path.relpath(path, root)
                    entries.append(e)
    return entries


def build(source):
    rom = bytearray(source)
    font.add_glyphs(rom)
    refs = find_pointers(source)
    free, free_end = find_free_space(source)
    errors, report = [], {"in_place": 0, "moved": 0}

    seen = {}
    written = []  # (start, end, where) of every in-place write

    def claim(start, end, where):
        """Refuses two translations writing over the same bytes."""
        for s, t, w in written:
            if start < t and s < end:
                errors.append("%s: sobrepõe %s (%07X-%07X)" % (where, w, s, t))
                return False
        written.append((start, end, where))
        return True

    for e in load_translations():
        where = "%s %s" % (e["file"], e["offset"])
        if e["offset"] in seen:
            errors.append("%s: já traduzido em %s" % (where, seen[e["offset"]]))
            continue
        seen[e["offset"]] = e["file"]
        off = int(e["offset"], 16)
        decoded = decode(source, off)
        if decoded is None or decoded[0] != e["en"]:
            errors.append("%s: texto em inglês não confere com o ROM" % where)
            continue
        end = decoded[1]
        if "max_bytes" not in e and any(a <= off < b for a, b in tabelas.table_ranges()):
            errors.append("%s: dentro de uma tabela de nomes fixa" % where)
            continue
        if "max_bytes" not in e and fragment_of(source, off) is not None:
            errors.append("%s: começa no meio de outra string (em %07X)"
                          % (where, fragment_of(source, off)))
            continue
        limit = e.get("max_width", BOX_WIDTH)
        try:
            # single-line labels (a width limit and no break in the original)
            # must fit as they are; wrapping them would split a menu entry
            label = ("max_width" in e and "max_lines" not in e
                     and not re.search(r"\\[nlp]", e["en"]))
            pt = e["pt"] if label else wrap(rom, e["pt"], limit, newline_only="max_lines" in e)
            data = encode(pt)
        except ValueError as ex:
            errors.append("%s: %s" % (where, ex))
            continue
        lines = re.split(r"\\[nlp]", re.sub(r"(\\p)+$", "", pt))
        for line in lines:
            if line_width(rom, line) > limit:
                errors.append("%s: linha com %dpx (máx %d): %r"
                              % (where, line_width(rom, line), limit, line))
        if len(lines) > e.get("max_lines", len(lines)):
            errors.append("%s: %d linhas (máx %d): %r"
                          % (where, len(lines), e["max_lines"], pt))
        if "max_bytes" in e:
            # fixed-size field (name tables): rewrite the whole field
            if len(data) > e["max_bytes"]:
                errors.append("%s: %d bytes (campo de %d): %r"
                              % (where, len(data), e["max_bytes"], pt))
                continue
            if not claim(off, off + e["max_bytes"], where):
                continue
            rom[off:off + e["max_bytes"]] = data + bytes(e["max_bytes"] - len(data))
            report["in_place"] += 1
            continue
        interior = [t for t in refs if off < t < end]
        if len(data) <= end - off and not interior:
            if not claim(off, end, where):
                continue
            rom[off:off + len(data)] = data
            report["in_place"] += 1
            continue
        sites = refs.get(off, [])
        if not sites:
            errors.append("%s: texto cresceu e não tem ponteiro para realocar" % where)
            continue
        if free + len(data) > free_end:
            errors.append("%s: espaço livre esgotado" % where)
            continue
        rom[free:free + len(data)] = data
        for s in sites:
            rom[s:s + 4] = (ROM_BASE + free).to_bytes(4, "little")
        free += len(data)
        report["moved"] += 1
    return bytes(rom), errors, report


if __name__ == "__main__":
    check = "--check" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--check"]
    src_path = args[0]
    out_dir = args[1] if len(args) > 1 else "build"
    source = open(src_path, "rb").read()
    rom, errors, report = build(source)
    if errors:
        print("\n".join(errors))
        sys.exit(1)
    if check:
        print("ok: %(in_place)d no lugar, %(moved)d realocados (só verificação)" % report)
        sys.exit(0)
    patch = bps.create(source, rom)
    assert bps.apply(source, patch) == rom
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "Mariomon-PTBR.gba"), "wb") as f:
        f.write(rom)
    with open(os.path.join(out_dir, "Mariomon-PTBR.bps"), "wb") as f:
        f.write(patch)
    print("ok: %(in_place)d no lugar, %(moved)d realocados" % report,
          "| patch %d bytes" % len(patch))
