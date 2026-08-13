"""Regression tests for the master-dataset transform (stdlib only).

    python test_transform.py

Covers the things that would silently corrupt the deliverable:
  * F2 `values_json` surviving `mysql --batch` escaping (tabs/newlines inside a
    free-text answer are the classic way a TSV pipeline mangles data)
  * refusals (#825) arriving as data, not as a dropped row
  * pre-QN submissions keeping their facility_id but declaring a blank case_key
  * paper-encoded provenance
  * CAPI wide-join: every section's questions land on the case row
  * roster discovery by `occ` (so the F3 *_PAY_ROSTER tables need no code change)
  * write_csv keeping the file rectangular when rows have different keys
"""
import csv, json, sys, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from transform import transform_f2, transform_instrument, to_shared_dimensions
from run import write_csv

FAILURES = []


def check(name, cond, detail=""):
    if cond:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}  {detail}")
        FAILURES.append(name)


def mysql_escape(v):
    """What `mysql --batch` does to a value so each row stays on one line."""
    return (v.replace("\\", "\\\\").replace("\t", "\\t")
             .replace("\n", "\\n").replace("\r", "\\r"))


# --------------------------------------------------------------------------
def f2_fixture(root):
    d = root / "csweb_f2"
    d.mkdir(parents=True, exist_ok=True)
    cols = ["id", "submission_id", "client_submission_id", "submitted_at_server",
            "submitted_at_client", "source", "spec_version", "app_version",
            "hcw_id", "facility_id", "device_fingerprint", "sync_attempt_count",
            "status", "values_json", "submission_lat", "submission_lng",
            "source_path", "encoded_by", "encoded_at", "synced_at", "qn"]

    def row(csid, qn, status, vals, fac="040340002",
            src="self_admin", enc="NULL"):
        return "\t".join([
            "1", "srv-x", csid, "2026-07-10 03:00:00", "2026-07-10 02:59:00",
            "PWA", "2026-07-02-r6", "2.1.0", "HCW-1", fac, "fp", "1", status,
            mysql_escape(json.dumps(vals, ensure_ascii=False)),
            "NULL", "NULL", src, enc, "NULL", "2026-07-10 03:00:01", qn])

    lines = ["\t".join(cols)]
    # a real submit whose free text contains a TAB and a NEWLINE — the payload
    # most likely to corrupt a TSV pipeline. Answer keys are `Q3`-style and
    # values are LABELS, exactly as the live store holds them (verified 07-13).
    lines.append(row("c1", "040340002001", "stored", {
        "q1_role": "3", "Q3": "Female", "q7_years": 4, "consent_given": 1,
        "q88_comment": "line one\nline two\tafter tab"}))
    lines.append(row("c2", "040340002002", "refusal", {"consent_given": 0}))
    lines.append(row("c3", "", "stored", {"q1_role": "1", "consent_given": 1},
                     fac="DEMO-FAC-RHU-QC-1"))                  # pre-QN legacy
    lines.append(row("c4", "040340002003", "stored",
                     {"q1_role": "2", "consent_given": 1},
                     src="paper_encoded", enc="marriz_admin"))
    (d / "f2_responses.tsv").write_text("\n".join(lines), encoding="utf-8")


def test_f2():
    print("\nF2 — PWA store (values_json explode)")
    root = Path(tempfile.mkdtemp()) / "raw"
    f2_fixture(root)
    notes = []
    rows = transform_f2(root, notes)

    check("all 4 submissions transformed", len(rows) == 4, f"got {len(rows)}")
    by = {r["f2_client_submission_id"]: r for r in rows}

    c1 = by["c1"]
    check("tab + newline survive mysql escaping",
          c1.get("q88_comment") == "line one\nline two\tafter tab",
          repr(c1.get("q88_comment")))
    check("answers exploded into columns",
          c1.get("q1_role") == "3" and c1.get("q7_years") == 4 and c1.get("Q3") == "Female")
    check("qn becomes the 12-digit case_key",
          c1["case_key"] == "040340002001", c1["case_key"])

    check("refusal (#825) is DATA, consent_given=0",
          by["c2"].get("consent_given") == 0)

    c3 = by["c3"]
    check("pre-QN row: blank key, facility kept",
          c3["case_key"] == "" and c3["facility_id"] == "DEMO-FAC-RHU-QC-1",
          f"{c3['case_key']!r} {c3['facility_id']!r}")
    check("pre-QN row raises a QA note",
          any("NO qn" in n for n in notes))

    check("paper-encoded provenance preserved",
          by["c4"]["response_source"] == "paper_encoded")

    # a spec change (a new question) must not break older rows
    cols = {k for r in rows for k in r}
    check("column union covers every answer key seen",
          {"q1_role", "Q3", "q7_years", "q88_comment"} <= cols)

    shared = to_shared_dimensions(rows, notes)
    f2_shared = [s for s in shared if s["instrument"] == "f2"]
    check("F2 feeds the shared-dimension join layer", len(f2_shared) > 0,
          f"{len(f2_shared)} rows")

    # --- regressions found by the first live run against the box, 2026-07-13 ---
    dims = {(s["dimension"], s["value"]) for s in shared}

    # F2 answers are display LABELS ('Female'), CAPI answers are codes ('2').
    # The wide file keeps the label; the join layer must speak one language.
    check("F2 sex label recoded to the canonical code (codebook §3)",
          ("sex", "2") in dims,
          sorted(v for d, v in dims if d == "sex"))

    # facility slugs must NOT be sliced into a region: 'DEMO-FAC-…'[:2] == 'DE',
    # which silently poisons every cross-instrument geography join.
    regions = {v for d, v in dims if d == "region_code"}
    check("slug facilities yield NO region_code (not 'DE')",
          regions == {"04"}, regions)


