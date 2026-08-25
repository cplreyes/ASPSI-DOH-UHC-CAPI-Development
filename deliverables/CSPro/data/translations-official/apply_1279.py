#!/usr/bin/env python3
r"""Apply the #1279 cleanup, honouring the audit - including its recovered text.

The audit's most valuable output was not the rejections but the RECOVERIES: for most of the
drops it judged needless, a reviewer supplied in `better` the exact translation that should
have been kept. The cleanup's own rules kept giving up on values shaped like

    "Enumerator: Applicable only to respondents in areas with GAMOT
     Kung oo, unsa ang imong mga tinubdan sa impormasyon bahin aning GAMOT Package?"

because the span removal left fragments behind and the residue failed a quality gate.

TRUSTING `better` SAFELY
------------------------
`better` is text produced by a language model, so it is NOT taken on faith. Each one is
accepted only if it is a pure DELETION of the stored value: every word of `better` must
appear in the original, in the same order. That makes it impossible for a reviewer to have
paraphrased, corrected spelling, or invented wording - the same guarantee the rest of this
pipeline gives. Anything failing the check keeps the cleanup's original disposition.

    python apply_1279.py --rejects <audit.json>            # dry run
    python apply_1279.py --rejects <audit.json> --apply
"""
import argparse
import io
import json
import os
import re

CS = (r"C:\Users\analy\Documents\analytiflow\1_Projects"
      r"\ASPSI-DOH-CAPI-CSPro-Development\deliverables\CSPro")


def norm(s):
    return re.sub(r"\s+", " ", (s or "").strip())


def words(s):
    return re.findall(r"[\w’'-]+", (s or "").lower())


def is_deletion_of(candidate, original):
    """True when `candidate` can be produced from `original` by deleting text only."""
    c, o = words(candidate), words(original)
    if not c:
        return False
    i = 0
    for w in o:
        if i < len(c) and w == c[i]:
            i += 1
    return i == len(c)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--diff", default="clean1279.json")
    ap.add_argument("--rejects", required=True)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    diff = json.loads(io.open(a.diff, encoding="utf-8").read())
    rr = json.loads(io.open(a.rejects, encoding="utf-8").read())
    if isinstance(rr, dict):
        rr = rr.get("rejects", [])

    # several reviewers may flag the same key with different replacement text; keep them
    # all and use the first that survives the deletion check
    by_key = {}
    for r in rr:
        by_key.setdefault((r.get("instrument", "").upper(), r.get("locale", "").lower(),
                           norm(r.get("key"))), []).append(r)

    plan = {}                      # (inst, loc) -> {key: value or None}
    stats = {"trim": 0, "drop": 0, "recovered": 0, "reject_kept": 0, "better_refused": 0}

    for x in diff:
        inst, loc, key = x["instrument"], x["locale"], x["key"]
        cands = by_key.get((inst, loc, norm(key)))
        action, value = x["action"], (x["now"] or None)

        if cands:
            better = ""
            for c in cands:
                b = norm(c.get("better") or "")
                if b and is_deletion_of(b, x["was"]):
                    better = b
                    break
            offered = any(norm(c.get("better") or "") for c in cands)
            if better:
                action, value = "trim", better
                stats["recovered"] += 1
            elif offered:
                # a "better" that is not a pure deletion would be composed text
                stats["better_refused"] += 1
                stats["reject_kept"] += 1
                continue
            else:
                # vetoed with no replacement -> leave the stored value untouched
                stats["reject_kept"] += 1
                continue

        plan.setdefault((inst, loc), {})[key] = value if action == "trim" else None
        stats["trim" if action == "trim" else "drop"] += 1

    print(f"trims {stats['trim']}, drops {stats['drop']}, "
          f"recovered-from-audit {stats['recovered']}, "
          f"left untouched {stats['reject_kept']} "
          f"(of which {stats['better_refused']} had non-deletion 'better' text)")

    if a.apply:
        for (inst, loc), items in plan.items():
            path = os.path.join(CS, inst, "translations", loc + ".json")
            obj = json.loads(io.open(path, encoding="utf-8").read())
            for k, v in items.items():
                if v is None:
                    obj.pop(k, None)
                else:
                    obj[k] = v
            with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
                json.dump(obj, fh, ensure_ascii=False, indent=1)
        print(f"APPLIED to {len(plan)} maps")


if __name__ == "__main__":
    main()
