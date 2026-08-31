#!/usr/bin/env python3
r"""Write the verified-safe cleared translations into the instrument translation maps.

Fills strings the tablet currently renders in English, using the DOH-cleared June-5
wording verbatim. Nothing is authored here.

2026-08-17 v2 — NAME-SCOPED KEYS. The old applier keyed on full English label text,
where a bare option key ("No") was shared by every value set in the instrument (36 in
F1), so per-question wording could not be expressed and 32 cleared keys had to be
skipped as conflicting (ILO Yes/No among them — the #1222 wall). The maps are now
name-scoped (cspro_helpers.walk_labeled_nodes):

    stem   -> item:<ITEM> and vs:<ITEM>_VS1 (the value-set label mirrors the item label)
    option -> val:<VS>:<code>, resolved from the safe entry's (item, index) against the
              PRE-APPLY source dictionary, with the entry's English asserted against the
              value's English label — a moved option is a skip, never a silent mis-write

Still skipped: keys already holding a DIFFERENT translation (the audit said English
renders, so map-vs-audit disagreement is surfaced, not overwritten), and proposals
equal to the English. Idempotent: already-applied entries count as `already_same`.

    python apply_safe.py                 # dry run - report only
    python apply_safe.py --apply         # write the maps
    python apply_safe.py --apply --only F1
"""
import argparse
import io
import json
import os
import re
import sys
from collections import Counter, OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
CSPRO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, CSPRO)
sys.path.insert(0, HERE)
from cspro_helpers import walk_labeled_nodes, _value_pair_key  # noqa: E402
from migrate_maps_namekeys import capture_source_dict  # noqa: E402

if hasattr(sys.stdout, "buffer") and (sys.stdout.encoding or "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)

SAFE = os.path.join(HERE, "safe_to_apply.json")


def norm(s):
    return re.sub(r"\s+", " ", (s or "").strip())


def load_map(path):
    # newline="" — without it Python's universal-newline translation eats the "\r"
    # and the crlf flag below is False for a CRLF map, so save_map would silently
    # rewrite the whole file with LF endings (a 100%-lines diff on every write).
    raw = io.open(path, encoding="utf-8", newline="").read()
    lines = raw.split("\n")
    indent = 1
    for ln in lines[1:]:
        if ln.strip().startswith('"'):
            indent = len(ln) - len(ln.lstrip(" "))
            break
    return json.loads(raw, object_pairs_hook=OrderedDict), max(indent, 1), "\r\n" in raw


def save_map(path, data, indent, crlf):
    with io.open(path, "w", encoding="utf-8", newline="\r\n" if crlf else "\n") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=indent)
        fh.write("\n")


def build_resolver(inst):
    """(entry) -> list of name-scoped keys, using the pre-apply source dictionary."""
    src = capture_source_dict(inst, "generate_dcf.py")
    all_keys = set()
    for key, _node in walk_labeled_nodes(src):
        all_keys.add(key)
    items = {}
    for lvl in src.get("levels", []):
        pool = list((lvl.get("ids") or {}).get("items", []) or [])
        for rec in lvl.get("records", []) or []:
            pool.extend(rec.get("items", []) or [])
        for it in pool:
            items[it.get("name")] = it

    def resolve(entry):
        item = items.get(entry.get("item"))
        if item is None:
            return None, f"item {entry.get('item')!r} not in dictionary"
        if entry.get("kind") == "stem":
            keys = [k for k in (f"item:{entry['item']}", f"vs:{entry['item']}_VS1")
                    if k in all_keys]
            return (keys or None), (None if keys else "no stem keys in dictionary")
        # option
        vss = item.get("valueSets") or []
        if not vss:
            return None, "item has no value set"
        vs = vss[0]
        values = vs.get("values") or []
        idx = entry.get("index")
        cand = None
        if isinstance(idx, int) and 0 <= idx < len(values):
            v = values[idx]
            v_en = (v.get("labels") or [{}])[0].get("text", "")
            if norm(v_en).casefold() == norm(entry.get("english")).casefold():
                cand = v
        if cand is None:      # index drifted — fall back to a UNIQUE English match
            hits = [v for v in values
                    if norm((v.get("labels") or [{}])[0].get("text", "")).casefold()
                    == norm(entry.get("english")).casefold()]
            if len(hits) == 1:
                cand = hits[0]
        if cand is None:
            return None, "option not found by index or unique English match"
        return [f"val:{vs.get('name')}:{_value_pair_key(cand)}"], None

    return resolve


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--only")
    ap.add_argument("--report", default=os.path.join(HERE, "apply_diff.json"))
    a = ap.parse_args()

    safe = json.loads(io.open(SAFE, encoding="utf-8").read())
    diff_out = {}
    grand = Counter()

    for inst in sorted(safe):
        if a.only and inst != a.only:
            continue
        resolve = build_resolver(inst)
        tdir = os.path.join(CSPRO, inst, "translations")
        for lg in sorted(safe[inst]):
            path = os.path.join(tdir, lg.lower() + ".json")
            if not os.path.exists(path):
                print(f"  {inst}/{lg}: no map file - skipped")
                continue
            m, indent, crlf = load_map(path)

            writes, skips = OrderedDict(), []
            proposed = {}                       # key -> value (conflict guard)
            for e in safe[inst][lg]:
                val = norm(e.get("apply"))
                if not val:
                    continue
                if val.casefold() == norm(e.get("english")).casefold():
                    grand["skip_same_as_english"] += 1
                    continue
                keys, why = resolve(e)
                if not keys:
                    skips.append({"entry": {k: e.get(k) for k in ("item", "kind", "index", "q")},
                                  "reason": why})
                    grand["skip_unresolved"] += 1
                    continue
                for key in keys:
                    if key in proposed and proposed[key] != val:
                        skips.append({"key": key, "reason": "two safe entries propose "
                                      "different wording for the same node",
                                      "values": [proposed[key], val]})
                        grand["skip_conflict"] += 1
                        continue
                    proposed[key] = val
                    cur = m.get(key)
                    if cur is not None:
                        if norm(cur) == val:
                            grand["already_same"] += 1
                        else:
                            skips.append({"key": key, "reason": "map already holds a "
                                          "different translation", "current": cur,
                                          "proposed": val})
                            grand["skip_existing"] += 1
                        continue
                    writes[key] = val
                    grand["write"] += 1

            diff_out.setdefault(inst, {})[lg] = {
                "writes": writes, "skips": skips,
                "counts": {"write": len(writes), "skip": len(skips)},
            }
            print(f"  {inst}/{lg}: write {len(writes):>4}   skip {len(skips):>3}"
                  f"   (map had {len(m)} keys)")

            if a.apply and writes:
                for k, v in writes.items():
                    m[k] = v
                save_map(path, m, indent, crlf)

    print(f"\n{'APPLIED' if a.apply else 'DRY RUN'} - "
          f"write {grand['write']}, already-same {grand['already_same']}, "
          f"skip(existing) {grand['skip_existing']}, "
          f"skip(conflict) {grand['skip_conflict']}, "
          f"skip(unresolved) {grand['skip_unresolved']}, "
          f"skip(same as English) {grand['skip_same_as_english']}")
    with io.open(a.report, "w", encoding="utf-8") as fh:
        json.dump(diff_out, fh, ensure_ascii=False, indent=1)
    print(f"Diff written to {a.report}")


if __name__ == "__main__":
    main()
