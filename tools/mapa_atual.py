"""Tells which map the game is on, from an EWRAM dump (remote.lua DUMPWRAM).

The game keeps a copy of the current MapHeader in EWRAM; this finds the
28-byte copy that matches a header listed in build/mapas.json.

usage: python3 tools/mapa_atual.py ROM.gba ewram.bin build/mapas.json
"""

import json
import sys

HEADER_SIZE = 0x1C

rom = open(sys.argv[1], "rb").read()
ram = open(sys.argv[2], "rb").read()
maps = json.load(open(sys.argv[3], encoding="utf-8"))["maps"]
for m in maps:
    h = int(m["header"], 16)
    if rom[h:h + HEADER_SIZE] in ram:
        print("%d.%d %s (scripts %s, %d textos)"
              % (m["group"], m["num"], m["name"], m["scripts"], len(m["texts"])))
