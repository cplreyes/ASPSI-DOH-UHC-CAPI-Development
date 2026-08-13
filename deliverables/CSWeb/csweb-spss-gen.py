#!/usr/bin/env python3
r"""Generate SPSS (.sav) + Stata (.dta) + R (.rds) case exports for ALL FOUR
instruments from the Responses Data Room CSVs + the questionnaire codebooks.
(Filename kept as csweb-spss-gen.py for cron/log continuity — since 2026-07-21
it is the stats-package generator for all three formats.)

Why a separate generator (not just the CSVs): the data-room CSVs carry RAW
codes (1/2, not Male/Female). The stats formats' whole value over CSV is the
embedded metadata — variable labels (the question text) and value labels
(1="Male"). This script attaches both, so an analyst opens a .sav/.dta and
every variable/value is self-describing, no codebook lookup.

Per format:
  SPSS .sav   variable labels + value labels embedded (as before).
  Stata .dta  same labels embedded; variable names sanitized to Stata's rules
              (<=32 chars, [A-Za-z_][A-Za-z0-9_]*) with any renames listed in
              the zip's README.txt; variable labels capped at Stata's 80 chars.
              Written as DTA 118 (Stata 14+, UTF-8).
  R .rds      typed data frames (readRDS()), values stay the RAW codes — R has
              no standard embedded-label slot pyreadr can write, so labels ride
              along as <inst>_codebook.csv (variable + value labels, one file
              per instrument, included in the R zips). Deliberately NOT factor-
              converted: partially-labeled numerics (amounts with 98=DK style
              specials) would corrupt to NA. Nullable ints become R numeric.

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
Output = one .sav + .dta + .rds per CSV + a codebook CSV per instrument +
per-instrument-per-format zips + combined per-format zips + one manifest
(spss-manifest.json — name kept; it now carries "zips"/"combined_zips" per
format, plus the legacy "zip"/"combined" SPSS keys).

Decoupled from MySQL on purpose: it reads the CSVs the responses generator
already writes, so it runs anywhere those CSVs + the DCF codebooks land.

ON-BOX (the live extract on the dashboard/data room, added 2026-07-20):
runs from cron on the odd minutes, sharing the responses-gen lock file so it
never reads a CSV mid-rewrite. Codebooks live flat in /opt/spss-meta (3 .dcf +
f2-item-labels.json — re-scp after any dictionary redeploy). Deps live in a
venv (Ubuntu 24.04 blocks system pip): /opt/venvs/spss.
  1-59/2 * * * * flock -n /tmp/csweb-responses.lock /opt/venvs/spss/bin/python \
    /opt/csweb-spss-gen.py --meta-dir /opt/spss-meta >> /var/log/csweb-spss.log 2>&1
Same .htaccess guard as the responses generator: refuses to write into the
live dir unless the dir carries its own auth stanza.

OFF-BOX (ad-hoc rebuild, e.g. a one-off cut for ASPSI):
  # pull the latest CSVs off the box (credential-free, read-only)
  scp -i ~/.ssh/aspsi-csweb 'root@207.148.65.115:/opt/app/lamp/www/docs/data/*.csv' <data-dir>/
  python deliverables/CSWeb/csweb-spss-gen.py --data-dir <data-dir> --out-dir <out>

Requires: pyreadstat, pyreadr, pandas (pip). Built 2026-07-20 ("the file
Marriz needed"); Stata + R formats added 2026-07-21.
"""
import argparse, csv, io, json, os, re, sys, zipfile, datetime
import pandas as pd
import pyreadstat
import pyreadr

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))               # deliverables/
CSPRO = os.path.join(REPO, "CSPro")
DCF = {"f1": os.path.join(CSPRO, "F1", "FacilityHeadSurvey.dcf"),
       "f3": os.path.join(CSPRO, "F3", "PatientSurvey.dcf"),
       "f4": os.path.join(CSPRO, "F4", "HouseholdSurvey.dcf")}
DCF_NAME = {k: os.path.basename(v) for k, v in DCF.items()}    # flat --meta-dir layout
LIVE_DATA = "/opt/app/lamp/www/docs/data"
NAMES = {"f1": "F1 - Facility Head", "f3": "F3 - Patient",
         "f4": "F4 - Household", "f2": "F2 - Healthcare Worker (PWA)"}
VARLABEL_MAX = 256      # SPSS variable-label byte cap
VALLABEL_MAX = 120      # SPSS value-label byte cap
STATA_NAME_MAX = 32     # Stata variable-name cap
STATA_VARLABEL_MAX = 80 # Stata variable-label cap
# format -> (made-entry key, combined-zip name)
FORMATS = (("spss", "file"), ("stata", "dta"), ("r", "rds"))
COMBINED = {"spss": "uhc-year2-cases-spss.zip",
            "stata": "uhc-year2-cases-stata.zip",
            "r": "uhc-year2-cases-r.zip"}

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


def prep_frame(csv_path, itemmap, extra_labels=None):
    """One wide/roster CSV -> (df, header, var_labels{col:label}, val_labels{col:{code:label}})."""
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
    return pd.DataFrame(data, columns=header), header, var_labels, val_labels


