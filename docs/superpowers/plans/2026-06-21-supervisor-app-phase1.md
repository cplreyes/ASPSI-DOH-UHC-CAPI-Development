# Supervisor App — Phase 1 (Review Layer) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a read-only field-QA report for F1/F3/F4 CAPI cases — partial-case visibility (#561), coverage vs plan, read-only spot-check pointers, and automated data-quality flags — that a supervisor runs at base each evening.

**Architecture:** A small **Python** tool (`supervisor_qa_report.py`) reads **CSV exports** of the pulled F1/F3/F4 cases (the supervisor exports them from the desktop Data Viewer / CSWeb) plus an **assignment/target CSV**, computes coverage / partials / flags, and writes **one self-contained HTML report**. Pure functions per concern (case model, coverage, QA rules, HTML) so each is unit-tested with pytest. The tool never writes case data and never needs the network — it reads exports that exist regardless of how cases arrived (CSWeb GET now, Bluetooth in Phase 2).

**Tech Stack:** Python 3 (stdlib only: `csv`, `dataclasses`, `argparse`, `html`, `datetime`) + pytest for tests. No new runtime dependencies. Lives alongside the repo's existing Python automation.

**Why Python (refinement of the spec's "CSPro batch app"):** the spec's intent is "a laptop tool that reads pulled cases → HTML." The repo's tooling is already all Python (`generate_*.py`, `verify_questions.py`), and Python over CSV exports is fully unit-testable (the spec's open item — a CSPro `Case`-object multi-dictionary batch app — is neither testable nor idiomatic here). The supervisor's SOP gains one step (export to CSV from Data Viewer); a future enhancement can read `.csdb` SQLite directly to drop that step.

## Global Constraints

- **Do NOT git commit or push.** Carl handles all git manually. End each task by leaving changes in the working tree (no `git add`/`git commit`).
- **Read-only.** The tool never writes/edits/syncs case data; it only reads CSV exports + the assignment CSV and writes one HTML file.
- **PII-light report.** The HTML contains case keys + facility + enumerator ID + status + flag reasons ONLY. Never names, never answer values. A test asserts this.
- **Phase-2 compatible.** Input is CSV exports of cases — independent of transport (CSWeb GET or Bluetooth). No code path assumes the network or a specific sync method.
- **Completeness source of truth:** `CASE_DISPOSITION` (F3/F4: `1`=Completed, `2`=Partial, `0`=In Progress). **F1 has no `CASE_DISPOSITION`** — derive completeness from `ENUM_RESULT_FINAL_VISIT` (F1 Completed = code `1`). This split is shipped + device-confirmed (Cluster 5, 2026-06-21).
- **Stuck-partial threshold:** `N = 2` days (partial/in-progress case whose `DATE_FINAL_VISIT` is older than 2 days).
- **Python:** stdlib only; no pip installs beyond pytest (dev-only).

---

## File Structure

All under `deliverables/CSWeb/supervisor-app/`:

- `case_model.py` — `Case` dataclass + `FIELD_MAP` (per-instrument item names) + `load_cases(csv_path, instrument)` → `list[Case]`. One responsibility: turn a CSV export into normalized, PII-light Case records.
- `assignment.py` — `Assignment` dataclass + `load_assignments(csv_path)` → `dict[facility -> Assignment]`. The coverage "plan".
- `coverage.py` — `compute_coverage(cases, assignments)` → `list[CoverageRow]` + team totals. Pure.
- `qa_rules.py` — the 5 rule functions + `run_rules(cases)` → `list[Flag]`. Pure.
- `report_html.py` — `render_report(coverage, partials, flags, meta)` → HTML string. Pure; PII-light.
- `supervisor_qa_report.py` — CLI entry: wires loaders → compute → render → write file.
- `assignments.example.csv` — template for the assignment lookup.
- `README.md` — supervisor SOP: CSWeb role config (C1), tablet review setup (C5), export + run steps.
- `tests/` — `test_case_model.py`, `test_assignment.py`, `test_coverage.py`, `test_qa_rules.py`, `test_report_html.py`, `test_cli.py`, plus `tests/fixtures/` synthetic CSVs.

**Run tests:** `cd deliverables/CSWeb/supervisor-app && python -m pytest -q`

---

### Task 1: Case model + CSV loader

**Files:**
- Create: `deliverables/CSWeb/supervisor-app/case_model.py`
- Create: `deliverables/CSWeb/supervisor-app/tests/test_case_model.py`
- Create: `deliverables/CSWeb/supervisor-app/tests/fixtures/f3_sample.csv`

**Interfaces:**
- Produces: `Case` dataclass with fields `instrument:str, case_key:str, facility:str, enumerator_name:str, disposition:str ("complete"|"partial"|"in_progress"), result_code:str, has_gps:bool, has_photo:bool, final_visit_date:str, answers_present:bool`; `FIELD_MAP: dict`; `load_cases(csv_path:str, instrument:str) -> list[Case]`.

