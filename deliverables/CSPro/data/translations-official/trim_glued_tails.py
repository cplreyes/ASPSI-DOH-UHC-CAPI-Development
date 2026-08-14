#!/usr/bin/env python3
r"""Trim a doubled foreign fragment off the END of an otherwise-good translation.

Five values survived the automated passes: a correct translation with the NEXT option's
label repeated on the end.

    F3 ceb  "Public Bus"        -> "Publikong bus Taxi Taxi"
    F1 war  "Enumerator's Name" -> "Ngaran han Enumerator Resulta Resulta"

Deleting these would throw away a correct translation and fall back to English; keeping
them shows the wrong label on screen, which is how an enumerator records the wrong code.
So trim instead - and only at a boundary that can be identified exactly: the trailing
run must be a doubled fragment, and everything before it must still be non-empty.

This removes contamination; it does not compose translated text. The kept portion is
verbatim what the source already had.

    python trim_glued_tails.py            # dry run
    python trim_glued_tails.py --apply
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
    return re.sub(r"\s+", " ", (s or "").strip())


def trim(value, option_labels=frozenset()):
    """-> trimmed value, or None when there is nothing safe to cut.

    Cutting at ANY doubled run is destructive: it turned the good Ilocano
    "Adda ababa a panawen, panawen, kassual a trabaho/negosio" into "Adda ababa a" and
    the Waray "Mga panakot ngan iba pa nga panakot ..." into "Mga". Repeated words are
    ordinary in these languages.

    So cut only where the repetition is provably foreign - the doubled run is ANOTHER
    OPTION'S LABEL from the same file ("Taxi", "Resulta", "Multi-tasking") - or the run
    sits flush at the end of the string. Anything else is left for translator review.
    """
    w = norm(value).split()
    n = len(w)
    best = None
    for size in range(1, n // 2 + 1):
        for start in range(1, n - 2 * size + 1):
            a, b = w[start:start + size], w[start + size:start + 2 * size]
            if a != b or sum(len(x) for x in a) < 4:
                continue
            run = " ".join(a).strip(" .,;:()").lower()
            at_end = (start + 2 * size == n)
            if at_end or run in option_labels:
                best = start if best is None else min(best, start)
    if best is None:
        return None
    head = " ".join(w[:best]).strip(" -/,;:")
    # trailing debris like "aCodes: 1" that sits between the head and the doubled run
    head = re.sub(r"\s+a?Codes?:?\s*\d*$", "", head, flags=re.I).strip(" -/,;:")
    return head if len(head) >= 3 else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    n = 0
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

            labels = set()
            for k in m:
                labels.add(k.strip().lower())
                for sep in ('—', '–', ' - '):
                    if sep in k:
                        labels.add(k.rsplit(sep, 1)[-1].strip().lower())
            changed = False
            for k, v in list(m.items()):
                t = trim(v, labels)
                if t and t != norm(v):
                    print(f"  {inst}/{fn[:-5].upper()} {k[:40]!r}")
                    print(f"      was : {v[:80]!r}")
                    print(f"      now : {t[:80]!r}")
                    m[k] = t
                    changed = True
                    n += 1
            if a.apply and changed:
                with io.open(path, "w", encoding="utf-8",
                             newline="\r\n" if crlf else "\n") as fh:
                    json.dump(m, fh, ensure_ascii=False, indent=indent)
                    fh.write("\n")

    print(f"\n{'APPLIED' if a.apply else 'DRY RUN'} - {n} value(s) trimmed")


if __name__ == "__main__":
    main()