def prep_f2(csv_path, f2labels):
    """Explode f2 values_json into per-question columns -> (df, header, var_labels)."""
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
    var_labels = {}
    for c in header_out:
        lab = base_lab.get(c) or (f2labels.get(c, {}).get("label") if c in f2labels else "") or c
        var_labels[c] = lab[:VARLABEL_MAX]
    return df, header_out, var_labels


def stata_names(header):
    """Sanitize columns to legal, unique Stata names; return (names, renames)."""
    names, used, renamed = [], set(), []
    for c in header:
        n = re.sub(r"[^A-Za-z0-9_]", "_", c)
        if not re.match(r"[A-Za-z_]", n):
            n = "v_" + n
        n = n[:STATA_NAME_MAX]
        base, i = n, 2
        while n.lower() in used:
            suf = "_%d" % i
            n = base[:STATA_NAME_MAX - len(suf)] + suf
            i += 1
        used.add(n.lower())
        names.append(n)
        if n != c:
            renamed.append((c, n))
    return names, renamed


def write_formats(df, header, var_labels, val_labels, out_dir, base, title):
    """Write base.{sav,dta,rds}; return (manifest entry, stata renames)."""
    pyreadstat.write_sav(
        df, os.path.join(out_dir, base + ".sav"), file_label=title[:60],
        column_labels=[var_labels[c] for c in header],
        variable_value_labels=val_labels)
    names, renamed = stata_names(header)
    sdf = df.copy()
    sdf.columns = names
    colmap = dict(zip(header, names))
    pyreadstat.write_dta(
        sdf, os.path.join(out_dir, base + ".dta"), file_label=title[:80],
        column_labels=[var_labels[c][:STATA_VARLABEL_MAX] for c in header],
        variable_value_labels={colmap[c]: v for c, v in val_labels.items()})
    rdf = df.copy()
    for c in rdf.columns:                     # pyreadr can't take nullable Int64
        if str(rdf[c].dtype) == "Int64":
            rdf[c] = rdf[c].astype("float64")
    pyreadr.write_rds(os.path.join(out_dir, base + ".rds"), rdf, compress="gzip")
    return ({"file": base + ".sav", "dta": base + ".dta", "rds": base + ".rds",
             "rows": len(df), "cols": len(header)}, renamed)


def cb_add(cb, header, var_labels, val_labels):
    for c in header:
        if c not in cb:
            cb[c] = (var_labels.get(c, c), val_labels.get(c) or {})


def write_codebook(cb, path):
    """variable/value labels as CSV — the R zips' label companion."""
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["variable", "variable_label", "value", "value_label"])
        for c, (lab, vl) in cb.items():
            w.writerow([c, lab, "", ""])
            for code in sorted(vl):
                w.writerow([c, "", code, vl[code]])


def readme_text(inst, fmt, cases, stamp, renames, nl):
    head = [NAMES[inst],
            "%s export generated %s UTC from the Responses Data Room CSVs."
            % ({"spss": "SPSS", "stata": "Stata", "r": "R"}[fmt], stamp),
            "Cases: %d" % cases, ""]
    if fmt == "spss":
        body = ["One wide .sav (a row per case) plus one .sav per roster record (a row per",
                "case x occurrence). Variable labels (question text) and value labels",
                "(code -> answer) are embedded from the questionnaire codebook — no lookup",
                "needed. questionnaire_number is a 12-digit string."]
    elif fmt == "stata":
        body = ["One wide .dta (a row per case) plus one .dta per roster record (a row per",
                "case x occurrence). Variable labels and value labels are embedded from the",
                "questionnaire codebook. Format: DTA 118 (Stata 14 or newer, UTF-8).",
                "questionnaire_number is a 12-digit string."]
        if renames:
            body += ["",
                     "Variable names beyond Stata's 32-char limit were shortened:"]
            body += ["  %s -> %s" % (o, n) for o, n in renames]
    else:
        body = ["One wide .rds (a row per case) plus one .rds per roster record (a row per",
                "case x occurrence); open with readRDS(). Values are the RAW stored codes",
                "typed numeric/character — R has no standard embedded-label slot, so the",
                "variable + value labels are in %s_codebook.csv (in this zip)." % inst,
                "Deliberately not factor-converted: partially-labeled numerics (amounts",
                "with 98=Don't-know style specials) would corrupt to NA.",
                "questionnaire_number is a 12-digit string."]
    return nl.join(head + body + [""])