- [ ] **Step 1: Write the fixture** `tests/fixtures/f3_sample.csv` (CSPro CSV export uses dictionary item names as headers):

```csv
QUESTIONNAIRE_NUMBER,FACILITY_GPS_LATITUDE,VERIFICATION_PHOTO_FILENAME,ENUM_RESULT_FINAL_VISIT,CASE_DISPOSITION,Q1_IS_PATIENT,DATE_FINAL_VISIT,ENUMERATOR_S_NAME
010280001001,14.5995,case-010280001001-verification.jpg,1,1,1,20260620,Juan Dela Cruz
010280001002,,,6,2,1,20260619,Maria Santos
010280001003,14.6,,,0,,20260618,Pedro Reyes
```

- [ ] **Step 2: Write the failing test**

```python
# tests/test_case_model.py
import os
from case_model import load_cases, Case

FIX = os.path.join(os.path.dirname(__file__), "fixtures")

def test_load_f3_normalizes_three_cases():
    cases = load_cases(os.path.join(FIX, "f3_sample.csv"), "F3")
    assert len(cases) == 3
    c0, c1, c2 = cases
    # case 0: completed, has gps + photo, answers present
    assert c0.case_key == "010280001001"
    assert c0.facility == "01-02-800-01"
    assert c0.disposition == "complete"
    assert c0.has_gps is True and c0.has_photo is True
    assert c0.answers_present is True
    # case 1: withdraw (CASE_DISPOSITION=2 -> partial), no gps, no photo
    assert c1.disposition == "partial"
    assert c1.result_code == "6"
    assert c1.has_gps is False and c1.has_photo is False
    # case 2: in progress (CASE_DISPOSITION=0), blank result + blank consent
    assert c2.disposition == "in_progress"
    assert c2.answers_present is False
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd deliverables/CSWeb/supervisor-app && python -m pytest tests/test_case_model.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'case_model'`.

- [ ] **Step 4: Write the implementation**

```python
# case_model.py
"""Read a CSPro CSV export (one instrument) into normalized, PII-light Case records.

CSPro's CSV export uses dictionary item names as column headers, so FIELD_MAP just
names the items we read per instrument. Completeness comes from CASE_DISPOSITION
(F3/F4, shipped 2026-06-21); F1 has no such field, so it falls back to the result code.
"""
import csv
from dataclasses import dataclass

# Per-instrument item names. F4's GPS latitude column differs — confirm with:
#   grep -oE '"name": "[A-Z_]*GPS_LATITUDE"' F4/HouseholdSurvey.dcf | sort -u
# and replace "HH_GPS_LATITUDE" below with the exact name before running on F4.
FIELD_MAP = {
    "F1": {"disposition": None, "result": "ENUM_RESULT_FINAL_VISIT",
           "completed_codes": {"1"}, "gps_lat": "FACILITY_GPS_LATITUDE",
           "photo": "VERIFICATION_PHOTO_FILENAME", "early": "Q1_NAME",
           "date": "DATE_FINAL_VISIT", "enumerator": "ENUMERATOR_S_NAME"},
    "F3": {"disposition": "CASE_DISPOSITION", "result": "ENUM_RESULT_FINAL_VISIT",
           "completed_codes": {"1", "2", "5"}, "gps_lat": "FACILITY_GPS_LATITUDE",
           "photo": "VERIFICATION_PHOTO_FILENAME", "early": "Q1_IS_PATIENT",
           "date": "DATE_FINAL_VISIT", "enumerator": "ENUMERATOR_S_NAME"},
    "F4": {"disposition": "CASE_DISPOSITION", "result": "ENUM_RESULT_FINAL_VISIT",
           "completed_codes": {"1"}, "gps_lat": "HH_GPS_LATITUDE",
           "photo": "VERIFICATION_PHOTO_FILENAME", "early": "Q1_IS_HH_HEAD",
           "date": "DATE_FINAL_VISIT", "enumerator": "ENUMERATOR_S_NAME"},
}


@dataclass
class Case:
    instrument: str
    case_key: str
    facility: str
    enumerator_name: str   # PII — used only for the spot-check pointer, never rendered
    disposition: str       # "complete" | "partial" | "in_progress"
    result_code: str
    has_gps: bool
    has_photo: bool
    final_visit_date: str
    answers_present: bool


def _facility_from_key(key):
    k = (key or "").strip()
    if len(k) < 12:
        return k
    return f"{k[0:2]}-{k[2:4]}-{k[4:7]}-{k[7:9]}"   # RR-PP-MMM-FF


def _disposition(row, m):
    """complete / partial / in_progress from CASE_DISPOSITION, else the result code."""
    if m["disposition"]:
        d = (row.get(m["disposition"]) or "").strip()
        if d == "1":
            return "complete"
        if d == "0" or d == "":
            return "in_progress"
        return "partial"
    # F1 fallback: no sentinel — use the result code
    r = (row.get(m["result"]) or "").strip()
    if r in m["completed_codes"]:
        return "complete"
    if r == "":
        return "in_progress"
    return "partial"


def load_cases(csv_path, instrument):
    m = FIELD_MAP[instrument]
    out = []
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            key = (row.get("QUESTIONNAIRE_NUMBER") or "").strip()
            out.append(Case(
                instrument=instrument,
                case_key=key,
                facility=_facility_from_key(key),
                enumerator_name=(row.get(m["enumerator"]) or "").strip(),
                disposition=_disposition(row, m),
                result_code=(row.get(m["result"]) or "").strip(),
                has_gps=bool((row.get(m["gps_lat"]) or "").strip()),
                has_photo=bool((row.get(m["photo"]) or "").strip()),
                final_visit_date=(row.get(m["date"]) or "").strip(),
                answers_present=bool((row.get(m["early"]) or "").strip()),
            ))
    return out
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd deliverables/CSWeb/supervisor-app && python -m pytest tests/test_case_model.py -q`
Expected: PASS (1 passed).

