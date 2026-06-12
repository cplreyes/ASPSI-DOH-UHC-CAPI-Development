"""Transform: codebook.md recodes (skeleton — shared-dimension subset).

Implemented dimensions (codebook section in parens):
  case key + facility_id (§2), geography region_code (§1, partial),
  sex (§3), survey datetimes (§10), consent (§9, discovery-based),
  interviewer/response_source (§11).
Remaining sections are stubbed via DIMENSION_TODO so qa_report shows
exactly what the skeleton does not yet cover.

Column *discovery*: each dimension lists candidate source columns; the
transform searches every record table of the instrument and reports
found/missing (etl-spec §4 "codebook drift" gate).
"""
from extract_csweb import load_table, tables_in

INSTRUMENTS = {
    "f1": "csweb_f1_breakout",
    "f3": "csweb_f3_breakout",
    "f4": "csweb_f4_breakout",
}
KEY_WIDTH = 12        # RR-PP-MMM-FF-CCC
FACILITY_WIDTH = 9    # first 9 digits of the key

# dimension -> candidate column names (lowercase), per instrument ('*' = any)
CANDIDATES = {
    "sex": {"f1": ["q4_sex"], "f3": ["q7_sex"], "f4": ["q3_sex"]},
    # codebook §9 expects consent_given; NOT present in as-built Jun dcfs
    # (a_informed_consent has no boolean) — kept so drift stays visible
    "consent_given": {"*": ["consent_given", "q3_consent", "q1_consent",
                            "informed_consent", "consent"]},
    # as-built Jun dcfs: DATE_STARTED/TIME_STARTED replaced by visit dates
    # (codebook §10 needs amending; no time-of-day captured anywhere)
    "date_started": {"f1": ["date_first_visited_the_facility", "date_started"],
                     "*": ["date_first_visited", "date_started"]},
    "date_final": {"f1": ["date_of_final_visit_to_the_facility"],
                   "*": ["date_final_visit"]},
    # as-built: INTERVIEWER_ID gone; only free-text enumerator name remains
    # (codebook §11 expects roster IDs — flagged for ASPSI)
    "interviewer_id": {"*": ["interviewer_id", "enumerator_s_name"]},
    "language_used": {"*": ["language_used"]},   # §13/§15.E — as-built ✓
    "region_psgc": {"f1": ["region"], "f3": ["p_region"], "f4": ["region"]},
}
DIMENSION_TODO = ["age (§4)", "leadership role (§5)", "discipline (§6)",
                  "employment (§7)", "philhealth (§8)", "disposition (§12)",
                  "language (§13)", "per-question f*_q* columns (§0.1)",
                  "stata .dta output (§0.3)", "missing-value sentinels (§0.2)"]


def pad_key(v):
    """Zero-pad a case key to canonical width (etl-spec §2.1 caveat 2)."""
    return v.zfill(KEY_WIDTH) if v else v


def find_column(raw_dir, db, names):
    """First (table, column) whose column matches any candidate name."""
    for table in tables_in(raw_dir, db):
        rows = load_table(raw_dir, db, table)
        if not rows:
            # still need header for empty tables
            path = raw_dir / db / f"{table}.tsv"
            lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
            cols = [c.lower() for c in lines[0].split("\t")] if lines else []
        else:
            cols = list(rows[0].keys())
        for name in names:
            if name in cols:
                return table, name
    return None, None


def candidates_for(dim, inst):
    spec = CANDIDATES[dim]
    return spec.get(inst, spec.get("*", []))


def iso_datetime(date_v, time_v):
    """YYYYMMDD + HHMMSS (numeric, may have lost leading zeros) -> ISO."""
    if not date_v:
        return None
    d = date_v.split(".")[0].zfill(8)
    t = (time_v or "0").split(".")[0].zfill(6)
    return f"{d[0:4]}-{d[4:6]}-{d[6:8]}T{t[0:2]}:{t[2:4]}:{t[4:6]}"


def transform_instrument(raw_dir, inst, qa_notes):
    db = INSTRUMENTS[inst]
    level1 = load_table(raw_dir, db, "level-1")
    cases = {c["id"]: c for c in load_table(raw_dir, db, "cases")}

    # resolve dimension source columns once per instrument
    colmap = {}
    for dim in CANDIDATES:
        table, col = find_column(raw_dir, db, candidates_for(dim, inst))
        colmap[dim] = (table, col)
        if col is None:
            qa_notes.append(f"[drift] {inst}: no source column found for "
                            f"dimension '{dim}' (candidates: "
                            f"{candidates_for(dim, inst)})")

    # cache the record tables we actually need
    tables = {t: load_table(raw_dir, db, t)
              for t in {t for t, c in colmap.values() if t}}

    def value_for(dim, l1id):
        table, col = colmap[dim]
        if not col:
            return None
        for row in tables[table]:
            if row.get("level-1-id") == l1id:
                return row.get(col)
        return None

    clean = []
    for l1 in level1:
        raw_key = l1.get("questionnaire_number") or ""
        if len(raw_key) != KEY_WIDTH:
            qa_notes.append(f"[key] {inst}: questionnaire_number '{raw_key}' is "
                            f"{len(raw_key)} chars, expected {KEY_WIDTH} — "
                            f"zero-padded for joins (instrument should enforce "
                            f"canonical key; see runbook caveat)")
        key = pad_key(raw_key)
        case = cases.get(l1.get("case-id"), {})
        if case.get("deleted") == "1":
            continue
        l1id = l1.get("level-1-id")
        rec = {
            "_source_instrument": inst,
            "case_key": key,
            "facility_id": key[:FACILITY_WIDTH],
            "case_seq": key[FACILITY_WIDTH:],
            "partial_save": 1 if case.get("partial_save_mode") else 0,
            "response_source": "capi",                          # §11
            "interviewer_id": value_for("interviewer_id", l1id),
            "sex": value_for("sex", l1id),                      # §3 numeric passthrough
            "consent_given": value_for("consent_given", l1id),  # §9
            # §1: PSGC values are numeric-entered -> leading zeros lost;
            # zfill to the 10-digit PSA-2024 width BEFORE slicing region
            "region_code": ((value_for("region_psgc", l1id) or "").zfill(10)[:2]
                            if value_for("region_psgc", l1id) else None),
            "survey_started_at": iso_datetime(value_for("date_started", l1id),
                                              None),                # §10 (date-only as-built)
            "survey_submitted_at": iso_datetime(value_for("date_final", l1id),
                                                None),              # §10 final-visit date
            "survey_language": value_for("language_used", l1id),    # §13
        }
        clean.append(rec)

    roster = []
    if inst == "f4":
        for m in load_table(raw_dir, db, "c_household_roster"):
            l1ids = {r.get("level-1-id"): r for r in level1}
            parent = l1ids.get(m.get("level-1-id"), {})
            roster.append({
                "_source_instrument": "f4_roster",
                "case_key": pad_key(parent.get("questionnaire_number") or ""),
                "member_occ": m.get("occ"),
                "sex": m.get("q33_sex"),
            })
    return clean, roster


def to_shared_dimensions(clean_rows):
    """Long format: one row per (instrument, case, dimension). Codebook §0.3."""
    out = []
    dims = ["facility_id", "region_code", "sex", "consent_given",
            "survey_started_at", "survey_submitted_at", "survey_language",
            "interviewer_id", "response_source"]
    for r in clean_rows:
        for d in dims:
            if r.get(d) is not None:
                out.append({"instrument": r["_source_instrument"],
                            "case_key": r["case_key"],
                            "dimension": d, "value": r[d]})
    return out
