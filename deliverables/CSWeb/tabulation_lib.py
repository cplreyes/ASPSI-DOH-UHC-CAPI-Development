# -*- coding: utf-8 -*-
"""tabulation_lib.py — pure, testable helpers for the UHC Year 2 tabulation
preview engine (Carl, 2026-07-28).

The generator (csweb-tabulations-gen.py) is the I/O + packaging shell; every
data decision lives here so it can be unit-tested on synthetic frames with no
box, no MySQL, no fixtures. Design spec:
docs/superpowers/specs/2026-07-28-tabulations-preview-engine-design.md

Two lanes:
  - Lane 1 (plan-driven): tabulate() a single categorical source variable,
    crossed by its committed breakdown, with codes labeled as words.
  - Lane 2 (curated): multi_tally() for checkbox multi-code fields; explode_f2()
    for the F2 values_json items.

Everything here is UNWEIGHTED and phase-scoped by the caller. Nothing here
claims a committed weighted number.
"""
import csv
import json
import os
import re

import pandas as pd

NO_ANSWER = "(no answer)"

# The DCF value-label parser is shared with csweb-spss-gen.py. That module's
# filename is hyphenated (not importable), so the two small functions are copied
# verbatim; keep them in sync if the SPSS gen's parser changes.

DCF_FILES = {"f1": "FacilityHeadSurvey.dcf",
             "f3": "PatientSurvey.dcf",
             "f4": "HouseholdSurvey.dcf"}


def _en(o):
    """Best English label from a CSPro labels[] list."""
    labs = o.get("labels") or []
    for l in labs:
        if l.get("language") == "EN" and l.get("text"):
            return l["text"]
    for l in labs:
        if l.get("text"):
            return l["text"]
    return ""


def parse_dcf(path):
    """lower(item_name) -> {label, ctype, vlabels{code_str: label}}."""
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
                            if "value" in p and "from" not in p:   # discrete codes only
                                vlabels[str(p["value"]).strip()] = lab
                out[it["name"].lower()] = {"label": _en(it),
                                           "ctype": it.get("contentType"),
                                           "vlabels": vlabels}
    return out


def load_dcf(meta_dir):
    """{inst: itemmap} for the three CAPI instruments found in meta_dir."""
    out = {}
    for inst, fn in DCF_FILES.items():
        p = os.path.join(meta_dir, fn)
        if os.path.exists(p):
            out[inst] = parse_dcf(p)
    return out


def load_value_labels(meta_dir):
    """{inst: {col_lower: {code_str: label}}}."""
    return {inst: {col: m["vlabels"] for col, m in itemmap.items() if m["vlabels"]}
            for inst, itemmap in load_dcf(meta_dir).items()}


def load_var_labels(meta_dir):
    """{inst: {col_lower: item_label}}."""
    return {inst: {col: m["label"] for col, m in itemmap.items()}
            for inst, itemmap in load_dcf(meta_dir).items()}


# ---------------------------------------------------------------- classify ----

def first_var(sv):
    """First variable token of a plan source_variables cell, lowercased."""
    s = (sv or "").split("(")[0]
    m = re.match(r"\s*([A-Za-z0-9_]+)", s)
    return m.group(1).lower() if m else ""


def is_multi(sv):
    """A checkbox / multi-code source field."""
    s = (sv or "").lower()
    return "checkbox" in s or "multi" in s


def classify_rows(plan, headers_by_inst):
    """Classify every plan row.

    plan: list of dicts from tabulation-plan.csv (DictReader).
    headers_by_inst: {inst: set(lower column names)} from the responses CSVs.

    Returns list of {no, annex, inst, description, breakdown, universe,
    source_var, klass, col} where klass is one of previewable | multi |
    partial | gap | f2. `col` is the resolved lowercase CSV column for
    previewable AND multi rows (Lane 2 needs it), else None.
    """
    out = []
    for r in plan:
        inst = r["instrument"].strip().lower()
        sv = r["source_variables"].strip()
        ms = r["mapping_status"].strip().lower()
        col = first_var(sv)
        headers = headers_by_inst.get(inst, set())
        if inst == "f2":
            klass, keep = "f2", None
        elif is_multi(sv):
            klass, keep = "multi", (col if col in headers else None)
        elif ms == "gap" or not col:
            klass, keep = "gap", None
        elif ms == "mapped" and col in headers:
            klass, keep = "previewable", col
        else:
            klass, keep = "partial", None      # mapped-but-unresolved falls here too
        out.append({"no": r["no"].strip(), "annex": r["annex"].strip(), "inst": inst,
                    "description": r["description"].strip(),
                    "breakdown": r["breakdown"].strip().lower(),
                    "universe": r.get("universe", "").strip(),
                    "source_var": sv, "klass": klass, "col": keep})
    return out


# --------------------------------------------------------------- breakdown ----

def resolve_breakdown(inst, breakdown_text, headers):
    """(column_or_None, note_or_None) for a plan breakdown string.

    F3/F4 "by province" -> province_name. F1 "by facility type" -> ownership
    (fallback service level) as an explicitly-noted proxy. Anything else ->
    total-only.
    """
    b = (breakdown_text or "").lower()
    if "province" in b and "province_name" in headers:
        return "province_name", None
    if "facility type" in b or "type of facility" in b:
        for c in ("q7_ownership", "q8_service_level"):
            if c in headers:
                return c, ("proxy: tabulated by %s — the true facility-type split "
                           "(RHU / gov / private) is applied in the weighted lane" % c)
    return None, None