- [ ] **Step 6: Confirm the F4 GPS field name** (data-derived, not a placeholder)

Run: `grep -oE '"name": "[A-Z_]*GPS_LATITUDE"' deliverables/CSPro/F4/HouseholdSurvey.dcf | sort -u`
Then set `FIELD_MAP["F4"]["gps_lat"]` to the exact name returned. Leave the working tree changed (Carl commits).

---

### Task 2: Assignment / target lookup loader

**Files:**
- Create: `deliverables/CSWeb/supervisor-app/assignment.py`
- Create: `deliverables/CSWeb/supervisor-app/assignments.example.csv`
- Create: `deliverables/CSWeb/supervisor-app/tests/test_assignment.py`

**Interfaces:**
- Consumes: nothing from Task 1.
- Produces: `Assignment` dataclass `(enumerator_id:str, facility:str, instrument:str, target:int)`; `load_assignments(csv_path:str) -> dict[(instrument, facility) -> Assignment]`.

- [ ] **Step 1: Write the example/template CSV** `assignments.example.csv`:

```csv
ENUMERATOR_ID,FACILITY_CODE,INSTRUMENT,TARGET_COUNT
se-004,01-02-800-01,F3,10
se-011,01-02-800-02,F3,10
fs-01,01-02-800-01,F1,1
```

- [ ] **Step 2: Write the failing test**

```python
# tests/test_assignment.py
import os
from assignment import load_assignments

FIX = os.path.join(os.path.dirname(__file__), "..", "assignments.example.csv")

def test_load_assignments_keys_by_instrument_and_facility():
    a = load_assignments(FIX)
    assert a[("F3", "01-02-800-01")].target == 10
    assert a[("F3", "01-02-800-01")].enumerator_id == "se-004"
    assert a[("F1", "01-02-800-01")].target == 1
    assert ("F3", "01-02-800-99") not in a
```

- [ ] **Step 3: Run test to verify it fails**

Run: `python -m pytest tests/test_assignment.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'assignment'`.

- [ ] **Step 4: Write the implementation**

```python
# assignment.py
"""Load the supervisor-maintained assignment/target lookup (the coverage 'plan')."""
import csv
from dataclasses import dataclass


@dataclass
class Assignment:
    enumerator_id: str
    facility: str
    instrument: str
    target: int


def load_assignments(csv_path):
    out = {}
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            inst = (row.get("INSTRUMENT") or "").strip()
            fac = (row.get("FACILITY_CODE") or "").strip()
            try:
                target = int((row.get("TARGET_COUNT") or "0").strip())
            except ValueError:
                target = 0
            out[(inst, fac)] = Assignment(
                enumerator_id=(row.get("ENUMERATOR_ID") or "").strip(),
                facility=fac, instrument=inst, target=target)
    return out
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_assignment.py -q`
Expected: PASS.

---

### Task 3: Coverage computation

**Files:**
- Create: `deliverables/CSWeb/supervisor-app/coverage.py`
- Create: `deliverables/CSWeb/supervisor-app/tests/test_coverage.py`

**Interfaces:**
- Consumes: `Case` (Task 1), `Assignment` + `load_assignments` map (Task 2).
- Produces: `CoverageRow` dataclass `(instrument:str, facility:str, enumerator_id:str, done:int, partial:int, target:int, remaining:int, behind:bool)`; `compute_coverage(cases:list[Case], assignments:dict) -> list[CoverageRow]`. `done` counts `disposition=="complete"`; `partial` counts `partial`+`in_progress`; `remaining = max(target-done, 0)`; `behind = done < target`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_coverage.py
from case_model import Case
from assignment import Assignment
from coverage import compute_coverage

