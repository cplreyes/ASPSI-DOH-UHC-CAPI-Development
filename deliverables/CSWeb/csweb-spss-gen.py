#!/usr/bin/env python3
r"""Generate SPSS (.sav) case exports for ALL FOUR instruments from the
Responses Data Room CSVs + the questionnaire codebooks.

Why a separate generator (not just the CSVs): the data-room CSVs carry RAW
codes (1/2, not Male/Female). SPSS's whole value over CSV is the embedded
metadata — variable labels (the question text) and value labels (1="Male").
This script attaches both, so Marriz opens a .sav and every variable/value is
self-describing, no codebook lookup.

Label sources (the codebook truth):
  F1/F3/F4  the CSPro .dcf dictionaries (JSON, CSPro 8.0) — item labels +
            value-set code->label pairs. Data column names are the lowercased
            DCF item names, so the join is exact (verified 100% coverage).
  F2        f2-item-labels.json (extracted from the PWA's generated items;
            regenerate via the note at the bottom). F2 answers live in a
            values_json blob of already-English strings, so this EXPLODES the
            blob into one column per question (variable labels attached; values
            stay as strings — multi-selects joined with "; ").

Input = the Responses Data Room CSVs (produced by csweb-responses-gen.py):
  f1_responses.csv / f3_responses.csv / f4_responses.csv  (wide: 1 row/case)
  f{3,4}_roster_*.csv                                      (1 row/case x occ)
  f2_responses.csv                                         (values_json blob)
Output = one .sav per CSV + a per-instrument zip + a combined zip + manifest.

Decoupled from MySQL and from the box on purpose: it reads the CSVs the
responses generator already writes, so it runs anywhere those CSVs + the
committed DCFs land. To refresh: re-pull the data room, re-run.

  # pull the latest CSVs off the box (credential-free, read-only)
  scp -i ~/.ssh/aspsi-csweb 'root@207.148.65.115:/opt/app/lamp/www/docs/data/*.csv' <data-dir>/
  python deliverables/CSWeb/csweb-spss-gen.py --data-dir <data-dir> --out-dir <out>

Requires: pyreadstat, pandas (pip). Built 2026-07-20 ("the file Marriz needed").
"""
import argparse, csv, io, json, os, sys, zipfile, datetime
import pandas as pd
import pyreadstat

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))               # deliverables/
CSPRO = os.path.join(REPO, "CSPro")
DCF = {"f1": os.path.join(CSPRO, "F1", "FacilityHeadSurvey.dcf"),
       "f3": os.path.join(CSPRO, "F3", "PatientSurvey.dcf"),
       "f4": os.path.join(CSPRO, "F4", "HouseholdSurvey.dcf")}
NAMES = {"f1": "F1 - Facility Head", "f3": "F3 - Patient",
         "f4": "F4 - Household", "f2": "F2 - Healthcare Worker (PWA)"}
VARLABEL_MAX = 256      # SPSS variable-label byte cap
VALLABEL_MAX = 120      # SPSS value-label byte cap

# F2: the values_json keys that are provenance, not survey answers (kept as
# plain columns, no explode); everything else Q* is an answer column.
F2_META_KEYS = {"survey_language", "consent_given", "consent_timestamp",
                "facility_id", "facility_type", "gps_status",
                "submission_lat", "submission_lng"}
# F2 base columns to carry from the CSV (identity + provenance), in this order.
F2_BASE = ["submission_id", "qn", "hcw_id", "facility_id", "submitted_at_server",
           "status", "source_path", "spec_version", "app_version",
           "submission_lat", "submission_lng"]


def _en(o):
    labs = o.get("labels") or []
    for l in labs:
        if l.get("language") == "EN" and l.get("text"):
            return l["text"]
    for l in labs:
        if l.get("text"):
            return l["text"]
    return ""


def parse_dcf(path):
    """lower(item_name) -> {label, ctype, dec, vlabels{code:label}}."""
    d = json.load(open(path, encoding="utf-8"))
    out = {}
    for lv in d.get("levels", []):
        blocks = []
        if lv.get("ids"):
            blocks.append({"items": lv["ids"].get("items", [])})
        blocks += lv.get("records", [])
        for r in blocks:
            for it in r.get("items", []):
                vlabels = {}
                vs = it.get("valueSets") or []
                if vs:
                    for val in vs[0].get("values", []):
                        lab = _en(val)
                        for p in val.get("pairs", []):
                            # discrete codes only; skip validation RANGES (from/to)
                            if "value" in p and "from" not in p:
                                vlabels[str(p["value"]).strip()] = lab
                out[it["name"].lower()] = {
                    "label": _en(it), "ctype": it.get("contentType"),
                    "dec": it.get("decimalPlaces"), "vlabels": vlabels}
    return out


