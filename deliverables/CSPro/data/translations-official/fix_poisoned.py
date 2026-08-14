#!/usr/bin/env python3
r"""Remove the DOUBLED poisoned entries from the instrument translation maps.

Seven keys hold a value that is a DIFFERENT option's text, repeated - the corruption
class #1231 reported and that the 2026-08-13 sweep missed. Two are live data-integrity
defects, because the wrong label makes two options look identical and an enumerator
ticking one records the other:

    F3 CEB  Q52_PLANS       "Pag-ibig"    -> "SSS SSS"
    F4 BCL  Q94_TRANSPORT   "Public Bus"  -> "Taxi Taxi"

The fix is DELETION, not substitution. apply_translations falls back to the English label
when a key is absent, and for every one of these the cleared June-5 questionnaire leaves
the term in English anyway ("Pag-ibig", "Public Bus", "YAKAP/Konsulta utilization
reports"). Deleting therefore restores exactly the cleared wording, and invents nothing.

Formatting (indent, CRLF, key order) is preserved - a blind re-dump produced ~2,700 lines
of diff noise on 2026-08-13.

    python fix_poisoned.py            # dry run
    python fix_poisoned.py --apply
"""
import argparse
import io
import json
import os
import re
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
CSPRO = os.path.abspath(os.path.join(HERE, "..", ".."))


def norm(s):
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def doubled(v):
    w = norm(v).split()
    n = len(w)
    return n >= 2 and n % 2 == 0 and w[: n // 2] == w[n // 2:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    total = 0
    for inst in ("F1", "F3", "F4"):
        tdir = os.path.join(CSPRO, inst, "translations")
        if not os.path.isdir(tdir):
            continue
        for fn in sorted(os.listdir(tdir)):
            if not fn.endswith(".json"):
                continue
            path = os.path.join(tdir, fn)
            raw = io.open(path, encoding="utf-8").read()
            m = json.loads(raw, object_pairs_hook=OrderedDict)
            indent = 1
            for ln in raw.split("\n")[1:]:
                if ln.strip().startswith('"'):
                    indent = max(len(ln) - len(ln.lstrip(" ")), 1)
                    break
            crlf = "\r\n" in raw

            drop = [k for k, v in m.items() if doubled(v)]
            if not drop:
                continue
            for k in drop:
                print(f"  {inst}/{fn[:-5].upper()}: DROP {k!r} -> {m[k]!r}")
                total += 1
            if a.apply:
                for k in drop:
                    del m[k]
                with io.open(path, "w", encoding="utf-8",
                             newline="\r\n" if crlf else "\n") as fh:
                    json.dump(m, fh, ensure_ascii=False, indent=indent)
                    fh.write("\n")

    print(f"\n{'APPLIED' if a.apply else 'DRY RUN'} - {total} poisoned entries")


if __name__ == "__main__":
    main()
