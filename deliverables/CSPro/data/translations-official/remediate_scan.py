#!/usr/bin/env python3
r"""Remediate scan_poisoned_keys.py findings against the cleared June-5 corpus.

Policy (conservative — wrong data is worse than English fallback):
  * value already == its OWN cleared text  -> false positive, skip (near-duplicate
    questions make WRONG_Q_CLEARED fire on correct translations, e.g. F4 Q119 BIS)
  * GLUED_CLEARED / WRONG_Q_CLEARED / EN_FRAGMENT / DOUBLED
        -> REPLACE with the own cleared text when it exists (stem via question
           number; option via EN-option match, only at option_confidence
           'matched' and a non-empty cleared string)
        -> else DELETE for the wrong-text classes (English fallback)
        -> else LEAVE + report for DOUBLED (reduplication is grammatical in
           Philippine languages — deleting on the heuristic alone destroys
           good translations; 2026-08-14 v2.1.1 lesson)
  * IS_OTHER_EN -> DELETE always (another node's English in the slot is the
    wrong-code class: #1231)
  * SELF_ECHO   -> DELETE (fallback produces the identical output)
  * STALE_KEY   -> DELETE (matches no dictionary node)

Maps are the machine-written name-scoped v2 files, so a re-dump with the same
serializer is formatting-stable (indent=2, LF, trailing newline).

    python remediate_scan.py findings.json            # report only
    python remediate_scan.py findings.json --write    # apply to the maps
"""
import argparse
import difflib
import io
import json
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
CSPRO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, CSPRO)
sys.path.insert(0, HERE)
from cspro_helpers import walk_labeled_nodes  # noqa: E402
from migrate_maps_namekeys import capture_source_dict  # noqa: E402