def read_csv_rows(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rd = csv.reader(f)
        header = next(rd)
        rows = list(rd)
    return header, rows


def numeric_or_none(cells):
    """Return (list, is_int) coercing all cells to numbers, or None if any
    non-empty cell is not numeric (then the column stays string)."""
    out, is_int = [], True
    for v in cells:
        if v is None or v == "":
            out.append(None)
            continue
        try:
            f = float(v)
        except (TypeError, ValueError):
            return None, False
        if not f.is_integer():
            is_int = False
        out.append(f)
    return out, is_int


def build_sav(csv_path, sav_path, itemmap, title, extra_labels=None):
    """Write one .sav from one wide/roster CSV using the DCF item map."""
    header, rows = read_csv_rows(csv_path)
    cols = {c: [r[i] if i < len(r) else "" for r in rows] for i, c in enumerate(header)}
    # Restore the canonical 12-digit QN: the F1/F3/F4 breakout stores
    # questionnaire_number numerically, so a leading region zero (e.g. 04) is
    # dropped -> 11 chars. Left-pad to 12 so it joins the F2 mirror's 12-digit
    # qn and reads as text (never scientific notation). Only pads all-digit keys.
    if "questionnaire_number" in cols:
        cols["questionnaire_number"] = [v.zfill(12) if v.isdigit() and len(v) < 12 else v
                                        for v in cols["questionnaire_number"]]
    data, var_labels, val_labels = {}, {}, {}
    for c in header:
        key = c.split("__", 1)[1] if "__" in c else c        # strip clash prefix
        meta = itemmap.get(key)
        raw = cols[c]
        label = (meta["label"] if meta else "") or (extra_labels or {}).get(c, "")
        var_labels[c] = (label or c)[:VARLABEL_MAX]
        numeric = None
        if c not in ("questionnaire_number", "occ") and meta and meta["ctype"] == "numeric":
            numeric, is_int = numeric_or_none(raw)
        elif c == "occ":
            numeric, is_int = numeric_or_none(raw)
        if numeric is not None:
            data[c] = pd.array([None if v is None else (int(v) if is_int else v)
                                for v in numeric], dtype="Int64" if is_int else "float64")
            if meta and meta["vlabels"]:
                vl = {}
                for code, lab in meta["vlabels"].items():
                    try:
                        k = int(float(code)) if is_int else float(code)
                    except ValueError:
                        continue
                    vl[k] = (lab or str(code))[:VALLABEL_MAX]
                if vl:
                    val_labels[c] = vl
        else:
            data[c] = pd.Series(["" if v is None else str(v) for v in raw], dtype="object")
    df = pd.DataFrame(data, columns=header)
    pyreadstat.write_sav(
        df, sav_path, file_label=title[:60],
        column_labels=[var_labels[c] for c in header],
        variable_value_labels=val_labels)
    return {"file": os.path.basename(sav_path), "rows": len(df), "cols": len(header)}


def build_f2(csv_path, sav_path, f2labels):
    """Explode f2 values_json into per-question columns and write .sav."""
    header, rows = read_csv_rows(csv_path)
    idx = {c: i for i, c in enumerate(header)}
    recs = []
    qkeys = []
    seen = set()
    for r in rows:
        try:
            vj = json.loads(r[idx["values_json"]] or "{}")
        except (ValueError, KeyError):
            vj = {}
        rec = {}
        for b in F2_BASE:
            rec[b] = r[idx[b]] if b in idx and idx[b] < len(r) else ""
        if rec.get("qn", "").isdigit() and len(rec["qn"]) < 12:      # canonical 12-digit
            rec["qn"] = rec["qn"].zfill(12)
        for k, v in vj.items():
            if k in F2_META_KEYS:
                continue
            if k not in seen:
                seen.add(k)
                qkeys.append(k)
            rec[k] = "; ".join(str(x) for x in v) if isinstance(v, list) else (
                "" if v is None else str(v))
        recs.append(rec)
    # stable column order: base identity, then Q* in questionnaire order
    def qsort(k):
        base = k.split("_")[0]
        try:
            return (int(base[1:]), k)
        except ValueError:
            return (10 ** 6, k)
    qcols = sorted(qkeys, key=qsort)
    header_out = F2_BASE + qcols
    data = {c: [rec.get(c, "") for rec in recs] for c in header_out}
    df = pd.DataFrame(data, columns=header_out)
    # F2 answers stay strings (already English); coerce the obvious numerics.
    num_base = {"submission_lat", "submission_lng"}
    for c in header_out:
        if c in num_base or (c in f2labels and f2labels[c].get("type") == "number"):
            nums, is_int = numeric_or_none(df[c].tolist())
            if nums is not None:
                df[c] = pd.array([None if v is None else (int(v) if is_int else v)
                                  for v in nums], dtype="Int64" if is_int else "float64")
    base_lab = {"submission_id": "Server submission ID", "qn": "Questionnaire number (12-digit)",
                "hcw_id": "Healthcare worker ID", "facility_id": "Facility ID / EA code",
                "submitted_at_server": "Server submission timestamp (UTC)",
                "status": "Submission status", "source_path": "Capture path (self-admin / paper-encoded)",
                "spec_version": "Questionnaire spec version", "app_version": "PWA app version",
                "submission_lat": "GPS latitude", "submission_lng": "GPS longitude"}
    labels = []
    for c in header_out:
        lab = base_lab.get(c) or (f2labels.get(c, {}).get("label") if c in f2labels else "") or c
        labels.append(lab[:VARLABEL_MAX])
    pyreadstat.write_sav(df, sav_path, file_label=NAMES["f2"][:60], column_labels=labels)
    return {"file": os.path.basename(sav_path), "rows": len(df), "cols": len(header_out)}


def main():
    ap = argparse.ArgumentParser(description="Generate SPSS .sav case exports for all instruments.")
    ap.add_argument("--data-dir", required=True, help="dir holding the data-room CSVs")
    ap.add_argument("--out-dir", required=True, help="output dir for the .sav files + zips")
    ap.add_argument("--f2-labels", default=os.path.join(HERE, "f2-item-labels.json"))
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    f2labels = json.load(open(a.f2_labels, encoding="utf-8")) if os.path.exists(a.f2_labels) else {}
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M")
    manifest = {"generated": stamp + " UTC", "instruments": {}}

    for inst in ("f1", "f3", "f4"):
        itemmap = parse_dcf(DCF[inst])
        made = []
        wide = os.path.join(a.data_dir, "%s_responses.csv" % inst)
        if os.path.exists(wide):
            made.append(build_sav(wide, os.path.join(a.out_dir, "%s_responses.sav" % inst),
                                  itemmap, NAMES[inst]))
        for fn in sorted(os.listdir(a.data_dir)):
            if fn.startswith("%s_roster_" % inst) and fn.endswith(".csv"):
                sav = fn[:-4] + ".sav"
                made.append(build_sav(os.path.join(a.data_dir, fn),
                                      os.path.join(a.out_dir, sav), itemmap, NAMES[inst]))
        manifest["instruments"][inst] = made

    f2csv = os.path.join(a.data_dir, "f2_responses.csv")
    if os.path.exists(f2csv):
        manifest["instruments"]["f2"] = [
            build_f2(f2csv, os.path.join(a.out_dir, "f2_responses.sav"), f2labels)]

    # per-instrument zip + a combined bundle
    combined = os.path.join(a.out_dir, "uhc-year2-cases-spss.zip")
    with zipfile.ZipFile(combined, "w", zipfile.ZIP_DEFLATED) as cz:
        for inst, made in manifest["instruments"].items():
            if not made:
                continue
            iz = os.path.join(a.out_dir, "%s-cases-spss.zip" % inst)
            with zipfile.ZipFile(iz, "w", zipfile.ZIP_DEFLATED) as z:
                for e in made:
                    p = os.path.join(a.out_dir, e["file"])
                    z.write(p, e["file"])
                    cz.write(p, e["file"])
    with open(os.path.join(a.out_dir, "spss-manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1)

    print("SPSS export -> %s" % a.out_dir)
    for inst, made in manifest["instruments"].items():
        rows = made[0]["rows"] if made else 0
        print("  %-4s %2d file(s), %d cases: %s"
              % (inst, len(made), rows, ", ".join(e["file"] for e in made)))


if __name__ == "__main__":
    main()

# ---------------------------------------------------------------------------
# Regenerating f2-item-labels.json (only when the F2 questionnaire changes):
#   cd deliverables/F2/PWA/app && cat > /tmp/d.mjs <<'JS'
#   import { sections } from './src/generated/items.ts';
#   const out={}; const walk=(xs)=>{for(const it of xs??[]){ if(it.id&&!(it.id in out))
#     out[it.id]={label:(it.label?.en??'').replace(/\s+/g,' ').trim(),type:it.type??''};
#     if(it.subFields)walk(it.subFields); if(it.items)walk(it.items);}};
#   for(const s of sections)walk(s.items); process.stdout.write(JSON.stringify(out,null,1));
#   JS
#   npx tsx /tmp/d.mjs > ../../../CSWeb/f2-item-labels.json
