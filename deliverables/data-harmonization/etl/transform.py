"""Transform: CAPI breakout tables + F2 store -> the MASTER DATASET.

WHAT CHANGED (2026-07-13): the ETL's consumer is now ASPSI's data-processing
team, not our own tabulation programs (Ma'am Myra moved table production to
ASPSI). So this stage no longer emits a 13-column shared-dimension subset —
it must emit **every question**, for **all four instruments**. That is the
deliverable.

Output per instrument:
  <inst>_clean.csv          one row per case; EVERY question column
  <inst>__<roster>.csv      one row per (case, occurrence) for each repeating
                            record — discovered, not hard-coded
  shared_dimensions.csv     the harmonized cross-instrument join layer (kept)

Design notes
------------
* Wide-join is safe: CSPro guarantees item names are unique **within** a
  dictionary, so the section tables (a_*, b_*, …) merge into one row with no
  prefixing and no collisions (verified across F1/F3/F4: 682/821/645 unique
  columns, zero clashes).
* Rosters are discovered by the presence of an `occ` column, so the F3
  cost-matrix rosters added on 2026-06-20 (Q92/94/96/97/98, Q107/109/112/113
  → *_PAY_ROSTER) are picked up automatically without touching this file.
* F2 is not CSPro: its answers live in a `values_json` blob on
  csweb_f2.f2_responses. We explode that blob into columns, union-ing the keys
  seen across all rows, so the F2 spec can evolve without an ETL change.
* Names >32 chars break Stata (.dta) but not CSV. We do NOT truncate here —
  truncation would silently collide. `long_names()` reports them so a .dta
  writer (or ASPSI) can map them deliberately once the handoff format is
  settled.
"""
import json

from extract_csweb import load_table, tables_in

INSTRUMENTS = {
    "f1": "csweb_f1_breakout",
    "f3": "csweb_f3_breakout",
    "f4": "csweb_f4_breakout",
}
F2_DB = "csweb_f2"
F2_TABLE = "f2_responses"

KEY_WIDTH = 12        # RR-PP-MMM-FF-CCC
FACILITY_WIDTH = 9    # first 9 digits of the key
STATA_NAME_MAX = 32

# CSPro/CSWeb plumbing — never part of the survey payload.
SYSTEM_TABLES = {"cases", "cspro_jobs", "cspro_meta", "notes", "level-1"}
SYSTEM_COLS = {"level-1-id", "occ", "case-id", "record-type", "id"}

# F2 store columns that are metadata, not answers (answers are inside values_json).
F2_META_COLS = ["submission_id", "client_submission_id", "submitted_at_server",
                "submitted_at_client", "source", "spec_version", "app_version",
                "hcw_id", "facility_id", "qn", "device_fingerprint", "status",
                "submission_lat", "submission_lng", "source_path", "encoded_by",
                "encoded_at"]

# --- the harmonized cross-instrument layer (codebook §1-§13) -------------------
# Unchanged in meaning: these are the few dimensions that mean the same thing in
# every instrument. They are now DERIVED FROM the wide row rather than being the
# whole output.
CANDIDATES = {
    # F2 is handled separately (f2_shared) — its keys are `Q3`-style and its
    # values are labels, not codes.
    "sex": {"f1": ["q4_sex"], "f3": ["q7_sex"], "f4": ["q3_sex"]},
    "consent_given": {"*": ["consent_given", "q3_consent", "q1_consent",
                            "informed_consent", "consent"]},
    "date_started": {"f1": ["date_first_visited_the_facility", "date_started"],
                     "*": ["date_first_visited", "date_started"]},
    "date_final": {"f1": ["date_of_final_visit_to_the_facility"],
                   "*": ["date_final_visit"]},
    "interviewer_id": {"*": ["interviewer_id", "enumerator_s_name"]},
    "language_used": {"*": ["language_used"]},
    "region_psgc": {"f1": ["region"], "f3": ["p_region"], "f4": ["region"]},
}
SHARED_DIMS = ["facility_id", "region_code", "sex", "consent_given",
               "survey_started_at", "survey_submitted_at", "survey_language",
               "interviewer_id", "response_source"]


def pad_key(v):
    """Zero-pad a case key to canonical width (etl-spec §2.1 caveat 2)."""
    return v.zfill(KEY_WIDTH) if v else v


def candidates_for(dim, inst):
    spec = CANDIDATES[dim]
    return spec.get(inst, spec.get("*", []))


def iso_datetime(date_v, time_v=None):
    """YYYYMMDD (+ HHMMSS) numeric, leading zeros possibly lost -> ISO."""
    if not date_v:
        return None
    d = str(date_v).split(".")[0].zfill(8)
    t = str(time_v or "0").split(".")[0].zfill(6)
    return f"{d[0:4]}-{d[4:6]}-{d[6:8]}T{t[0:2]}:{t[2:4]}:{t[4:6]}"


