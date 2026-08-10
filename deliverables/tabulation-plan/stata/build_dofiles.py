#!/usr/bin/env python3
"""build_dofiles.py — GENERATOR for the UHC Y2 Stata 12 tabulation do-file skeletons.

GENERATOR-FIRST RULE: never hand-edit the emitted .do files. Change this script
(or tabulation-plan.csv upstream) and re-run:

    PYTHONIOENCODING=utf-8 python build_dofiles.py

Reads ../tabulation-plan.csv (197 rows) and emits, into this stata/ folder:
    run.do          master runner (globals, log, do-chain)
    00_import.do    insheet the harmonization-ETL CSVs -> .dta
    01_svyset.do    per-instrument SSRCS Annex-A survey designs
    10_annex1.do    Annex 1 (F1 facility)   — 1 block per table
    20_annex2.do    Annex 2 (F3 patient)    — 1 block per table
    30_annex3.do    Annex 3 (F4 household)  — 1 block per table
    40_annex4.do    Annex 4 (F2 HCW)        — 1 block per table

Stata 12 hard rules baked in: version 12 header everywhere; insheet (never the
Stata 13+ delimited importer); tabout for table export (never putexcel /
collect/etable); svy: prefix; log using ..., text replace.
"""

import csv
import re
import textwrap
from pathlib import Path

HERE = Path(__file__).resolve().parent
CSV_PATH = HERE.parent / "tabulation-plan.csv"

# ---------------------------------------------------------------- sanitation
# Stata 12 is not Unicode; keep emitted files pure ASCII.
SANITIZE = {
    "’": "'", "‘": "'", "“": '"', "”": '"',
    "×": "x", "–": "-", "—": "-", "…": "...",
    "₱": "PHP ", "ñ": "n", "Ñ": "N", " ": " ",
    "≥": ">=", "≤": "<=",
}


def ascii_clean(s):
    for k, v in SANITIZE.items():
        s = s.replace(k, v)
    return s.encode("ascii", "replace").decode("ascii")


def wrap_comment(text, prefix="* ", width=90, first_prefix=None):
    """Wrap text at ~width cols as Stata comment lines."""
    text = ascii_clean(" ".join(text.split()))
    if not text:
        return []
    fp = first_prefix if first_prefix is not None else prefix
    lines = textwrap.wrap(text, width=width - len(prefix),
                          initial_indent="", subsequent_indent="")
    out = []
    for i, ln in enumerate(lines):
        out.append((fp if i == 0 else prefix) + ln)
    return out


# ---------------------------------------------------------------- CSV model
def load_rows():
    with open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def clean_varlist(source_variables):
    """'Q66_X (checkbox multi),Q67_Y' -> ['q66_x', 'q67_y'] (lowercased to
    match the ETL CSV headers, which insheet preserves)."""
    out = []
    for part in source_variables.split(","):
        name = re.sub(r"\(.*?\)", "", part).strip().lower()
        if name:
            out.append(name)
    return out


# breakdown-dimension -> (stata var, needs f_type join note)
DIM_MAP = [
    ("facility type", "f_type"),
    ("facility level", "f_type"),
    ("province", "province_huc"),
    ("in/out", "patient_type"),
]


def parse_breakdown(breakdown):
    """Return (bygroup_var or None, [comment lines about extra/unmapped dims])."""
    b = breakdown.strip().lower()
    comments = []
    if not b or b == "none stated":
        return None, comments
    dims = [d.strip() for d in re.split(r"×|\bx\b(?=\s)", breakdown) if d.strip()]
    mapped, unmapped = [], []
    for dim in dims:
        dl = dim.lower()
        hit = None
        for key, var in DIM_MAP:
            if key in dl:
                hit = var
                break
        if hit and hit not in mapped:
            mapped.append(hit)
        elif not hit:
            unmapped.append(dim)
    bygroup = mapped[0] if mapped else None
    if bygroup == "f_type":
        comments.append("* f_type comes from the facility master-list join (see plan notes)")
    if len(mapped) > 1:
        comments.append("* TODO extra breakdown dim(s) mapped but not in this two-way tab: "
                        + ", ".join(mapped[1:]) + " (run as subpop or second pass)")
    if unmapped:
        comments += wrap_comment(
            "TODO breakdown dim(s) with no standard bygroup var yet: "
            + "; ".join(ascii_clean(u.replace("by ", "", 1)) for u in unmapped),
            prefix="*   ", first_prefix="* ")
    return bygroup, comments


# ---------------------------------------------------------------- synthesis
PERCENT_TYPES = ("percent", "percent distribution")
MEAN_TYPES = ("average", "mean", "score", "summary", "descriptive stats")


def xls_for(annex):
    return '"$OUT_DIR/annex%s_tables.xls"' % annex