if hasattr(sys.stdout, "buffer") and (sys.stdout.encoding or "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)

OFFICIAL = os.path.join(HERE, "official_translations.json")
LABEL_Q = re.compile(r"^\s*(\d{1,3}(?:\.\d)?)\s*[\.\)]")
NAME_Q = re.compile(r"^Q(\d{1,3})(?:_(\d))?_")
NUM_PREFIX = re.compile(r"^\s*\d{1,3}(?:\.\d)?\s*[\.\)]\s*")


def norm(s):
    return re.sub(r"\s+", " ", NUM_PREFIX.sub("", (s or "")).strip().casefold())


def qnum_of(key, en):
    m = LABEL_Q.match(en or "")
    if m:
        return m.group(1)
    stem = key.split(":", 1)[1] if ":" in key else key
    m = NAME_Q.match(stem)
    if m:
        return m.group(1) + (f".{m.group(2)}" if m.group(2) else "")
    return None


def own_cleared(official, inst, loc, key, en):
    """Cleared text for THIS node in THIS locale, or None."""
    q = qnum_of(key, en)
    if not q:
        return None
    entry = official.get(inst, {}).get(q)
    if not entry:
        return None
    if key.startswith(("item:", "vs:")):
        stem = entry.get(loc, {}).get("stem")
        return stem or None
    if key.startswith("val:"):
        loc_e = entry.get(loc, {})
        if loc_e.get("option_confidence") != "matched":
            return None
        en_opts = [norm(o) for o in entry.get("EN", {}).get("options", [])]
        tgt = norm(en)
        hits = [i for i, o in enumerate(en_opts) if o == tgt]
        if len(hits) != 1:
            return None
        opts = loc_e.get("options", [])
        val = opts[hits[0]] if hits[0] < len(opts) else ""
        return val or None
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("findings")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()

    findings = json.load(io.open(a.findings, encoding="utf-8"))
    official = json.load(io.open(OFFICIAL, encoding="utf-8"))

    # own-EN per key needs the qnum from the item's label — the val: EN is the
    # bare option text with no number, so map val:VS -> parent item's qnum.
    key_en = {}
    vs_parent_q = {}
    for inst in sorted({f["instrument"] for f in findings}):
        src = capture_source_dict(inst, "generate_dcf.py")
        for key, node in walk_labeled_nodes(src):
            labs = node.get("labels")
            if (isinstance(labs, list) and labs and isinstance(labs[0], dict)
                    and "text" in labs[0]):
                key_en[(inst, key)] = labs[0]["text"]
        for lvl in src.get("levels", []):
            recs = list(lvl.get("records", []))
            items = [i for r in recs for i in r.get("items", [])]
            items += (lvl.get("ids") or {}).get("items", [])
            for it in items:
                q = qnum_of("item:" + it.get("name", ""),
                            (it.get("labels") or [{}])[0].get("text", ""))
                for vs in it.get("valueSets", []) or []:
                    vs_parent_q[(inst, vs.get("name"))] = q

    def own_cleared_for(f):
        inst, loc, key = f["instrument"], f["locale"], f["key"]
        en = f["en"] or ""
        if key.startswith("val:"):
            vs_name = key.split(":", 2)[1]
            q = vs_parent_q.get((inst, vs_name))
            if not q:
                return None
            entry = official.get(inst, {}).get(q)
            if not entry:
                return None
            loc_e = entry.get(loc, {})
            if loc_e.get("option_confidence") != "matched":
                return None
            en_opts = [norm(o) for o in entry.get("EN", {}).get("options", [])]
            hits = [i for i, o in enumerate(en_opts) if o == norm(en)]
            if len(hits) != 1:
                return None
            opts = loc_e.get("options", [])
            val = opts[hits[0]] if hits[0] < len(opts) else ""
            return val or None
        return own_cleared(official, inst, loc, key, en)

    DIRECTIVE = re.compile(r"\b(DO NOT READ|READ OPTIONS|SELECT ALL THAT APPLY)\b", re.I)

    def doubled(vtext):
        w = norm(vtext).split()
        n = len(w)
        if n < 2:
            return False
        if n % 2 == 0 and w[: n // 2] == w[n // 2:]:
            return True
        for size in range(1, n // 2 + 1):
            for i in range(n - 2 * size + 1):
                x, y = w[i:i + size], w[i + size:i + 2 * size]
                if x == y and sum(len(t) for t in x) >= 4:
                    return True
        return False

    def cleared_is_clean(cleared, current):
        """The cleared source has its own defects (doubled stems, embedded
        enumerator directives — the 2026-08-14 five defect classes). Only
        replace when the substitution is a strict improvement: cleared is not
        doubled and does not INTRODUCE a directive the current value lacks."""
        if doubled(cleared):
            return False
        if DIRECTIVE.search(cleared) and not DIRECTIVE.search(current):
            return False
        return True

    actions = []      # (inst, loc, key, action, old, new)
    for f in findings:
        inst, loc, key, reason = f["instrument"], f["locale"], f["key"], f["reason"]
        v = f["value"]
        cleared = own_cleared_for(f)
        if cleared and norm(v) == norm(cleared):
            actions.append((inst, loc, key, "SKIP_FALSE_POSITIVE", v, None))
            continue
        usable = cleared is not None and cleared_is_clean(cleared, v)
        if reason in ("STALE_KEY", "SELF_ECHO", "IS_OTHER_EN"):
            actions.append((inst, loc, key, "DELETE", v, None))
        elif reason in ("GLUED_CLEARED", "WRONG_Q_CLEARED", "EN_FRAGMENT"):
            if usable:
                actions.append((inst, loc, key, "REPLACE", v, cleared))
            else:
                actions.append((inst, loc, key, "DELETE", v, None))
        elif reason == "DOUBLED":
            if usable:
                actions.append((inst, loc, key, "REPLACE", v, cleared))
            else:
                # reduplication is grammatical in Philippine languages and the
                # cleared source may carry the same defect — human review, no
                # blind deletes (v2.1.1 lesson)
                actions.append((inst, loc, key, "REVIEW", v, None))

    tally = Counter(x[3] for x in actions)
    print("action tally:", dict(tally))

    by_file = {}
    for inst, loc, key, act, old, new in actions:
        by_file.setdefault((inst, loc), []).append((key, act, old, new))

    for (inst, loc), rows in sorted(by_file.items()):
        print(f"\n=== {inst}/{loc.lower()}.json")
        for key, act, old, new in rows:
            print(f"  {act:<20} {key}")
            if act in ("REPLACE",):
                print(f"      was: {old[:84]!r}")
                print(f"      now: {new[:84]!r}")
            elif act in ("DELETE", "REVIEW"):
                print(f"      val: {old[:84]!r}")

    if not a.write:
        print("\n(report only — re-run with --write to apply)")
        return

    for (inst, loc), rows in sorted(by_file.items()):
        path = os.path.join(CSPRO, inst, "translations", f"{loc.lower()}.json")
        m = json.load(io.open(path, encoding="utf-8"))
        changed = False
        for key, act, old, new in rows:
            if act == "REPLACE" and m.get(key) == old:
                m[key] = new
                changed = True
            elif act == "DELETE" and m.get(key) == old:
                del m[key]
                changed = True
        if changed:
            with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
                json.dump(m, fh, ensure_ascii=False, indent=2)
                fh.write("\n")
            print(f"wrote {path}")
    print("\napplied")


if __name__ == "__main__":
    main()