def _c(fac, disp):
    return Case("F3", fac.replace("-", "") + "001", fac, "x", disp, "1", True, True, "20260620", True)

def test_coverage_counts_done_partial_and_remaining():
    cases = [_c("01-02-800-01", "complete"), _c("01-02-800-01", "complete"),
             _c("01-02-800-01", "partial"), _c("01-02-800-02", "complete")]
    assignments = {("F3", "01-02-800-01"): Assignment("se-004", "01-02-800-01", "F3", 10),
                   ("F3", "01-02-800-02"): Assignment("se-011", "01-02-800-02", "F3", 10)}
    rows = {(r.instrument, r.facility): r for r in compute_coverage(cases, assignments)}
    r1 = rows[("F3", "01-02-800-01")]
    assert (r1.done, r1.partial, r1.remaining, r1.behind) == (2, 1, 8, True)
    assert r1.enumerator_id == "se-004"
    r2 = rows[("F3", "01-02-800-02")]
    assert (r2.done, r2.remaining) == (1, 9)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_coverage.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'coverage'`.

- [ ] **Step 3: Write the implementation**

```python
# coverage.py
"""Coverage vs plan, per (instrument, facility). Enumerator id comes from the assignment."""
from dataclasses import dataclass


@dataclass
class CoverageRow:
    instrument: str
    facility: str
    enumerator_id: str
    done: int
    partial: int
    target: int
    remaining: int
    behind: bool


def compute_coverage(cases, assignments):
    agg = {}   # (instrument, facility) -> [done, partial]
    for c in cases:
        d = agg.setdefault((c.instrument, c.facility), [0, 0])
        if c.disposition == "complete":
            d[0] += 1
        else:
            d[1] += 1
    # include assigned facilities even with zero cases synced
    keys = set(agg) | set(assignments)
    rows = []
    for k in sorted(keys):
        inst, fac = k
        done, partial = agg.get(k, [0, 0])
        a = assignments.get(k)
        target = a.target if a else 0
        rows.append(CoverageRow(
            instrument=inst, facility=fac,
            enumerator_id=a.enumerator_id if a else "(unassigned)",
            done=done, partial=partial, target=target,
            remaining=max(target - done, 0), behind=done < target))
    return rows
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_coverage.py -q`
Expected: PASS.

---

### Task 4: Data-quality flag rules (the 5-rule set)

**Files:**
- Create: `deliverables/CSWeb/supervisor-app/qa_rules.py`
- Create: `deliverables/CSWeb/supervisor-app/tests/test_qa_rules.py`

**Interfaces:**
- Consumes: `Case` (Task 1).
- Produces: `Flag` dataclass `(case_key:str, facility:str, rule:str, detail:str)`; `run_rules(cases:list[Case], today:str) -> list[Flag]`. `today` is `YYYYMMDD` (passed in, not read from the clock, so tests are deterministic). Rules: `no_gps`, `no_photo_completed`, `stuck_partial` (partial/in_progress AND `final_visit_date` > 2 days before `today`), `disposition_mismatch` (complete but `answers_present is False`), `consent_contradiction` (`result_code` is a withdraw/refusal code AND `answers_present is True`).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_qa_rules.py
from case_model import Case
from qa_rules import run_rules

def _c(**kw):
    base = dict(instrument="F3", case_key="010280001001", facility="01-02-800-01",
                enumerator_name="x", disposition="complete", result_code="1",
                has_gps=True, has_photo=True, final_visit_date="20260621",
                answers_present=True)
    base.update(kw)
    return Case(**base)

def test_no_gps_flag():
    flags = run_rules([_c(has_gps=False)], today="20260621")
    assert any(f.rule == "no_gps" for f in flags)

def test_no_photo_on_completed_flag():
    flags = run_rules([_c(has_photo=False, disposition="complete")], today="20260621")
    assert any(f.rule == "no_photo_completed" for f in flags)

def test_partial_without_photo_is_not_flagged_for_photo():
    flags = run_rules([_c(has_photo=False, disposition="partial", result_code="6")], today="20260621")
    assert not any(f.rule == "no_photo_completed" for f in flags)

def test_stuck_partial_flag():
    flags = run_rules([_c(disposition="in_progress", final_visit_date="20260618")], today="20260621")
    assert any(f.rule == "stuck_partial" for f in flags)

def test_disposition_mismatch_flag():
    flags = run_rules([_c(disposition="complete", answers_present=False)], today="20260621")
    assert any(f.rule == "disposition_mismatch" for f in flags)

def test_consent_contradiction_flag():
    flags = run_rules([_c(result_code="6", disposition="partial", answers_present=True)], today="20260621")
    assert any(f.rule == "consent_contradiction" for f in flags)

def test_clean_case_no_flags():
    assert run_rules([_c()], today="20260621") == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_qa_rules.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'qa_rules'`.

- [ ] **Step 3: Write the implementation**

