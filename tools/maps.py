"""Groups the text catalogue by map.

Finds the map header table (gMapGroups) by structure, names each map from
the region map section table, and assigns every string to the map whose
script block contains the pointer that refers to it. In decomp builds each
map's scripts and texts are emitted together, starting at the map's
MapScripts table, so the block between one map's scripts and the next is
that map's.

usage: python3 tools/maps.py ROM.gba build/textos.json build/mapas.json
"""

import bisect
import json
import struct
import sys

from gen3text import decode

ROM_BASE = 0x08000000
HEADER_SIZE = 0x1C


def ptr(rom, at):
    if at + 4 > len(rom):
        return None
    v = struct.unpack_from("<I", rom, at)[0]
    return v - ROM_BASE if ROM_BASE <= v < ROM_BASE + len(rom) else None


def is_layout(rom, off):
    if off is None or off + 24 > len(rom):
        return False
    w, h = struct.unpack_from("<ii", rom, off)
    return 0 < w <= 0x200 and 0 < h <= 0x200 and all(ptr(rom, off + 8 + 4 * i) for i in range(4))


def is_events(rom, off):
    if off is None or off + 20 > len(rom):
        return False
    counts = rom[off:off + 4]
    if max(counts) > 128:
        return False
    for i, n in enumerate(counts):
        p = struct.unpack_from("<I", rom, off + 4 + 4 * i)[0]
        if n and ptr(rom, off + 4 + 4 * i) is None:
            return False
        if not n and p and ptr(rom, off + 4 + 4 * i) is None:
            return False
    return True


def is_header(rom, off):
    return (is_layout(rom, ptr(rom, off)) and is_events(rom, ptr(rom, off + 4))
            and ptr(rom, off + 8) is not None)


def find_map_groups(rom):
    """gMapGroups: array of pointers to arrays of header pointers. Picks the
    longest run of such pointers."""
    best = []
    off = 0
    while off < len(rom) - 4:
        run = []
        o = off
        while True:
            g = ptr(rom, o)
            if g is None or not ptr(rom, g) or not is_header(rom, ptr(rom, g)):
                break
            run.append(g)
            o += 4
        if len(run) > len(best):
            best = run
            best_at = off
        off = o + 4 if run else off + 4
    groups = []
    starts = sorted(set(best))
    for gi, g in enumerate(best):
        maps = []
        o = g
        # a group ends at the next group's array or at the first non-header
        nxt = min([s for s in starts if s > g] or [len(rom)])
        while o < nxt:
            h = ptr(rom, o)
            if h is None or not is_header(rom, h):
                break
            maps.append(h)
            o += 4
        groups.append(maps)
    return best_at, groups


def find_section_names(rom):
    """Region map entries are {u8 x, y, w, h; u8 *name}: the table is the
    longest run of entries with small coordinates and a decodable name."""
    def entry(a):
        p = ptr(rom, a + 4)
        if (p is None or max(rom[a], rom[a + 1]) >= 64
                or not (1 <= rom[a + 2] <= 32 and 1 <= rom[a + 3] <= 32)):
            return None
        res = decode(rom, p)
        return res[0] if res else None

    best_at, best = None, []
    a = 0
    while a < len(rom) - 8:
        run = []
        while (name := entry(a + 8 * len(run))) is not None:
            run.append(name)
        if len(run) > len(best):
            best_at, best = a, run
        a += 8 * len(run) + 4 if run else 4
    return best_at, dict(enumerate(best))


def build(rom, catalogue):
    table_at, groups = find_map_groups(rom)
    names_at, names = find_section_names(rom)
    maps = []
    for gi, g in enumerate(groups):
        for mi, h in enumerate(g):
            maps.append({"group": gi, "num": mi, "header": "%07X" % h,
                         "scripts": ptr(rom, h + 8), "section": rom[h + 0x14],
                         "name": names.get(rom[h + 0x14], "?"), "texts": []})
    blocks = sorted((m["scripts"], k) for k, m in enumerate(maps))
    starts = [b[0] for b in blocks]
    for e in catalogue:
        owners = set()
        for site in e["pointers"]:
            i = bisect.bisect_right(starts, int(site, 16)) - 1
            if i >= 0 and int(site, 16) - starts[i] < 0x40000:
                owners.add(blocks[i][1])
        for k in owners:
            maps[k]["texts"].append(e["offset"])
    for m in maps:
        m["scripts"] = "%07X" % m["scripts"]
    return {"map_groups": "%07X" % table_at,
            "section_names": "%07X" % names_at if names_at is not None else None,
            "maps": maps}


if __name__ == "__main__":
    rom = open(sys.argv[1], "rb").read()
    catalogue = json.load(open(sys.argv[2], encoding="utf-8"))
    result = build(rom, catalogue)
    with open(sys.argv[3], "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    maps = result["maps"]
    print("gMapGroups em %s, %d grupos, %d mapas, nomes em %s"
          % (result["map_groups"], len({m["group"] for m in maps}), len(maps),
             result["section_names"]))