def header_of(raw_dir, db, table):
    """Column names of a table, even when it has no data rows."""
    path = raw_dir / db / f"{table}.tsv"
    if not path.exists():
        return []
    line = open(path, encoding="utf-8", errors="replace").readline().rstrip("\n")
    return [c.lower() for c in line.split("\t")] if line else []


def is_payload_col(c):
    """A real survey/answer column — not breakout plumbing."""
    return c not in SYSTEM_COLS and not c.endswith("-id")


def classify_tables(raw_dir, db):
    """Split an instrument's tables into (case_level, rosters).

    A table is a ROSTER iff it carries an `occ` column — CSPro emits that for
    every repeating record. This is why the F3 *_PAY_ROSTER tables added after
    this code was written need no change here.
    """
    case_level, rosters = [], []
    for t in tables_in(raw_dir, db):
        if t in SYSTEM_TABLES:
            continue
        cols = header_of(raw_dir, db, t)
        if not cols:
            continue
        (rosters if "occ" in cols else case_level).append(t)
    return case_level, rosters


def transform_instrument(raw_dir, inst, qa_notes):
    """One wide row per case (every question) + one child list per roster."""
    db = INSTRUMENTS[inst]
    level1 = load_table(raw_dir, db, "level-1")
    cases = {c["id"]: c for c in load_table(raw_dir, db, "cases")}
    case_tables, roster_tables = classify_tables(raw_dir, db)

    # index every case-level table by level-1-id for an O(1) wide join
    indexed = {}
    for t in case_tables:
        idx = {}
        for row in load_table(raw_dir, db, t):
            idx[row.get("level-1-id")] = row
        indexed[t] = idx

    clean, key_by_l1id = [], {}
    for l1 in level1:
        case = cases.get(l1.get("case-id"), {})
        if case.get("deleted") == "1":
            continue
        raw_key = l1.get("questionnaire_number") or ""
        if len(raw_key) != KEY_WIDTH:
            qa_notes.append(f"[key] {inst}: questionnaire_number '{raw_key}' is "
                            f"{len(raw_key)} chars, expected {KEY_WIDTH} — "
                            f"zero-padded for joins")
        key = pad_key(raw_key)
        l1id = l1.get("level-1-id")
        key_by_l1id[l1id] = key

        rec = {
            "_source_instrument": inst,
            "case_key": key,
            "facility_id": key[:FACILITY_WIDTH],
            "case_seq": key[FACILITY_WIDTH:],
            "partial_save": 1 if case.get("partial_save_mode") else 0,
            "response_source": "capi",
        }
        # THE POINT OF THIS FILE: every question, every section.
        for t in case_tables:
            row = indexed[t].get(l1id)
            for col in header_of(raw_dir, db, t):
                if is_payload_col(col):
                    rec[col] = (row or {}).get(col)
        clean.append(rec)

    rosters = {}
    for t in roster_tables:
        out = []
        cols = [c for c in header_of(raw_dir, db, t) if is_payload_col(c)]
        for row in load_table(raw_dir, db, t):
            key = key_by_l1id.get(row.get("level-1-id"))
            if key is None:
                continue          # orphan / deleted parent case
            child = {"_source_instrument": f"{inst}_{t}",
                     "case_key": key,
                     "occ": row.get("occ")}
            for col in cols:
                child[col] = row.get(col)
            out.append(child)
        rosters[t] = out
        if not out:
            qa_notes.append(f"[roster] {inst}.{t}: 0 rows (no occurrences in "
                            f"this extract)")
    return clean, rosters


def transform_f2(raw_dir, qa_notes):
    """F2 (PWA) -> one row per submission, answers exploded from values_json.

    F2 is NOT CSPro: `csweb_f2.f2_responses` stores the whole answer set as a
    JSON blob. We union the keys across submissions so a spec change does not
    require an ETL change. Column names are prefixed `q…` exactly as the app
    stores them — no renaming, so the F2 spec stays the codebook.
    """
    rows = load_table(raw_dir, F2_DB, F2_TABLE)
    if not rows:
        qa_notes.append("[f2] no rows found in csweb_f2.f2_responses — was the "
                        "F2 extract run? (see extract_csweb.F2_TABLES)")
        return []

    parsed = []
    answer_keys = []          # ordered, de-duplicated union of all answer keys
    seen = set()
    for r in rows:
        blob = r.get("values_json") or "{}"
        try:
            vals = json.loads(blob)
            if not isinstance(vals, dict):
                raise ValueError("values_json is not an object")
        except (ValueError, TypeError) as e:
            qa_notes.append(f"[f2] {r.get('client_submission_id')}: unparseable "
                            f"values_json ({e}) — row kept, answers blank")
            vals = {}
        for k in vals:
            if k not in seen:
                seen.add(k)
                answer_keys.append(k)
        parsed.append((r, vals))

    clean = []
    for r, vals in parsed:
        qn = (r.get("qn") or "").strip()
        if qn and len(qn) != KEY_WIDTH:
            qa_notes.append(f"[key] f2: qn '{qn}' is {len(qn)} chars, expected "
                            f"{KEY_WIDTH} — zero-padded")
        key = pad_key(qn) if qn else ""
        if not key:
            qa_notes.append(f"[key] f2: submission "
                            f"{r.get('client_submission_id')} has NO qn "
                            f"(pre-QN enrollment) — case_key left blank; it "
                            f"cannot join to F1/F3/F4 by key")
        facility = (r.get("facility_id") or "")
        rec = {
            "_source_instrument": "f2",
            "case_key": key,
            # F2's facility_id is authoritative (the key may be blank on legacy
            # rows), so take it from the column, not from a slice of the key.
            "facility_id": facility.zfill(FACILITY_WIDTH) if facility.isdigit() else facility,
            "case_seq": key[FACILITY_WIDTH:] if key else "",
            "partial_save": 0,          # F2 submits atomically; no partial rows
            "response_source": "pwa" if r.get("source_path") != "paper_encoded"
                               else "paper_encoded",
        }
        for col in F2_META_COLS:
            if col not in rec:
                rec[f"f2_{col}"] = r.get(col)
        # #825: a refusal is data — consent_given=0 is inside values_json.
        for k in answer_keys:
            v = vals.get(k)
            rec[k] = json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v
        clean.append(rec)
    return clean


