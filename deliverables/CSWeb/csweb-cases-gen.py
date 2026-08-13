#!/usr/bin/env python3
"""Per-case F1/F3/F4 detail JSON for /docs/case.html — the uniform counterpart of
csweb-f2-cases-gen.py, so every instrument's case opens on the console's own login.

Before this, F2 rows opened here while F1/F3/F4 bounced to CSWeb and a SECOND,
different login. Same viewing experience for all four is the point.

Source of truth: the data-room CSVs that csweb-responses-gen.py already writes
every 2 minutes — NOT a fresh MySQL query. Two reasons:
  * the console viewer can then never disagree with the CSV / SPSS / Stata / R
    exports, because it is reading the very same extraction; and
  * no database credential goes anywhere near a web page (the viewer is static
    HTML that fetches these files).

Labels come from the published f<n>_codebook.csv (variable,variable_label,value,
value_label) — both variable AND value labels, already in sync with the exports.
That is better than re-parsing the .dcf: one codebook, one truth.

Layout written:
  /docs/cases/<inst>/_labels.json   variable + value labels, ONE per instrument
  /docs/cases/<inst>/<qn>.json      code+raw only, per case
Splitting the labels out keeps each case file small and lets the browser cache the
labels once while a reader moves between cases — the same lesson as plan.json on
the dashboard: never ship reference data with every record.
"""
import csv, glob, json, os, sys, datetime

DATA_DIR = "/opt/app/lamp/www/docs/data"
OUT_ROOT = "/opt/app/lamp/www/docs/cases"
INSTS = ("f1", "f3", "f4")

# Columns that are case identity/provenance, surfaced as meta rather than answers.
META_COLS = ("questionnaire_number", "phase", "activity")


def read_csv(path):
    """utf-8-sig: every data-room CSV carries a BOM (written for Excel), and a
    stray \\ufeff on the first header would silently break the column lookup."""
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_labels(inst):
    """-> (var_labels{col:label}, val_labels{col:{code:label}})

    Parsed with the csv module, never by splitting on commas: variable_label
    routinely contains commas and quoted text (e.g. an instruction to the
    interviewer), which field-splitting shreds."""
    path = os.path.join(DATA_DIR, "%s_codebook.csv" % inst)
    var, val = {}, {}
    for r in read_csv(path):
        col = (r.get("variable") or "").strip()
        if not col:
            continue
        lab = (r.get("variable_label") or "").strip()
        if lab and col not in var:
            var[col] = lab
        code = (r.get("value") or "").strip()
        vlab = (r.get("value_label") or "").strip()
        if code != "" and vlab:
            val.setdefault(col, {})[code] = vlab
    return var, val


def qkey(q):
    """Join key. The breakout drops the questionnaire number's leading zero, and
    different exports have historically disagreed on whether it is 11 or 12 chars,
    so every join normalises rather than trusting the stored width."""
    return (q or "").strip().lstrip("0")


def load_rosters(inst):
    """-> {qn_key: [ {record, rows:[{occ, cells:{col:val}}]} ]} for this instrument."""
    out = {}
    for path in sorted(glob.glob(os.path.join(DATA_DIR, "%s_roster_*.csv" % inst))):
        record = os.path.basename(path)[len(inst) + 8:-4]      # strip "<inst>_roster_" / ".csv"
        for r in read_csv(path):
            k = qkey(r.get("questionnaire_number"))
            if not k:
                continue
            cells = {c: v for c, v in r.items()
                     if c not in ("questionnaire_number", "occ") and c}
            if not any((v or "").strip() for v in cells.values()):
                continue                                        # an all-blank occurrence is not a row
            grp = out.setdefault(k, {}).setdefault(record, [])
            grp.append({"occ": (r.get("occ") or "").strip(), "cells": cells})
    # dict-of-dict -> stable list, rosters in filename order, rows by occurrence
    return {k: [{"record": rec, "rows": sorted(rows, key=lambda x: _occ(x["occ"]))}
                for rec, rows in sorted(v.items())]
            for k, v in out.items()}


def _occ(o):
    try:
        return int(o)
    except Exception:
        return 10 ** 6


def write_if_changed(path, blob):
    """Atomic, and only when content actually differs — `generated` is excluded
    from the comparison or every run would rewrite every file and the mtimes
    would stop meaning "the data changed"."""
    cmp_new = json.dumps({k: v for k, v in blob.items() if k != "generated"},
                         sort_keys=True, ensure_ascii=False)
    try:
        prev = json.load(open(path, encoding="utf-8"))
        if json.dumps({k: v for k, v in prev.items() if k != "generated"},
                      sort_keys=True, ensure_ascii=False) == cmp_new:
            return False
    except Exception:
        pass
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(blob, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, path)
    return True


def main():
    gen = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    total_w = total_s = 0
    failed = []

    for inst in INSTS:
        out_dir = os.path.join(OUT_ROOT, inst)
        os.makedirs(out_dir, exist_ok=True)
        # Same refuse-guard as the responses generator: /docs/ FilesMatch rules match
        # FILENAMES, so an ungated directory of respondent answers would be public.
        if not os.path.isfile(os.path.join(OUT_ROOT, ".htaccess")):
            print("REFUSING: %s/.htaccess missing — an ungated dir here would be public."
                  % OUT_ROOT)
            return 2
        resp_csv = os.path.join(DATA_DIR, "%s_responses.csv" % inst)
        if not os.path.isfile(resp_csv):
            print("ERROR %s: %s missing — skipped" % (inst, resp_csv))
            failed.append(inst)
            continue

        var_labels, val_labels = load_labels(inst)
        rosters = load_rosters(inst)
        rows = read_csv(resp_csv)

        # Labels ship once per instrument, not once per case.
        if write_if_changed(os.path.join(out_dir, "_labels.json"),
                            {"inst": inst, "var": var_labels, "val": val_labels,
                             "generated": gen}):
            print("  %s: _labels.json updated (%d vars, %d coded)"
                  % (inst, len(var_labels), len(val_labels)))

        w = s = 0
        for r in rows:
            qn = (r.get("questionnaire_number") or "").strip()
            if not qn:
                continue
            answers = [{"c": c, "v": (v or "").strip()}
                       for c, v in r.items()
                       if c and c not in META_COLS]
            blob = {
                "inst": inst, "qn": qn,
                "phase": (r.get("phase") or "").strip(),
                "activity": (r.get("activity") or "").strip(),
                "answered": sum(1 for a in answers if a["v"] != ""),
                "answers": answers,
                "rosters": rosters.get(qkey(qn), []),
                "generated": gen,
            }
            # The filename is the questionnaire number exactly as the dashboard's
            # case list carries it, so the link needs no transformation.
            safe = "".join(ch for ch in qn if ch.isalnum())
            if not safe:
                failed.append(qn)
                continue
            if write_if_changed(os.path.join(out_dir, safe + ".json"), blob):
                w += 1
            else:
                s += 1
        total_w += w
        total_s += s
        print("  %s: %d cases (%d written, %d unchanged, %d roster records)"
              % (inst, len(rows), w, s, sum(len(v) for v in rosters.values())))

    print("cases: %d written, %d unchanged, %d FAILED -> %s"
          % (total_w, total_s, len(failed), OUT_ROOT))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
