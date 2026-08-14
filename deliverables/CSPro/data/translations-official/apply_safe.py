#!/usr/bin/env python3
r"""Write the verified-safe cleared translations into the instrument translation maps.

Fills strings the tablet currently renders in English, using the DOH-cleared June-5
wording verbatim. Nothing is authored here.

THE CONSTRAINT THAT SHAPES THIS SCRIPT
--------------------------------------
apply_translations() keys on the FULL English label text of each label node
(cspro_helpers.apply_translations). For a value-set option the label is the BARE option
text (cspro_helpers._value_set), so a key like "No" is shared by EVERY value set in that
instrument - 36 of them in F1. A key therefore cannot carry two different translations.

So an option fix is only safe when every question proposing it proposes the SAME wording.
Where the cleared source disagrees across questions (the Dai/Dae split behind #1222), the
key is SKIPPED and reported: expressing it needs per-question keys, i.e. a generator
change, not a translation-map edit.

Also skipped: keys that already hold a real translation. RECOVERABLE means the tablet
shows English, so such a key means the audit and the map disagree - not something to
overwrite silently.

Formatting is preserved per file (indent width, CRLF, insertion order). A blind re-dump
produced ~2,700 lines of diff noise on 2026-08-13 and buried the real change.

    python apply_safe.py                 # dry run - report only
    python apply_safe.py --apply         # write the maps
    python apply_safe.py --apply --only F1
"""
import argparse
import io
import json
import os
import re
from collections import Counter, OrderedDict, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
CSPRO = os.path.abspath(os.path.join(HERE, "..", ".."))
SAFE = os.path.join(HERE, "safe_to_apply.json")


def norm(s):
    return re.sub(r"\s+", " ", (s or "").strip())


def load_map(path):
    raw = io.open(path, encoding="utf-8").read()
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
        tdir = os.path.join(CSPRO, inst, "translations")
        for lg in sorted(safe[inst]):
            path = os.path.join(tdir, lg.lower() + ".json")
            if not os.path.exists(path):
                print(f"  {inst}/{lg}: no map file - skipped")
                continue
            m, indent, crlf = load_map(path)

            # group proposals by the key apply_translations will actually look up
            proposals = defaultdict(list)
            for e in safe[inst][lg]:
                proposals[e["english"]].append(e)

            writes, skips = OrderedDict(), []
            for key, entries in proposals.items():
                vals = {norm(e["apply"]) for e in entries if norm(e["apply"])}
                if not vals:
                    continue
                if len(vals) > 1:
                    skips.append({"key": key, "reason": "conflicting wording across "
                                  f"{len(entries)} questions - needs per-question keys",
                                  "values": sorted(vals)[:4],
                                  "questions": sorted({e["q"] for e in entries})[:8]})
                    grand["skip_conflict"] += 1
                    continue
                val = vals.pop()
                cur = m.get(key)
                if cur is not None and norm(cur) != norm(key):
                    skips.append({"key": key, "reason": "map already holds a translation",
                                  "current": cur, "proposed": val})
                    grand["skip_existing"] += 1
                    continue
                if norm(val) == norm(key):
                    grand["skip_same_as_english"] += 1
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
          f"write {grand['write']}, "
          f"skip(conflict) {grand['skip_conflict']}, "
          f"skip(existing) {grand['skip_existing']}, "
          f"skip(same as English) {grand['skip_same_as_english']}")
    with io.open(a.report, "w", encoding="utf-8") as fh:
        json.dump(diff_out, fh, ensure_ascii=False, indent=1)
    print(f"Diff written to {a.report}")


if __name__ == "__main__":
    main()