def shared_row(rec, inst, qa_notes):
    """Derive the harmonized dimensions from a wide row (codebook §1-§13)."""
    def pick(dim):
        for name in candidates_for(dim, inst):
            if name in rec and rec[name] not in (None, ""):
                return rec[name]
        return None

    region = pick("region_psgc")
    started, final = pick("date_started"), pick("date_final")
    return {
        "facility_id": rec.get("facility_id"),
        "region_code": str(region).zfill(10)[:2] if region else None,
        "sex": pick("sex"),
        "consent_given": pick("consent_given"),
        "survey_started_at": iso_datetime(started) if started else None,
        "survey_submitted_at": iso_datetime(final) if final else None,
        "survey_language": pick("language_used"),
        "interviewer_id": pick("interviewer_id"),
        "response_source": rec.get("response_source"),
    }


def region_from_facility(facility_id):
    """First 2 digits of the 9-digit PSGC facility code.

    ONLY for a real numeric code. F2's legacy facilities are slugs
    ('DEMO-FAC-RHU-QC-1'), and blindly slicing one yields region 'DE' — junk
    that would silently pollute the cross-instrument join layer. Verified live
    2026-07-13: all 41 F2 submissions carry slug facilities.
    """
    f = (facility_id or "").strip()
    if not f.isdigit():
        return None
    return f.zfill(FACILITY_WIDTH)[:2]


# codebook §3: F1/F3/F4 store sex as a numeric code; F2 (a web form) stores the
# display LABEL. The master dataset keeps each instrument's raw answer intact in
# its own file, but the harmonized join layer must speak one language.
F2_SEX_TO_CODE = {"male": "1", "female": "2"}


def f2_shared(r, qa_notes):
    """F2's harmonized dimensions. F2 is a web form, not CSPro: its answer keys
    are `Q2`,`Q3`,… and its values are labels, so it needs its own mapping."""
    raw_sex = r.get("Q3")
    sex = F2_SEX_TO_CODE.get(str(raw_sex).strip().lower()) if raw_sex else None
    if raw_sex and sex is None:
        qa_notes.append(f"[f2] unmapped sex label {raw_sex!r} (codebook §3 "
                        f"expects Male/Female) — left blank in shared_dimensions")
    return {
        "facility_id": r.get("facility_id"),
        "region_code": region_from_facility(r.get("facility_id")),
        "sex": sex,
        "consent_given": r.get("consent_given"),
        "survey_started_at": r.get("f2_submitted_at_client"),
        "survey_submitted_at": r.get("f2_submitted_at_server"),
        "survey_language": r.get("survey_language"),
        # F2 is self-administered: there is no interviewer. The only human in
        # the loop is the admin who transcribed a paper form (§11 provenance).
        "interviewer_id": r.get("f2_encoded_by"),
        "response_source": r.get("response_source"),
    }


def to_shared_dimensions(clean_rows, qa_notes):
    """Long format: one row per (instrument, case, dimension). Codebook §0.3."""
    out = []
    for r in clean_rows:
        inst = r["_source_instrument"]
        dims = f2_shared(r, qa_notes) if inst == "f2" else shared_row(r, inst, qa_notes)
        for d in SHARED_DIMS:
            v = dims.get(d)
            if v not in (None, ""):
                out.append({"instrument": inst, "case_key": r["case_key"],
                            "dimension": d, "value": v})
    return out


def long_names(rows):
    """Column names that exceed Stata's 32-char variable limit.

    Reported, never silently truncated — truncation can collide, and which
    names get shortened is ASPSI's call once the handoff format is agreed.
    """
    if not rows:
        return []
    return sorted({c for c in rows[0] if len(c) > STATA_NAME_MAX})