def percent_cmds(varlist, bygroup, annex):
    """svy: tab + tabout lines for percent/percent-distribution rows.

    Every runnable command is `capture noisily`-guarded: with the ETL's variable
    extraction still partial, a missing variable logs its error (visible as r()
    codes in the log) and the run CONTINUES instead of aborting the annex.
    """
    xls = xls_for(annex)
    lines = []
    if len(varlist) > 1:
        lines.append("capture noisily {")
        lines.append("foreach v in " + " ".join(varlist) + " {")
        if bygroup:
            lines.append("    svy: tab `v' %s, col percent" % bygroup)
            lines.append("    tabout `v' %s using %s, append svy percent cells(col) f(1)"
                         % (bygroup, xls))
        else:
            lines.append("    svy: tab `v', percent")
            lines.append("    tabout `v' using %s, append svy oneway percent cells(cell) f(1)"
                         % xls)
        lines.append("}")
        lines.append("}")
    elif len(varlist) == 1:
        v = varlist[0]
        if bygroup:
            lines.append("capture noisily svy: tab %s %s, col percent" % (v, bygroup))
            lines.append("capture noisily tabout %s %s using %s, append svy percent cells(col) f(1)"
                         % (v, bygroup, xls))
        else:
            lines.append("capture noisily svy: tab %s, percent" % v)
            lines.append("capture noisily tabout %s using %s, append svy oneway percent cells(cell) f(1)"
                         % (v, xls))
    return lines


def mean_cmds(varlist, bygroup, annex, stat_type):
    """svy: mean + tabout-sum lines for average/score/summary/descriptive rows."""
    xls = xls_for(annex)
    lines = []
    if stat_type != "average":
        lines.append("* stat_type '%s': skeleton uses svy: mean over the component items; "
                     "composite recipe TBD" % stat_type)
    if not varlist:
        return lines
    vl = " ".join(varlist)
    if bygroup:
        lines.append("capture noisily svy: mean %s, over(%s)" % (vl, bygroup))
        cells = " ".join("mean %s" % v for v in varlist)
        lines.append("capture noisily tabout %s using %s, append svy sum cells(%s) f(2)"
                     % (bygroup, xls, cells))
    else:
        lines.append("capture noisily svy: mean %s" % vl)
        lines.append("* no breakdown var: tabout sum needs a row variable - "
                     "read the svy: mean results from the log")
    return lines


def checkbox_stub(varlist):
    lines = ["* CHECKBOX: split alpha multi-code field into dummies before tab:"]
    for v in varlist:
        lines.append("* gen byte %s_XX = strpos(%s, \"XX\") > 0  // one per code" % (v, v))
    return lines


def roster_stub():
    return [
        "* ROSTER: this table reads the F3 pay/expenditure roster extract, a separate",
        "* long-format dataset (one row per bill line / pay source).",
        "* use \"$DATA_DIR/f3_roster.dta\", clear   // TODO - roster extract not in ETL yet",
        "* ... (tab/collapse the roster, then:  use \"$DATA_DIR/f3.dta\", clear )",
    ]


def build_block(row):
    """One generated block per tabulation-plan row."""
    no = row["no"]
    desc = row["description"]
    status = row["mapping_status"].strip().lower()
    stat_type = row["stat_type"].strip().lower()
    notes = row["notes"].strip()
    annex = row["annex"].strip()
    sv = row["source_variables"]
    varlist = clean_varlist(sv)

    blob = (sv + " " + notes).lower()
    is_checkbox = "checkbox" in blob
    is_roster = "(roster)" in blob
    is_derived = "derived" in notes.lower()

    lines = []
    head = "*----- Table %s - %s -----" % (no, desc)
    lines += wrap_comment(head, prefix="*       ", width=96, first_prefix="")
    lines += wrap_comment(
        "universe: %s | breakdown: %s | status: %s"
        % (row["universe"], row["breakdown"], status),
        prefix="*   ", width=100, first_prefix="* ")

    if status == "gap":
        lines += wrap_comment("GAP - no source in instrument: " + (notes or "(no notes)"),
                              prefix="*   ", first_prefix="* ")
        return lines

    comment_out = False  # whether the runnable commands get commented

    if status == "partial":
        lines += wrap_comment("PARTIAL: " + (notes or "(no notes)"),
                              prefix="*   ", first_prefix="* ")
        comment_out = True

    if is_derived:
        lines += wrap_comment("DERIVED: " + notes, prefix="*   ", first_prefix="* ")
        lines.append("* gen <derived_var> = ...   // TODO derive per recipe above, then tab it")
        comment_out = True

    if status == "mapped" and not is_derived and not is_checkbox and not is_roster and notes:
        lines += wrap_comment("note: " + notes, prefix="*   ", first_prefix="* ")

    if is_roster:
        if status == "mapped" and not is_derived and notes:
            lines += wrap_comment("note: " + notes, prefix="*   ", first_prefix="* ")
        lines += roster_stub()
        comment_out = True  # roster extract not in ETL yet

    if is_checkbox:
        if status == "mapped" and not is_derived and not is_roster and notes:
            lines += wrap_comment("note: " + notes, prefix="*   ", first_prefix="* ")
        lines += checkbox_stub(varlist)
        comment_out = True  # tab runs on the (not-yet-generated) dummies

    bygroup, by_comments = parse_breakdown(row["breakdown"])
    lines += by_comments

    if stat_type in PERCENT_TYPES:
        cmds = percent_cmds(varlist, bygroup, annex)
    elif stat_type in MEAN_TYPES:
        cmds = mean_cmds(varlist, bygroup, annex, stat_type)
    else:  # unknown stat_type - be loud, default to percent skeleton
        cmds = ["* TODO unrecognized stat_type '%s'" % stat_type]
        cmds += percent_cmds(varlist, bygroup, annex)

    if comment_out:
        cmds = [("* " + c) if not c.lstrip().startswith("*") else c for c in cmds]
    lines += cmds
    return lines


