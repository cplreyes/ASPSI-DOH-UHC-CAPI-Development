#!/usr/bin/env python3
r"""Find poisoned entries in the translation JSONs.

#1231 exposed one the 2026-08-13 sweep missed: in F1/translations/bcl.json the bare key
"YAKAP/Konsulta utilization reports" maps to "NBB compliance NBB compliance" - a DIFFERENT
option's English text, doubled. The tablet therefore showed two identical NBB rows in
Q34's value set. The earlier sweep looked for English-looking values and for concatenated
English tails; it did not look for a value that is another option's text, nor for a value
that repeats itself.

Detects, per locale file:
  DOUBLED      value is the same phrase twice ("NBB compliance NBB compliance")
  IS_OTHER_KEY value is exactly some OTHER key in the same file (i.e. English of a
               different question/option pasted in as if it were a translation)
  SELF_ECHO    value equals its own key (untranslated, silently masking a gap)

Run:  python scan_poisoned_keys.py [--apply-report out.json]
"""
import argparse
import io
import json
import os
import re
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
CSPRO = os.path.abspath(os.path.join(HERE, "..", ".."))
INSTR = ["F1", "F3", "F4"]


def norm(s):
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def doubled(v):
    """'NBB compliance NBB compliance' -> True. Also catches 'x y x y'."""
    w = norm(v).split()
    n = len(w)
    if n < 2 or n % 2:
        return False
    return w[: n // 2] == w[n // 2:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply-report")
    a = ap.parse_args()

    findings = []
    tally = Counter()
    for inst in INSTR:
        tdir = os.path.join(CSPRO, inst, "translations")
        if not os.path.isdir(tdir):
            continue
        for fn in sorted(os.listdir(tdir)):
            if not fn.endswith(".json"):
                continue
            path = os.path.join(tdir, fn)
            m = json.loads(io.open(path, encoding="utf-8").read())
            keys_norm = {norm(k) for k in m}
            for k, v in m.items():
                reason = None
                if doubled(v):
                    reason = "DOUBLED"
                elif norm(v) == norm(k):
                    reason = "SELF_ECHO"
                elif norm(v) in keys_norm and norm(v) != norm(k):
                    reason = "IS_OTHER_KEY"
                if reason:
                    tally[(inst, fn[:-5].upper(), reason)] += 1
                    findings.append({"instrument": inst, "locale": fn[:-5].upper(),
                                     "reason": reason, "key": k, "value": v})

    print(f"{'instrument':<11}{'locale':<8}{'reason':<14}{'count':>7}")
    for (inst, lg, reason), n in sorted(tally.items()):
        print(f"{inst:<11}{lg:<8}{reason:<14}{n:>7}")
    print(f"\nTOTAL suspect entries: {len(findings)}")

    print("\n--- samples ---")
    seen = set()
    for f in findings:
        tag = (f["reason"], f["instrument"], f["locale"])
        if tag in seen:
            continue
        seen.add(tag)
        print(f"\n[{f['reason']}] {f['instrument']}/{f['locale']}")
        print(f"   key   : {f['key'][:110]}")
        print(f"   value : {f['value'][:110]}")

    if a.apply_report:
        with io.open(a.apply_report, "w", encoding="utf-8") as fh:
            json.dump(findings, fh, ensure_ascii=False, indent=1)
        print(f"\nWrote {a.apply_report}")


if __name__ == "__main__":
    main()