```python
# qa_rules.py
"""Five data-quality rules over normalized Case records → a flag worklist (PII-light)."""
from dataclasses import dataclass
from datetime import date

# Withdraw / refusal result codes per instrument (consent refusal == these codes).
WITHDRAW_CODES = {"F1": {"3"}, "F3": {"6"}, "F4": {"4"}}   # F1 Refused=3; F3/F4 Withdraw
STUCK_DAYS = 2


@dataclass
class Flag:
    case_key: str
    facility: str
    rule: str
    detail: str


def _days_between(yyyymmdd, today):
    try:
        a = date(int(yyyymmdd[0:4]), int(yyyymmdd[4:6]), int(yyyymmdd[6:8]))
        b = date(int(today[0:4]), int(today[4:6]), int(today[6:8]))
        return (b - a).days
    except (ValueError, IndexError):
        return 0


def run_rules(cases, today):
    flags = []
    for c in cases:
        if not c.has_gps:
            flags.append(Flag(c.case_key, c.facility, "no_gps", "no GPS fix"))
        if c.disposition == "complete" and not c.has_photo:
            flags.append(Flag(c.case_key, c.facility, "no_photo_completed",
                              "Completed but no verification photo"))
        if c.disposition in ("partial", "in_progress") and c.final_visit_date \
                and _days_between(c.final_visit_date, today) > STUCK_DAYS:
            flags.append(Flag(c.case_key, c.facility, "stuck_partial",
                              f"partial > {STUCK_DAYS} days (last visit {c.final_visit_date})"))
        if c.disposition == "complete" and not c.answers_present:
            flags.append(Flag(c.case_key, c.facility, "disposition_mismatch",
                              "Completed but the opening question is blank"))
        if c.result_code in WITHDRAW_CODES.get(c.instrument, set()) and c.answers_present:
            flags.append(Flag(c.case_key, c.facility, "consent_contradiction",
                              "Withdraw/Refused but answers are present"))
    return flags
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_qa_rules.py -q`
Expected: PASS (7 passed).

---

### Task 5: Partials panel

**Files:**
- Create: `deliverables/CSWeb/supervisor-app/partials.py`
- Create: `deliverables/CSWeb/supervisor-app/tests/test_partials.py`

**Interfaces:**
- Consumes: `Case` (Task 1).
- Produces: `PartialRow` dataclass `(instrument:str, case_key:str, facility:str, reason:str)`; `list_partials(cases:list[Case]) -> list[PartialRow]`. Includes every case whose `disposition != "complete"`. `reason` = a human label from disposition + result code (e.g. "Withdrew", "Postponed", "In progress — no disposition").

- [ ] **Step 1: Write the failing test**

```python
# tests/test_partials.py
from case_model import Case
from partials import list_partials

def _c(disp, result):
    return Case("F3", "010280001001", "01-02-800-01", "x", disp, result, False, False, "20260620", False)

def test_partials_lists_noncomplete_with_reasons():
    cases = [_c("complete", "1"), _c("partial", "6"), _c("partial", "3"), _c("in_progress", "")]
    rows = list_partials(cases)
    assert len(rows) == 3
    reasons = {r.reason for r in rows}
    assert "Withdrew" in reasons
    assert "Postponed" in reasons
    assert any("In progress" in r for r in reasons)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_partials.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'partials'`.

- [ ] **Step 3: Write the implementation**

```python
# partials.py
"""The #561 panel: every non-complete case with a human-readable disposition reason."""
from dataclasses import dataclass

# Result-code -> label, per instrument (matches ENUM_RESULT_OPTIONS_* in cspro_helpers.py).
RESULT_LABELS = {
    "F1": {"2": "Postponed", "3": "Refused", "4": "Incomplete"},
    "F3": {"3": "Postponed", "4": "Incomplete", "6": "Withdrew"},
    "F4": {"2": "Postponed", "3": "Incomplete", "4": "Withdrew"},
}


@dataclass
class PartialRow:
    instrument: str
    case_key: str
    facility: str
    reason: str


def _reason(case):
    label = RESULT_LABELS.get(case.instrument, {}).get(case.result_code)
    if label:
        return label
    if case.disposition == "in_progress":
        return "In progress — no disposition (e.g. force-quit)"
    return "Partial"


def list_partials(cases):
    return [PartialRow(c.instrument, c.case_key, c.facility, _reason(c))
            for c in cases if c.disposition != "complete"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_partials.py -q`
Expected: PASS.

---

### Task 6: HTML report renderer (PII-light)

**Files:**
- Create: `deliverables/CSWeb/supervisor-app/report_html.py`
- Create: `deliverables/CSWeb/supervisor-app/tests/test_report_html.py`