# ---------------------------------------------------------------- do-files
GEN_BANNER = "* GENERATED by build_dofiles.py - do NOT hand-edit; edit the generator and re-run."

RUN_DO = """\
* run.do - UHC Y2 tabulation plan, master runner (Stata 12)
%(banner)s
* Batch run:  "C:\\Users\\analy\\Downloads\\Stata 12\\StataSE.exe" /e do run.do
version 12
clear all
set more off
set linesize 120
capture log close

* ---------------- globals ----------------
global DATA_DIR "data"
global OUT_DIR  "out"
* NOWEIGHT toggle: 1 = run UNWEIGHTED (weights wf arrive post-collection);
*                  0 = use the real svyset designs with [pweight=wf].
global NOWEIGHT 1

capture mkdir "$DATA_DIR"
capture mkdir "$OUT_DIR"
capture mkdir "logs"

log using "logs/run.log", text replace

do 00_import.do
do 01_svyset.do
do 10_annex1.do
do 20_annex2.do
do 30_annex3.do
do 40_annex4.do

log close
"""

IMPORT_DO = """\
* 00_import.do - bring the harmonization-ETL CSVs into Stata 12 .dta files
%(banner)s
* WHY insheet: the ETL (transform.py) does not emit .dta yet (transform.py section 0.3
* TODO); and Stata 13+'s newer delimited importer does NOT exist in Stata 12,
* so -insheet- is the Stata-12-native path.
version 12

* ================= EDIT ME =================
* Point ETL_DIR at the harmonization ETL output snapshot you want to tabulate:
*   deliverables/data-harmonization/etl/out/<date>
global ETL_DIR "../../data-harmonization/etl/out/2026-06-12"
* ===========================================

insheet using "$ETL_DIR/f1_clean.csv", comma names case clear
save "$DATA_DIR/f1.dta", replace

insheet using "$ETL_DIR/f3_clean.csv", comma names case clear
save "$DATA_DIR/f3.dta", replace

insheet using "$ETL_DIR/f4_clean.csv", comma names case clear
save "$DATA_DIR/f4.dta", replace

insheet using "$ETL_DIR/f4_roster_clean.csv", comma names case clear
save "$DATA_DIR/f4_roster.dta", replace

insheet using "$ETL_DIR/shared_dimensions.csv", comma names case clear
save "$DATA_DIR/shared_dimensions.dta", replace

* ---- TODO: not in the ETL yet - stubbed with capture guards ----
* F2 (HCW census) clean extract does not exist in the ETL yet:
capture confirm file "$ETL_DIR/f2_clean.csv"
if _rc == 0 {
    insheet using "$ETL_DIR/f2_clean.csv", comma names case clear
    save "$DATA_DIR/f2.dta", replace
}
else {
    display as error "TODO: f2_clean.csv not in ETL output yet - Annex 4 will be skipped"
}

* F3 pay/expenditure roster extracts do not exist in the ETL yet:
capture confirm file "$ETL_DIR/f3_roster_clean.csv"
if _rc == 0 {
    insheet using "$ETL_DIR/f3_roster_clean.csv", comma names case clear
    save "$DATA_DIR/f3_roster.dta", replace
}
else {
    display as error "TODO: f3 roster extract not in ETL output yet - roster tables stay stubbed"
}
"""

