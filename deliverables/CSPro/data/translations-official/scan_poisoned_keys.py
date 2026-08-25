#!/usr/bin/env python3
r"""Find poisoned entries in the (name-scoped) translation maps.

2026-08-17 v2 — rewritten for the name-scoped map format AND extended with the
wrong-question-text detectors the render-evidence run proved necessary: the F3
Waray Q2 slot held a fluent Waray EXPENSES question — untranslated-English scans
can never see that class, only comparison against the cleared corpus can.

Detectors, per map entry (key -> value):
  DOUBLED         value contains an adjacent repeated word-run ("NBB compliance NBB compliance")
  SELF_ECHO       value == its node's source English (untranslated, masking a gap)
  IS_OTHER_EN     value == the source English of a DIFFERENT node
  EN_FRAGMENT     value contains a >=20-char different node's English (glued/spilled English)
  WRONG_Q_CLEARED value == the CLEARED translation (same locale) of a DIFFERENT question
  GLUED_CLEARED   value == the cleared translation of its OWN question + extra junk
  STALE_KEY       key no longer matches any node of the dictionary (post-edit orphan)

English per node comes from the PRE-APPLY source dictionary (captured the same way
the migrator does), because post-apply passes (#714) rewrite built labels.

Run:  python scan_poisoned_keys.py [--apply-report out.json]
NOTE: capturing the source dictionaries runs each generate_dcf.py, so the .dcf
files are regenerated (from the current maps) as a side effect.
"""
import argparse
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

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)

INSTR = ["F1", "F3", "F4"]
OFFICIAL = os.path.join(HERE, "official_translations.json")
LABEL_Q = re.compile(r"^\s*(\d{1,3}(?:\.\d)?)\s*[\.\)]")
NAME_Q = re.compile(r"^Q(\d{1,3})(?:_(\d))?_")
NUM_PREFIX = re.compile(r"^\s*\d{1,3}(?:\.\d)?\s*[\.\)]\s*")


def norm(s):
    return re.sub(r"\s+", " ", NUM_PREFIX.sub("", (s or "")).strip().casefold())