def main():
    ap = argparse.ArgumentParser(description="Generate SPSS/Stata/R case exports for all instruments.")
    ap.add_argument("--data-dir", default=LIVE_DATA, help="dir holding the data-room CSVs (default: %(default)s)")
    ap.add_argument("--out-dir", default=LIVE_DATA, help="output dir for the export files + zips (default: %(default)s)")
    ap.add_argument("--meta-dir", default=None,
                    help="flat dir with the 3 .dcf codebooks + f2-item-labels.json "
                         "(on-box: /opt/spss-meta); default: the repo checkout layout")
    ap.add_argument("--f2-labels", default=None, help="override the f2-item-labels.json path")
    a = ap.parse_args()
    dcf = ({k: os.path.join(a.meta_dir, DCF_NAME[k]) for k in DCF} if a.meta_dir else DCF)
    f2p = a.f2_labels or os.path.join(a.meta_dir or HERE, "f2-item-labels.json")
    live = os.path.abspath(a.out_dir) == os.path.abspath(LIVE_DATA)
    os.makedirs(a.out_dir, exist_ok=True)
    if live and not os.path.exists(os.path.join(a.out_dir, ".htaccess")):
        sys.exit("REFUSING to write: %s/.htaccess is missing — the parent /docs/.htaccess only "
                 "gates three filenames, so this dir would serve every response PUBLICLY. "
                 "Restore the auth stanza first (see deliverables/CSWeb docs)." % a.out_dir)
    f2labels = json.load(open(f2p, encoding="utf-8")) if os.path.exists(f2p) else {}
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M")
    manifest = {"generated": stamp + " UTC", "combined": COMBINED["spss"],
                "combined_zips": dict(COMBINED), "instruments": {}}
    renames_by_inst = {}

    # one instrument failing (stale codebook, torn CSV) must not sink the others
    for inst in ("f1", "f3", "f4"):
        made, renames, cb = [], [], {}
        try:
            itemmap = parse_dcf(dcf[inst])
            wide = os.path.join(a.data_dir, "%s_responses.csv" % inst)
            srcs = ([wide] if os.path.exists(wide) else [])
            srcs += [os.path.join(a.data_dir, fn) for fn in sorted(os.listdir(a.data_dir))
                     if fn.startswith("%s_roster_" % inst) and fn.endswith(".csv")]
            for src in srcs:
                df, header, vlab, vall = prep_frame(src, itemmap)
                e, ren = write_formats(df, header, vlab, vall, a.out_dir,
                                       os.path.basename(src)[:-4], NAMES[inst])
                made.append(e)
                renames += ren
                cb_add(cb, header, vlab, vall)
            if made:
                write_codebook(cb, os.path.join(a.out_dir, "%s_codebook.csv" % inst))
        except Exception as e:
            made = []
            print("WARN: %s failed: %s" % (inst, str(e)[:300]))
        manifest["instruments"][inst] = {"files": made}
        renames_by_inst[inst] = list(dict.fromkeys(renames))

    f2made = []
    f2csv = os.path.join(a.data_dir, "f2_responses.csv")
    if os.path.exists(f2csv):
        try:
            df, header, vlab = prep_f2(f2csv, f2labels)
            e, ren = write_formats(df, header, vlab, {}, a.out_dir,
                                   "f2_responses", NAMES["f2"])
            f2made = [e]
            cb = {}
            cb_add(cb, header, vlab, {})
            write_codebook(cb, os.path.join(a.out_dir, "f2_codebook.csv"))
            renames_by_inst["f2"] = list(dict.fromkeys(ren))
        except Exception as e:
            print("WARN: f2 failed: %s" % str(e)[:300])
    manifest["instruments"]["f2"] = {"files": f2made}
    renames_by_inst.setdefault("f2", [])

    # zips: per instrument per format + a combined bundle per format; zip/cases
    # mirror manifest.json so the dashboard Downloads band + data-room index can
    # label buttons without parsing files
    NL = chr(10)
    for inst, m in manifest["instruments"].items():
        if m["files"]:
            m["cases"] = m["files"][0]["rows"]
            m["zip"] = "%s-cases-spss.zip" % inst                    # legacy key
            m["zips"] = {fmt: "%s-cases-%s.zip" % (inst, fmt) for fmt, _ in FORMATS}
    for fmt, key in FORMATS:
        with zipfile.ZipFile(os.path.join(a.out_dir, COMBINED[fmt]), "w",
                             zipfile.ZIP_DEFLATED) as cz:
            for inst, m in manifest["instruments"].items():
                if not m["files"]:
                    continue
                cbname = "%s_codebook.csv" % inst
                with zipfile.ZipFile(os.path.join(a.out_dir, m["zips"][fmt]), "w",
                                     zipfile.ZIP_DEFLATED) as z:
                    z.writestr("README.txt", readme_text(inst, fmt, m["cases"], stamp,
                                                         renames_by_inst[inst], NL))
                    if fmt == "r" and os.path.exists(os.path.join(a.out_dir, cbname)):
                        z.write(os.path.join(a.out_dir, cbname), cbname)
                        cz.write(os.path.join(a.out_dir, cbname), cbname)
                    for e in m["files"]:
                        p = os.path.join(a.out_dir, e[key])
                        z.write(p, e[key])
                        cz.write(p, e[key])
    with open(os.path.join(a.out_dir, "spss-manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1)

    print("SPSS/Stata/R export -> %s" % a.out_dir)
    for inst, m in manifest["instruments"].items():
        made = m["files"]
        print("  %-4s %2d file(s) x 3 formats, %s cases: %s"
              % (inst, len(made), m.get("cases", 0),
                 ", ".join(e["file"] for e in made) or "FAIL"))


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