SVYSET_DO = """\
* 01_svyset.do - per-instrument survey designs (SSRCS Annex A)
%(banner)s
version 12

* ============================ LOUD TODO =====================================
* WEIGHTS DO NOT EXIST YET. Sampling weights (wf) are computed POST-COLLECTION
* from the realized sample. Until then run UNWEIGHTED via the NOWEIGHT toggle
* in run.do (global NOWEIGHT 1), which svysets each file as SRS (_n) so every
* svy: command still runs. When wf lands: merge it onto each .dta, construct
* the strata/fpc variables flagged below, set NOWEIGHT 0, and re-run.
* ============================================================================

* ---------------- F1 - facility survey ----------------
* SSRCS Annex A design: STRATIFIED SINGLE-STAGE sample of facilities;
* strata = facility-type x province; with finite-population correction.
use "$DATA_DIR/f1.dta", clear
if "$NOWEIGHT" == "1" {
    svyset _n
}
else {
    * TODO construct before use:  egen strata_f1 = group(f_type province_huc)
    * TODO construct before use:  fpc_f1 = facilities in stratum (master list)
    svyset facility_id [pweight=wf], strata(strata_f1) fpc(fpc_f1)
}
save "$DATA_DIR/f1.dta", replace

* ---------------- F3 - patient exit survey ----------------
* SSRCS Annex A design: TWO-STAGE; PSU = facility, patients sampled within.
use "$DATA_DIR/f3.dta", clear
if "$NOWEIGHT" == "1" {
    svyset _n
}
else {
    * TODO construct before use:  egen strata_f3 = group(f_type province_huc)
    svyset facility_id [pweight=wf], strata(strata_f3) || _n
}
save "$DATA_DIR/f3.dta", replace

* ---------------- F4 - household survey ----------------
* SSRCS Annex A design: TWO-STAGE; PSU = barangay, households sampled within.
use "$DATA_DIR/f4.dta", clear
if "$NOWEIGHT" == "1" {
    svyset _n
}
else {
    * TODO construct before use: barangay_psu (PSGC barangay code) + strata_f4
    svyset barangay_psu [pweight=wf], strata(strata_f4) || _n
}
save "$DATA_DIR/f4.dta", replace

* ---------------- F2 - health-care worker survey ----------------
* SSRCS Annex A design: CENSUS of HCWs within sampled facilities - no
* second-phase sampling, so self-weighting (wf=1); svyset as SRS.
capture confirm file "$DATA_DIR/f2.dta"
if _rc == 0 {
    use "$DATA_DIR/f2.dta", clear
    svyset _n
    save "$DATA_DIR/f2.dta", replace
}
else {
    display as error "f2.dta missing (ETL f2_clean.csv TODO) - skipping F2 svyset"
}
"""

ANNEX_META = {
    "1": ("10_annex1.do", "f1", "Annex 1 - F1 facility survey"),
    "2": ("20_annex2.do", "f3", "Annex 2 - F3 patient exit survey"),
    "3": ("30_annex3.do", "f4", "Annex 3 - F4 household survey"),
    "4": ("40_annex4.do", "f2", "Annex 4 - F2 health-care worker survey"),
}


def annex_header(annex, fname, dta, title):
    lines = [
        "* %s - %s table skeletons (Stata 12)" % (fname, title),
        GEN_BANNER,
        "version 12",
        "",
        "capture erase %s" % xls_for(annex),  # tabout blocks all use append
    ]
    if dta == "f2":
        lines += [
            "capture confirm file \"$DATA_DIR/f2.dta\"",
            "if _rc {",
            "    display as error \"f2.dta missing (ETL f2_clean.csv TODO) - skipping Annex 4\"",
            "    exit",
            "}",
        ]
    lines += ["use \"$DATA_DIR/%s.dta\", clear" % dta, ""]
    return lines


def main():
    rows = load_rows()
    print("rows read: %d" % len(rows))

    files = {
        "run.do": RUN_DO % {"banner": GEN_BANNER},
        "00_import.do": IMPORT_DO % {"banner": GEN_BANNER},
        "01_svyset.do": SVYSET_DO % {"banner": GEN_BANNER},
    }

    counts = {}
    for annex in ("1", "2", "3", "4"):
        fname, dta, title = ANNEX_META[annex]
        arows = [r for r in rows if r["annex"].strip() == annex]
        counts[fname] = len(arows)
        lines = annex_header(annex, fname, dta, title)
        for r in arows:
            lines += build_block(r)
            lines.append("")
        files[fname] = "\n".join(lines) + "\n"

    for fname, content in files.items():
        content = ascii_clean(content)
        (HERE / fname).write_text(content, encoding="ascii", newline="\r\n")
        print("emitted %-14s (%d lines)" % (fname, content.count("\n") + 1))

    for fname, n in sorted(counts.items()):
        print("  %s: %d table blocks" % (fname, n))


if __name__ == "__main__":
    main()