def doubled(v):
    """Any adjacent repeated run of words, anywhere in the value (v1 heuristic,
    kept verbatim: it caught 'Publikong bus Taxi Taxi' post-deploy)."""
    w = norm(v).split()
    n = len(w)
    if n < 2:
        return False
    if n % 2 == 0 and w[: n // 2] == w[n // 2:]:
        return True
    for size in range(1, n // 2 + 1):
        for i in range(n - 2 * size + 1):
            a, b = w[i:i + size], w[i + size:i + 2 * size]
            if a == b and sum(len(x) for x in a) >= 4:
                return True
    return False


def qnum_of(key, en):
    # Label number first: it carries sub-numbers the item name flattens
    # (Q61_DELAY_REASON is labeled "61.1." — name-first misfiled it as 61).
    m = LABEL_Q.match(en or "")
    if m:
        return m.group(1)
    stem = key.split(":", 1)[1] if ":" in key else key
    m = NAME_Q.match(stem)
    if m:
        return m.group(1) + (f".{m.group(2)}" if m.group(2) else "")
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply-report")
    a = ap.parse_args()

    official = json.load(io.open(OFFICIAL, encoding="utf-8"))
    findings = []
    tally = Counter()

    for inst in INSTR:
        tdir = os.path.join(CSPRO, inst, "translations")
        if not os.path.isdir(tdir):
            continue
        src = capture_source_dict(inst, "generate_dcf.py")
        key2en = {}
        for key, node in walk_labeled_nodes(src):
            labs = node.get("labels")
            if (isinstance(labs, list) and labs and isinstance(labs[0], dict)
                    and "text" in labs[0]):
                key2en[key] = labs[0]["text"]
        en_index = {}                                  # norm(EN) -> set of keys
        for k, en in key2en.items():
            en_index.setdefault(norm(en), set()).add(k)
        frag_ens = [(en.casefold(), k) for k, en in key2en.items() if len(en) >= 20]

        cleared_by_loc = {}                            # LOC -> norm(stem) -> qnum
        cleared_en = {}                                # qnum -> EN stem
        for q, per_loc in official.get(inst, {}).items():
            if per_loc.get("EN", {}).get("stem"):
                cleared_en[q] = per_loc["EN"]["stem"]
            for loc, entry in per_loc.items():
                if loc == "EN":
                    continue
                stem = entry.get("stem")
                if stem and len(norm(stem)) >= 15:
                    cleared_by_loc.setdefault(loc, {})[norm(stem)] = q
        cleared_stem = {}                              # (LOC, qnum) -> stem text
        for q, per_loc in official.get(inst, {}).items():
            for loc, entry in per_loc.items():
                if loc != "EN" and entry.get("stem"):
                    cleared_stem[(loc, q)] = entry["stem"]

        for fn in sorted(os.listdir(tdir)):
            if not fn.endswith(".json"):
                continue
            loc = fn[:-5].upper()
            m = json.load(io.open(os.path.join(tdir, fn), encoding="utf-8"))
            m.pop("_meta", None)
            for k, v in m.items():
                en = key2en.get(k)
                reasons = []
                if en is None:
                    reasons.append("STALE_KEY")
                else:
                    is_stem = k.startswith(("item:", "vs:"))
                    if doubled(v):
                        reasons.append("DOUBLED")
                    if norm(v) == norm(en):
                        reasons.append("SELF_ECHO")
                    else:
                        hit = en_index.get(norm(v))
                        if hit and k not in hit and len(norm(v)) >= 8:
                            reasons.append("IS_OTHER_EN")
                    if not reasons:
                        vf = v.casefold()
                        enf = en.casefold()
                        for frag, fk in frag_ens:
                            if fk != k and frag in vf and frag not in enf:
                                reasons.append("EN_FRAGMENT")
                                break
                    if is_stem and not reasons:
                        q = qnum_of(k, en)
                        own = cleared_stem.get((loc, q)) if q else None
                        wrong = cleared_by_loc.get(loc, {}).get(norm(v))
                        # Numbering guard: CAPI and cleared numbering drift in
                        # places (the Q107 lesson), so a number mismatch alone is
                        # not wrong text — only flag when the OTHER question's
                        # ENGLISH also disagrees with this node's English.
                        if wrong and wrong != q:
                            other_en = cleared_en.get(wrong, "")
                            import difflib
                            same_q = (difflib.SequenceMatcher(
                                None, norm(en), norm(other_en)).ratio() >= 0.75)
                            if not same_q:
                                reasons.append("WRONG_Q_CLEARED")
                        elif own and v != own and norm(v) != norm(own):
                            o = own.strip()
                            vv = v.strip()
                            if (vv.startswith(o) or vv.endswith(o)) and len(vv) > len(o) + 2:
                                reasons.append("GLUED_CLEARED")
                for reason in reasons:
                    tally[(inst, loc, reason)] += 1
                    findings.append({"instrument": inst, "locale": loc, "reason": reason,
                                     "key": k, "en": en, "value": v})

    print(f"\n{'instrument':<11}{'locale':<8}{'reason':<16}{'count':>7}")
    for (inst, lg, reason), n in sorted(tally.items()):
        print(f"{inst:<11}{lg:<8}{reason:<16}{n:>7}")
    print(f"\nTOTAL suspect entries: {len(findings)}")

    print("\n--- samples (one per reason/instrument/locale) ---")
    seen = set()
    for f in findings:
        tag = (f["reason"], f["instrument"], f["locale"])
        if tag in seen:
            continue
        seen.add(tag)
        print(f"\n[{f['reason']}] {f['instrument']}/{f['locale']}  {f['key'][:60]}")
        print(f"   en    : {(f['en'] or '')[:100]}")
        print(f"   value : {f['value'][:100]}")

    if a.apply_report:
        with io.open(a.apply_report, "w", encoding="utf-8") as fh:
            json.dump(findings, fh, ensure_ascii=False, indent=1)
        print(f"\nWrote {a.apply_report}")


if __name__ == "__main__":
    main()