**Interfaces:**
- Consumes: `CoverageRow` (Task 3), `Flag` (Task 4), `PartialRow` (Task 5).
- Produces: `render_report(coverage:list[CoverageRow], partials:list[PartialRow], flags:list[Flag], cluster:str, generated:str) -> str` (a complete HTML document string). Three `<section>`s in order: Coverage, Partials, Flags. PII-light: must contain case keys / facility / enumerator_id / status / flag reasons only.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_report_html.py
from coverage import CoverageRow
from partials import PartialRow
from qa_rules import Flag
from report_html import render_report

def test_report_has_three_panels_and_is_pii_light():
    cov = [CoverageRow("F3", "01-02-800-01", "se-004", 8, 1, 10, 2, True)]
    par = [PartialRow("F3", "010280001002", "01-02-800-01", "Withdrew")]
    fl = [Flag("010280001007", "01-02-800-01", "no_gps", "no GPS fix")]
    html = render_report(cov, par, fl, cluster="01028", generated="2026-06-21 22:10")
    assert "Coverage vs plan" in html and "Partials" in html and "Data-quality flags" in html
    assert "se-004" in html and "8" in html and "Withdrew" in html and "no GPS fix" in html
    # PII-light: a respondent name must never appear (enumerator NAME is not passed in)
    assert "Juan Dela Cruz" not in html

def test_empty_inputs_render_zero_not_error():
    html = render_report([], [], [], cluster="x", generated="t")
    assert "Coverage vs plan" in html   # renders, no crash
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_report_html.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'report_html'`.

- [ ] **Step 3: Write the implementation**

```python
# report_html.py
"""Render the 3-panel Supervisor-QA report as one self-contained HTML file.

PII-light by construction: only case keys, facility, enumerator IDs, statuses and
flag reasons are passed in — never names or answer values.
"""
from html import escape

_CSS = """body{font:14px system-ui,Arial;margin:24px;color:#1a1a1a}
h1{font-size:20px} h2{font-size:16px;margin-top:28px;border-bottom:2px solid #ccc}
table{border-collapse:collapse;margin-top:8px} td,th{border:1px solid #bbb;padding:4px 10px;text-align:left}
.behind{color:#b00;font-weight:bold} .muted{color:#777}"""


def _coverage_tbl(rows):
    if not rows:
        return "<p class=muted>No coverage data (no cases / no assignment lookup).</p>"
    out = ["<table><tr><th>Instr</th><th>Facility</th><th>Enumerator</th>"
           "<th>Done</th><th>Partial</th><th>Target</th><th>Remaining</th></tr>"]
    for r in rows:
        cls = " class=behind" if r.behind else ""
        out.append(f"<tr{cls}><td>{escape(r.instrument)}</td><td>{escape(r.facility)}</td>"
                   f"<td>{escape(r.enumerator_id)}</td><td>{r.done}</td><td>{r.partial}</td>"
                   f"<td>{r.target}</td><td>{r.remaining}</td></tr>")
    out.append("</table>")
    return "".join(out)


def _partials_tbl(rows):
    if not rows:
        return "<p class=muted>No partial / incomplete cases.</p>"
    out = ["<table><tr><th>Instr</th><th>Case</th><th>Facility</th><th>Reason</th></tr>"]
    for r in rows:
        out.append(f"<tr><td>{escape(r.instrument)}</td><td>{escape(r.case_key)}</td>"
                   f"<td>{escape(r.facility)}</td><td>{escape(r.reason)}</td></tr>")
    out.append("</table>")
    return "".join(out)


def _flags_tbl(flags):
    if not flags:
        return "<p class=muted>No data-quality flags.</p>"
    out = ["<table><tr><th>Case</th><th>Facility</th><th>Flag</th><th>Detail</th></tr>"]
    for f in flags:
        out.append(f"<tr><td>{escape(f.case_key)}</td><td>{escape(f.facility)}</td>"
                   f"<td>{escape(f.rule)}</td><td>{escape(f.detail)}</td></tr>")
    out.append("</table>")
    return "".join(out)


