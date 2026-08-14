#!/usr/bin/env python3
r"""Delete translation values that have ANOTHER OPTION's text welded onto them.

Distinct from fix_poisoned.py. That one removes values which are wholly a repeated
phrase. This one targets the wider class byte-verification exposed after deploy:
a REAL translation with a foreign fragment appended, e.g.

    ceb.json  "Public Bus"  ->  "Publikong bus Taxi Taxi"

"Publikong bus" is correct; "Taxi Taxi" is the next option bleeding in. On screen the
Public Bus row reads "Taxi", so an enumerator picking it records Public Bus - the same
wrong-code defect as #1231.

WHY NOT JUST DELETE EVERY DOUBLED VALUE
---------------------------------------
Reduplication is grammatical in Philippine languages: Bikol "lain lain" (various),
"katanggap tanggap" (acceptable), Cebuano/Waray equivalents. A blanket doubled-word rule
deletes correct translations. So a value is removed ONLY when the doubled or trailing
fragment is demonstrably foreign - it matches another KEY in the same file, or it is an
English enumerator directive, or it carries an option-code prefix like "05-Flu".
Everything else is reported for translator review and left untouched.

    python fix_glued_options.py            # dry run
    python fix_glued_options.py --apply
"""
import argparse
import io
import json
import os
import re
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
CSPRO = os.path.abspath(os.path.join(HERE, "..", ".."))
DIRECTIVE = re.compile(r"(READ\s+OPTIONS?\s+OUT\s+LOUD|SELECT\s+ALL\s+THAT\s+APPLY"
                       r"|DO\s+NOT\s+READ|SELECT\s+ONE\s+ANSWER)", re.I)
CODE_PREFIX = re.compile(r"\b\d{2}-\w+\s+\d{2}-\w+")      # "05-Flu 05-Flu"
NUMBERED_ROW = re.compile(r"\b\d{2,3}\.\s+\S+\s+\S+")      # "157. Sub-total Sub-total"


def norm(s):
    return re.sub(r"\s+", " ", (s or "").strip())


def doubled_runs(v):
    """-> list of adjacent repeated word-runs found in the value."""
    w = norm(v).split()
    out = []
    n = len(w)
    for size in range(1, n // 2 + 1):
        for i in range(n - 2 * size + 1):
            a, b = w[i:i + size], w[i + size:i + 2 * size]
            if a == b and sum(len(x) for x in a) >= 4:
                out.append(" ".join(a))
    return out


def option_texts(keys):
    """Every OPTION label in the file, as its own string.

    Keys come in two shapes: a bare option ("Taxi") and a scoped one
    ("94. What mode/s of transportation ... — Taxi"). Matching a doubled run against the
    raw key list therefore missed "Taxi Taxi", because the file only holds the scoped
    form. Index the tail after the em-dash as well, so short option names are matched
    exactly instead of by a substring-length fudge that would swallow reduplication.
    """
    out = set()
    for k in keys:
        out.add(k.strip().lower())
        for sep in ("—", "–", " - "):
            if sep in k:
                out.add(k.rsplit(sep, 1)[-1].strip().lower())
    return {o for o in out if o}


def reason_to_delete(key, value, other_keys):
    if DIRECTIVE.search(value):
        return "English enumerator directive welded on"
    if CODE_PREFIX.search(value) or NUMBERED_ROW.search(value):
        return "another numbered option/row welded on"
    opts = option_texts(other_keys)
    for run in doubled_runs(value):
        rl = run.strip().lower()
        if len(rl) >= 3 and rl in opts:
            return f"contains another option's label ({run!r})"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    deleted = kept = 0
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

            keys = list(m)
            drop = []
            for k, v in m.items():
                if not doubled_runs(v):
                    continue
                why = reason_to_delete(k, v, [x for x in keys if x != k])
                tag = f"{inst}/{fn[:-5].upper()}"
                if why:
                    drop.append(k)
                    deleted += 1
                    print(f"  DELETE {tag} {k[:44]!r}\n         {v[:78]!r}\n         ({why})")
                else:
                    kept += 1
                    print(f"  keep   {tag} {k[:44]!r} -> {v[:60]!r}  (looks like reduplication)")
            if a.apply and drop:
                for k in drop:
                    del m[k]
                with io.open(path, "w", encoding="utf-8",
                             newline="\r\n" if crlf else "\n") as fh:
                    json.dump(m, fh, ensure_ascii=False, indent=indent)
                    fh.write("\n")

    print(f"\n{'APPLIED' if a.apply else 'DRY RUN'} - delete {deleted}, "
          f"keep {kept} for translator review")


if __name__ == "__main__":
    main()
