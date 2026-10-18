"""Applies the glossary's final spellings to every translation.

Batches were translated in parallel, so a few recurring terms came out in
more than one form. Each rule below rewrites the losing form in "pt"; the
script prints how many lines each rule touched. Run it after all batches
are filled and before consistencia.py.

usage: python3 tools/padronizar.py [--dry-run]
"""

import glob
import json
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(__file__), "..", "traducao")

# (pattern, replacement): regexes over the Portuguese text
RULES = [
    (r"JARDINS DO CASTELO", "JARDIM DO CASTELO"),
    (r"CAVERNA CINTILANTE", "GRUTA CINTILANTE"),
    (r"GLITTERING CAVE", "GRUTA CINTILANTE"),
    (r"MUSHROOM HILL", "COLINA COGUMELO"),
    (r"TEAM AQUA", "EQUIPE AQUA"),
    (r"TEAM MAGMA", "EQUIPE MAGMA"),
    (r"MR\. BRINEY", "SR. BRINEY"),
    (r"CAPT\. STERN", "CAPITÃO STERN"),
    (r"MONTE CHIMNEY", "MT. CHIMNEY"),
    (r"SERPENTE DE BATALHA", "TRILHA DE BATALHA"),
    (r"Batalha de Escolha", "Escolha de Batalha"),
    (r"Batalha de Troca", "Troca de Batalha"),
    (r"FÃ-CLUBE DAS CAPTURAS", "FÃ-CLUBE DE CAPTURAS"),
    (r"JORNAL DAS CAPTURAS", "NOTÍCIAS CAPTURA"),
    (r"SOLDADO GOOMP", "PRIVATE GOOMP"),
    # TM/HM stay in English (the MT/MO -> TM/HM pass, with article
    # agreement, was done once; these catch any new bare uses)
    (r"(?<![A-Za-zÀ-ÿ])MT(s?)(?=\d|\b)(?!\. [A-Z])", r"TM\1"),
    (r"(?<![A-Za-zÀ-ÿ])MO(s?)(?=\d|\b)(?!\. [A-Z])", r"HM\1"),
    # BAG is BOLSA; MOCHILA stays only in item names (MOCHILA DO CAPITÃO,
    # MOCHILA DE EXPLORADOR)
    (r"\bMOCHILA\b(?! D[EO] )", "BOLSA"),
]


def main(dry_run):
    counts = [0] * len(RULES)
    for path in sorted(glob.glob(os.path.join(ROOT, "**", "*.json"), recursive=True)):
        with open(path, encoding="utf-8") as f:
            entries = json.load(f)
        changed = False
        for e in entries:
            pt = e.get("pt", "")
            for i, (pat, rep) in enumerate(RULES):
                new = re.sub(pat, rep, pt)
                if new != pt:
                    counts[i] += 1
                    pt = new
            if pt != e.get("pt", ""):
                e["pt"] = pt
                changed = True
        if changed and not dry_run:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(entries, f, ensure_ascii=False, indent=1)
    for (pat, rep), n in zip(RULES, counts):
        if n:
            print("%4d  %s -> %s" % (n, pat, rep))


if __name__ == "__main__":
    main("--dry-run" in sys.argv)