def render_report(coverage, partials, flags, cluster, generated):
    return (f"<!doctype html><html><head><meta charset=utf-8>"
            f"<title>Supervisor-QA — {escape(cluster)}</title><style>{_CSS}</style></head><body>"
            f"<h1>Supervisor-QA Report — {escape(cluster)} — {escape(generated)}</h1>"
            f"<h2>Coverage vs plan</h2>{_coverage_tbl(coverage)}"
            f"<h2>Partials / incomplete (#561)</h2>{_partials_tbl(partials)}"
            f"<h2>Data-quality flags</h2>{_flags_tbl(flags)}"
            f"</body></html>")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_report_html.py -q`
Expected: PASS.

---

### Task 7: CLI entry + end-to-end integration

**Files:**
- Create: `deliverables/CSWeb/supervisor-app/supervisor_qa_report.py`
- Create: `deliverables/CSWeb/supervisor-app/tests/test_cli.py`
- Create: `deliverables/CSWeb/supervisor-app/tests/fixtures/f4_sample.csv`

**Interfaces:**
- Consumes: `load_cases` (T1), `load_assignments` (T2), `compute_coverage` (T3), `run_rules` (T4), `list_partials` (T5), `render_report` (T6).
- Produces: a CLI `python supervisor_qa_report.py --exports <dir> --assignments <csv> --out <html> [--cluster <name>] [--today YYYYMMDD]`. It reads `<dir>/F1.csv`, `<dir>/F3.csv`, `<dir>/F4.csv` if present (skips missing with a note), and a `build_report(export_dir, assignments_csv, cluster, today)` function returning the HTML string.

- [ ] **Step 1: Write the F4 fixture** `tests/fixtures/f4_sample.csv`:

```csv
QUESTIONNAIRE_NUMBER,HH_GPS_LATITUDE,VERIFICATION_PHOTO_FILENAME,ENUM_RESULT_FINAL_VISIT,CASE_DISPOSITION,Q1_IS_HH_HEAD,DATE_FINAL_VISIT,ENUMERATOR_S_NAME
010280002001,14.6,case-x.jpg,1,1,1,20260620,Ana Cruz
010280002002,,,4,2,1,20260619,Ben Lim
```

- [ ] **Step 2: Write the failing integration test**

```python
# tests/test_cli.py
import os, shutil
from supervisor_qa_report import build_report

HERE = os.path.dirname(__file__)
FIX = os.path.join(HERE, "fixtures")

def test_build_report_combines_instruments(tmp_path):
    exp = tmp_path / "exports"
    exp.mkdir()
    shutil.copy(os.path.join(FIX, "f3_sample.csv"), exp / "F3.csv")
    shutil.copy(os.path.join(FIX, "f4_sample.csv"), exp / "F4.csv")
    assign = tmp_path / "a.csv"
    assign.write_text("ENUMERATOR_ID,FACILITY_CODE,INSTRUMENT,TARGET_COUNT\n"
                      "se-004,01-02-800-01,F3,10\nse-050,01-02-800-02,F4,5\n", encoding="utf-8")
    html = build_report(str(exp), str(assign), cluster="01028", today="20260621")
    assert "Coverage vs plan" in html
    assert "Withdrew" in html          # F3 case 002 + F4 case 002
    assert "se-004" in html and "se-050" in html
    assert "Juan Dela Cruz" not in html and "Ana Cruz" not in html   # PII-light
```

- [ ] **Step 3: Run test to verify it fails**

Run: `python -m pytest tests/test_cli.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'supervisor_qa_report'`.

- [ ] **Step 4: Write the implementation**

```python
# supervisor_qa_report.py
"""Supervisor-QA report — read CSV exports of F1/F3/F4 + the assignment lookup,
write one PII-light HTML report (coverage / partials / flags). Read-only.

Usage:
  python supervisor_qa_report.py --exports ./exports --assignments ./assignments.csv \
      --out ./supervisor-qa.html --cluster 01028 --today 20260621

Expects ./exports/F1.csv, F3.csv, F4.csv (any subset). Missing instruments are skipped.
Run tests: python -m pytest -q
"""
import argparse
import os
from case_model import load_cases
from assignment import load_assignments
from coverage import compute_coverage
from qa_rules import run_rules
from partials import list_partials
from report_html import render_report


def build_report(export_dir, assignments_csv, cluster, today):
    cases = []
    for inst in ("F1", "F3", "F4"):
        path = os.path.join(export_dir, f"{inst}.csv")
        if os.path.exists(path):
            cases.extend(load_cases(path, inst))
    assignments = load_assignments(assignments_csv) if os.path.exists(assignments_csv) else {}
    coverage = compute_coverage(cases, assignments)
    flags = run_rules(cases, today=today)
    partials = list_partials(cases)
    return render_report(coverage, partials, flags, cluster=cluster,
                         generated=f"{today} (cases: {len(cases)})")