# --------------------------------------------------------------------------
def capi_fixture(root):
    """Minimal CSPro breakout: 1 case, 2 sections, 1 roster (by `occ`)."""
    d = root / "csweb_f1_breakout"
    d.mkdir(parents=True, exist_ok=True)
    w = lambda n, s: (d / f"{n}.tsv").write_text(s, encoding="utf-8")
    w("level-1", "level-1-id\tcase-id\tquestionnaire_number\n1\tcase-a\t10280001001")
    w("cases", "id\tdeleted\tpartial_save_mode\ncase-a\t0\t")
    w("a_profile", "a_profile-id\tlevel-1-id\tq4_sex\tq5_age\n1\t1\t2\t41")
    w("b_services", "b_services-id\tlevel-1-id\tq10_beds\tq11_open\n1\t1\t120\t1")
    w("c_staff_roster",
      "c_staff_roster-id\tlevel-1-id\tocc\tq20_name\tq21_role\n"
      "1\t1\t1\tNurse A\t2\n2\t1\t2\tNurse B\t3")


def test_capi():
    print("\nF1/F3/F4 — CSPro wide join + roster discovery")
    root = Path(tempfile.mkdtemp()) / "raw"
    capi_fixture(root)
    notes = []
    clean, rosters = transform_instrument(root, "f1", notes)

    check("one wide row per case", len(clean) == 1, f"got {len(clean)}")
    r = clean[0]
    check("11-digit key zero-padded to 12",
          r["case_key"] == "010280001001", r["case_key"])
    check("facility_id sliced from key", r["facility_id"] == "010280001")
    check("EVERY section's questions land on the case row",
          r.get("q4_sex") == "2" and r.get("q5_age") == "41"
          and r.get("q10_beds") == "120" and r.get("q11_open") == "1",
          {k: r.get(k) for k in ("q4_sex", "q5_age", "q10_beds", "q11_open")})
    check("breakout plumbing kept OUT of the payload",
          not any(k.endswith("-id") or k == "occ" for k in r))

    check("roster discovered by `occ` (not hard-coded)",
          list(rosters) == ["c_staff_roster"], list(rosters))
    staff = rosters["c_staff_roster"]
    check("roster rows keyed to the parent case + occurrence",
          len(staff) == 2 and staff[0]["case_key"] == "010280001001"
          and staff[0]["occ"] == "1" and staff[1]["q20_name"] == "Nurse B")

    shared = to_shared_dimensions(clean, notes)
    check("shared dimensions still derived from the wide row",
          any(s["dimension"] == "sex" and s["value"] == "2" for s in shared))


# --------------------------------------------------------------------------
def test_write_csv():
    print("\nwrite_csv — rectangular output across ragged rows")
    out = Path(tempfile.mkdtemp()) / "x.csv"
    cols = write_csv(out, [{"a": 1, "b": 2}, {"a": 3, "c": 4}])
    check("column union, not just row[0]'s keys", cols == ["a", "b", "c"], cols)
    rows = list(csv.DictReader(open(out, encoding="utf-8")))
    check("missing cells blank-filled, file stays rectangular",
          rows[1]["b"] == "" and rows[1]["c"] == "4")


if __name__ == "__main__":
    test_f2()
    test_capi()
    test_write_csv()
    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILED: {FAILURES}")
        sys.exit(1)
    print("all green")