# ---------------------------------------------------------------- tabulate ----

def _lab(code, vlabels):
    if code is None:
        return NO_ANSWER
    s = str(code).strip()
    if s == "" or s.lower() == "nan":
        return NO_ANSWER
    return (vlabels or {}).get(s, s)


def tabulate(df, col, vlabels=None, breakdown_col=None, breakdown_vlabels=None):
    """Unweighted frequency of `col`, optionally within `breakdown_col`.

    Returns a list of {category, group, n, pct}; pct is the percent within the
    group (or overall when no breakdown). Blank/NaN -> "(no answer)". Category
    and group codes are label-applied, raw-code fallback.
    """
    if col not in df.columns:
        return []
    series = df[col].astype("object")
    cat = series.map(lambda v: _lab(v, vlabels))
    if breakdown_col and breakdown_col in df.columns:
        grp = df[breakdown_col].astype("object").map(lambda v: _lab(v, breakdown_vlabels))
        tab = pd.DataFrame({"group": grp, "category": cat})
        rows = []
        for g, sub in tab.groupby("group", sort=True):
            tot = len(sub)
            vc = sub["category"].value_counts()
            for c in vc.index:
                n = int(vc[c])
                rows.append({"category": c, "group": g, "n": n,
                             "pct": round(n / tot * 100, 1) if tot else 0.0})
        return rows
    vc = cat.value_counts()
    tot = int(vc.sum())
    return [{"category": c, "group": "", "n": int(vc[c]),
             "pct": round(int(vc[c]) / tot * 100, 1) if tot else 0.0}
            for c in vc.index]


# ------------------------------------------------------------- multi tally ----

def code_width(vlabels):
    """Fixed code width for a concatenated multi-code field: the (max) length of
    the value-set codes, defaulting to 2 when unknown."""
    if vlabels:
        widths = {len(str(k).strip()) for k in vlabels if str(k).strip()}
        if len(widths) == 1:
            return widths.pop()
        if widths:
            return max(widths)
    return 2


def _split_codes(cell, width):
    s = "" if cell is None else str(cell).strip()
    if s == "" or s.lower() == "nan":
        return []
    return [s[i:i + width] for i in range(0, len(s), width)]


def multi_tally(df, col, vlabels=None, width=None):
    """Multiple-response tally of a concatenated fixed-width multi-code field.

    Returns list of {category, n, pct_resp} for each option (n = respondents
    selecting it, pct_resp = % of responding respondents), plus a trailing
    {meta: 'respondents', n: <n_resp>} row. Percentages sum > 100 by design.
    """
    if col not in df.columns:
        return []
    w = width or code_width(vlabels)
    per_row, n_resp = [], 0
    for cell in df[col].tolist():
        codes = [c for c in _split_codes(cell, w) if c and set(c) != {"0"}]
        if codes:
            n_resp += 1
        per_row.append(codes)
    counts = {}
    for codes in per_row:
        for c in set(codes):                    # count each option once per respondent
            counts[c] = counts.get(c, 0) + 1
    rows = []
    for code in sorted(counts, key=lambda c: (-counts[c], c)):
        rows.append({"category": (vlabels or {}).get(code, code), "code": code,
                     "n": counts[code],
                     "pct_resp": round(counts[code] / n_resp * 100, 1) if n_resp else 0.0})
    rows.append({"meta": "respondents", "n": n_resp})
    return rows


# ------------------------------------------------------------------ F2 -------

F2_META_KEYS = {"survey_language", "consent_given", "consent_timestamp",
                "facility_id", "facility_type", "gps_status",
                "submission_lat", "submission_lng"}

# Curated F2 previews: (values_json item id, plan table no, fallback title).
# All four are single-answer items with strong pretest coverage.
F2_PREVIEWS = [("Q5", "4.19", "Healthcare workers by role"),
               ("Q6", "4.20", "Healthcare workers by specialization"),
               ("Q12", "4.3", "Healthcare workers who have heard of UHC"),
               ("Q123", "4.17", "Healthcare workers who considered leaving the facility")]


def explode_f2(rows, f2labels):
    """Explode F2 values_json rows into a per-item string DataFrame.

    rows: iterable of dicts (DictReader of f2_responses.csv) OR a DataFrame with
    a values_json column. Returns (df, {item_id: label}); multi-selects are
    joined with '; '. Meta keys are dropped.
    """
    if isinstance(rows, pd.DataFrame):
        rows = rows.to_dict("records")
    recs, keys, seen = [], [], set()
    for r in rows:
        try:
            vj = json.loads(r.get("values_json", "{}") or "{}")
        except (ValueError, TypeError):
            vj = {}
        rec = {}
        for k, v in vj.items():
            if k in F2_META_KEYS:
                continue
            if k not in seen:
                seen.add(k)
                keys.append(k)
            rec[k] = "; ".join(str(x) for x in v) if isinstance(v, list) else (
                "" if v is None else str(v))
        recs.append(rec)
    data = {k: [rec.get(k, "") for rec in recs] for k in keys}
    df = pd.DataFrame(data, columns=keys)
    labels = {k: (f2labels.get(k, {}).get("label") or k) for k in keys}
    return df, labels


# --------------------------------------------------------------- csv load ----

def read_headers(csv_path):
    """Set of lowercase column names for a responses CSV (utf-8-sig)."""
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        return set(c.strip().lower() for c in next(csv.reader(f)))