def main():
    ap = argparse.ArgumentParser(description="Supervisor-QA report (read-only).")
    ap.add_argument("--exports", required=True, help="dir with F1.csv/F3.csv/F4.csv")
    ap.add_argument("--assignments", required=True, help="assignment/target CSV")
    ap.add_argument("--out", required=True, help="output HTML path")
    ap.add_argument("--cluster", default="(cluster)")
    ap.add_argument("--today", required=True, help="YYYYMMDD (stuck-partial reference)")
    args = ap.parse_args()
    html = build_report(args.exports, args.assignments, args.cluster, args.today)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_cli.py -q`
Expected: PASS.

- [ ] **Step 6: Run the full suite**

Run: `cd deliverables/CSWeb/supervisor-app && python -m pytest -q`
Expected: all tests pass (Tasks 1–7).

---

### Task 8: Supervisor SOP + CSWeb role config + tablet review (C1 + C5, docs only)

**Files:**
- Create: `deliverables/CSWeb/supervisor-app/README.md`

**Interfaces:** none (documentation). Captures the non-code components C1 (CSWeb GET role + PII confirm) and C5 (tablet review setup), and the laptop run procedure.

- [ ] **Step 1: Write `README.md`** with these exact sections:

````markdown
# Supervisor App — Phase 1 (Review Layer)

Read-only field QA over pulled F1/F3/F4 cases. No write-back; enumerators keep
syncing directly to CSWeb (Phase 1). See the spec:
`docs/superpowers/specs/2026-06-20-supervisor-app-design.md`.

## C1 — CSWeb supervisor role (one-time, server admin)
Extend the `supervisor-monitor` role (see
`deliverables/CSWeb/CSWeb-User-Management-and-RBAC-Provisioning-Pack.md`) with
**dictionary GET / down-sync** on `FACILITYHEADSURVEY_DICT`, `PATIENTSURVEY_DICT`,
`HOUSEHOLDSURVEY_DICT`. PII NOTE: pulling cases exposes respondent data; the report
is PII-light, but the case-level spot-check shows PII — confirm supervisors are
authorized for QA spot-check before enabling.

## C5 — Tablet review (on-site, thin)
On the supervisor tablet, CSEntry with the GET-enabled supervisor account:
1. Sync → CSWeb → GET (pull latest).
2. Open the app in review mode; the case list shows **partial cases with a red bar /
   distinct icon**. Open a case read-only to spot-check.
(On-site review needs signal; otherwise do the laptop pass at base. Phase 2's
Bluetooth hub removes the signal dependency.)

## Evening laptop run (the report engine)
1. **Pull**: Data Manager → GET F1/F3/F4 onto the laptop.
2. **Export to CSV**: in the desktop **Data Viewer**, open each instrument's data and
   `File → Export → CSV`, saving as `exports/F1.csv`, `exports/F3.csv`, `exports/F4.csv`
   (the CSV headers are the dictionary item names — the report reads them directly).
3. **Maintain** `assignments.csv` from `assignments.example.csv` (one row per
   enumerator/facility/instrument with the target count).
4. **Run**:
   ```
   python supervisor_qa_report.py --exports ./exports --assignments ./assignments.csv \
       --out ./supervisor-qa.html --cluster <cluster> --today <YYYYMMDD>
   ```
5. **Review** `supervisor-qa.html`: coverage vs plan, partials (#561), QA flags. For any
   flagged/partial case, open it read-only in Data Viewer (the only PII step) and chase
   the enumerator by radio. Partial-case visibility note: CSWeb's web dashboard does NOT
   show partial vs complete — this report and the Data Viewer "Partial Cases Only" filter
   do.

## Notes
- Read-only: the tool never writes case data.
- Phase-2 compatible: it reads CSV exports regardless of how cases arrived.
- Stuck-partial threshold is 2 days; edit `STUCK_DAYS` in `qa_rules.py` to change.
````

- [ ] **Step 2: Verify the README references match the code** — confirm the run command, file names (`exports/F{1,3,4}.csv`, `assignments.csv`), and `STUCK_DAYS` all match Tasks 1–7. Leave the working tree changed (Carl commits).

---

## Self-Review

**1. Spec coverage:**
- C1 (CSWeb GET role + PII) → Task 8 README §C1. ✓
- C2 (report engine: coverage / partials / flags, PII-light, reads pulled cases) → Tasks 1,3,4,5,6,7. ✓
- C3 (assignment/target lookup) → Task 2. ✓
- C4 (5-rule QA set) → Task 4 (no_gps, no_photo_completed, stuck_partial, disposition_mismatch, consent_contradiction). ✓
- C5 (tablet review setup) → Task 8 README §C5. ✓
- Read-only / Phase-2 compatible / PII-light → Global Constraints + tested in Tasks 6,7. ✓
- CASE_DISPOSITION dependency → consumed in Task 1 `_disposition`; F1 fallback handled. ✓

**2. Placeholder scan:** No "TBD"/"implement later". The two data-derived values (F4 `gps_lat` name; whether to read `.csdb` directly later) are concrete grep/SOP steps, not placeholders.

**3. Type consistency:** `Case` fields (Task 1) are used unchanged in Tasks 3/4/5; `CoverageRow`/`Flag`/`PartialRow` names match between producers (Tasks 3/4/5) and the renderer (Task 6) and CLI (Task 7). `run_rules(cases, today=...)` keyword matches Task 4 ↔ Task 7. `render_report(...)` signature matches Task 6 ↔ Task 7.

**Note (F1 break-off gap, out of scope):** F1 has no `CASE_DISPOSITION`/`BREAKOFF` (Cluster 5 covered F3+F4). The report derives F1 completeness from `ENUM_RESULT_FINAL_VISIT`. If ASPSI later wants F1 break-off too, fan out the Cluster-5 pattern to F1 first (separate task) — the report already handles F1 via the result-code fallback.
