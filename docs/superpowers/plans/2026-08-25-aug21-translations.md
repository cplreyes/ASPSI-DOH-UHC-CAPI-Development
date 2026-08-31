# Aug-21 Translations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring all four UHC Year-2 CAPI instruments (F1/F3/F4 CSPro, F2 PWA) onto ASPSI's revised Deliverable-2 Aug-21 questionnaires — English aligned to the paper and all seven dialect maps re-imported from the 28 Aug-21 translated PDFs — shipped per instrument with byte-verified, tablet-proven evidence.

**Architecture:** Day-0 builds the shared tooling once (a repeatable build-vs-Aug-21-English delta gate, a name-scoped paper extractor, the `apply_aug21.py` merge tool with `aug21-overrides.json`, the notes/ICF layers, and the F2 flat-map variant). Then four independent waves ship in order F1 → F2 → F4 → F3; inside every wave the sequence is fixed: align English to the paper → extract + merge translations → build → static/compile gates → deploy → byte-verify + device evidence → patch note. Wave 5 closes out with the coverage table, the translator worklist and the status hand-off to ASPSI.

**Tech Stack:** Python 3.13 (PyMuPDF, pytest), CSPro 8 generators (generate_dcf/apc/fmf/qsf.py + cspro_helpers), pywinauto Designer driver, CSWeb auto_deploy, F2 PWA (TypeScript/Vite/vitest/Playwright), deploy-f2-pwa.ps1

**Spec:** docs/superpowers/specs/2026-08-25-aug21-translations-design.md

## Global Constraints

- Scope: the Aug-21 revised instruments (English + 7 translations × F1/F2/F3/F4) — English alignment and translation import only; runtime error messages (`messages.<loc>.json`) are OUT OF SCOPE; the spec's Open items defer the ~590-string translator sheet to *a separate request, not this build*, so Task 46 (export-only sheet) is OPTIONAL and skipped by default — nothing is wired either way.
- Conflicts rule: Aug-21 wins over June-5/Aug-17 values on every key, EXCEPT keys listed in `data/translations-official/aug21-overrides.json` (every override carries a reason); overrides are added only for defects the Aug-21 extract actually re-introduces.
- Versions: F1 4.1.0 / F2 m4 (`LOCAL_SPEC_VERSION = '2026-08-2x-m4'`) / F4 3.2.0 / F3 6.1.0 (minor; 97.x/115.x already exist, no data-shape change).
- Spec erratum (known, read before Task 42): the spec's *Deployment & cutover* bullet still says "F3's note carries the MAJOR/data-shape warning verbatim from the F1 v4.0.0 note" — that sentence predates the 2026-08-25-evening correction of Decision 4 (F3 = 6.1.0 MINOR, no data-shape change). This plan follows the corrected Decision 4; Task 42 Step 4 replaces the stale spec sentence with "F3's note states no codes changed" so spec and plan agree.
- PSA submission set stays frozen at tag `capi-psa-2026-08-20`; everything shipped here is DEV channel.
- `raw/` is immutable and gitignored — the Aug-21 PDFs under `raw/Survey-Instruments-2026-08-21/` are read-only inputs.
- Generator-first: never hand-edit a `.dcf` / `.apc` / `.fmf` / `.qsf`; every artefact is regenerated from `generate_*.py`.
- Translation maps are `name-scoped-v2` (`item:` / `vs:` / `val:` keys); `apply_translations()` SystemExits on any key without `:`.
- English alignment precedes extraction inside every wave (the extractor anchors on the BUILD's English; a stale label yields nothing or bleeds).
- No git commits for CSPro-side changes (generators, maps, tools, patch notes) — Carl commits; the only sanctioned commits are evidence PNG/README folders under `docs/uat-fix-evidence/` and the F2 PWA tree (required by `deploy-f2-pwa.ps1`'s HEAD == origin/main guard).

### Reconciled names used throughout this plan (single source of truth)

| thing | name used everywhere below |
|---|---|
| CSPro extractor | `deliverables/CSPro/data/translations-official/anchor_extract.py --source DIR --instrument F<n> (--dcf PATH or --generator F3) --out DIR [--locales A,B] [--live-maps DIR]` |
| F2 extractor | `deliverables/CSPro/data/translations-official/anchor_extract_f2.py --source DIR --english-strings PATH --out DIR` |
| extractor output root | `deliverables/CSPro/data/translations-official/out-aug21/<INST>/{loc}.json`, `{loc}_flagged.json`, `QA-REPORT.md` (gitignored) |
| CSPro merge | `apply_aug21.py [--apply] [--only F<n>] [--extract DIR] [--unmatched] [--seed FINDINGS] [--compare-findings PRE POST]`; overrides always read from `aug21-overrides.json` beside it (no `--overrides` flag); dry-run report `aug21_apply_diff.json` |
| F2 apply | `deliverables/F2/PWA/app/scripts/apply-paper-translations.py [--extract-dir DIR] [--overrides PATH] [--apply] [--report PATH]`; report `out-aug21/F2/apply-report.json` |
| overrides file | `deliverables/CSPro/data/translations-official/aug21-overrides.json` — `{F1/F3/F4: {key: {keep, reason}}, F2: {loc: {English: {keep: text or null, reason}}}}`; notes/ICF keys `note:<key>:<LOC>`, `icf:<p>:<i>:<LOC>` (`keep: ""` = render English); F2 `keep: null` = never write the key |
| English delta gate | `aug21_english_delta.py [--only F<n>] [--out DIR]` → `out-delta/<inst>_english_delta.json` |
| F3 anchors | always `--generator F3` (pre-apply generator dictionary), never the written `PatientSurvey.dcf` |
| byte-verify | `deliverables/CSPro/aug17-tools/byte_verify_aug21.py <INST> <zip> <maps_dir> <out.txt> [--version vX.Y.Z] [--deploy-shot SRC DST]` (PROBE_KEYS for F1/F3/F4) |
| CSWeb box | `root@207.148.65.115` (no `csweb` ssh alias exists); packages under `/opt/app/lamp/www/csweb/files/apps/` |
| evidence folder | `docs/uat-fix-evidence/<EVDATE>-aug21-translations/{F1,F2,F4,F3}/` (`EVDATE` = real deploy date of the wave, never the literal `2026-08-2x`; upper-case instrument subfolders) |
| patch notes | `deliverables/CSPro/patch-notes/` (created once; left uncommitted for Carl) |
| F2 stamp | `LOCAL_SPEC_VERSION = '2026-08-2x-m4'` (2x = real apply date; test regex `^2026-08-\d{2}-m4$`) |
| F2 override shape | locale-nested, `keep: null` suppresses a write (the `drop: true` spelling is NOT used) |
| patch-note file names | `deliverables/CSPro/patch-notes/<EVDATE>-<inst>-v<ver>-aug21-translations.md` — lower-case instrument, `v` prefix: `<EVDATE>-f1-v4.1.0-aug21-translations.md`, `<EVDATE>-f2-m4-aug21-translations.md` (spec stamp, no `v`), `<EVDATE>-f4-v3.2.0-aug21-translations.md`, `<EVDATE>-f3-v6.1.0-aug21-translations.md`; a draft started before the deploy date is known is `draft-<inst>-…` and is renamed on save; working notes that are not Slack patch notes carry no date (`aug21-day0.md`, `aug21-notes-layer.md`) |
| F2 consent extractor | `deliverables/CSPro/data/translations-official/extract_icf_f2.py --source DIR --en APP/src/i18n/locales/en.ts [--out APP/src/i18n/locales/consent.aug21.ts] [--report PATH]` (Task 21); overrides live in the F2 locale-nested section keyed by the English paragraph |

---

## File structure

**Day-0 tooling (`deliverables/CSPro/data/translations-official/`)**
- Create `aug21_english_delta.py` — build-vs-paper English gate (Task 0)
- Create `test_aug21_english_delta.py` (Task 0)
- Create `anchor_extract.py` — committed name-scoped extractor (Task 1)
- Create `test_anchor_extract.py` (Tasks 1–2)
- Create `aug21_overrides.py` + `aug21-overrides.json` — override schema/validator (Task 3)
- Create `apply_aug21.py` — merge tool (Tasks 4–7)
- Create `test_apply_aug21.py` (Tasks 3–7)
- Create `run_aug21_gates.ps1` — post-merge gate wrapper (Task 7)
- Modify `extract_notes.py` — `--source/--provenance aug21`, `merge_notes`, widened const regex (Task 8)
- Create `extract_icf.py` + `icf.json` + `icf-report.json` (Task 10)
- Create `test_notes_icf_aug21.py` (Tasks 8–11)
- Create `anchor_extract_f2.py` + `test_anchor_extract_f2.py` (Task 14)
- Create `extract_icf_f2.py` + `test_extract_icf_f2.py` — F2 consent-screen extractor (Task 21)
- Create `test_aug21_f4_extract.py` (Tasks 27–28)
- Create `export_worklist.py` (Task 45)
- Modify `README.md` — Aug-21 extractor entry (Task 1)
- Modify `notes.json` (Tasks 8, 29), `aug21-overrides.json` (Tasks 6, 10, 17, 22, 28, 40)
- Modify repo-root `.gitignore` — `out-delta/`, `out-aug21/`, `aug21_apply_diff.json`, `aug21_pre_findings.json`, `aug21_post_findings.json`, `text-aug21/` (Tasks 0, 7, 8)

**Shared CSPro helpers / automation**
- Modify `deliverables/CSPro/icf_content.py` — per-language screens (Task 9)
- Create `deliverables/CSPro/automation/aug21_check_gates.py` (Task 25)
- Create `deliverables/CSPro/automation/translation_coverage.py` (Task 44)
- Create `deliverables/CSPro/automation/aug21_coverage_baseline.json` — wave-start coverage before-values (Task 44)
- Create `deliverables/CSPro/automation/export_messages_sheet.py` (Task 46 — OPTIONAL, deferred per spec Open items; skipped unless Carl asks)
- Create `deliverables/CSPro/automation/scenarios/f3_aug21_bill_detail_war.txt`, `f3_aug21_bill_detail_hil.txt` (Tasks 39, 41)
- Create `deliverables/CSPro/aug17-tools/byte_verify_aug21.py` + `test_aug21_f1.py` (Tasks 16–19)
- Modify `deliverables/CSPro/versions.json` via `stamp_version.py` only (Tasks 18, 30, 42)

**F1**
- Modify `deliverables/CSPro/F1/generate_dcf.py` (Q75), `generate_qsf.py` (OVERRIDES, `_CAPITATION_RE`) (Tasks 11, 16)
- Modify `deliverables/CSPro/F1/translations/{fil,bcl,bis,ceb,war,hil,ilo}.json` via `apply_aug21.py --apply` only (Task 17)
- Regenerate `FacilityHeadSurvey.dcf/.apc/.fmf/.qsf` (Task 18)

**F2 PWA (`deliverables/F2/PWA/app/`)**
- Create `scripts/lib/english-strings.ts` + `.test.ts` + snapshot (Task 12)
- Create `scripts/dump-english-strings.ts`; modify `package.json` (`dump:english`); create `spec/english-strings.json` (Task 13)
- Create `scripts/apply-paper-translations.py` + `scripts/test_apply_paper_translations.py` (Task 15)
- Create `scripts/lib/apply-translations.aug21.test.ts`, `scripts/f2-coverage.py` (Task 22)
- Modify `spec/translations/{fil,ceb,bis,ilo,hil,war,bcl}.json` via the apply script only; regenerate `src/generated/items.ts` (Task 22)
- Modify `src/lib/draft.ts` (`LOCAL_SPEC_VERSION` m4); create `src/lib/draft.specversion.test.ts` (Task 23)
- Create (generated) `src/i18n/locales/consent.aug21.ts`; modify `src/i18n/locales/{fil,ceb,bis,ilo,hil,war,bcl}.ts` (one import + one spread line each); create `src/i18n/consent.aug21.test.ts`; modify `e2e/locale-shots.spec.ts` (consent assertion) (Task 21)

**F4**
- Modify `deliverables/CSPro/F4/generate_dcf.py` (Q30/Q35/Q36/Q40/Q67), `generate_qsf.py` (gate constants, `INSTRUCTIONS_BY_NAME`, `note_html`, OVERRIDES) (Tasks 11, 24, 25)
- Create `deliverables/CSPro/F4/test_aug21_f4.py` (Tasks 24–34)
- Modify `deliverables/CSPro/F4/translations/*.json` via `apply_aug21.py --apply` only (Task 28)

**F3**
- Modify `deliverables/CSPro/F3/generate_dcf.py` (Q47/Q69/Q94/Q96/Q98, 97.2/115.x labels, `_FACILITY_NEUTRAL`), `generate_qsf.py` (`INSTRUCTIONS_BY_NAME`, OVERRIDES) (Tasks 11, 36–38)
- Create `deliverables/CSPro/F3/test_aug21_labels.py` + `test_fixtures/{aug21_vs_codes_before.json,r25_baseline_f3.txt,aug21_coverage_after_align.txt}` (Tasks 35, 39)
- Create `deliverables/CSPro/F3/PatientSurvey_desktest_HIL.pff` (Task 41)
- Modify `deliverables/CSPro/F3/translations/*.json` via `apply_aug21.py --apply` only (Task 40)

**Evidence, notes, close-out**
- Create `docs/uat-fix-evidence/<EVDATE>-aug21-translations/{F1,F2,F4,F3}/` (+ `README.md`, PNGs, `byte-verify.txt`) (Tasks 19, 20, 23, 32, 33, 42, 43, 47)
- Create `deliverables/CSPro/patch-notes/*.md` (Tasks 0, 8, 17, 20, 23, 34, 42, 47) — Slack patch notes follow the `<EVDATE>-<inst>-v<ver>-aug21-translations.md` pattern from the Reconciled-names table
- Create `deliverables/CSPro/TRANSLATION-STATUS-2026-08-28.md` (Task 44)
- Create `deliverables/CSPro/translator-worklist-aug21.{xlsx,csv}` (Task 45)
- Create `deliverables/CSPro/runtime-messages-for-translation.csv` (Task 46 — OPTIONAL, only if Carl asks)
- Create `wiki/sources/Source - Revised Deliverable 2 Translated Questionnaires (Aug 21).md`; modify `wiki/entities/ASPSI.md`, `wiki/concepts/CSPro.md`, `log.md` (Task 47)

---

## Day 0 (part 1): English baseline delta gate + name-scoped paper extractor

Scope of this section: Task 0 of the spec (repeatable build-vs-Aug-21-English delta), then the extractor refactor the spec's Day-0 table calls for (`anchor_extract.py` committed under `data/translations-official/`, argparse'd, emitting `item:`/`vs:`/`val:` keys directly), with pytest coverage. Nothing here writes into a build or a live map; every output lands in gitignored `out-*/` folders or the pytest tmp dir.

Conventions used throughout: Python is `python` (3.13, Windows). **Every gate command in this section is PowerShell, run from the repo root** `C:\Users\analy\Documents\analytiflow\1_Projects\ASPSI-DOH-CAPI-CSPro-Development`, with `$env:PYTHONIOENCODING='utf-8'` set once per shell because the reports print Filipino text; inline scripts use a PowerShell here-string piped to `python -` (never a bash heredoc). Paths are repo-root-relative. `raw/` is read-only. The June-5 extractor at `deliverables/CSPro/translations-paper-extract/anchor_extract.py` stays untouched (gitignored, on disk); the new one is a committed sibling that imports nothing from it — the reusable functions are copied verbatim so the committed tool has no gitignored dependency.

Two facts established while reviewing this section that shape the tasks below (both verified against the real files):

- The Aug-21 English papers are not cleanly numbered: F1 prints the Result-of-Visit list `1. Completed / 2. Postponed / 3. Refused / 4. Incomplete` before Q1; F2 numbers the employment-type definitions; F3 prints `97.1 Other than…` with **no dot** but `115.1. Other than…` with one. A first-occurrence, dot-required parser mis-scores every instrument. The gate therefore keeps **all** occurrences per number and counts a match when any occurrence starts with the build stem; the wave rule is "diffs limited to the documented artefact list", not "diffs 0".
- For F3 the written `PatientSurvey.dcf` is post-`_neutralise_facility_placeholder` (generate_dcf.py `main()`: build → apply_translations → neutralise → write_dcf), so its Q66/Q88/Q143/Q162/Q172 labels read "this facility" while the paper and the qsf (the thing that renders) carry `[facility_name_input]`. "Anchor on the current dcf" means "anchor on the build's English": F3 anchors come from the generator's pre-apply dictionary, not the file.

### Task 0: `aug21_english_delta.py` — repeatable build-vs-paper English gate

**Files:**
- Create: `deliverables/CSPro/data/translations-official/aug21_english_delta.py`
- Test: `deliverables/CSPro/data/translations-official/test_aug21_english_delta.py`

**Interfaces:**
- Consumes: `cspro_helpers.walk_labeled_nodes(dictionary)` (cspro_helpers.py:1126-1151) for dcf items; `fitz.open(path)[i].get_text()`; items.ts literal shape `{ id: 'Q5', section: 'A', … label: { en: '...' } }` for items and `{ id: 'Q13_1', displayNumber: 'Q13.1', section: 'B', …}` for real sub-questions (items.ts:10, :31) — sub-fields nest as `subFields: [{ id: 'Q1_1', label: …` with NO `section:` and must not count.
- Produces: `numbered_labels_dcf(dcf_path) -> dict[qnum, label]`, `numbered_labels_items_ts(path) -> dict[qnum, label]`, `paper_numbered(pdf_path) -> dict[qnum, list[str]]` (every occurrence, in page order), `compare(build, paper) -> {match, total, diffs, paper_only}`, CLI `python aug21_english_delta.py [--only F1] [--out DIR]` writing `DIR/<inst>_english_delta.json`. Wave tasks (16, 25, 38) re-run this before every extraction (spec Risks row 3).

- [ ] **Step 1: Write the failing tests** (the Q6 fixture is a real reword — "Age at last birthday" does not start with "Age in years" — so the prefix rule genuinely fails it; a second test locks the all-occurrences rule that the F1 Result-of-Visit list needs)

```python
# deliverables/CSPro/data/translations-official/test_aug21_english_delta.py
import json
from pathlib import Path

import fitz
import pytest

import aug21_english_delta as d


def make_pdf(path, lines):
    doc = fitz.open()
    page = doc.new_page()
    y = 60
    for ln in lines:
        page.insert_text((40, y), ln, fontsize=9)
        y += 14
    doc.save(str(path))
    doc.close()


def test_numbered_labels_dcf_keeps_first_label_per_qnum(tmp_path):
    dcf = {"name": "T", "levels": [{"name": "L", "records": [{"name": "R", "items": [
        {"name": "Q5_SEX", "labels": [{"text": "5. Sex at birth"}],
         "valueSets": [{"name": "Q5_SEX_VS1", "labels": [{"text": "5. Sex at birth"}],
                        "values": [{"labels": [{"text": "Male"}], "pairs": [{"value": "1"}]}]}]},
        {"name": "Q6_AGE", "labels": [{"text": "6. Age in years"}]},
        {"name": "Q6_AGE_TXT", "labels": [{"text": "6. Age — specify text"}]},
    ]}]}]}
    p = tmp_path / "t.dcf"
    p.write_text(json.dumps(dcf), encoding="utf-8")
    out = d.numbered_labels_dcf(p)
    assert out == {"5": "5. Sex at birth", "6": "6. Age in years"}


def test_numbered_labels_items_ts_skips_subfields(tmp_path):
    p = tmp_path / "items.ts"
    p.write_text(
        "{ id: 'Q4', section: 'A', label: { en: 'How old are you?', fil: 'Ilang taon?' }, "
        "subFields: [{ id: 'Q4_1', label: { en: 'Year(s)' }, kind: 'number' }] },\n"
        "{ id: 'Q5', section: 'A', label: { en: 'What is your role?' } },\n"
        "{ id: 'Q13_1', displayNumber: 'Q13.1', section: 'B', label: { en: 'If yes, why?' } },\n",
        encoding="utf-8")
    assert d.numbered_labels_items_ts(p) == {"4": "How old are you?", "5": "What is your role?",
                                             "13.1": "If yes, why?"}


def test_paper_numbered_and_compare(tmp_path):
    pdf = tmp_path / "F9-English_x_Aug21.pdf"
    make_pdf(pdf, ["5. Sex at birth", "Male  Female",
                   "6. Age at last birthday (completed years)",
                   "7. New paper-only item",
                   "97.1 Other than the expenses above",      # decimal number, NO dot (F3 layout)
                   "115.1. Other than the expenses above"])   # decimal number WITH dot
    paper = d.paper_numbered(pdf)
    assert paper["5"] == ["Sex at birth Male Female"]
    assert paper["97.1"] == ["Other than the expenses above"]
    assert paper["115.1"] == ["Other than the expenses above"]
    build = {"5": "5. Sex at birth", "6": "6. Age in years"}
    r = d.compare(build, paper)
    assert r["match"] == 1 and r["total"] == 2
    assert r["diffs"][0]["q"] == "6"
    assert r["paper_only"] == ["7", "97.1", "115.1"]


def test_compare_accepts_any_occurrence(tmp_path):
    # F1 layout: the Result-of-Visit list "1. Completed ... 4. Incomplete" precedes Q1
    pdf = tmp_path / "F9-English_x_Aug21.pdf"
    make_pdf(pdf, ["1. Completed", "2. Postponed", "1. What is your name?", "2. What is your designation?"])
    paper = d.paper_numbered(pdf)
    assert paper["1"] == ["Completed", "What is your name?"]
    r = d.compare({"1": "1. What is your name?", "2": "2. What is your designation?"}, paper)
    assert r["match"] == 2 and r["diffs"] == [] and r["paper_only"] == []
```

- [ ] **Step 2: Run tests to verify they fail** — Run: `cd deliverables\CSPro\data\translations-official; python -m pytest test_aug21_english_delta.py -q` Expected: FAIL with `ModuleNotFoundError: No module named 'aug21_english_delta'`.

- [ ] **Step 3: Write minimal implementation**

```python
#!/usr/bin/env python3
"""aug21_english_delta.py — does each build's numbered English match the Aug-21 paper?

Re-runs the 2026-08-25 measurement as a gate: for F1/F3/F4 the dcf item labels that
start with a question number; for F2 the `label: { en: ... }` of every top-level
`id: 'Qn'` / `id: 'Qn_m'` item in items.ts (nested subFields are NOT items). Paper side =
every "N. ..." / "N.m ..." line of the Aug-21 English PDF (PyMuPDF), ALL occurrences kept
because the papers re-use question numbers for option lists and definitions.
Match = ANY paper occurrence starts with the build stem (both normalised).
Writes <out>/<inst>_english_delta.json and prints one table. Nothing is modified.

    python aug21_english_delta.py                 # all four
    python aug21_english_delta.py --only F3 --out out-delta
"""
import argparse
import io
import json
import os
import re
import sys

import fitz

HERE = os.path.dirname(os.path.abspath(__file__))
CSPRO = os.path.abspath(os.path.join(HERE, "..", ".."))
REPO = os.path.abspath(os.path.join(CSPRO, "..", ".."))
sys.path.insert(0, CSPRO)
from cspro_helpers import walk_labeled_nodes  # noqa: E402

ENGLISH_DIR = os.path.join(REPO, "raw", "Survey-Instruments-2026-08-21", "English")
BUILDS = {
    "F1": os.path.join(CSPRO, "F1", "FacilityHeadSurvey.dcf"),
    "F2": os.path.join(REPO, "deliverables", "F2", "PWA", "app", "src", "generated", "items.ts"),
    "F3": os.path.join(CSPRO, "F3", "PatientSurvey.dcf"),
    "F4": os.path.join(CSPRO, "F4", "HouseholdSurvey.dcf"),
}
QNUM_LABEL = re.compile(r"^\s*(\d{1,3}(?:\.\d)?)\.?\s+(.*)$")
# integers need the dot ("1. What…"); decimals may omit it ("97.1 Other…" vs "115.1. Other…")
QNUM_LINE_INT = re.compile(r"^(\d{1,3})\.\s+(\S.*)$")
QNUM_LINE_DEC = re.compile(r"^(\d{1,3}\.\d)\.?\s+(\S.*)$")
# top-level items only: `section:` follows the id (after an optional displayNumber);
# nested subFields carry no `section:` and are skipped by construction
ITEM_RE = re.compile(
    r"\{ id: 'Q(\d{1,3}(?:_\d)?)',(?: displayNumber: '[^']*',)? section: '[A-Z]'"
    r".*?label: \{ en: '((?:[^'\\]|\\.)*)'", re.S)


def norm(s):
    s = s.replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"')
    s = re.sub(r"\[[^\]]{0,80}\]", " ", s)           # [facility_name_input], [Answer only ...]
    return " ".join(re.sub(r"[^a-z0-9' ]", " ", s.lower()).split())


def numbered_labels_dcf(dcf_path):
    d = json.load(io.open(dcf_path, encoding="utf-8"))
    out = {}
    for key, node in walk_labeled_nodes(d):
        if not key.startswith("item:") or key.endswith("_TXT"):
            continue
        labs = node.get("labels") or []
        if not labs:
            continue
        m = QNUM_LABEL.match(labs[0].get("text") or "")
        if m and m.group(1) not in out:
            out[m.group(1)] = labs[0]["text"].strip()
    return out


def numbered_labels_items_ts(path):
    src = io.open(path, encoding="utf-8").read()
    out = {}
    for m in ITEM_RE.finditer(src):
        q = m.group(1).replace("_", ".")
        if q not in out:
            out[q] = m.group(2).replace("\\'", "'").replace("\\n", " ")
    return out


def paper_numbered(pdf_path):
    """{qnum: [text of every occurrence, in page order]}."""
    doc = fitz.open(str(pdf_path))
    lines = []
    for page in doc:
        lines.extend(page.get_text().split("\n"))
    doc.close()
    out, cur = {}, None
    for ln in lines:
        ln = " ".join(ln.split())
        m = QNUM_LINE_DEC.match(ln) or QNUM_LINE_INT.match(ln)
        if m:
            cur = m.group(1)
            out.setdefault(cur, []).append(m.group(2))
        elif cur and ln:
            out[cur][-1] = out[cur][-1] + " " + ln
    return {q: [" ".join(t.split()) for t in ts] for q, ts in out.items()}


def compare(build, paper):
    diffs, match = [], 0
    for q, label in sorted(build.items(), key=lambda kv: float(kv[0])):
        stem = norm(re.sub(r"^\s*\d{1,3}(?:\.\d)?\.?\s*", "", label))
        stem = re.split(r" (?:hours|minutes|specify text)$", stem)[0]
        occ = paper.get(q)
        if not occ:
            diffs.append({"q": q, "build": label, "paper": None})
            continue
        if any(norm(p).startswith(stem[:60]) for p in occ):
            match += 1
        else:
            diffs.append({"q": q, "build": label, "paper": [p[:240] for p in occ]})
    paper_only = sorted((q for q in paper if q not in build), key=float)
    return {"match": match, "total": len(build), "diffs": diffs, "paper_only": paper_only}


def english_pdf(inst):
    names = sorted(n for n in os.listdir(ENGLISH_DIR) if n.startswith(f"{inst}-English") and n.endswith(".pdf"))
    return os.path.join(ENGLISH_DIR, names[0]) if names else None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=sorted(BUILDS))
    ap.add_argument("--out", default=os.path.join(HERE, "out-delta"))
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    print("%-4s %6s %6s %6s %10s" % ("inst", "match", "total", "diffs", "paper-only"))
    rc = 0
    for inst in (a.only,) if a.only else sorted(BUILDS):
        pdf = english_pdf(inst)
        if pdf is None:
            print(f"{inst:<4} no Aug-21 English PDF under {ENGLISH_DIR}"); rc = 1; continue
        build = numbered_labels_items_ts(BUILDS[inst]) if inst == "F2" else numbered_labels_dcf(BUILDS[inst])
        r = compare(build, paper_numbered(pdf))
        r["build"], r["paper"] = BUILDS[inst], pdf
        with io.open(os.path.join(a.out, f"{inst}_english_delta.json"), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(r, fh, ensure_ascii=False, indent=1)
        print("%-4s %6d %6d %6d %10d" % (inst, r["match"], r["total"], len(r["diffs"]), len(r["paper_only"])))
        for x in r["diffs"]:
            first = (x["paper"] or [""])[0] if isinstance(x["paper"], list) else (x["paper"] or "")
            print(f"   Q{x['q']}: build={x['build'][:80]!r}\n         paper={first[:80]!r}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests to verify they pass** — Run: `python -m pytest test_aug21_english_delta.py -q` Expected: `4 passed`.

- [ ] **Step 5: Verify/gate** — From the repo root in PowerShell:

```
$env:PYTHONIOENCODING='utf-8'
python deliverables\CSPro\data\translations-official\aug21_english_delta.py
```

The numbers printed here ARE the baseline; do not carry forward the pre-review figures (185/186 etc.), which were measured by a different method. What the review run of the un-fixed tool produced, and what the fixes above are expected to change:

| inst | un-fixed run | expected after fixes | must still appear as diffs (real rewords) | known parser artefacts to document, not fix |
|---|---|---|---|---|
| F1 | 179/186, 7 diffs | Q1-Q4 recover (all-occurrences rule) → ≈183-185/186 | Q75 | Q30.1 / Q35.2 if they remain — check whether the paper numbers them differently |
| F2 | 124/139 | total drops to the item count (≈133) once `subFields` ids are excluded; Q1-Q9 may still diff because the paper's numbered employment-type definitions are also occurrences — those recover only if one occurrence starts with the stem | none (NO English change on F2) | any residual Q1-Q9 definition-list diffs |
| F3 | 146/180, 34 diffs, paper_only 115.1/115.2 only | `paper_only` now lists **97.1 97.2 115.1 115.2**; Q1-Q9 / Q106-113 / Q131-140 recover where a second occurrence matches | Q47 (4 rows), Q66, Q69, Q88, Q94, Q96, Q98 | Q143/Q162/Q172 `[FACILITY…]` stems if `norm()`'s bracket strip does not cover them |
| F4 | 128/163, 35 diffs, 27 spurious paper_only (142-163) | spurious paper_only rows shrink to those numbers the paper really has beyond the build | Q30, Q35, Q36, Q40, Q67, Q117, Q118, Q131, Q135 | anything else — list it |

Acceptance for this step: every "must still appear" row IS listed as a diff for its instrument (if one is missing, `norm()` or the prefix rule is too lenient — tighten before trusting the waves), and every remaining diff is either in that column or written down in the artefact column of the wave note. Then confirm the output folder is ignored — the rule must go in the **repo-root** `.gitignore` (there is no `deliverables/CSPro/.gitignore`; the existing extraction rule is root `.gitignore` line 169 `deliverables/CSPro/translations-paper-extract/`): add `deliverables/CSPro/data/translations-official/out-delta/` and `deliverables/CSPro/data/translations-official/out-aug21/` directly under that line, then `git check-ignore -v deliverables/CSPro/data/translations-official/out-delta/F1_english_delta.json` must print the rule.

- [ ] **Step 6: Record** — Paste the four console lines plus the per-instrument artefact list into the wave note draft (`deliverables/CSPro/patch-notes/aug21-day0.md`, create it — `New-Item -ItemType Directory -Force deliverables/CSPro/patch-notes` first; the folder does not exist yet) under `## Baseline delta 2026-08-25`. Wave rule (replaces "diffs 0"): each wave's "align EN" task re-runs `--only F<n>` and must reach **diffs limited to the documented artefact list for that instrument** (F3: `paper-only` keeps 97.1/97.2/115.1/115.2 — those build labels are un-numbered stubs by design, spec §F3 bill-detail) before its extraction step. No commit — Carl commits CSPro tooling.

### Task 1: Committed `anchor_extract.py` with argparse + name-scoped anchors (tests first)

**Files:**
- Create: `deliverables/CSPro/data/translations-official/anchor_extract.py`
- Test: `deliverables/CSPro/data/translations-official/test_anchor_extract.py`
- Reference (read-only, copy from): `deliverables/CSPro/translations-paper-extract/anchor_extract.py:38-249, 299-308`

**Interfaces:**
- Consumes: `cspro_helpers.walk_labeled_nodes(dictionary)` yielding `(key, node)` with key shapes `item:<NAME> | vs:<VSNAME> | val:<VSNAME>:<code>` (cspro_helpers.py:1126-1151); `migrate_maps_namekeys.capture_source_dict(inst, "generate_dcf.py")` (data/translations-official/migrate_maps_namekeys.py:63 — runs the generator with `apply_translations` hooked and returns the PRE-APPLY dictionary; side effect: it regenerates that instrument's .dcf); the June-5 functions `pdf_text`, `build_norm`, `norm_for_match`, `clean_span`, `digits_of`, `qa_flags` and the span algorithm of `extract()` (translations-paper-extract/anchor_extract.py:48-249), copied verbatim.
- Produces: `dcf_anchors(dcf_path) -> dict[key, en_text]`; `generator_anchors(instrument) -> dict[key, en_text]`; `extract(pdf_path, anchors) -> {file, anchored, clean:{key:tr}, flagged:[{key,en,tr,flags}]}`; `find_paper(source_dir, instrument, paper_name) -> Path|None`; `write_outputs(results, out_dir, instrument) -> Path`; `main(argv) -> int`. Output files `OUT/<loc>.json` are name-scoped flat maps (no `_meta`) that `apply_aug21.py` (Tasks 4–7) reads unchanged; `OUT/<loc>_flagged.json` is the translator worklist; `OUT/QA-REPORT.md` keeps the June-5 flag digest plus a differ-from-live column when `--live-maps` is given.
- `qa_flags` gains exactly two flags, appended after the June-5 ones (which stay byte-identical): `glued-short-label` — the span contains, word-bounded, another anchor's English of normalised length 4-9 (below `contains-other-label`'s 10-char floor; this is the `…ipinanganak ka? Male Lalaki` class that rendered live on 2026-08-17: "Male" is 4 chars, shorter than `MIN_BOUND`, so it never bounded the span); `ends-with-other-label` — the span ends with another anchor's English of length ≥ 3. Both only fire for anchors not contained in the span's own English.
- Anchors strip the `— Hours` / `— Minutes` component suffix before matching (mirror of F3/F4 `generate_qsf._strip_component_suffix`): the F4 `item:Q67_TRAVEL_HH` and F3 `item:Q69_USUAL_TRAVEL_HH/_MM` labels carry the suffix in the dcf but the paper prints the bare stem + `Time (HH:MM)`; without the strip those keys can never match (required by Tasks 27 and 39).

- [ ] **Step 1: Write the failing tests** (synthetic dcf + generated 1-page PDF; covers name-scoped keys, value-set option pairing, the reachable "untranslated on paper" outcome, the two new flags, the component-suffix strip, CLI). Note on the Q3 fixture: a paper line identical to the English is itself an anchor occurrence, so the span between the two copies and after the last is **empty** — `echo-english` is unreachable through `extract()` by construction and is exercised only through `qa_flags()` directly.

```python
# deliverables/CSPro/data/translations-official/test_anchor_extract.py
import json
from pathlib import Path

import fitz
import pytest

import anchor_extract as ax

DCF = {"name": "TINY", "labels": [{"text": "Tiny survey"}], "levels": [{"name": "LVL", "labels": [{"text": "Level"}],
       "records": [{"name": "REC", "labels": [{"text": "Record A"}], "items": [
           {"name": "Q1_MARITAL", "labels": [{"text": "1. What is your current marital status?"}],
            "valueSets": [{"name": "Q1_MARITAL_VS1", "labels": [{"text": "1. What is your current marital status?"}],
                           "values": [{"labels": [{"text": "Single, never married"}], "pairs": [{"value": "1"}]},
                                      {"labels": [{"text": "Married or living together"}], "pairs": [{"value": "2"}]},
                                      {"labels": [{"text": "Legally separated"}], "pairs": [{"value": "3"}]}]}]},
           {"name": "Q2_EMPLOYED", "labels": [{"text": "2. Are you currently employed in this facility?"}]},
           {"name": "Q3_UNTOUCHED", "labels": [{"text": "3. This label was left in English on paper"}]},
           {"name": "Q4_TRAVEL_HH", "labels": [{"text": "4. How long is the travel time? — Hours"}]},
       ]}]}]}

PAPER = [
    "1. What is your current marital status?",
    "Ano ang iyong kasalukuyang katayuan sa pag-aasawa?",
    "Single, never married  Walang asawa, hindi kailanman nag-asawa",
    "Married or living together  May asawa o nagsasama",
    "Legally separated  Legal na hiwalay",
    "2. Are you currently employed in this facility?",
    "Kasalukuyan ka bang nagtatrabaho sa pasilidad na ito?",
    "3. This label was left in English on paper",
    "3. This label was left in English on paper",
]


def make_pdf(path, lines):
    doc = fitz.open()
    page = doc.new_page()
    y = 60
    for ln in lines:
        page.insert_text((40, y), ln, fontsize=9)
        y += 14
    doc.save(str(path))
    doc.close()


@pytest.fixture
def fixture_dir(tmp_path):
    (tmp_path / "t.dcf").write_text(json.dumps(DCF), encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    make_pdf(src / "F9-Tagalog_Tiny Survey_Aug21.pdf", PAPER)
    return tmp_path


def test_dcf_anchors_are_name_scoped(fixture_dir):
    anchors = ax.dcf_anchors(fixture_dir / "t.dcf")
    assert anchors["item:Q1_MARITAL"] == "1. What is your current marital status?"
    assert anchors["vs:Q1_MARITAL_VS1"] == "1. What is your current marital status?"
    assert anchors["val:Q1_MARITAL_VS1:2"] == "Married or living together"
    assert all(":" in k for k in anchors)


def test_component_suffix_is_stripped_from_anchor(fixture_dir):
    anchors = ax.dcf_anchors(fixture_dir / "t.dcf")
    assert anchors["item:Q4_TRAVEL_HH"] == "4. How long is the travel time?"


def test_extract_pairs_value_set_options_and_emits_name_keys(fixture_dir):
    anchors = ax.dcf_anchors(fixture_dir / "t.dcf")
    r = ax.extract(fixture_dir / "src" / "F9-Tagalog_Tiny Survey_Aug21.pdf", anchors)
    assert r["clean"]["item:Q1_MARITAL"] == "Ano ang iyong kasalukuyang katayuan sa pag-aasawa?"
    assert r["clean"]["vs:Q1_MARITAL_VS1"] == "Ano ang iyong kasalukuyang katayuan sa pag-aasawa?"
    assert r["clean"]["val:Q1_MARITAL_VS1:1"] == "Walang asawa, hindi kailanman nag-asawa"
    assert r["clean"]["val:Q1_MARITAL_VS1:2"] == "May asawa o nagsasama"
    assert r["clean"]["item:Q2_EMPLOYED"] == "Kasalukuyan ka bang nagtatrabaho sa pasilidad na ito?"


def test_untranslated_on_paper_is_held_back_as_empty(fixture_dir):
    anchors = ax.dcf_anchors(fixture_dir / "t.dcf")
    r = ax.extract(fixture_dir / "src" / "F9-Tagalog_Tiny Survey_Aug21.pdf", anchors)
    assert "item:Q3_UNTOUCHED" not in r["clean"]
    row = next(f for f in r["flagged"] if f["key"] == "item:Q3_UNTOUCHED")
    assert row["flags"] == ["empty"]


def test_qa_flags_kept_verbatim_plus_glue_flags():
    assert ax.qa_flags("5. Sex", "5. Sex", {"5 sex"}) == ["echo-english"]
    assert ax.qa_flags("Level 3 hospital", "Ospital na Level 1", set()) == ["digit-mismatch"]
    assert ax.qa_flags("Physician", "", set()) == ["empty"]
    # the 2026-08-17 live spill class: a short option label glued onto the stem
    assert ax.qa_flags("4. What is your sex assigned at birth?",
                       "Ano ang iyong kasarian noong ipinanganak ka? Male Lalaki",
                       {"4 what is your sex assigned at birth", "male", "female"}) == ["glued-short-label"]
    assert ax.qa_flags("Do you own the building?", "Pag-aari mo ba ang gusali? Yes",
                       {"do you own the building", "yes", "no"}) == ["ends-with-other-label"]
    # an anchor that is part of the span's own English never fires either flag
    assert ax.qa_flags("Male nurse", "Lalaking nars", {"male nurse", "male"}) == []


def test_cli_writes_name_scoped_maps_and_report(fixture_dir):
    out = fixture_dir / "out"
    rc = ax.main(["--source", str(fixture_dir / "src"), "--instrument", "F9",
                  "--dcf", str(fixture_dir / "t.dcf"), "--out", str(out), "--locales", "FIL"])
    assert rc == 0
    m = json.loads((out / "fil.json").read_text(encoding="utf-8"))
    assert "_meta" not in m and all(":" in k for k in m)
    assert m["val:Q1_MARITAL_VS1:3"] == "Legal na hiwalay"
    flagged = json.loads((out / "fil_flagged.json").read_text(encoding="utf-8"))
    assert any(f["key"] == "item:Q3_UNTOUCHED" for f in flagged)
    report = (out / "QA-REPORT.md").read_text(encoding="utf-8")
    assert "| FIL |" in report and "`empty`" in report
    assert not (out / "bcl.json").exists()
```

- [ ] **Step 2: Run tests to verify they fail** — Run: `cd deliverables\CSPro\data\translations-official; python -m pytest test_anchor_extract.py -q` Expected: FAIL with `ModuleNotFoundError: No module named 'anchor_extract'`.

- [ ] **Step 3: Write the implementation** (full script; the text-prep/QA block is the June-5 code verbatim with the two new flags appended at the END of `qa_flags` — do not touch the existing flags, they are calibrated against 28 papers)

```python
#!/usr/bin/env python3
"""anchor_extract.py — anchor-based extraction of translations from a bilingual paper PDF,
emitting NAME-SCOPED keys (item:/vs:/val:) that apply_translations() accepts directly.

Method (unchanged from the June-5 tool at translations-paper-extract/anchor_extract.py):
  1. Anchors = every (key, EN text) pair from cspro_helpers.walk_labeled_nodes() on the
     BUILD's English — either the written .dcf (--dcf) or, for F3 where the written file is
     post-neutralise, the generator's pre-apply dictionary (--generator F3).
  2. Normalise the PDF text with a char-offset map back to the original.
  3. Find every word-bounded occurrence of every anchor text in the normalised text.
  4. Sort by position; each anchor's candidate translation = original-text span from the
     anchor's end to the next anchor's start.
  5. clean_span + qa_flags; only unflagged pairs land in <loc>.json.

    python anchor_extract.py --source "raw/Survey-Instruments-2026-08-21/Translations" \
        --instrument F1 --dcf deliverables/CSPro/F1/FacilityHeadSurvey.dcf \
        --out deliverables/CSPro/data/translations-official/out-aug21/F1 \
        [--locales FIL,BCL] [--live-maps deliverables/CSPro/F1/translations]
    python anchor_extract.py --source ... --instrument F3 --generator F3 --out .../out-aug21/F3

--live-maps prints, per locale, how many CLEAN pairs differ from the live map's current
value (the number apply_aug21.py's replace-by-default would overwrite) and lists
"keys not in dcf" (always [] by construction — printed so the gate is explicit).
Writes <out>/<loc>.json, <out>/<loc>_flagged.json, <out>/QA-REPORT.md. NOTHING is written
into the build or the live maps — apply_aug21.py is the only writer.
"""
import argparse
import io
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import fitz

HERE = os.path.dirname(os.path.abspath(__file__))
CSPRO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, CSPRO)
sys.path.insert(0, HERE)
from cspro_helpers import walk_labeled_nodes  # noqa: E402

# (paper-filename language word, locale code) — Aug-21 files are F<n>-<Language>_..._Aug21.pdf
LANGS = [("Tagalog", "FIL"), ("Bicolano", "BCL"), ("Bisaya", "BIS"), ("Cebuano", "CEB"),
         ("Waray", "WAR"), ("Hiligaynon", "HIL"), ("Ilocano", "ILO")]

BOX = re.compile(r"[\u2610\u2611\u2612\u25a1\u25a0\u2751]")
NOISE = re.compile(r"ICF ver\.|Translated Questionnaire ver\.|^\s*\d+\s*$")
SKIP_NOTE = re.compile(r"<[^>]{0,60}>")
# F3/F4 HH:MM items carry "— Hours" / "— Minutes" in the dcf label only (the paper prints the
# bare stem + "Time (HH:MM)"); mirror of generate_qsf._strip_component_suffix.
COMPONENT_SUFFIX_RE = re.compile(r"\s+\u2014\s+(Hours|Minutes)\s*$")

MIN_EMIT = 8      # normalised length to emit a translation for
MIN_BOUND = 6     # normalised length to serve as a span boundary
MAX_SPAN = 420    # candidate longer than this = boundary failure


# ---------------------------------------------------------------- text prep --
# verbatim from translations-paper-extract/anchor_extract.py:48-85 (June-5 tool)
def pdf_text(path):
    d = fitz.open(str(path))
    t = "\n".join(d[i].get_text() for i in range(len(d)))
    d.close()
    lines = [ln for ln in t.split("\n") if not NOISE.search(ln)]
    return " ".join(" ".join(lines).split())


def build_norm(text):
    """Lower-cased alnum+space projection of `text`, plus map norm-idx -> orig-idx."""
    norm_chars, idx = [], []
    prev_space = True
    for i, c in enumerate(text):
        cl = c.lower()
        if cl == "\u2019" or cl == "\u2018":
            cl = "'"
        if cl.isalnum():
            norm_chars.append(cl); idx.append(i); prev_space = False
        else:
            if not prev_space:
                norm_chars.append(" "); idx.append(i); prev_space = True
    return "".join(norm_chars), idx


def norm_for_match(s):
    # same projection as build_norm applied to a label
    out, prev = [], True
    for c in s.lower().replace("\u2019", "'").replace("\u2018", "'"):
        if c.isalnum():
            out.append(c); prev = False
        elif not prev:
            out.append(" "); prev = True
    return "".join(out).strip()


# ------------------------------------------------------------------- anchors --
def _anchors_from_dict(d):
    out = {}
    for key, node in walk_labeled_nodes(d):
        labs = node.get("labels") or []
        if not labs:
            continue
        first = labs[0]
        if first.get("language") not in (None, "EN"):
            continue
        en = COMPONENT_SUFFIX_RE.sub("", (first.get("text") or "").strip())
        if en:
            out[key] = en
    return out


def dcf_anchors(dcf_path):
    """{name-scoped key: EN label text} for every labels-bearing node of a WRITTEN dcf.

    Uses the shared walker so keys are byte-identical to what apply_translations()
    looks up (cspro_helpers.py:1126). labels[0] is the English label (language None/EN).
    Right for F1/F4. NOT right for F3: PatientSurvey.dcf is written after
    _neutralise_facility_placeholder, so use generator_anchors("F3").
    """
    return _anchors_from_dict(json.load(io.open(dcf_path, encoding="utf-8")))


def generator_anchors(instrument):
    """Anchors from the generator's PRE-APPLY dictionary (placeholders intact — the text
    the qsf renders). Side effect: capture_source_dict re-runs the generator, which
    rewrites <inst>/<App>.dcf from the current translations (a no-op on a clean tree)."""
    from migrate_maps_namekeys import capture_source_dict
    return _anchors_from_dict(capture_source_dict(instrument, "generate_dcf.py"))


# ---------------------------------------------------------------- extraction --
# verbatim from translations-paper-extract/anchor_extract.py:120-183, plus two flags at the end
def clean_span(span):
    s = BOX.sub(" ", span)
    s = SKIP_NOTE.sub(" ", s)
    s = " ".join(s.split()).strip(" .:;,-")
    # residue of the anchor's own trailing punctuation ("? (", ") /" when the
    # anchor's normalised form ends before a closing paren, slashes, dashes)
    s = s.lstrip("?!.:;,)/- ").strip()
    # Ilocano layout: the whole candidate is one balanced paren group
    if s.startswith("(") and s.endswith(")") and s.count("(") == s.count(")"):
        inner = s[1:-1].strip()
        if inner:
            s = inner
    return s


def digits_of(s, strip_qnum=True):
    if strip_qnum:
        s = re.sub(r"^\s*\d+(\.\d+)?\s*\.", "", s)
    return Counter(re.findall(r"\d+", s))


def qa_flags(en, tr, nlabels):
    flags = []
    if not tr:
        return ["empty"]
    ne, nt = norm_for_match(en), norm_for_match(tr)
    if nt == ne:
        flags.append("echo-english")
    if len(tr) > MAX_SPAN:
        flags.append("overlong-span")
    ratio = len(nt) / max(len(ne), 1)
    if ratio < 0.25 or ratio > 4.0:
        flags.append("length-ratio")
    # catastrophic: the "translation" IS another English label verbatim
    # ("Physician" -> "Nurse" when the next option had no anchored translation)
    if nt != ne and nt in nlabels:
        flags.append("is-other-label")
    # boundary bleed: candidate contains some OTHER known label (word-bounded)
    padded = f" {nt} "
    for other in nlabels:
        if other == ne or len(other) < 10 or other in ne:
            continue
        if f" {other} " in padded:
            flags.append("contains-other-label")
            break
    # table-row bleed: Yes/No + amount furniture swept up from a grid
    if " yes " in padded and " no " in padded and len(nt) < 90:
        flags.append("table-bleed")
    if "amount in pesos" in padded:
        flags.append("table-bleed")
    de, dt = digits_of(en), digits_of(tr, strip_qnum=False)
    if de and dt and de != dt and (de - dt or dt - de):
        # digits present on both sides but different sets -> e.g. Level 3 -> Level 1
        if set(de) != set(dt):
            flags.append("digit-mismatch")
    if nt.startswith(ne[: max(10, len(ne) // 2)]) and len(nt) > len(ne):
        flags.append("starts-with-english")
    # span opens mid-English-sentence: the dcf label was truncated relative to
    # the paper wording, so the span begins with the English tail, not a translation
    first = nt.split(" ", 1)[0] if nt else ""
    if first in {"to", "of", "and", "for", "in", "the", "with", "from", "are",
                 "is", "was", "has", "have", "that", "by", "on", "or", "date"}:
        flags.append("starts-mid-english")
    # ---- Aug-21 additions (2026-08-25) — appended, June-5 flags above untouched ----
    # glued-short-label: a SHORT other anchor (4-9 chars, below contains-other-label's
    # floor and often below MIN_BOUND so it never bounded the span) sits inside the span:
    # the ")  Male (Lalaki" class that rendered live on 2026-08-17.
    for other in nlabels:
        if other == ne or not (4 <= len(other) < 10) or other in ne:
            continue
        if f" {other} " in padded:
            flags.append("glued-short-label")
            break
    # ends-with-other-label: the span's last word(s) are another anchor's English
    # (Yes/No/Oo grid furniture, a following option's English swept in).
    for other in nlabels:
        if other == ne or len(other) < 3 or other in ne:
            continue
        if padded.endswith(f" {other} "):
            flags.append("ends-with-other-label")
            break
    return flags


def find_paper(source_dir, instrument, paper_name):
    """Aug-21 naming: F<n>-<Language>_<title>_Aug21.pdf (instrument FIRST — the June-5
    glob '<Language>*<Fn>*.pdf' does not match these files)."""
    cands = sorted(Path(source_dir).glob(f"{instrument}-{paper_name}*.pdf")) or \
        sorted(Path(source_dir).glob(f"{paper_name}*{instrument}*.pdf"))
    return cands[0] if cands else None


def extract(pdf_path, anchors):
    """anchors: {key: EN}. Same span algorithm as the June-5 extract() (:186-249), but the
    occurrence list carries the KEY, so identical English on two nodes (an item label and
    its vs: label, or the same option under two value sets) yields one pair per key."""
    text = pdf_text(pdf_path)
    ntext, idx = build_norm(text)

    # group keys by normalised English so each distinct text is searched once
    by_norm = defaultdict(list)
    for key, en in anchors.items():
        by_norm[norm_for_match(en)].append(key)

    occ = []          # (start_norm, end_norm, norm_en)
    for ne in by_norm:
        if len(ne) < MIN_BOUND:
            continue
        pat = re.compile(r"(?<![a-z0-9])" + re.escape(ne) + r"(?![a-z0-9])")
        # NO small cap here: frequent option labels ("Others (specify)", the Yes-
        # variants) must bound EVERY span they open, or spans bleed into the next
        # English option. 64 is a runaway guard, not a working limit.
        for m in list(pat.finditer(ntext))[:64]:
            occ.append((m.start(), m.end(), ne))
    occ.sort()

    # de-overlap: keep the longest anchor at each position
    kept = []
    last_end = -1
    for s, e, ne in occ:
        if s < last_end:
            if e <= last_end:
                continue
        kept.append((s, e, ne))
        last_end = max(last_end, e)

    results = defaultdict(list)
    nlabels = set(by_norm)
    for i, (s, e, ne) in enumerate(kept):
        if len(ne) < MIN_EMIT:
            continue
        nxt = kept[i + 1][0] if i + 1 < len(kept) else len(ntext)
        o_start = idx[e - 1] + 1 if e - 1 < len(idx) else len(text)
        o_end = idx[nxt] if nxt < len(idx) else len(text)
        results[ne].append(clean_span(text[o_start:o_end]))

    clean, flagged = {}, []
    for ne, cands_tr in results.items():
        keys = by_norm[ne]
        en = anchors[keys[0]]
        best, best_flags = None, None
        counted = Counter(c for c in cands_tr if c)
        for tr, _n in counted.most_common():
            fl = qa_flags(en, tr, nlabels)
            if not fl:
                best, best_flags = tr, []
                break
            if best is None:
                best, best_flags = tr, fl
        for key in keys:
            if best is None:
                flagged.append({"key": key, "en": en, "tr": "", "flags": ["empty"]})
            elif best_flags:
                flagged.append({"key": key, "en": en, "tr": best, "flags": best_flags})
            else:
                clean[key] = best
    return {"file": Path(pdf_path).name, "anchored": len(results),
            "clean": clean, "flagged": flagged}


# -------------------------------------------------------------------- output --
MEAN = {"is-other-label": "the 'translation' is verbatim another English label — worst class, never import",
        "starts-mid-english": "span opens mid-English (dcf label truncated vs the paper wording)",
        "table-bleed": "Yes/No or amount-grid furniture swept into the span",
        "echo-english": "translation is identical to the English (left untranslated on paper)",
        "starts-with-english": "span starts by repeating the English (run-together layout residue)",
        "contains-other-label": "span bleeds into the next question (boundary failure)",
        "overlong-span": "span too long — an un-anchored stretch follows",
        "length-ratio": "translation implausibly short/long vs the English",
        "digit-mismatch": "numbers differ between English and translation (e.g. Level 3 vs Level 1)",
        "empty": "nothing between this anchor and the next (paper copy identical to the English, or blank)",
        "glued-short-label": "a short option label (Male/Yes/None…) is glued inside the span — the 2026-08-17 live spill class",
        "ends-with-other-label": "span ends with another label's English (grid furniture / next option swept in)"}


def differ_from_live(clean, live_path):
    """(differ, same, new) counts of CLEAN pairs vs the live map at live_path."""
    if not live_path or not os.path.exists(live_path):
        return None
    live = json.load(io.open(live_path, encoding="utf-8"))
    live.pop("_meta", None)
    differ = same = new = 0
    for k, v in clean.items():
        if k not in live:
            new += 1
        elif live[k] == v:
            same += 1
        else:
            differ += 1
    return {"differ": differ, "same": same, "new": new}


def write_outputs(results, out_dir, instrument, live_dir=None):
    """results: {locale code: extract() result or None}. Returns the QA-REPORT.md path."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report = ["# Paper-translation extraction — QA report", "",
              f"Instrument: **{instrument}**. Anchors: the build's English via walk_labeled_nodes().",
              "Keys are name-scoped (item:/vs:/val:). Nothing has been written into the build.", "",
              "| locale | file | anchored | clean pairs | flagged | differ from live | same | new |",
              "|---|---|---|---|---|---|---|---|"]
    fc, samples = Counter(), defaultdict(list)
    for code, r in results.items():
        if r is None:
            report.append(f"| {code} | — | — | — | no paper file | | | |")
            continue
        with io.open(out_dir / f"{code.lower()}.json", "w", encoding="utf-8", newline="\n") as fh:
            json.dump(r["clean"], fh, ensure_ascii=False, indent=1); fh.write("\n")
        with io.open(out_dir / f"{code.lower()}_flagged.json", "w", encoding="utf-8", newline="\n") as fh:
            json.dump(r["flagged"], fh, ensure_ascii=False, indent=1); fh.write("\n")
        dl = differ_from_live(r["clean"], os.path.join(live_dir, f"{code.lower()}.json")) if live_dir else None
        dcols = f"{dl['differ']} | {dl['same']} | {dl['new']}" if dl else " | | "
        report.append(f"| {code} | {r['file']} | {r['anchored']} | {len(r['clean'])} | {len(r['flagged'])} | {dcols} |")
        for row in r["flagged"]:
            for fl in row["flags"]:
                fc[fl] += 1
                if len(samples[fl]) < 2:
                    samples[fl].append((code, row["key"], row["en"][:70], row["tr"][:70]))
    report += ["", "## Flag digest (why pairs were held back)", "", "| flag | count | meaning |", "|---|---|---|"]
    for fl, n in fc.most_common():
        report.append(f"| `{fl}` | {n} | {MEAN.get(fl, '')} |")
    report.append("")
    for fl in ("digit-mismatch", "contains-other-label", "is-other-label", "glued-short-label", "ends-with-other-label"):
        if samples.get(fl):
            report.append(f"### `{fl}` samples")
            for code, key, en, tr in samples[fl]:
                report.append(f"- **{code} {key}** — EN: “{en}” → “{tr}”")
            report.append("")
    path = out_dir / "QA-REPORT.md"
    path.write_text("\n".join(report), encoding="utf-8")
    return path


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True, help="folder holding the bilingual PDFs")
    ap.add_argument("--instrument", required=True, help="F1 | F3 | F4 (filename prefix)")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--dcf", help="a WRITTEN .dcf to anchor on (F1/F4)")
    src.add_argument("--generator", help="anchor on this instrument's PRE-APPLY generator dictionary (F3)")
    ap.add_argument("--out", required=True, help="output folder (gitignored)")
    ap.add_argument("--locales", default=",".join(c for _, c in LANGS),
                    help="comma list of locale codes, default all seven")
    ap.add_argument("--live-maps", help="<inst>/translations dir — print differ-from-live per locale")
    a = ap.parse_args(argv)
    want = {c.strip().upper() for c in a.locales.split(",") if c.strip()}
    anchors = generator_anchors(a.generator) if a.generator else dcf_anchors(a.dcf)
    bad = [k for k in anchors if ":" not in k]
    print(f"{a.instrument}: {len(anchors)} anchors from {a.generator or a.dcf}; keys not in dcf: {bad[:5]}")
    if bad:
        return 1
    results = {}
    print("%-4s %8s %8s %8s %8s  %s" % ("loc", "anchored", "clean", "flagged", "differ", "file"))
    for paper, code in LANGS:
        if code not in want:
            continue
        pdf = find_paper(a.source, a.instrument, paper)
        if pdf is None:
            results[code] = None
            print("%-4s %8s %8s %8s %8s  %s" % (code, "-", "-", "-", "-", "no paper file"))
            continue
        r = extract(pdf, anchors)
        results[code] = r
        dl = differ_from_live(r["clean"], os.path.join(a.live_maps, f"{code.lower()}.json")) if a.live_maps else None
        print("%-4s %8d %8d %8d %8s  %s" % (code, r["anchored"], len(r["clean"]), len(r["flagged"]),
                                           dl["differ"] if dl else "-", r["file"]))
    print("wrote", write_outputs(results, a.out, a.instrument, a.live_maps))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests to verify they pass** — Run: `python -m pytest test_anchor_extract.py -q` Expected: `6 passed`. If `test_extract_pairs_value_set_options...` fails on `val:Q1_MARITAL_VS1:3` only, the PDF's last option has no following anchor and the span runs to end-of-page — that is expected on real papers too and is why the test asserts codes 1 and 2 in `extract()` and code 3 only through the CLI test (where "2. Are you..." bounds it). Do not loosen `MIN_BOUND`. If `test_qa_flags_kept_verbatim_plus_glue_flags` fails on the `Male nurse` case, the `other in ne` guard on the two new flags is missing.

- [ ] **Step 5: Verify/gate on real data (F1 written dcf, F3 generator dictionary; no writes into the build)** — From the repo root in PowerShell:

```
$env:PYTHONIOENCODING='utf-8'
python deliverables\CSPro\data\translations-official\anchor_extract.py --source "raw\Survey-Instruments-2026-08-21\Translations" --instrument F1 --dcf deliverables\CSPro\F1\FacilityHeadSurvey.dcf --out deliverables\CSPro\data\translations-official\out-aug21\F1 --live-maps deliverables\CSPro\F1\translations
python deliverables\CSPro\data\translations-official\anchor_extract.py --source "raw\Survey-Instruments-2026-08-21\Translations" --instrument F3 --generator F3 --out deliverables\CSPro\data\translations-official\out-aug21\F3 --live-maps deliverables\CSPro\F3\translations
git -C . status --short deliverables/CSPro/F3/PatientSurvey.dcf
```

Expected: first line of each run ends `keys not in dcf: []`; seven table rows with a file each (`F1-Tagalog_Facility Head Survey Questionnaire_UHC Year 2_Aug21.pdf` etc.); clean pairs in the hundreds per locale (the review's un-fixed F1 run gave FIL 842 clean / 174 flagged with **172 clean pairs differing from live** — after the two new flags expect clean to drop and flagged to rise; the `differ` column is the number the merge dry-run must explain before any `--apply`). A locale with < 50 clean means the paper's English differs from the build — check `aug21_english_delta.py --only F<n>` first. For F3, the `git status` line must be empty (capture_source_dict regenerated `PatientSurvey.dcf` byte-identically); if it is not, the tree was already dirty — do not commit that file from here. Open both `QA-REPORT.md`s: the `is-other-label` and `glued-short-label` samples are the worst classes and feed `aug21-overrides.json` review in Task 6; if `glued-short-label` dominates the digest (> ~25% of flags) on the Ilocano paper, note it — the 4-char floor may need raising to 5 for ILO only, decide in Task 6, not here. Confirm ignore: `git check-ignore -v deliverables/CSPro/data/translations-official/out-aug21/F1/fil.json` must print the root-`.gitignore` rule added in Task 0 Step 5. Run the existing suite too so nothing regressed: `cd deliverables\CSPro\aug17-tools; python -m pytest test_tools.py -q` — Expected: all pass (unchanged file).

- [ ] **Step 6: Record** — In `deliverables/CSPro/patch-notes/aug21-day0.md` add `## Extractor` with the F1 and F3 seven-row tables (incl. the `differ` column) and the flag-digest top 3 per instrument. Note explicitly: the June-5 script at `translations-paper-extract/` is now superseded for imports (leave it on disk; it is gitignored), and F3 anchors come from `--generator F3`, never from the written .dcf. Update `deliverables/CSPro/data/translations-official/README.md` with a 5-line "Aug-21 extractor" entry: CLI line for `--dcf` and `--generator`, output shape (`<loc>.json` name-scoped, no `_meta`), "anchors on the BUILD's English — align English first (F3: generator dict, not the file)", the two added flags + the component-suffix strip, and the rule that only `apply_aug21.py` writes into `F<n>/translations/`. No git commit (Carl commits CSPro tooling).

### Task 2: Lock the extractor contract against `apply_translations()` (regression lock)

**Files:**
- Modify: `deliverables/CSPro/data/translations-official/test_anchor_extract.py` (append one test)

**Interfaces:**
- Consumes: `cspro_helpers.apply_translations(dictionary, translations_dir, languages=TRANSLATION_LANGUAGES)` (cspro_helpers.py:1154-1240), which `SystemExit`s on any key without `:` (:1175-1180) and prints `FIL: m/t labels translated (p%)` (:1238-1239); `anchor_extract.main` (Task 1).
- Produces: proof that the extractor's `fil.json` is loadable by the real consumer with zero legacy keys — the property every wave's `apply_aug21.py --apply` relies on.

This is a regression lock, not a fail-first test: with Task 1 correct it passes on first run. Its job is to fail the day someone changes `write_outputs` or `dcf_anchors` in a way `apply_translations` rejects.

- [ ] **Step 1: Write the test**

```python
# append to test_anchor_extract.py
import copy
import sys
sys.path.insert(0, ax.CSPRO)
from cspro_helpers import apply_translations  # noqa: E402


def test_extractor_output_is_accepted_by_apply_translations(fixture_dir, capsys):
    out = fixture_dir / "out"
    ax.main(["--source", str(fixture_dir / "src"), "--instrument", "F9",
             "--dcf", str(fixture_dir / "t.dcf"), "--out", str(out), "--locales", "FIL"])
    d = apply_translations(copy.deepcopy(DCF), out, languages=[("EN", "English", None), ("FIL", "Filipino", "fil.json")])
    item = d["levels"][0]["records"][0]["items"][0]
    fil = {l["language"]: l["text"] for l in item["labels"]}["FIL"]
    assert fil == "Ano ang iyong kasalukuyang katayuan sa pag-aasawa?"
    assert "FIL:" in capsys.readouterr().out
```

- [ ] **Step 2: Run it** — Run: `python -m pytest test_anchor_extract.py -q -k accepted` Expected: `1 passed` immediately. If it errors with `SystemExit ... legacy text-format keys`, fix `_anchors_from_dict` (it must never yield a text key); if `apply_translations` raises from `_find_missed` (a labels node the walker did not reach), the synthetic `DCF` gained a node shape the walker does not know — keep the fixture to dict/level/record/item/valueSet/value only, exactly as in Task 1 Step 1.

- [ ] **Step 3: Implementation** — none required beyond Task 1.

- [ ] **Step 4: Run the whole Day-0 suite** — Run: `python -m pytest test_anchor_extract.py test_aug21_english_delta.py -q` Expected: `11 passed` (4 delta + 6 extractor + 1 lock).

- [ ] **Step 5: Verify/gate** — Real-data round trip without touching the live maps, from the repo root in PowerShell (here-string, not a heredoc):

```
$env:PYTHONIOENCODING='utf-8'
@'
import sys
sys.path.insert(0, "deliverables/CSPro")
sys.path.insert(0, "deliverables/CSPro/F1")
from cspro_helpers import apply_translations
import generate_dcf as g
apply_translations(g.build_dictionary(), "deliverables/CSPro/data/translations-official/out-aug21/F1")
'@ | python -
```

Expected: prints the `Languages:` line and seven `<CODE>: m/t labels translated (p%)` lines with no `SystemExit`. Record the seven percentages as the **raw Aug-21 yield (extractor only, pre-merge)** against the current F1 English — a key-presence count that still includes whatever the two new flags did not catch — alongside the `differ` column from Task 1 Step 5. Together they become the before-columns of the Wave-1 coverage table (baseline live map: FIL67 BCL67 BIS67 CEB63 WAR67 HIL66 ILO62); neither number is "usable yield" until the merge dry-run has reconciled the differ count.

- [ ] **Step 6: Record** — Append the seven yield lines and the F1 `differ` counts to `patch-notes/aug21-day0.md` under `## F1 raw yield (extractor only, pre-merge)`. This closes Day 0 part 1; the merge tool (`apply_aug21.py`, overrides file), notes/ICF layers and the F2 apply script follow in Tasks 3–15 and consume `out-aug21/<inst>/<loc>.json` as produced here.

---

## Merge tool: `apply_aug21.py`, `aug21-overrides.json`, gate wiring

All files live beside `apply_safe.py` in `C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSPro/data/translations-official/` (`HERE` below). Conventions reused verbatim from `apply_safe.py`: `HERE`/`CSPRO` location (:34-35), `norm(s)` (:47), `load_map(path)` → `(OrderedDict, indent, crlf)` (:51-59), `save_map(path, data, indent, crlf)` (:62-65, `json.dump(..., ensure_ascii=False, indent=indent)` + trailing newline, CRLF preserved via `newline=`), per-instrument map dir `os.path.join(CSPRO, inst, "translations", loc.lower() + ".json")` (:131-133). The one behaviour that is inverted versus `apply_safe.py:162-171` is the *different existing value* branch: Aug-21 REPLACES unless the key is listed in `aug21-overrides.json`.

Input contract (from Task 1): per instrument an out dir containing `{loc}.json` = `{ "<name-scoped key>": "<translation>" }` (optionally with `_meta`, ignored) and `{loc}_flagged.json` = `[ {"key": ..., "en": ..., "tr": ..., "flags": [...]} ]`, `loc` lower-case (`fil bcl bis ceb war hil ilo`). Default location `HERE/out-aug21/F<n>/` (the Task 0/1 output root, gitignored).

Measured baselines (2026-08-25, BEFORE any Aug-21 change) that the gates are calibrated against:
- `python aug17-tools/bridge_check.py --check` → `Total defects found: 18` (F3/bis 1, F3/hil 4, F3/ilo 3, F4/hil 5, F4/ilo 5), exit 0 always (bridge_check.py:365-366 print totals; `main()` never calls `sys.exit`). Rule A (`A-mismatch`, bridge_check.py:264-269) fires whenever a scoped `item:` value differs from the June-5 legacy archive `translations/legacy-textkey-2026-08-17/<loc>.json` and is explicitly "NOT applied … triage only" — every Aug-21 REPLACE of an `item:` key with a legacy entry is an A-mismatch by construction, so a zero target is impossible and wrong. Only Rules B (`B-admin-leak`) and C (`C-glued-fragments`) are hard defects.
- `scan_poisoned_keys.py` WRONG_Q_CLEARED / GLUED_CLEARED (scan_poisoned_keys.py:108-172) compare stems against `official_translations.json` = the JUNE-5 cleared corpus; Aug-21 rewordings legitimately differ from it. The pre-apply TOTAL is therefore measured per wave (Task 6 step 5.1) and the gate is `post <= pre` per reason, not `0`.

Run every command below from `C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSPro` with `PYTHONIOENCODING=utf-8` set (`$env:PYTHONIOENCODING='utf-8'` in PowerShell). F1/F3/F4 generator runs need the main checkout (psgc_* are gitignored in worktrees); the plan below avoids generator runs in the default dry-run path for that reason.

### Task 3: `aug21-overrides.json` + validator module

**Files:**
- Create: `deliverables/CSPro/data/translations-official/aug21_overrides.py`
- Create: `deliverables/CSPro/data/translations-official/aug21-overrides.json`
- Test: `deliverables/CSPro/data/translations-official/test_apply_aug21.py`

**Interfaces:**
- Consumes: nothing (stdlib only).
- Produces: `OVERRIDES_PATH` (str), `INSTRUMENTS = ("F1", "F3", "F4", "F2")`, `validate_overrides(data: dict) -> list[str]` (empty list = valid; every error string starts with `<INST>:` or `<INST>/<key>:`), `load_overrides(path: str = OVERRIDES_PATH) -> dict` (raises `SystemExit` with the joined error list on invalid). F1/F3/F4 blocks are `{key: {keep, reason}}`; the F2 block is locale-nested `{loc: {English: {keep: str|null, reason}}}` (the contract of `apply-paper-translations.py`, Task 15) — `keep: null` is legal ONLY for F2 and means "never write this key". Notes/ICF entries (`note:…:<LOC>`, `icf:…:<LOC>`, Tasks 8/10) live in the F1/F3/F4 blocks and may carry `keep: ""` (render English) — the validator accepts an empty `keep` for keys starting with `note:` or `icf:`.

- [ ] **Step 1: Write the failing test**

```python
# deliverables/CSPro/data/translations-official/test_apply_aug21.py
import io
import json
import os
import sys
from collections import OrderedDict

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from aug21_overrides import validate_overrides, load_overrides  # noqa: E402


def test_validate_overrides_accepts_spec_example():
    data = {"F3": {"val:Q5_SEX_VS1:1": {
        "keep": "Lalaki", "reason": "Aug-21 PDF still swaps Male/Female (June-5 defect carried)"}}}
    assert validate_overrides(data) == []


def test_validate_overrides_rejects_bad_shapes():
    errs = validate_overrides({
        "F9": {},                                             # unknown instrument
        "F1": {"Q1_NAME": {"keep": "x", "reason": "r"}},      # no ':' in a CSPro key
        "F3": {"item:Q1_NAME": {"keep": "x"}},                # reason missing
        "F4": {"item:Q1_NAME": {"keep": "", "reason": "r"}},  # empty keep on a map key
        "F2": {"fil": {"Sex": {"keep": "Kasarian", "reason": "ok"},
                       "No": {"keep": None, "reason": "suppress"}}},   # F2 = locale-nested, null ok
    })
    assert any(e.startswith("F9:") for e in errs)
    assert any(e.startswith("F1/") and "Q1_NAME" in e and "':'" in e for e in errs)
    assert any(e.startswith("F3/") and "reason" in e for e in errs)
    assert any(e.startswith("F4/") and "keep" in e for e in errs)
    assert not any(e.startswith("F2/") or e.startswith("F2:") for e in errs)


def test_validate_overrides_allows_empty_keep_for_notes_and_icf():
    data = {"F1": {"icf:1:1:FIL": {"keep": "", "reason": "force English"},
                   "note:intro:4:BCL": {"keep": "", "reason": "force English"}}}
    assert validate_overrides(data) == []


def test_load_overrides_exits_on_invalid(tmp_path):
    p = tmp_path / "ov.json"
    p.write_text(json.dumps({"F1": {"nokey": {"keep": "x", "reason": "r"}}}), encoding="utf-8")
    with pytest.raises(SystemExit):
        load_overrides(str(p))
    p.write_text("{}", encoding="utf-8")
    assert load_overrides(str(p)) == {}
```

- [ ] **Step 2: Run test to verify it fails** — Run: `python -m pytest data/translations-official/test_apply_aug21.py -q` Expected: `ERROR collecting ... ModuleNotFoundError: No module named 'aug21_overrides'` (a module-level import failure is a collection error, not a FAIL).

- [ ] **Step 3: Write minimal implementation**

```python
# deliverables/CSPro/data/translations-official/aug21_overrides.py
#!/usr/bin/env python3
"""aug21-overrides.json — keys the Aug-21 import must NOT replace.

Schema:  { "F1"|"F3"|"F4": { "<key>": { "keep": "<current text>", "reason": "<why>" } },
           "F2": { "<loc>": { "<exact English>": { "keep": "<text>"|null, "reason": "<why>" } } } }
F1/F3/F4 keys are name-scoped (item:/vs:/val:, must contain ':') or the notes/ICF keys
note:<key>:<LOC> / icf:<p>:<i>:<LOC> (for which keep == "" means "render English").
F2 keys are the flat exact-English strings the PWA store uses, nested by locale; keep null
means "never write this key". Every entry needs a non-empty reason — an override without
a reason is a silent defect carrier.
"""
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OVERRIDES_PATH = os.path.join(HERE, "aug21-overrides.json")
INSTRUMENTS = ("F1", "F3", "F4", "F2")


def _check_reason(errs, where, ent):
    if not isinstance(ent.get("reason"), str) or not ent.get("reason", "").strip():
        errs.append(f"{where}: 'reason' must be a non-empty string")


def validate_overrides(data):
    errs = []
    if not isinstance(data, dict):
        return ["top level must be an object keyed by instrument"]
    for inst, block in data.items():
        if inst.startswith("_"):
            continue                       # _readme / _seeded provenance blocks
        if inst not in INSTRUMENTS:
            errs.append(f"{inst}: unknown instrument")   # no INSTRUMENTS echo: keeps prefix-matching clean
            continue
        if not isinstance(block, dict):
            errs.append(f"{inst}: block must be an object keyed by translation key")
            continue
        if inst == "F2":
            # locale-nested: {loc: {English: {keep: str|null, reason}}} (apply-paper-translations.py)
            for loc, sub in block.items():
                if not isinstance(sub, dict):
                    errs.append(f"{inst}/{loc!r}: locale block must be an object keyed by English string")
                    continue
                for key, ent in sub.items():
                    if not isinstance(ent, dict):
                        errs.append(f"{inst}/{loc}/{key!r}: entry must be an object with keep + reason")
                        continue
                    if not (ent.get("keep") is None or isinstance(ent.get("keep"), str)):
                        errs.append(f"{inst}/{loc}/{key!r}: 'keep' must be a string or null")
                    _check_reason(errs, f"{inst}/{loc}/{key!r}", ent)
            continue
        for key, ent in block.items():
            if ":" not in key:
                errs.append(f"{inst}/{key!r}: CSPro override key must be name-scoped (contain ':')")
            if not isinstance(ent, dict):
                errs.append(f"{inst}/{key!r}: entry must be an object with keep + reason")
                continue
            keep = ent.get("keep")
            empty_ok = key.startswith(("note:", "icf:"))     # "" = render English (Tasks 8/10)
            if not isinstance(keep, str) or (not keep.strip() and not empty_ok):
                errs.append(f"{inst}/{key!r}: 'keep' must be a non-empty string")
            _check_reason(errs, f"{inst}/{key!r}", ent)
    return errs


def load_overrides(path=OVERRIDES_PATH):
    if not os.path.exists(path):
        return {}
    data = json.loads(io.open(path, encoding="utf-8").read())
    errs = validate_overrides(data)
    if errs:
        raise SystemExit("aug21-overrides.json invalid:\n  " + "\n  ".join(errs))
    return {k: v for k, v in data.items() if not k.startswith("_")}


if __name__ == "__main__":
    errs = validate_overrides(json.loads(io.open(OVERRIDES_PATH, encoding="utf-8").read()))
    print("OK" if not errs else "\n".join(errs))
    raise SystemExit(1 if errs else 0)
```

Seed file (committed, starts empty of entries):

```json
{
  "_readme": "Keys the Aug-21 translation import must NOT replace. Schema: {F1|F3|F4: {key: {keep, reason}}, F2: {loc: {English: {keep: text|null, reason}}}}. F1/F3/F4 keys are name-scoped (item:/vs:/val:) or note:<key>:<LOC> / icf:<p>:<i>:<LOC> (keep '' = render English). F2 keys are exact English strings nested by locale (keep null = never write). Add rows ONLY for defects the Aug-21 extract actually re-introduces, confirmed during a wave's apply_aug21.py dry-run (see --seed). Validate: python data/translations-official/aug21_overrides.py",
  "F1": {},
  "F3": {},
  "F4": {},
  "F2": {}
}
```

- [ ] **Step 4: Run test to verify it passes** — Run: `python -m pytest data/translations-official/test_apply_aug21.py -q` Expected: `4 passed`.

- [ ] **Step 5: Verify/gate** — Run: `python data/translations-official/aug21_overrides.py` Expected: `OK`, exit 0.

- [ ] **Step 6: Record** — note in the wave log that `aug21-overrides.json` exists with zero entries; no commit (Carl commits CSPro data/tool changes).

### Task 4: `apply_aug21.py` merge core (`merge_locale`)

**Files:**
- Create: `deliverables/CSPro/data/translations-official/apply_aug21.py`
- Test: `deliverables/CSPro/data/translations-official/test_apply_aug21.py` (append)

**Interfaces:**
- Consumes: `apply_safe.norm`, `apply_safe.load_map`, `apply_safe.save_map` (imported from `apply_safe`; exact signatures quoted above); `aug21_overrides.load_overrides` (Task 3).
- Produces: `MergeResult` (dataclass: `writes: OrderedDict`, `replaced: list[tuple[key, old, new]]`, `overridden: list[tuple[key, current, proposed]]`, `flagged_skipped: int`, `already_same: int`, `unmatched: list[str]`, `override_stale: list[key]`) and `merge_locale(current: OrderedDict, pairs: dict, flagged_keys: set, overrides: dict, all_keys: set | None = None) -> MergeResult`. `override_stale` is reported as `WARN override 'keep' != current map value` by the CLI — every wave treats any such WARN as a STOP (fix the `keep` text, re-run) before `--apply`; the tool itself does not exit non-zero on it.

- [ ] **Step 1: Write the failing test**

```python
# append to test_apply_aug21.py
from apply_aug21 import merge_locale  # noqa: E402


def _cur():
    return OrderedDict([("_meta", {"format": "name-scoped-v2"}),
                        ("item:Q1_NAME", "Ano ang pangalan mo?"),
                        ("val:Q5_SEX_VS1:1", "Babae"),          # swapped defect, kept by override
                        ("val:Q5_SEX_VS1:2", "Lalaki"),
                        ("item:Q9_OLD", "luma")])


def test_merge_absent_equal_different_override_flagged():
    pairs = {"item:Q1_NAME": "Ano ang pangalan mo?",           # equal -> already_same
             "item:Q2_ROLE": "Ano ang tungkulin mo?",          # absent -> write
             "val:Q5_SEX_VS1:1": "Lalaki",                     # different but overridden
             "val:Q5_SEX_VS1:2": "Babae",                      # different -> replace
             "item:Q7_FLAGGED": "bleed text"}                  # flagged -> never written
    overrides = {"val:Q5_SEX_VS1:1": {"keep": "Babae", "reason": "June-5 swap carried"}}
    r = merge_locale(_cur(), pairs, {"item:Q7_FLAGGED"}, overrides)
    assert r.writes == OrderedDict([("item:Q2_ROLE", "Ano ang tungkulin mo?"),
                                    ("val:Q5_SEX_VS1:2", "Babae")])
    assert r.replaced == [("val:Q5_SEX_VS1:2", "Lalaki", "Babae")]
    assert r.overridden == [("val:Q5_SEX_VS1:1", "Babae", "Lalaki")]
    assert r.already_same == 1
    assert r.flagged_skipped == 1
    assert r.override_stale == []        # keep == current map value
    assert "item:Q7_FLAGGED" not in r.writes


def test_merge_whitespace_equal_counts_as_same_and_override_stale_is_reported():
    # Q1: whitespace-only difference -> already_same.
    # Q5:1: proposed EQUALS current ("Babae") -> already_same, but the override's keep text
    # ("Lalaki") has drifted from the map -> override_stale.
    pairs = {"item:Q1_NAME": "Ano  ang pangalan mo? ", "val:Q5_SEX_VS1:1": "Babae"}
    overrides = {"val:Q5_SEX_VS1:1": {"keep": "Lalaki", "reason": "keep text drifted"}}
    r = merge_locale(_cur(), pairs, set(), overrides)
    assert r.already_same == 2
    assert r.writes == OrderedDict() and r.overridden == []
    assert r.override_stale == ["val:Q5_SEX_VS1:1"]


def test_merge_override_branch_with_stale_keep():
    # different proposal + override whose keep no longer matches the map -> overridden AND stale
    pairs = {"val:Q5_SEX_VS1:1": "Lalaki"}
    overrides = {"val:Q5_SEX_VS1:1": {"keep": "Lalake", "reason": "typo in keep"}}
    r = merge_locale(_cur(), pairs, set(), overrides)
    assert r.overridden == [("val:Q5_SEX_VS1:1", "Babae", "Lalaki")]
    assert r.override_stale == ["val:Q5_SEX_VS1:1"] and r.writes == OrderedDict()


def test_merge_unmatched_anchors_and_meta_never_touched():
    all_keys = {"item:Q1_NAME", "item:Q2_ROLE", "val:Q5_SEX_VS1:1", "val:Q5_SEX_VS1:2",
                "item:Q3_UNSEEN"}
    r = merge_locale(_cur(), {"item:Q2_ROLE": "x"}, {"val:Q5_SEX_VS1:1"}, {}, all_keys)
    assert set(r.unmatched) == {"item:Q3_UNSEEN", "item:Q1_NAME", "val:Q5_SEX_VS1:2"}
    assert "_meta" not in r.writes
```

- [ ] **Step 2: Run test to verify it fails** — Run: `python -m pytest data/translations-official/test_apply_aug21.py -q` Expected: `ERROR collecting ... ModuleNotFoundError: No module named 'apply_aug21'` (whole file stops collecting; `-k merge` would show 0 selected — run without `-k`).

- [ ] **Step 3: Write minimal implementation**

```python
# deliverables/CSPro/data/translations-official/apply_aug21.py
#!/usr/bin/env python3
r"""Merge the Aug-21 paper extract into the name-scoped translation maps.

Rule per extracted (key, translation):
    key absent in map                 -> WRITE
    present and norm-equal            -> already_same
    present and different             -> REPLACE  (Aug-21 wins)
        ... unless key is listed in aug21-overrides.json -> keep current, count OVERRIDE
    key appears in {loc}_flagged.json -> never written (flagged_skipped)
_meta is never a write target; _meta.sources.aug21 is stamped on --apply when something was written.

    python apply_aug21.py                      # dry run (default): per-locale table; touches NOTHING
    python apply_aug21.py --apply              # write the maps + _meta.sources.aug21
    python apply_aug21.py --apply --only F1
    python apply_aug21.py --only F3 --extract C:/path/to/out   # extractor out dir override
    python apply_aug21.py --only F3 --unmatched               # + unmatched-anchor column (reads the BUILT .dcf, no generator run)
    python apply_aug21.py --only F3 --seed findings.json      # candidate override rows
    python apply_aug21.py --compare-findings pre.json post.json   # scan_poisoned_keys per-reason delta gate
"""
import argparse
import datetime as _dt
import io
import json
import os
import re
import sys
from collections import Counter, OrderedDict
from dataclasses import dataclass, field

HERE = os.path.dirname(os.path.abspath(__file__))
CSPRO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, CSPRO)
sys.path.insert(0, HERE)
from apply_safe import norm, load_map, save_map          # noqa: E402
from aug21_overrides import load_overrides, OVERRIDES_PATH  # noqa: E402

if hasattr(sys.stdout, "buffer") and (sys.stdout.encoding or "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)

LOCALES = ["fil", "bcl", "bis", "ceb", "war", "hil", "ilo"]
CSPRO_INSTRUMENTS = ("F1", "F3", "F4")
DCF_FILE = {"F1": "FacilityHeadSurvey.dcf", "F3": "PatientSurvey.dcf", "F4": "HouseholdSurvey.dcf"}
EXTRACT_ROOT = os.path.join(HERE, "out-aug21")      # anchor_extract.py --out root (Task 1)


@dataclass
class MergeResult:
    writes: "OrderedDict" = field(default_factory=OrderedDict)
    replaced: list = field(default_factory=list)      # (key, old, new)
    overridden: list = field(default_factory=list)    # (key, current, proposed)
    flagged_skipped: int = 0
    already_same: int = 0
    unmatched: list = field(default_factory=list)
    override_stale: list = field(default_factory=list)


def merge_locale(current, pairs, flagged_keys, overrides, all_keys=None):
    r = MergeResult()
    seen = set()
    for key, tr in pairs.items():
        if key == "_meta" or ":" not in key:
            continue
        val = norm(tr)
        if not val:
            continue
        seen.add(key)
        if key in flagged_keys:
            r.flagged_skipped += 1
            continue
        cur = current.get(key)
        if cur is None:
            r.writes[key] = val
            continue
        if norm(cur) == val:
            r.already_same += 1
            if key in overrides and norm(overrides[key]["keep"]) != norm(cur):
                r.override_stale.append(key)
            continue
        if key in overrides:
            r.overridden.append((key, cur, val))
            if norm(overrides[key]["keep"]) != norm(cur):
                r.override_stale.append(key)
            continue
        r.replaced.append((key, cur, val))
        r.writes[key] = val
    r.flagged_skipped += len([k for k in flagged_keys if k not in pairs])
    seen |= set(flagged_keys)
    if all_keys is not None:
        r.unmatched = sorted(k for k in all_keys if k not in seen)
    return r
```

- [ ] **Step 4: Run test to verify it passes** — Run: `python -m pytest data/translations-official/test_apply_aug21.py -q` Expected: `8 passed`.

- [ ] **Step 5: Verify/gate** — `python -c "import sys; sys.path.insert(0,'data/translations-official'); import apply_aug21; print('import ok')"` from `deliverables/CSPro` Expected: `import ok` (confirms the `apply_safe` import chain — `cspro_helpers`, `migrate_maps_namekeys` — resolves; importing does NOT run a generator).

- [ ] **Step 6: Record** — none yet (no map touched).

### Task 5: `apply_aug21.py` CLI — extract loading, dry-run table, `--apply` with `_meta.sources.aug21`, `--only`, `--unmatched`

**Files:**
- Modify: `deliverables/CSPro/data/translations-official/apply_aug21.py` (append below `merge_locale`)
- Test: `deliverables/CSPro/data/translations-official/test_apply_aug21.py` (append)

**Interfaces:**
- Consumes: `merge_locale` (Task 4); `cspro_helpers.walk_labeled_nodes(dictionary)` (yields `(key, node)`) applied to the already-BUILT `F<n>/<App>.dcf` JSON for the unmatched-anchor denominator (no generator run, so no `.dcf` rewrite during a dry run); `load_map` / `save_map` from `apply_safe`.
- Produces: `load_extract(extract_dir: str, loc: str) -> tuple[dict, set]` (pairs, flagged_keys); `stamp_meta(m: OrderedDict, file: str, r: MergeResult, date: str) -> None`; `run(inst: str, extract_dir: str, map_dir: str, overrides: dict, apply: bool, all_keys: set | None, date: str) -> dict[loc, MergeResult]`; `built_dcf_keys(inst: str) -> set`; `main()`. Dry-run report `aug21_apply_diff.json` (the file every wave reads for `replaced[].was` when seeding overrides).

- [ ] **Step 1: Write the failing test**

```python
# append to test_apply_aug21.py
from apply_aug21 import load_extract, stamp_meta, run  # noqa: E402


def _write(path, obj, crlf=False, indent=2):
    txt = json.dumps(obj, ensure_ascii=False, indent=indent)
    if crlf:
        txt = txt.replace("\n", "\r\n")
    with io.open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(txt + ("\r\n" if crlf else "\n"))


def test_load_extract_reads_clean_and_flagged(tmp_path):
    _write(tmp_path / "fil.json", {"_meta": {"x": 1}, "item:Q1": "a"})
    _write(tmp_path / "fil_flagged.json", [{"key": "item:Q2", "en": "e", "tr": "t", "flags": ["table-bleed"]}])
    pairs, flagged = load_extract(str(tmp_path), "fil")
    assert pairs == {"item:Q1": "a"} and flagged == {"item:Q2"}
    assert load_extract(str(tmp_path), "war") == ({}, set())   # missing locale = empty, not error


def test_run_apply_preserves_crlf_indent_order_and_stamps_meta(tmp_path):
    ex = tmp_path / "extract"; ex.mkdir()
    maps = tmp_path / "maps"; maps.mkdir()
    _write(ex / "fil.json", {"item:Q2": "bago", "item:Q1": "iba na"})
    _write(ex / "fil_flagged.json", [{"key": "item:Q3", "en": "", "tr": "", "flags": ["empty"]}])
    _write(maps / "fil.json", OrderedDict([("_meta", {"format": "name-scoped-v2"}),
                                           ("item:Q1", "luma"), ("item:Q9", "z")]), crlf=True, indent=1)
    res = run("F1", str(ex), str(maps), {}, apply=True, all_keys=None, date="2026-08-26")
    raw = io.open(maps / "fil.json", encoding="utf-8", newline="").read()
    assert "\r\n" in raw and raw.startswith('{\r\n "_meta"')          # CRLF + 1-space indent kept
    m = json.loads(raw, object_pairs_hook=OrderedDict)
    assert list(m) == ["_meta", "item:Q1", "item:Q9", "item:Q2"]     # order kept, new key appended
    assert m["item:Q1"] == "iba na"
    assert m["_meta"]["sources"]["aug21"] == {"date": "2026-08-26", "file": "fil.json",
        "n_written": 1, "n_replaced": 1, "n_overridden": 0, "n_flagged_skipped": 1}
    assert res["fil"].replaced == [("item:Q1", "luma", "iba na")]


def test_run_dry_run_writes_nothing(tmp_path):
    ex = tmp_path / "extract"; ex.mkdir()
    maps = tmp_path / "maps"; maps.mkdir()
    _write(ex / "bcl.json", {"item:Q1": "bago"})
    _write(maps / "bcl.json", {"_meta": {}, "item:Q1": "luma"})
    before = io.open(maps / "bcl.json", encoding="utf-8").read()
    res = run("F1", str(ex), str(maps), {}, apply=False, all_keys=None, date="2026-08-26")
    assert res["bcl"].replaced and io.open(maps / "bcl.json", encoding="utf-8").read() == before


def test_run_apply_override_only_locale_is_not_rewritten(tmp_path):
    """Overrides alone change nothing -> the map file must not be touched (no _meta-only diff)."""
    ex = tmp_path / "extract"; ex.mkdir()
    maps = tmp_path / "maps"; maps.mkdir()
    _write(ex / "ceb.json", {"item:Q1": "bago"})
    _write(maps / "ceb.json", {"_meta": {}, "item:Q1": "luma"})
    before = io.open(maps / "ceb.json", encoding="utf-8").read()
    ov = {"item:Q1": {"keep": "luma", "reason": "kept"}}
    res = run("F1", str(ex), str(maps), ov, apply=True, all_keys=None, date="2026-08-26")
    assert res["ceb"].overridden == [("item:Q1", "luma", "bago")]
    assert io.open(maps / "ceb.json", encoding="utf-8").read() == before
```

- [ ] **Step 2: Run test to verify it fails** — Run: `python -m pytest data/translations-official/test_apply_aug21.py -q` Expected: `ERROR collecting ... ImportError: cannot import name 'load_extract' from 'apply_aug21'`.

- [ ] **Step 3: Write minimal implementation** (append to `apply_aug21.py`)

```python
def load_extract(extract_dir, loc):
    clean = os.path.join(extract_dir, f"{loc}.json")
    flagged = os.path.join(extract_dir, f"{loc}_flagged.json")
    if not os.path.exists(clean):
        return {}, set()
    pairs = json.loads(io.open(clean, encoding="utf-8").read())
    pairs.pop("_meta", None)
    fk = set()
    if os.path.exists(flagged):
        for row in json.loads(io.open(flagged, encoding="utf-8").read()):
            if row.get("key"):
                fk.add(row["key"])
    return pairs, fk


def stamp_meta(m, file, r, date):
    meta = m.get("_meta")
    if not isinstance(meta, dict):
        meta = OrderedDict()
        m["_meta"] = meta
        m.move_to_end("_meta", last=False)
    meta.setdefault("sources", OrderedDict())["aug21"] = OrderedDict([
        ("date", date), ("file", file),
        ("n_written", len(r.writes) - len(r.replaced)),
        ("n_replaced", len(r.replaced)),
        ("n_overridden", len(r.overridden)),
        ("n_flagged_skipped", r.flagged_skipped)])


def run(inst, extract_dir, map_dir, overrides, apply, all_keys, date):
    out = {}
    for loc in LOCALES:
        path = os.path.join(map_dir, f"{loc}.json")
        pairs, flagged = load_extract(extract_dir, loc)
        if not pairs and not flagged:
            continue
        if not os.path.exists(path):
            print(f"  {inst}/{loc}: no map file - skipped")
            continue
        m, indent, crlf = load_map(path)
        r = merge_locale(m, pairs, flagged, overrides, all_keys)
        out[loc] = r
        if apply and r.writes:                      # override-only / same-only locales: file untouched
            for k, v in r.writes.items():
                m[k] = v                              # existing keys keep position; new ones append
            stamp_meta(m, f"{loc}.json", r, date)
            save_map(path, m, indent, crlf)
    return out


def built_dcf_keys(inst):
    """Anchor denominator from the already-built F<n>/<App>.dcf (JSON) — NO generator run,
    so a dry run never rewrites the .dcf. Requires the .dcf to be current (it is regenerated
    by every generate_dcf.py / scan_poisoned_keys.py run)."""
    from cspro_helpers import walk_labeled_nodes
    path = os.path.join(CSPRO, inst, DCF_FILE[inst])
    d = json.loads(io.open(path, encoding="utf-8").read())
    keys = set()
    for key, node in walk_labeled_nodes(d):
        labs = node.get("labels") or []
        if labs and (labs[0].get("text") or "").strip():
            keys.add(key)
    return keys


def print_table(inst, results):
    print(f"\n{inst}  {'locale':<7}{'written':>8}{'replaced':>9}{'override':>9}"
          f"{'same':>6}{'flagged':>8}{'unmatched':>10}")
    for loc, r in results.items():
        print(f"    {loc:<7}{len(r.writes) - len(r.replaced):>8}{len(r.replaced):>9}"
              f"{len(r.overridden):>9}{r.already_same:>6}{r.flagged_skipped:>8}{len(r.unmatched):>10}")
        for key in r.override_stale:
            print(f"      WARN override 'keep' != current map value: {key}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write maps (default = dry run)")
    ap.add_argument("--only", choices=CSPRO_INSTRUMENTS)
    ap.add_argument("--extract", help="extractor out dir (default out-aug21/<inst>/)")
    ap.add_argument("--unmatched", action="store_true",
                    help="add the unmatched-anchor column (reads the built .dcf; no generator run)")
    ap.add_argument("--report", default=os.path.join(HERE, "aug21_apply_diff.json"))
    ap.add_argument("--seed", help="scan_poisoned_keys --apply-report JSON; print candidate override rows")
    ap.add_argument("--compare-findings", nargs=2, metavar=("PRE", "POST"),
                    help="per-reason delta gate between two scan_poisoned_keys reports; exit 1 if any reason grew")
    a = ap.parse_args()

    if a.compare_findings:
        ok = compare_findings(*a.compare_findings)      # Task 7
        raise SystemExit(0 if ok else 1)

    overrides_all = load_overrides(OVERRIDES_PATH)
    date = _dt.date.today().isoformat()
    diff = {}
    for inst in CSPRO_INSTRUMENTS:
        if a.only and inst != a.only:
            continue
        extract_dir = a.extract if (a.extract and a.only) else os.path.join(EXTRACT_ROOT, inst)
        if not os.path.isdir(extract_dir):
            print(f"  {inst}: no extract dir {extract_dir} - skipped")
            continue
        all_keys = built_dcf_keys(inst) if a.unmatched else None
        map_dir = os.path.join(CSPRO, inst, "translations")
        results = run(inst, extract_dir, map_dir, overrides_all.get(inst, {}),
                      a.apply, all_keys, date)
        print_table(inst, results)
        diff[inst] = {loc: {"writes": r.writes,
                            "replaced": [{"key": k, "was": o, "now": n} for k, o, n in r.replaced],
                            "overridden": [{"key": k, "current": c, "proposed": p} for k, c, p in r.overridden],
                            "unmatched": r.unmatched, "flagged_skipped": r.flagged_skipped,
                            "already_same": r.already_same}
                      for loc, r in results.items()}
        if a.seed:
            src = None
            if not a.apply:
                # Seeding needs the PRE-APPLY dictionary; the built .dcf already reflects the
                # current (pre-apply) maps, so read it instead of running the generator.
                src = json.loads(io.open(os.path.join(CSPRO, inst, DCF_FILE[inst]), encoding="utf-8").read())
            seed_candidates(inst, a.seed, results, src=src)
    with io.open(a.report, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(diff, fh, ensure_ascii=False, indent=1)
    print(f"\n{'APPLIED' if a.apply else 'DRY RUN'} - diff written to {a.report}")


if __name__ == "__main__":
    main()
```

(`seed_candidates` and `compare_findings` are defined in Tasks 6 and 7; until then add `def seed_candidates(*_, **__): print("  --seed not available yet")` and `def compare_findings(*_): return True` as placeholders that those tasks replace. Note the built `.dcf` carries labels for all 8 languages, but `walk_labeled_nodes` keys are language-independent and `_value_pair_key` reads only codes, so the key set equals the pre-apply generator's.)

- [ ] **Step 4: Run test to verify it passes** — Run: `python -m pytest data/translations-official/test_apply_aug21.py -q` Expected: `12 passed`.

- [ ] **Step 5: Verify/gate** — dry-run against the real F1 extract produced in Task 1 Step 5 (`out-aug21/F1/`): `python data/translations-official/apply_aug21.py --only F1 --unmatched` Expected: a table `F1  locale  written replaced override same flagged unmatched` with 7 rows, ending `DRY RUN - diff written to ...aug21_apply_diff.json`. Nothing is written: `git status --short deliverables/CSPro/F1` shows no change to `translations/*.json` NOR to `FacilityHeadSurvey.dcf` (the dry run reads the built .dcf; it does not run `generate_dcf.py`).

- [ ] **Step 6: Record** — paste the dry-run table into the wave note as the "before" row; list every `replaced` row count per locale.

### Task 6: Seed step — candidate override rows from the repair lists vs the dry-run replaced set

**Files:**
- Modify: `deliverables/CSPro/data/translations-official/apply_aug21.py` (replace the `seed_candidates` placeholder)
- Test: `deliverables/CSPro/data/translations-official/test_apply_aug21.py` (append)

**Interfaces:**
- Consumes: `MergeResult.replaced` (Task 4); findings JSON from `scan_poisoned_keys.py --apply-report out.json` = list of `{instrument, locale, reason, key, en, value}` (scan_poisoned_keys.py:176-177); `recovery_exclusions.json` `exclusions` keyed `INST|LOC|QNUM|OPTION_INDEX` (`_README` line 1); `official_translations.json` (gitignored, present) `[inst][qnum]["EN"]["options"]` for disambiguation; `cspro_helpers._value_pair_key(value)` for `val:` keys.
- Produces: `resolve_exclusion_id(src: dict, ex_id: str, official: dict | None = None) -> tuple[str | None, str]` (name-scoped `val:` key or None, plus a status string `ok | absent | ambiguous:<n> | index-out-of-range`); `seed_candidates(inst: str, findings_path: str, results: dict, src: dict | None = None, exclusions: dict | None = None, official: dict | None = None) -> list[dict]` (each `{locale, key, keep, reason, proposed}`; printed as ready-to-paste JSON; prints `WARN unresolved exclusion` for every id it could not map).

- [ ] **Step 1: Write the failing test**

```python
# append to test_apply_aug21.py
from apply_aug21 import resolve_exclusion_id, seed_candidates, MergeResult  # noqa: E402


def _vs(name, labels):
    return {"name": name, "labels": [{"text": name}],
            "values": [{"labels": [{"text": t}], "pairs": [{"value": str(i + 1)}]} for i, t in enumerate(labels)]}


SRC = {"name": "T", "levels": [{"name": "L", "ids": {"items": []}, "records": [{"name": "R", "items": [
    {"name": "Q140_WHY", "labels": [{"text": "140. Why?"}], "valueSets": [_vs("Q140_WHY_VS1", ["A", "B", "C"])]},
    # Q47: FOUR value-set-bearing items under one qnum (F3 Q47_* pattern)
    {"name": "Q47_PHYSICIAN_CHECKUP", "labels": [{"text": "47a"}], "valueSets": [_vs("Q47_PHYSICIAN_CHECKUP_VS1", ["Yes", "No"])]},
    {"name": "Q47_HOSPITAL_CONF", "labels": [{"text": "47b"}], "valueSets": [_vs("Q47_HOSPITAL_CONF_VS1", ["Yes", "No"])]},
    # Q96: checkbox + roster pair — different option lists, English disambiguates
    {"name": "Q96_SOURCES", "labels": [{"text": "96"}], "valueSets": [_vs("Q96_SOURCES_VS1", ["Out-of-pocket", "Donation"])]},
    {"name": "Q96_PAY_LINE", "labels": [{"text": "96 row"}]},
    {"name": "Q96_PAY_SRC", "labels": [{"text": "96 src"}], "valueSets": [_vs("Q96_PAY_SRC_VS1", ["Out-of-pocket", "Donation", "In kind"])]},
]}]}]}


def test_resolve_exclusion_id_maps_qnum_index_to_val_key():
    assert resolve_exclusion_id(SRC, "F1|BIS|140|2") == ("val:Q140_WHY_VS1:3", "ok")
    assert resolve_exclusion_id(SRC, "F1|BIS|999|0") == (None, "absent")
    assert resolve_exclusion_id(SRC, "F1|BIS|140|7") == (None, "index-out-of-range")


def test_resolve_exclusion_id_ambiguous_reports_count_and_english_disambiguates():
    key, status = resolve_exclusion_id(SRC, "F3|HIL|47|1")
    assert key is None and status == "ambiguous:2"
    # official English option[2] == "In kind" matches ONLY Q96_PAY_SRC_VS1 -> resolved
    official = {"F3": {"96": {"EN": {"options": ["Out-of-pocket", "Donation", "In kind"]}}}}
    assert resolve_exclusion_id(SRC, "F3|HIL|96|2", official) == ("val:Q96_PAY_SRC_VS1:3", "ok")
    # option[0] "Out-of-pocket" is in BOTH value sets -> still ambiguous
    assert resolve_exclusion_id(SRC, "F3|HIL|96|0", official) == (None, "ambiguous:2")


def test_seed_candidates_only_reports_reintroduced_keys_and_warns_unresolved(tmp_path, capsys):
    findings = tmp_path / "f.json"
    findings.write_text(json.dumps([
        {"instrument": "F1", "locale": "BIS", "reason": "IS_OTHER_EN",
         "key": "item:Q140_WHY", "en": "140. Why?", "value": "Why?"},
        {"instrument": "F1", "locale": "BIS", "reason": "DOUBLED",
         "key": "item:Q7_X", "en": "", "value": "a a"}]), encoding="utf-8")
    r = MergeResult()
    r.replaced = [("item:Q140_WHY", "Ngano?", "Why?"), ("val:Q140_WHY_VS1:3", "good", "bad")]
    rows = seed_candidates("F1", str(findings), {"bis": r}, src=SRC,
                           exclusions={"F1|BIS|140|2": {"test": "contamination", "why": "stranded word"},
                                       "F1|BIS|47|1": {"test": "offset", "why": "row shift"}},
                           official={})
    keys = {(x["locale"], x["key"]) for x in rows}
    assert keys == {("bis", "item:Q140_WHY"), ("bis", "val:Q140_WHY_VS1:3")}   # Q7_X not replaced -> absent
    rec = [x for x in rows if x["key"] == "val:Q140_WHY_VS1:3"][0]
    assert rec["keep"] == "good" and "recovery_exclusions" in rec["reason"]
    out = capsys.readouterr().out
    assert '"val:Q140_WHY_VS1:3"' in out and '"keep": "good"' in out
    assert "WARN unresolved exclusion F1|BIS|47|1: ambiguous:2" in out
```

- [ ] **Step 2: Run test to verify it fails** — Run: `python -m pytest data/translations-official/test_apply_aug21.py -q` Expected: `ERROR collecting ... ImportError: cannot import name 'resolve_exclusion_id' from 'apply_aug21'`.

- [ ] **Step 3: Write minimal implementation** (replace the placeholder in `apply_aug21.py`)

```python
EXCLUSIONS_PATH = os.path.join(HERE, "recovery_exclusions.json")
OFFICIAL_PATH = os.path.join(HERE, "official_translations.json")


def _items_with_vs(src, qnum):
    pat = re.compile(rf"^Q{re.escape(qnum.replace('.', ''))}_")
    hits = []
    for lvl in src.get("levels", []) or []:
        pool = list((lvl.get("ids") or {}).get("items", []) or [])
        for rec in lvl.get("records", []) or []:
            pool.extend(rec.get("items", []) or [])
        for it in pool:
            if pat.match(it.get("name", "")) and it.get("valueSets"):
                hits.append(it)
    return hits


def resolve_exclusion_id(src, ex_id, official=None):
    """'INST|LOC|QNUM|OPTION_INDEX' -> ('val:<VS>:<code>', 'ok') via the pre-apply dictionary.
    Unique Q<QNUM>_* item with a value set wins outright. When several items share the prefix
    (F3 Q47_*, Q1141_*/Q1142_*, every Q<n>_SOURCES + Q<n>_PAY_SRC pair) the English of
    official_translations.json[inst][qnum]['EN']['options'][idx] is matched against each
    candidate's value label at that index; exactly one match resolves, else ('ambiguous:<n>')."""
    from cspro_helpers import _value_pair_key
    parts = ex_id.split("|")
    if len(parts) != 4:
        return None, "malformed"
    inst, _loc, qnum, idx = parts[0], parts[1], parts[2], int(parts[3])
    hits = _items_with_vs(src, qnum)
    if not hits:
        return None, "absent"

    def key_at(it):
        values = (it["valueSets"][0].get("values") or [])
        if not (0 <= idx < len(values)):
            return None, None
        vs = it["valueSets"][0]
        lab = ((values[idx].get("labels") or [{}])[0].get("text") or "").strip()
        return f"val:{vs.get('name')}:{_value_pair_key(values[idx])}", lab

    if len(hits) == 1:
        key, _ = key_at(hits[0])
        return (key, "ok") if key else (None, "index-out-of-range")
    en_opts = (((official or {}).get(inst, {}).get(qnum, {}) or {}).get("EN", {}) or {}).get("options") or []
    if 0 <= idx < len(en_opts):
        want = norm(en_opts[idx]).casefold()
        matched = [k for k, lab in (key_at(h) for h in hits) if k and norm(lab).casefold() == want]
        if len(matched) == 1:
            return matched[0], "ok"
    return None, f"ambiguous:{len(hits)}"


def seed_candidates(inst, findings_path, results, src=None, exclusions=None, official=None):
    """Candidate override rows = repair-list keys that the Aug-21 extract would REPLACE.
    Prints ready-to-paste aug21-overrides.json rows; the human confirms each one.
    Every recovery_exclusions id that cannot be mapped is printed as a WARN so the seed is
    never silently incomplete."""
    findings = json.loads(io.open(findings_path, encoding="utf-8").read()) if findings_path else []
    if exclusions is None:
        exclusions = json.loads(io.open(EXCLUSIONS_PATH, encoding="utf-8").read()).get("exclusions", {})
    if official is None:
        official = (json.loads(io.open(OFFICIAL_PATH, encoding="utf-8").read())
                    if os.path.exists(OFFICIAL_PATH) else {})
    if src is None:
        src = json.loads(io.open(os.path.join(CSPRO, inst, DCF_FILE[inst]), encoding="utf-8").read())
    replaced = {(loc, k): (old, new) for loc, r in results.items() for k, old, new in r.replaced}
    rows = []
    for f in findings:
        if f.get("instrument") != inst:
            continue
        hit = (f.get("locale", "").lower(), f.get("key"))
        if hit in replaced:
            old, new = replaced[hit]
            rows.append({"locale": hit[0], "key": hit[1], "keep": old, "proposed": new,
                         "reason": f"scan_poisoned_keys {f.get('reason')} on the Aug-14/17 pass; Aug-21 re-introduces it"})
    unresolved = []
    for ex_id, ent in exclusions.items():
        p = ex_id.split("|")
        if len(p) != 4 or p[0] != inst:
            continue
        key, status = resolve_exclusion_id(src, ex_id, official)
        if key is None:
            unresolved.append((ex_id, status))
            continue
        hit = (p[1].lower(), key)
        if hit in replaced:
            old, new = replaced[hit]
            rows.append({"locale": hit[0], "key": key, "keep": old, "proposed": new,
                         "reason": f"recovery_exclusions {ex_id} ({ent.get('test')}): {ent.get('why', '')[:120]}"})
    for ex_id, status in unresolved:
        print(f"  WARN unresolved exclusion {ex_id}: {status} - check by hand against aug21_apply_diff.json")
    print(f"\n  {inst}: {len(rows)} candidate override row(s), {len(unresolved)} unresolved exclusion id(s) — "
          f"paste the ones you confirm into aug21-overrides.json[{inst!r}]")
    for row in rows:
        print(f"    [{row['locale']}] proposed: {row['proposed'][:80]!r}")
        print("    " + json.dumps({row["key"]: {"keep": row["keep"], "reason": row["reason"]}},
                                  ensure_ascii=False))
    return rows
```

- [ ] **Step 4: Run test to verify it passes** — Run: `python -m pytest data/translations-official/test_apply_aug21.py -q` Expected: `15 passed`.

- [ ] **Step 5: Verify/gate** — per wave, before `--apply` (F1 shown; the same five sub-steps are run by Tasks 17, 28 and 39):
  1. `python data/translations-official/scan_poisoned_keys.py --apply-report data/translations-official/aug21_pre_findings.json` — SIDE EFFECT: this regenerates the three `.dcf` from the current (pre-apply) maps; expected and wanted, because Tasks 5/6 read the built `.dcf`. Prints a per-reason tally then `TOTAL suspect entries: N_pre` and `Wrote ...aug21_pre_findings.json`. Record `N_pre` and the per-reason tally in the wave note — this is the baseline for the Task 7 gate.
  2. `python data/translations-official/apply_aug21.py --only F1 --seed data/translations-official/aug21_pre_findings.json` Expected: the dry-run table, zero or more `WARN unresolved exclusion <id>: <status>` lines (resolve each by hand: look the qnum up in `aug21_apply_diff.json[F1][loc].replaced` and decide), then `F1: N candidate override row(s), M unresolved exclusion id(s)` and one JSON line per row.
  3. Paste confirmed rows into `aug21-overrides.json` under `"F1"`, then `python data/translations-official/aug21_overrides.py` → `OK`.
  4. Re-run the dry-run; the `override` column must equal the number of rows pasted and `WARN override 'keep' != current` must not print (any WARN = STOP: paste the verbatim current map value into `keep`, never a paraphrase or a placeholder).

- [ ] **Step 6: Record** — in the wave note: every override key with its reason (spec close-out: "every override to a reason"), every unresolved exclusion id and how it was settled; the pre-findings JSON stays gitignored data.

### Task 7: Apply + post-merge gates (`scan_poisoned_keys.py` per-reason delta, `bridge_check.py` B/C delta)

**Files:**
- Modify: `deliverables/CSPro/F<n>/translations/{fil,bcl,bis,ceb,war,hil,ilo}.json` (written by `apply_aug21.py --apply` only — never by hand)
- Modify: `deliverables/CSPro/data/translations-official/apply_aug21.py` (replace the `compare_findings` placeholder)
- Create: `deliverables/CSPro/data/translations-official/run_aug21_gates.ps1`
- Modify: repo-root `.gitignore` (append after line 208, the `TICKET-COUNTER-CHECK.md` line of the translations-official block)
- Test: `deliverables/CSPro/data/translations-official/test_apply_aug21.py` (append)

**Interfaces:**
- Consumes: `apply_aug21.main()` `--apply --only F<n>`; `scan_poisoned_keys.py` (CLI `python scan_poisoned_keys.py [--apply-report out.json]`, prints `TOTAL suspect entries: N` at :182, report = list of `{instrument, locale, reason, key, value[, en]}`); `aug17-tools/bridge_check.py --check` (prints `Scanned 3 instruments x 7 locales.` and `Total defects found: N` at :365-366, per-file `  <inst>/<loc>.json: N defect(s)` at :372, per-row lines carry the rule tag `A-mismatch` / `B-admin-leak` / `C-glued-fragments`; never exits non-zero); `cspro_helpers.apply_translations(dictionary, translations_dir)` hard-fails on any key without `':'` (:1175-1180) and pops `_meta` (:1174).
- Produces: the merged maps + `_meta.sources.aug21` per written locale; `compare_findings(pre_path: str, post_path: str) -> bool` (prints a per-reason `pre / post / delta` table, True iff no reason grew); `run_aug21_gates.ps1 -Inst F<n> [-PreBridge N]` exiting 0 only when (gate 1) no scan reason grew versus `aug21_pre_findings.json` and (gate 2) the bridge_check B/C defect count did not grow versus the pre-apply run. Every wave (Tasks 17, 28, 40) runs this wrapper after its `--apply`.

- [ ] **Step 1: Write the failing test**

```python
# append to test_apply_aug21.py
from apply_aug21 import compare_findings  # noqa: E402


def test_stamped_map_still_loads_through_apply_translations_contract(tmp_path):
    """apply_translations pops _meta and rejects any key without ':' — the stamp must not add one."""
    maps = tmp_path / "maps"; maps.mkdir()
    ex = tmp_path / "ex"; ex.mkdir()
    _write(ex / "ilo.json", {"item:Q1": "bago"})
    _write(maps / "ilo.json", {"item:Q1": "daan"})           # no _meta at all
    run("F4", str(ex), str(maps), {}, apply=True, all_keys=None, date="2026-08-26")
    m = json.loads(io.open(maps / "ilo.json", encoding="utf-8").read(), object_pairs_hook=OrderedDict)
    assert list(m)[0] == "_meta"                                # stamp created + moved to the front
    m.pop("_meta", None)
    assert [k for k in m if ":" not in k] == []                 # nothing legacy-shaped left behind


def test_compare_findings_per_reason_delta(tmp_path, capsys):
    pre = tmp_path / "pre.json"; post = tmp_path / "post.json"
    row = lambda reason, key: {"instrument": "F1", "locale": "FIL", "reason": reason, "key": key, "value": "v"}
    pre.write_text(json.dumps([row("WRONG_Q_CLEARED", "item:A"), row("WRONG_Q_CLEARED", "item:B"),
                               row("DOUBLED", "item:C")]), encoding="utf-8")
    post.write_text(json.dumps([row("WRONG_Q_CLEARED", "item:A"), row("DOUBLED", "item:C")]), encoding="utf-8")
    assert compare_findings(str(pre), str(post)) is True        # shrank + equal -> ok
    post.write_text(json.dumps([row("DOUBLED", "item:C"), row("SELF_ECHO", "item:D")]), encoding="utf-8")
    assert compare_findings(str(pre), str(post)) is False       # SELF_ECHO 0 -> 1 grew
    out = capsys.readouterr().out
    assert "SELF_ECHO" in out and "GREW" in out and "item:D" in out
```

- [ ] **Step 2: Run test to verify it fails** — Run: `python -m pytest data/translations-official/test_apply_aug21.py -q` Expected: the contract test PASSES already if Task 5's `stamp_meta` is correct (if it fails with `list(m)[0] == 'item:Q1'`, `move_to_end("_meta", last=False)` is missing — fix in `stamp_meta`); `test_compare_findings_per_reason_delta` FAILS with `AssertionError` (`compare_findings` is still the `return True` placeholder, so the second assert `is False` fails).

- [ ] **Step 3: Write minimal implementation**

`compare_findings` (replace the placeholder in `apply_aug21.py`):

```python
def compare_findings(pre_path, post_path):
    """scan_poisoned_keys per-reason delta gate. The scan compares against the JUNE-5 cleared
    corpus (official_translations.json), so Aug-21 rewordings can be legitimate suspects; the
    gate is therefore post <= pre per reason, not zero. Prints new keys for any reason that grew."""
    def load(p):
        rows = json.loads(io.open(p, encoding="utf-8").read())
        return rows, Counter(r.get("reason", "?") for r in rows)
    pre_rows, pre = load(pre_path)
    post_rows, post = load(post_path)
    pre_keys = {(r.get("instrument"), r.get("locale"), r.get("key")) for r in pre_rows}
    ok = True
    print(f"\n  {'reason':<18}{'pre':>6}{'post':>6}{'delta':>7}")
    for reason in sorted(set(pre) | set(post)):
        d = post[reason] - pre[reason]
        tag = "  GREW" if d > 0 else ""
        ok = ok and d <= 0
        print(f"  {reason:<18}{pre[reason]:>6}{post[reason]:>6}{d:>+7}{tag}")
        if d > 0:
            for r in post_rows:
                if r.get("reason") == reason and (r.get("instrument"), r.get("locale"), r.get("key")) not in pre_keys:
                    print(f"      NEW {r.get('instrument')}/{r.get('locale')} {r.get('key')}: {str(r.get('value'))[:80]!r}")
    print(f"  scan gate: {'OK' if ok else 'FAILED'} (total {sum(pre.values())} -> {sum(post.values())})")
    return ok
```

The gate wrapper (PowerShell 5.1: no `2>&1` on native exes, every `Select-String` guarded, `-Inst` used only to focus the bridge_check per-file lines since both tools scan all three instruments):

```powershell
# deliverables/CSPro/data/translations-official/run_aug21_gates.ps1
# Usage (from deliverables/CSPro):  .\data\translations-official\run_aug21_gates.ps1 -Inst F1 [-PreBridge 18]
#   -Inst      focuses the bridge_check per-file lines; BOTH tools scan all three instruments.
#   -PreBridge B/C defect count measured BEFORE --apply (see step 5); default = 0 rows (i.e. any B/C is a fail).
param(
    [Parameter(Mandatory=$true)][ValidateSet("F1","F3","F4")][string]$Inst,
    [int]$PreBridge = 0
)
$env:PYTHONIOENCODING = "utf-8"
$here  = Split-Path -Parent $MyInvocation.MyCommand.Path
$cspro = (Resolve-Path (Join-Path $here "..\..")).Path
$pre   = Join-Path $here "aug21_pre_findings.json"
$post  = Join-Path $here "aug21_post_findings.json"
if (-not (Test-Path $pre)) { Write-Host "missing $pre - run scan_poisoned_keys.py --apply-report BEFORE --apply (Task 6 step 5.1)"; exit 1 }
Push-Location $cspro
try {
    Write-Host "== gate 1: scan_poisoned_keys.py (regenerates the .dcf files as a side effect)"
    $scan = & python (Join-Path $here "scan_poisoned_keys.py") --apply-report $post
    $m = $scan | Select-String -Pattern "^TOTAL suspect entries: (\d+)"
    if (-not $m) { Write-Host "scan did not complete (no TOTAL line):"; $scan | Select-Object -Last 15; exit 1 }
    $scanTotal = $m.Matches[0].Groups[1].Value
    & python (Join-Path $here "apply_aug21.py") --compare-findings $pre $post
    $scanOk = ($LASTEXITCODE -eq 0)

    Write-Host "== gate 2: bridge_check.py --check (Rule A = June-5 legacy mismatch, EXPECTED after Aug-21 replaces; only B/C count)"
    $bridge = & python (Join-Path $cspro "aug17-tools\bridge_check.py") --check
    $t = $bridge | Select-String -Pattern "^Total defects found: (\d+)"
    if (-not $t) { Write-Host "bridge_check did not complete:"; $bridge | Select-Object -Last 15; exit 1 }
    $bridgeTotal = [int]$t.Matches[0].Groups[1].Value
    $bc = @($bridge | Select-String -Pattern "B-admin-leak|C-glued-fragments")
    $bridgeBC = $bc.Count
    $bridge | Select-String -Pattern "^Scanned|^Total defects found|^  $Inst/"
    $bc | ForEach-Object { Write-Host "  B/C: $_" }
    $bridgeOk = ($bridgeBC -le $PreBridge)

    Write-Host ("== {0} gates: scan total={1} ({2})  bridge total={3} (A-mismatch ignored), B/C={4} vs pre {5} ({6})" -f
        $Inst, $scanTotal, $(if ($scanOk) {"no reason grew"} else {"a reason GREW"}),
        $bridgeTotal, $bridgeBC, $PreBridge, $(if ($bridgeOk) {"ok"} else {"GREW"}))
    if (-not ($scanOk -and $bridgeOk)) { Write-Host "GATES FAILED - do not regenerate"; exit 1 }
    Write-Host "GATES CLEAN - proceed to generate_dcf.py"; exit 0
} finally { Pop-Location }
```

Root `.gitignore` addition (append directly after the existing line 208 `/deliverables/CSPro/data/translations-official/TICKET-COUNTER-CHECK.md`; there is NO folder-level `.gitignore` and none should be created; `out-aug21/` and `out-delta/` were already added in Task 0):

```
/deliverables/CSPro/data/translations-official/aug21_apply_diff.json
/deliverables/CSPro/data/translations-official/aug21_pre_findings.json
/deliverables/CSPro/data/translations-official/aug21_post_findings.json
```

Then the apply itself (per wave, F1 shown):

```powershell
$env:PYTHONIOENCODING='utf-8'
# baselines (pre-apply; scan already ran in Task 6 step 5.1 and wrote aug21_pre_findings.json)
python aug17-tools\bridge_check.py --check | Select-String "B-admin-leak|C-glued-fragments|^Total"   # note the B/C row count -> $preBC (2026-08-25: total 18, all rows to be classified on first run)
python data\translations-official\apply_aug21.py --only F1            # dry run, review table
python data\translations-official\apply_aug21.py --only F1 --apply    # writes F1/translations/*.json
.\data\translations-official\run_aug21_gates.ps1 -Inst F1 -PreBridge $preBC
```

- [ ] **Step 4: Run test to verify it passes** — Run: `python -m pytest data/translations-official/test_apply_aug21.py -q` Expected: `17 passed`.

- [ ] **Step 5: Verify/gate** — exact commands and expected clean output (run from `deliverables/CSPro`):
  - Gate 1: `python data/translations-official/scan_poisoned_keys.py --apply-report data/translations-official/aug21_post_findings.json` (side effect: regenerates the three `.dcf` from the now-merged maps) then `python data/translations-official/apply_aug21.py --compare-findings data/translations-official/aug21_pre_findings.json data/translations-official/aug21_post_findings.json` Expected: the per-reason table with no `GREW` tag and a final `scan gate: OK (total N_pre -> N_post)`, exit 0. If a reason GREW, each `NEW <inst>/<loc> <key>` line is triaged: WRONG_Q_CLEARED / GLUED_CLEARED rows are checked against the Aug-21 PDF (the scan's reference corpus is June-5, so a legitimate Aug-21 rewording can land here — if the Aug-21 text is right, accept it and note it; do NOT auto-fail); DOUBLED / SELF_ECHO / IS_OTHER_EN / EN_FRAGMENT rows are real: add an override (`keep` = `aug21_apply_diff.json[inst][loc].replaced[].was`) and re-run `--apply` (idempotent: re-applied rows count as `same`).
  - Gate 2: `python aug17-tools/bridge_check.py --check` Expected: `Scanned 3 instruments x 7 locales.`, `Total defects found: N` where N may be ABOVE the 18 baseline (every replaced `item:` key with a legacy entry adds an `A-mismatch` — triage-only by the tool's own docstring), and the count of rows tagged `B-admin-leak` / `C-glued-fragments` not above the pre-apply count. Any new B/C row → override or fix, then re-apply.
  - Wrapper: `.\data\translations-official\run_aug21_gates.ps1 -Inst F1 -PreBridge <preBC>` Expected final lines `== F1 gates: scan total=... (no reason grew)  bridge total=... (A-mismatch ignored), B/C=k vs pre k (ok)` then `GATES CLEAN - proceed to generate_dcf.py`, exit 0.
  - Then the build gate for the wave: `python F1/generate_dcf.py` prints `    FIL: <m>/<t> labels translated (<pct>%)` for the 7 locales — record all seven against the baseline (F1 FIL67 BCL67 BIS67 CEB63 WAR67 HIL66 ILO62; remember the % counts key presence, not real translation), and `python automation/verify_questions.py F1` must end `=== per-question verification: F1 PASS`.
  - Confirm provenance landed: `python -c "import json;print(json.load(open('F1/translations/fil.json',encoding='utf-8'))['_meta']['sources']['aug21'])"` Expected: `{'date': '2026-08-2x', 'file': 'fil.json', 'n_written': ..., 'n_replaced': ..., 'n_overridden': ..., 'n_flagged_skipped': ...}` for every locale that had writes (a locale with only `same`/override activity is untouched and has no stamp — that is by design; its override count is in `aug21_apply_diff.json`).

- [ ] **Step 6: Record** — in the wave note: the dry-run table, the scan per-reason pre/post table, the bridge totals (`total` incl. A-mismatch, and B/C pre → post; 2026-08-25 baseline total = 18), the 7 before/after coverage percentages, and the `_meta.sources.aug21` counters per written locale. `aug21_apply_diff.json`, `aug21_pre_findings.json`, `aug21_post_findings.json` and `out-aug21/` are gitignored via the root `.gitignore`; `apply_aug21.py`, `aug21_overrides.py`, `aug21-overrides.json`, `run_aug21_gates.ps1`, `test_apply_aug21.py`, the `.gitignore` edit and the merged maps stay in the working tree for Carl to commit — no git step here.

---

## Notes layer + ICF consent from the Aug-21 PDFs (Day 0 tooling, consumed by waves 1/3/4)

Ground truth read 2026-08-25 (all paths under `C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSPro/`):

- `data/translations-official/extract_notes.py` has one flag (`--json`), reads pre-dumped `text/<INST>_<LOC>.txt`, and never opens a PDF. `english_notes(inst)` scrapes `(SECTION_)INTROS` + `_UPPER` constants from `<INST>/generate_qsf.py`; `find_translation(hay_lines, english)` slices the text after the full English match; `norm`, `looks_english`, `polish` are the reusable primitives. Two properties of those primitives drive the tests below: **`polish()` strips the terminal period** (`.strip(" .:-")` at :158) — every note in `notes.json` ends without `.` by design; and **`looks_english()` (:74-76) counts ≥3 English function words after stripping only acronyms** (`ALLOWED_EN` :70-71: UHC, PhilHealth, YAKAP, DOH, HMO, …) — the spelled-out program names ("Guaranteed and Accessible Medications for Outpatient Treatment", "Department of Health") are NOT stripped, so a translated consent paragraph that keeps them is rejected as English. `notes.json` top-level keys today: `F1`, `F3`, `F4` (13/13, 25/24, 27/23 english/translated keys). The module-constant scrape regex at `extract_notes.py:60` is `^(_[A-Z_]+)` — Task 8 widens it to `^(_[A-Z0-9_]+)` so a digit in a constant NAME cannot hide an anchor (Task 25 still names its gate constants digit-free by convention).
- `notes_lookup.py`: `_load()` flattens every top-level block via `block.get("english", {})` / `block.get("translations", {})` — a new top-level dict without those keys is skipped harmlessly; **first writer wins** (F1 → F3 → F4), so Aug-21-wins has to be enforced in `notes.json` values. `coverage()` exists but no generator prints it.
- `icf_content.py`: `SCREENS[inst] = ([screen1 paras], [screen2 paras])`, English only; contact blocks start with `<b>`; `build_screen_html(instrument, part, logo_html="")` has no language; `clearance_html` hardcodes `Translated Questionnaire ver. 06/05/2026`. F1 and F3 paragraph 1 contain a double space (`"(ASPSI).  We are here"`, :35 and :101) — the new code must NOT collapse whitespace or the EN body changes by a byte. Each `F{1,3,4}/generate_qsf.py` builds `OVERRIDES = {"ICF_PART1": _icf.build_screen_html("F1", 1, _LOGO_HTML), ...}` and consumes it as `ov = OVERRIDES.get(nm)` then `body = ov or (...)` (F1 :451, F4 :559) / `if ov: body = ov` (F3 :516-517) inside `for lnm, _ in langs:` where `lnm` is the dcf language code (`EN`, `FIL`, `BCL`, ...). F3 (:381) and F4 (:21) import `generate_dcf` at module top level — importing the three generators in one process needs `sys.modules` cleared between them.
- Aug-21 PDF ICF page (verified on all 21 translated PDFs, page 1): the paper's paragraph 1 reads *"Hello, my name is (data collector name). I work for Asian Social Project Services, Inc. (ASPSI). I am here to invite you …"* while `SCREENS` reads *"We work for … We are here to invite you …"* — the **head differs, the tail is identical** ("…participate in a study about the Universal Health Care (UHC) … Please let me tell you more about the study."), so paragraph 1 needs a **suffix anchor**. The translated paragraph 1 in every locale keeps the English program names verbatim, so plain `looks_english()` rejects all 21 of them — `extract_icf` needs its own acceptance test (Task 10). **F1-Tagalog paragraph 2 is a paper defect in the ENGLISH line only**: it prints F3's coverage sentence ("The questions will cover your Patient Profile…") above the CORRECT F1 Tagalog ("Layunin ng pag-aaral na ito na makalikom ng ebidensya … profile ng pasilidad at/o pinuno ng pasilidad …"). The automatic drop is right (the candidate starts with the English tail), but the Tagalog itself is good and is seeded via override. The contact table on screen 2 prints cell-by-cell (`Office  Email  Contact No …`), so the `<b>` blocks are never located as boundaries and the candidate after "…you may contact:" runs into the table furniture unless stopped. Ilocano prints the translation glued on the same line as the English (no newline) — the flattened-blob approach handles it. Header stamp: 20 of 21 PDFs print `Translated Questionnaire ver. 08/21/2026`; **F3-Tagalog still prints 06/05/2026 on both lines** — keep 08/21/2026 for all three instruments regardless.
- Override convention shared with the map merge (`aug21-overrides.json`, Task 3): `{ "<INST>": { "<key>": { "keep": "...", "reason": "..." } } }`. Notes and ICF entries use locale-suffixed keys: `note:intro:4:FIL`, `icf:1:0:HIL`. **`"keep": ""` means "render English"** — an empty value is treated as missing by `translate_note`/`screens_for`, which is the documented way to suppress a paragraph that extracted badly (the validator in Task 3 accepts an empty `keep` only for `note:`/`icf:` keys).

### Task 8: `extract_notes.py` — `--source DIR`, `--provenance aug21`, Aug-21-wins merge

**Files:**
- Modify: `deliverables/CSPro/data/translations-official/extract_notes.py:26-36` (imports/constants), `:60` (const regex), `:164-196` (`main`)
- Test: `deliverables/CSPro/data/translations-official/test_notes_icf_aug21.py` (new)

**Interfaces:**
- Consumes: `norm(s)`, `english_notes(inst)`, `find_translation(hay_lines, english)`, `LOCALES` (all existing in `extract_notes.py`); `notes_lookup._load()` block shape `{english:{key:EN}, translations:{key:{LOC:text}}}`.
- Produces: `PAPER_LANG` dict (paper language word → locale code), `PAPER_NAME` regex, `pdf_lines(path) -> list[str]`, `dump_source(source_dir, text_dir) -> dict[(inst, loc)] = filename`, `load_overrides(path) -> dict`, `merge_notes(existing, fresh, overrides, provenance) -> (merged, counts)` where `counts = {"written", "replaced", "overridden", "kept_prior"}`, CLI `python extract_notes.py --source DIR --provenance aug21 --json notes.json`. Task 10 imports `norm`, `looks_english`, `polish`, `PAPER_LANG`, `PAPER_NAME`, `pdf_lines`, `load_overrides` from this module. Widened const regex `^(_[A-Z0-9_]+)` (line 60) so Task 25/29 constants are scraped as `const:<NAME>` anchors.

- [ ] **Step 1: Write the failing test**

```python
# deliverables/CSPro/data/translations-official/test_notes_icf_aug21.py
"""Aug-21 notes + ICF tooling. NOTE: extract_notes.polish() strips the terminal period of
every note by design, so note comparisons use .rstrip('.'); ICF paragraphs (Task 10) keep
their terminal punctuation and are compared verbatim."""
import io, json, os, sys
import fitz
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
CSPRO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, CSPRO)

import extract_notes as en_mod  # noqa: E402

EN_INTRO = "Now I will ask you some questions about the services offered at this facility."
FIL_INTRO = "Ngayon ay magtatanong ako ng ilang katanungan tungkol sa mga serbisyong inaalok sa pasilidad na ito."


def make_pdf(path, text):
    doc = fitz.open()
    page = doc.new_page()
    rc = page.insert_textbox(fitz.Rect(30, 30, 565, 810), text, fontsize=7, fontname="helv")
    assert rc >= 0, "synthetic page overflowed"
    doc.save(path)
    doc.close()


def test_dump_source_names_files_by_instrument_and_locale(tmp_path):
    src = tmp_path / "Translations"; src.mkdir()
    make_pdf(str(src / "F1-Tagalog_Facility Head Survey Questionnaire_UHC Year 2_Aug21.pdf"),
             EN_INTRO + "\n" + FIL_INTRO + "\nREAD ALL OPTIONS.")
    make_pdf(str(src / "F2-Tagalog_Healthcare Worker Survey Questionnaire_UHC Year 2_Aug21.pdf"), "x")
    out = tmp_path / "text-aug21"
    written = en_mod.dump_source(str(src), str(out))
    assert list(written) == [("F1", "FIL")]           # F2 is not a CSPro instrument
    raw = (out / "F1_FIL.txt").read_bytes()           # binary: text-mode read would hide CRLF
    assert b"magtatanong" in raw and b"\r\n" not in raw


def test_find_translation_on_synthetic_aug21_page(tmp_path):
    pdf = tmp_path / "F1-Tagalog_x_Aug21.pdf"
    make_pdf(str(pdf), EN_INTRO + "\n" + FIL_INTRO + "\nREAD ALL OPTIONS.")
    lines = en_mod.pdf_lines(str(pdf))
    assert en_mod.find_translation(lines, EN_INTRO) == FIL_INTRO.rstrip(".")   # polish() drops the period


def test_merge_notes_aug21_wins_except_override():
    existing = {"F1": {"english": {"intro:1": EN_INTRO, "intro:2": "Second English note here."},
                       "translations": {"intro:1": {"FIL": "LUMA", "BCL": "luma-bcl"},
                                        "intro:2": {"FIL": "keep-me"}}}}
    fresh = {"F1": {"english": {"intro:1": EN_INTRO, "intro:2": "Second English note here."},
                    "translations": {"intro:1": {"FIL": FIL_INTRO, "BCL": "bago-bcl", "ILO": "baro"},
                                     "intro:2": {}}}}
    overrides = {"F1": {"note:intro:1:BCL": {"keep": "luma-bcl", "reason": "Aug-21 BCL re-glues Q2"}}}
    merged, counts = en_mod.merge_notes(existing, fresh, overrides,
                                        {"date": "2026-08-25", "source": "raw/x", "files": {}})
    t = merged["F1"]["translations"]
    assert t["intro:1"]["FIL"] == FIL_INTRO          # replaced
    assert t["intro:1"]["BCL"] == "luma-bcl"         # overridden
    assert t["intro:1"]["ILO"] == "baro"             # written
    assert t["intro:2"]["FIL"] == "keep-me"          # Aug-21 empty -> prior kept
    assert counts == {"written": 1, "replaced": 1, "overridden": 1, "kept_prior": 1}
    assert merged["_provenance"]["aug21"]["n_replaced"] == 1
    assert "english" not in merged["_provenance"]    # notes_lookup._load skips it


def test_merge_notes_reworded_english_drops_stale_prior_but_keeps_fresh():
    existing = {"F3": {"english": {"intro:4": "OLD wording."},
                       "translations": {"intro:4": {"FIL": "old", "BCL": "old-bcl"}}}}
    fresh = {"F3": {"english": {"intro:4": "NEW wording."},
                    "translations": {"intro:4": {"FIL": "bago"}}}}
    merged, counts = en_mod.merge_notes(existing, fresh, {},
                                        {"date": "2026-08-25", "source": "x", "files": {}})
    assert merged["F3"]["english"]["intro:4"] == "NEW wording."
    assert merged["F3"]["translations"]["intro:4"] == {"FIL": "bago"}   # stale BCL gone, fresh FIL in
    assert counts["written"] == 1 and counts["kept_prior"] == 0


def test_const_regex_accepts_digits_in_constant_names():
    # extract_notes.py:60 widened from ^(_[A-Z_]+) to ^(_[A-Z0-9_]+) — a digit in a NAME must not hide an anchor
    assert en_mod._CONST_RE.match("_GATE_Q112 = 'x'")
```

- [ ] **Step 2: Run test to verify it fails** — Run (from `deliverables/CSPro`): `$env:PYTHONIOENCODING='utf-8'; python -m pytest data/translations-official/test_notes_icf_aug21.py -q` Expected: FAIL with `AttributeError: module 'extract_notes' has no attribute 'dump_source'`.

- [ ] **Step 3: Write minimal implementation** — in `extract_notes.py`, first widen the module-constant regex at line 60 (whatever its local name is — name it `_CONST_RE` if it is an inline literal) from `^(_[A-Z_]+)` to `^(_[A-Z0-9_]+)`. Then, after `LOCALES = [...]` (line 36) add:

```python
# Aug-21 pack: raw/Survey-Instruments-2026-08-21/Translations/F{n}-{Language}_..._Aug21.pdf
PAPER_LANG = {"Tagalog": "FIL", "Bicolano": "BCL", "Bisaya": "BIS", "Cebuano": "CEB",
              "Waray": "WAR", "Hiligaynon": "HIL", "Ilocano": "ILO"}
PAPER_NAME = re.compile(r"^(F[134])-([A-Za-z]+)_.*\.pdf$")


def pdf_lines(path):
    """Whole PDF as text lines (PyMuPDF), same shape as the text/ dumps."""
    import fitz
    doc = fitz.open(path)
    txt = "\n".join(p.get_text() for p in doc)
    doc.close()
    return txt.split("\n")


def dump_source(source_dir, text_dir):
    """PDF -> <INST>_<LOC>.txt under text_dir (LF, utf-8). -> {(inst, loc): filename}."""
    os.makedirs(text_dir, exist_ok=True)
    written = OrderedDict()
    for name in sorted(os.listdir(source_dir)):
        m = PAPER_NAME.match(name)
        if not m or m.group(2) not in PAPER_LANG:
            continue
        inst, loc = m.group(1), PAPER_LANG[m.group(2)]
        with io.open(os.path.join(text_dir, f"{inst}_{loc}.txt"), "w",
                     encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(pdf_lines(os.path.join(source_dir, name))))
        written[(inst, loc)] = name
    return written


def load_overrides(path):
    """aug21-overrides.json -> {INST: {key: {keep, reason}}}; {} when absent.
    keep == "" means: render English (empty is 'missing' to every consumer)."""
    if not path or not os.path.exists(path):
        return {}
    return json.load(io.open(path, encoding="utf-8"))


def merge_notes(existing, fresh, overrides, provenance):
    """Aug-21-wins on the full English string; override keys note:<key>:<LOC> keep prior.
    A fresh EMPTY never clears a prior value (kept_prior). When the English of a key was
    reworded since the prior file, the prior translations are STALE and are dropped, but
    the fresh ones are still written."""
    counts = {"written": 0, "replaced": 0, "overridden": 0, "kept_prior": 0}
    merged = OrderedDict()
    for inst in ("F1", "F3", "F4"):
        old = existing.get(inst, {}) or {}
        new = fresh.get(inst, {}) or {}
        old_english = old.get("english") or {}
        english = OrderedDict(new.get("english") or old_english)
        trans = OrderedDict()
        keys = list(dict.fromkeys(list((old.get("translations") or {}))
                                  + list((new.get("translations") or {}))))
        ov = overrides.get(inst, {})
        for key in keys:
            if key not in english:
                continue                       # note no longer exists in the generator
            prior = dict((old.get("translations") or {}).get(key, {}))
            if key in old_english and old_english[key] != english[key]:
                prior = {}                     # reworded English: prior values are stale
            cand = (new.get("translations") or {}).get(key, {})
            row = OrderedDict(prior)
            for lg in LOCALES:
                val = (cand.get(lg) or "").strip()
                if not val:
                    if prior.get(lg):
                        counts["kept_prior"] += 1
                    continue
                okey = f"note:{key}:{lg}"
                if okey in ov:
                    row[lg] = ov[okey].get("keep", prior.get(lg, val))
                    counts["overridden"] += 1
                elif prior.get(lg):
                    if norm(prior[lg]) != norm(val):
                        counts["replaced"] += 1
                    row[lg] = val
                else:
                    row[lg] = val
                    counts["written"] += 1
            if row:
                trans[key] = row
        merged[inst] = OrderedDict([("english", english), ("translations", trans)])
    merged["_provenance"] = OrderedDict(existing.get("_provenance", {}))
    merged["_provenance"]["aug21"] = OrderedDict(
        [("date", provenance["date"]), ("source", provenance["source"]),
         ("files", provenance.get("files", {})),
         ("n_written", counts["written"]), ("n_replaced", counts["replaced"]),
         ("n_overridden", counts["overridden"]), ("n_kept_prior", counts["kept_prior"])])
    return merged, counts
```

Replace `main()` (lines 164-196) with:

```python
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    ap.add_argument("--source", help="folder of F{n}-{Language}_..._Aug21.pdf; dumps text first")
    ap.add_argument("--provenance", choices=["june5", "aug21"], default="june5")
    ap.add_argument("--text-dir", help="default: text/ (june5) or text-aug21/ (aug21)")
    ap.add_argument("--overrides", default=os.path.join(HERE, "aug21-overrides.json"))
    ap.add_argument("--merge-into", default=os.path.join(HERE, "notes.json"),
                    help="prior notes.json to merge onto (aug21 only)")
    a = ap.parse_args()

    text_dir = a.text_dir or (os.path.join(HERE, "text-aug21") if a.provenance == "aug21" else TEXT)
    files = {}
    if a.source:
        files = {f"{i}_{l}": n for (i, l), n in dump_source(a.source, text_dir).items()}
        print(f"dumped {len(files)} PDFs -> {text_dir}")

    result = {}
    for inst in ("F1", "F3", "F4"):
        notes = english_notes(inst)
        result[inst] = {"english": notes, "translations": {}}
        got = {lg: 0 for lg in LOCALES}
        for lg in LOCALES:
            p = os.path.join(text_dir, f"{inst}_{lg}.txt")
            if not os.path.exists(p):
                continue
            lines = io.open(p, encoding="utf-8").read().split("\n")
            for key, en in notes.items():
                tr = find_translation(lines, en)
                if tr:
                    result[inst]["translations"].setdefault(key, {})[lg] = tr
                    got[lg] += 1
        print(f"[{inst}] {len(notes)} English notes  |  "
              + "  ".join(f"{lg} {got[lg]}" for lg in LOCALES))

    if a.provenance == "aug21":
        prior = json.load(io.open(a.merge_into, encoding="utf-8")) if os.path.exists(a.merge_into) else {}
        result, counts = merge_notes(prior, result, load_overrides(a.overrides),
                                     {"date": "2026-08-25", "source": a.source or text_dir,
                                      "files": files})
        print("aug21 merge: " + ", ".join(f"{k} {v}" for k, v in counts.items()))

    if a.json:
        raw_prior = io.open(a.merge_into, encoding="utf-8").read() if os.path.exists(a.merge_into) else ""
        nl = "\r\n" if "\r\n" in raw_prior else "\n"
        with io.open(a.json, "w", encoding="utf-8", newline=nl) as fh:
            json.dump(result, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        print(f"\nWrote {a.json}")
```

Update the module docstring usage lines (23-24) to:

```python
    python extract_notes.py                                   # June-5 text/ dumps, report only
    python extract_notes.py --json notes.json                 # June-5 rebuild
    python extract_notes.py --source "C:/.../raw/Survey-Instruments-2026-08-21/Translations" \
        --provenance aug21 --json notes.json                  # Aug-21: dump PDFs, Aug-21-wins merge
```

- [ ] **Step 4: Run test to verify it passes** — Run: `$env:PYTHONIOENCODING='utf-8'; python -m pytest data/translations-official/test_notes_icf_aug21.py -q` Expected: `5 passed`.

- [ ] **Step 5: Verify/gate** — Record the BEFORE coverage, run the Aug-21 pass in dry mode (no `--json`), then write:

```
cd C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSPro
$env:PYTHONIOENCODING='utf-8'
python -c "import notes_lookup; print('notes BEFORE', notes_lookup.coverage())"
python data/translations-official/extract_notes.py --source "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/Survey-Instruments-2026-08-21/Translations" --provenance aug21
python data/translations-official/extract_notes.py --source "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/Survey-Instruments-2026-08-21/Translations" --provenance aug21 --json data/translations-official/notes.json
python -c "import notes_lookup; print('notes AFTER', notes_lookup.coverage())"
python -c "import json;d=json.load(open('data/translations-official/notes.json',encoding='utf-8'));print(list(d), d['_provenance']['aug21'])"
```
Expected: `dumped 21 PDFs -> ...text-aug21`; per-instrument counts ≥ the June-5 line (F1 13, F3 25, F4 27 English notes); `aug21 merge: written N, replaced N, overridden 0, kept_prior N`; AFTER ≥ BEFORE for every locale; top-level keys `['F1','F3','F4','_provenance']`. If `replaced` includes a value that reads worse than the prior (open `notes.json` diff), add `note:<key>:<LOC>` to `aug21-overrides.json` with a reason (or `"keep": ""` to force English) and re-run `--json`. Note: Task 25 adds four new F4 gate constants and Task 29 re-runs this command for them — the pass here covers every note that exists today.

- [ ] **Step 6: Record** — append the exact line `/deliverables/CSPro/data/translations-official/text-aug21/` to `.gitignore` directly under line 198 (`/deliverables/CSPro/data/translations-official/text/` — same root-anchored form, or the dump stays trackable). Write the BEFORE/AFTER coverage dicts and the merge counts into `deliverables/CSPro/patch-notes/aug21-notes-layer.md` (folder created in Task 0 Step 6). No commit (Carl commits generator/map changes).

### Task 9: `icf_content.py` — per-language screens with English fallback

**Files:**
- Modify: `deliverables/CSPro/icf_content.py:1-24` (docstring), `:240` (after `CONTINUE_OPTIONS`), `:269-285` (`clearance_html`, `build_screen_html`)
- Test: `deliverables/CSPro/data/translations-official/test_notes_icf_aug21.py` (append)

**Interfaces:**
- Consumes: `SCREENS`, `CLEARANCE_NO`, `SURVEY_TITLE_HTML` (existing).
- Produces: `ICF_LANGS = ["FIL","BCL","BIS","CEB","WAR","HIL","ILO"]`, `paragraph_key(part, idx) -> "icf:<part>:<idx>"`, `screens_for(instrument, lang="EN") -> (list[str], list[str])`, `build_screen_html(instrument, part, logo_html="", lang="EN")`, `screens_html_by_lang(instrument, part, logo_html="") -> {code: html}` for `EN` + `ICF_LANGS`, `coverage() -> {LOC: n_paragraphs}`, data file `data/translations-official/icf.json` shaped `{INST: {"icf:1:0": {"EN": ..., "FIL": ...}}, "_provenance": {...}}` (written by Task 10).

- [ ] **Step 1: Write the failing test** — append to `test_notes_icf_aug21.py`:

```python
import icf_content  # noqa: E402


def test_screens_for_falls_back_per_paragraph(tmp_path, monkeypatch):
    en1, en2 = icf_content.SCREENS["F1"]
    data = {"F1": {"icf:1:1": {"EN": en1[1], "FIL": "Layunin ng pag-aaral na ito ..."},
                   "icf:1:2": {"EN": en1[2], "FIL": ""},              # "keep": "" -> English
                   "icf:2:0": {"EN": "REWORDED", "FIL": "must-not-show"}}}
    p = tmp_path / "icf.json"
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(icf_content, "_ICF_PATH", p)
    monkeypatch.setattr(icf_content, "_ICF", None)
    s1, s2 = icf_content.screens_for("F1", "FIL")
    assert s1[0] == en1[0]                                # no translation -> English
    assert s1[1] == "Layunin ng pag-aaral na ito ..."     # translated
    assert s1[2] == en1[2]                                # empty keep -> English
    assert s2[0] == en2[0]                                # EN mismatch -> English
    assert icf_content.screens_for("F1", "EN") == (list(en1), list(en2))
    html = icf_content.screens_html_by_lang("F1", 1, "<p>LOGO</p>")
    assert set(html) == {"EN", *icf_content.ICF_LANGS}
    assert "Layunin" in html["FIL"] and "Layunin" not in html["EN"]
    assert "\n" not in html["FIL"]                        # one-line body for the .qsf `|` scalar
    assert "(ASPSI).  We are here" in html["EN"]          # paragraph text is NOT whitespace-collapsed
    assert "Translated Questionnaire ver. 08/21/2026" in html["EN"]
    assert icf_content.coverage() == {"FIL": 1}
```

- [ ] **Step 2: Run test to verify it fails** — Run: `python -m pytest data/translations-official/test_notes_icf_aug21.py -q -k screens_for` Expected: FAIL with `AttributeError: module 'icf_content' has no attribute '_ICF_PATH'`.

- [ ] **Step 3: Write minimal implementation** — in `icf_content.py`, replace the docstring paragraph at lines 16-18 with:

```python
Per-language text (Aug-21 pack, 2026-08-25): data/translations-official/icf.json holds the
seven translations of each paragraph, keyed icf:<screen>:<index> with the English kept
alongside; screens_for() returns a paragraph's translation only when its stored English
equals the paragraph here (full-English-string rule, same as notes_lookup), else English.
An empty stored value ("keep": "" in aug21-overrides.json) also renders English.
Contact blocks (<b>...) are never translated.
```

After `CONTINUE_OPTIONS = [("Continue", "1")]` (line 240) add:

```python
import json as _json
from pathlib import Path as _Path

ICF_LANGS = ["FIL", "BCL", "BIS", "CEB", "WAR", "HIL", "ILO"]
_ICF_PATH = _Path(__file__).parent / "data" / "translations-official" / "icf.json"
_ICF = None


def paragraph_key(part, idx):
    return f"icf:{part}:{idx}"


def _load_icf():
    global _ICF
    if _ICF is None:
        _ICF = (_json.loads(_ICF_PATH.read_text(encoding="utf-8"))
                if _ICF_PATH.exists() else {})
    return _ICF


def screens_for(instrument, lang="EN"):
    """(screen1_paras, screen2_paras) in `lang`; each paragraph falls back to English."""
    en1, en2 = SCREENS[instrument]
    if lang in (None, "", "EN"):
        return list(en1), list(en2)
    block = _load_icf().get(instrument, {}) or {}
    out = []
    for part, paras in ((1, en1), (2, en2)):
        row = []
        for i, en in enumerate(paras):
            entry = block.get(paragraph_key(part, i)) or {}
            tr = (entry.get(lang) or "").strip()
            row.append(tr if (tr and entry.get("EN") == en) else en)
        out.append(row)
    return out[0], out[1]


def coverage():
    """-> {locale: n} translated ICF paragraphs actually usable (EN matches SCREENS)."""
    out = {}
    for inst, (en1, en2) in SCREENS.items():
        for lang in ICF_LANGS:
            s1, s2 = screens_for(inst, lang)
            n = sum(1 for a, b in zip(s1 + s2, list(en1) + list(en2)) if a != b)
            if n:
                out[lang] = out.get(lang, 0) + n
    return out
```

Replace lines 269-285 (`clearance_html`, `build_screen_html`) with:

```python
def clearance_html(instrument):
    """Survey title (reference year inside it, #1190/#1304) + PSA/SJREB clearance.
    Translated Questionnaire ver. bumped 06/05 -> 08/21/2026 with the Aug-21 import: 20 of
    the 21 translated PDFs carry 08/21/2026 in their header (their SJREB line still prints
    06/05 — the header is the newer stamp). F3-Tagalog is the one outlier that still prints
    06/05/2026 on both lines; it is the same Aug-21 pack, so 08/21/2026 stays for all three
    instruments — do not 'correct' F3 back."""
    return (SURVEY_TITLE_HTML + '<p class="instruction">PSA SSRCS Clearance No. '
            f'{CLEARANCE_NO[instrument]} &middot; issued July 2026 &middot; valid until '
            '31 July 2027<br/>SJREB: ICF ver. 07/25/2026 &middot; Translated '
            'Questionnaire ver. 08/21/2026</p>')


def build_screen_html(instrument, part, logo_html="", lang="EN"):
    """Full question-text HTML for one ICF screen (part = 1 or 2) in one language.

    Returned as a single line: the .qsf emits each language's body as one indented
    line under a `|` block scalar, so an embedded newline would corrupt the YAML.
    SCREENS paragraphs contain no newlines and extract_icf stores single-line text, so
    only a literal newline is removed — internal spacing (incl. the double space after
    '(ASPSI).') is left as-is to keep the EN body byte-identical to the pre-Aug-21 build.
    """
    paras = screens_for(instrument, lang)[part - 1]
    body = "".join(f'<p class="normal">{t.replace(chr(10), " ").replace(chr(13), "")}</p>'
                   for t in paras)
    return logo_html + body + clearance_html(instrument)


def screens_html_by_lang(instrument, part, logo_html=""):
    """{dcf language code: html} for EN + ICF_LANGS — what generate_qsf's OVERRIDES holds."""
    return {code: build_screen_html(instrument, part, logo_html, code)
            for code in ["EN"] + ICF_LANGS}
```

- [ ] **Step 4: Run test to verify it passes** — Run: `python -m pytest data/translations-official/test_notes_icf_aug21.py -q` Expected: `6 passed`.

- [ ] **Step 5: Verify/gate** — with no `icf.json` on disk yet, the three generators must produce qsf bodies identical to before apart from the version-line bump (`06/05/2026` → `08/21/2026`) — nothing else, since whitespace is not collapsed:

```
cd C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSPro
python -c "import icf_content as i; print(i.coverage()); h=i.build_screen_html('F1',1); print(len(h), '08/21/2026' in h, '(ASPSI).  We are here' in h)"
```
Expected: `{}` then a length > 1000, `True`, `True`.

- [ ] **Step 6: Record** — note in the wave note that the footer stamp moved to 08/21/2026 for all three instruments (renders on cover + both ICF screens × 8 locales) — this alone makes waves 1/3/4 a visible change on-device — and record the F3-Tagalog 06/05 header outlier so nobody reverts F3's stamp later.

### Task 10: `extract_icf.py` — ICF paragraphs from the Aug-21 PDFs into `icf.json`

**Files:**
- Create: `deliverables/CSPro/data/translations-official/extract_icf.py`
- Test: `deliverables/CSPro/data/translations-official/test_notes_icf_aug21.py` (append)

**Interfaces:**
- Consumes: `extract_notes.norm`, `extract_notes.looks_english`, `extract_notes.polish`, `extract_notes.PAPER_LANG`, `extract_notes.PAPER_NAME`, `extract_notes.pdf_lines`, `extract_notes.load_overrides` (Task 8); `icf_content.SCREENS`, `icf_content.paragraph_key`, `icf_content.ICF_LANGS` (Task 9).
- Produces: `plain(para) -> str` (HTML stripped + `norm`), `locate(low, en, min_words=8) -> (start, end, kind) | None` with `kind in {"exact","prefix","suffix"}`, `reads_english(cand, en) -> bool` (ICF-specific acceptance: program names stripped before the function-word count, plus an English-head check), `finish(raw) -> str` (`polish()` for leading debris, terminal punctuation restored), `extract_screens(lines, instrument) -> (translations: {pkey: text}, report: {pkey: kind|"missing"|"dropped-english"|"dropped-short"})`, `build_icf(source_dir, overrides, prior) -> (icf: dict, report: dict)`, CLI `python extract_icf.py --source DIR [--json icf.json] [--report icf-report.json]`.

- [ ] **Step 1: Write the failing test** — append:

```python
import extract_icf  # noqa: E402

PAPER_P1 = ("Hello, my name is (data collector name). I work for Asian Social Project Services, "
            "Inc. (ASPSI). I am here to invite you to participate in a study about the Universal "
            "Health Care (UHC) and packages of programs like Yaman ng Kalusugan Program (YAKAP), "
            "No Balance Billing (NBB), Zero Balance Billing (ZBB), Bagong Urgent Care and "
            "Ambulatory Services (BUCAS), and Guaranteed and Accessible Medications for "
            "Outpatient Treatment (GAMOT). The Department of Health funded this study. Please "
            "let me tell you more about the study.")
# The REAL Aug-21 F1-Tagalog paragraph 1: the program names stay in English (this is what
# makes plain looks_english() reject all 21 locales). HARD PREREQUISITE: Task 8 Step 5 has
# run, so text-aug21/F1_FIL.txt exists. Paste the paragraph VERBATIM from that dump (Step 1a
# prints it) BEFORE running Step 2 — test_fil_p1_is_verbatim_from_the_dump fails on any
# paraphrase or leftover placeholder and only skips while the dump is absent.
FIL_P1 = ("Kamusta, ako si (pangalan ng data collector). Ako ay nagtatrabaho sa Asian Social "
          "Project Services, Inc. (ASPSI). Narito ako upang anyayahan kayong lumahok sa isang "
          "pag-aaral tungkol sa Universal Health Care (UHC) at mga pakete ng programa tulad ng "
          "Yaman ng Kalusugan Program (YAKAP), No Balance Billing (NBB), Zero Balance Billing "
          "(ZBB), Bagong Urgent Care and Ambulatory Services (BUCAS), at Guaranteed and "
          "Accessible Medications for Outpatient Treatment (GAMOT). Pinondohan ng Department of "
          "Health ang pag-aaral na ito. Hayaan ninyo akong magsabi pa tungkol sa pag-aaral.")
FIL_P2 = ("Layunin ng pag-aaral na ito na makalikom ng ebidensya tungkol sa pagpapatupad ng UHC "
          "at ng mga programa nito sa pamamagitan ng mga survey sa mga pasilidad, pasyente at "
          "sambahayan sa buong bansa. Sasaklawin ng mga tanong ang profile ng pasilidad at/o "
          "pinuno ng pasilidad, mga pagbabago sa pagpapatupad ng UHC mula 2019, at ang mga "
          "karanasan ninyo sa mga programa. Tatagal ang panayam nang humigit-kumulang isang oras.")
FIL_P3 = "Nais mo bang lumahok bilang respondent sa pag-aaral? Maaaring tumagal ng humigit-kumulang isang oras ang panayam."
TEXT_AUG21_F1_FIL = os.path.join(HERE, "text-aug21", "F1_FIL.txt")   # Task 8 Step 5 dump (gitignored)


def test_fil_p1_is_verbatim_from_the_dump():
    """Fixture guard: FIL_P1 must be the paper's own paragraph, never an invented one."""
    if not os.path.exists(TEXT_AUG21_F1_FIL):
        pytest.skip("text-aug21/F1_FIL.txt missing - run Task 8 Step 5 first (extract_notes.py --source ... --provenance aug21)")
    dump = en_mod.norm(" ".join(io.open(TEXT_AUG21_F1_FIL, encoding="utf-8").read().split("\n")))
    assert en_mod.norm(FIL_P1) in dump, "FIL_P1 is not verbatim from the Aug-21 F1-Tagalog dump - paste it from Step 1a"


def test_reads_english_accepts_translation_that_keeps_program_names():
    en = extract_icf.plain(icf_content.SCREENS["F1"][0][0])
    assert not extract_icf.reads_english(FIL_P1, en)
    assert extract_icf.reads_english(PAPER_P1, en)                   # English head -> rejected
    assert extract_icf.reads_english("will cover your Patient Profile and the services you "
                                     "used, and the changes in the facility since 2019", en)


def test_finish_keeps_terminal_punctuation():
    assert extract_icf.finish(FIL_P3 + " ") == FIL_P3
    assert extract_icf.finish("(UHC) Magtatanong kami sa inyo.") == "Magtatanong kami sa inyo."
    assert extract_icf.finish("Walang masamang mangyayari sa inyo. A") == "Walang masamang mangyayari sa inyo."


def test_extract_screens_suffix_and_exact_anchors(tmp_path):
    en1 = icf_content.SCREENS["F1"][0]
    text = "\n".join([PAPER_P1, FIL_P1, en1[1], FIL_P2, en1[2], FIL_P3, "PART II: PRIVACY",
                      icf_content.SCREENS["F1"][1][0]])
    pdf = tmp_path / "F1-Tagalog_x_Aug21.pdf"
    make_pdf(str(pdf), text)
    tr, rep = extract_icf.extract_screens(en_mod.pdf_lines(str(pdf)), "F1")
    assert rep["icf:1:0"] == "suffix" and tr["icf:1:0"].startswith("Kamusta, ako si")
    assert tr["icf:1:0"].endswith(".")                            # terminal period kept
    assert rep["icf:1:1"] == "exact" and tr["icf:1:1"].startswith("Layunin")
    assert tr["icf:1:2"] == FIL_P3 and "PART II" not in tr["icf:1:2"]
    assert rep["icf:2:0"] in ("dropped-short", "missing")       # nothing follows it on the page
    assert "icf:2:4" not in rep                                  # <b> contact blocks never anchored


def test_extract_screens_stops_at_contact_table_furniture(tmp_path):
    en2 = icf_content.SCREENS["F1"][1]
    text = "\n".join([en2[3], "Kung may mga alalahanin kayo tungkol sa pag-aaral, maaari mong "
                      "kontakin ang:", "Office Email Contact No", "Single Joint Research Ethics "
                      "Board sjreb@doh.gov.ph 8651-7800"])
    pdf = tmp_path / "F1-Tagalog_x_Aug21.pdf"
    make_pdf(str(pdf), text)
    tr, rep = extract_icf.extract_screens(en_mod.pdf_lines(str(pdf)), "F1")
    assert rep["icf:2:3"] == "exact"
    assert tr["icf:2:3"].endswith("kontakin ang:") and "Office" not in tr["icf:2:3"]


def test_build_icf_writes_english_alongside_and_overrides(tmp_path):
    src = tmp_path / "Translations"; src.mkdir()
    en1 = icf_content.SCREENS["F1"][0]
    make_pdf(str(src / "F1-Tagalog_x_Aug21.pdf"), "\n".join([en1[2], FIL_P3, en1[1], FIL_P2]))
    ov = {"F1": {"icf:1:2:FIL": {"keep": "PRIOR", "reason": "test"},
                 "icf:1:1:FIL": {"keep": "", "reason": "force English"}}}
    icf, report = extract_icf.build_icf(str(src), ov, {})
    assert icf["F1"]["icf:1:2"] == {"EN": en1[2], "FIL": "PRIOR"}
    assert icf["F1"]["icf:1:1"] == {"EN": en1[1], "FIL": ""}
    assert icf["_provenance"]["aug21"]["n_overridden"] == 2
    assert report["F1"]["FIL"]["icf:1:2"] == "override"
```

- [ ] **Step 1a: Paste the real FIL paragraph (prerequisite: Task 8 Step 5 dump on disk)** — from `deliverables/CSPro`:

```powershell
$env:PYTHONIOENCODING='utf-8'
Test-Path data/translations-official/text-aug21/F1_FIL.txt      # must be True - otherwise run Task 8 Step 5 first
python -c "import io;t=' '.join(io.open('data/translations-official/text-aug21/F1_FIL.txt',encoding='utf-8').read().split());i=t.find('tell you more about the study.');print(t[i+31:i+1100])"
```
Copy the Tagalog paragraph that follows (up to and including its final period, stopping before the next English sentence) into `FIL_P1` verbatim — program names and all. Do not run Step 2 with the placeholder body in place.

- [ ] **Step 2: Run test to verify it fails** — Run: `python -m pytest data/translations-official/test_notes_icf_aug21.py -q` Expected: FAIL with `ModuleNotFoundError: No module named 'extract_icf'` (the `test_fil_p1_is_verbatim_from_the_dump` guard is collected in the same file and must not be the failing test — if it fails, the paste in Step 1a is not verbatim).

- [ ] **Step 3: Write minimal implementation**

```python
#!/usr/bin/env python3
"""ICF (informed consent) paragraph translations from the Aug-21 translated PDFs.

Anchor set = the English paragraphs in ../../icf_content.py SCREENS (not the paper's own
English: the paper opens "Hello, my name is ... I work for" where the build reads "We work
for ...", so paragraph 1 is found by its identical TAIL). Translation = the text between
the end of one located English paragraph and the start of the next located one, trimmed
at PART headings / ballot glyphs / contact-table furniture ("Office Email Contact No",
SJREB rows — the <b> contact blocks are printed cell-by-cell and are never located).

Acceptance is NOT extract_notes.looks_english(): every locale keeps the English program
names ("Guaranteed and Accessible Medications for Outpatient Treatment", "Department of
Health") inside paragraph 1, which alone trips the >=3-function-word rule. reads_english()
strips those names first and additionally rejects a candidate whose head repeats the
English paragraph's head (the F1-Tagalog paper defect: F3's English coverage sentence is
printed above the CORRECT F1 Tagalog — the auto-drop is right, the Tagalog is seeded via
aug21-overrides.json icf:1:1:FIL).

These are read-aloud paragraphs, so the terminal punctuation polish() strips is restored.

    python extract_icf.py --source "C:/.../raw/Survey-Instruments-2026-08-21/Translations"
    python extract_icf.py --source ... --json icf.json --report icf-report.json
"""
import argparse
import io
import json
import os
import re
import sys
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
CSPRO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, CSPRO)
from extract_notes import norm, looks_english, polish, PAPER_LANG, PAPER_NAME, pdf_lines, load_overrides  # noqa: E402
import icf_content  # noqa: E402

TAG = re.compile(r"<[^>]+>")
STOP = re.compile(r"\bPART\s+I{1,3}\b|[☐☑☒□]|\bVERIFICATION\b"
                  r"|\bOffice\s+Email\b|\bEmail:|\bContact No\b"
                  r"|Single Joint Research Ethics Board|\bSJREB\b")
# English proper names every locale keeps verbatim inside the consent text.
PROGRAM_NAMES = re.compile(
    r"Yaman ng Kalusugan Program|No Balance Billing|Zero Balance Billing"
    r"|Bagong Urgent Care and Ambulatory Services"
    r"|Guaranteed and Accessible Medications for Outpatient Treatment"
    r"|Department of Health|Asian Social Project Services,? Inc\.?|Universal Health Care"
    r"|Single Joint Research Ethics Board|data collector", re.I)
HEAD = 60


def plain(para):
    return norm(TAG.sub(" ", para))


def locate(low, en, min_words=8):
    """(start, end, kind) of `en` (lowercased) in `low`: exact, else longest prefix,
    else longest suffix of >= min_words words. None when absent."""
    enl = en.lower()
    p = low.find(enl)
    if p >= 0:
        return p, p + len(enl), "exact"
    words = enl.split()
    for k in range(len(words) - 1, min_words - 1, -1):
        probe = " ".join(words[:k])
        p = low.find(probe)
        if p >= 0:
            return p, p + len(probe), "prefix"
    for k in range(len(words) - 1, min_words - 1, -1):
        probe = " ".join(words[-k:])
        p = low.find(probe)
        if p >= 0:
            return p, p + len(probe), "suffix"
    return None


def reads_english(cand, en):
    """True when the candidate is (still) the English paragraph, not a translation."""
    c, e = norm(cand).lower(), norm(en).lower()
    if c[:HEAD] == e[:HEAD]:
        return True                                    # starts by repeating the English
    if len(c) >= HEAD and c[:HEAD] in e:
        return True                                    # starts mid-English (prefix-anchor tail)
    return looks_english(PROGRAM_NAMES.sub(" ", cand))


def finish(raw):
    """polish() for leading debris, then put back the terminal punctuation it strips."""
    raw = norm(raw)
    tail = raw[-1] if raw and raw[-1] in ".?!" else ""
    s = polish(raw)
    if s and tail and not s.endswith((".", "?", "!")):
        s += tail
    return s


def _anchors(instrument):
    """[(pkey|None, plain_en)] in screen order; contact blocks (<b>) are boundaries only."""
    out = []
    for part, paras in enumerate(icf_content.SCREENS[instrument], start=1):
        for i, para in enumerate(paras):
            key = None if para.lstrip().startswith("<b>") else icf_content.paragraph_key(part, i)
            out.append((key, plain(para)))
    return out


def extract_screens(lines, instrument):
    blob = norm(" ".join(lines))
    low = blob.lower()
    anchors = _anchors(instrument)
    found = []
    for key, en in anchors:
        loc = locate(low, en)
        found.append((key, en, loc))
    trans, report = OrderedDict(), OrderedDict()
    for n, (key, en, loc) in enumerate(found):
        if key is None:
            continue
        if loc is None:
            report[key] = "missing"
            continue
        start, end, kind = loc
        nxt = next((l[0] for _, _, l in found[n + 1:] if l is not None and l[0] > end), len(blob))
        cand = blob[end:nxt].lstrip(" .:-)")
        m = STOP.search(cand)
        if m:
            cand = cand[:m.start()]
        cand = finish(cand[:int(len(en) * 2.5) + 40])
        if len(cand) < 20:
            report[key] = "dropped-short"
        elif reads_english(cand, en):
            report[key] = "dropped-english"
        else:
            trans[key] = cand
            report[key] = kind
    return trans, report


def build_icf(source_dir, overrides, prior):
    icf = OrderedDict((k, OrderedDict(v)) for k, v in prior.items() if k != "_provenance")
    report = OrderedDict()
    counts = {"written": 0, "replaced": 0, "overridden": 0, "kept_prior": 0}
    files = OrderedDict()
    for name in sorted(os.listdir(source_dir)):
        m = PAPER_NAME.match(name)
        if not m or m.group(2) not in PAPER_LANG:
            continue
        inst, loc = m.group(1), PAPER_LANG[m.group(2)]
        files[f"{inst}_{loc}"] = name
        trans, rep = extract_screens(pdf_lines(os.path.join(source_dir, name)), inst)
        block = icf.setdefault(inst, OrderedDict())
        ov = overrides.get(inst, {})
        for key, en in ((k, e) for k, e in _anchors(inst) if k):
            entry = block.setdefault(key, OrderedDict())
            if entry.get("EN") != en:          # SCREENS reworded since the prior file
                entry.clear()
                entry["EN"] = en
            val = trans.get(key)
            okey = f"{key}:{loc}"
            if okey in ov:
                entry[loc] = ov[okey].get("keep", entry.get(loc, val))   # "" = render English
                counts["overridden"] += 1
                rep[key] = "override"
            elif val:
                if entry.get(loc) and norm(entry[loc]) != norm(val):
                    counts["replaced"] += 1
                elif not entry.get(loc):
                    counts["written"] += 1
                entry[loc] = val
            elif entry.get(loc):
                counts["kept_prior"] += 1
        report.setdefault(inst, OrderedDict())[loc] = rep
    icf["_provenance"] = OrderedDict(prior.get("_provenance", {}))
    icf["_provenance"]["aug21"] = OrderedDict(
        [("date", "2026-08-25"), ("source", source_dir), ("files", files),
         ("n_written", counts["written"]), ("n_replaced", counts["replaced"]),
         ("n_overridden", counts["overridden"]), ("n_kept_prior", counts["kept_prior"])])
    return icf, report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--json")
    ap.add_argument("--report", default=os.path.join(HERE, "icf-report.json"))
    ap.add_argument("--overrides", default=os.path.join(HERE, "aug21-overrides.json"))
    ap.add_argument("--merge-into", default=os.path.join(HERE, "icf.json"))
    a = ap.parse_args()
    prior = json.load(io.open(a.merge_into, encoding="utf-8")) if os.path.exists(a.merge_into) else {}
    icf, report = build_icf(a.source, load_overrides(a.overrides), prior)
    for inst in report:
        for loc, rep in report[inst].items():
            kinds = {}
            for k in rep.values():
                kinds[k] = kinds.get(k, 0) + 1
            print(f"[{inst} {loc}] " + "  ".join(f"{k} {v}" for k, v in sorted(kinds.items())))
    print("aug21 icf: " + ", ".join(f"{k} {v}" for k, v in icf["_provenance"]["aug21"].items()
                                     if k.startswith("n_")))
    with io.open(a.report, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)
    if a.json:
        with io.open(a.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(icf, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        print(f"Wrote {a.json}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes** — Run: `$env:PYTHONIOENCODING='utf-8'; python -m pytest data/translations-official/test_notes_icf_aug21.py -q` Expected: `12 passed` (11 + the FIL_P1 verbatim guard; `11 passed, 1 skipped` only if the Task 8 dump is absent — which contradicts Step 1a, so fix that first). If `test_reads_english_accepts_translation_that_keeps_program_names` fails on the real FIL line pasted in from `text-aug21/F1_FIL.txt`, extend `PROGRAM_NAMES` with whatever English phrase remains (print `ENGLISH_FUNC.findall(PROGRAM_NAMES.sub(" ", FIL_P1))` to see which words trip it) — do NOT loosen the head check.

- [ ] **Step 5: Verify/gate** — dry run against the real pack, inspect, then write:

```
cd C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSPro
$env:PYTHONIOENCODING='utf-8'
python data/translations-official/extract_icf.py --source "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/Survey-Instruments-2026-08-21/Translations"
python -c "import json;r=json.load(open('data/translations-official/icf-report.json',encoding='utf-8'));[print(i,l,r[i][l]['icf:1:0'],r[i][l].get('icf:1:1'),r[i][l].get('icf:2:3')) for i in r for l in r[i]]"
```
Expected: 21 `[F<n> <LOC>]` lines; `icf:1:0` = `suffix` for all 21 (if any locale shows `dropped-english`, print the candidate and extend `PROGRAM_NAMES` — never ship with paragraph 1 dropped); F1-FIL `icf:1:1` = `dropped-english` (the English-line paper defect); `icf:2:0..2:3` mostly `exact`, `icf:2:3` texts ending at the colon with no `Office`/`Email` bleed; `missing` only where a locale prints no consent page. Then seed the known override in `aug21-overrides.json`:

```json
"F1": {
  "icf:1:1:FIL": {
    "keep": "<verbatim Tagalog paragraph from page 1 of raw/.../F1-Tagalog_..._Aug21.pdf, starting 'Layunin ng pag-aaral na ito na makalikom ng ebidensya ...' through '... isang oras.'>",
    "reason": "paper prints F3's English coverage sentence above the CORRECT F1 Tagalog; auto-drop is right for the English, the Tagalog is good"
  }
}
```
Spot-check the FIL and ILO paragraphs (`python -c "import json;d=json.load(open('data/translations-official/icf-report.json'))"`-style plus the printed candidates) against page 1 of the matching PDF; each stored paragraph must end in `.`/`?`. For any paragraph that reads wrong, add `icf:<p>:<i>:<LOC>` with a corrected `keep` and a reason, or `"keep": ""` to force English. Validate with `python data/translations-official/aug21_overrides.py` → `OK`. Then:

```
python data/translations-official/extract_icf.py --source "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/Survey-Instruments-2026-08-21/Translations" --json data/translations-official/icf.json
python -c "import icf_content as i; print('icf AFTER', i.coverage())"
python -c "import json;d=json.load(open('data/translations-official/icf.json',encoding='utf-8'));bad=[(i,k,l) for i in d if i!='_provenance' for k,e in d[i].items() for l,v in e.items() if l!='EN' and v and v[-1] not in '.?!:'];print('no-terminal-punct', bad)"
```
Expected: `Wrote ...icf.json`; `icf AFTER` shows all 7 locales with n > 0 (ceiling = 3 instruments × 8 anchored paragraphs = 24 per locale; contact blocks excluded); `no-terminal-punct []`.

- [ ] **Step 6: Record** — `icf.json`, `icf-report.json` and `aug21-overrides.json` are committed data (Carl commits); write the per-locale `exact/prefix/suffix/override/dropped/missing` table and `icf AFTER` into the wave note; log the F1-Tagalog paragraph-2 ENGLISH-line defect (F3 sentence printed on the F1 paper) as an item for ASPSI in the consolidated status (Task 47).

### Task 11: Wire per-language consent into `F{1,3,4}/generate_qsf.py` + coverage before/after

**Files:**
- Modify: `deliverables/CSPro/F1/generate_qsf.py:212-215` (OVERRIDES), `:437` (`ov`), `:451-455`; `deliverables/CSPro/F3/generate_qsf.py:163-166`, `:512`, `:516-517`; `deliverables/CSPro/F4/generate_qsf.py:131-134`, `:527`, `:559-561`
- Test: `deliverables/CSPro/data/translations-official/test_notes_icf_aug21.py` (append)

**Interfaces:**
- Consumes: `icf_content.screens_html_by_lang(instrument, part, logo_html)` (Task 9); `notes_lookup.coverage()`, `icf_content.coverage()`.
- Produces: `OVERRIDES[name] -> {lang_code: html}` in all three generators; qsf `ICF_PART1`/`ICF_PART2` bodies differ per language.

- [ ] **Step 1: Write the failing test** — append:

```python
def test_generators_hold_per_language_overrides():
    """F3/F4 generate_qsf import generate_dcf at module top; sys.modules caches F1's copy,
    so each instrument is loaded with its own dir at sys.path[0] and the cache cleared."""
    import importlib.util
    for inst in ("F1", "F3", "F4"):
        inst_dir = os.path.join(CSPRO, inst)
        for m in ("generate_dcf", "generate_qsf", f"qsf_{inst}"):
            sys.modules.pop(m, None)
        sys.path.insert(0, inst_dir)
        try:
            spec = importlib.util.spec_from_file_location(f"qsf_{inst}", os.path.join(inst_dir, "generate_qsf.py"))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        finally:
            sys.path.remove(inst_dir)
            sys.modules.pop("generate_dcf", None)
        ov = mod.OVERRIDES["ICF_PART1"]
        assert isinstance(ov, dict) and set(ov) == {"EN", *icf_content.ICF_LANGS}, inst
        assert all("\n" not in v for v in ov.values()), inst
        assert f'screens_html_by_lang("{inst}"' in io.open(os.path.join(inst_dir, "generate_qsf.py"), encoding="utf-8").read(), inst
```

- [ ] **Step 2: Run test to verify it fails** — Run: `python -m pytest data/translations-official/test_notes_icf_aug21.py -q -k per_language_overrides` Expected: FAIL with `AssertionError: F1` (OVERRIDES value is a `str`).

- [ ] **Step 3: Write minimal implementation** — F1 `generate_qsf.py` lines 212-215 become:

```python
OVERRIDES = {
    "ICF_PART1": _icf.screens_html_by_lang("F1", 1, _LOGO_HTML),   # {lang: html}
    "ICF_PART2": _icf.screens_html_by_lang("F1", 2, _LOGO_HTML),
}
```
F1 line 451 `body = ov or (pre + txt + post)` becomes `body = ov[lnm] if ov else (pre + txt + post)` (the `if not ov and _cap_dup(...)` guard at :455 is unchanged — `ov` is still truthy as a dict).

F3 `generate_qsf.py` lines 163-166 use the same `screens_html_by_lang("F3", ...)` shape; lines 516-517:

```python
                    if ov:
                        body = ov[lnm]
```
F4 `generate_qsf.py` lines 131-134 same shape with `"F4"`; line 559 `body = ov or (pre + _html(labmap.get(lnm) or en) + post)` becomes `body = ov[lnm] if ov else (pre + _html(labmap.get(lnm) or en) + post)`. Also update the three header comments that say "emitted identically for every declared language (English fallback until SJREB-approved ICF translations arrive)" (F1 :204-206 and the F3/F4 twins) to: `# Per language since the Aug-21 import: icf_content.screens_for() falls back to English per paragraph.`

- [ ] **Step 4: Run test to verify it passes** — Run: `python -m pytest data/translations-official/test_notes_icf_aug21.py -q` Expected: `13 passed`.

- [ ] **Step 5: Verify/gate** — regenerate and check the rendered qsf per language (F1 shown; repeat for F3 and F4 in their waves — Tasks 41 and 28):

```
cd C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSPro
$env:PYTHONIOENCODING='utf-8'
python -c "import notes_lookup, icf_content; print('notes', notes_lookup.coverage()); print('icf', icf_content.coverage())"
python F1/generate_dcf.py
python F1/generate_qsf.py
@'
import re, io
q = io.open("F1/FacilityHeadSurvey.qsf", encoding="utf-8").read()
blk = q[q.index(".ICF_PART1"):q.index(".ICF_PART2")]
fil = re.search(r"\n          FIL: \|\n            (.*)", blk).group(1)
en = re.search(r"\n          EN: \|\n            (.*)", blk).group(1)
print("FIL differs from EN:", fil != en, "| Kamusta in FIL:", "Kamusta" in fil, "| 08/21/2026:", "08/21/2026" in en, "| FIL para 2 translated:", "Layunin" in fil)
assert fil != en and "\n" not in fil
'@ | python -
python automation/verify_questions.py F1
```
(The probe is a PowerShell here-string PIPED into `python -` — never `python - @'…'@`, which hands the text to argv and blocks on stdin.) Expected: coverage dicts printed (paste into the wave note as AFTER; BEFORE = the values captured in Task 8 Step 5 and `{}` for icf); `generate_dcf.py` prints its per-locale `%` lines unchanged (ICF text is qsf-side, not dcf-side); the probe prints `True True True True` (the last one proves the `icf:1:1:FIL` override landed); `[F1] ... PASS`. The Designer compile (`python automation/cspro_compile_driver.py F1 --build --save`) and deploy (`python automation/auto_deploy.py F1 --deploy`) run in Wave 1 (Tasks 18–19), not here — this task ends at a clean qsf.

- [ ] **Step 6: Record** — in `deliverables/CSPro/patch-notes/aug21-notes-layer.md` write: notes coverage BEFORE/AFTER per locale, icf coverage AFTER, the override keys added with reasons (incl. `icf:1:1:FIL` and any `"keep": ""` English-forcing entries), and the one-line tester-visible sentence for each wave's patch note: *"The consent screens and the section intros now read in the selected language (Aug-21 cleared translations); paragraphs without a cleared translation stay English."* No git commit (Carl commits `extract_notes.py`, `extract_icf.py`, `icf_content.py`, the three generators, `notes.json`, `icf.json`, `icf-report.json`, `aug21-overrides.json`, the test file, the `.gitignore` line; `text-aug21/` stays gitignored).

---

## F2 extractor variant + apply-paper-translations.py (Wave 2 tooling)

Scope: give the F2 PWA the same paper→map pipeline the CSPro instruments get, on the PWA's **flat English-keyed** store (`spec/translations/{loc}.json`, read by `scripts/lib/apply-translations.ts` `readMap`/`localizeString`). Three pieces: (1) a committed dump of the exact English strings `applyTranslations()` localizes, (2) an F2 mode of the anchor extractor that anchors on that dump instead of a dcf, (3) a committed apply script with Aug-21-wins + overrides. The Wave-2 run itself is Tasks 22–23.

Facts that shape every task (verified 2026-08-25, review-corrected):

- Aug-21 F2 PDFs (7 translations + English) live at `raw/Survey-Instruments-2026-08-21/Translations/F2-{Bicolano,Bisaya,Cebuano,Hiligaynon,Ilocano,Tagalog,Waray}_Healthcare Worker*_Aug21.pdf` (Cebuano file is `F2-Cebuano_Healthcare Worker_Survey_UHC Year 2_Aug21.pdf` — glob on `F2-{Language}_*.pdf`). Every file is "English line, then translation line", options as `☐ English Translation`; Bicolano additionally echoes English for untranslated options (`☐ Administrator Administrator`) and glues one (`☐ Other (specify) ba pa, ispecify`). The anchor method (span = text between one English anchor and the next) is layout-independent, so both layouts extract the same way. **An echo is itself a second verbatim hit of the same anchor** — the raw span between the two hits is empty, which `qa_flags()` reports as `empty`, not `echo-english`; the F2 extractor therefore collapses back-to-back hits of one anchor into a single echo occurrence and flags it `echo-english` explicitly (Task 14).
- `applyTranslations()` (`scripts/lib/apply-translations.ts:61-80`) localizes exactly: `section.title`, `section.preamble`, `item.label`, `item.help`, `choice.label`, `subField.label`. It does NOT localize `item.preamble` or `item.inputLabel` — those are excluded from the anchor set so no dead keys are written.
- F2's choice universe is dominated by short labels (Yes, No, Male, Nurse, Doctor, Midwife, Regular, Casual…). The F1/F3/F4 thresholds (`MIN_EMIT=8`, `MIN_BOUND=6`) would never emit `Yes`/`No` and would let every stem's span run into `☐ Yes … ☐ No …` (→ `table-bleed`). F2 mode uses its own thresholds (`F2_MIN_BOUND=2`, `F2_MIN_EMIT=2`) with one guard: an anchor shorter than 6 normalized chars only counts when the paper prefixes it with a box glyph (both layouts do for options), so a stray `no` inside a translation does not cut a span.
- `readMap` (`apply-translations.ts:28-42`) silently drops non-string values, and `scripts/audit-translations.py:59-66` calls `norm(v)` on every value — a `_meta` object in an F2 map would crash the audit. **F2 maps carry no `_meta`; provenance goes to the apply report only.**
- Existing F2 maps are `indent=1`, **CRLF** (all seven files begin `{\r\n` — verified with `od -c`), `ensure_ascii=False`, trailing newline; keys in first-appearance order. The apply script detects and preserves the file's line-ending style (apply_safe.py's approach) so untouched entries stay byte-identical and `git diff` shows value-only changes.
- `scripts/audit-translations.py:42` flags any value matching `\s\d{1,3}\s*$` ("trailing question number"). In the papers the next anchor is the next question's English stem, so option-label spans that end without punctuation sweep in a bare number (`Tagapangasiwa 6`). The apply script strips that residue whenever the English string itself does not end in a digit (Task 15) — otherwise the audit gate fails across all locales.
- `tsconfig.scripts.json` includes `scripts/**` with `types: ["node", "vitest/globals"]`, `noUnusedLocals`, `exactOptionalPropertyTypes` — any new `.ts` under `scripts/` must satisfy `tsc -b --force`.
- **Shell: every command block below is Windows PowerShell 5.1** (the session shell). Python paths as `C:/...`. Set `$env:PYTHONIOENCODING='utf-8'` before any python invocation that prints PDF text (cp1252 console crashes on `☐`, verified). `&&` and `set X=Y` are NOT valid here; the Git-Bash equivalent is `PYTHONIOENCODING=utf-8 python ...`.
- The Day-0 committed copy `data/translations-official/anchor_extract.py` (Task 1) is the module `anchor_extract_f2.py` imports by explicit path; the gitignored June-5 original at `translations-paper-extract/anchor_extract.py` (guards its entry point at :327, verified) is the fallback only if Task 1 has not landed.

Repo root below = `C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development`; `APP` = `<root>/deliverables/F2/PWA/app`; `TOFF` = `<root>/deliverables/CSPro/data/translations-official`.

---

### Task 12: English-string collector (`scripts/lib/english-strings.ts`) + vitest

**Files:**
- Create: `deliverables/F2/PWA/app/scripts/lib/english-strings.ts`
- Test: `deliverables/F2/PWA/app/scripts/lib/english-strings.test.ts`

**Interfaces:**
- Consumes: `parseSpec(markdown: string): ParseResult` (`scripts/lib/parse-spec.ts:342`); types `ParseResult`, `Section`, `Item`, `Choice`, `SubField`, `LocalizedString` (`scripts/lib/types.ts`).
- Produces: `export type EnglishKind = 'section.title' | 'section.preamble' | 'item.label' | 'item.help' | 'choice.label' | 'subField.label'`; `export interface EnglishStringEntry { text: string; kinds: EnglishKind[]; ids: string[] }`; `export function collectEnglishStrings(result: ParseResult): EnglishStringEntry[]` (unique by exact `en`, first-appearance order, same six fields `applyTranslations()` localizes).

- [ ] **Step 1: Write the failing test**

```ts
// deliverables/F2/PWA/app/scripts/lib/english-strings.test.ts
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { collectEnglishStrings } from './english-strings';
import { parseSpec } from './parse-spec';
import type { ParseResult } from './types';

const base: ParseResult = {
  sections: [
    {
      id: 'A',
      title: { en: 'Profile' },
      preamble: { en: 'Intro' },
      items: [
        {
          id: 'Q1', section: 'A', type: 'single', required: true,
          label: { en: 'Yes or no?' },
          help: { en: 'Tick one' },
          preamble: { en: 'NOT LOCALIZED' },
          inputLabel: { en: 'ALSO NOT LOCALIZED' },
          choices: [
            { label: { en: 'Yes' }, value: 'Yes' },
            { label: { en: 'No' }, value: 'No' },
          ],
        },
        {
          id: 'Q2', section: 'A', type: 'multi-field', required: true,
          label: { en: 'Yes or no?' },
          subFields: [{ id: 'Q2_1', label: { en: 'Yes' }, kind: 'short-text' }],
        },
      ],
    },
  ],
  unsupported: [],
};

describe('collectEnglishStrings', () => {
  it('collects exactly the six fields applyTranslations localizes, unique, in first-appearance order', () => {
    const out = collectEnglishStrings(base);
    expect(out.map((e) => e.text)).toEqual(['Profile', 'Intro', 'Yes or no?', 'Tick one', 'Yes', 'No']);
    expect(out.map((e) => e.text)).not.toContain('NOT LOCALIZED');
    expect(out.map((e) => e.text)).not.toContain('ALSO NOT LOCALIZED');
  });

  it('merges kinds and ids when the same English recurs', () => {
    const yes = collectEnglishStrings(base).find((e) => e.text === 'Yes')!;
    expect(yes.kinds).toEqual(['choice.label', 'subField.label']);
    expect(yes.ids).toEqual(['Q1', 'Q2_1']);
    const stem = collectEnglishStrings(base).find((e) => e.text === 'Yes or no?')!;
    expect(stem.ids).toEqual(['Q1', 'Q2']);
  });

  it('real spec: unique English string count is stable (snapshot = the Aug-21 anchor universe)', () => {
    const md = readFileSync(resolve(__dirname, '../../spec/F2-Spec.md'), 'utf-8');
    const out = collectEnglishStrings(parseSpec(md));
    expect(out.length).toMatchSnapshot();
    expect(out.every((e) => e.text.length > 0)).toBe(true);
  });
});
```

- [ ] **Step 2: Run test to verify it fails** — Run (PowerShell, in `APP`): `npx vitest run scripts/lib/english-strings.test.ts` Expected: FAIL — `Cannot find module './english-strings'`.

- [ ] **Step 3: Write minimal implementation**

```ts
// deliverables/F2/PWA/app/scripts/lib/english-strings.ts
// The exact set of English source strings that scripts/lib/apply-translations.ts
// localizes (section.title, section.preamble, item.label, item.help, choice.label,
// subField.label). item.preamble / item.inputLabel are deliberately NOT included:
// applyTranslations() never passes them through localizeString(), so a map key for
// them would be dead. This list is the anchor universe for the F2 paper extractor.
import type { ParseResult } from './types';

export type EnglishKind =
  | 'section.title'
  | 'section.preamble'
  | 'item.label'
  | 'item.help'
  | 'choice.label'
  | 'subField.label';

export interface EnglishStringEntry {
  text: string;
  kinds: EnglishKind[];
  ids: string[];
}

export function collectEnglishStrings(result: ParseResult): EnglishStringEntry[] {
  const order: string[] = [];
  const byText = new Map<string, EnglishStringEntry>();
  const add = (text: string, kind: EnglishKind, id: string): void => {
    if (!text) return;
    let e = byText.get(text);
    if (!e) {
      e = { text, kinds: [], ids: [] };
      byText.set(text, e);
      order.push(text);
    }
    if (!e.kinds.includes(kind)) e.kinds.push(kind);
    if (!e.ids.includes(id)) e.ids.push(id);
  };
  for (const s of result.sections) {
    add(s.title.en, 'section.title', s.id);
    if (s.preamble) add(s.preamble.en, 'section.preamble', s.id);
    for (const it of s.items) {
      add(it.label.en, 'item.label', it.id);
      if (it.help) add(it.help.en, 'item.help', it.id);
      for (const c of it.choices ?? []) add(c.label.en, 'choice.label', it.id);
      for (const sf of it.subFields ?? []) add(sf.label.en, 'subField.label', sf.id);
    }
  }
  return order.map((t) => byText.get(t)!);
}
```

- [ ] **Step 4: Run test to verify it passes** — Run: `npx vitest run scripts/lib/english-strings.test.ts` Expected: PASS, `1 snapshot written` (creates `scripts/lib/__snapshots__/english-strings.test.ts.snap`). Re-run once more: `1 snapshot passed`.

- [ ] **Step 5: Verify/gate** — Run: `npx tsc -b --force` Expected: exit 0 (no unused locals, `exactOptionalPropertyTypes` satisfied — the test object literals only set optional fields to real values).

- [ ] **Step 6: Record** — note the snapshot number (the unique-string count) in the wave-2 note (`deliverables/CSPro/patch-notes/draft-f2-m4-aug21-translations.md`, create it; renamed to `<EVDATE>-f2-m4-aug21-translations.md` in Task 23); it is the denominator "anchors" for the extractor report. Commit later with Task 23 (F2 changes are committed + pushed because `deploy-f2-pwa.ps1:165-190` requires HEAD == origin/main).

---

### Task 13: `scripts/dump-english-strings.ts` → `spec/english-strings.json`

**Files:**
- Create: `deliverables/F2/PWA/app/scripts/dump-english-strings.ts`
- Modify: `deliverables/F2/PWA/app/package.json` (add `"dump:english"` script after `"generate": "tsx scripts/generate.ts",` at :17)
- Test: covered by Task 12's vitest (collector) + a CLI smoke check in Step 3

**Interfaces:**
- Consumes: `collectEnglishStrings(result)` (Task 12); `parseSpec(markdown)` (`parse-spec.ts:342`).
- Produces: file `spec/english-strings.json` with shape `{ "source": "spec/F2-Spec.md", "count": N, "strings": [ { "text", "kinds", "ids" } ] }` — **deterministic for an unchanged spec (no timestamp)** so re-dumps never create spurious diffs. The F2 anchor set consumed by Task 14 (`f2_labels()`) and Task 15 (`load_english_set()`).

- [ ] **Step 1: Write the failing test (CLI existence check)** — Run: `npx tsx scripts/dump-english-strings.ts` Expected: FAIL — file not found.

- [ ] **Step 2: Write minimal implementation**

```ts
#!/usr/bin/env tsx
// deliverables/F2/PWA/app/scripts/dump-english-strings.ts
/**
 * Dump the exact English strings applyTranslations() localizes, for the paper
 * extractor (deliverables/CSPro/data/translations-official/anchor_extract_f2.py).
 * Invoke: `npm run dump:english`  ->  spec/english-strings.json
 * Output is deterministic (no timestamp): it changes only when F2-Spec.md changes.
 */
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import { collectEnglishStrings } from './lib/english-strings';
import { parseSpec } from './lib/parse-spec';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const APP_ROOT = resolve(__dirname, '..');
const SPEC_PATH = resolve(APP_ROOT, 'spec/F2-Spec.md');
const OUT_PATH = resolve(APP_ROOT, 'spec/english-strings.json');

const strings = collectEnglishStrings(parseSpec(readFileSync(SPEC_PATH, 'utf-8')));
const payload = {
  source: 'spec/F2-Spec.md',
  count: strings.length,
  strings,
};
writeFileSync(OUT_PATH, JSON.stringify(payload, null, 1) + '\n', 'utf-8');
console.log(`dump-english-strings: ${strings.length} unique English strings -> ${OUT_PATH}`);
```

package.json edit (insert one line after `"generate": "tsx scripts/generate.ts",`):

```json
    "dump:english": "tsx scripts/dump-english-strings.ts",
```

- [ ] **Step 3: Run to verify it works** — Run: `npm run dump:english` Expected: `dump-english-strings: N unique English strings -> ...spec/english-strings.json` where N equals the Task 12 snapshot. Check: `node -e "const j=require('./spec/english-strings.json');console.log(j.count, j.strings[0].text)"` → `N Healthcare Worker Profile`. Run `npm run dump:english` a second time and `git status --short spec/english-strings.json` must show the same single `??` entry with no content change (`git diff --no-index` against a copy is identical) — determinism check.

- [ ] **Step 4: Verify/gate** — Run: `npx tsc -b --force; npx vitest run scripts/lib` Expected: both exit 0. `git status --short spec/` shows only `?? spec/english-strings.json` (committed as a build input).

- [ ] **Step 5: Record** — write the count into the wave-2 note as "F2 anchors: N".

---

### Task 14: F2 mode of the paper extractor (`anchor_extract_f2.py`) + pytest

**Files:**
- Create: `deliverables/CSPro/data/translations-official/anchor_extract_f2.py`
- Test: `deliverables/CSPro/data/translations-official/test_anchor_extract_f2.py`

**Interfaces:**
- Consumes (unchanged helpers, loaded by explicit path — `TOFF/anchor_extract.py` from Task 1, else `deliverables/CSPro/translations-paper-extract/anchor_extract.py`): `pdf_text(path)`, `build_norm(text)` → `(ntext, idx)`, `norm_for_match(s)`, `clean_span(span)`, `qa_flags(en, tr, nlabels)`, `LANGS` (`[(paper_name, CODE), …]`). `MIN_EMIT`/`MIN_BOUND` are NOT imported — F2 uses its own. Input file `spec/english-strings.json` (Task 13).
- Produces: module constants `F2_MIN_BOUND = 2`, `F2_MIN_EMIT = 2`, `SHORT_ANCHOR = 6`; `f2_labels(path) -> dict[str, dict]` (`{EN text: {}}`); `find_paper(source_dir, paper_name) -> Path|None`; `extract_text(text: str, labels: dict) -> {"anchored": int, "clean": {EN: tr}, "flagged": [{"en","tr","flags"}], "collisions": {norm: [EN, ...]}}`; `extract_pdf(pdf_path, labels)`; CLI `python anchor_extract_f2.py --source DIR --english-strings PATH --out DIR` writing `OUT/{loc}.json` (clean, English-keyed), `OUT/{loc}_flagged.json`, `OUT/QA-REPORT.md` (incl. a collisions section) for `loc ∈ fil,bcl,bis,ceb,war,hil,ilo`. Locale mapping `CODE_TO_LOC = {"FIL":"fil","BCL":"bcl","BIS":"bis","CEB":"ceb","WAR":"war","HIL":"hil","ILO":"ilo"}`. Output root is `out-aug21/F2/` (same tree as the CSPro extractor, already gitignored by Task 0).

- [ ] **Step 1: Write the failing test**

```python
# deliverables/CSPro/data/translations-official/test_anchor_extract_f2.py
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anchor_extract_f2 as x  # noqa: E402

LABELS = {
    "What is your role at this health facility?": {},
    "Administrator": {},
    "Other (specify)": {},
    "How old are you as of your last birthday (in years)?": {},
}

# Tagalog-style layout (English line, translation line, boxed options)
TAGALOG = ("4. How old are you as of your last birthday (in years)? "
           "Ilang na kayong taon noong huling kaarawan ninyo? "
           "5. What is your role at this health facility? "
           "Ano ang iyong tungkulin sa health facility na ito? "
           "☐ Administrator Tagapangasiwa ☐ Other (specify) Iba pa, tukuyin 6. Next")

# Bicolano-style inline layout: options echo English; 'Other' glued/truncated
BICOL = ("4. How old are you as of your last birthday (in years)? "
         "Pira an edad mo sa huring kaarawan mo (sa taon)? "
         "5. What is your role at this health facility? "
         "Ano an saimong papel sa health facility na ini? "
         "☐ Administrator Administrator ☐ Other (specify) ba pa, ispecify 6. Next")

YESNO_LABELS = {"Do you have a license?": {}, "Yes": {}, "No": {}}
# short anchors: 'Yes'/'No' must bound AND emit when box-prefixed; a bare 'no'
# inside the translation must NOT cut the stem span
YESNO = ("7. Do you have a license? Mayroon ka bang lisensya (oo o no)? "
         "☐ Yes Oo ☐ No Hindi")


def test_spans_between_anchors_tagalog():
    r = x.extract_text(TAGALOG, LABELS)
    assert r["clean"]["How old are you as of your last birthday (in years)?"] == \
        "Ilang na kayong taon noong huling kaarawan ninyo? 5"
    assert r["clean"]["What is your role at this health facility?"] == \
        "Ano ang iyong tungkulin sa health facility na ito?"
    assert r["clean"]["Administrator"] == "Tagapangasiwa"
    assert r["clean"]["Other (specify)"] == "Iba pa, tukuyin 6. Next"


def test_bicolano_echo_is_flagged_not_imported():
    r = x.extract_text(BICOL, LABELS)
    assert "Administrator" not in r["clean"]
    flagged = {f["en"]: f for f in r["flagged"]}
    assert "echo-english" in flagged["Administrator"]["flags"]
    assert flagged["Administrator"]["tr"] == "Administrator"
    # stems still extract from the inline layout — no line assumptions
    assert r["clean"]["What is your role at this health facility?"] == \
        "Ano an saimong papel sa health facility na ini?"
    assert r["clean"]["Other (specify)"] == "ba pa, ispecify 6. Next"


def test_short_yes_no_anchors_extract_and_stem_not_bled():
    r = x.extract_text(YESNO, YESNO_LABELS)
    assert r["clean"]["Yes"] == "Oo"
    assert r["clean"]["No"] == "Hindi"
    assert r["clean"]["Do you have a license?"] == "Mayroon ka bang lisensya (oo o no)?"
    assert not [f for f in r["flagged"] if f["en"] == "Do you have a license?"]


def test_normalized_collisions_emit_under_every_original():
    labels = {"Other (specify)": {}, "Other, specify": {}, "What is your role at this health facility?": {}}
    text = ("5. What is your role at this health facility? Ano ang tungkulin mo? "
            "☐ Other (specify) Iba pa, tukuyin")
    r = x.extract_text(text, labels)
    assert r["collisions"] == {"other specify": ["Other (specify)", "Other, specify"]}
    assert r["clean"]["Other (specify)"] == "Iba pa, tukuyin"
    assert r["clean"]["Other, specify"] == "Iba pa, tukuyin"


def test_f2_labels_reads_english_strings_json(tmp_path):
    p = tmp_path / "english-strings.json"
    p.write_text(json.dumps({"count": 2, "strings": [
        {"text": "Yes", "kinds": ["choice.label"], "ids": ["Q7"]},
        {"text": "What is your name?", "kinds": ["item.label"], "ids": ["Q1"]}]}),
        encoding="utf-8")
    labs = x.f2_labels(str(p))
    assert list(labs) == ["Yes", "What is your name?"]
    assert labs["Yes"] == {}


def test_paper_glob_matches_aug21_names(tmp_path):
    (tmp_path / "F2-Cebuano_Healthcare Worker_Survey_UHC Year 2_Aug21.pdf").write_bytes(b"")
    (tmp_path / "F2-Tagalog_Healthcare Worker Survey Questionnaire_UHC Year 2_Aug21.pdf").write_bytes(b"")
    assert x.find_paper(str(tmp_path), "Cebuano").name.startswith("F2-Cebuano_")
    assert x.find_paper(str(tmp_path), "Tagalog").name.startswith("F2-Tagalog_")
    assert x.find_paper(str(tmp_path), "Waray") is None
```

Note on the first assertion: the trailing ` 5` / ` 6. Next` residue is *expected* from the raw span rule (the next question's number sits before the next anchor); `digit-mismatch` does not fire because it requires digits on BOTH sides (`anchor_extract.py` `digits_of`, `de and dt`) and the English has none. The extractor does not guess — the apply script strips bare trailing numbers (Task 15 `strip_qnum_residue(tr, en)`).

- [ ] **Step 2: Run test to verify it fails** — Run (PowerShell, from `TOFF`): `$env:PYTHONIOENCODING='utf-8'; python -m pytest test_anchor_extract_f2.py -q` Expected: FAIL — `ModuleNotFoundError: No module named 'anchor_extract_f2'`.

- [ ] **Step 3: Write minimal implementation**

```python
"""F2 mode of the paper extractor.

Anchors on the F2 PWA's English strings (spec/english-strings.json, produced by
`npm run dump:english`) instead of a CSPro dcf, and emits ENGLISH-TEXT-KEYED pairs
per locale because the PWA store (spec/translations/{loc}.json) is flat English-keyed.
Span rule is the anchor rule from anchor_extract.py: translation = text between one
English anchor and the next kept anchor. No line/column assumptions, so the Bicolano
inline layout extracts identically.

F2-specific rules (differ from the F1/F3/F4 extractor):
  * F2_MIN_BOUND / F2_MIN_EMIT = 2 so 'Yes'/'No'/'Male' options bound AND emit;
    an anchor shorter than SHORT_ANCHOR normalized chars counts only when the paper
    prefixes it with a box glyph (option layout), so a bare 'no' inside a translation
    never cuts a span.
  * Back-to-back hits of the SAME anchor with nothing but whitespace/box glyphs
    between them (Bicolano '☐ Administrator Administrator') collapse into ONE echo
    occurrence flagged 'echo-english' (the raw gap would otherwise read as 'empty').
  * Distinct English strings that normalize identically are reported as collisions
    and the translation is emitted under every colliding original key.

Usage (PowerShell):
  $env:PYTHONIOENCODING='utf-8'
  python anchor_extract_f2.py --source "C:/.../raw/Survey-Instruments-2026-08-21/Translations" `
      --english-strings "C:/.../deliverables/F2/PWA/app/spec/english-strings.json" `
      --out "C:/.../deliverables/CSPro/data/translations-official/out-aug21/F2"
"""
import argparse
import importlib.util
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent

# Prefer the committed Day-0 copy next to this file; fall back to the gitignored
# on-disk original. Explicit path, so the two can never be confused.
_CANDIDATES = [HERE / "anchor_extract.py",
               HERE.parents[1] / "translations-paper-extract" / "anchor_extract.py"]
_AE_PATH = next(p for p in _CANDIDATES if p.exists())
_spec = importlib.util.spec_from_file_location("anchor_extract", _AE_PATH)
_ae = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_ae)          # safe: anchor_extract.py guards main() (:327)
pdf_text, build_norm, norm_for_match = _ae.pdf_text, _ae.build_norm, _ae.norm_for_match
clean_span, qa_flags, LANGS = _ae.clean_span, _ae.qa_flags, _ae.LANGS

CODE_TO_LOC = {"FIL": "fil", "BCL": "bcl", "BIS": "bis", "CEB": "ceb",
               "WAR": "war", "HIL": "hil", "ILO": "ilo"}
F2_MIN_BOUND = 2       # 'No' must bound a span
F2_MIN_EMIT = 2        # ... and be emitted
SHORT_ANCHOR = 6       # below this, an anchor counts only when box-prefixed on paper
_BOX_BEFORE = re.compile(r"[☐☑☒□■❑]\s*$")


def f2_labels(path):
    """spec/english-strings.json -> {EN text: {}} (same shape as dcf_labels())."""
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    return {s["text"]: {} for s in d["strings"] if s.get("text")}


def find_paper(source_dir, paper_name):
    """Aug-21 naming is instrument-first: F2-{Language}_*.pdf."""
    cands = sorted(Path(source_dir).glob(f"F2-{paper_name}_*.pdf"))
    return cands[0] if cands else None


def _box_prefixed(text, orig_start):
    return bool(_BOX_BEFORE.search(text[max(0, orig_start - 4):orig_start]))


def extract_text(text, labels):
    ntext, idx = build_norm(text)
    by_norm = defaultdict(list)                 # norm form -> [original EN, ...]
    for en in labels:
        ne = norm_for_match(en)
        if ne:
            by_norm[ne].append(en)
    collisions = {ne: ens for ne, ens in by_norm.items() if len(ens) > 1}
    occ = []
    for ne in by_norm:
        if len(ne) < F2_MIN_BOUND:
            continue
        pat = re.compile(r"(?<![a-z0-9])" + re.escape(ne) + r"(?![a-z0-9])")
        for m in list(pat.finditer(ntext))[:64]:
            if len(ne) < SHORT_ANCHOR and not _box_prefixed(text, idx[m.start()]):
                continue                        # stray short word, not an option
            occ.append((m.start(), m.end(), ne))
    occ.sort()
    kept = []                                   # de-overlap: keep the longest anchor
    for s, e, ne in occ:
        if kept and s < kept[-1][1]:
            if (e - s) > (kept[-1][1] - kept[-1][0]):
                kept[-1] = (s, e, ne)
            continue
        kept.append((s, e, ne))
    merged = []                                 # collapse echoes: (s, e, ne, echo)
    for s, e, ne in kept:
        if merged and merged[-1][2] == ne and not ntext[merged[-1][1]:s].strip():
            ps, _pe, _ne, _ = merged[-1]
            merged[-1] = (ps, e, ne, True)
            continue
        merged.append((s, e, ne, False))
    cands = defaultdict(list)
    for i, (s, e, ne, echo) in enumerate(merged):
        if len(ne) < F2_MIN_EMIT:
            continue                            # bounds spans but does not emit
        if echo:
            cands[ne].append(by_norm[ne][0])    # verbatim English -> qa_flags: echo-english
            continue
        nxt = merged[i + 1][0] if i + 1 < len(merged) else len(ntext)
        start = idx[e - 1] + 1
        end = idx[nxt] if nxt < len(idx) else len(text)
        cands[ne].append(clean_span(text[start:end]))
    nset = set(by_norm)
    clean, flagged = {}, []
    for ne, spans in cands.items():
        en0 = by_norm[ne][0]
        scored = [(sp, qa_flags(en0, sp, nset)) for sp in spans]
        ok = [sp for sp, fl in scored if not fl]
        for en in by_norm[ne]:                  # emit under every colliding original
            if ok:
                clean[en] = Counter(ok).most_common(1)[0][0]
            else:
                sp, fl = scored[0]
                flagged.append({"en": en, "tr": sp, "flags": fl})
    return {"anchored": len(merged), "clean": clean, "flagged": flagged,
            "collisions": collisions}


def extract_pdf(pdf_path, labels):
    r = extract_text(pdf_text(str(pdf_path)), labels)
    r["file"] = Path(pdf_path).name
    return r


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--english-strings", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    labels = f2_labels(a.english_strings)
    rows, collisions = [], {}
    for paper, code in LANGS:
        loc = CODE_TO_LOC[code]
        pdf = find_paper(a.source, paper)
        if pdf is None:
            rows.append((loc, "NO PDF", 0, 0, 0, 0)); continue
        r = extract_pdf(pdf, labels)
        collisions = r["collisions"]
        echoes = sum(1 for f in r["flagged"] if "echo-english" in f["flags"])
        (out / f"{loc}.json").write_text(
            json.dumps(r["clean"], ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        (out / f"{loc}_flagged.json").write_text(
            json.dumps(r["flagged"], ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        rows.append((loc, r["file"], r["anchored"], len(r["clean"]), len(r["flagged"]), echoes))
    lines = ["# F2 Aug-21 paper extract — QA report", "",
             f"anchors (unique English strings): {len(labels)}",
             f"thresholds: F2_MIN_BOUND={F2_MIN_BOUND} F2_MIN_EMIT={F2_MIN_EMIT} "
             f"SHORT_ANCHOR={SHORT_ANCHOR} (box-prefix rule)", "",
             "| locale | file | anchored | clean | flagged | of which echo-english |",
             "|---|---|---|---|---|---|"]
    lines += [f"| {l} | {f} | {an} | {c} | {fl} | {ec} |" for l, f, an, c, fl, ec in rows]
    lines += ["", f"## Normalized-key collisions ({len(collisions)})", ""]
    lines += [f"- `{ne}` <- {ens}" for ne, ens in sorted(collisions.items())] or ["- none"]
    (out / "QA-REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run test to verify it passes** — Run: `$env:PYTHONIOENCODING='utf-8'; python -m pytest test_anchor_extract_f2.py -q` Expected: `6 passed`.

- [ ] **Step 5: Verify/gate (real PDFs, dry data)** — Run (PowerShell, from `TOFF`):

```
$env:PYTHONIOENCODING='utf-8'
python anchor_extract_f2.py --source "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/Survey-Instruments-2026-08-21/Translations" --english-strings "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/F2/PWA/app/spec/english-strings.json" --out "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSPro/data/translations-official/out-aug21/F2"
```

Expected: 7 table rows, each with a file name (no `NO PDF`), `anchored` in the hundreds, `clean` > 0 for every locale, and `Yes`/`No` present as keys in `fil.json` (proves the short-anchor rule works on real PDFs); `bcl` shows the lowest `clean` and the highest `of which echo-english` — that is the expected Bicolano yield (untranslated options echo English on that paper). Read the collisions section: each entry is a pair of spec strings that differ only in punctuation/case — note them in the wave note; none needs action unless the two strings should carry different translations (then the flat store cannot express it — see Task 23 Step 6). Confirm the output is ignored: `git check-ignore -q deliverables/CSPro/data/translations-official/out-aug21/F2/fil.json; if ($?) { 'ignored' }` (the root rule added in Task 0 covers it — do NOT create a folder-level `.gitignore`).

- [ ] **Step 6: Record** — paste the QA table into the wave-2 note. Do not commit `out-aug21/` (data stays gitignored). `anchor_extract_f2.py` and its test are CSPro-side files → left in the working tree for Carl.

---

### Task 15: `apply-paper-translations.py` decision rules + pytest

**Files:**
- Create: `deliverables/F2/PWA/app/scripts/apply-paper-translations.py`
- Test: `deliverables/F2/PWA/app/scripts/test_apply_paper_translations.py`

**Interfaces:**
- Consumes: `OUT/{loc}.json` from Task 14 (`{EN: tr}`); `spec/english-strings.json` (Task 13); `deliverables/CSPro/data/translations-official/aug21-overrides.json` — F2 section shape `{"F2": {"<loc>": {"<English string>": {"keep": "<text>" | null, "reason": "..."}}}}` (the F2 section nests a locale level because `keep` is locale text; `"keep": null` means "do not write this key at all"; missing file / missing `F2` key → no overrides; validated by Task 3's `aug21_overrides.py`). Existing maps `spec/translations/{loc}.json` (flat `{EN: tr}`, indent 1, CRLF today).
- Produces: `LOCALES = ["fil","ceb","bis","ilo","hil","war","bcl"]` (same order as `TRANSLATION_LOCALES`, `apply-translations.ts:8`); `strip_qnum_residue(tr: str, en: str) -> str`; `decide(en, tr, current, english_set, overrides_loc) -> tuple[str, str|None]` with action ∈ `{"unmatched","override","skip_same_as_english","already_same","write","replace"}` — **overrides are consulted first** so they can also suppress a fresh write; `apply_locale(extract, current, english_set, overrides_loc) -> (new_map: OrderedDict, counts: dict, rows: list)`; `load_map(path) -> (OrderedDict, crlf: bool)` / `save_map(path, data, crlf)` (indent=1, `ensure_ascii=False`, line endings as loaded, trailing newline); CLI `python scripts/apply-paper-translations.py [--extract-dir DIR] [--overrides PATH] [--apply] [--report PATH]` (dry-run by default; a map is saved only when its content actually changed; the script never writes an empty string — `keep: null` leaves the key absent, and `readMap` would silently drop `""` anyway, which would make the Task 22 orphan test fail for a structural reason).

- [ ] **Step 1: Write the failing test**

```python
# deliverables/F2/PWA/app/scripts/test_apply_paper_translations.py
import importlib.util, io, os

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "apply_paper_translations", os.path.join(HERE, "apply-paper-translations.py"))
m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m)

EN = {"What is your name?", "Yes", "No", "Other (specify)", "Level 3"}


def test_strip_qnum_residue():
    # bare trailing number after any text is residue when the English has no trailing digit
    assert m.strip_qnum_residue("Ilang taon ka na? 5", "How old are you?") == "Ilang taon ka na?"
    assert m.strip_qnum_residue("Tagapangasiwa 6", "Administrator") == "Tagapangasiwa"
    assert m.strip_qnum_residue("Oo 13.1", "Yes") == "Oo"
    assert m.strip_qnum_residue("Tapos na.) 12", "Done.)") == "Tapos na.)"
    # not residue: number is not at the very end
    assert m.strip_qnum_residue("Iba pa, tukuyin 6. Next", "Other (specify)") == "Iba pa, tukuyin 6. Next"
    # not residue: the English itself ends in a digit
    assert m.strip_qnum_residue("Antas 3", "Level 3") == "Antas 3"


def test_decide_rules():
    cur = {"Yes": "Oo", "No": "Hindi"}
    assert m.decide("Nope", "x", cur, EN, {}) == ("unmatched", None)
    assert m.decide("Yes", "yes", cur, EN, {}) == ("skip_same_as_english", None)
    assert m.decide("Yes", "Oo", cur, EN, {}) == ("already_same", None)
    assert m.decide("What is your name?", "Ano ang pangalan mo?", cur, EN, {}) == ("write", "Ano ang pangalan mo?")
    assert m.decide("No", "Wala", cur, EN, {}) == ("replace", "Wala")               # Aug-21 wins
    ov = {"No": {"keep": "Hindi", "reason": "PDF carries the June-5 swap"}}
    assert m.decide("No", "Wala", cur, EN, ov) == ("override", "Hindi")
    # overrides run BEFORE the write branch: keep=null suppresses a fresh write of an absent key
    ov2 = {"What is your name?": {"keep": None, "reason": "mis-anchored span"}}
    assert m.decide("What is your name?", "junk", cur, EN, ov2) == ("override", None)
    # a hand-corrected keep that differs from the current value is applied
    ov3 = {"No": {"keep": "Dili", "reason": "corrected by hand"}}
    assert m.decide("No", "Wala", cur, EN, ov3) == ("override", "Dili")


def test_apply_locale_preserves_order_and_appends():
    cur = {"Yes": "Oo", "No": "Hindi"}
    ext = {"No": "Wala", "What is your name?": "Ano ang pangalan mo?", "Junk": "x", "Yes": "Oo"}
    new, counts, rows = m.apply_locale(ext, cur, EN, {})
    assert list(new) == ["Yes", "No", "What is your name?"]
    assert new["No"] == "Wala"
    assert counts == {"unmatched": 1, "override": 0, "skip_same_as_english": 0,
                      "already_same": 1, "write": 1, "replace": 1}
    assert {"en": "No", "action": "replace", "was": "Hindi", "now": "Wala"} in rows


def test_apply_locale_override_null_never_writes_and_keep_changes_map():
    cur = {"No": "Hindi"}
    ext = {"What is your name?": "junk", "No": "Wala"}
    ov = {"What is your name?": {"keep": None, "reason": "mis-anchored"},
          "No": {"keep": "Dili", "reason": "hand-corrected"}}
    new, counts, rows = m.apply_locale(ext, cur, EN, ov)
    assert "What is your name?" not in new
    assert new["No"] == "Dili"
    assert counts["override"] == 2 and counts["write"] == 0 and counts["replace"] == 0
    assert new != cur                       # -> main() saves this map


def test_save_map_preserves_line_endings(tmp_path):
    p = tmp_path / "fil.json"
    m.save_map(str(p), {"Yes": "Oo", "ñ": "Biñan"}, crlf=True)
    raw = io.open(p, encoding="utf-8", newline="").read()
    assert raw == '{\r\n "Yes": "Oo",\r\n "ñ": "Biñan"\r\n}\r\n'   # indent 1, CRLF, no escaping
    data, crlf = m.load_map(str(p))
    assert dict(data) == {"Yes": "Oo", "ñ": "Biñan"} and crlf is True
    m.save_map(str(p), data, crlf=False)
    assert io.open(p, encoding="utf-8", newline="").read() == '{\n "Yes": "Oo",\n "ñ": "Biñan"\n}\n'
    assert m.load_map(str(p))[1] is False
```

- [ ] **Step 2: Run test to verify it fails** — Run (PowerShell, from `APP`): `$env:PYTHONIOENCODING='utf-8'; python -m pytest scripts/test_apply_paper_translations.py -q` Expected: FAIL — `FileNotFoundError` on `apply-paper-translations.py`.

- [ ] **Step 3: Write minimal implementation**

```python
"""Apply Aug-21 paper translations to the F2 PWA store.

Input  = deliverables/CSPro/data/translations-official/out-aug21/F2/{loc}.json
         (anchor_extract_f2.py output, ENGLISH-TEXT-KEYED — the PWA store is flat
         English-keyed, applied by scripts/lib/apply-translations.ts at generate time).
Join   = EXACT English string against spec/english-strings.json (the six fields
         applyTranslations() localizes). Question-number joins are NOT used
         (2026-08-13 row-misalignment scar).
Rule   = overrides first: aug21-overrides.json["F2"][loc][english] = {"keep": text|null}
         -> keep text (written if it differs from the map) or null (never write).
         Otherwise Aug-21 wins: absent -> write; equal -> already_same; different -> replace.
Residue= a bare trailing question number swept in from the paper is stripped unless the
         English string itself ends in a digit (audit-translations.py flags '\\s\\d{1,3}$').
Format = indent 1, ensure_ascii=False, line endings preserved as loaded (maps are CRLF
         today), trailing newline; a map is saved only when its content changed.
No _meta is written into the maps: readMap() drops non-strings silently and
scripts/audit-translations.py would crash on a dict value. Provenance -> --report.

  python scripts/apply-paper-translations.py            # dry run, report only
  python scripts/apply-paper-translations.py --apply    # write spec/translations/{loc}.json
"""
import argparse
import io
import json
import os
import re
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.abspath(os.path.join(HERE, ".."))
ROOT = os.path.abspath(os.path.join(APP, "..", "..", "..", ".."))
TDIR = os.path.join(APP, "spec", "translations")
ENGLISH_STRINGS = os.path.join(APP, "spec", "english-strings.json")
DEFAULT_EXTRACT = os.path.join(ROOT, "deliverables", "CSPro", "data", "translations-official",
                               "out-aug21", "F2")
DEFAULT_OVERRIDES = os.path.join(ROOT, "deliverables", "CSPro", "data", "translations-official",
                                 "aug21-overrides.json")
DEFAULT_REPORT = os.path.join(DEFAULT_EXTRACT, "apply-report.json")
LOCALES = ["fil", "ceb", "bis", "ilo", "hil", "war", "bcl"]
ACTIONS = ["unmatched", "override", "skip_same_as_english", "already_same", "write", "replace"]
_RESIDUE = re.compile(r"\s+\d{1,3}(?:\.\d{1,2})?\s*$")
_EN_ENDS_DIGIT = re.compile(r"\d\s*$")


def norm(s):
    return " ".join((s or "").replace("\u2019", "'").replace("\u2018", "'").split())


def strip_qnum_residue(tr, en):
    """Drop a bare next-question number swept in after the translation, unless the
    English string itself ends in a digit (then the number is content, e.g. 'Level 3')."""
    val = norm(tr)
    if _EN_ENDS_DIGIT.search(en or ""):
        return val
    return _RESIDUE.sub("", val).rstrip()


def load_map(path):
    """-> (OrderedDict, crlf_flag). Line-ending style is detected so save_map can keep it."""
    with io.open(path, encoding="utf-8", newline="") as fh:
        raw = fh.read()
    if raw.startswith("\ufeff"):
        raw = raw[1:]
    crlf = "\r\n" in raw
    data = json.loads(raw, object_pairs_hook=OrderedDict) if raw.strip() else OrderedDict()
    return data, crlf


def save_map(path, data, crlf):
    with io.open(path, "w", encoding="utf-8", newline="\r\n" if crlf else "\n") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
        fh.write("\n")


def load_english_set(path=ENGLISH_STRINGS):
    d = json.load(io.open(path, encoding="utf-8"))
    return {s["text"] for s in d["strings"] if s.get("text")}


def load_overrides(path, loc):
    if not os.path.exists(path):
        return {}
    d = json.load(io.open(path, encoding="utf-8"))
    return (d.get("F2") or {}).get(loc) or {}


def decide(en, tr, current, english_set, overrides_loc):
    if en not in english_set:
        return "unmatched", None
    if en in overrides_loc:                       # overrides win over every other rule
        return "override", overrides_loc[en].get("keep")
    val = strip_qnum_residue(tr, en)
    if not val or val.casefold() == norm(en).casefold():
        return "skip_same_as_english", None
    cur = current.get(en)
    if cur is not None and norm(cur) == val:
        return "already_same", None
    if cur is None:
        return "write", val
    return "replace", val


def apply_locale(extract, current, english_set, overrides_loc):
    new = OrderedDict(current)
    counts = {a: 0 for a in ACTIONS}
    rows = []
    for en, tr in extract.items():
        action, val = decide(en, tr, current, english_set, overrides_loc)
        counts[action] += 1
        if action in ("write", "replace"):
            rows.append({"en": en, "action": action, "was": current.get(en), "now": val})
            new[en] = val
        elif action == "override":
            rows.append({"en": en, "action": action, "was": current.get(en), "now": val,
                         "reason": overrides_loc[en].get("reason")})
            if val is not None and new.get(en) != val:
                new[en] = val                    # hand-corrected keep is applied
            # val is None -> never write this key (leave map as-is)
    return new, counts, rows


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--extract-dir", default=DEFAULT_EXTRACT)
    ap.add_argument("--overrides", default=DEFAULT_OVERRIDES)
    ap.add_argument("--report", default=DEFAULT_REPORT)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args(argv)
    english_set = load_english_set()
    report = {"source": "raw/Survey-Instruments-2026-08-21/Translations", "provenance": "aug21",
              "mode": "APPLY" if a.apply else "DRY RUN", "locales": {}}
    print(f"{'APPLIED' if a.apply else 'DRY RUN'}  anchors={len(english_set)}")
    print("locale  unmatched  override  same-as-en  already  write  replace  saved")
    for loc in LOCALES:
        src = os.path.join(a.extract_dir, f"{loc}.json")
        if not os.path.exists(src):
            print(f"{loc:6}  (no extract)"); continue
        extract, _ = load_map(src)
        path = os.path.join(TDIR, f"{loc}.json")
        current, crlf = load_map(path) if os.path.exists(path) else (OrderedDict(), True)
        new, counts, rows = apply_locale(extract, current, english_set, load_overrides(a.overrides, loc))
        changed = new != current
        c = counts
        print(f"{loc:6}  {c['unmatched']:9}  {c['override']:8}  {c['skip_same_as_english']:10}  "
              f"{c['already_same']:7}  {c['write']:5}  {c['replace']:7}  "
              f"{'yes' if (a.apply and changed) else ('would' if changed else 'no')}")
        report["locales"][loc] = {"counts": counts, "rows": rows, "changed": changed,
                                  "unmatched": sorted(k for k in extract if k not in english_set)}
        if a.apply and changed:
            save_map(path, new, crlf)
    os.makedirs(os.path.dirname(a.report), exist_ok=True)
    with io.open(a.report, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)
    print(f"report -> {a.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test to verify it passes** — Run: `$env:PYTHONIOENCODING='utf-8'; python -m pytest scripts/test_apply_paper_translations.py -q` Expected: `5 passed`.

- [ ] **Step 5: Verify/gate (dry run against the real extract)** — Run (PowerShell, from `APP`): `$env:PYTHONIOENCODING='utf-8'; python scripts/apply-paper-translations.py` Expected: one row per locale; `unmatched` small (paper strings not in the build, e.g. `<proceed to Q31>` notes); `write` + `replace` > 0 for at least fil/ceb/ilo; `saved` column reads `would` for every locale with changes; `report -> ...out-aug21/F2/apply-report.json`. `git status --short spec/translations` is EMPTY (dry run writes nothing).

- [ ] **Step 6: Record** — attach the dry-run table to the wave-2 note. Review `apply-report.json` `rows` where `action == "replace"`: any replacement that re-introduces a June-5 defect (compare against `deliverables/CSPro/data/translations-official/FINDINGS.md` §4 live defects and `recovery_exclusions.json`) becomes an entry under `"F2": {"<loc>": {...}}` in `aug21-overrides.json` with `keep` = current map value and a one-line `reason` — only for re-introduced defects, per the spec's Overrides row. For a mis-anchored span on a key that is currently ABSENT, use `"keep": null` (suppress the write). Validate with `python <TOFF>/aug21_overrides.py` → `OK`. The apply itself is Task 22.

---

## Wave 1 — F1 → 4.1.0

**Preconditions (Day-0 deliverables this wave depends on — do not start until they are on disk and their tests pass):** `anchor_extract.py` (Task 1), `apply_aug21.py` + `aug21-overrides.json` + `run_aug21_gates.ps1` (Tasks 3–7), `aug21_english_delta.py` (Task 0), the notes/ICF layer wired into `F1/generate_qsf.py` (Tasks 8–11).

Nothing under `raw/` is touched; CSPro generator/map edits stay in Carl's working tree; only evidence PNGs/README are committed.

Common Windows notes for every task below: run Python as `python` from a PowerShell prompt with `$env:PYTHONIOENCODING='utf-8'`; all paths `C:/...`; set `$root='C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development'` once per prompt and derive every evidence path from it; map files are read with `newline=''` and written with the newline detected by `apply_safe.load_map` (never let `write_text` convert to CRLF). Never put `2>&1` on a native exe in PowerShell 5.1 (it wraps stderr in ErrorRecords and flips `$?`). Never use bash heredocs inside a PowerShell block — commit messages go through a file. `EVDATE` = the real F1 deploy date (Task 19); every evidence path below uses `docs/uat-fix-evidence/<EVDATE>-aug21-translations/F1/` — never leave a literal `2026-08-2x` in a path.

---

### Task 16: F1 Q75 English alignment (label + emphasis regex)

**Files:**
- Modify: `deliverables/CSPro/F1/generate_dcf.py:873-874`
- Modify: `deliverables/CSPro/F1/generate_qsf.py:150-158` (comment block :140-152 + `_CAPITATION_RE` :153-158)
- Test: `deliverables/CSPro/aug17-tools/test_aug21_f1.py` (new)

**Interfaces:**
- Consumes: `cspro_helpers.yes_no_dk(name, label)` (cspro_helpers.py:259); `generate_dcf.build_dictionary()` (F1/generate_dcf.py:1516); `generate_qsf._CAPITATION_RE` (F1/generate_qsf.py:153-158); `aug21_english_delta.py --only F1` (Task 0).
- Produces: `Q75_IS_1700_ENOUGH` dcf label `"75. The maximum per capita rate amount for YAKAP/Konsulta is at Php 1,700 across private and public facilities (40% after first patient encounter, 60% based on registered catchment population by December). Based on your practice, is this enough?"` (252 chars). The translation **key** is the item name (`item:Q75_IS_1700_ENOUGH`, `vs:Q75_IS_1700_ENOUGH_VS1`, `val:Q75_IS_1700_ENOUGH_VS1:<code>`) and survives the reword unchanged; the EN label is only the **anchor** the Task 17 extractor matches in the PDF.

- [ ] **Step 1: Write the failing test**

```python
# deliverables/CSPro/aug17-tools/test_aug21_f1.py
import importlib.util
import sys
from pathlib import Path

CSPRO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CSPRO))
sys.path.insert(0, str(CSPRO / "F1"))

Q75_AUG21 = ("75. The maximum per capita rate amount for YAKAP/Konsulta is at Php 1,700 "
             "across private and public facilities (40% after first patient encounter, "
             "60% based on registered catchment population by December). "
             "Based on your practice, is this enough?")


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _f1_items():
    gen = _load("f1_generate_dcf", CSPRO / "F1" / "generate_dcf.py")
    d = gen.build_dictionary()
    out = {}
    for lvl in d["levels"]:
        for rec in lvl["records"]:
            for it in rec["items"]:
                out[it["name"]] = it
    return out


def test_q75_label_matches_aug21_paper():
    it = _f1_items()["Q75_IS_1700_ENOUGH"]
    assert it["labels"][0]["text"] == Q75_AUG21
    assert len(Q75_AUG21) <= 255          # CSPro label cap (252 chars today)


def test_q75_value_set_codes_unchanged():
    it = _f1_items()["Q75_IS_1700_ENOUGH"]
    codes = [v["pairs"][0]["value"] for v in it["valueSets"][0]["values"]]
    assert codes == ["1", "2", "3"]       # Yes / No / I don't know — yes_no_dk


def test_capitation_regex_still_fires_on_aug21_stem():
    qsf = _load("f1_generate_qsf", CSPRO / "F1" / "generate_qsf.py")
    m = qsf._CAPITATION_RE.match(f"<p>{Q75_AUG21}</p>")
    assert m is not None
    assert m.group(2) == "Php 1,700"
```

- [ ] **Step 2: Run test to verify it fails** — Run: `cd C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSPro/aug17-tools; python -m pytest test_aug21_f1.py -q` Expected: FAIL — `test_q75_label_matches_aug21_paper` (label still reads `rate for YAKAP/Konsulta is Php`) and `test_capitation_regex_still_fires_on_aug21_stem` (`m is None`); `test_q75_value_set_codes_unchanged` PASS.

- [ ] **Step 3: Write minimal implementation**

`deliverables/CSPro/F1/generate_dcf.py:873-874` — replace the label string only:

```python
    items.append(yes_no_dk("Q75_IS_1700_ENOUGH",
                           "75. The maximum per capita rate amount for YAKAP/Konsulta is at Php 1,700 across private and public facilities (40% after first patient encounter, 60% based on registered catchment population by December). Based on your practice, is this enough?"))  # aug21: 'rate amount ... is at Php 1,700' (DOH Aug-21 paper, 252 chars)
```

`deliverables/CSPro/F1/generate_qsf.py:150-152` — update the stale sentence in the comment block so the next reader is not misled (it currently ends `Aug-17 condensed the stem to 236 chars, so the dcf label now carries the full text itself and the emphasis can be derived from it like every other rule here.`):

```python
# locale falling back to English. And it is no longer needed: Aug-17 condensed
# the stem to 236 chars (Aug-21 rewords it to 252 — 'rate amount ... is at Php
# 1,700' — still under the 255 cap), so the dcf label carries the full text
# itself and the emphasis can be derived from it like every other rule here.
```

`deliverables/CSPro/F1/generate_qsf.py:153-158` — widen the prefix group so the emphasis wrapper keeps firing on both the Aug-17 and Aug-21 prefixes:

```python
_CAPITATION_RE = re.compile(
    r"^(<p>\d+\. The maximum per capita rate(?: amount)? for YAKAP/Konsulta is(?: at)? )"
    r"(Php 1,700)"
    r"(.*?)"
    r"(Based on your practice, is this enough\?)"
    r"(</p>)$")
```

- [ ] **Step 4: Run test to verify it passes** — Run: `python -m pytest test_aug21_f1.py -q` Expected: `3 passed`.

- [ ] **Step 5: Verify/gate** — Regenerate and prove the build now equals the Aug-21 paper:

```powershell
$root='C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development'
cd "$root/deliverables/CSPro"
$env:PYTHONIOENCODING='utf-8'
python F1/generate_dcf.py            # prints per-locale '    {CODE}: n/1363 labels translated (x%)' — save as BEFORE
python data/translations-official/aug21_english_delta.py --only F1
```
Expected: the F1 row's `diffs` shrink by one versus the Task 0 baseline (Q75 no longer listed) and the remaining diffs are exactly the artefact rows documented in `aug21-day0.md`. If the delta still prints a Q75 residual, diff the two strings with a small script file (`difflib.ndiff`) — a curly apostrophe or double space in the paper is the usual cause; the paper wins.

- [ ] **Step 6: Record** — paste the BEFORE per-locale lines (F1 FIL67 BCL67 BIS67 CEB63 WAR67 HIL66 ILO62 baseline, 1363 arrays) into the wave note draft `deliverables/CSPro/patch-notes/draft-f1-v4.1.0-aug21-translations.md` under a `## Coverage` heading (renamed to `<EVDATE>-f1-v4.1.0-aug21-translations.md` and completed in Task 20). No git commit — Carl commits generator changes.

---

### Task 17: F1 Aug-21 extraction, merge dry-run, apply, gates

**Files:**
- Create: `deliverables/CSPro/data/translations-official/out-aug21/F1/{fil,bcl,bis,ceb,war,hil,ilo}.json` + `{loc}_flagged.json` + `QA-REPORT.md` (gitignored data output; re-generated here against the Task 16 English — the Task 1 Step 5 run anchored on the pre-alignment label)
- Modify: `deliverables/CSPro/F1/translations/{fil,bcl,bis,ceb,war,hil,ilo}.json` (values only, via `apply_aug21.py --apply`)
- Modify: `deliverables/CSPro/data/translations-official/aug21-overrides.json` (F1 section, only for re-introduced defects)
- Test: `deliverables/CSPro/aug17-tools/test_aug21_f1.py` (extend)

**Interfaces:**
- Consumes: `anchor_extract.py --source DIR --instrument F1 --dcf PATH --out DIR [--live-maps DIR]` (Task 1); `apply_aug21.py --only F1 [--extract DIR] [--seed FINDINGS] [--apply]` (Tasks 5–7; report `aug21_apply_diff.json`); `scan_poisoned_keys.py --apply-report`; `run_aug21_gates.ps1 -Inst F1 -PreBridge N` (Task 7); `cspro_helpers.apply_translations` SystemExit rule (any key without `:` is fatal, cspro_helpers.py:1175-1180).
- Produces: updated F1 maps whose `_meta.sources.aug21 = {date, file, n_written, n_replaced, n_overridden, n_flagged_skipped}` (today `_meta` = format/migrated/keys/source only); `aug21-overrides.json["F1"]` entries `{key: {"keep": ..., "reason": ...}}`.

Note on what the tests can prove: the maps are name-scoped, so `item:Q75_IS_1700_ENOUGH` already exists in every F1 map with its June-5 value (fil: `Ang pinakamataas na halaga ng per capita rate para sa YAKAP/Konsulta ay Php 1,700 …`). Relabelling Q75 in Task 16 neither removes nor changes that key. A test that only checks "key present and not English" passes before any Aug-21 merge and would hide a digit-mismatch flag that silently leaves the old value in place. The tests below therefore compare the map against the **extractor's own output**.

- [ ] **Step 1: Write the failing test** — append to `test_aug21_f1.py`:

```python
import json

F1_TR = CSPRO / "F1" / "translations"
OUT_AUG21 = CSPRO / "data" / "translations-official" / "out-aug21" / "F1"
LOCALES = ["fil", "bcl", "bis", "ceb", "war", "hil", "ilo"]
Q75_KEYS = ["item:Q75_IS_1700_ENOUGH", "vs:Q75_IS_1700_ENOUGH_VS1"]


def _map(loc):
    return json.loads((F1_TR / f"{loc}.json").read_text(encoding="utf-8"))


def _extracted(loc):
    return json.loads((OUT_AUG21 / f"{loc}.json").read_text(encoding="utf-8"))


def _flagged_keys(loc):
    rows = json.loads((OUT_AUG21 / f"{loc}_flagged.json").read_text(encoding="utf-8"))
    return {r["key"] for r in rows}


def test_f1_maps_carry_aug21_provenance():
    for loc in LOCALES:
        m = _map(loc)
        src = m["_meta"].get("sources", {}).get("aug21")
        assert src, f"{loc}: no _meta.sources.aug21 block"
        assert set(src) >= {"date", "file", "n_written", "n_replaced", "n_overridden"}


def test_f1_maps_name_scoped():
    for loc in LOCALES:
        assert all(":" in k for k in _map(loc) if k != "_meta"), f"{loc}: legacy key present"


def test_f1_q75_holds_the_aug21_value_or_is_flagged():
    """Aug-21 wins: for every locale the map value must equal what the Aug-21
    extractor emitted (clean), else the key must sit in the flagged worklist —
    a June-5 value surviving silently is the failure this catches."""
    for loc in LOCALES:
        m, ex, fl = _map(loc), _extracted(loc), _flagged_keys(loc)
        for k in Q75_KEYS:
            if k in ex:
                assert m.get(k) == ex[k], f"{loc} {k}: map != Aug-21 extract"
            else:
                assert k in fl, f"{loc} {k}: neither extracted clean nor flagged"
```

- [ ] **Step 2: Run test to verify it fails** — Run: `python -m pytest test_aug21_f1.py -q -k "provenance or name_scoped or aug21_value"` Expected: `test_f1_maps_carry_aug21_provenance` FAIL (`_meta` has no `sources.aug21`); `test_f1_q75_holds_the_aug21_value_or_is_flagged` FAIL (the extract on disk still anchors on the pre-Task-16 Q75 label, or the maps hold the June-5 value); `test_f1_maps_name_scoped` PASS (maps were migrated 2026-08-14).

- [ ] **Step 3: Write minimal implementation** — re-extract against the aligned English, then dry-run + seed:

```powershell
$root='C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development'
cd "$root/deliverables/CSPro"
$env:PYTHONIOENCODING='utf-8'
python data/translations-official/anchor_extract.py `
  --source "$root/raw/Survey-Instruments-2026-08-21/Translations" `
  --instrument F1 `
  --dcf "$root/deliverables/CSPro/F1/FacilityHeadSurvey.dcf" `
  --out data/translations-official/out-aug21/F1 `
  --live-maps F1/translations
python data/translations-official/scan_poisoned_keys.py --apply-report data/translations-official/aug21_pre_findings.json   # Task 6 step 5.1 (regenerates the .dcf; record N_pre)
python aug17-tools/bridge_check.py --check | Select-String "B-admin-leak|C-glued-fragments|^Total"                          # note the B/C row count -> $preBC
python data/translations-official/apply_aug21.py --only F1 --unmatched --seed data/translations-official/aug21_pre_findings.json   # --unmatched = the spec's risk mitigation: unmatched anchors per locale BEFORE any write
```
Read `data/translations-official/out-aug21/F1/QA-REPORT.md` (and the `unmatched` column / `aug21_apply_diff.json[F1][loc].unmatched` — an unmatched anchor is an extract key with no map key of that name, i.e. an extractor/dcf drift, never a translation gap; > 0 on any locale = STOP and reconcile before `--apply`) and `aug21_apply_diff.json`. Review rule (Decision 2): every `replaced` row is accepted **unless** its new value is one of the known June-5 defect classes — the `--seed` output lists candidate rows automatically from `aug21_pre_findings.json` + `recovery_exclusions.json`; also check each replaced key by hand against `FINDINGS.md` §3/§4 (F1 rows: BCL Q115 `3-3 na bulan`, BCL Q120 `31-60 na bulan`, BIS Q33 `Matag onom ka bulan`, ILO Q63 `1-2 a bulan`, CEB Q140, BIS Q121, Q43 BCL/FIL). Those references are by question number, not name-scoped key: resolve `Qnn` → `val:Q<nn>_<STEM>_VS1:<code>` by grepping the built dcf for `"Q<nn>_` (or read the `--seed` JSON line, which already carries the resolved key). For each re-introduced defect add an override (`keep` = the verbatim current map value from `aug21_apply_diff.json[F1][loc].replaced[].was`):

```json
{
  "F1": {
    "val:Q115_TIMELINESS_VS1:2": {
      "keep": "1-3 na bulan",
      "reason": "Aug-21 BCL PDF still prints '3-3 na bulan' (June-5 range defect, FINDINGS.md §3); Aug-14 repair kept"
    }
  }
}
```
Then validate, re-dry-run (override column == rows pasted, no `WARN override 'keep' != current`) and apply:

```powershell
python data/translations-official/aug21_overrides.py
python data/translations-official/apply_aug21.py --only F1
python data/translations-official/apply_aug21.py --only F1 --apply
```

- [ ] **Step 4: Run test to verify it passes** — Run: `python -m pytest test_aug21_f1.py -q` Expected: `6 passed`. If `test_f1_q75_holds_the_aug21_value_or_is_flagged` fails on a locale, open `out-aug21/F1/<loc>_flagged.json` and find the Q75 key — the flag names the cause (`digit-mismatch` on `1,700`/`40%`/`60%` is a false positive when the PDF prints `1700`; accept by hand-copying the flagged `tr` into the map only if the digits are the same numbers, and record it in the wave note `## Merge`). If the key is in neither file the extractor never anchored Q75 in that PDF — check the PDF wording against `Q75_AUG21` with `python -c` + fitz (single-quoted PowerShell string, double quotes inside Python).

- [ ] **Step 5: Verify/gate**

```powershell
.\data\translations-official\run_aug21_gates.ps1 -Inst F1 -PreBridge $preBC
```
Expected: `== F1 gates: scan total=... (no reason grew)  bridge total=... (A-mismatch ignored), B/C=k vs pre k (ok)` then `GATES CLEAN - proceed to generate_dcf.py`, exit 0 (Task 7 Step 5 triage rules apply to any `GREW`: WRONG_Q_CLEARED / GLUED_CLEARED checked against the Aug-21 PDF and accepted if right; DOUBLED / SELF_ECHO / IS_OTHER_EN / EN_FRAGMENT → override + re-apply; any DOUBLED/SELF_ECHO row can also be auto-repaired with `python data/translations-official/remediate_scan.py data/translations-official/aug21_post_findings.json` → review → `--write`, then re-run the gates). Both gates must be clean before Task 18.

- [ ] **Step 6: Record** — In the wave note draft add `## Merge` with the dry-run counts per locale (written / replaced / already_same / overridden / flagged / **unmatched**) and one bullet per override with its reason, plus any hand-accepted digit-mismatch rows, the scan per-reason pre/post table and the bridge B/C pre → post. Keep `out-aug21/F1/*_flagged.json` — it is the translator worklist for ASPSI (exported in Task 45). No git commit.

---

### Task 18: F1 rebuild, coverage capture, static gates, version stamp, Designer compile

**Files:**
- Modify: `deliverables/CSPro/F1/FacilityHeadSurvey.dcf`, `.qsf`, `.apc`, `.fmf` (regenerated)
- Modify: `deliverables/CSPro/versions.json:18` (F1 4.0.0 → 4.1.0 via `stamp_version.py`)
- Test: `deliverables/CSPro/automation/verify_questions.py` (existing gate), `deliverables/CSPro/aug17-tools/test_aug21_f1.py`

**Interfaces:**
- Consumes: `python F1/generate_dcf.py` (prints `    {CODE}: {matched}/{total} labels translated ({pct}%)`, cspro_helpers.py:1234-1239); `py automation/verify_questions.py F1` (exit 0 + `[F1] ... PASS`); `py automation/stamp_version.py bump F1 --minor --type changed --notes "..."` (hand-parsed sys.argv, not argparse); `py automation/cspro_compile_driver.py F1 --build --save` (shot `automation/shots/F1_compile.png`); the per-language ICF OVERRIDES from Task 11 render in this rebuild.
- Produces: `versions.json["F1"] == {"version": "4.1.0", "channel": "dev"}`; pff Description `Facility Head Survey v4.1.0 (<EVDATE>) [DEV]`; compiled `F1/FacilityHeadSurvey.ent`.

- [ ] **Step 1: Write the failing test** — append to `test_aug21_f1.py`:

```python
def test_versions_json_f1_is_4_1_0():
    v = json.loads((CSPRO / "versions.json").read_text(encoding="utf-8"))
    assert v["F1"]["version"] == "4.1.0"
    assert v["F1"]["channel"] == "dev"


def test_built_dcf_carries_aug21_q75_values():
    """The regenerated dcf must carry the SAME values the maps now hold (i.e. the
    Aug-21 extract), not merely 'something non-English'."""
    d = json.loads((CSPRO / "F1" / "FacilityHeadSurvey.dcf").read_text(encoding="utf-8"))
    it = next(i for l in d["levels"] for r in l["records"] for i in r["items"]
              if i["name"] == "Q75_IS_1700_ENOUGH")
    by_lang = {l["language"]: l["text"] for l in it["labels"]}
    assert by_lang["EN"] == Q75_AUG21
    for loc in LOCALES:
        expected = _map(loc).get("item:Q75_IS_1700_ENOUGH", Q75_AUG21)
        assert by_lang[loc.upper()] == expected, f"{loc}: dcf label != map value"
```

- [ ] **Step 2: Run test to verify it fails** — Run: `python -m pytest test_aug21_f1.py -q -k "versions or built_dcf"` Expected: FAIL — version is `4.0.0`; dcf not yet regenerated after the merge (labels still hold June-5 values).

- [ ] **Step 3: Write minimal implementation**

```powershell
$root='C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development'
cd "$root/deliverables/CSPro"
$env:PYTHONIOENCODING='utf-8'
cmd /c "set PYTHONIOENCODING=utf-8&& python F1\generate_dcf.py > data\translations-official\out-aug21\F1\coverage-after.txt 2>&1"
Get-Content -Encoding utf8 data\translations-official\out-aug21\F1\coverage-after.txt
python F1/generate_apc.py
python F1/generate_fmf.py
python F1/generate_qsf.py
py automation/stamp_version.py bump F1 --minor --type changed --notes "Aug-21 translations imported for all 7 languages; Q75 stem aligned to the Aug-21 paper; consent screens and section intros per language"
```
(The `cmd /c … > file 2>&1` form is used instead of `Tee-Object` because PS 5.1 `Tee-Object` writes UTF-16 and mojibakes the em-dashes.) Expected on the generate_dcf run: seven `    {CODE}: n/1363 labels translated (x%)` lines, each ≥ the Task 16 BEFORE value (F1 baseline FIL67 BCL67 BIS67 CEB63 WAR67 HIL66 ILO62). Coverage counts key presence, so it can only drop if an override deleted a key. `stamp_version.py` prints the 4.0.0 → 4.1.0 bump, restamps the pff Description, regenerates the qsf footer, RELEASE-NOTES.md and WHATS-NEW and publishes whats-new to the portal.

- [ ] **Step 4: Run test to verify it passes** — Run: `python -m pytest test_aug21_f1.py -q` Expected: `8 passed`.

- [ ] **Step 5: Verify/gate**

```powershell
py automation/verify_questions.py F1
py automation/stamp_version.py show
Stop-Process -Name CSPro -Force -ErrorAction SilentlyContinue    # driver attaches to the OPEN Designer — start fresh
py automation/cspro_compile_driver.py F1 --build --save
```
Expected: `[F1] N items · N coded · reachable N/N · dead-conditions 0 · bad-skips 0 · PASS` and `=== per-question verification: F1 PASS`; `show` exits 0 (no pff/qsf drift); the driver prints `COMPILE-SHOT ...\automation\shots\F1_compile.png` — open the PNG with the Read tool and confirm the Compiler Output tab reads `Compile Successful`. Also run the Task 11 Step 5 qsf probe once more (ICF FIL body differs from EN, `Kamusta` present) — the stamp regenerated the qsf.

- [ ] **Step 6: Record** — Copy `coverage-after.txt` lines into the wave note `## Coverage` (AFTER column beside BEFORE). Note the compile shot path. No git commit.

---

### Task 19: F1 publish, auto-deploy, byte-verify served package

**Files:**
- Create: `deliverables/CSPro/aug17-tools/byte_verify_aug21.py`
- Create: `docs/uat-fix-evidence/<EVDATE>-aug21-translations/F1/byte-verify.txt`
- Create: `docs/uat-fix-evidence/<EVDATE>-aug21-translations/F1/00-deploy-result.png` (one chosen shot from `automation/shots/deploy/`)
- Test: `deliverables/CSPro/aug17-tools/test_aug21_f1.py` (extend)

**Interfaces:**
- Consumes: `py automation/csweb_deploy_designer.py open | filemenu | click X Y [name]` (vision-guided publish; `open` launches on `DEPLOY_KEY` env, default F1, and kills any running Designer first); `py automation/auto_deploy.py F1 --deploy` (requires the Designer 'Deploy to CSWeb' dialog open; `CSPRO_ADMIN_USER` + `CSPRO_ADMIN_PASS_FILE` env; several shots per run → `automation/shots/deploy/`); served package `root@207.148.65.115:/opt/app/lamp/www/csweb/files/apps/FacilityHeadSurvey.zip` (bz2 .pen inside; probe via `bytes.find(term.encode("utf-16-le"))`).
- Produces: `pen_bytes_from_zip(zip_path) -> bytes`, `probe(blob, term) -> bool`, `sample_probes(maps_dir, keys)` in `byte_verify_aug21.py`; CLI `py byte_verify_aug21.py <INST> <zip> <maps_dir> <out.txt> [--version vX.Y.Z] [--deploy-shot SRC.png DST.png]` with `PROBE_KEYS` for F1, F4 and F3 — the ONE byte-verify tool reused by Tasks 32 and 41 (exit 1 on any MISS).

- [ ] **Step 1: Write the failing test**

```python
# append to test_aug21_f1.py
from byte_verify_aug21 import pen_bytes_from_zip, probe


def test_probe_finds_utf16le_terms():
    blob = "xx".encode("utf-16-le") + "Ano ang iyong pangalan".encode("utf-16-le") + b"\x00\x00"
    assert probe(blob, "Ano ang iyong pangalan") is True
    assert probe(blob, "Batay sa inyong praktis") is False
    # odd-offset case: whole-blob decode would misalign, bytes.find must not
    assert probe(b"\x00" + blob, "Ano ang iyong pangalan") is True
```

- [ ] **Step 2: Run test to verify it fails** — Run: `python -m pytest test_aug21_f1.py -q -k probe` Expected: FAIL — `ModuleNotFoundError: byte_verify_aug21`.

- [ ] **Step 3: Write minimal implementation**

```python
# deliverables/CSPro/aug17-tools/byte_verify_aug21.py
"""Byte-verify a CSWeb-served package against the translation maps (2026-08-14 method:
bz2-decompress the .pen, search each probe as UTF-16LE bytes with bytes.find — whole-blob
decode gives false negatives at odd offsets).
Usage: py byte_verify_aug21.py <INST> <App.zip> <INST/translations> <out.txt>
                                [--version vX.Y.Z] [--deploy-shot SRC.png DST.png]
Used by every wave (F1 Task 19, F4 Task 32, F3 Task 42). Exit 1 on any MISS.
"""
import bz2
import json
import shutil
import sys
import zipfile
from pathlib import Path

PROBE_KEYS = {
    "F1": ["item:Q75_IS_1700_ENOUGH", "val:Q75_IS_1700_ENOUGH_VS1:3", "item:Q1_NAME"],
    "F4": ["item:Q30_NAME", "item:Q35_HAS_DISABILITY", "item:Q36_SPECIFY_DISABILITY",
           "item:Q40_EDUCATION", "item:Q67_TRAVEL_HH"],
    "F3": ["item:Q47_PHYSICIAN_CHECKUP", "item:Q972_SOURCES", "val:Q972_SOURCES_VS1:90",
           "item:Q1142_HAS_OTHER", "item:Q66_SAME_AS_USUAL"],
}


def pen_bytes_from_zip(zip_path):
    with zipfile.ZipFile(zip_path) as z:
        pen = next(n for n in z.namelist() if n.lower().endswith(".pen"))
        raw = z.read(pen)
    try:
        return bz2.decompress(raw)
    except OSError:
        return raw


def probe(blob, term):
    return blob.find(term.encode("utf-16-le")) >= 0


def sample_probes(maps_dir, keys):
    out = []
    for loc in ("fil", "bcl", "bis", "ceb", "war", "hil", "ilo"):
        m = json.loads((Path(maps_dir) / f"{loc}.json").read_text(encoding="utf-8"))
        for k in keys:
            if k in m:
                out.append((f"{loc.upper()} {k}", m[k][:60]))
            else:
                out.append((f"{loc.upper()} {k} (no map value - English fallback)", None))
    return out


def main(argv):
    inst, zip_path, maps_dir, out = argv[:4]
    rest = argv[4:]
    version = rest[rest.index("--version") + 1] if "--version" in rest else None
    if "--deploy-shot" in rest:
        i = rest.index("--deploy-shot")
        shutil.copyfile(rest[i + 1], rest[i + 2])
    blob = pen_bytes_from_zip(zip_path)
    lines = [f"--- {inst} byte-verify {zip_path} ---", f"pen bytes: {len(blob)}"]
    ok_all = True
    probes = sample_probes(maps_dir, PROBE_KEYS[inst])
    if version:
        probes.append(("footer version (non-truncation signal)", version))
    for label, term in probes:
        if term is None:
            lines.append(f"SKIP {label}")
            continue
        ok = probe(blob, term)
        ok_all &= ok
        lines.append(f"{'OK  ' if ok else 'MISS'} {label}: {term!r}")
    lines.append("RESULT: " + ("ALL PASS" if ok_all else "FAIL"))
    Path(out).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(lines))
    sys.exit(0 if ok_all else 1)


if __name__ == "__main__":
    main(sys.argv[1:])
```

Publish + deploy (fresh Designer, F1):

```powershell
$root='C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development'
cd "$root/deliverables/CSPro"
Stop-Process -Name CSPro -Force -ErrorAction SilentlyContinue
$env:DEPLOY_KEY='F1'
py automation/csweb_deploy_designer.py open        # launches Designer on F1, baseline shot
py automation/csweb_deploy_designer.py filemenu    # Alt+F, read the shot, find 'Deploy to CSWeb...'
py automation/csweb_deploy_designer.py click <X> <Y> deploy-menu   # coords read from the filemenu shot
$env:CSPRO_ADMIN_USER='admin'; $env:CSPRO_ADMIN_PASS_FILE='C:/Users/analy/.secrets/csweb_admin.txt'
py automation/auto_deploy.py F1 --deploy
```
Expected: `auto_deploy.py` exits 0, shots in `automation/shots/deploy/` show the CSWeb result dialog for `FacilityHeadSurvey` (package-name-locked); a NEW CSDeploy pid is the publish gate. **Fix `EVDATE` now** (`$EVDATE = Get-Date -Format yyyy-MM-dd`) and use it in every F1 evidence path. Then pick the single result-dialog shot by name and byte-verify the served artefact:

```powershell
$EVDATE = Get-Date -Format yyyy-MM-dd
Get-ChildItem automation/shots/deploy | Sort-Object LastWriteTime | Select-Object Name, LastWriteTime   # pick the F1 result-dialog PNG
$shot = "automation/shots/deploy/<the-one-F1-result-file>.png"
$ev = "$root/docs/uat-fix-evidence/$EVDATE-aug21-translations/F1"
New-Item -ItemType Directory -Force $ev | Out-Null
scp root@207.148.65.115:/opt/app/lamp/www/csweb/files/apps/FacilityHeadSurvey.zip C:/Users/analy/tmp/FacilityHeadSurvey-4.1.0.zip
py aug17-tools/byte_verify_aug21.py F1 C:/Users/analy/tmp/FacilityHeadSurvey-4.1.0.zip F1/translations "$ev/byte-verify.txt" --version v4.1.0 --deploy-shot $shot "$ev/00-deploy-result.png"
```
(Keep `$EVDATE` identical across F1/F2 if both deploy the same day; F4 and F3 fix their own `EVDATE` on their deploy days — the folder name is per wave, the subfolder is per instrument.)

- [ ] **Step 4: Run test to verify it passes** — Run: `python -m pytest test_aug21_f1.py -q` Expected: `9 passed`; byte-verify prints `RESULT: ALL PASS` including the `OK   footer version ... 'v4.1.0'` line (qsf footer near the end of the pack = non-truncation signal).

- [ ] **Step 5: Verify/gate** — Open `$ev/00-deploy-result.png` with Read and confirm the dialog reports success with the `v4.1.0` Description. A `MISS` on any Q75 probe means the served .pen predates the publish — re-run the publish, never patch the zip. `Test-Path "$root/docs/uat-fix-evidence/2026-08-2x-aug21-translations"` must be `False` (no placeholder folder).

- [ ] **Step 6: Record** — Wave note `## Deploy`: served zip size, `RESULT: ALL PASS`, deploy timestamp. Evidence files are the loop's sanctioned commit: `git add docs/uat-fix-evidence/$EVDATE-aug21-translations/F1; git commit -m "evidence: F1 v4.1.0 Aug-21 translations deploy + byte-verify"` (nothing else staged).

---

### Task 20: F1 emulator locale shots + patch note

**Files:**
- Create: `docs/uat-fix-evidence/<EVDATE>-aug21-translations/F1/01-app-list-v4.1.0.png`, `02-q75-fil.png`, `03-q75-ilo.png`, `04-q75-options-fil.png`, `05-icf-fil.png`, `README.md`
- Create: `deliverables/CSPro/patch-notes/<EVDATE>-f1-v4.1.0-aug21-translations.md` (rename the Task 16 draft `draft-f1-v4.1.0-aug21-translations.md` on save)
- Test: manual visual check (Read each PNG)

**Interfaces:**
- Consumes: `deliverables/training/capture-csentry-screenshots.ps1 -Shot <name> -OutDir <abs dir> | -Kill` (emulator-5554, `gov.census.cspro.csentry`; `-OutDir` defaults to `$PSScriptRoot\csentry-screenshots`, so pass an absolute path); sideload path `/storage/emulated/0/Android/data/gov.census.cspro.csentry/files/csentry/FacilityHeadSurvey/`; the 8 PSGC lookup files (`psgc_*.dat`, `.dat.csidx`, `.dcf`) are NOT in the CSWeb zip — `auto_deploy.py` adds them separately on publish, so copy them on-device from an existing app folder (reference_csentry_pen_sideload); cold-boot perms fix `adb root; adb shell chown -R u0_a192:ext_data_rw /data/media/0/...; adb shell chmod -R 770 ...`; CSEntry in-app language menu (hand-switched — no adb command exists for it); patch-note template `.claude/skills/cspro-patch-fix/SKILL.md:160-165`.
- Produces: README.md file-table pattern reused by F2/F4/F3 evidence folders.

- [ ] **Step 1: Write the failing test** — the "test" is the README's file table listing five PNGs that do not exist yet; create it first at `$ev/README.md`:

```markdown
# Aug-21 translations — F1 v4.1.0 render evidence (<EVDATE>)

**Driver:** ASPSI revised Deliverable 2 (Aug-21), 7 translated F1 questionnaires. **Ships as:** F1 v4.1.0 (DEV channel).
**Method:** deployed package pulled from CSWeb (`files/apps/FacilityHeadSurvey.zip`), sideloaded to the `capi_tablet` AVD with the PSGC lookups copied on-device, language switched in CSEntry's language menu, `adb shell screencap`.

| file | what it shows |
|---|---|
| `00-deploy-result.png` | CSWeb deploy dialog, v4.1.0 |
| `01-app-list-v4.1.0.png` | CSEntry app list showing `Facility Head Survey v4.1.0 (date) [DEV]` |
| `02-q75-fil.png` | Q75 (reworded stem) in Filipino |
| `03-q75-ilo.png` | Q75 in Ilocano |
| `04-q75-options-fil.png` | Q75 Yes / No / I don't know options in Filipino |
| `05-icf-fil.png` | ICF screen 1 in Filipino (Aug-21 consent paragraphs + 08/21/2026 stamp) |
| `byte-verify.txt` | served .pen probed for map values (UTF-16LE) + v4.1.0 footer |
```

- [ ] **Step 2: Run test to verify it fails** — Run: `Get-ChildItem $ev` Expected: only `00-deploy-result.png`, `byte-verify.txt`, `README.md` — five PNGs missing.

- [ ] **Step 3: Write minimal implementation**

```powershell
$root='C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development'
$ev = "$root/docs/uat-fix-evidence/$EVDATE-aug21-translations/F1"
cd $root
Expand-Archive C:/Users/analy/tmp/FacilityHeadSurvey-4.1.0.zip C:/Users/analy/tmp/fhs-4.1.0 -Force
& "$env:LOCALAPPDATA\Android\Sdk\emulator\emulator.exe" -avd capi_tablet -no-snapshot -gpu host   # separate window
adb wait-for-device; adb root
$base = "/storage/emulated/0/Android/data/gov.census.cspro.csentry/files/csentry"
$dst = "$base/FacilityHeadSurvey"
adb shell mkdir -p $dst
Get-ChildItem C:/Users/analy/tmp/fhs-4.1.0 -Recurse -Include *.pen,*.pff | ForEach-Object { adb push $_.FullName "$dst/" }
# PSGC lookups are not in the zip: copy them on-device from any already-installed F1/F3/F4 folder
adb shell "ls $base"                                        # find a folder that has psgc_* (e.g. HouseholdSurvey)
adb shell "cp $base/HouseholdSurvey/psgc_* $dst/"
adb shell chown -R u0_a192:ext_data_rw /data/media/0/Android/data/gov.census.cspro.csentry/files/csentry/FacilityHeadSurvey
adb shell chmod -R 770 /data/media/0/Android/data/gov.census.cspro.csentry/files/csentry/FacilityHeadSurvey
adb shell monkey -p gov.census.cspro.csentry -c android.intent.category.LAUNCHER 1
.\deliverables\training\capture-csentry-screenshots.ps1 -Shot 01-app-list-v4.1.0 -OutDir $ev
# open Facility Head Survey, start a case, ⋮ → Language → Filipino; the first screen is ICF part 1
.\deliverables\training\capture-csentry-screenshots.ps1 -Shot 05-icf-fil -OutDir $ev
# navigate to Q75
.\deliverables\training\capture-csentry-screenshots.ps1 -Shot 02-q75-fil -OutDir $ev
.\deliverables\training\capture-csentry-screenshots.ps1 -Shot 04-q75-options-fil -OutDir $ev   # with the value list open
# ⋮ → Language → Ilocano
.\deliverables\training\capture-csentry-screenshots.ps1 -Shot 03-q75-ilo -OutDir $ev
.\deliverables\training\capture-csentry-screenshots.ps1 -Kill
```
If no installed folder has `psgc_*`, pull the 8 files from `deliverables/CSPro/F1/` (gitignored but on disk) and `adb push` them the same way. If the app sits on "loading" forever, the PSGC copy failed (FACILITY_LOOKUP startup loop). If a screencap is black: `adb shell input keyevent 224` then `adb shell service call SurfaceFlinger 1008 i32 1` and retry.

Patch note `deliverables/CSPro/patch-notes/<EVDATE>-f1-v4.1.0-aug21-translations.md` (Carl's loop posts it to `#f1-uat`):

```markdown
🔧 **Facility Head Survey (F1) — patch deployed (v4.1.0)**
*Changed:* All seven language versions now carry ASPSI's revised Aug-21 translations (Tagalog, Bikol, Bisaya, Cebuano, Waray, Hiligaynon, Ilocano). Q75 (YAKAP/Konsulta per-capita rate) wording now matches the Aug-21 paper questionnaire. The consent screens and the section intros now read in the selected language (Aug-21 cleared translations); paragraphs without a cleared translation stay English. No question codes or data layout changed.
*To get it:* In CSEntry, **remove Facility Head Survey, then Add Application → from CSWeb**. You're on the new build when the app list shows **v4.1.0 (<EVDATE>)**. (⋮ → Update Installed Applications is unreliable.)
Cases already in progress are unaffected.
*Still English on some screens?* That item had no translation in ASPSI's cleared Aug-21 source for that language — it is not a build defect; the list of those items has been sent back to ASPSI's translators.

## Coverage (labels translated, of 1363)
| | FIL | BCL | BIS | CEB | WAR | HIL | ILO |
|---|---|---|---|---|---|---|---|
| before (4.0.0) | 67% | 67% | 67% | 63% | 67% | 66% | 62% |
| after (4.1.0) | … | … | … | … | … | … | … |

## Merge
(dry-run counts + overrides + hand-accepted flagged rows from Task 17)

## Deploy
(byte-verify RESULT + timestamp from Task 19)
```

- [ ] **Step 4: Run test to verify it passes** — Open each of the five PNGs with the Read tool: `01` shows `v4.1.0`; `02`/`03` show the Q75 stem in a non-English language containing `1,700`; `04` shows three translated options; `05` shows the Filipino consent paragraph (`Kamusta`) and `08/21/2026`. Any English Q75 in a locale that had a map value → re-check `byte-verify.txt` for that locale before suspecting the map.

- [ ] **Step 5: Verify/gate** — Fill the `after` row from `coverage-after.txt`; confirm every cell ≥ its `before` cell (a drop means an override deleted a key — inspect `aug21_apply_diff.json`). `Select-String "<EVDATE>|2026-08-2x|…" deliverables/CSPro/patch-notes/*-f1-v4.1.0-aug21-translations.md` returns nothing, and `Test-Path deliverables/CSPro/patch-notes/draft-f1-*` is `False` (no placeholders left).

- [ ] **Step 6: Record** — `git add docs/uat-fix-evidence/$EVDATE-aug21-translations/F1; git commit -m "evidence: F1 v4.1.0 Aug-21 locale shots (Q75 FIL/ILO + options + ICF)"`. The patch-note file and generator/map edits stay uncommitted for Carl. Append a dated entry to `log.md` (`### <EVDATE> - Aug-21 translations wave 1: F1 v4.1.0`) with coverage before/after and override count.

---

## Wave 2 — F2 PWA → m4

**Preconditions:** Tasks 12–15 (english-strings collector + dump, `anchor_extract_f2.py`, `apply-paper-translations.py`) on disk with green tests; `spec/english-strings.json` dumped; Task 14 Step 5 extract in `out-aug21/F2/`; Task 10 (`extract_icf.py`, imported by Task 21's consent extractor) green. Wave order: Task 21 (consent screen) → Task 22 (survey maps) → Task 23 (stamp, gates, commit, deploy). Wave 2 is independent of Wave 1 and can run in parallel with it. Shell for every block: PowerShell 5.1 in `APP` = `<root>/deliverables/F2/PWA/app` unless stated.

---

### Task 21: F2 consent screen from the Aug-21 PDFs (chrome `consent.*` per locale)

Why this task exists: the spec's Scope In includes "consent text from the same PDFs" and its Scope Out excludes only "F2 chrome strings *beyond* the consent screen". The F2 consent screen does NOT live in `spec/F2-Spec.md`: it is app chrome in `src/i18n/locales/{loc}.ts` under `consent.*` (`fil.ts:150-155` still says "English until the ASPSI translation pass delivers dialect wording"; `#1313` left `infoStudy`/`infoBenefits` English on 2026-08-25). The english-strings dump (Task 13), `anchor_extract_f2.py` (Task 14) and `apply-paper-translations.py` (Task 15) never see it, so without this task `f2_consent_fil.png` (Task 23) shows an English consent screen. Verified 2026-08-25 against the seven Aug-21 F2 PDFs (Tagalog, Bicolano, Ilocano read): every paper prints each English Part-I paragraph **verbatim** (`requests your participation` at ~950 chars in) immediately followed by its translation, then the next English paragraph — the same "English anchor, translation span" layout `extract_icf.py` (Task 10) already handles for F1/F3/F4. `en.ts` carries two capi-adaptation tails the paper lacks (`infoStudy` "Your progress is saved automatically…", `infoRights` "…before submitting the form"), which `extract_icf.locate()` resolves as `prefix` hits. Headings, buttons, `intro`, the raffle block and `contactsBody` (a table printed cell-by-cell) have no paper counterpart and stay English chrome by the spec's own Scope Out.

**Files:**
- Create: `deliverables/CSPro/data/translations-official/extract_icf_f2.py`
- Create: `deliverables/CSPro/data/translations-official/test_extract_icf_f2.py`
- Create (generated, committed): `deliverables/F2/PWA/app/src/i18n/locales/consent.aug21.ts`
- Modify: `deliverables/F2/PWA/app/src/i18n/locales/{fil,ceb,bis,ilo,hil,war,bcl}.ts` (one `import` + one spread line each)
- Create: `deliverables/F2/PWA/app/src/i18n/consent.aug21.test.ts`
- Modify: `deliverables/F2/PWA/app/e2e/locale-shots.spec.ts:1` (`expect` import) and `:61-67` (consent assertion)
- Modify: `deliverables/CSPro/data/translations-official/aug21-overrides.json` (`"F2"` locale-nested section, only for a mis-anchored paragraph)
- Test: `test_extract_icf_f2.py` (pytest), `src/i18n/consent.aug21.test.ts` (vitest), `e2e/locale-shots.spec.ts` (Playwright)

**Interfaces:**
- Consumes: `extract_icf.locate(low, en, min_words=8)`, `extract_icf.reads_english(cand, en)`, `extract_icf.finish(raw)`, `extract_icf.STOP` (Task 10); `extract_notes.norm`, `extract_notes.pdf_lines`, `extract_notes.PAPER_LANG`, `extract_notes.load_overrides` (Task 8); `src/i18n/locales/en.ts` `consent.*` (read as text — no TS toolchain on the CSPro side); `EnBundle` (`en.ts:249`, `Translatable<typeof en>` — a locale may differ from English per leaf, keys must match exactly); the F2 override shape of `aug21-overrides.json` (`{F2: {loc: {<English paragraph>: {keep: text|null, reason}}}}`, Task 3).
- Produces: `CONSENT_PARAGRAPH_KEYS = ["infoStudy", "infoPrivacy", "infoBenefits", "infoRights", "contactsHeading"]`; `en_consent(en_ts_path) -> OrderedDict[key, text]`; `extract_consent(lines, anchors) -> (trans: {key: text}, report: {key: "exact"|"prefix"|"suffix"|"missing"|"dropped-short"|"dropped-english"})`; `build_consent(source_dir, anchors, overrides) -> ({loc: {key: text}}, {loc: report})`; `render_ts(by_loc) -> str`; CLI `python extract_icf_f2.py --source DIR --en PATH [--out PATH] [--report PATH] [--overrides PATH]`; the generated `consentAug21: Record<'fil'|'ceb'|'bis'|'ilo'|'hil'|'war'|'bcl', ConsentAug21Patch>` spread LAST into each locale's `consent` block (paper wins over the English placeholders; absent keys fall back to English by construction).

- [ ] **Step 1: Write the failing tests** — pytest first:

```python
# deliverables/CSPro/data/translations-official/test_extract_icf_f2.py
import io, os, sys, textwrap
import fitz
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import extract_icf_f2 as m  # noqa: E402

EN_STUDY = ("The Asian Social Project Services, Inc. (ASPSI) requests your participation in a study on "
            "Universal Health Care (UHC). This study aims to generate evidence on the overall experience of "
            "the healthcare service providers and the general public. The Department of Health funded this "
            "study. Your progress is saved automatically on this device — you can pause and continue at any "
            "time before submitting.")
EN_RIGHTS = ("You are free to decline participation or to stop at any time before submitting the form. "
             "Choosing not to participate will not result in any penalty, and you will not have to pay "
             "anything to take part in this study.")
EN_CONTACT = "If you have concerns or questions about your rights as a participant, you can contact:"
# the paper prints the English WITHOUT the two capi-adaptation tails, then the translation
PAPER_STUDY = EN_STUDY.split(" Your progress")[0]
PAPER_RIGHTS = EN_RIGHTS.replace(" before submitting the form", "")
FIL_STUDY = ("Hinihiling ng Asian Social Project Services, Inc. (ASPSI) ang iyong paglahok sa isang pag-aaral "
             "tungkol sa Universal Health Care (UHC). Layunin ng pag-aaral na ito na makakuha ng impormasyon "
             "tungkol sa karanasan ng mga tagapagbigay ng serbisyong pangkalusugan at ng publiko. Ang pag-aaral "
             "na ito ay pinondohan ng Kagawaran ng Kalusugan.")
FIL_RIGHTS = ("Malaya kang tumanggi sa paglahok o huminto anumang oras. Ang pagpili na hindi sumali ay hindi "
              "magreresulta sa anumang parusa, at hindi ka kailangang magbayad para makibahagi sa pag-aaral na ito.")
FIL_CONTACT = ("Kung mayroon kang mga isyu o tanong tungkol sa iyong mga karapatan bilang kalahok, maaari kang "
               "makipag-ugnayan sa:")
ANCHORS = {"infoStudy": EN_STUDY, "infoRights": EN_RIGHTS, "contactsHeading": EN_CONTACT}


def make_pdf(path, paras):
    """One paragraph per PDF line group, wrapped so nothing falls outside the page rect."""
    doc = fitz.open()
    page = doc.new_page()
    y = 50
    for para in paras:
        for ln in textwrap.wrap(para, 95) or [""]:
            if y > 780:
                page = doc.new_page()
                y = 50
            page.insert_text((36, y), ln, fontsize=7)
            y += 10
    doc.save(str(path))
    doc.close()


def test_en_consent_reads_the_five_paragraphs_from_en_ts(tmp_path):
    ts = tmp_path / "en.ts"
    ts.write_text(
        "export const en = {\n  chrome: { x: 'a' },\n  consent: {\n    heading: 'H',\n"
        "    infoStudy:\n      'It\\'s a study. Line two.',\n    infoPrivacy: \"We are committed.\",\n"
        "    infoBenefits: 'B',\n    infoRights: 'R',\n    contactsHeading:\n      'C:',\n  },\n} as const;\n",
        encoding="utf-8")
    en = m.en_consent(str(ts))
    assert list(en) == m.CONSENT_PARAGRAPH_KEYS
    assert en["infoStudy"] == "It's a study. Line two." and en["infoPrivacy"] == "We are committed."


def test_extract_consent_prefix_anchors_and_contact_table_stop(tmp_path):
    pdf = tmp_path / "F2-Tagalog_x_Aug21.pdf"
    make_pdf(pdf, [PAPER_STUDY, FIL_STUDY, PAPER_RIGHTS, FIL_RIGHTS, EN_CONTACT, FIL_CONTACT,
                   "Office Email Contact No.", "Single Joint Research Ethics Board (SJREB) sjreb@doh.gov.ph"])
    tr, rep = m.extract_consent(m.pdf_lines(str(pdf)), ANCHORS)
    assert rep == {"infoStudy": "prefix", "infoRights": "prefix", "contactsHeading": "exact"}
    assert tr["infoStudy"].startswith("Hinihiling") and tr["infoStudy"].endswith("Kalusugan.")
    assert "Universal Health Care (UHC)" in tr["infoStudy"]          # program names kept, not dropped-english
    assert m.norm(tr["infoRights"]) == m.norm(FIL_RIGHTS)
    assert tr["contactsHeading"].endswith("sa:") and "Office" not in tr["contactsHeading"]


def test_extract_consent_drops_english_echo_and_reports_missing(tmp_path):
    pdf = tmp_path / "F2-Bicolano_x_Aug21.pdf"
    make_pdf(pdf, [PAPER_STUDY, PAPER_STUDY, EN_CONTACT])             # echoed English, no rights paragraph
    tr, rep = m.extract_consent(m.pdf_lines(str(pdf)), ANCHORS)
    assert rep["infoStudy"] == "dropped-english" and rep["infoRights"] == "missing"
    assert "infoStudy" not in tr


def test_build_consent_applies_f2_overrides_and_render_ts(tmp_path):
    src = tmp_path / "Translations"
    src.mkdir()
    make_pdf(src / "F2-Tagalog_x_Aug21.pdf", [PAPER_RIGHTS, FIL_RIGHTS, EN_CONTACT, FIL_CONTACT, "Office Email Contact No."])
    make_pdf(src / "F2-Waray_x_Aug21.pdf", [PAPER_RIGHTS, PAPER_RIGHTS, EN_CONTACT])
    ov = {"F2": {"fil": {EN_CONTACT: {"keep": None, "reason": "test: never write"}},
                 "war": {EN_RIGHTS: {"keep": "Pinned WAR", "reason": "test: pin"}}}}
    by_loc, rep = m.build_consent(str(src), {"infoRights": EN_RIGHTS, "contactsHeading": EN_CONTACT}, ov)
    assert m.norm(by_loc["fil"]["infoRights"]) == m.norm(FIL_RIGHTS) and "contactsHeading" not in by_loc["fil"]
    assert rep["fil"]["contactsHeading"] == "override"
    assert by_loc["war"] == {"infoRights": "Pinned WAR"} and rep["war"]["infoRights"] == "override"
    assert by_loc["ceb"] == {}                                          # no PDF -> empty patch -> English fallback
    ts = m.render_ts(by_loc)
    assert "export const consentAug21: Record<'fil' | 'ceb' | 'bis' | 'ilo' | 'hil' | 'war' | 'bcl', ConsentAug21Patch> = {" in ts
    assert "  war: {\n    infoRights: 'Pinned WAR',\n  }," in ts and "  ceb: {\n  }," in ts
    assert m.ts_str("it's \"x\"\nnext") == "'it\\'s \"x\"\\nnext'"
```

vitest (new file, `src/` side — picked up by `vitest run` and by `tsc -b --force` through `tsconfig.app.json`):

```ts
// deliverables/F2/PWA/app/src/i18n/consent.aug21.test.ts
import { describe, expect, it } from 'vitest';
import { en } from './locales/en';
import { fil } from './locales/fil';
import { ceb } from './locales/ceb';
import { bis } from './locales/bis';
import { ilo } from './locales/ilo';
import { hil } from './locales/hil';
import { war } from './locales/war';
import { bcl } from './locales/bcl';
import { consentAug21 } from './locales/consent.aug21';

const bundles = { fil, ceb, bis, ilo, hil, war, bcl } as const;
type Loc = keyof typeof bundles;
const KEYS = ['infoStudy', 'infoPrivacy', 'infoBenefits', 'infoRights', 'contactsHeading'] as const;

describe('Aug-21 F2 consent screen (chrome consent.*)', () => {
  it('fil infoStudy is the Aug-21 Tagalog paragraph, not English', () => {
    expect(fil.consent.infoStudy).not.toEqual(en.consent.infoStudy);
    expect(fil.consent.infoStudy).not.toMatch(/requests your participation/);
    expect(fil.consent.infoStudy).toMatch(/Universal Health Care \(UHC\)/); // program names kept verbatim
  });

  it.each(Object.keys(bundles) as Loc[])('%s: every generated paragraph is wired last and never echoes the English head', (loc) => {
    for (const k of KEYS) {
      const patch = consentAug21[loc][k];
      if (patch === undefined) continue; // no cleared paragraph -> English fallback by design
      expect(bundles[loc].consent[k]).toEqual(patch);
      expect(patch.slice(0, 60)).not.toEqual(en.consent[k].slice(0, 60));
    }
  });

  it('never exceeds the anchor set (headings, buttons, raffle block stay chrome)', () => {
    for (const loc of Object.keys(bundles) as Loc[]) {
      for (const k of Object.keys(consentAug21[loc])) expect(KEYS as readonly string[]).toContain(k);
    }
  });
});
```

- [ ] **Step 2: Run tests to verify they fail** — Run (from `deliverables/CSPro`): `$env:PYTHONIOENCODING='utf-8'; python -m pytest data/translations-official/test_extract_icf_f2.py -q` Expected: FAIL — `ModuleNotFoundError: No module named 'extract_icf_f2'`. Run (from `APP`): `npx vitest run src/i18n/consent.aug21.test.ts` Expected: FAIL — `Failed to resolve import "./locales/consent.aug21"`.

- [ ] **Step 3: Write minimal implementation**

```python
#!/usr/bin/env python3
"""F2 PWA consent screen (chrome `consent.*`) from the seven Aug-21 F2 translated PDFs.

Anchor set = the English Part-I paragraphs in APP/src/i18n/locales/en.ts `consent`
(infoStudy / infoPrivacy / infoBenefits / infoRights / contactsHeading). Every Aug-21 F2
paper prints each English paragraph verbatim followed by its translation (verified
2026-08-25 on the Tagalog, Bicolano and Ilocano files), so the translation is the span
between one located English paragraph and the next located one — the same
locate / reads_english / finish trio as extract_icf.py (F1/F3/F4 ICF). en.ts carries two
capi-adaptation tails the paper lacks (infoStudy "Your progress is saved…", infoRights
"…before submitting the form") which locate() resolves as `prefix` hits.

Headings, buttons, `intro`, the raffle block and `contactsBody` (a contact TABLE printed
cell-by-cell) have no paper counterpart and stay app chrome — spec Scope Out ("F2 chrome
strings beyond the consent screen").

    python extract_icf_f2.py --source RAW/Translations --en APP/src/i18n/locales/en.ts           # report only
    python extract_icf_f2.py --source ... --en ... --out APP/src/i18n/locales/consent.aug21.ts   # write the TS patch
"""
import argparse
import io
import json
import os
import re
import sys
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from extract_notes import norm, pdf_lines, PAPER_LANG, load_overrides  # noqa: E402
from extract_icf import locate, reads_english, finish, STOP  # noqa: E402

CONSENT_PARAGRAPH_KEYS = ["infoStudy", "infoPrivacy", "infoBenefits", "infoRights", "contactsHeading"]
LOCALES = ["fil", "ceb", "bis", "ilo", "hil", "war", "bcl"]      # F2 order (scripts/lib/apply-translations.ts:7)
F2_NAME = re.compile(r"^F2-([A-Za-z]+)_.*\.pdf$")               # extract_notes.PAPER_NAME covers F1/F3/F4 only
# English phrases the F2 paragraphs keep verbatim in every locale, on top of extract_icf.PROGRAM_NAMES
EXTRA_NAMES = re.compile(r"Implementing Rules and Regulations|UHC Act|YAKAP/?KONSULTA|NBB/ZBB|BUCAS|GAMOT|\bDOH\b|PhP", re.I)
_LIT = r"(?P<q>['\"])(?P<v>(?:\\.|(?!(?P=q)).)*)(?P=q)"


def en_consent(path):
    """{key: text} for CONSENT_PARAGRAPH_KEYS read straight from en.ts (no TS toolchain needed)."""
    src = io.open(path, encoding="utf-8").read()
    blk = src[src.index("  consent: {"):]
    out = OrderedDict()
    for k in CONSENT_PARAGRAPH_KEYS:
        m = re.search(r"^\s*" + k + r":\s*" + _LIT, blk, re.M | re.S)
        if not m:
            raise SystemExit(f"en.ts: consent.{k} not found")
        out[k] = m.group("v").replace("\\'", "'").replace('\\"', '"').replace("\\n", "\n")
    return out


def extract_consent(lines, anchors):
    blob = norm(" ".join(lines))
    low = blob.lower()
    found = [(k, en, locate(low, norm(en))) for k, en in anchors.items()]
    trans, report = OrderedDict(), OrderedDict()
    for n, (k, en, loc) in enumerate(found):
        if loc is None:
            report[k] = "missing"
            continue
        start, end, kind = loc
        nxt = next((l[0] for _, _, l in found[n + 1:] if l is not None and l[0] > end), len(blob))
        cand = blob[end:nxt].lstrip(" .:-)")
        m = STOP.search(cand)
        if m:
            cand = cand[:m.start()]
        cand = finish(cand[:int(len(en) * 2.5) + 40])
        if len(cand) < 20:
            report[k] = "dropped-short"
        elif reads_english(EXTRA_NAMES.sub(" ", cand), en):
            report[k] = "dropped-english"
        else:
            trans[k] = cand
            report[k] = kind
    return trans, report


def build_consent(source_dir, anchors, overrides):
    by_loc = OrderedDict((l, OrderedDict()) for l in LOCALES)
    report = OrderedDict()
    for name in sorted(os.listdir(source_dir)):
        m = F2_NAME.match(name)
        if not m or m.group(1) not in PAPER_LANG:
            continue
        loc = PAPER_LANG[m.group(1)].lower()
        trans, rep = extract_consent(pdf_lines(os.path.join(source_dir, name)), anchors)
        ov = overrides.get("F2", {}).get(loc, {})
        for k, en in anchors.items():
            if en in ov:                                     # F2 override shape: keyed by the English string
                keep = ov[en].get("keep")
                rep[k] = "override"
                if keep:                                     # None = never write; text = pin
                    by_loc[loc][k] = keep
            elif k in trans:
                by_loc[loc][k] = trans[k]
        report[loc] = rep
    return by_loc, report


def ts_str(v):
    """Single-quoted TS literal (eslint-config-prettier: single quotes)."""
    return "'" + v.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n") + "'"


def render_ts(by_loc):
    keys = " | ".join(f"'{k}'" for k in CONSENT_PARAGRAPH_KEYS)
    locs = " | ".join(f"'{l}'" for l in LOCALES)
    lines = [
        "// GENERATED by deliverables/CSPro/data/translations-official/extract_icf_f2.py from the Aug-21 F2",
        "// translated PDFs (raw/Survey-Instruments-2026-08-21/Translations). Do not edit — re-run the extractor.",
        "// Each locale bundle spreads its patch LAST into `consent`, so an absent key falls back to English.",
        "import type { EnBundle } from './en';",
        "",
        f"export type ConsentAug21Patch = Partial<Pick<EnBundle['consent'], {keys}>>;",
        "",
        f"export const consentAug21: Record<{locs}, ConsentAug21Patch> = {{",
    ]
    for loc in LOCALES:
        lines.append(f"  {loc}: {{")
        for k, v in by_loc.get(loc, {}).items():
            lines.append(f"    {k}: {ts_str(v)},")
        lines.append("  },")
    lines += ["};", ""]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True, help="raw/Survey-Instruments-2026-08-21/Translations")
    ap.add_argument("--en", required=True, help="APP/src/i18n/locales/en.ts")
    ap.add_argument("--out", help="APP/src/i18n/locales/consent.aug21.ts (omit = report only)")
    ap.add_argument("--report", default=os.path.join(HERE, "out-aug21", "F2", "consent-report.json"))
    ap.add_argument("--overrides", default=os.path.join(HERE, "aug21-overrides.json"))
    a = ap.parse_args()
    anchors = en_consent(a.en)
    by_loc, report = build_consent(a.source, anchors, load_overrides(a.overrides))
    for loc in LOCALES:
        rep = report.get(loc, {})
        print(f"[F2 {loc}] " + "  ".join(f"{k}={rep.get(k, 'no-pdf')}" for k in CONSENT_PARAGRAPH_KEYS))
    os.makedirs(os.path.dirname(a.report), exist_ok=True)
    with io.open(a.report, "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"anchors": anchors, "report": report,
                   "written": {l: list(v) for l, v in by_loc.items()}}, fh, ensure_ascii=False, indent=1)
    if a.out:
        with io.open(a.out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(render_ts(by_loc))
        print(f"Wrote {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Dry-run against the real pack, inspect, seed overrides, then write the TS patch:

```powershell
$root='C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development'
$APP="$root/deliverables/F2/PWA/app"
cd "$root/deliverables/CSPro"
$env:PYTHONIOENCODING='utf-8'
python data/translations-official/extract_icf_f2.py --source "$root/raw/Survey-Instruments-2026-08-21/Translations" --en "$APP/src/i18n/locales/en.ts"
python -c "import json;r=json.load(open('data/translations-official/out-aug21/F2/consent-report.json',encoding='utf-8'));[print(l, r['report'][l]) for l in r['report']]"
```
Expected: seven `[F2 <loc>] infoStudy=prefix infoPrivacy=exact infoBenefits=exact infoRights=prefix contactsHeading=exact` lines (`missing` only where a paper prints no consent page; `dropped-english` on a Bicolano-style echoed paragraph is a correct drop — that paragraph stays English). Spot-check the FIL and ILO `infoStudy` candidates against page 1 of the matching PDF (print them with a 3-line fitz script in `C:/Users/analy/tmp/pdfpage.py`, never inline Python in PowerShell); each must end in `.`/`:` and begin with the translation, not with `The Asian Social…`. For a paragraph that reads wrong, add `"F2": {"<loc>": {"<verbatim English paragraph from en.ts>": {"keep": null | "<corrected text>", "reason": "..."}}}` to `aug21-overrides.json` and validate with `python data/translations-official/aug21_overrides.py` → `OK`. Then write and wire:

```powershell
python data/translations-official/extract_icf_f2.py --source "$root/raw/Survey-Instruments-2026-08-21/Translations" --en "$APP/src/i18n/locales/en.ts" --out "$APP/src/i18n/locales/consent.aug21.ts"
cd $APP
@'
import io, os
LOC = "src/i18n/locales"
for loc in ["fil", "ceb", "bis", "ilo", "hil", "war", "bcl"]:
    p = os.path.join(LOC, f"{loc}.ts")
    s = io.open(p, encoding="utf-8", newline="").read()
    if "consentAug21" in s:
        print(loc, "already wired"); continue
    eol = "\r\n" if "\r\n" in s else "\n"
    s = s.replace("import type { EnBundle } from './en';",
                  "import type { EnBundle } from './en';" + eol + "import { consentAug21 } from './consent.aug21';", 1)
    i = s.index("  consent: {")
    j = s.index(eol + "  },", i)                       # end of the consent block (flat keys only)
    s = s[:j] + eol + f"    // Aug-21 consent import (Task 21): the paper's Part-I paragraphs win; absent keys stay English." + eol + f"    ...consentAug21.{loc}," + s[j:]
    io.open(p, "w", encoding="utf-8", newline="").write(s)
    print(loc, "wired")
'@ | python -
git diff --stat src/i18n/locales
```
Expected: `fil wired` … `bcl wired`; the diff shows exactly 3 added lines per locale file (import, comment, spread) and the new `consent.aug21.ts`. Then the e2e assertion — `e2e/locale-shots.spec.ts` line 1 becomes `import { expect, test } from '@playwright/test';` and lines 61-67 become:

```ts
    // The ICF consent gate precedes Section A. Capture it once (fil) and assert the
    // Part-I paragraphs render in Filipino (Aug-21 consent import), then pass it.
    const consentRadio = page.getByRole('radio').first();
    if ((await consentRadio.count()) > 0 && (await page.getByRole('radio').count()) === 2) {
      if (loc === 'fil') {
        await expect(page.getByText(/requests your participation/)).toHaveCount(0);
        await expect(page.getByText(/Layunin ng pag-?\s?aaral na ito/)).toBeVisible();
        await page.screenshot({ path: `${outdir}/f2_consent_${loc}.png`, fullPage: false });
      }
```
(`Layunin ng pag-aaral na ito` is the second sentence of the Aug-21 F2-Tagalog `infoStudy`, verified 2026-08-25; the paper hyphenates `pag- aaral` across a line break, hence the regex.)

- [ ] **Step 4: Run tests to verify they pass** — Run: `cd "$root/deliverables/CSPro"; python -m pytest data/translations-official/test_extract_icf_f2.py -q` Expected: `4 passed`. Run: `cd $APP; npx vitest run src/i18n/consent.aug21.test.ts` Expected: `9 passed` (1 + 7 per-locale + 1). If the per-locale test fails on `bundles[loc].consent[k] toEqual patch`, the spread is not last in that locale file (a later literal key re-overrides it) — move it.

- [ ] **Step 5: Verify/gate**

```powershell
cd $APP
npx tsc -b --force                     # EnBundle typing: an extra/missing consent key is a compile error
npm run lint
npm test                               # full vitest run, 0 failures (locale-context / localized suites still pass)
npx playwright test -c e2e/playwright.config.ts e2e/locale-shots.spec.ts   # consent assertion passes; writes locale-shots/f2_consent_fil.png
```
Open `locale-shots/f2_consent_fil.png` with Read: Part-I paragraphs in Filipino, headings/buttons unchanged (English). Expected `git status --short`: `src/i18n/locales/consent.aug21.ts` (new), seven `src/i18n/locales/{loc}.ts`, `src/i18n/consent.aug21.test.ts` (new), `e2e/locale-shots.spec.ts` — nothing under `spec/` or `src/generated/` (this task does not touch survey content). No commit here — Task 23 commits the F2 tree in one go (its `git add` list includes these files).

- [ ] **Step 6: Record** — in the wave-2 note `deliverables/CSPro/patch-notes/draft-f2-m4-aug21-translations.md` add `## Consent screen`: the per-locale `exact/prefix/missing/dropped/override` table from `consent-report.json`, override keys with reasons, and the tester-visible sentence for the Task 23 patch note: *"The consent screen's Part-I paragraphs now read in the chosen language (Aug-21 cleared consent text); headings and buttons stay as before."* `extract_icf_f2.py` + its test are CSPro-side tooling (Carl commits); `consent-report.json` is gitignored under `out-aug21/`.

---

### Task 22: F2 Aug-21 apply to `spec/translations` (with vitest guard), regenerate, gates, coverage

**Files:**
- Modify: `deliverables/F2/PWA/app/spec/translations/{fil,ceb,bis,ilo,hil,war,bcl}.json` (by the apply script only)
- Modify: `deliverables/F2/PWA/app/src/generated/items.ts` (by `npm run generate` only)
- Modify: `deliverables/CSPro/data/translations-official/aug21-overrides.json` (F2 section)
- Create: `deliverables/F2/PWA/app/scripts/f2-coverage.py`
- Test: `deliverables/F2/PWA/app/scripts/lib/apply-translations.aug21.test.ts` (new); existing `scripts/lib/apply-translations.test.ts`, `scripts/audit-translations.py`

**Interfaces:**
- Consumes: `anchor_extract_f2.py --source DIR --english-strings PATH --out DIR` (Task 14; English-text-keyed `out-aug21/F2/{loc}.json`); `scripts/apply-paper-translations.py [--extract-dir DIR] [--overrides PATH] [--apply] [--report PATH]` (Task 15; joins ONLY on the `applyTranslations()` set; report `out-aug21/F2/apply-report.json`); `loadTranslationMaps(dir?)` (apply-translations.ts:20); `parseSpec(markdown)` (parse-spec.ts:342); `localizeString` (apply-translations.ts:48); `npm run generate` (`scripts/generate.ts:31-46` prints `translations loaded: fil:N, …` — raw key counts); `scripts/audit-translations.py` (exit 0 = no suspects).
- Override contract (F2 section of `aug21-overrides.json`, locale-nested, keyed by the exact English string): `{"keep": null, "reason": ...}` means **never write the key** (an absent key stays absent; an existing key is left untouched — to retire a stale key that is no longer in the English universe, delete it from the map by hand and record it); `{"keep": "<text>", "reason": ...}` pins that text. The apply script never writes an empty string.
- Produces: updated 7 F2 maps; regenerated `items.ts`; the vitest file asserting every map key is a live English string reachable by `applyTranslations()` (no orphan keys), the Section A `Q2` employment stem is translated in `fil` (item id confirmed `Q2` in items.ts:11), and no value echoes its own key; before/after label-object coverage (denominator 707 — baseline fil75 ceb78 bis78 ilo78 hil75 war80 bcl77 %).

- [ ] **Step 1: Write the failing test**

```ts
// deliverables/F2/PWA/app/scripts/lib/apply-translations.aug21.test.ts
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { loadTranslationMaps, TRANSLATION_LOCALES } from './apply-translations';
import { parseSpec } from './parse-spec';

const APP = resolve(__dirname, '../..');
const spec = parseSpec(readFileSync(resolve(APP, 'spec/F2-Spec.md'), 'utf-8'));
const maps = loadTranslationMaps(resolve(APP, 'spec/translations'));

// Exactly the set applyTranslations() localizes (apply-translations.ts:61-80).
// item.preamble / item.inputLabel are LocalizedString but NOT localized — a key
// for them would be dead, so it is an orphan here on purpose.
function englishUniverse(): Set<string> {
  const en = new Set<string>();
  for (const s of spec.sections) {
    en.add(s.title.en);
    if (s.preamble) en.add(s.preamble.en);
    for (const it of s.items) {
      en.add(it.label.en);
      if (it.help) en.add(it.help.en);
      for (const c of it.choices ?? []) en.add(c.label.en);
      for (const sf of it.subFields ?? []) en.add(sf.label.en);
    }
  }
  return en;
}

describe('Aug-21 F2 translation maps', () => {
  const en = englishUniverse();

  it('every map key is a live English string applyTranslations() can reach', () => {
    for (const loc of TRANSLATION_LOCALES) {
      const orphans = Object.keys(maps[loc]).filter((k) => !en.has(k));
      expect(orphans, `${loc} orphan keys`).toEqual([]);
    }
  });

  it('Q2 employment stem is translated in fil after the Aug-21 import', () => {
    const q2 = spec.sections[0].items.find((i) => i.id === 'Q2');
    expect(q2).toBeDefined();
    const t = maps.fil[q2!.label.en];
    expect(t, 'fil Q2 stem').toBeTruthy();
    expect(t).not.toEqual(q2!.label.en);
  });

  it('no value echoes its own English key', () => {
    for (const loc of TRANSLATION_LOCALES) {
      const echoes = Object.entries(maps[loc]).filter(([k, v]) => k === v);
      expect(echoes, `${loc} self-echo`).toEqual([]);
    }
  });
});
```

- [ ] **Step 2: Run test to verify it fails** — Run: `cd C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/F2/PWA/app; npx vitest run scripts/lib/apply-translations.aug21.test.ts` Expected: FAIL on `Q2 employment stem is translated in fil` only (items.ts:11 has ceb/bis/ilo/hil/war/bcl for the Q2 stem but no `fil`); the orphan and self-echo tests pass today (0 self-echoes verified in all 7 maps) and act as guards for the import.

- [ ] **Step 3: Baseline coverage (before), then apply** — the node one-liner and the committed script agree; run both once so the wave note has the number in the same shape the close-out (Task 44) reads:

```
node -e "const s=require('fs').readFileSync('src/generated/items.ts','utf8');const L=['fil','ceb','bis','ilo','hil','war','bcl'];const objs=s.match(/\{ en: '(?:[^'\\\\]|\\\\.)*'[^}]*\}/g);console.log('label objects',objs.length);for(const l of L){const n=objs.filter(o=>new RegExp(', '+l+\": '\").test(o)).length;console.log(l,n,Math.round(100*n/objs.length)+'%')}"
```

Expected: `label objects 707` and the baseline percentages above (fil 75 … bcl 77). Save the output as `before`. Create `scripts/f2-coverage.py` (committed with Task 23) so the label-object coverage is reproducible without PowerShell quoting:

```python
# deliverables/F2/PWA/app/scripts/f2-coverage.py
"""Per-locale count of label objects in src/generated/items.ts that carry a dialect string."""
import io, os, re
APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
s = io.open(os.path.join(APP, "src", "generated", "items.ts"), encoding="utf-8").read()
total = len(re.findall(r"\ben: '", s))
counts = {l: len(re.findall(r"\b" + l + r": '", s)) for l in ["fil", "ceb", "bis", "ilo", "hil", "war", "bcl"]}
print("label objects:", total)
print(" ".join(f"{l}{n}" for l, n in counts.items()))
```

Then extract (already done in Task 14 Step 5 — re-run only if `spec/english-strings.json` changed), dry-run, review, apply:

```powershell
$root='C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development'
$env:PYTHONIOENCODING='utf-8'
python scripts/f2-coverage.py                                   # before
$ov = "$root/deliverables/CSPro/data/translations-official/aug21-overrides.json"
$from = "$root/deliverables/CSPro/data/translations-official/out-aug21/F2"
python scripts/apply-paper-translations.py --extract-dir $from --overrides $ov          # dry run
```
Review `out-aug21/F2/apply-report.json`: per locale `unmatched / override / same-as-en / already / write / replace`. F2-Bicolano (inline EN/BCL lines) is expected to yield fewer pairs — low yield is acceptable, mis-pairs are not: spot-check 10 random `replaced` rows for `bcl` against the PDF page (put a 3-line fitz script in `C:/Users/analy/tmp/pdfpage.py` rather than quoting Python inline in PowerShell). Add any re-introduced June-5 defect to `aug21-overrides.json["F2"][loc]` keyed by the exact English string (Task 15 Step 6 rules), e.g.:

```json
{
  "F2": {
    "fil": {
      "Dashboards": {
        "keep": null,
        "reason": "Q24.2 placeholder label retired in m3 (#1312); Aug-21 PDF still prints the old 3-option list — do not resurrect (key is not in the spec's English universe)"
      }
    }
  }
}
```
Then `python $root/deliverables/CSPro/data/translations-official/aug21_overrides.py` → `OK`, and:

```powershell
python scripts/apply-paper-translations.py --extract-dir $from --overrides $ov --apply
```
Expected: `APPLIED`, same counts as the dry run, `saved = yes` on every changed locale. Then `git diff --stat spec/translations` shows only the seven locale files, and `git diff spec/translations/fil.json | Select-Object -First 40` shows value-only `-`/`+` pairs plus appended keys at the end — **no whole-file churn** (CRLF preserved; if every line shows as changed, `load_map` mis-detected the line ending — stop and fix before continuing).

- [ ] **Step 4: Run test to verify it passes** — Run: `npx vitest run scripts/lib/apply-translations.aug21.test.ts` Expected: `3 passed`. An orphan-key failure means the extractor emitted a key that only exists in items.ts but not in the parse (an `inputLabel`/`item.preamble` string — not localized by `applyTranslations`); add it as a `keep: null` override and re-apply rather than widening the join.

- [ ] **Step 5: Verify/gate** — regenerate, byte-diff, audit:

```powershell
npm run generate                       # prints 'translations loaded: fil:N, ceb:N, ...' (raw key counts, N >= baseline)
git diff --stat                        # ONLY spec/translations/*.json, src/generated/items.ts (+ package.json and the Task 12-15 untracked files)
python scripts/audit-translations.py   # exit 0 = no suspects
python scripts/f2-coverage.py          # after: every locale >= its baseline (Aug-21-wins never removes a key)
```
If `schema.ts` appears in the diff, STOP — translations must not change the schema (option *values* are English and untouched; `value` is separate from `label.en`), so a schema diff means the spec file itself changed. If `audit-translations.py` reports `value is a DIFFERENT English string` or `English prose in a dialect slot` for a key, that key is a mis-anchored span: add it to `aug21-overrides.json` `F2` section (`keep` = previous value if the key existed, `null` if it was newly written; reason = "Aug-21 extract mis-anchored: <flag>"), re-run `--apply`, regenerate, re-audit. A `trailing question number` hit means an English string ends in a digit AND the paper swept a number after it — same override treatment. `ORPHAN key` cannot occur (the join is against the same English set `items.ts` is built from).

- [ ] **Step 6: Record** — in the wave-2 note `deliverables/CSPro/patch-notes/draft-f2-m4-aug21-translations.md`: before/after 7-locale table (`## Coverage`), the apply counts table, override count with reasons, `npm run generate` key counts, the collisions list from the Task 14 QA report. No commit yet (Task 23 commits everything together).

---

### Task 23: F2 spec-version stamp, full gates, evidence, commit + push, deploy, patch note

**Files:**
- Modify: `deliverables/F2/PWA/app/src/lib/draft.ts:41` (`LOCAL_SPEC_VERSION` m3 → m4, comment block above it)
- Create: `deliverables/F2/PWA/app/src/lib/draft.specversion.test.ts` (new file — `draft.test.ts` already imports `LOCAL_SPEC_VERSION` at :7, so a second import there would be a duplicate-identifier error under `tsc -b --force` / eslint)
- Create: `docs/uat-fix-evidence/<EVDATE>-aug21-translations/F2/f2_secA_{en,fil,ceb,bis,ilo,hil,war,bcl}.png`, `f2_consent_fil.png`, `README.md`
- Create: `deliverables/CSPro/patch-notes/<EVDATE>-f2-m4-aug21-translations.md` (the Task 12/22 draft renamed)
- Commit (F2 only): `scripts/lib/english-strings.ts`, `scripts/lib/english-strings.test.ts`, `scripts/lib/__snapshots__/english-strings.test.ts.snap`, `scripts/dump-english-strings.ts`, `scripts/apply-paper-translations.py`, `scripts/test_apply_paper_translations.py`, `scripts/f2-coverage.py`, `scripts/lib/apply-translations.aug21.test.ts`, `package.json`, `spec/english-strings.json`, `spec/translations/*.json`, `src/generated/items.ts`, `src/lib/draft.ts`, `src/lib/draft.specversion.test.ts`, `src/i18n/locales/consent.aug21.ts`, the seven `src/i18n/locales/{loc}.ts`, `src/i18n/consent.aug21.test.ts`, `e2e/locale-shots.spec.ts` (Task 21) + the evidence folder. NOT committed: `anchor_extract_f2.py`, its test, `extract_icf_f2.py`, its test, `aug21-overrides.json`, `deliverables/CSPro/patch-notes/` (CSPro side — Carl commits).
- Test: `src/lib/draft.specversion.test.ts` + `e2e/locale-shots.spec.ts`

**Interfaces:**
- Consumes: `LOCAL_SPEC_VERSION` (draft.ts:41, used at :174 as `spec_version`); `npx tsc -b --force`; `npm test` (vitest run); `npx playwright test -c e2e/playwright.config.ts e2e/locale-shots.spec.ts` (writes `./locale-shots/f2_secA_{loc}.png`, `f2_consent_fil.png`); `deploy-f2-pwa.ps1` at `deliverables/F2/PWA/` (guard 1: `git fetch origin main` then HEAD == origin/main — unpushed commits fail it; guard 2 bundle markers; guard 3 Test-Live; stamps `dist/build-info.json {sha, branch, built_at, admin_bundle, matches_main}`; `$SiteUrl = "https://uhc-hcw.asiansocial.org"` at :46; `-VerifyOnly` re-checks live).
- Produces: `LOCAL_SPEC_VERSION = '2026-08-2x-m4'` (2x = the real apply date); live `https://uhc-hcw.asiansocial.org/build-info.json` sha == pushed HEAD; patch-note file for Carl's Slack loop (#f2-pwa-uat).

- [ ] **Step 1: Write the failing test** — new file (do NOT append to `draft.test.ts`):

```ts
// deliverables/F2/PWA/app/src/lib/draft.specversion.test.ts
import { describe, expect, it } from 'vitest';
import { LOCAL_SPEC_VERSION } from './draft';

describe('LOCAL_SPEC_VERSION (Aug-21 translations)', () => {
  it('is the m4 stamp', () => {
    expect(LOCAL_SPEC_VERSION).toMatch(/^2026-08-\d{2}-m4$/);
  });
});
```

- [ ] **Step 2: Run test to verify it fails** — Run: `npx vitest run src/lib/draft.specversion.test.ts` Expected: FAIL — value is `'2026-08-25-m3'`.

- [ ] **Step 3: Write minimal implementation** — `src/lib/draft.ts:40-41`, insert the comment block directly after the m3 block and change the constant (replace `2x` with the deploy day):

```ts
// m4 (2026-08-2x, ASPSI revised Deliverable 2 Aug-21): the seven dialect maps under
// spec/translations re-imported from the Aug-21 translated questionnaires (Aug-21 wins
// over the June-5/Aug-17 values except the tracked aug21-overrides.json entries) via
// scripts/apply-paper-translations.py — text only, no payload/schema change; option
// values stay English. English source unchanged (Aug-24 English == build), so items.ts
// differs in dialect strings ONLY: no ids, no enums, no schema change. Nothing to
// migrate; the stamp moves so a submission records which translation set the HCW saw.
export const LOCAL_SPEC_VERSION = '2026-08-2x-m4';
```

- [ ] **Step 4: Run test to verify it passes** — Run: `npx vitest run src/lib/draft.specversion.test.ts src/lib/draft.test.ts scripts/lib/apply-translations.aug21.test.ts` Expected: all pass (the existing draft.test.ts suite must still pass with the new stamp).

- [ ] **Step 5: Verify/gate** — full F2 gate set, evidence, then commit, push, deploy.

```powershell
$root='C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development'
cd "$root/deliverables/F2/PWA/app"
npx tsc -b --force                     # must be clean (memory: always --force before push)
npm run lint
npm test                               # vitest run — existing suite + the new tests (english-strings, aug21 maps, specversion), 0 failures
$env:PYTHONIOENCODING='utf-8'; python scripts/audit-translations.py   # exit 0
npx playwright test -c e2e/playwright.config.ts e2e/locale-shots.spec.ts   # 'Captured locales: en, fil, ceb, bis, ilo, hil, war, bcl'
```
Open `locale-shots/f2_secA_fil.png` with Read: the Q2 employment stem and its options must now be Filipino (the 2026-08-17 gap). Open `locale-shots/f2_consent_fil.png` with Read: the Part-I paragraphs must be **Filipino** (Task 21 — `Layunin ng pag-aaral na ito…`), the headings/buttons may stay English; an English `requests your participation` body is a FAIL (the e2e assertion from Task 21 Step 3 should already have caught it). Fix `EVDATE` (`$EVDATE = Get-Date -Format yyyy-MM-dd`; same value as Wave 1 if deployed the same day), copy evidence and write its README (same table shape as Task 20; files `f2_secA_{loc}.png` ×8 + `f2_consent_fil.png`, method line: `e2e/locale-shots.spec.ts`, mock backend, locale via localStorage `f2_locale`):

```powershell
$EVDATE = Get-Date -Format yyyy-MM-dd
$ev = "$root/docs/uat-fix-evidence/$EVDATE-aug21-translations/F2"
New-Item -ItemType Directory -Force $ev | Out-Null
Copy-Item locale-shots/f2_secA_*.png, locale-shots/f2_consent_fil.png $ev
```
Commit + push (the deploy script's guard 1 requires the push to have landed). PowerShell 5.1 has no heredoc, so write the message to a file with a single-quoted here-string (closing `'@` at column 0) and use `git commit -F`:

```powershell
cd $root
New-Item -ItemType Directory -Force C:/Users/analy/tmp | Out-Null
@'
F2 PWA m4: Aug-21 translations imported via apply-paper-translations.py (7 locales) + consent screen per locale; dump-english-strings anchor set

ASPSI's revised Deliverable 2 (2026-08-21) carries seven translated F2 questionnaires.
spec/translations/{fil,ceb,bis,ilo,hil,war,bcl}.json re-imported via the new committed
scripts/apply-paper-translations.py (exact-English join on the applyTranslations() set;
Aug-21 wins over June-5/Aug-17 values except aug21-overrides.json). English source
unchanged (Aug-24 English == build): items.ts differs in dialect strings only, schema.ts
byte-identical. Section A Q2 employment stem/options now render in FIL (the 2026-08-17
render-evidence gap). Anchor universe = spec/english-strings.json (npm run dump:english).
Consent screen (chrome consent.infoStudy/infoPrivacy/infoBenefits/infoRights/contactsHeading)
now per locale from the same PDFs via extract_icf_f2.py -> src/i18n/locales/consent.aug21.ts
(spread last into each locale bundle; absent paragraphs fall back to English).

Coverage (label objects of 707): fil 75->NN, ceb 78->NN, bis 78->NN, ilo 78->NN,
hil 75->NN, war 80->NN, bcl 77->NN. Untranslated remainder = no source in the cleared PDF.

LOCAL_SPEC_VERSION 2026-08-25-m3 -> 2026-08-2x-m4 (text only, no payload change).
e2e/locale-shots.spec.ts PNGs under docs/uat-fix-evidence/<EVDATE>-aug21-translations/F2.

Gates: tsc -b --force clean, eslint clean, vitest NNN/NNN, audit-translations 0 suspects,
production build OK.

Claude-Session: https://claude.ai/code/session_014JxLZREsash8rvKjcvnvQX
'@ | Set-Content -Encoding utf8 C:/Users/analy/tmp/f2-m4-commit.txt
git add deliverables/F2/PWA/app/scripts/lib/english-strings.ts deliverables/F2/PWA/app/scripts/lib/english-strings.test.ts deliverables/F2/PWA/app/scripts/lib/__snapshots__ deliverables/F2/PWA/app/scripts/dump-english-strings.ts deliverables/F2/PWA/app/scripts/apply-paper-translations.py deliverables/F2/PWA/app/scripts/test_apply_paper_translations.py deliverables/F2/PWA/app/scripts/f2-coverage.py deliverables/F2/PWA/app/scripts/lib/apply-translations.aug21.test.ts deliverables/F2/PWA/app/package.json deliverables/F2/PWA/app/spec/english-strings.json deliverables/F2/PWA/app/spec/translations deliverables/F2/PWA/app/src/generated/items.ts deliverables/F2/PWA/app/src/lib/draft.ts deliverables/F2/PWA/app/src/lib/draft.specversion.test.ts deliverables/F2/PWA/app/src/i18n/locales/consent.aug21.ts deliverables/F2/PWA/app/src/i18n/locales/fil.ts deliverables/F2/PWA/app/src/i18n/locales/ceb.ts deliverables/F2/PWA/app/src/i18n/locales/bis.ts deliverables/F2/PWA/app/src/i18n/locales/ilo.ts deliverables/F2/PWA/app/src/i18n/locales/hil.ts deliverables/F2/PWA/app/src/i18n/locales/war.ts deliverables/F2/PWA/app/src/i18n/locales/bcl.ts deliverables/F2/PWA/app/src/i18n/consent.aug21.test.ts deliverables/F2/PWA/app/e2e/locale-shots.spec.ts docs/uat-fix-evidence/$EVDATE-aug21-translations/F2
git commit -F C:/Users/analy/tmp/f2-m4-commit.txt
git push origin main
```
(Fill the `NN` / `NNN` / `2x` / `<EVDATE>` placeholders in the file before committing — from `scripts/f2-coverage.py` and the vitest summary.) Expected: push succeeds; `git rev-parse HEAD` == `git rev-parse origin/main`. (Working-tree CSPro edits stay unstaged — `git status --short` still lists `deliverables/CSPro/...`; that is intended.) Then deploy and verify the live sha:

```powershell
cd "$root/deliverables/F2/PWA"
.\deploy-f2-pwa.ps1                    # guard 1 'checkout matches origin/main', guard 2 bundle markers, guard 3 Test-Live; 'stamped build-info.json (<sha8>)'
$sha = (git rev-parse HEAD).Trim()
(Invoke-WebRequest "https://uhc-hcw.asiansocial.org/build-info.json?cb=$(Get-Random)" -UseBasicParsing).Content
.\deploy-f2-pwa.ps1 -VerifyOnly
```
Expected: `build-info.json` `sha` equals `$sha` and `matches_main: true`; `-VerifyOnly` exits 0. If guard 1 fails with `Checkout is NOT at origin/main`, the push did not land — do NOT use `-Force`; fix the push. Never pass `-Force` here. Then in `APP`: `npm test; npx tsc -b --force` once more on the pushed HEAD → both exit 0; `git status --short deliverables/F2` empty.

- [ ] **Step 6: Record** — Write `deliverables/CSPro/patch-notes/<EVDATE>-f2-m4-aug21-translations.md` (Carl's loop posts to `#f2-pwa-uat`; `Remove-Item deliverables/CSPro/patch-notes/draft-f2-*` once its content is folded in):

```markdown
🔧 **Healthcare Worker Survey (F2 PWA) — update deployed (spec 2026-08-2x-m4)**
*Changed:* All seven language versions (Tagalog, Cebuano, Bisaya, Ilocano, Hiligaynon, Waray, Bicolano) now carry ASPSI's revised Aug-21 translations. Section A Q2 (employment) and the Q5 cadre list now render in the chosen language. The consent screen's Part-I paragraphs (study, privacy, benefits, rights, contacts line) now read in the chosen language too (Aug-21 cleared consent text); headings, buttons and the raffle block stay as before. Coverage per language went from fil 75 / ceb 78 / bis 78 / ilo 78 / hil 75 / war 80 / bcl 77 % to <after values> % of the 707 on-screen labels. English wording, option values and saved answers are unchanged.
*To get it:* Open the app while online and reload once (pull down or F5); the PWA updates itself on the next load. The Settings screen / footer shows spec **2026-08-2x-m4** when you're current. Drafts in progress are kept.
*Still English on a screen?* That text had no translation in ASPSI's cleared Aug-21 source for that language — not a build defect; the list has gone back to ASPSI's translators.
*Evidence:* docs/uat-fix-evidence/<EVDATE>-aug21-translations/F2/ (Section A in all 8 locales + the consent screen in FIL — Filipino Part-I paragraphs).

## Coverage (label objects of 707)
| | fil | ceb | bis | ilo | hil | war | bcl |
|---|---|---|---|---|---|---|---|
| before (m3) | 75 | 78 | 78 | 78 | 75 | 80 | 77 |
| after (m4) | … | … | … | … | … | … | … |

## Deploy
build-info.json sha <sha>, built_at <ts>, matches_main true; -VerifyOnly exit 0.
```
Fill every placeholder; `Select-String "<after|<sha>|<ts>|2026-08-2x|<EVDATE>" <the file>` must return nothing. Prepend a dated entry to `log.md` (`### <EVDATE> - Aug-21 translations wave 2: F2 m4`): anchors N, collisions (count + pairs), apply counts, overrides (count + reasons), before/after coverage, deployed sha, evidence path. Note for the close (Task 47): the F2 store is still flat English-keyed — same-English/different-translation conflicts (51 known from the 08-17 pass, plus any normalized-key collisions the extractor reported) remain inexpressible; the id-scoped re-key stays parked. Wave 2 is complete; Wave 3 (F4) starts from Day-0 tooling, independent of this wave.

---

## Wave 3 — F4 Household Survey → 3.2.0 (Aug-21 English alignment + 7-locale import)

Preconditions (all Day-0 tasks green): `anchor_extract.py` (Task 1) accepts `--source DIR --instrument F4 --dcf PATH --out DIR`, emits name-scoped keys **and strips the `— Hours` / `— Minutes` component suffix from a dcf label before anchoring** (without it `item:Q67_TRAVEL_HH` can never match the paper); `apply_aug21.py` (Tasks 5–7) accepts `--only F4 [--extract DIR] [--apply]` and prints `WARN override 'keep' != current map value` for any override whose `keep` differs from the map's current value (**any such WARN is a STOP** — a pasted placeholder must never become the live translation); `aug21_english_delta.py --only F4` (Task 0) compares the built `HouseholdSurvey.dcf` English against `raw/Survey-Instruments-2026-08-21/English/F4-English_Household Survey Questionnaire_UHC Year 2_Aug21.pdf`; `extract_notes.py` (Task 8) accepts `--source DIR --provenance aug21` with the widened `^(_[A-Z0-9_]+)` const regex — see Task 25 for why the gate constants are nonetheless named without digits; `icf_content` / F4 `generate_qsf.py` per-language OVERRIDES (Tasks 9–11).
Live F4 = `3.1.4` (2026-08-20, channel `dev`). Baseline label coverage (generator print, 1403 label nodes): FIL60 BCL62 BIS61 CEB64 WAR66 HIL50 ILO60. Baseline `notes_lookup.coverage()` (measured 2026-08-25, de-duplicated across instruments): FIL 51 · BCL 45 · CEB 28 · WAR 48 · HIL 45 · ILO 38 · BIS 45 — after Task 8 these rise; the floor test in Task 29 uses the 2026-08-25 values as a non-regression floor.

**Evidence folder date (`EVDATE`)**: fix it on the day Task 31 deploys (e.g. `2026-08-26`) and use `docs/uat-fix-evidence/<EVDATE>-aug21-translations/F4/` verbatim in Tasks 32–34. Never leave the spec's `2026-08-2x` placeholder in a path — PowerShell will happily create a folder literally named `2026-08-2x-…`.

**CSWeb box**: there is no `csweb` alias in `~/.ssh/config` (only contabo/linode/server01/server02). Every ssh/scp below uses `root@207.148.65.115` (the aspsi-csweb-prod box, as in the CSWeb runbooks).

Exact Aug-21 English (extracted from the F4 English PDF with PyMuPDF, 2026-08-25):

| Item | Aug-21 paper text |
|---|---|
| Q30 | `Name (Write the complete name of HH member)` |
| Q35 | `With disability?` |
| Q36 | `Would the patient like to specify the type of disability?` |
| Q40 | `Highest level of education completed` |
| Q67 | `How much time does it take for you to reach the nearest pharmacy from your home? A Pharmacy is an ancillary primary care facility with a FDA LTO where registered medicines can be bought.` |
| Q117/Q118 gate | `[Answer only “yes” in Q112]` (paper prints curly quotes; keep them — `_esc()` does not touch quotes) |
| Q131/Q135 gate | `[Ask only if they went to a DOH-retained hospital]` |

Windows notes for every step below: run Python as `python` from the path shown; set `$env:PYTHONIOENCODING='utf-8'` once per PowerShell session (labels contain `—` and `“”`); all generator files are LF, translation maps are LF with `indent=2` (apply_aug21 preserves that). **PowerShell 5.1 has no `<<'EOF'` heredoc** — every multi-line Python snippet in this wave is a committed script under `deliverables/CSPro/automation/` invoked as `python <script>`.

### Task 24: F4 dcf labels → Aug-21 wording (Q30 / Q35 / Q36 / Q40 / Q67)

**Files:**
- Modify: `deliverables/CSPro/F4/generate_dcf.py:637-638` (Q30_NAME), `:648-652` (Q35/Q36), `:665-667` (Q40), `:1051-1053` (Q67_TRAVEL_HH)
- Test: `deliverables/CSPro/F4/test_aug21_f4.py` (new)

**Interfaces:**
- Consumes: `build_f4_dictionary()` (F4/generate_dcf.py:2196, returns the pre-translation dict); `cspro_helpers.walk_labeled_nodes(dictionary)` (:1126, yields `(key, node)`); helpers `alpha(name, label, length=50)`, `select_one(name, label, options, length=2)`, `numeric(name, label, length=1, ...)` (cspro_helpers.py:225/269/212)
- Produces: `AUG21_F4_LABELS` dict in `test_aug21_f4.py` = `{item_name: expected_EN_label}` reused by Tasks 26 and 31; the five re-labelled items with unchanged NAMES and CODES (`Q30_NAME`, `Q35_HAS_DISABILITY`, `Q36_SPECIFY_DISABILITY`, `Q40_EDUCATION`, `Q67_TRAVEL_HH`; `Q67_TRAVEL_MM` untouched)

- [ ] **Step 1: Write the failing test**

```python
# deliverables/CSPro/F4/test_aug21_f4.py
"""Wave 3 (Aug-21 translations design): F4 English alignment + qsf gate notes.
Run from deliverables/CSPro/F4:  python -m pytest test_aug21_f4.py -q
"""
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))          # generate_dcf / generate_qsf
sys.path.insert(0, str(HERE.parent))   # cspro_helpers / notes_lookup / icf_content

from generate_dcf import build_f4_dictionary          # noqa: E402
from cspro_helpers import walk_labeled_nodes          # noqa: E402

# Aug-21 paper text (F4-English_..._Aug21.pdf), number prefix per the F4 label convention.
AUG21_F4_LABELS = {
    "Q30_NAME": "30. Name (Write the complete name of HH member)",
    "Q35_HAS_DISABILITY": "35. With disability?",
    "Q36_SPECIFY_DISABILITY": "36. Would the patient like to specify the type of disability?",
    "Q40_EDUCATION": "40. Highest level of education completed",
    "Q67_TRAVEL_HH": ("67. How much time does it take for you to reach the nearest pharmacy "
                      "from your home? A Pharmacy is an ancillary primary care facility with "
                      "a FDA LTO where registered medicines can be bought. — Hours"),
    "Q67_TRAVEL_MM": "67. Travel time to nearest pharmacy — Minutes",   # #1073: short 2nd component, unchanged
}


@pytest.fixture(scope="module")
def en_labels():
    d = build_f4_dictionary()
    return {key.split(":", 1)[1]: node["labels"][0]["text"]
            for key, node in walk_labeled_nodes(d) if key.startswith("item:")}


@pytest.mark.parametrize("name,expected", sorted(AUG21_F4_LABELS.items()))
def test_aug21_label_text(en_labels, name, expected):
    assert en_labels[name] == expected


def test_relabelled_items_keep_their_codes(en_labels):
    d = build_f4_dictionary()
    vs = {key: [v["pairs"][0]["value"] for v in node["values"]]
          for key, node in walk_labeled_nodes(d) if key.startswith("vs:")}
    assert vs["vs:Q35_HAS_DISABILITY_VS1"] == ["0", "1"]          # YN_01
    assert vs["vs:Q36_SPECIFY_DISABILITY_VS1"] == ["0", "1"]
    # Q40_EDUCATION codes are 2-char zero-padded (generate_dcf.py:529-532: "01","02","03"...)
    assert vs["vs:Q40_EDUCATION_VS1"][:3] == ["01", "02", "03"]
    assert all(len(lbl) <= 255 for lbl in en_labels.values())   # write_dcf cap
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd deliverables/CSPro/F4; python -m pytest test_aug21_f4.py -q`
Expected: FAIL — 5 parametrized cases (`Q30_NAME`, `Q35_HAS_DISABILITY`, `Q36_SPECIFY_DISABILITY`, `Q40_EDUCATION`, `Q67_TRAVEL_HH`) with `AssertionError` showing the current text (e.g. `'30. Name (LAST NAME, FIRST NAME & MIDDLE NAME, EXT)'`); `Q67_TRAVEL_MM` and `test_relabelled_items_keep_their_codes` PASS (the codes test must pass BEFORE the edit too — it is a guard, not a fail-first).

- [ ] **Step 3: Write minimal implementation**

`deliverables/CSPro/F4/generate_dcf.py:637-638` — replace:

```python
        alpha("Q30_NAME",
              "30. Name (LAST NAME, FIRST NAME & MIDDLE NAME, EXT)", length=120),
```
with
```python
        alpha("Q30_NAME",
              # aug21: F4-English_..._Aug21.pdf, Section C roster column Q30 caption.
              "30. Name (Write the complete name of HH member)", length=120),
```

`:648-652` — replace:

```python
        select_one("Q35_HAS_DISABILITY",
                   "35. Do you identify as a person with a disability?",
                   YN_01, length=1),
        select_one("Q36_SPECIFY_DISABILITY",
                   "36. Would you like to specify the type of disability?",
                   YN_01, length=1),
```
with
```python
        select_one("Q35_HAS_DISABILITY",
                   "35. With disability?",                                   # aug21 wording
                   YN_01, length=1),
        select_one("Q36_SPECIFY_DISABILITY",
                   "36. Would the patient like to specify the type of disability?",   # aug21
                   YN_01, length=1),
```

`:665-667` — replace:

```python
        select_one("Q40_EDUCATION",
                   "40. Highest level of education attended (the highest level the person reached, even if not completed — e.g. someone who reached Grade 2 is Primary)",  # #608: 'attended/reached', not 'completed' (ASPSI go/no-go via Carl 2026-06-21)
                   Q40_EDUCATION, length=2),
```
with
```python
        select_one("Q40_EDUCATION",
                   # aug21: the DOH-submitted paper reads "completed" — this REVERSES #608
                   # ('attended/reached', ASPSI go/no-go via Carl 2026-06-21). The paper
                   # wins; the 3.2.0 patch note says so explicitly.
                   "40. Highest level of education completed",
                   Q40_EDUCATION, length=2),
```

`:1051-1053` — replace:

```python
        numeric("Q67_TRAVEL_HH",
                "67. How much time does it take to reach the nearest pharmacy from your home? — Hours",
                length=2),
```
with
```python
        numeric("Q67_TRAVEL_HH",
                # aug21: full paper stem incl. the pharmacy definition rides on Hours only
                # (#1073 pattern); Minutes keeps its short prompt.
                "67. How much time does it take for you to reach the nearest pharmacy from "
                "your home? A Pharmacy is an ancillary primary care facility with a FDA LTO "
                "where registered medicines can be bought. — Hours",
                length=2),
```

Leave `Q67_TRAVEL_MM` (:1054-1058) untouched.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd deliverables/CSPro/F4; python -m pytest test_aug21_f4.py -q`
Expected: `7 passed`.

- [ ] **Step 5: Verify/gate — regenerate and confirm nothing but the five labels moved**

```powershell
$env:PYTHONIOENCODING='utf-8'
cd deliverables/CSPro/F4
python generate_dcf.py        # prints "    FIL: N/1403 labels translated (..%)" per locale
python generate_apc.py; python generate_fmf.py; python generate_qsf.py
cd ..; python automation/verify_questions.py F4
```
Expected: `[F4] ... dead-conditions 0 · bad-skips 0 · PASS`. Coverage print for each locale equals the baseline (FIL60 BCL62 BIS61 CEB64 WAR66 HIL50 ILO60) — the five re-labelled keys (`item:Q30_NAME`, `item:Q35_HAS_DISABILITY`, `vs:Q35_HAS_DISABILITY_VS1`, …) still hold their June-5 values because `apply_translations` looks up by NAME, not text; those values are now stale-vs-English and will be replaced in Task 28.

- [ ] **Step 6: Record**

Note in the wave log (`deliverables/CSPro/patch-notes/<EVDATE>-f4-v3.2.0-aug21-translations.md` is the patch note written in Task 34; use `log.md` and the F4 evidence README for the running wave log): the 5 label edits (old → new), that names/codes are unchanged, the per-locale coverage line as printed, and that #608 is reversed by the Aug-21 paper. No git step (Carl commits generator changes).

### Task 25: Printed gates on Q117/Q118/Q131/Q135 as qsf help text

**Files:**
- Modify: `deliverables/CSPro/F4/generate_qsf.py:138-144` (header comment), `:290-300` (`INSTRUCTIONS_BY_NAME`), `:479-485` (`note_html`)
- Create: `deliverables/CSPro/automation/aug21_check_gates.py`
- Test: `deliverables/CSPro/F4/test_aug21_f4.py`

**Interfaces:**
- Consumes: `question_extras(nm, intro_used) -> (intro_english, instruction_english)` (generate_qsf.py:448-477; resolution order `INSTRUCTIONS_BY_NAME.get(nm)` first, then `INSTRUCTIONS.get(q)`); `note_html(intro_en, instr_en, lang) -> (pre, post)` (:479-485, renders `<p class="instruction">` via `notes_lookup.translate_note(english, lang)` with English fallback); `_READ_ONE` constant (:145 `"READ OPTIONS OUT LOUD. SELECT ONE ANSWER ONLY."`)
- Produces: module constants `_GATE_ANSWER_ONLY_IF_YES = '[Answer only “yes” in Q112]'` and `_GATE_DOH_RETAINED = '[Ask only if they went to a DOH-retained hospital]'` (**named WITHOUT digits** by convention even though Task 8 widened the scrape regex; the `Q112` stays inside the string); `INSTRUCTIONS_BY_NAME` values may now be a `str` OR a `tuple[str, ...]` — each part is translated INDEPENDENTLY by `note_html` (a concatenated "gate + _READ_ONE" string would be a key `notes.json` never carries and would fall back to English in every locale); four new entries. The two English gate strings are the `notes.json` anchors Task 29 looks up. `automation/aug21_check_gates.py <INST> <ITEM...>` (qsf gate-note counter, reused by Task 29 and the close-out).

- [ ] **Step 1: Write the failing test** (append to `test_aug21_f4.py`)

```python
import generate_qsf as qsf   # noqa: E402  (module-level reads versions.json + cover_logos.png)

GATE_Q112 = "[Answer only “yes” in Q112]"
GATE_DOH = "[Ask only if they went to a DOH-retained hospital]"


def _parts(instr):
    return instr if isinstance(instr, tuple) else (instr,)


@pytest.mark.parametrize("name,gate", [
    ("Q117_SPECIALIST_FOLLOWUP", GATE_Q112),
    ("Q118_SAT_REFERRAL_PROCESS", GATE_Q112),
    ("Q131_NBB_OOP", GATE_DOH),
    ("Q135_ZBB_OOP", GATE_DOH),
])
def test_printed_gate_is_help_text_not_label(en_labels, name, gate):
    intro, instr = qsf.question_extras(name, set())
    assert instr is not None and _parts(instr)[0] == gate
    assert gate not in en_labels[name]                # dcf label = translation key, stays clean


def test_q118_keeps_read_one_as_a_separate_part():
    _, instr = qsf.question_extras("Q118_SAT_REFERRAL_PROCESS", set())
    assert instr == (GATE_Q112, qsf._READ_ONE)        # tuple: each part translated on its own


def test_gate_constants_have_no_digits_in_their_names():
    # convention kept even after extract_notes.py widened its scrape regex (Task 8)
    assert hasattr(qsf, "_GATE_ANSWER_ONLY_IF_YES") and hasattr(qsf, "_GATE_DOH_RETAINED")
    assert qsf._GATE_ANSWER_ONLY_IF_YES == GATE_Q112 and qsf._GATE_DOH_RETAINED == GATE_DOH


def test_gate_renders_as_instruction_paragraph():
    pre, post = qsf.note_html(None, GATE_DOH, "EN")
    assert pre == "" and post == f'<p class="instruction">{GATE_DOH}</p>'


def test_tuple_instruction_renders_one_paragraph_per_part():
    pre, post = qsf.note_html(None, (GATE_Q112, qsf._READ_ONE), "EN")
    assert post == (f'<p class="instruction">{GATE_Q112}</p>'
                    f'<p class="instruction">{qsf._READ_ONE}</p>')
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd deliverables/CSPro/F4; python -m pytest test_aug21_f4.py -q -k "gate or tuple or q118"`
Expected: FAIL — `test_printed_gate_is_help_text_not_label[Q117…]`, `[Q131…]`, `[Q135…]` with `instr is None`; `[Q118…]` fails because `instr == _READ_ONE`; `test_q118_keeps_read_one_as_a_separate_part` FAIL; `test_gate_constants_have_no_digits_in_their_names` FAIL (`AttributeError`); `test_tuple_instruction_renders_one_paragraph_per_part` FAIL (`TypeError` — `translate_note` gets a tuple); `test_gate_renders_as_instruction_paragraph` PASS (mechanism already exists).

- [ ] **Step 3: Write minimal implementation**

`generate_qsf.py:138-144` header comment — replace the sentence
`# fields. Paper-only navigation notes (<proceed to Qx>, skip-to rules) are`
`# omitted — CAPI logic automates the routing. English-only, like consent.`
with
```python
# fields. Paper-only navigation notes (<proceed to Qx>, skip-to rules) are
# omitted — CAPI logic automates the routing — EXCEPT the four Aug-21 printed
# gates on Q117/Q118/Q131/Q135, which ASPSI kept in the question text; they
# ride as name-keyed help notes so the dcf label (the translation key) stays
# clean (#1101/#658 dropped them from the label; aug21 restores them as notes).
```

`generate_qsf.py:290-300` — insert the two constants above `INSTRUCTIONS_BY_NAME` and four entries inside it:

```python
# aug21: printed gates the Aug-21 paper carries inside the stem (curly quotes as printed).
# Constant NAMES carry no digits by convention (data/translations-official/extract_notes.py
# scrapes module constants as const:<NAME> anchors; the Q112 lives inside the string).
_GATE_ANSWER_ONLY_IF_YES = "[Answer only “yes” in Q112]"
_GATE_DOH_RETAINED = "[Ask only if they went to a DOH-retained hospital]"

# Values are a str OR a tuple of str. A tuple renders one <p class="instruction"> per
# part and each part is translated on its own (notes.json keys on the FULL English
# string, so "gate + _READ_ONE" glued together would never find a translation).
INSTRUCTIONS_BY_NAME = {
    # #1202: Q18 renders as the paper's two parts. ...
    "Q18_INCOME_AMOUNT": ("Enumerator note: Ensure that the respondent will provide a valid "
                          "response. In case the respondent fails to provide one, input -98 "
                          "for “I don’t know” and -99 for “Refuse to Answer”."),
    "Q18_INCOME_BRACKET": ("Enumerator note: Select the income category that corresponds to "
                           "the respondent’s approximate household income."),
    # aug21 printed gates (routing is still enforced by the apc: #816 Q117 preproc, Q118
    # gate on Q112=Yes, Q130/Q132 bypasses for Q131/Q135). A name key REPLACES the
    # number-keyed note, so Q118 re-attaches its _READ_ONE as a second tuple part.
    "Q117_SPECIALIST_FOLLOWUP": _GATE_ANSWER_ONLY_IF_YES,
    "Q118_SAT_REFERRAL_PROCESS": (_GATE_ANSWER_ONLY_IF_YES, _READ_ONE),
    "Q131_NBB_OOP": _GATE_DOH_RETAINED,
    "Q135_ZBB_OOP": _GATE_DOH_RETAINED,
}
```
(Beware: the existing Q18 entries are parenthesised implicit string concatenations, NOT tuples — leave them as-is; only a trailing comma inside the parens makes a tuple.)

`generate_qsf.py:479-485` — replace `note_html`:

```python
def note_html(intro_en, instr_en, lang):
    """Render the two notes in ONE language; missing translation keeps English, which is
    what the tablet shows today, so a miss is never a regression.
    instr_en may be a str or a tuple of str (aug21): one instruction paragraph per part,
    each translated independently so notes.json can carry the gate and the READ-ONE
    note as two separate full-string keys."""
    pre = f"<p>{_esc(translate_note(intro_en, lang))}</p>" if intro_en else ""
    parts = instr_en if isinstance(instr_en, tuple) else ((instr_en,) if instr_en else ())
    post = "".join(f'<p class="instruction">{_esc(translate_note(p, lang))}</p>' for p in parts)
    return pre, post
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd deliverables/CSPro/F4; python -m pytest test_aug21_f4.py -q`
Expected: `15 passed`.

- [ ] **Step 5: Verify/gate — regenerate the qsf and count the gate paragraphs with a committed script**

Create `deliverables/CSPro/automation/aug21_check_gates.py` (re-used by Task 29 and the close-out):

```python
"""Count <p class="instruction">[A... gate notes per item across the 8 qsf languages.
Usage:  python automation/aug21_check_gates.py F4 Q117_SPECIALIST_FOLLOWUP Q118_SAT_REFERRAL_PROCESS Q131_NBB_OOP Q135_ZBB_OOP
Exit 1 if any named item shows fewer than 8 gate paragraphs."""
import io, sys
from pathlib import Path

QSF = {"F1": "F1/FacilityHeadSurvey.ent.qsf", "F3": "F3/PatientSurvey.ent.qsf",
       "F4": "F4/HouseholdSurvey.ent.qsf"}

def main(inst, items):
    t = io.open(Path(__file__).resolve().parent.parent / QSF[inst], encoding="utf-8").read()
    bad = 0
    for nm in items:
        blk = t[t.index(f".{nm}\n"):][:6000]
        n = blk.count('<p class="instruction">[A')
        print(f"{nm}: {n} gate notes across 8 languages")
        bad += (n < 8)
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2:]))
```

```powershell
cd deliverables/CSPro/F4; python generate_qsf.py
cd ..; python automation/aug21_check_gates.py F4 Q117_SPECIALIST_FOLLOWUP Q118_SAT_REFERRAL_PROCESS Q131_NBB_OOP Q135_ZBB_OOP
```
Expected: each item prints `8 gate notes across 8 languages`, exit 0 (English fallback in all locales until Task 29 lands the translations). `Wrote ...HouseholdSurvey.ent.qsf (N questions x 8 languages)` with N unchanged from Task 24.

- [ ] **Step 6: Record**

Wave log: gates added as help notes (mechanism `INSTRUCTIONS_BY_NAME` → `question_extras` → `note_html`, tuple support), the convention reversal recorded in the header comment, Q118 keeps `_READ_ONE` as a separate part, constant names digit-free. No git step.

### Task 26: English delta vs the Aug-21 paper (aug21_english_delta F4)

**Files:**
- Create: `deliverables/CSPro/data/translations-official/out-delta/F4_english_delta.json` (gitignored output of Task 0's tool) and a text capture `out-aug21/F4/english-delta.txt`
- Test: `deliverables/CSPro/F4/test_aug21_f4.py` (no new test — the delta tool has its own Day-0 tests)

**Interfaces:**
- Consumes: `python deliverables/CSPro/data/translations-official/aug21_english_delta.py --only F4` (Task 0; reads `F4/HouseholdSurvey.dcf` EN labels + the F4 English Aug-21 PDF; prints the `inst match total diffs paper-only` row plus one `Q<n>: build=… paper=…` pair per diff)
- Produces: the recorded parser-artifact list below, reused verbatim in the Task 34 patch note and the Wave-5 close

- [ ] **Step 1: Run the delta on the regenerated build**

```powershell
$env:PYTHONIOENCODING='utf-8'
cd deliverables/CSPro
New-Item -ItemType Directory -Force data/translations-official/out-aug21/F4 | Out-Null
cmd /c "set PYTHONIOENCODING=utf-8&& python data\translations-official\aug21_english_delta.py --only F4 > data\translations-official\out-aug21\F4\english-delta.txt 2>&1"
Get-Content -Encoding utf8 data\translations-official\out-aug21\F4\english-delta.txt
```
Expected: the 2026-08-25 pre-wave rows for Q30, Q35, Q36, Q40, Q67 no longer appear as diffs; Q117/Q118/Q131/Q135 still show as diffs ONLY by the leading `[Answer only …]` / `[Ask only …]` bracket (gate lives in help text by design; `norm()` strips brackets so they may already match) — record these four as accepted either way.

- [ ] **Step 2: Classify every remaining diff row**

For each remaining row, one of: (a) known parser artifact — roster grid header bleed (`35. 36. 37. 38. HH Roster # Name First Name only …`), the second `67.` hit in Section N (`67. Housing (actual rentals …)` is the consumption-items table, not Q67), `Time (HH:MM)` component suffixes vs `— Hours/— Minutes`; (b) intentional CAPI wording (#1073 short Minutes prompt, `_TXT` specify stubs); (c) a real miss → go back to Task 24 and fix. Expected: zero rows in class (c).

- [ ] **Step 3: Verify/gate**

Run: `python automation/verify_questions.py F4` → `PASS`. Expected `english-delta.txt` present, ≤ 12 non-MATCH rows, all classified.

- [ ] **Step 4: Record**

Paste the classified row list into the wave log under "F4 English delta after alignment"; this list is the "known parser-artifact rows" the patch note refers to.

### Task 27: Extract the 7 F4 locales from the Aug-21 PDFs

**Files:**
- Create: `deliverables/CSPro/data/translations-official/out-aug21/F4/{fil,bcl,bis,ceb,war,hil,ilo}.json`, `…/{loc}_flagged.json`, `…/QA-REPORT.md` (all gitignored)
- Test: `deliverables/CSPro/data/translations-official/test_aug21_f4_extract.py` (new, smoke test on the produced files)

**Interfaces:**
- Consumes: `anchor_extract.py --source DIR --instrument F4 --dcf PATH --out DIR --live-maps DIR` (Task 1; anchors on `walk_labeled_nodes()` (key, EN) pairs of the CURRENT dcf with the `— Hours/— Minutes` suffix stripped; emits name-scoped keys; QA flags `is-other-label`, `starts-mid-english`, `table-bleed`, `echo-english`, `starts-with-english`, `contains-other-label`, `overlong-span`, `length-ratio`, `digit-mismatch`, `empty`, `glued-short-label`, `ends-with-other-label`)
- Produces: `out-aug21/F4/{loc}.json` = `{name-scoped key: translation}` consumed by Task 28; `out-aug21/F4/{loc}_flagged.json` rows for the roster-grid items (Q30/Q35/Q36 are grid column captions on paper and will most likely land here as `table-bleed`/`contains-other-label`, NOT in the clean map)

- [ ] **Step 1: Write the failing smoke test**

```python
# deliverables/CSPro/data/translations-official/test_aug21_f4_extract.py
import json
from pathlib import Path

import pytest

OUT = Path(__file__).resolve().parent / "out-aug21" / "F4"
LOCS = ["fil", "bcl", "bis", "ceb", "war", "hil", "ilo"]
# Hard-asserted: prose stems the paper prints as full sentences.
ALIGNED_PROSE = ["item:Q40_EDUCATION", "item:Q36_SPECIFY_DISABILITY"]
# Reported only: roster GRID captions (Q30/Q35) and the suffix-stripped Q67 — the paper
# prints them as table headers / with "Time (HH:MM)", so they usually land in _flagged.json.
ALIGNED_GRID = ["item:Q30_NAME", "item:Q35_HAS_DISABILITY", "item:Q67_TRAVEL_HH"]


@pytest.mark.parametrize("loc", LOCS)
def test_extract_exists_and_is_name_scoped(loc):
    p = OUT / f"{loc}.json"
    assert p.exists(), f"run anchor_extract.py for F4 first ({p})"
    m = json.loads(p.read_text(encoding="utf-8"))
    m.pop("_meta", None)
    assert m and all(":" in k for k in m), "legacy text-keyed output would SystemExit in apply_translations"
    assert all(isinstance(v, str) and v.strip() for v in m.values())


@pytest.mark.parametrize("loc", ["fil", "ceb"])
def test_aligned_prose_items_recovered(loc):
    m = json.loads((OUT / f"{loc}.json").read_text(encoding="utf-8"))
    missing = [k for k in ALIGNED_PROSE if k not in m]
    assert missing == [], f"{loc}: aligned prose items not recovered from the Aug-21 PDF: {missing}"


@pytest.mark.parametrize("loc", ["fil", "ceb"])
def test_aligned_grid_items_reported(loc, capsys):
    """Never hard-fails: prints where each grid item landed (clean / flagged+flags / absent)
    so the reviewer can hand-accept a flagged span that is a complete sentence."""
    clean = json.loads((OUT / f"{loc}.json").read_text(encoding="utf-8"))
    flagged = {r["key"]: r for r in json.loads((OUT / f"{loc}_flagged.json").read_text(encoding="utf-8"))}
    for k in ALIGNED_GRID:
        where = ("clean" if k in clean else
                 f"flagged {flagged[k]['flags']} -> {flagged[k]['tr'][:80]!r}" if k in flagged else "absent")
        print(f"{loc} {k}: {where}")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd deliverables/CSPro/data/translations-official; python -m pytest test_aug21_f4_extract.py -q`
Expected: FAIL — `AssertionError: run anchor_extract.py for F4 first` for all 7 locales; the prose/grid tests error on the missing files.

- [ ] **Step 3: Run the extractor**

```powershell
$env:PYTHONIOENCODING='utf-8'
cd deliverables/CSPro/data/translations-official
python anchor_extract.py --source "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/Survey-Instruments-2026-08-21/Translations" --instrument F4 --dcf "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSPro/F4/HouseholdSurvey.dcf" --out out-aug21/F4 --live-maps ../../F4/translations
```
Expected: console summary table with one row per locale (`FIL anchored N clean C flagged K differ D`), 7 `{loc}.json` + 7 `{loc}_flagged.json` + `QA-REPORT.md` under `out-aug21/F4/`. Source files matched are `F4-{Bicolano,Bisaya,Cebuano,Hiligaynon,Ilocano,Tagalog,Waray}_Household Survey Questionnaire_UHC Year 2_Aug21.pdf`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest test_aug21_f4_extract.py -q -s`
Expected: `11 passed`; the `-s` output shows where `item:Q30_NAME` / `item:Q35_HAS_DISABILITY` / `item:Q67_TRAVEL_HH` landed per locale. For each `flagged` row: open `QA-REPORT.md`; if the span is a complete translated sentence for THAT question (e.g. Q67 with a `contains-other-label` flag from the `Time (HH:MM)` + Q68 run-on), copy it by hand into `out-aug21/F4/{loc}.json` (and remove the row from `{loc}_flagged.json`, otherwise `apply_aug21.py` skips it as flagged) and note the key in the wave log; otherwise leave it to English fallback (Task 28 tolerates absence).

- [ ] **Step 5: Verify/gate — review QA-REPORT.md**

Read `out-aug21/F4/QA-REPORT.md`. Expected: `is-other-label` count 0 per locale (that class is never imported); `echo-english` rows are the paper's deliberately untranslated cells (memory: ~53 % of empty cells are deliberate) — leave them out of the clean map.

- [ ] **Step 6: Record**

Wave log: per-locale anchored/clean/flagged/differ counts, the flag histogram from the report, and the grid-item landing table (clean / hand-accepted / fallback).

### Task 28: Merge the extract into F4 maps (apply_aug21 dry-run → overrides → apply → gates)

**Files:**
- Modify: `deliverables/CSPro/F4/translations/{fil,bcl,bis,ceb,war,hil,ilo}.json` (values + `_meta.sources.aug21`)
- Modify: `deliverables/CSPro/data/translations-official/aug21-overrides.json` (`"F4"` section, only if the dry-run re-introduces a known defect)
- Test: `deliverables/CSPro/data/translations-official/test_aug21_f4_extract.py`

**Interfaces:**
- Consumes: `apply_aug21.py --only F4 [--extract out-aug21/F4] [--seed FINDINGS] [--apply]` (Tasks 5–7: absent → write; equal → `already_same`; different → replace unless key ∈ `aug21-overrides.json["F4"]` → `override`; **`WARN override 'keep' != current map value` = STOP** — `keep` must be pasted verbatim from the map; writes `_meta.sources.aug21 = {date, file, n_written, n_replaced, n_overridden, n_flagged_skipped}`; report `aug21_apply_diff.json`); `scan_poisoned_keys.py --apply-report`; `run_aug21_gates.ps1 -Inst F4 -PreBridge N` (Task 7)
- Produces: updated F4 maps read by `cspro_helpers.apply_translations(dictionary, translations_dir)` in `F4/generate_dcf.py:2235`

- [ ] **Step 1: Write the failing test** (append to `test_aug21_f4_extract.py`)

```python
F4_MAPS = Path(__file__).resolve().parents[2] / "F4" / "translations"


@pytest.mark.parametrize("loc", LOCS)
def test_f4_map_carries_aug21_provenance(loc):
    m = json.loads((F4_MAPS / f"{loc}.json").read_text(encoding="utf-8"))
    src = m["_meta"].get("sources", {}).get("aug21")
    assert src, f"{loc}: apply_aug21.py --apply has not run for F4"
    assert set(src) >= {"date", "file", "n_written", "n_replaced", "n_overridden"}
    assert src["file"] == f"{loc}.json"


def test_f4_q40_no_longer_carries_the_attended_translation():
    # FIL June-5 value for the #608 wording must have been REPLACED by the Aug-21 cell.
    ext = json.loads((OUT / "fil.json").read_text(encoding="utf-8"))
    if "item:Q40_EDUCATION" not in ext:
        pytest.skip("item:Q40_EDUCATION not in the clean FIL extract - see _flagged.json / wave log")
    m = json.loads((F4_MAPS / "fil.json").read_text(encoding="utf-8"))
    assert m["item:Q40_EDUCATION"] == ext["item:Q40_EDUCATION"]


def test_no_override_keeps_a_placeholder():
    p = Path(__file__).resolve().parent / "aug21-overrides.json"
    if not p.exists():
        pytest.skip("no overrides file yet")
    ov = json.loads(p.read_text(encoding="utf-8")).get("F4", {})
    for key, ent in ov.items():
        assert not ent["keep"].startswith("<"), f"{key}: 'keep' is a placeholder, paste the real map value"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest test_aug21_f4_extract.py -q -k "provenance or q40 or placeholder"`
Expected: FAIL — `KeyError: 'sources'` / `AssertionError: fil: apply_aug21.py --apply has not run for F4`; q40 test fails (or skips if the key was never recovered — then record that); placeholder test passes (F4 block empty) or skips.

- [ ] **Step 3: Dry-run, seed overrides, apply**

```powershell
$env:PYTHONIOENCODING='utf-8'
cd deliverables/CSPro
python data/translations-official/scan_poisoned_keys.py --apply-report data/translations-official/aug21_pre_findings.json   # Task 6 step 5.1 (regenerates the .dcf; record N_pre)
python aug17-tools/bridge_check.py --check | Select-String "B-admin-leak|C-glued-fragments|^Total"                          # B/C row count -> $preBC
python data/translations-official/apply_aug21.py --only F4 --unmatched --seed data/translations-official/aug21_pre_findings.json   # dry-run + candidate override rows + unmatched anchors per locale (spec risk mitigation; > 0 = STOP, reconcile before --apply)
```
Review the `replaced` rows per locale (`aug21_apply_diff.json[F4]`) against the FINDINGS.md §3/§4 F4 entries (`HIL F4 Q25 Ginabahinan namon sa komunidad`, `WAR F4 Q9 NO option carries the YES text`, `BIS F4 Q6 Diborsyado`, `CEB F4 Q195 fragment`, `CEB F4 Q78`) and `recovery_exclusions.json` ids `F4|…` (the `--seed` output lists the resolved candidates). For each one the Aug-21 extract re-introduces, add an override. `keep` MUST be the verbatim current map value — copy it out of the map file (e.g. `Select-String '"val:Q9_PWD_CARD_VS1:2"' F4/translations/war.json`) or from `replaced[].was`, never type a paraphrase or a placeholder. Real-key example (WAR, key confirmed in `war.json:75`):

```json
{
  "F4": {
    "val:Q9_PWD_CARD_VS1:2": {
      "keep": "Dire (waray kard ha oras han interbyu)",
      "reason": "Aug-21 WAR PDF still prints the YES text on the NO option (FINDINGS.md §3, 2026-08-14)"
    }
  }
}
```
Then:
```powershell
python data/translations-official/aug21_overrides.py                          # OK
python data/translations-official/apply_aug21.py --only F4                    # re-run dry-run: rows now count as override; NO 'WARN override' line
python data/translations-official/apply_aug21.py --only F4 --apply
```
Expected: `F4  locale written replaced override same flagged unmatched` table (one row per locale) then `APPLIED - diff written to ...`; every override maps to a reason.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd data/translations-official; python -m pytest test_aug21_f4_extract.py -q`
Expected: `20 passed` (or `19 passed, 1 skipped` when Q40 was not recovered clean — record which).

- [ ] **Step 5: Verify/gate — post-merge gates + regenerate**

```powershell
cd deliverables/CSPro
.\data\translations-official\run_aug21_gates.ps1 -Inst F4 -PreBridge $preBC
cd F4; python generate_dcf.py
```
Expected: `GATES CLEAN - proceed to generate_dcf.py`, exit 0 (Task 7 Step 5 triage rules for any `GREW`; DOUBLED/SELF_ECHO rows may be auto-repaired with `remediate_scan.py … --write`, then re-run the gates); `generate_dcf.py` per-locale print rises above the baseline (target ≥ +10 points per locale; HIL from 50 %). Record the seven lines verbatim.

- [ ] **Step 6: Record**

Wave log: dry-run counts (incl. the per-locale `unmatched` count — expected 0), override keys + reasons, scan pre/post + bridge B/C, coverage before/after table (FIL60→?, BCL62→?, BIS61→?, CEB64→?, WAR66→?, HIL50→?, ILO60→?). No git step.

### Task 29: Notes layer — gate strings + F4 intros/instructions from the Aug-21 PDFs

**Files:**
- Modify: `deliverables/CSPro/data/translations-official/notes.json` (`F4` block values, `aug21` provenance)
- Test: `deliverables/CSPro/F4/test_aug21_f4.py`

**Interfaces:**
- Consumes: `extract_notes.py --source DIR --provenance aug21 --json notes.json` (Task 8; PDF → `text-aug21/` via PyMuPDF; anchors = English strings scraped from `F4/generate_qsf.py` `(SECTION_)INTROS` and `_UPPER_CONST` strings — `find_translation` locates the ENGLISH note in the translated PDF's text and takes what follows, so it only works where the PDF is bilingual-inline; Aug-21-wins keyed on the full English string); `notes_lookup.translate_note(english, lang)` (:63-71), `notes_lookup.coverage()` (:74-80); `icf_content.coverage()` (Task 9)
- Produces: `notes.json["F4"]["translations"]` entries (`const:_GATE_ANSWER_ONLY_IF_YES`, `const:_GATE_DOH_RETAINED`, intros) the qsf renders through `note_html`

- [ ] **Step 0: Classify each Aug-21 F4 PDF as bilingual-inline or monolingual (source limit, not extractor bug)**

```powershell
$env:PYTHONIOENCODING='utf-8'
cd deliverables/CSPro/data/translations-official
python -c "import fitz,glob; [print(p.split('F4-')[1].split('_')[0], 'gate-EN' if '[Ask only if they went' in ''.join(pg.get_text() for pg in fitz.open(p)) else 'NO English gate text') for p in sorted(glob.glob(r'C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/Survey-Instruments-2026-08-21/Translations/F4-*.pdf'))]"
```
Expected: one line per language. `NO English gate text` = the PDF prints the gate only in the dialect (or is monolingual like June-5 Waray F4) → `extract_notes` cannot anchor there; record those locales as source-limited in the wave log BEFORE running the extractor.

- [ ] **Step 1: Write the failing test** (append to `test_aug21_f4.py`)

```python
from notes_lookup import translate_note, coverage   # noqa: E402

# Pre-wave floor measured 2026-08-25 (coverage() de-duplicates notes across instruments,
# so it is NOT F1 13 + F3 24 + F4 23). Non-regression floor, not a target.
NOTES_FLOOR = {"FIL": 51, "BCL": 45, "CEB": 28, "WAR": 48, "HIL": 45, "ILO": 38, "BIS": 45}


@pytest.mark.parametrize("const", ["_GATE_DOH_RETAINED", "_GATE_ANSWER_ONLY_IF_YES"])
def test_gate_note_translates_in_at_least_fil(const):
    # Both are digit-free module constants -> extract_notes emits const:<NAME> anchors.
    en = getattr(qsf, const)
    assert translate_note(en, "FIL") != en


def test_notes_coverage_did_not_regress():
    cov = coverage()
    for lg, floor in NOTES_FLOOR.items():
        assert cov.get(lg, 0) >= floor, f"{lg}: {cov.get(lg)} < pre-wave floor {floor}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd deliverables/CSPro/F4; python -m pytest test_aug21_f4.py -q -k "note"`
Expected: both `test_gate_note_translates_in_at_least_fil` cases FAIL (English fallback returned — the gate constants did not exist when Task 8 ran); `test_notes_coverage_did_not_regress` PASS (floor ≤ the Task 8 AFTER values).

- [ ] **Step 3: Re-extract notes with the Aug-21 source**

```powershell
$env:PYTHONIOENCODING='utf-8'
cd deliverables/CSPro/data/translations-official
python extract_notes.py --source "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/Survey-Instruments-2026-08-21/Translations" --provenance aug21 --json notes.json
```
Expected: console coverage per instrument; `notes.json["F4"]["translations"]` gains `const:_GATE_ANSWER_ONLY_IF_YES` and `const:_GATE_DOH_RETAINED` entries for the locales Step 0 classified as bilingual (spot-check `F4-Tagalog…Aug21.pdf` for `[` near Q117). Values must not start with `information ` debris — if any do, that is the `polish()` gap already noted for June-5; add a `note:const:_GATE_…:<LOC>` override with the corrected `keep` (never hand-edit `notes.json`, the next `--json` run would overwrite it) and re-run.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd deliverables/CSPro/F4; python -m pytest test_aug21_f4.py -q`
Expected: `18 passed`. If Step 0 showed the Tagalog PDF prints a gate only in English (no dialect text follows the anchor), mark that parametrized case `xfail(reason="Aug-21 FIL PDF prints the gate in English")` and record it.

- [ ] **Step 5: Verify/gate**

`cd deliverables/CSPro/F4; python generate_qsf.py` then `cd ..; python automation/aug21_check_gates.py F4 Q117_SPECIALIST_FOLLOWUP Q118_SAT_REFERRAL_PROCESS Q131_NBB_OOP Q135_ZBB_OOP` — still 8 per item (the `[A` prefix counts only the English fallbacks; translated gates begin with the dialect bracket — if the count drops below 8 for an item that IS translated, the check counts English only: that is expected, read the per-language bodies instead). Then for BOTH Q118 and Q131 confirm the eight `<p class="instruction">` bodies are no longer all identical:
`Select-String -Path F4/HouseholdSurvey.ent.qsf -Pattern 'class="instruction">' -Context 0,0 | Select-Object -First 40` around each item — expected: translated gate text in the locales Step 0 classified bilingual; Q118 shows TWO instruction paragraphs per language (gate, then READ-ONE), each translated independently. Also run the Task 11 Step 5 ICF probe adapted to `F4/HouseholdSurvey.ent.qsf` (FIL ICF body ≠ EN).

- [ ] **Step 6: Record**

Wave log: Step-0 bilingual/monolingual table, notes coverage per locale before/after (`coverage()` output vs `NOTES_FLOOR`), which locales carry a translated gate. No git step.

### Task 30: Static gates + version stamp 3.2.0

**Files:**
- Modify: `deliverables/CSPro/versions.json:29-33` (F4 → `3.2.0`, today's date) via `stamp_version.py` only
- Modify (generated): `deliverables/CSPro/F4/HouseholdSurvey.pff` Description, `HouseholdSurvey.ent.qsf` footer, `automation/RELEASE-NOTES.md`, `WHATS-NEW.md`
- Test: `deliverables/CSPro/F4/test_aug21_f4.py`

**Interfaces:**
- Consumes: `py automation/stamp_version.py bump F4 --minor --type changed --notes "..."` (hand-parsed sys.argv — only `--notes`/`--type`/`--breaking` exist (stamp_version.py:27-30, 208-211), `--notes` MUST be the last argument, there is NO `--whatsnew` flag: WHATS-NEW is regenerated from the release-note bullet; MINOR = new/changed functionality; regenerates RELEASE-NOTES + WHATS-NEW + portal publish via `release_notes.py`); `py automation/verify_questions.py F4`; `py automation/stamp_version.py show` (exit 1 on drift)
- Produces: `versions.json["F4"] == {"app": "Household Survey", "version": "3.2.0", "date": "<today>", "channel": "dev"}`; pff Description `Household Survey (F4) - v3.2.0 (<date>) [DEV]`

- [ ] **Step 1: Write the failing test** (append to `test_aug21_f4.py`)

```python
import json as _json   # noqa: E402


def test_f4_version_is_3_2_0():
    v = _json.loads((HERE.parent / "versions.json").read_text(encoding="utf-8"))["F4"]
    assert v["version"] == "3.2.0" and v["channel"] == "dev"
    pff = (HERE / "HouseholdSurvey.pff").read_text(encoding="utf-8", errors="ignore")
    assert "v3.2.0" in pff and "[DEV]" in pff
```

- [ ] **Step 2: Run test to verify it fails** — `python -m pytest test_aug21_f4.py -q -k version` → FAIL (`'3.1.4' == '3.2.0'`).

- [ ] **Step 3: Run the gates, then bump**

```powershell
$env:PYTHONIOENCODING='utf-8'
cd deliverables/CSPro
python F4/generate_apc.py; python F4/generate_fmf.py
python automation/verify_questions.py F4
python automation/skip_boundary_check.py F4
python automation/stamp_version.py bump F4 --minor --type changed --notes "Aug-21 questionnaire alignment: Q30/Q35/Q36/Q40/Q67 wording (Q40 'completed' reverses #608), printed gates on Q117/Q118/Q131/Q135 as on-screen notes, Aug-21 translations imported for all 7 languages, consent screens and section intros per language"
python automation/stamp_version.py show
```
Expected: `[F4] … PASS`; `[ OK ] F4: no skip target/source/noinput-gate inside a shared screen`; bump prints `F4 3.1.4 -> 3.2.0`, restamps the pff, regenerates the qsf; `show` exits 0 (no drift).

- [ ] **Step 4: Run test to verify it passes**

Run: `cd F4; python -m pytest test_aug21_f4.py -q` → `19 passed`.

- [ ] **Step 5: Verify/gate**

`git status --short deliverables/CSPro/F4 deliverables/CSPro/versions.json deliverables/CSPro/automation` — expected modified set: `generate_dcf.py`, `generate_qsf.py`, `HouseholdSurvey.dcf/.apc/.fmf/.pff/.ent.qsf`, `translations/*.json`, `test_aug21_f4.py` (new), `automation/aug21_check_gates.py` (new), `versions.json`, `RELEASE-NOTES.md`, `WHATS-NEW.md`, `whats-new.html`. Nothing under `raw/`.

- [ ] **Step 6: Record**

Wave log: version line, gate outputs. No git step.

### Task 31: Fresh-Designer compile + publish + auto_deploy F4

**Files:**
- Create: `deliverables/CSPro/automation/shots/F4_compile.png`, `deliverables/CSPro/automation/shots/deploy/*F4*.png`
- Test: none (vision-checked screenshots are the gate)

**Interfaces:**
- Consumes: `py automation/cspro_compile_driver.py F4 --build --save` (regenerate → bind → compile → Ctrl+S; prints `COMPILE-SHOT <path>`); `py automation/csweb_deploy_designer.py open|filemenu|shot|keys "<seq>"|click X Y` (vision-guided steps to reach the 'Deploy to CSWeb' dialog, WM_COMMAND 44038 per memory; `open` launches on `DEPLOY_KEY` env — default F1 — and kills any running Designer first); `py automation/auto_deploy.py F4 --deploy` (package-name-locked to `HouseholdSurvey`, ships `review.html` for F4 :189-190, needs `CSPRO_ADMIN_USER` + `CSPRO_ADMIN_PASS_FILE`)
- Produces: deployed `HouseholdSurvey.zip` on the CSWeb box (`root@207.148.65.115:/opt/app/lamp/www/csweb/files/apps/`) with pff Description `v3.2.0`

- [ ] **Step 1: Compile in a FRESH Designer (attach trap)**

```powershell
Get-Process CSPro -ErrorAction SilentlyContinue | Stop-Process -Force   # PS Stop-Process, never Git-Bash taskkill
cd deliverables/CSPro
python automation/cspro_compile_driver.py F4 --build --save
```
Expected: `COMPILE-SHOT …\automation\shots\F4_compile.png`; open the PNG (Read tool) and confirm the Compiler Output tab reads `Compile Successful`. On an error line, fix the generator, never the .apc.

- [ ] **Step 2: Publish from the open Designer**

```powershell
$env:DEPLOY_KEY = "F4"
python automation/csweb_deploy_designer.py shot          # confirm HouseholdSurvey is the open app
python automation/csweb_deploy_designer.py filemenu       # File menu shot -> locate "Deploy to CSWeb"
python automation/csweb_deploy_designer.py click <x> <y> deploy-to-csweb   # coordinates read from the shot
```
Expected: the 'Deploy to CSWeb' dialog is open (shot shows package name `HouseholdSurvey`); the memory rule applies — a NEW CSDeploy pid is the publish gate.

- [ ] **Step 3: Deploy**

```powershell
$env:CSPRO_ADMIN_USER='admin'; $env:CSPRO_ADMIN_PASS_FILE='C:/Users/analy/.secrets/csweb_admin.txt'
python automation/auto_deploy.py F4 --deploy
```
Expected: exit 0, result shot under `automation/shots/deploy/`, CSWeb dialog reports success. Exit 1 = dialog not found / package-name mismatch → re-do Step 2.

- [ ] **Step 4: Verify/gate — CSWeb shows the new build**

```powershell
ssh root@207.148.65.115 "ls -l --time-style=full-iso /opt/app/lamp/www/csweb/files/apps/HouseholdSurvey.zip"
```
Expected: mtime within the last minutes. **Fix `EVDATE` now** (`$EVDATE = Get-Date -Format yyyy-MM-dd`) for Tasks 32–34.

- [ ] **Step 5: Record**

Wave log: compile shot path, deploy shot path, zip mtime, `EVDATE`.

### Task 32: Byte-verify the deployed package against the maps

**Files:**
- Create: `docs/uat-fix-evidence/<EVDATE>-aug21-translations/F4/byte-verify.txt`, `00-deploy-result.png`
- Test: the tool IS the check (exit 1 on any miss)

**Interfaces:**
- Consumes: deployed `HouseholdSurvey.zip` (scp from `root@207.148.65.115:/opt/app/lamp/www/csweb/files/apps/`); F4 maps; `aug17-tools/byte_verify_aug21.py` (Task 19; `PROBE_KEYS["F4"]` = the five aligned items; memory rule: verify via `bytes.find` of the UTF-16-LE encoding, whole-blob decode false-negatives at odd offsets)
- Produces: `byte-verify.txt` (the evidence file the 2026-08-20 folder precedent uses)

- [ ] **Step 1: Pull + verify**

```powershell
$root='C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development'
$EVDATE = "<EVDATE>"     # e.g. 2026-08-26 — fixed in Task 31 Step 4
$ev = "$root/docs/uat-fix-evidence/$EVDATE-aug21-translations/F4"; New-Item -ItemType Directory -Force $ev | Out-Null
scp root@207.148.65.115:/opt/app/lamp/www/csweb/files/apps/HouseholdSurvey.zip $env:TEMP/HouseholdSurvey.zip
$env:PYTHONIOENCODING='utf-8'
cd "$root/deliverables/CSPro"
Get-ChildItem automation/shots/deploy | Sort-Object LastWriteTime | Select-Object Name, LastWriteTime   # pick the F4 result-dialog PNG
$shot = "automation/shots/deploy/<the-one-F4-result-file>.png"
py aug17-tools/byte_verify_aug21.py F4 $env:TEMP/HouseholdSurvey.zip F4/translations "$ev/byte-verify.txt" --version v3.2.0 --deploy-shot $shot "$ev/00-deploy-result.png"
```
Expected: every map value `OK` (keys without a map value print `SKIP … English fallback`), `OK   footer version … 'v3.2.0'`, `RESULT: ALL PASS`, exit 0. A `MISS` for a value present in the map means the deployed .pen was packaged from a stale build (the truncated-upload-reports-SUCCESS trap) → redo Task 31.

- [ ] **Step 2: Verify/gate** — `Get-Content $ev/byte-verify.txt | Select-String MISS` returns nothing; `Test-Path "$root/docs/uat-fix-evidence/2026-08-2x-aug21-translations"` is `False` (no placeholder folder was created).

- [ ] **Step 3: Record** — byte-verify.txt is committed with the evidence in Task 33 (evidence commits are sanctioned).

### Task 33: Emulator locale shots — Q40 + Q67 in FIL and CEB

**Files:**
- Create: `docs/uat-fix-evidence/<EVDATE>-aug21-translations/F4/f4_q40_{en,fil,ceb}.png`, `f4_q67_{en,fil,ceb}.png`, `f4_q131_fil.png`, `00-app-list-f4-3.2.0.png`, `README.md`
- Test: none (PNG contents are checked by eye via the Read tool)

**Interfaces:**
- Consumes: the 2026-08-17 capture method (memory `reference_uat_fix_evidence.md` / `reference_csentry_pen_sideload.md`): `emulator -avd capi_tablet -no-snapshot -gpu host`; `adb shell monkey -p gov.census.cspro.csentry -c android.intent.category.LAUNCHER 1`; sideload the DEPLOYED zip's `.pen + .pff + psgc_*` into `/storage/emulated/0/Android/data/gov.census.cspro.csentry/files/csentry/HouseholdSurvey/`; cold-boot perms fix `adb root; chown -R u0_a192:ext_data_rw; chmod -R 770` on `/data/media/0/Android/data/gov.census.cspro.csentry/files/csentry/HouseholdSurvey`; capture `adb shell screencap -p /sdcard/cap.png` + `adb pull` (never PowerShell `>`); language switch = CSEntry's in-app language menu by hand; `adb emu kill`
- Produces: SHA-pinned PNG evidence + README in the wave evidence folder

- [ ] **Step 1: Boot + sideload the deployed package**

```powershell
$adb = "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe"
Start-Process "$env:LOCALAPPDATA\Android\Sdk\emulator\emulator.exe" -ArgumentList @("-avd","capi_tablet","-no-snapshot","-gpu","host")
& $adb wait-for-device; & $adb shell input keyevent 224
Expand-Archive -Force $env:TEMP/HouseholdSurvey.zip $env:TEMP/HouseholdSurvey
$dst = "/storage/emulated/0/Android/data/gov.census.cspro.csentry/files/csentry/HouseholdSurvey"
& $adb shell mkdir -p $dst
Get-ChildItem $env:TEMP/HouseholdSurvey -Recurse -Include *.pen,*.pff,*.dcf,psgc_*,review.html | ForEach-Object { & $adb push $_.FullName "$dst/" }
& $adb root; & $adb shell "chown -R u0_a192:ext_data_rw /data/media/0/Android/data/gov.census.cspro.csentry/files/csentry/HouseholdSurvey; chmod -R 770 /data/media/0/Android/data/gov.census.cspro.csentry/files/csentry/HouseholdSurvey"
& $adb shell monkey -p gov.census.cspro.csentry -c android.intent.category.LAUNCHER 1
```
Expected: the CSEntry app list shows `Household Survey (F4) - v3.2.0 (<date>) [DEV]`. Capture it as `00-app-list-f4-3.2.0.png` (Step 3 command). If the PSGC files are not in the zip (they are added by `auto_deploy.py` separately), copy them on-device from another installed app folder exactly as Task 20 Step 3 does.

- [ ] **Step 2: Navigate to Q40, then Q67, once per language (EN, FIL, CEB)**

Open the app → Add case → enter a test case key → consent Continue → Section B minimal answers → Section C roster line 1 → stop on `Q40_EDUCATION`. Switch language via ⋮ → Language → Filipino, re-shoot; → Cebuano, re-shoot. Continue to Section D `Q67_TRAVEL_HH` and repeat. Also shoot `Q131_NBB_OOP` in FIL once to show the gate note (route: Q130 = DOH-retained).

- [ ] **Step 3: Capture (binary-safe; run in an interactive PowerShell window, not the tool — `Read-Host` paces the shots)**

```powershell
$ev = "docs/uat-fix-evidence/$EVDATE-aug21-translations/F4"
foreach ($n in "00-app-list-f4-3.2.0","f4_q40_en","f4_q40_fil","f4_q40_ceb","f4_q67_en","f4_q67_fil","f4_q67_ceb","f4_q131_fil") {
  Read-Host "Screen ready for $n ? press Enter"
  & $adb shell screencap -p /sdcard/cap.png; & $adb pull /sdcard/cap.png "$ev/$n.png"; & $adb shell rm /sdcard/cap.png
}
& $adb emu kill
```
Expected: 8 PNGs > 1000 bytes each; opening `f4_q40_fil.png` shows the FIL text from `fil.json["item:Q40_EDUCATION"]` (no `attended`), `f4_q67_fil.png` shows the pharmacy definition in FIL, `f4_q131_fil.png` shows the gate note in blue instruction style.

- [ ] **Step 4: README + commit the evidence (sanctioned write)**

```markdown
# Aug-21 translations — F4 fix evidence (wave 3, v3.2.0)

**Driver:** ASPSI Aug-21 revised instruments (raw/Survey-Instruments-2026-08-21). **Ships as:** F4 v3.2.0 (dev channel).
**What changed:** Q30/Q35/Q36/Q40/Q67 English aligned to the paper (Q40 "completed" reverses #608); printed gates on Q117/Q118/Q131/Q135 as on-screen notes; 7-locale Aug-21 import (coverage FIL60→?, …); consent screens + section intros per language.

| file | what it shows |
|---|---|
| `00-deploy-result.png` | CSWeb deploy dialog, v3.2.0 |
| `00-app-list-f4-3.2.0.png` | app list with the v3.2.0 [DEV] stamp |
| `f4_q40_{en,fil,ceb}.png` | Q40 "Highest level of education completed" + its FIL/CEB Aug-21 cell |
| `f4_q67_{en,fil,ceb}.png` | Q67 pharmacy stem with the definition, EN/FIL/CEB |
| `f4_q131_fil.png` | Q131 printed gate rendered as an instruction note in FIL |
| `byte-verify.txt` | deployed .pen contains every map value for the 5 aligned items (utf-16-le bytes.find, aug17-tools/byte_verify_aug21.py) |
```
```powershell
git add "docs/uat-fix-evidence/$EVDATE-aug21-translations/F4"
git commit -m "evidence: F4 v3.2.0 Aug-21 translations locale shots + byte-verify"
git push
```
Expected: commit SHA printed; URLs `https://raw.githubusercontent.com/<org>/<repo>/<sha>/docs/uat-fix-evidence/<EVDATE>-aug21-translations/F4/f4_q40_fil.png` resolve.

- [ ] **Step 5: Record** — SHA + file list in the wave log.

### Task 34: F4 patch note file (#f4-uat)

**Files:**
- Create: `deliverables/CSPro/patch-notes/<EVDATE>-f4-v3.2.0-aug21-translations.md` (`<EVDATE>` = `versions.json["F4"].date` written by Task 30)
- Test: `deliverables/CSPro/F4/test_aug21_f4.py`

**Interfaces:**
- Consumes: the cspro-patch-fix SKILL.md template (:160-165: bold header, *Fixed:*, *To get it:* remove + re-add, `v<X.Y.Z> (<date>)`, "Cases already in progress are unaffected"); `versions.json["F4"]` date; Task 26 artifact list; Task 28 coverage table; Task 33 SHA-pinned URLs
- Produces: the note text Carl's loop posts to `#f4-uat` (the task does NOT post)

- [ ] **Step 1: Write the failing test** (append to `test_aug21_f4.py`)

```python
import re as _re   # noqa: E402


def test_patch_note_exists_and_leads_with_remove_readd():
    notes = sorted((HERE.parent / "patch-notes").glob("*-f4-v3.2.0-aug21-translations.md"))
    assert notes, "no <EVDATE>-f4-v3.2.0-aug21-translations.md under patch-notes/"
    p = notes[-1]
    assert _re.match(r"\d{4}-\d{2}-\d{2}-f4-v3\.2\.0-aug21-translations\.md$", p.name), p.name   # dated, never 'draft-'
    t = p.read_text(encoding="utf-8")
    assert "v3.2.0" in t and "remove" in t.lower() and "Add Application" in t
    assert "#608" in t and "completed" in t          # the reversal is stated
    assert not _re.search(r"<\?>|<date>|<URL|2026-08-2x", t)   # no placeholders survive
```

- [ ] **Step 2: Run test to verify it fails** — `python -m pytest test_aug21_f4.py -q -k patch_note` → FAIL (`assert p.exists()`).

- [ ] **Step 3: Write the note** (`New-Item -ItemType Directory -Force deliverables/CSPro/patch-notes`, then the file, LF, UTF-8)

```markdown
🔧 **Household Survey (F4) — patch deployed (v3.2.0)**
*Changed:* The app now matches ASPSI's **Aug-21 revised questionnaire** and carries the **Aug-21 translations in all 7 languages** (Filipino, Bikol, Bisaya, Cebuano, Waray, Hiligaynon, Ilocano — coverage FIL <?>%, BCL <?>%, BIS <?>%, CEB <?>%, WAR <?>%, HIL <?>%, ILO <?>%, up from 60/62/61/64/66/50/60).
- Q30 roster name prompt now reads "Name (Write the complete name of HH member)".
- Q35 "With disability?" / Q36 "Would the patient like to specify the type of disability?".
- Q40 now reads "Highest level of education **completed**" — this reverses the earlier tester ruling #608 ("attended/reached"); the DOH-submitted paper wins.
- Q67 pharmacy travel-time stem now carries the paper's pharmacy definition (FDA LTO).
- Q117/Q118 show the paper's "[Answer only “yes” in Q112]" and Q131/Q135 "[Ask only if they went to a DOH-retained hospital]" as blue notes; routing is unchanged (the app already skips them automatically).
- The consent screens and the section intros now read in the selected language (Aug-21 cleared translations); paragraphs without a cleared translation stay English.
- No question numbers, codes or data shape changed (MINOR bump).
*Known:* the build-vs-paper checker still lists a few rows that are PDF layout artifacts, not wording differences (roster grid headers on Q35–Q40, the Section N "67. Housing" table row, HH:MM component suffixes).
*To get it:* In CSEntry, **remove Household Survey, then Add Application → from CSWeb**. You're on the new build when the app list shows **v3.2.0 (<date>) [DEV]**. (⋮ → Update Installed Applications is unreliable.)
Cases already in progress are unaffected.
Evidence: <raw.githubusercontent.com SHA-pinned URLs for f4_q40_fil.png, f4_q67_ceb.png, byte-verify.txt>
```
Fill every `<?>`/`<date>`/`<URL>` from Tasks 28, 30 and 32 before saving.

- [ ] **Step 4: Run test to verify it passes** — `python -m pytest test_aug21_f4.py -q` → `20 passed`.

- [ ] **Step 5: Verify/gate** — `Select-String "<\?>|<date>|<URL|2026-08-2x" deliverables/CSPro/patch-notes/*-f4-v3.2.0-aug21-translations.md` returns nothing (no placeholders left).

- [ ] **Step 6: Record** — prepend a dated entry to `log.md`: "F4 v3.2.0 — Aug-21 alignment + translations; coverage table; overrides; notes floor vs after; evidence SHA; note file path". Wave 3 closes; Carl commits the CSPro tree when ready. No git step for generator/map changes.

---

## Wave 4a — F3 English alignment: rewords, 97.x/115.x label re-sync, HIL/ILO facility-fill gap

**Scope guard (Carl, 2026-08-25):** text-only. No new items, no new records, no code changes to any value set; 115.1/115.2 stay the flat Yes/No + `_AMT` matrix (`F3/generate_dcf.py` :1727-1757, comment :1760-1762). F3 ships **6.1.0** once (minor; live 6.0.3) — the bump/deploy is Task 42, AFTER the Wave-4b import (Tasks 40–41), so the reworded questions ship WITH their Aug-21 translations in a single build.

**Prerequisite (Day-0):** Task 39 Step 3 calls `data/translations-official/aug21_english_delta.py --only F3` (Task 0). If for any reason it is not on disk, use the inline fallback in Task 39 Step 3.

**PowerShell convention for every inline Python block in this section:** `python - @'...'@` does NOT work (the here-string becomes argv[1] and python blocks on stdin). Every block below is written as `@' ... '@ | python -` — the here-string is PIPED into python. Keep it that way.

**Run-time date:** wherever a path or file name below contains `<date>`, substitute the build date at run time: `$d = Get-Date -Format yyyy-MM-dd`. The patch-note date MUST equal the `date` field that `stamp_version.py` writes into `versions.json` for F3 (Task 42 Step 1).

**What the Aug-21 English PDF actually says** (read 2026-08-25 with fitz from `raw/Survey-Instruments-2026-08-21/English/F3-English_Patient Survey Questionnaire_UHC Year 2_Aug21.pdf`):
- Q47: `Are you aware that there are PhilHealth packages for the following health services:` rows `Physician check-up` / `Diagnostic tests (e.g. laboratory tests and imaging)` / `Hospital confinement` / `Outpatient drugs`
- Q66: `Is [facility_name] the facility you usually go to for general health concerns?` — **the seven translated PDFs still carry `[facility_name_input]`** (HIL: "Ang [facility_name_input] bala ang pasilidad…", ILO: "Ti kadi [facility_name_input] ti pasilidad…"), and `_FACILITY_PLACEHOLDER_RE` (:2450-2456) matches only the `_input` forms → **leave the Q66/Q88 labels unchanged.**
- Q69: `How long does it take you to travel from your house when going to the health facility that you usually go to?` Time (HH:MM)
- Q94: `How much was the cost of [laboratory test: ]?`
- Q96: `How much was spent for (NAME IN ___)'s prescribed medicines?` — options **already** read `Free, charge to PhilHealth` etc. with commas (the earlier "no comma" delta was a parser artifact) → `Q96_MEDS_PAY` (:1198-1207) and `generate_apc.py` `Q96_ROSTER_PROCS` (:599-606) stay byte-identical.
- Q97.1: identical to the build (`Q971_SOURCES` :1229-1235, stem :1413-1417) → no change.
- Q97.2: `…that were NOT included in the outpatient bill?`; negative option `No, did not pay for any other expenses` (no `g)`).
- Q98: `Did you use any of the following to pay for medical costs? (select all that apply)`
- Q115.1: `Other than the expenses above (e.g. confinement, medicines, laboratory, etc.), which of the following were also included in the bill? How much were you charged or billed?` options `Doctor's Professional Fee` · `Medical equipment or supplies` · `Non-medical expenses: (e.g. Hygiene kit)` · `Diagnostic or laboratory procedure inside the facility` · `Medicines or drugs inside the facility` · `Other expenses:` · `None`
- Q115.2: `Did you pay for any other expenses during your confinement that were not included in the hospital bill?` Yes `<indicate the amount spent>` → 7 rows (build list `Q1142_NOT_IN_BILL` :1637-1645 already verbatim); `No`.

**Decision — tick directives in labels (Q96 vs Q98):** project convention (#1189 comment at :1320-1322) keeps "Select all that apply" OUT of dcf labels and in the qsf `INSTRUCTIONS`. Q96's paper stem carries no directive, so its label drops it and `INSTRUCTIONS_BY_NAME["Q96_SOURCES"] = _SELECT_ALL` keeps the blue note. Q98's paper stem PRINTS `(select all that apply)` inside the sentence; the label keeps it **verbatim** so the Aug-21 extractor anchors on the paper's exact English (anchoring wins over the convention for this one key; the r25/dedup reviewers' earlier objection was to directives duplicated as separate prompts, which this is not). Q98 therefore gets NO `INSTRUCTIONS_BY_NAME` entry (it would double the directive).

---

### Task 35: Code snapshot, r25 baseline, failing label tests (F3)

**Files:**
- Create: `deliverables/CSPro/F3/test_fixtures/aug21_vs_codes_before.json`
- Create: `deliverables/CSPro/F3/test_fixtures/r25_baseline_f3.txt`
- Create: `deliverables/CSPro/F3/test_aug21_labels.py`
- Test: `deliverables/CSPro/F3/test_aug21_labels.py`

**Interfaces:**
- Consumes: `generate_dcf.build_f3_dictionary()` (`F3/generate_dcf.py:2371`), `cspro_helpers.walk_labeled_nodes(dictionary)` (:1126, yields `(key, node)`), `cspro_helpers._value_pair_key(value)` (:1108), `cspro_helpers.TRANSLATION_LANGUAGES` (:1093-1105), `generate_dcf._FACILITY_NEUTRAL` (:2460-2467), `generate_dcf._neutralise_facility_placeholder(dictionary)` (:2486), `aug17-tools/r25_caption_check.py F3`
- Produces: `vs_code_map(dictionary) -> dict[str, list[str]]` (vs name → ordered code list) and `en_labels(dictionary) -> dict[str, str]` (name-scoped key → EN text), both reused by Tasks 36–38; fixture `aug21_vs_codes_before.json` = `{vs_name: [codes…]}` taken BEFORE any edit; `r25_baseline_f3.txt` = the pre-wave r25 output

- [ ] **Step 1: Take the pre-edit value-set snapshot** (run BEFORE touching the generator; note the `| python -` pipe)

```powershell
cd "C:\Users\analy\Documents\analytiflow\1_Projects\ASPSI-DOH-CAPI-CSPro-Development\deliverables\CSPro"
New-Item -ItemType Directory -Force F3\test_fixtures | Out-Null
$env:PYTHONIOENCODING = "utf-8"
@'
import json, sys
sys.path.insert(0, "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSPro")
sys.path.insert(0, "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSPro/F3")
from generate_dcf import build_f3_dictionary
from cspro_helpers import walk_labeled_nodes, _value_pair_key
d = build_f3_dictionary()
snap = {}
for key, node in walk_labeled_nodes(d):
    if key.startswith("vs:"):
        snap[key[3:]] = [_value_pair_key(v) for v in node.get("values", []) or []]
out = "C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSPro/F3/test_fixtures/aug21_vs_codes_before.json"
with open(out, "w", encoding="utf-8", newline="\n") as fh:
    json.dump(snap, fh, ensure_ascii=False, indent=1); fh.write("\n")
print(len(snap), "value sets snapshotted")
'@ | python -
Test-Path F3\test_fixtures\aug21_vs_codes_before.json
```
Expected: `213 value sets snapshotted` (>200; the build has 213 value sets, verified 2026-08-25) and `True`.

- [ ] **Step 2: Record the r25 baseline on the UNTOUCHED checkout** (the gate already fails before this wave: 11 GPS fields `REC_FACILITY_CAPTURE_FORM.FACILITY_GPS_*` / `REC_PATIENT_HOME_CAPTURE_FORM.P_HOME_GPS_*` have empty qsf questionText → `R25 caption gate: FAIL ['F3']`, verified 2026-08-25)

```powershell
cmd /c "set PYTHONIOENCODING=utf-8&& python aug17-tools\r25_caption_check.py F3 > F3\test_fixtures\r25_baseline_f3.txt 2>&1"
Select-String -Path F3\test_fixtures\r25_baseline_f3.txt -Pattern "no qsf prompt|caption=|collisions|R25 caption gate"
```
Expected (pre-flight scan 2026-08-25, run on the untouched checkout): `[FAIL] fields with no qsf prompt: 52` (control-form fields, the 14 roster `_PAY_LINE`/`_PAY_SRC` stubs, `FIELD_CONTROL_FORM_3`, and the 12 GPS rows - all pre-existing; the tool never prints a `NO-PROMPT` token), `same-screen caption collisions: 0`, `R25 caption gate: FAIL ['F3']`. This is the baseline — Task 39's criterion is "no NEW rows vs this file", not "exit 0". (Fixing the GPS prompts is a separate pre-existing defect, NOT this wave's.)

- [ ] **Step 3: Write the failing tests**

```python
# deliverables/CSPro/F3/test_aug21_labels.py
"""Wave 4a (Aug-21 English alignment) — F3 label re-sync is text-only.

Run from deliverables/CSPro:  python -m pytest F3/test_aug21_labels.py -q
"""
import json
import sys
from pathlib import Path

import pytest

CSPRO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CSPRO))
sys.path.insert(0, str(CSPRO / "F3"))

from cspro_helpers import TRANSLATION_LANGUAGES, walk_labeled_nodes, _value_pair_key  # noqa: E402
import generate_dcf  # noqa: E402

FIX = Path(__file__).parent / "test_fixtures" / "aug21_vs_codes_before.json"


def vs_code_map(dictionary):
    out = {}
    for key, node in walk_labeled_nodes(dictionary):
        if key.startswith("vs:"):
            out[key[3:]] = [_value_pair_key(v) for v in node.get("values", []) or []]
    return out


def en_labels(dictionary):
    out = {}
    for key, node in walk_labeled_nodes(dictionary):
        labs = node.get("labels") or []
        if labs:
            out[key] = labs[0].get("text", "")
    return out


@pytest.fixture(scope="module")
def d():
    return generate_dcf.build_f3_dictionary()


@pytest.fixture(scope="module")
def labels(d):
    return en_labels(d)


Q47_STEM = "47. Are you aware that there are PhilHealth packages for the following health services: — "
Q69_STEM = ("69. How long does it take you to travel from your house when going to the health "
            "facility that you usually go to?")
Q1141_STEM = ("115.1 Other than the expenses above (e.g. confinement, medicines, laboratory, etc.), "
              "which of the following were also included in the bill?")
Q1142_STEM = ("115.2 Did you pay for any other expenses during your confinement that were not "
              "included in the hospital bill?")


@pytest.mark.parametrize("name,service", [
    ("Q47_PHYSICIAN_CHECKUP", "Physician check-up"),
    ("Q47_DIAGNOSTIC_TESTS", "Diagnostic tests (e.g. laboratory tests and imaging)"),
    ("Q47_HOSPITAL_CONF", "Hospital confinement"),
    ("Q47_OUTPATIENT_DRUGS", "Outpatient drugs"),
])
def test_q47_single_stem(labels, name, service):
    assert labels[f"item:{name}"] == Q47_STEM + service


def test_q69_paper_stem(labels):
    assert labels["item:Q69_USUAL_TRAVEL_HH"] == Q69_STEM + " — Hours"
    assert labels["item:Q69_USUAL_TRAVEL_MM"] == Q69_STEM + " — Minutes"


def test_q94_q96_q98_stems(labels):
    assert labels["item:Q94_LAB_AMT"] == \
        "94. How much was the cost of [laboratory test]? (amount paid out-of-pocket, Pesos)"
    assert labels["item:Q96_SOURCES"] == "96. How much was spent for the prescribed medicines?"
    assert labels["item:Q98_SOURCES"] == \
        "98. Did you use any of the following to pay for medical costs? (select all that apply)"


def test_q972_paper_text(labels):
    assert labels["item:Q972_SOURCES"] == ("97.2 Did you pay for any other expenses during your "
                                           "OPD visit that were NOT included in the outpatient bill?")
    assert labels["val:Q972_SOURCES_VS1:90"] == "No, did not pay for any other expenses"


def test_q1141_q1142_paper_text(labels):
    assert labels["item:Q1141_1"] == Q1141_STEM + " — Doctor's Professional Fee"
    assert labels["item:Q1141_3"] == Q1141_STEM + " — Non-medical expenses: (e.g. Hygiene kit)"
    assert labels["item:Q1141_6"] == Q1141_STEM + " — Other expenses:"
    assert labels["item:Q1141_3_AMT"] == \
        "115.1 How much were you charged or billed? — Non-medical expenses: (e.g. Hygiene kit) (Amount in Pesos)"
    assert labels["item:Q1141_NONE"] == Q1141_STEM + " — None"
    assert labels["item:Q1142_HAS_OTHER"] == Q1142_STEM
    assert labels["item:Q1142_2"] == Q1142_STEM + " — Payment made directly to doctor/s and their secretary"
    assert labels["item:Q1142_7_AMT"] == "115.2 Indicate the amount spent — Other (specify) (Amount in Pesos)"


def test_q66_q88_placeholders_untouched(labels):
    # The translated Aug-21 PDFs still carry [facility_name_input]; the regex only matches that form.
    assert "[facility_name_input]" in labels["item:Q66_SAME_AS_USUAL"]
    assert "[FACILITY_NAME_INPUT]" in labels["item:Q88_WHY_VISIT"]


def test_every_label_under_255(labels):
    long = {k: len(v) for k, v in labels.items() if len(v) > 255}
    assert long == {}


def test_value_set_codes_unchanged(d):
    before = json.loads(FIX.read_text(encoding="utf-8"))
    assert vs_code_map(d) == before


def test_checkbox_value_sets_ascend(d):
    for name in ("Q971_SOURCES_VS1", "Q972_SOURCES_VS1", "Q96_SOURCES_VS1", "Q98_SOURCES_VS1"):
        codes = vs_code_map(d)[name]
        assert codes == sorted(codes, key=int), name


def test_facility_neutral_covers_every_locale():
    want = {code for code, _disp, _f in TRANSLATION_LANGUAGES}
    assert set(generate_dcf._FACILITY_NEUTRAL) == want


def test_neutralise_touches_every_language():
    labs = [{"language": code, "text": "Is [facility_name_input] the one?"}
            for code, _d, _f in TRANSLATION_LANGUAGES]
    node = {"labels": labs}
    n = generate_dcf._neutralise_facility_placeholder(node)
    assert n == len(TRANSLATION_LANGUAGES)
    for lab in labs:
        assert "[facility_name_input]" not in lab["text"], lab
        # Non-English labels must NOT fall back to the English phrase (HIL/ILO gap).
        if lab["language"] != "EN":
            assert lab["text"] != "Is this facility the one?", lab
```

- [ ] **Step 4: Run tests to verify they fail**

Run: `cd deliverables/CSPro; $env:PYTHONIOENCODING="utf-8"; python -m pytest F3/test_aug21_labels.py -q`
Expected: FAIL — `test_q47_single_stem[Q47_PHYSICIAN_CHECKUP-Physician check-up]`, `[Q47_DIAGNOSTIC_TESTS-Diagnostic tests (e.g. laboratory tests and imaging)]`, `[Q47_HOSPITAL_CONF-Hospital confinement]`, `[Q47_OUTPATIENT_DRUGS-Outpatient drugs]`, `test_q69_paper_stem`, `test_q94_q96_q98_stems`, `test_q972_paper_text`, `test_q1141_q1142_paper_text`, `test_facility_neutral_covers_every_locale`, `test_neutralise_touches_every_language` (HIL/ILO currently substitute English "this facility") fail; `test_value_set_codes_unchanged`, `test_checkbox_value_sets_ascend`, `test_q66_q88_placeholders_untouched`, `test_every_label_under_255` PASS.

- [ ] **Step 5: Record** — note in the wave log that `aug21_vs_codes_before.json` is the pre-edit code baseline (dated 2026-08-25, build 6.0.3) and `r25_baseline_f3.txt` is the pre-existing GPS NO-PROMPT residue (not this wave's).

---

### Task 36: Reword Q47 / Q69 / Q94 / Q96 / Q98 stems to the Aug-21 paper

**Files:**
- Modify: `deliverables/CSPro/F3/generate_dcf.py:719-724` (Q47_PACKAGES), `:982-987` (Q69), `:128-130` (Q94_LAB_AMT inside `_build_lab_payment_roster`), `:1393-1397` (Q96_SOURCES), `:1451-1455` (Q98_SOURCES)
- Modify: `deliverables/CSPro/F3/generate_qsf.py:269` (INSTRUCTIONS_BY_NAME — keep the tick directive Q96 loses from its label)
- Test: `deliverables/CSPro/F3/test_aug21_labels.py::test_q47_single_stem`, `::test_q69_paper_stem`, `::test_q94_q96_q98_stems`

**Interfaces:**
- Consumes: `checkbox_multiselect(prefix, label, options, with_other_txt=None)` (`cspro_helpers.py:298`), `yes_no(name, label)` (:257), `numeric(name, label, length=…)` (:212), `_strip_component_suffix(nm, text)` (`generate_qsf.py:109-114`, strips `— Hours/— Minutes`; `Q69_USUAL_TRAVEL_HH/_MM` are already in `_COMPONENT_SUFFIX_ITEMS` :100), `INSTRUCTIONS_BY_NAME` (`generate_qsf.py:269`), `_SELECT_ALL` (`generate_qsf.py:192`)
- Produces: the five EN label strings asserted in Task 35 (these become the `item:` keys' EN text that `apply_translations` :1154 and the Aug-21 extractor anchor on)

- [ ] **Step 1: Q47 — single paper stem + per-service suffix** (replace :719-724)

```python
    # aug21: paper prints ONE stem + four service rows. Each item keeps the whole stem
    # (dcf labels are the translation anchors, #1059 rule) with the row appended.
    _Q47_STEM = ("47. Are you aware that there are PhilHealth packages for the following "
                 "health services: — ")
    Q47_PACKAGES = [
        ("Q47_PHYSICIAN_CHECKUP", _Q47_STEM + "Physician check-up"),
        ("Q47_DIAGNOSTIC_TESTS",  _Q47_STEM + "Diagnostic tests (e.g. laboratory tests and imaging)"),
        ("Q47_HOSPITAL_CONF",     _Q47_STEM + "Hospital confinement"),
        ("Q47_OUTPATIENT_DRUGS",  _Q47_STEM + "Outpatient drugs"),
    ]
```

- [ ] **Step 2: Q69 — paper stem, component suffix kept** (replace :982-987)

```python
        numeric("Q69_USUAL_TRAVEL_HH",
                "69. How long does it take you to travel from your house when going to the health "
                "facility that you usually go to? — Hours",
                length=2),
        numeric("Q69_USUAL_TRAVEL_MM",
                "69. How long does it take you to travel from your house when going to the health "
                "facility that you usually go to? — Minutes",
                length=2),
```
(`_COMPONENT_SUFFIX_RE` :105-106 still strips the ` — Hours` / ` — Minutes` tail from the qsf prompt; the dcf label keeps it; the Task 1 extractor strips it before anchoring.)

- [ ] **Step 3: Q94 amount label — paper bracket form** (replace :128-130 inside `_build_lab_payment_roster`)

```python
        numeric("Q94_LAB_AMT",
                "94. How much was the cost of [laboratory test]? (amount paid out-of-pocket, Pesos)",   # aug21: paper's bracket fill; the qsf pipes ~~getvaluelabel(Q94_LAB_CODE)~~ above it (INSTRUCTIONS[94])
                length=amt_length),
```

- [ ] **Step 4: Q96 / Q98 stems** (replace :1393-1397 and :1451-1455)

```python
    items.extend(checkbox_multiselect(
        "Q96_SOURCES",
        "96. How much was spent for the prescribed medicines?",   # aug21: paper stem; "(NAME)" fill not modelled, tick directive moved to qsf INSTRUCTIONS_BY_NAME
        Q96_MEDS_PAY, with_other_txt=False))
```
```python
    items.extend(checkbox_multiselect(
        "Q98_SOURCES",
        # aug21: paper stem kept VERBATIM incl. "(select all that apply)" so the Aug-21 extractor
        # anchors on the paper's exact English (decision in the wave header; no qsf note added,
        # or the directive would print twice).
        "98. Did you use any of the following to pay for medical costs? (select all that apply)",
        Q98_SOURCES, with_other_txt=False))
```

- [ ] **Step 5: Keep the Q96 tick directive as a blue note** — in `generate_qsf.py` `INSTRUCTIONS_BY_NAME = {` (:269) add one entry (name-keyed so it does NOT spray onto `Q96_PAY_LINE/_SRC/_AMT`, which share the `Q96_` prefix):

```python
    "Q96_SOURCES": _SELECT_ALL,   # aug21: the label lost "(Select all that apply.)" to match the paper stem
```

- [ ] **Step 6: Run tests**

Run: `cd deliverables/CSPro; python -m pytest F3/test_aug21_labels.py -q -k "q47 or q69 or q94 or codes or ascend or 255"`
Expected: PASS (the Q47/Q69/Q94-Q96-Q98 tests, plus the code-snapshot, ascending and 255-cap guards).

- [ ] **Step 7: Record** — log the five reworded stems, the Q96-vs-Q98 directive decision, and that `Q96_MEDS_PAY` / `Q96_ROSTER_PROCS` option lists were verified unchanged against the paper (comma form).

---

### Task 37: Re-sync 97.2 / 115.1 / 115.2 labels and option text to the paper (codes untouched)

**Files:**
- Modify: `deliverables/CSPro/F3/generate_dcf.py:1433-1434` (Q972_SOURCES comprehension — negative option), `:1437-1441` (Q972 stem), `:1629-1636` (Q1141_IN_BILL text), `:1727-1757` (115.1/115.2 emitted labels). `Q972_EXPENSES` (:1236-1243) unchanged.
- Test: `deliverables/CSPro/F3/test_aug21_labels.py::test_q972_paper_text`, `::test_q1141_q1142_paper_text`, `::test_value_set_codes_unchanged`

**Interfaces:**
- Consumes: `yes_no(name, label)`, `numeric(name, label, length=…)`, `alpha(name, label, length=…)` (`cspro_helpers.py:225`), `checkbox_multiselect` — all as quoted; `Q1141_IN_BILL`, `Q1142_NOT_IN_BILL` lists; `Q972_SOURCES` comprehension (:1433-1434)
- Produces: EN label text asserted in Task 35; `Q1141_<c>` / `Q1141_<c>_AMT` / `Q1142_<c>` / `Q1142_<c>_AMT` names and `Q1142_HAS_OTHER` are unchanged (the apc `SKIP_RULES` row `("Q1142_HAS_OTHER", "Q1142_HAS_OTHER = 2", "Q116_NBB_HEARD")` at `generate_apc.py:1526` keeps working)

- [ ] **Step 1: Q97.2 — "NOT" + negative option without the g) letter** (replace :1433-1434 and :1437-1441; keep the #1208 comment block between them)

```python
    Q972_SOURCES = ([(label, f"{int(code):02d}") for label, code in Q972_EXPENSES]
                    + [("No, did not pay for any other expenses", "90")])   # aug21: paper prints no g) on the negative option
```
```python
    items.extend(checkbox_multiselect(
        "Q972_SOURCES",
        "97.2 Did you pay for any other expenses during your OPD visit that were NOT "
        "included in the outpatient bill?",   # aug21: paper capitalises NOT
        Q972_SOURCES, with_other_txt=False))
```

- [ ] **Step 2: 115.1 option text — paper colons** (replace :1629-1636; codes 1-6 unchanged; current text reads `Non-medical expenses (e.g. Hygiene kit)` / `Other expenses` without colons)

```python
    Q1141_IN_BILL = [
        ("Doctor's Professional Fee",                                       "1"),
        ("Medical equipment or supplies",                                   "2"),
        ("Non-medical expenses: (e.g. Hygiene kit)",                        "3"),   # aug21: paper colon
        ("Diagnostic or laboratory procedure inside the facility",          "4"),
        ("Medicines or drugs inside the facility",                          "5"),
        ("Other expenses:",                                                 "6"),   # aug21: paper colon
    ]
```

- [ ] **Step 3: 115.1 / 115.2 emitted labels = paper stem + row** (replace :1727-1757; names, order and lengths identical)

```python
    # aug21: labels carry the paper stem so the Aug-21 extractor anchors match; the flat
    # Yes/No + _AMT shape is unchanged (Carl 2026-08-25 — no data-shape change this build).
    _Q1141_STEM = ("115.1 Other than the expenses above (e.g. confinement, medicines, laboratory, "
                   "etc.), which of the following were also included in the bill?")
    for label, code in Q1141_IN_BILL:
        items.append(yes_no(f"Q1141_{code}", f"{_Q1141_STEM} — {label}"))
        items.append(numeric(f"Q1141_{code}_AMT",
                             f"115.1 How much were you charged or billed? — {label} (Amount in Pesos)",
                             length=9))
    items.append(alpha("Q1141_OTHER_TXT",
                       "115.1 Other expenses — specify text", length=120))
    items.append(yes_no("Q1141_NONE", f"{_Q1141_STEM} — None"))
    _Q1142_STEM = ("115.2 Did you pay for any other expenses during your confinement "
                   "that were not included in the hospital bill?")
    items.append(yes_no("Q1142_HAS_OTHER", _Q1142_STEM))
    for label, code in Q1142_NOT_IN_BILL:
        items.append(yes_no(f"Q1142_{code}", f"{_Q1142_STEM} — {label}"))
        items.append(numeric(f"Q1142_{code}_AMT",
                             f"115.2 Indicate the amount spent — {label} (Amount in Pesos)",
                             length=9))
    items.append(alpha("Q1142_OTHER_TXT",
                       "115.2 Other expenses — specify text", length=120))
```
Keep the existing `# aug17 {.mark}` comments above `Q1141_NONE` and `Q1142_HAS_OTHER` in place; only the label strings change.

- [ ] **Step 4: Run the full test file**

Run: `cd deliverables/CSPro; python -m pytest F3/test_aug21_labels.py -q`
Expected: all label tests PASS; only `test_facility_neutral_covers_every_locale` and `test_neutralise_touches_every_language` still FAIL.

- [ ] **Step 5: Gate — the apc error strings that name these options** (English literals, runtime messages are out of scope, but the `'None'` wording must still be true): `grep -n "'None'" deliverables/CSPro/F3/generate_apc.py` → the `Q971`/`Q972` messages (:301, :313, :620, :624) still refer to an option literally labelled `None` (Q971 code 90 unchanged) — no edit needed.

- [ ] **Step 6: Record** — note "97.2 negative option lost its `g)`; 115.1 options gained the paper's colons; 115.1/115.2 rows now carry the paper stem; codes unchanged (fixture diff empty)".

---

### Task 38: Close the HIL/ILO gap in `_FACILITY_NEUTRAL`

**Files:**
- Modify: `deliverables/CSPro/F3/generate_dcf.py:2460-2467` (`_FACILITY_NEUTRAL`)
- Test: `deliverables/CSPro/F3/test_aug21_labels.py::test_facility_neutral_covers_every_locale`, `::test_neutralise_touches_every_language`

**Interfaces:**
- Consumes: `_FACILITY_NEUTRAL` dict keyed by `TRANSLATION_LANGUAGES` code; `_neutralise_facility_placeholder(dictionary)` (:2486, `repl = _FACILITY_NEUTRAL.get(lab.get("language"), "this facility")` — so HIL/ILO TODAY get English "this facility", never the raw token), `_PLACEHOLDER_CLEANUPS` (:2477-2483)
- Produces: `_FACILITY_NEUTRAL["HIL"]`, `_FACILITY_NEUTRAL["ILO"]`

- [ ] **Step 1: Read the phrase from the Aug-21 PDFs** (the paper's own wording of "this facility" is in Q67, the neighbour of Q66; piped into python)

```powershell
cd "C:\Users\analy\Documents\analytiflow\1_Projects\ASPSI-DOH-CAPI-CSPro-Development"
$env:PYTHONIOENCODING = "utf-8"
@'
import fitz, re, glob
for lang in ("Hiligaynon", "Ilocano"):
    f = glob.glob(rf"raw/Survey-Instruments-2026-08-21/Translations/F3-{lang}*.pdf")[0]
    d = fitz.open(f); t = " ".join(" ".join(p.get_text().split()) for p in d); d.close()
    for q in (r"66\. Is \[facility_name_input\].{0,220}", r"67\. Why did you go to this facility.{0,160}"):
        m = re.search(q, t)
        print(lang, "::", m.group(0) if m else "NO MATCH for " + q)
'@ | python -
```
Expected (verified 2026-08-25): HIL Q67 `…nagkadto ka sa sini nga pasilidad…` (oblique `sini` after `sa`; nominative demonstrative = `ini nga pasilidad`), HIL Q66 `Ang [facility_name_input] bala ang pasilidad…`; ILO Q67 `…napanka iti daytoy a pasilidad…` (`daytoy a pasilidad` = "this facility"), ILO Q66 `Ti kadi [facility_name_input] ti pasilidad…`.

- [ ] **Step 2: Add the two entries** (replace :2460-2467)

```python
_FACILITY_NEUTRAL = {
    "EN":  "this facility",
    "FIL": "ang pasilidad na ito",
    "BCL": "an pasilidad na ini",
    "BIS": "kini nga pasilidad",
    "CEB": "kini nga pasilidad",
    "WAR": "ini nga pasilidad",
    # aug21: from the Aug-21 F3 Hiligaynon / Ilocano PDFs' own Q67 wording
    # ("sa sini nga pasilidad" / "iti daytoy a pasilidad"), nominative form.
    "HIL": "ini nga pasilidad",
    "ILO": "daytoy a pasilidad",
}
```

- [ ] **Step 3: Run tests**

Run: `cd deliverables/CSPro; python -m pytest F3/test_aug21_labels.py -q`
Expected: `14 passed` (4 Q47 parametrized cases + 10 others: Q69, Q94/Q96/Q98, 97.2, 114.1/114.2, Q66/Q88, <255, vs-codes, checkbox-ascend, facility-neutral, neutralise).

- [ ] **Step 4: Verify the rendered Q66 label per language** (on the in-memory dictionary; piped into python)

```powershell
cd "C:\Users\analy\Documents\analytiflow\1_Projects\ASPSI-DOH-CAPI-CSPro-Development\deliverables\CSPro"
$env:PYTHONIOENCODING = "utf-8"
@'
import sys; sys.path.insert(0, "."); sys.path.insert(0, "F3")
from pathlib import Path
import generate_dcf
d = generate_dcf.apply_translations(generate_dcf.build_f3_dictionary(), Path("F3/translations"))
generate_dcf._neutralise_facility_placeholder(d)
from cspro_helpers import walk_labeled_nodes
for k, n in walk_labeled_nodes(d):
    if k == "item:Q66_SAME_AS_USUAL":
        for lab in n["labels"]: print(lab.get("language"), "|", lab["text"])
'@ | python -
```
Expected: eight lines, none containing `facility_name_input`; HIL line contains `ini nga pasilidad`, ILO line contains `daytoy a pasilidad` (HIL/ILO show the dialect phrase inside English text until the Task 40 import fills `item:Q66_SAME_AS_USUAL`). Before this task those two lines read English "this facility".

- [ ] **Step 5: Record** — "HIL/ILO facility-neutral phrases sourced from Aug-21 F3 PDFs Q67; replaces the English 'this facility' fallback in the dcf labels (the qsf prompt already pipes ~~FACILITY_NAME~~ for every language); flagged for ASPSI dialect polish like the other six (existing FLAGGED note at :2472-2474 applies)".

---

### Task 39: Regenerate F3 and run the static + compile gates (pre-import)

**Files:**
- Modify (generated): `deliverables/CSPro/F3/PatientSurvey.dcf`, `PatientSurvey.ent.apc`, `PatientSurvey.fmf`, `PatientSurvey.ent.qsf`
- Create: `deliverables/CSPro/F3/test_fixtures/aug21_coverage_after_align.txt`, `deliverables/CSPro/automation/scenarios/f3_aug21_bill_detail_war.txt`
- Test: gate commands below

**Interfaces:**
- Consumes: `python F3/generate_dcf.py` (`main()` :2518-2530 → build → `apply_translations` → `_neutralise_facility_placeholder` → `write_dcf`), `generate_apc.py`, `generate_fmf.py`, `generate_qsf.py`; `automation/verify_questions.py [F3]`; `automation/skip_boundary_check.py F3`; `aug17-tools/r25_caption_check.py F3` (+ `F3/test_fixtures/r25_baseline_f3.txt` from Task 35); `data/translations-official/aug21_english_delta.py --only F3` (Task 0); `automation/cspro_compile_driver.py F3 --build --save`; `automation/csentry_runner.py <scenario> --keep`; `F3/PatientSurvey_WAR.pff` (`[Parameters] Language=WAR`, exists)
- Produces: regenerated F3 artefacts; per-locale coverage line `{CODE}: {matched}/{total} labels translated ({pct}%)` (`cspro_helpers.py:1239`) — record as the wave-4 "before import" baseline; WAR desk-render evidence for 97.1 / 97.2 / 115.1 / 115.2 (pre-import: reworded stems show English where the map has no value yet; the post-import run is Task 41)

- [ ] **Step 1: Regenerate the four artefacts and capture the coverage lines (UTF-8, not Tee-Object — PS 5.1 Tee writes UTF-16 and mojibakes the em-dashes)**

```powershell
cd "C:\Users\analy\Documents\analytiflow\1_Projects\ASPSI-DOH-CAPI-CSPro-Development\deliverables\CSPro"
cmd /c "set PYTHONIOENCODING=utf-8&& python F3\generate_dcf.py > F3\test_fixtures\aug21_coverage_after_align.txt 2>&1"
Get-Content -Encoding utf8 F3\test_fixtures\aug21_coverage_after_align.txt
$env:PYTHONIOENCODING = "utf-8"
python F3\generate_apc.py
python F3\generate_fmf.py
python F3\generate_qsf.py
```
Expected: `generate_dcf.py` prints `Languages: EN, FIL, BCL, BIS, CEB, WAR, HIL, ILO` and seven `XXX: n/1749 labels translated (p%)` lines (baseline measured on the untouched tree 2026-08-25 = FIL60 BCL53 BIS55 CEB58 WAR57 HIL43 ILO52; accept within +/-1 pt — the reworded keys are name-scoped so the counts do NOT drop; the old translations now sit under new English and are replaced by the Task 40 import), then `#714: neutralised facility-name placeholder in N label(s)` with N **unchanged** from the previous build (HIL/ILO labels were already being substituted with English "this facility"; only the replacement phrase changed). No `SystemExit`.

- [ ] **Step 2: Structural gates**

```powershell
python automation\verify_questions.py F3
python automation\skip_boundary_check.py F3
cmd /c "set PYTHONIOENCODING=utf-8&& python aug17-tools\r25_caption_check.py F3 > $env:TEMP\r25_after.txt 2>&1"
Compare-Object (Get-Content F3\test_fixtures\r25_baseline_f3.txt | Select-String "NO-PROMPT|caption=|COLLISION") (Get-Content $env:TEMP\r25_after.txt | Select-String "NO-PROMPT|caption=|COLLISION")
python -m pytest F3\test_aug21_labels.py aug17-tools\test_tools.py -q
```
Expected: `[F3] … dead-conditions 0 · bad-skips 0 · PASS` and `=== per-question verification: F3 PASS`; `[ OK ] F3: no skip target/source/noinput-gate inside a shared screen` (+ the `[WAIVED] ('VISIT_RECORD_BLOCK', 'ENUM_RESULT_FINAL_VISIT')` line); r25: `Compare-Object` prints NOTHING (no NEW NO-PROMPT/COLLISION rows vs the Task-35 baseline — the gate still reports `FAIL ['F3']` because of the pre-existing 11 GPS captions; that is not this wave's regression). If the DUPLICATION residual count rises (the 115.x rows now repeat the stem in their flat block), report the number, do not "fix" it. pytest all green.

- [ ] **Step 3: Prove the build matches the paper** — Task 0's delta tool:

```powershell
python data\translations-official\aug21_english_delta.py --only F3
```
If the script is unexpectedly absent, use this inline fallback (piped into python) which prints every dcf EN label whose normalised text is not a substring of the normalised Aug-21 English PDF:

```powershell
cd "C:\Users\analy\Documents\analytiflow\1_Projects\ASPSI-DOH-CAPI-CSPro-Development\deliverables\CSPro"
@'
import re, sys, glob, fitz
sys.path.insert(0, "."); sys.path.insert(0, "F3")
import generate_dcf
from cspro_helpers import walk_labeled_nodes
pdf = glob.glob(r"..\..\raw\Survey-Instruments-2026-08-21\English\F3-English*.pdf")[0]
doc = fitz.open(pdf); t = " ".join(" ".join(p.get_text().split()) for p in doc); doc.close()
norm = lambda s: " ".join(re.sub(r"[^a-z0-9 ]", " ", s.lower().replace("’", "'")).split())
nt = norm(t)
miss = []
for k, n in walk_labeled_nodes(generate_dcf.build_f3_dictionary()):
    if not k.startswith("item:"): continue
    en = re.sub(r"^\d+(\.\d+)?\.\s*", "", n["labels"][0]["text"])
    en = re.split(r" — ", en)[0]
    if len(norm(en)) >= 12 and norm(en) not in nt:
        miss.append((k, en))
for k, en in miss: print(k, "|", en)
print(len(miss), "labels not found verbatim in the Aug-21 English PDF")
'@ | python -
```
Expected: only parser-artifact rows remain (`paper-only` keeps 97.1/97.2/115.1/115.2 by design). List them verbatim in the wave note; the expected residue is (a) Q66 `[facility_name]` vs build `[facility_name_input]` (deliberate, Task 38 rationale), (b) Q94 `[laboratory test: ]` vs `[laboratory test]`, (c) Q96 `(NAME IN ___)'s` vs `the`, (d) Q97.1/Q115.1 rows where the paper's `Amount in Pesos` column furniture is glued to the option, (e) the Q69 `(BASED ON THE ANSWER ON Q64 …)` enumerator directive that lives in the qsf, not the label, plus (fallback only) roster/encoding stubs like `Payment row` / `auto-filled` / `specify text` that have no paper counterpart. Any OTHER row = go back to Task 36/37.

- [ ] **Step 4: Fresh-Designer compile** (attach trap: close any open Designer first)

```powershell
Stop-Process -Name CSPro -Force -ErrorAction SilentlyContinue
python automation\cspro_compile_driver.py F3 --build --save
```
Expected: `COMPILE-SHOT …\automation\shots\F3_compile.png`; open the PNG (Read tool) and confirm `Compile Successful` in the Compiler Output tab.

- [ ] **Step 5: Desk scenario in WARAY through 97.1 / 97.2 / 115.1 / 115.2 (tick / None / No paths)**

`scenarios/f3_qfs_roster.txt` (64 lines) stops at `shot at_q92_sources` in Section G — it never reaches 97.x or Section H, so it is only the STARTING walk. Create `deliverables/CSPro/automation/scenarios/f3_aug21_bill_detail_war.txt` by copying it, changing the first two live lines, and APPENDING the walk below. Every step auto-screenshots; the two `(continue …)` / `(pilot …)` gaps below (Q93→Q97 and Q98→Q115) are filled by pilot (run with `--keep`, read `run.log` + the last frame, add the next `type`/`key` lines, re-run) because the exact keystroke count depends on the answers chosen. **Time-box: at most 3 `--keep` pilot runs per gap.** Derive the keystrokes from `F3/PatientSurvey.ent.apc` (`SKIP_RULES` for Sections G/H: Q93 labs tick → Q94 roster one row per tick → Q95=1 → Q96 tick 1 + amount → Q97 amount; Q98 tick 1 + amount → Q99 inpatient=1 → Q100…Q112 minimal answers → Q113/Q114/Q115 amounts) and read each frame before adding lines. If a gap is not closed inside the box, STOP piloting: keep the frames reached so far, capture 97.1/97.2 (always reachable — the Q93→Q97 gap is short) and fall back for 115.x to the Task 41 HIL walk (`f3_ghreorder_op.txt` casekey + Section H direct path with `PATIENT_TYPE=Inpatient`, register row `order:G,H`), recording the fallback in the wave note. Wave 4a must not stall on this scenario.

```
# aug21 Wave 4a — re-synced 97.1/97.2/115.1/115.2 labels rendered in WARAY
# (pff [Parameters] Language=WAR). Opening walk = f3_qfs_roster.txt; then continues
# through Section G bill detail into Section H inpatient bill detail.
rmdata ../F3/desktest_war.csdb
launch ../F3/PatientSurvey_WAR.pff
# ... (identical lines from f3_qfs_roster.txt down to `shot at_q92_sources`) ...
# --- Q92 → Q97: tick Out-of-pocket, amounts, Q95 Yes, Q96 tick Out-of-pocket + amount, Q97 amount
note expect Q92_SOURCES tick screen in WAR
type 1
key {ENTER}
type 500
key {ENTER}
# (continue: Q93 labs tick, Q94 roster, Q95=1, Q96 tick 1 + amount, Q97 amount — pilot and fill in)
shot at_q96_sources
# --- 97.1: TICK path (Doctor's Professional Fee) then amount
shot at_q971_sources
type 1
key {ENTER}
type 300
key {ENTER}
shot at_q971_roster
# --- 97.2: NO path (option 90 "No, did not pay for any other expenses")
shot at_q972_sources
type 7
key {ENTER}
shot at_q972_no_option
# --- 98: tick Salary/income + amount, then Section H: Q99 inpatient = Yes ... through Q114/Q115
# (pilot: answer Section H so that Q113/Q114/Q115 are reached; record the keystrokes here)
shot at_q115_final_cash
type 2000
key {ENTER}
# --- 115.1: TICK path on row 1 (Yes + amount), No on rows 2-6, NONE = No
shot at_q1151_row1
type 1
key {ENTER}
type 250
key {ENTER}
type 2
type 2
type 2
type 2
type 2
shot at_q1151_none
type 2
# --- 115.2: NO path first (gate skips to Q116), captured; then the YES path is a second run
shot at_q1152_has_other
type 2
shot after_q1152_no_skips_to_q116
```
Run: `python automation\csentry_runner.py scenarios\f3_aug21_bill_detail_war.txt --keep`. Then make a copy `f3_aug21_bill_detail_war_yes.txt` whose last three lines answer `Q1142_HAS_OTHER = 1` and tick row 2 (`Payment made directly to doctor/s and their secretary`) with an amount, `shot at_q1152_row2`.
Expected: `automation/shots/f3_aug21_bill_detail_war*/NNN_*.png` + `run.log`; the frames show the WAR stem on 97.1 / 97.2 / 115.1 / 115.2 where the WAR map already has a value (English where it does not — the Task 40 import fills those); the 97.2 frame shows `No, did not pay for any other expenses` (no `g)`); the 115.2 No path lands on Q116. Keep the frames as the PRE-import reference; the evidence copies are taken from the post-import re-run in Task 41. Note: popup click coordinates shift under translated labels (`scenarios/f1_aug17_intro51_fil.txt` :128-131) — if a step lands on the wrong control, adjust the `click x y` line and re-run.

- [ ] **Step 6: Record** — paste the coverage lines, verify/skip/r25-diff summary, the delta residue list and the compile-shot path into the wave note (`deliverables/CSPro/patch-notes/draft-f3-v6.1.0-aug21-translations.md`, renamed to `<date>-f3-v6.1.0-aug21-translations.md` in Task 42 once `stamp_version.py` has written the F3 date; sections `## English alignment` / `## Coverage before import`). No git steps (Carl commits generator/map changes). Wave 4b (Tasks 40–43) continues from this build.

---

## Wave 4b — F3 Aug-21 import + 6.1.0 ship

**Preconditions:** Tasks 35–39 done (F3 English aligned, compile green, WAR pre-import frames on disk); Day-0 tooling (Tasks 0–11) committed by Carl or at least present in the working tree. Anchors for F3 ALWAYS come from `--generator F3` (Task 1): the written `PatientSurvey.dcf` is post-neutralise and its Q66/Q88/Q143/Q162/Q172 labels no longer carry the `[facility_name_input]` text the paper prints. Run every block from `C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSPro` in PowerShell 5.1 with `$env:PYTHONIOENCODING='utf-8'`; `$root` and `$d = (Get-Content versions.json -Raw | ConvertFrom-Json).F3.date` as in Wave 4a.

### Task 40: F3 Aug-21 extraction (generator anchors), merge dry-run, overrides, apply, gates

**Files:**
- Create: `deliverables/CSPro/data/translations-official/out-aug21/F3/{fil,bcl,bis,ceb,war,hil,ilo}.json` + `{loc}_flagged.json` + `QA-REPORT.md` (gitignored; re-generated here against the Task 36–38 English — the Task 1 Step 5 run anchored on the pre-alignment labels)
- Modify: `deliverables/CSPro/F3/translations/{fil,bcl,bis,ceb,war,hil,ilo}.json` (values + `_meta.sources.aug21`, via `apply_aug21.py --apply` only)
- Modify: `deliverables/CSPro/data/translations-official/aug21-overrides.json` (`"F3"` section, only for re-introduced defects)
- Test: `deliverables/CSPro/F3/test_aug21_labels.py` (append)

**Interfaces:**
- Consumes: `anchor_extract.py --source DIR --instrument F3 --generator F3 --out DIR --live-maps DIR` (Task 1; side effect: `capture_source_dict` regenerates `PatientSurvey.dcf` — byte-identical on the Task 39 tree); `apply_aug21.py --only F3 [--seed FINDINGS] [--apply]` (Tasks 5–7; `WARN override 'keep' != current` = STOP); `scan_poisoned_keys.py --apply-report`; `run_aug21_gates.ps1 -Inst F3 -PreBridge N` (Task 7); FINDINGS.md §3/§4 F3 rows and `recovery_exclusions.json` `F3|…` ids (the Q47/Q96/Q98 ids are the ambiguous-prefix cases Task 6's `resolve_exclusion_id` disambiguates via `official_translations.json`)
- Produces: updated F3 maps with `_meta.sources.aug21`; `aug21-overrides.json["F3"]` entries; the seven post-import coverage lines (baseline before import = Task 39 Step 1: FIL60 BCL53 BIS55 CEB59 WAR58 HIL43 ILO53 of 1749)

- [ ] **Step 1: Write the failing test** (append to `F3/test_aug21_labels.py`)

```python
F3_MAPS = CSPRO / "F3" / "translations"
OUT_F3 = CSPRO / "data" / "translations-official" / "out-aug21" / "F3"
LOCS = ["fil", "bcl", "bis", "ceb", "war", "hil", "ilo"]
# keys whose English was reworded in Tasks 36-38: their June-5 values are stale and MUST
# be replaced by the Aug-21 cell (or sit in the flagged worklist) — never survive silently.
REWORDED = ["item:Q47_PHYSICIAN_CHECKUP", "item:Q69_USUAL_TRAVEL_HH", "item:Q96_SOURCES",
            "item:Q98_SOURCES", "item:Q972_SOURCES", "val:Q972_SOURCES_VS1:90",
            "item:Q1141_1", "item:Q1142_HAS_OTHER"]


@pytest.mark.parametrize("loc", LOCS)
def test_f3_map_carries_aug21_provenance(loc):
    m = json.loads((F3_MAPS / f"{loc}.json").read_text(encoding="utf-8"))
    src = m["_meta"].get("sources", {}).get("aug21")
    assert src, f"{loc}: apply_aug21.py --apply has not run for F3"
    assert set(src) >= {"date", "file", "n_written", "n_replaced", "n_overridden"}


@pytest.mark.parametrize("loc", ["fil", "hil", "ilo"])
def test_f3_reworded_keys_hold_aug21_value_or_are_flagged(loc):
    m = json.loads((F3_MAPS / f"{loc}.json").read_text(encoding="utf-8"))
    ex = json.loads((OUT_F3 / f"{loc}.json").read_text(encoding="utf-8"))
    fl = {r["key"] for r in json.loads((OUT_F3 / f"{loc}_flagged.json").read_text(encoding="utf-8"))}
    for k in REWORDED:
        if k in ex:
            assert m.get(k) == ex[k], f"{loc} {k}: map != Aug-21 extract"
        else:
            assert k in fl, f"{loc} {k}: neither extracted clean nor flagged"


def test_f3_hil_ilo_q66_no_longer_english():
    # Task 38 gave HIL/ILO a dialect fill; the import should also land the whole Q66 stem.
    for loc in ("hil", "ilo"):
        m = json.loads((F3_MAPS / f"{loc}.json").read_text(encoding="utf-8"))
        v = m.get("item:Q66_SAME_AS_USUAL", "")
        assert v and not v.startswith("66. Is "), f"{loc}: Q66 still English"
```

- [ ] **Step 2: Run test to verify it fails** — Run: `python -m pytest F3/test_aug21_labels.py -q -k "provenance or reworded or q66_no_longer"` Expected: FAIL — no `_meta.sources.aug21`; `out-aug21/F3/` is stale or absent; HIL/ILO Q66 English.

- [ ] **Step 3: Extract, baseline scans, dry-run + seed, overrides, apply**

```powershell
$root='C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development'
cd "$root/deliverables/CSPro"
$env:PYTHONIOENCODING='utf-8'
python data/translations-official/anchor_extract.py --source "$root/raw/Survey-Instruments-2026-08-21/Translations" --instrument F3 --generator F3 --out data/translations-official/out-aug21/F3 --live-maps F3/translations
git status --short F3/PatientSurvey.dcf                                                                                    # must be EMPTY (generator re-run was byte-identical)
python data/translations-official/scan_poisoned_keys.py --apply-report data/translations-official/aug21_pre_findings.json   # Task 6 step 5.1; record N_pre
python aug17-tools/bridge_check.py --check | Select-String "B-admin-leak|C-glued-fragments|^Total"                          # B/C row count -> $preBC (baseline had F3/bis 1, F3/hil 4, F3/ilo 3 rows in total 18 — classify A vs B/C)
python data/translations-official/apply_aug21.py --only F3 --unmatched --seed data/translations-official/aug21_pre_findings.json
```
Expected: extractor first line `F3: N anchors from F3; keys not in dcf: []`, seven rows with files; `differ` column explains the dry-run `replaced` counts. Review `QA-REPORT.md` (the `glued-short-label` share on the Ilocano paper — if > ~25 % of ILO flags, keep the 4-char floor but note it for Task 47) and `aug21_apply_diff.json[F3]`. Every `replaced` row is accepted unless it re-introduces a FINDINGS.md §3/§4 F3 defect (`BIS F3` and the `HIL`/`ILO` rows the bridge_check B/C baseline lists, the June-5 Male/Female swap class `val:Q5_SEX_VS1:*`, the Q47 four-row offset class, the Q96/Q98 `_SOURCES` vs `_PAY_SRC` cross-pairing class) — `--seed` prints the candidate rows and any `WARN unresolved exclusion F3|…: ambiguous:N` lines (resolve by hand from `aug21_apply_diff.json`, deciding per key). Paste confirmed rows into `aug21-overrides.json["F3"]` with the verbatim current value as `keep` (from `replaced[].was`) and a reason; then:

```powershell
python data/translations-official/aug21_overrides.py                 # OK
python data/translations-official/apply_aug21.py --only F3           # override column == rows pasted; NO 'WARN override' line
python data/translations-official/apply_aug21.py --only F3 --apply
.\data\translations-official\run_aug21_gates.ps1 -Inst F3 -PreBridge $preBC
python F3/generate_dcf.py
```
Expected: `APPLIED - diff written to …`; `GATES CLEAN - proceed to generate_dcf.py` (Task 7 Step 5 triage on any `GREW`); `generate_dcf.py` prints seven lines each ≥ the Task 39 baseline, HIL/ILO rising the most (the reworded keys now carry Aug-21 text under their new English). Record the seven lines.

- [ ] **Step 4: Run test to verify it passes** — Run: `python -m pytest F3/test_aug21_labels.py -q` Expected: `25 passed` (14 from Task 35 + 7 provenance + 3 reworded + 1 Q66). If `test_f3_hil_ilo_q66_no_longer_english` fails, `item:Q66_SAME_AS_USUAL` is in `{loc}_flagged.json` — the placeholder `[facility_name_input]` is part of the anchor and paper alike, so the usual cause is `contains-other-label` from Q67 bleed; hand-accept the span if it is the complete Q66 sentence (copy into `out-aug21/F3/{loc}.json`, drop the flagged row, re-apply) and record it.

- [ ] **Step 5: Verify/gate** — `python automation/verify_questions.py F3` → `=== per-question verification: F3 PASS`; `python -m pytest F3/test_aug21_labels.py aug17-tools/test_tools.py data/translations-official/test_apply_aug21.py -q` all green; provenance: `python -c "import json;print(json.load(open('F3/translations/hil.json',encoding='utf-8'))['_meta']['sources']['aug21'])"` prints the counters.

- [ ] **Step 6: Record** — wave note `draft-f3-v6.1.0-aug21-translations.md`: `## Merge` (dry-run table, overrides with reasons, unresolved exclusions and how settled, hand-accepted flagged rows), `## Gates` (scan per-reason pre/post, bridge B/C pre → post), `## Coverage` (before-import = Task 39 lines, after-import = this task's lines). Keep `out-aug21/F3/*_flagged.json` for the Task 45 worklist. No git step.

### Task 41: F3 rebuild with ICF/notes per language, compile, HIL desk scenario

**Files:**
- Modify (generated): `deliverables/CSPro/F3/PatientSurvey.dcf`, `.ent.apc`, `.fmf`, `.ent.qsf`
- Create: `deliverables/CSPro/F3/PatientSurvey_desktest_HIL.pff`, `deliverables/CSPro/automation/scenarios/f3_aug21_bill_detail_hil.txt`
- Create: `docs/uat-fix-evidence/<date>-aug21-translations/F3/{f3_q971_war,f3_q972_war,f3_q1151_war,f3_q1152_war,f3_q971_hil,f3_q66_hil,f3_icf_hil}.png`
- Test: gate commands below

**Interfaces:**
- Consumes: the four F3 generators; `F3/generate_qsf.py` per-language `OVERRIDES` (Task 11) + `notes.json`/`icf.json` (Tasks 8/10); `automation/verify_questions.py F3`, `skip_boundary_check.py F3`, `aug17-tools/r25_caption_check.py F3` (+ `r25_baseline_f3.txt`); `automation/cspro_compile_driver.py F3 --build --save`; `automation/csentry_runner.py <scenario> --keep`; `F3/PatientSurvey_WAR.pff` as the template for a HIL pff (`[Files]/[ExternalFiles]/[Parameters]` pattern, `Language=HIL`); `scenarios/f3_aug21_bill_detail_war.txt` (Task 39) and `f3_ghreorder_op.txt` (12-char casekey walk to Q88) + `f1_aug17_accredited_arm.txt:19-24` Check Box `tick_x/tick_y` rule
- Produces: a compile-clean F3 build carrying the Aug-21 maps + per-language consent; WAR and HIL desk frames of 97.1/97.2/115.1/115.2, Q66 and ICF screen 1 (HIL = the locale with the lowest baseline, 43 %)

- [ ] **Step 1: Regenerate + ICF probe**

```powershell
cd "$root/deliverables/CSPro"
python F3/generate_dcf.py; python F3/generate_apc.py; python F3/generate_fmf.py; python F3/generate_qsf.py
@'
import re, io
q = io.open("F3/PatientSurvey.ent.qsf", encoding="utf-8").read()
blk = q[q.index(".ICF_PART1"):q.index(".ICF_PART2")]
hil = re.search(r"\n          HIL: \|\n            (.*)", blk).group(1)
en = re.search(r"\n          EN: \|\n            (.*)", blk).group(1)
print("HIL differs from EN:", hil != en, "| 08/21/2026:", "08/21/2026" in en)
assert hil != en and "\n" not in hil
'@ | python -
```
Expected: `True True` (F3-Tagalog's header still says 06/05 on paper — the build keeps 08/21/2026 per Task 9).

- [ ] **Step 2: Static gates** — `python automation/verify_questions.py F3` (PASS), `python automation/skip_boundary_check.py F3` (OK + the waived pair), r25 `Compare-Object` against `F3/test_fixtures/r25_baseline_f3.txt` prints nothing new (Task 39 Step 2 commands verbatim).

- [ ] **Step 3: Fresh-Designer compile** — `Stop-Process -Name CSPro -Force -ErrorAction SilentlyContinue; python automation/cspro_compile_driver.py F3 --build --save` → `COMPILE-SHOT …\F3_compile.png`, Read it: `Compile Successful`.

- [ ] **Step 4: HIL pff + desk scenarios (WAR re-run + HIL)**

```powershell
(Get-Content F3/PatientSurvey_WAR.pff) -replace 'Language=WAR', 'Language=HIL' -replace 'desktest_war', 'desktest_hil' | Set-Content -Encoding ascii F3/PatientSurvey_desktest_HIL.pff
Copy-Item automation/scenarios/f3_aug21_bill_detail_war.txt automation/scenarios/f3_aug21_bill_detail_hil.txt
(Get-Content automation/scenarios/f3_aug21_bill_detail_hil.txt) -replace 'desktest_war', 'desktest_hil' -replace 'PatientSurvey_WAR\.pff', 'PatientSurvey_desktest_HIL.pff' -replace 'WARAY', 'HILIGAYNON' | Set-Content -Encoding utf8 automation/scenarios/f3_aug21_bill_detail_hil.txt
python automation/csentry_runner.py scenarios/f3_aug21_bill_detail_war.txt --keep
python automation/csentry_runner.py scenarios/f3_aug21_bill_detail_hil.txt --keep
```
Add to the HIL scenario, after the consent screen, `shot at_icf_hil` and, at Q66, `shot at_q66_hil` (pilot the keystrokes from `f3_ghreorder_op.txt`). Expected: frames under `automation/shots/f3_aug21_bill_detail_{war,hil}/`; 97.1 / 97.2 / 115.1 / 115.2 stems now render in WAR and HIL (Aug-21 values), Q66 in HIL shows `ini nga pasilidad` inside a HIL sentence (or the full HIL stem if `item:Q66_SAME_AS_USUAL` landed), the ICF screen in HIL reads Hiligaynon with the 08/21/2026 stamp. Popup click coordinates shift under translated labels — adjust `click x y` lines and re-run as needed. Copy the frames:

```powershell
$d = Get-Date -Format yyyy-MM-dd
$ev = "$root/docs/uat-fix-evidence/$d-aug21-translations/F3"; New-Item -ItemType Directory -Force $ev | Out-Null
# pick the frames by run.log step name and copy as f3_q971_war.png, f3_q972_war.png, f3_q1151_war.png, f3_q1152_war.png, f3_q971_hil.png, f3_q66_hil.png, f3_icf_hil.png
```

- [ ] **Step 5: Verify/gate** — Read each copied PNG: non-English stems on the four bill-detail screens in both locales; `Test-Path "$root/docs/uat-fix-evidence/2026-08-2x-aug21-translations"` is `False`.

- [ ] **Step 6: Record** — wave note `## Desk render` with the frame paths and any hand-accepted keys revealed by the render (a stem that reads English although the map has a value = key mismatch → check `aug21_apply_diff.json[F3][loc].unmatched`).

### Task 42: F3 version bump 6.1.0, publish, deploy, byte-verify, patch note, evidence

**Files:**
- Modify: `deliverables/CSPro/versions.json` (`"F3": … "6.0.3"` → `6.1.0`, via `stamp_version.py` only)
- Create: `deliverables/CSPro/patch-notes/<date>-f3-v6.1.0-aug21-translations.md` (`<date>` = the F3 `date` field stamp_version wrote; the Task 39/40 draft renamed)
- Create: `docs/uat-fix-evidence/<date>-aug21-translations/F3/byte-verify.txt`, `00-deploy-result.png`, `README.md`
- Test: `python automation\stamp_version.py show` exit 0; `python automation\auto_deploy.py F3 --deploy` exit 0; `byte_verify_aug21.py F3` exit 0

**Interfaces:**
- Consumes: `py automation/stamp_version.py bump F3 --minor --type changed --notes "…"` (hand-parsed `sys.argv`, `--notes` last; regenerates `RELEASE-NOTES.md` + WHATS-NEW via `release_notes.py`), `automation/csweb_deploy_designer.py open|filemenu|click X Y` (**`cmd_open` launches on `KEY = os.environ.get("DEPLOY_KEY", "F1")` (:31) and calls `_kill_cspro()` first (:50)** — `DEPLOY_KEY` MUST be `F3`), `automation/auto_deploy.py F3 --deploy` (instrument-locked to package 'Patient Survey'; needs `CSPRO_ADMIN_USER` + `CSPRO_ADMIN_PASS`/`_FILE` env), `aug17-tools/byte_verify_aug21.py F3 …` (Task 19, `PROBE_KEYS["F3"]`), patch-note template `.claude/skills/cspro-patch-fix/SKILL.md:160-165`, CSWeb box `root@207.148.65.115` (ssh READ commands were denied by the permission classifier on 2026-08-25, scp allowed)
- Produces: F3 6.1.0 stamped pff Description ` [DEV]` + qsf footer; deploy shots under `automation/shots/deploy/`; `byte-verify.txt`; the patch-note file Carl's loop posts to `#f3-uat`; evidence README

- [ ] **Step 1: Bump (MINOR — wording + translations only, codes unchanged; no data-shape break so NO `--breaking`)**

```powershell
cd "C:\Users\analy\Documents\analytiflow\1_Projects\ASPSI-DOH-CAPI-CSPro-Development\deliverables\CSPro"
python automation\stamp_version.py bump F3 --minor --type changed --notes "Aug-21 paper alignment: Q47 single stem, Q69/Q94/Q96/Q98 stems, 97.2/115.1/115.2 labels and option text re-synced verbatim (codes unchanged); Hiligaynon/Ilocano facility-name dialect phrase; Aug-21 translations imported for all 7 languages; consent screens and section intros per language"
python automation\stamp_version.py show
$d = (Get-Content versions.json -Raw | ConvertFrom-Json).F3.date
"F3 stamp date = $d"
```
Expected: `F3 6.0.3 -> 6.1.0`, `RELEASE-NOTES.md` regenerated, `show` reports no drift (exit 0); `$d` is the date used for the patch-note filename, the evidence folder (must equal the Task 41 `$d` — if the day rolled over, rename the folder) and the "You're on the new build when…" line. The bump itself re-runs `generate_qsf.py` (restamp + regen).

- [ ] **Step 2: Re-compile after the stamp and publish from a fresh Designer — on F3, not the F1 default**

```powershell
Stop-Process -Name CSPro -Force -ErrorAction SilentlyContinue
python automation\cspro_compile_driver.py F3 --build --save
$env:DEPLOY_KEY = "F3"          # csweb_deploy_designer.py:31 defaults to F1 and `open` kills any running Designer
python automation\csweb_deploy_designer.py open
python automation\csweb_deploy_designer.py filemenu
```
Read the two shots (confirm the title bar shows PatientSurvey), click the `Deploy to CSWeb…` item with `python automation\csweb_deploy_designer.py click X Y deploy` (coordinates from the filemenu shot), then:

```powershell
$env:CSPRO_ADMIN_USER='admin'; $env:CSPRO_ADMIN_PASS_FILE='C:/Users/analy/.secrets/csweb_admin.txt'
python automation\auto_deploy.py F3 --deploy
```
Expected: exit 0; `automation/shots/deploy/` shows the PSGC 8-file list and the "successfully" popup; package name = Patient Survey. (If `auto_deploy` reports NO dialog / exit 1, the Designer is on the wrong instrument — re-check `$env:DEPLOY_KEY`.)

- [ ] **Step 3: Byte-verify the deployed package carries the new labels** (2026-08-14 method — `bytes.find` on the utf-16-le encoding, never a whole-blob decode). The package on the box is `PatientSurvey.zip` under `/opt/app/lamp/www/csweb/files/apps/`; because ssh reads may be blocked by the permission classifier, rely on the scp exit code:

```powershell
$d = (Get-Content versions.json -Raw | ConvertFrom-Json).F3.date
scp root@207.148.65.115:/opt/app/lamp/www/csweb/files/apps/PatientSurvey.zip $env:TEMP\PatientSurvey.zip
if ($LASTEXITCODE -ne 0) { throw "scp failed - wrong package path/name, NOT a content miss" }
$ev = "..\..\docs\uat-fix-evidence\$d-aug21-translations\F3"; New-Item -ItemType Directory -Force $ev | Out-Null
Get-ChildItem automation/shots/deploy | Sort-Object LastWriteTime | Select-Object Name, LastWriteTime   # pick the F3 result-dialog PNG
$shot = "automation/shots/deploy/<the-one-F3-result-file>.png"
py aug17-tools\byte_verify_aug21.py F3 $env:TEMP\PatientSurvey.zip F3\translations "$ev\byte-verify.txt" --version v6.1.0 --deploy-shot $shot "$ev\00-deploy-result.png"
@'
import os, zipfile
z = zipfile.ZipFile(os.path.join(os.environ["TEMP"], "PatientSurvey.zip"))
print("members:", z.namelist())
blob = b"".join(z.read(n) for n in z.namelist() if n.lower().endswith((".pen", ".dcf")))
for s in ("packages for the following health services", "were NOT included in the outpatient bill",
          "No, did not pay for any other expenses", "daytoy a pasilidad", "ini nga pasilidad"):
    print(s, "->", "FOUND" if (blob.find(s.encode("utf-16-le")) >= 0 or blob.find(s.encode("utf-8")) >= 0) else "MISSING")
'@ | python - | Tee-Object -Variable bv
$bv | Out-File -Encoding utf8 -Append "$ev\byte-verify.txt"
```
Expected: `RESULT: ALL PASS` from the tool (map probes for the five F3 keys × 7 locales + `v6.1.0` footer) and five `FOUND` lines from the English/dialect-phrase probe (the `.pen` is bzip2-compressed — the tool decompresses; the inline probe reads the raw members, so a MISSING there while the tool passes means the string sits in the compressed region only: trust the tool). A tool `MISS` on a value present in the map = stale package → redo Step 2, never patch the zip.

- [ ] **Step 4: Write the patch note** — `deliverables/CSPro/patch-notes/<date>-f3-v6.1.0-aug21-translations.md` with `<date>` = `$d` (template from `cspro-patch-fix/SKILL.md:160-165`; leads with remove + re-add; MINOR wording — the MAJOR/data-shape warning from the F1 v4.0.0 note is NOT used because no code or record changed). **Spec erratum, fix it here so spec and plan agree:** in `docs/superpowers/specs/2026-08-25-aug21-translations-design.md` *Deployment & cutover*, replace the sentence `F3's note carries the MAJOR/data-shape warning verbatim from the F1 v4.0.0 note.` with `F3's note states that no codes changed (Decision 4, corrected 2026-08-25 evening: 6.1.0 MINOR).` — one-line doc edit, left in the working tree for Carl's commit.

```markdown
<!-- deliverables/CSPro/patch-notes/<date>-f3-v6.1.0-aug21-translations.md — post to #f3-uat; <date> = versions.json F3.date -->
🔧 **Patient Survey (F3) — patch deployed (v6.1.0)**
*Changed:* Question wording now matches the DOH-submitted Aug-21 paper: Q47 reads as one stem
("Are you aware that there are PhilHealth packages for the following health services:") with the
four services; Q69, Q94, Q96 and Q98 stems reworded; 97.2 says "NOT included" and its No option
reads "No, did not pay for any other expenses"; 115.1/115.2 rows now show the full question
with each item. All seven language versions now carry ASPSI's revised Aug-21 translations
(coverage FIL <?>%, BCL <?>%, BIS <?>%, CEB <?>%, WAR <?>%, HIL <?>%, ILO <?>%, up from
61/54/56/59/58/43/53). Hiligaynon and Ilocano now use a dialect phrase ("ini nga pasilidad" /
"daytoy a pasilidad") instead of English "this facility" where the facility name is filled in.
The consent screens and the section intros now read in the selected language (Aug-21 cleared
translations); paragraphs without a cleared translation stay English.
**No answer codes changed** — data collected on 6.0.x lines up unchanged.
*To get it:* In CSEntry, **remove Patient Survey, then Add Application → from CSWeb**. You're on
the new build when the app list shows **v6.1.0 (<date>) [DEV]**. (⋮ → Update Installed
Applications is unreliable.)
Cases already in progress are unaffected.
*Still English on some screens?* That item had no translation in ASPSI's cleared Aug-21 source
for that language — not a build defect; the list has gone back to ASPSI's translators.
Evidence: <raw.githubusercontent.com SHA-pinned URLs for f3_q971_war.png, f3_q66_hil.png, byte-verify.txt>
Tablet: <SHA-pinned URLs for f3_q47_hil_tablet.png, f3_q972_war_tablet.png — appended by Task 43 Step 5 from the DEPLOYED package>
```
Replace both `<date>` tokens with `$d` and every `<?>`/`<URL>` before saving (`(Get-Content template) -replace '<date>', $d`).

- [ ] **Step 5: Evidence README + commit; verify/gate**

```markdown
# Aug-21 translations — F3 fix evidence (wave 4, v6.1.0)

**Driver:** ASPSI Aug-21 revised instruments (raw/Survey-Instruments-2026-08-21). **Ships as:** F3 v6.1.0 (dev channel).
**What changed:** Q47/Q69/Q94/Q96/Q98 + 97.2/115.1/115.2 English aligned to the paper (codes unchanged); HIL/ILO facility fill; 7-locale Aug-21 import (coverage FIL61→?, …); consent + intros per language.
**Method:** deployed package pulled from CSWeb (`files/apps/PatientSurvey.zip`), byte-verified, then sideloaded to the `capi_tablet` AVD for the `*_tablet.png` rows (Task 43 — the tablet proof, same method as F1/F4); the csentry_runner desk scenarios `f3_aug21_bill_detail_{war,hil}.txt` on the compiled build are supplementary.

| file | what it shows |
|---|---|
| `00-deploy-result.png` | CSWeb deploy dialog, v6.1.0 |
| `f3_q971_war.png`, `f3_q972_war.png`, `f3_q1151_war.png`, `f3_q1152_war.png` | bill-detail screens in Waray (tick / No / None paths) |
| `f3_q971_hil.png`, `f3_q66_hil.png`, `f3_icf_hil.png` | Hiligaynon (lowest-coverage locale): 97.1, Q66 facility fill, consent screen 1 |
| `byte-verify.txt` | deployed .pen probed for map values (utf-16-le bytes.find, aug17-tools/byte_verify_aug21.py) + v6.1.0 footer + English/dialect phrase probe |
```
```powershell
git add "docs/uat-fix-evidence/$d-aug21-translations/F3"
git commit -m "evidence: F3 v6.1.0 Aug-21 alignment + translations desk shots + byte-verify"
git push
python automation\stamp_version.py show                 # exit 0
python automation\verify_questions.py F3                # PASS (post-stamp regen)
Select-String "<\?>|<date>|<URL|2026-08-2x" patch-notes\$d-f3-v6.1.0-aug21-translations.md   # nothing
Test-Path patch-notes\draft-f3-*                                                             # False (draft renamed)
Get-ChildItem -Recurse -Filter "*2026-08-2x*" ..\..\docs                # nothing
git status --short F3 versions.json patch-notes                          # only the expected generator/artefact/versions/patch-note changes — for Carl's commit, do not commit
```

- [ ] **Step 6: Record** — prepend a dated entry to `log.md` (per `cspro-patch-fix` step 7): F3 6.1.0 wording alignment + Aug-21 import; residue list from Task 39 Step 3; coverage before/after; r25 baseline-vs-after diff (empty); overrides; evidence SHA; open items "115.x Shape-B conversion deferred (Carl 2026-08-25)" and "r25 GPS NO-PROMPT residue pre-dates this wave — separate fix". Task 43 (tablet locale shots from the deployed package) completes the wave's evidence; Wave 5 (Tasks 44–47) follows.

---

### Task 43: F3 emulator locale shots from the DEPLOYED package (Q47 + 97.2 in HIL and WAR, ICF in HIL)

Why this task exists: the spec's Verification design item 3 and Waves row 4 ("as wave 1") require device evidence from the **deployed** package, and the memory rule is "tablet proof REQUIRED". Task 41's desk frames come from the locally compiled build BEFORE the Task 42 deploy, and Task 42 only byte-verifies. F1 (Task 20) and F4 (Task 33) sideload the pulled zip to the `capi_tablet` AVD; F3 now does the same. The desk frames stay as supplementary evidence.

**Files:**
- Create: `docs/uat-fix-evidence/<date>-aug21-translations/F3/00-app-list-f3-6.1.0.png`, `f3_icf_hil_tablet.png`, `f3_q47_hil_tablet.png`, `f3_q47_war_tablet.png`, `f3_q972_hil_tablet.png`, `f3_q972_war_tablet.png`
- Modify: `docs/uat-fix-evidence/<date>-aug21-translations/F3/README.md` (Task 42 — append the tablet rows)
- Modify: `deliverables/CSPro/patch-notes/<date>-f3-v6.1.0-aug21-translations.md` (fill the `Tablet:` evidence line)
- Test: none (PNG contents checked by eye via the Read tool)

**Interfaces:**
- Consumes: `$env:TEMP\PatientSurvey.zip` (the served package pulled by `scp` in Task 42 Step 3 — the SAME bytes that were byte-verified); the 2026-08-17 capture method (memory `reference_uat_fix_evidence.md` / `reference_csentry_pen_sideload.md`, mirrored from Task 33): `emulator -avd capi_tablet -no-snapshot -gpu host`; sideload `.pen + .pff (+ psgc_* copied on-device)` into `/storage/emulated/0/Android/data/gov.census.cspro.csentry/files/csentry/PatientSurvey/`; cold-boot perms fix `adb root; chown -R u0_a192:ext_data_rw; chmod -R 770`; `adb shell screencap -p /sdcard/cap.png` + `adb pull` (never PowerShell `>`); CSEntry's in-app language menu by hand; the 12-digit PSGC-gated case key (memory `reference_cspro_casekey_psgc_gate`) — reuse the desk walk's key from `automation/scenarios/f3_ghreorder_op.txt` (`casekey 04 03 403 02 001`, facility `0403403001`, `RHU BINAN`); `PATIENT_TYPE = Outpatient` so Section G (97.x) is reached; `versions.json["F3"].date` = `$d` (Task 42)
- Produces: six SHA-pinned tablet PNGs + README rows + the `Tablet:` line of the patch note

- [ ] **Step 1: Boot + sideload the deployed package**

```powershell
$root='C:/Users/analy/Documents/analytiflow/1_Projects/ASPSI-DOH-CAPI-CSPro-Development'
cd "$root/deliverables/CSPro"
$d = (Get-Content versions.json -Raw | ConvertFrom-Json).F3.date
$ev = "$root/docs/uat-fix-evidence/$d-aug21-translations/F3"
Test-Path "$env:TEMP/PatientSurvey.zip"          # True - pulled in Task 42 Step 3; if False re-run that scp line, never rebuild locally
$adb = "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe"
Start-Process "$env:LOCALAPPDATA\Android\Sdk\emulator\emulator.exe" -ArgumentList @("-avd","capi_tablet","-no-snapshot","-gpu","host")
& $adb wait-for-device; & $adb shell input keyevent 224
Expand-Archive -Force $env:TEMP/PatientSurvey.zip $env:TEMP/PatientSurvey
$base = "/storage/emulated/0/Android/data/gov.census.cspro.csentry/files/csentry"
$dst = "$base/PatientSurvey"
& $adb shell mkdir -p $dst
Get-ChildItem $env:TEMP/PatientSurvey -Recurse -Include *.pen,*.pff,*.dcf,psgc_*,review.html | ForEach-Object { & $adb push $_.FullName "$dst/" }
& $adb shell "ls $base"                                          # if psgc_* were not in the zip, copy them from an installed folder:
& $adb shell "cp $base/HouseholdSurvey/psgc_* $dst/ 2>/dev/null; ls $dst"
& $adb root; & $adb shell "chown -R u0_a192:ext_data_rw /data/media/0/Android/data/gov.census.cspro.csentry/files/csentry/PatientSurvey; chmod -R 770 /data/media/0/Android/data/gov.census.cspro.csentry/files/csentry/PatientSurvey"
& $adb shell monkey -p gov.census.cspro.csentry -c android.intent.category.LAUNCHER 1
```
Expected: the CSEntry app list shows `Patient Survey (F3) - v6.1.0 ($d) [DEV]` — capture it as `00-app-list-f3-6.1.0.png` (Step 3). If no installed folder carries `psgc_*`, `adb push` the 8 files from `deliverables/CSPro/F3/` (gitignored, on disk). "Loading" forever = the PSGC copy failed (FACILITY_LOOKUP startup loop); black screencap = `adb shell input keyevent 224` then `adb shell service call SurfaceFlinger 1008 i32 1` and retry.

- [ ] **Step 2: Navigate once per language (HIL first, then WAR)**

Open Patient Survey → ⋮ → Language → **Hiligaynon** → Add case: the first screen is ICF part 1 → shoot `f3_icf_hil_tablet` (Hiligaynon consent + `08/21/2026`). Continue: case key `04 03 403 02 001`, facility `0403403001` / `RHU BINAN`, Result-of-Visit Completed, `PATIENT_TYPE` = Outpatient, minimal Section A–C answers (`JUAN DELA CRUZ`, sex 6-key path and birth year `1991` as in `f3_ghreorder_op.txt`), through Section D to **Q47** (the four PhilHealth-package rows under the single stem) → shoot `f3_q47_hil_tablet`; ⋮ → Language → **Waray** → shoot `f3_q47_war_tablet`. Continue on the outpatient path through Sections E/F/G with the answers of `scenarios/f3_aug21_bill_detail_war.txt` (Q92 Out-of-pocket + amounts … Q97 amount, 97.1 tick row 1 + amount) until **97.2** → shoot `f3_q972_war_tablet`; ⋮ → Language → Hiligaynon → shoot `f3_q972_hil_tablet`. Break off / discard the test case afterwards (do not sync it: the tablet is offline, CSWeb sync was not configured on this AVD).

- [ ] **Step 3: Capture (binary-safe; run in an interactive PowerShell window, not the tool — `Read-Host` paces the shots)**

```powershell
foreach ($n in "00-app-list-f3-6.1.0","f3_icf_hil_tablet","f3_q47_hil_tablet","f3_q47_war_tablet","f3_q972_war_tablet","f3_q972_hil_tablet") {
  Read-Host "Screen ready for $n ? press Enter"
  & $adb shell screencap -p /sdcard/cap.png; & $adb pull /sdcard/cap.png "$ev/$n.png"; & $adb shell rm /sdcard/cap.png
}
& $adb emu kill
```
Expected: 6 PNGs > 1000 bytes each. Read each: `00` shows `v6.1.0 ($d) [DEV]`; `f3_q47_*` show the single Aug-21 stem (`Are you aware that there are PhilHealth packages…` translated) with four rows, HIL text in `_hil`, WAR text in `_war`; `f3_q972_*` show the 97.2 stem with `NOT included` translated and the `No, did not pay for any other expenses` option in the locale; `f3_icf_hil_tablet` shows Hiligaynon consent paragraph 1 and `08/21/2026`. Any English stem on a key the map holds → re-check `byte-verify.txt` (Task 42) for that locale before suspecting the map: the tablet renders the SAME bytes that were probed.

- [ ] **Step 4: README rows + commit (sanctioned evidence write)**

Append to `$ev/README.md` (the Task 42 table):

```markdown
| `00-app-list-f3-6.1.0.png` | CSEntry app list on the `capi_tablet` AVD showing `Patient Survey (F3) - v6.1.0 (<date>) [DEV]` — sideloaded from the DEPLOYED `PatientSurvey.zip` |
| `f3_icf_hil_tablet.png` | ICF screen 1 in Hiligaynon on the tablet (Aug-21 consent + 08/21/2026 stamp) |
| `f3_q47_hil_tablet.png`, `f3_q47_war_tablet.png` | Q47 single stem + four PhilHealth-package rows, Hiligaynon / Waray, deployed package on the tablet |
| `f3_q972_hil_tablet.png`, `f3_q972_war_tablet.png` | 97.2 ("NOT included in the outpatient bill") + its No option, Hiligaynon / Waray, deployed package on the tablet |
```
```powershell
cd $root
git add "docs/uat-fix-evidence/$d-aug21-translations/F3"
git commit -m "evidence: F3 v6.1.0 tablet locale shots from the deployed package (Q47 + 97.2 HIL/WAR, ICF HIL)"
git push
git rev-parse HEAD
```
Expected: commit SHA printed; `https://raw.githubusercontent.com/<org>/<repo>/<sha>/docs/uat-fix-evidence/<date>-aug21-translations/F3/f3_q47_hil_tablet.png` resolves.

- [ ] **Step 5: Verify/gate** — fill the `Tablet:` line of `deliverables/CSPro/patch-notes/$d-f3-v6.1.0-aug21-translations.md` with the SHA-pinned URLs of `f3_q47_hil_tablet.png` and `f3_q972_war_tablet.png`; then `Select-String "<\?>|<date>|<URL|2026-08-2x|<SHA" patch-notes\$d-f3-v6.1.0-aug21-translations.md` returns nothing; `Test-Path "$root/docs/uat-fix-evidence/2026-08-2x-aug21-translations"` is `False`; `git status --short docs/uat-fix-evidence` is empty.

- [ ] **Step 6: Record** — add the SHA + the six file names to the `log.md` entry of Task 42 (same dated heading; one bullet "tablet proof from the deployed package"). Wave 4 closes; Wave 5 (Tasks 44–47) follows.

---

## Wave 5 — Close-out: coverage table, translator worklist, (optional) runtime-message sheet, status hand-off

All four instruments are live. This wave produces the artefacts ASPSI and Carl need to see where the translation set stands, without touching any build. Run from `deliverables/CSPro` in PowerShell 5.1 with `$env:PYTHONIOENCODING='utf-8'`. The date in file names below is the close-out date (`2026-08-28` per the wave plan; use the real day).

### Task 44: `translation_coverage.py` + `TRANSLATION-STATUS-2026-08-28.md`

**Files:**
- Create: `deliverables/CSPro/automation/translation_coverage.py`
- Create: `deliverables/CSPro/automation/test_translation_coverage.py`
- Create: `deliverables/CSPro/TRANSLATION-STATUS-2026-08-28.md`

**Interfaces:**
- Consumes: the `apply_translations` summary lines `    {CODE}: {matched}/{total} labels translated ({pct}%)` printed by `F{1,3,4}/generate_dcf.py` (cspro_helpers.py:1239); `deliverables/F2/PWA/app/src/generated/items.ts` label objects (same regexes as `scripts/f2-coverage.py`, Task 22); `notes_lookup.coverage()`, `icf_content.coverage()`; the before-values recorded in Tasks 16, 22, 24, 39 (baseline JSON below)
- Produces: `parse_generator_summary(text) -> dict[CODE, (matched, total, pct)]`; `f2_label_coverage(items_ts_path) -> (total, dict[loc, n])`; `render_table(before, after) -> str` (markdown, one row per instrument × locale, before → after, delta); CLI `python automation/translation_coverage.py --before baseline.json --out TRANSLATION-STATUS-2026-08-28.md` (runs the three generators' summaries by importing `apply_translations` on the pre-apply dictionary — no file writes — and reads items.ts)

- [ ] **Step 1: Write the failing test**

```python
# deliverables/CSPro/automation/test_translation_coverage.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import translation_coverage as tc  # noqa: E402

SUMMARY = """Languages: EN, FIL, BCL, BIS, CEB, WAR, HIL, ILO
    FIL: 1104/1363 labels translated (81%)
    BCL: 1090/1363 labels translated (80%)
"""


def test_parse_generator_summary():
    assert tc.parse_generator_summary(SUMMARY) == {"FIL": (1104, 1363, 81), "BCL": (1090, 1363, 80)}


def test_f2_label_coverage(tmp_path):
    p = tmp_path / "items.ts"
    p.write_text("label: { en: 'A', fil: 'a', ceb: 'b' }, label: { en: 'B', fil: 'c' }", encoding="utf-8")
    total, per = tc.f2_label_coverage(p)
    assert total == 2 and per["fil"] == 2 and per["ceb"] == 1 and per["bcl"] == 0


def test_render_table_shows_delta():
    before = {"F1": {"FIL": 67}, "F2": {"fil": 75}}
    after = {"F1": {"FIL": 81}, "F2": {"fil": 88}}
    md = tc.render_table(before, after)
    assert "| F1 | FIL | 67% | 81% | +14 |" in md and "| F2 | fil | 75% | 88% | +13 |" in md
```

- [ ] **Step 2: Run test to verify it fails** — `python -m pytest automation/test_translation_coverage.py -q` → `ModuleNotFoundError: translation_coverage`.

- [ ] **Step 3: Write minimal implementation**

```python
#!/usr/bin/env python3
"""translation_coverage.py — before/after coverage table for the Aug-21 import (Wave 5).

    python automation/translation_coverage.py --before automation/aug21_coverage_baseline.json --out TRANSLATION-STATUS-2026-08-28.md

Before = the per-locale % recorded at the start of each wave (Tasks 16/22/24/39). After = measured
now: F1/F3/F4 by running apply_translations() on each generator's pre-apply dictionary and
parsing its summary print (NO files are written — capture_source_dict is not used, the
generator's build_* function is called directly); F2 by counting label objects in items.ts.
"""
import argparse, contextlib, importlib, io, json, os, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CSPRO = HERE.parent
REPO = CSPRO.parents[1]
sys.path.insert(0, str(CSPRO))
LINE = re.compile(r"^\s*([A-Z]{3}): (\d+)/(\d+) labels translated \((\d+)%\)", re.M)
BUILDERS = {"F1": "build_dictionary", "F3": "build_f3_dictionary", "F4": "build_f4_dictionary"}
F2_ITEMS = REPO / "deliverables" / "F2" / "PWA" / "app" / "src" / "generated" / "items.ts"
F2_LOCS = ["fil", "ceb", "bis", "ilo", "hil", "war", "bcl"]


def parse_generator_summary(text):
    return {m.group(1): (int(m.group(2)), int(m.group(3)), int(m.group(4))) for m in LINE.finditer(text)}


def f2_label_coverage(items_ts_path):
    s = Path(items_ts_path).read_text(encoding="utf-8")
    total = len(re.findall(r"\ben: '", s))
    return total, {l: len(re.findall(r"\b" + l + r": '", s)) for l in F2_LOCS}


def cspro_after(inst):
    """Run apply_translations on the generator's pre-apply dict; return {CODE: pct}."""
    from cspro_helpers import apply_translations
    sys.path.insert(0, str(CSPRO / inst))
    sys.modules.pop("generate_dcf", None)
    gen = importlib.import_module("generate_dcf")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        apply_translations(getattr(gen, BUILDERS[inst])(), CSPRO / inst / "translations")
    sys.path.remove(str(CSPRO / inst)); sys.modules.pop("generate_dcf", None)
    return {code: pct for code, (_m, _t, pct) in parse_generator_summary(buf.getvalue()).items()}


def render_table(before, after):
    rows = ["| instrument | locale | before | after | delta |", "|---|---|---|---|---|"]
    for inst in sorted(set(before) | set(after)):
        for loc in sorted(set(before.get(inst, {})) | set(after.get(inst, {}))):
            b, a = before.get(inst, {}).get(loc), after.get(inst, {}).get(loc)
            d = f"{a - b:+d}" if (a is not None and b is not None) else ""
            rows.append(f"| {inst} | {loc} | {'' if b is None else str(b) + '%'} | {'' if a is None else str(a) + '%'} | {d} |")
    return "\n".join(rows)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--before", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    before = json.loads(Path(a.before).read_text(encoding="utf-8"))
    after = {inst: cspro_after(inst) for inst in BUILDERS}
    total, per = f2_label_coverage(F2_ITEMS)
    after["F2"] = {l: round(100 * n / total) for l, n in per.items()}
    import notes_lookup, icf_content
    body = ["# Translation status after the Aug-21 import", "",
            "Coverage = keys present in the map (label arrays for F1/F3/F4; label objects of "
            f"{total} for F2). Presence, not linguistic quality — the flagged worklist "
            "(translator-worklist-aug21.xlsx) lists what is still English and why.", "",
            render_table(before, after), "",
            f"Notes layer (notes_lookup.coverage): {notes_lookup.coverage()}",
            f"ICF paragraphs (icf_content.coverage): {icf_content.coverage()}", ""]
    Path(a.out).write_text("\n".join(body) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(body))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Baseline JSON `automation/aug21_coverage_baseline.json` (the values recorded at wave starts):

```json
{
  "F1": {"FIL": 67, "BCL": 67, "BIS": 67, "CEB": 63, "WAR": 67, "HIL": 66, "ILO": 62},
  "F3": {"FIL": 61, "BCL": 54, "BIS": 56, "CEB": 59, "WAR": 58, "HIL": 43, "ILO": 53},
  "F4": {"FIL": 60, "BCL": 62, "BIS": 61, "CEB": 64, "WAR": 66, "HIL": 50, "ILO": 60},
  "F2": {"fil": 75, "ceb": 78, "bis": 78, "ilo": 78, "hil": 75, "war": 80, "bcl": 77}
}
```

- [ ] **Step 4: Run test to verify it passes** — `python -m pytest automation/test_translation_coverage.py -q` → `3 passed`.

- [ ] **Step 5: Verify/gate** — `python automation/translation_coverage.py --before automation/aug21_coverage_baseline.json --out TRANSLATION-STATUS-2026-08-28.md` Expected: a 28-row table (4 instruments × 7 locales), every `delta` ≥ 0, the F2 `after` row equal to `scripts/f2-coverage.py` (Task 22), the F1/F3/F4 `after` rows equal to the lines recorded in Tasks 18, 28 and 39; `git status --short F1 F3 F4` unchanged by the run (no generator file writes). Append to the status file by hand: the per-instrument shipped versions (F1 4.1.0 / F2 m4 / F4 3.2.0 / F3 6.1.0) with deploy dates and evidence folder paths, the override count per instrument with a link to `aug21-overrides.json`, and the known source defects for ASPSI (F1-Tagalog ICF paragraph-2 English line, F3-Tagalog 06/05 header, monolingual F4 PDFs from Task 29 Step 0, echo-english cells).

- [ ] **Step 6: Record** — the status file is Carl's to commit; note its path in `log.md`.

### Task 45: Translator worklist export (`export_worklist.py`)

**Files:**
- Create: `deliverables/CSPro/data/translations-official/export_worklist.py`
- Create: `deliverables/CSPro/translator-worklist-aug21.xlsx`, `deliverables/CSPro/translator-worklist-aug21.csv`
- Test: `deliverables/CSPro/data/translations-official/test_export_worklist.py`

**Interfaces:**
- Consumes: `out-aug21/{F1,F3,F4}/{loc}_flagged.json` (`[{key, en, tr, flags}]`, Task 1) and `out-aug21/F2/{loc}_flagged.json` (`[{en, tr, flags}]`, Task 14); `aug21-overrides.json` (rows kept by override are listed with their reason); optional `aug21_apply_diff.json` (`unmatched` anchors per locale, from a `--unmatched` dry run) ; `openpyxl` for the xlsx (fallback: csv only if not installed)
- Produces: `collect_flagged(out_root, overrides_path, report_path=None) -> list[dict]` rows `{instrument, locale, key, english, extracted, flags, status}` with `status ∈ {flagged, override, unmatched, echo-english}`; `write_xlsx(rows, path)`, `write_csv(rows, path)`; CLI `python export_worklist.py [--out-root out-aug21] [--xlsx PATH] [--csv PATH]`

- [ ] **Step 1: Write the failing test**

```python
# deliverables/CSPro/data/translations-official/test_export_worklist.py
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import export_worklist as ew  # noqa: E402


def test_collect_flagged_merges_cspro_f2_and_overrides(tmp_path):
    (tmp_path / "F1").mkdir(); (tmp_path / "F2").mkdir()
    (tmp_path / "F1" / "fil_flagged.json").write_text(json.dumps(
        [{"key": "item:Q1", "en": "1. Name", "tr": "", "flags": ["empty"]},
         {"key": "item:Q2", "en": "2. Sex", "tr": "2. Sex", "flags": ["echo-english"]}]), encoding="utf-8")
    (tmp_path / "F2" / "bcl_flagged.json").write_text(json.dumps(
        [{"en": "Administrator", "tr": "Administrator", "flags": ["echo-english"]}]), encoding="utf-8")
    ov = tmp_path / "ov.json"
    ov.write_text(json.dumps({"F1": {"val:Q9_VS1:2": {"keep": "Dire", "reason": "swap"}},
                              "F2": {"fil": {"No": {"keep": None, "reason": "junk"}}}}), encoding="utf-8")
    rows = ew.collect_flagged(tmp_path, ov)
    by = {(r["instrument"], r["locale"], r["key"]): r for r in rows}
    assert by[("F1", "fil", "item:Q1")]["status"] == "flagged"
    assert by[("F1", "fil", "item:Q2")]["status"] == "echo-english"
    assert by[("F2", "bcl", "Administrator")]["status"] == "echo-english"
    assert by[("F1", "*", "val:Q9_VS1:2")]["status"] == "override" and by[("F1", "*", "val:Q9_VS1:2")]["flags"] == "swap"
    assert by[("F2", "fil", "No")]["status"] == "override"


def test_write_csv_roundtrip(tmp_path):
    rows = [{"instrument": "F1", "locale": "fil", "key": "item:Q1", "english": "1. Name",
             "extracted": "", "flags": "empty", "status": "flagged"}]
    p = tmp_path / "w.csv"
    ew.write_csv(rows, p)
    assert p.read_text(encoding="utf-8-sig").splitlines()[0] == "instrument,locale,key,english,extracted,flags,status"
```

- [ ] **Step 2: Run test to verify it fails** — `python -m pytest data/translations-official/test_export_worklist.py -q` → `ModuleNotFoundError: export_worklist`.

- [ ] **Step 3: Write minimal implementation**

```python
#!/usr/bin/env python3
"""export_worklist.py — the translator worklist for ASPSI after the Aug-21 import.

One row per (instrument, locale, key) that is STILL not carrying an Aug-21 translation and why:
flagged (extractor QA flag), echo-english (paper cell identical to the English), unmatched
(anchor never found on the paper — needs the English aligned or the paper fixed), override
(kept the prior value on purpose, with the reason). Sources: out-aug21/<INST>/<loc>_flagged.json,
aug21-overrides.json, optionally aug21_apply_diff.json (--report) for the unmatched column.

    python export_worklist.py --xlsx ../../translator-worklist-aug21.xlsx --csv ../../translator-worklist-aug21.csv
"""
import argparse, csv, io, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
COLS = ["instrument", "locale", "key", "english", "extracted", "flags", "status"]


def collect_flagged(out_root, overrides_path, report_path=None):
    out_root = Path(out_root)
    rows = []
    for inst_dir in sorted(p for p in out_root.iterdir() if p.is_dir()):
        inst = inst_dir.name
        for f in sorted(inst_dir.glob("*_flagged.json")):
            loc = f.name.split("_")[0]
            for r in json.loads(f.read_text(encoding="utf-8")):
                flags = r.get("flags") or []
                rows.append({"instrument": inst, "locale": loc, "key": r.get("key") or r.get("en"),
                             "english": r.get("en", ""), "extracted": r.get("tr", ""),
                             "flags": ",".join(flags),
                             "status": "echo-english" if flags == ["echo-english"] else "flagged"})
    if report_path and Path(report_path).exists():
        rep = json.loads(Path(report_path).read_text(encoding="utf-8"))
        for inst, locs in rep.items():
            for loc, r in locs.items():
                for key in r.get("unmatched", []):
                    rows.append({"instrument": inst, "locale": loc, "key": key, "english": "",
                                 "extracted": "", "flags": "", "status": "unmatched"})
    ov = json.loads(Path(overrides_path).read_text(encoding="utf-8")) if Path(overrides_path).exists() else {}
    for inst, block in ov.items():
        if inst.startswith("_"):
            continue
        if inst == "F2":
            for loc, sub in block.items():
                for key, ent in sub.items():
                    rows.append({"instrument": inst, "locale": loc, "key": key, "english": key,
                                 "extracted": "" if ent.get("keep") is None else ent["keep"],
                                 "flags": ent.get("reason", ""), "status": "override"})
        else:
            for key, ent in block.items():
                rows.append({"instrument": inst, "locale": "*", "key": key, "english": "",
                             "extracted": ent.get("keep", ""), "flags": ent.get("reason", ""),
                             "status": "override"})
    return rows


def write_csv(rows, path):
    with io.open(path, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in COLS})


def write_xlsx(rows, path):
    try:
        from openpyxl import Workbook
    except ImportError:
        print("openpyxl not installed - csv only"); return False
    wb = Workbook(); ws = wb.active; ws.title = "worklist"
    ws.append(COLS)
    for r in rows:
        ws.append([r.get(c, "") for c in COLS])
    ws.freeze_panes = "A2"; ws.auto_filter.ref = ws.dimensions
    wb.save(path); return True


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-root", default=str(HERE / "out-aug21"))
    ap.add_argument("--overrides", default=str(HERE / "aug21-overrides.json"))
    ap.add_argument("--report", default=str(HERE / "aug21_apply_diff.json"))
    ap.add_argument("--xlsx", required=True); ap.add_argument("--csv", required=True)
    a = ap.parse_args(argv)
    rows = collect_flagged(a.out_root, a.overrides, a.report)
    write_csv(rows, a.csv); write_xlsx(rows, a.xlsx)
    by = {}
    for r in rows:
        by[(r["instrument"], r["status"])] = by.get((r["instrument"], r["status"]), 0) + 1
    for k in sorted(by): print(f"{k[0]} {k[1]:<13} {by[k]}")
    print(f"{len(rows)} rows -> {a.csv} / {a.xlsx}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run test to verify it passes** — `python -m pytest data/translations-official/test_export_worklist.py -q` → `2 passed`.

- [ ] **Step 5: Verify/gate** — `python data/translations-official/apply_aug21.py --unmatched` (dry run over all three instruments so `aug21_apply_diff.json` carries the `unmatched` columns — writes nothing) then `python data/translations-official/export_worklist.py --xlsx translator-worklist-aug21.xlsx --csv translator-worklist-aug21.csv` Expected: per-instrument counts by status, `N rows -> …`; open the xlsx (or csv) and spot-check three rows against the matching PDF: an `echo-english` row shows the identical English cell on paper; a `flagged` row's `extracted` text shows the bleed the flag names. No build files changed (`git status --short F1 F3 F4` unchanged).

- [ ] **Step 6: Record** — the worklist files are Carl's to send to ASPSI (via the ASPSI email per memory) and to commit; note row counts per instrument/status in `log.md` and in the status file (Task 44).

### Task 46: Runtime-message sheet for ASPSI (`export_messages_sheet.py`) — OPTIONAL / DEFERRED, export only, nothing wired

> **Deferred by the spec (Open items: "emit the ~590-string sheet … a separate request, not this build").** Default = SKIP this task and let Task 47 log the sheet as an open item ("runtime messages English; sheet on request"). Run it only if Carl explicitly asks for the sheet during Wave 5; it touches no build either way.

**Files:**
- Create: `deliverables/CSPro/automation/export_messages_sheet.py`
- Create: `deliverables/CSPro/runtime-messages-for-translation.csv`
- Test: `deliverables/CSPro/automation/test_export_messages_sheet.py`

**Interfaces:**
- Consumes: `F{1,3,4}/messages-registry.json` (the `errmsg(N)` registry: `{ "<N>": {"text": "...", ...} }` or a list of `{id, text}` — read both shapes) and `F{1,3,4}/<Base>.ent.apc` (`errmsg(N` references, to mark which ids are live); `cspro_helpers.numberize_errmsgs` expects `<INST>/translations/messages.<loc>.json` keyed by English message text (cspro_helpers.py:1303-1304) — NONE exist and none are created here
- Produces: `rows_from_registry(inst, registry_path, apc_path=None) -> list[{instrument, id, english, referenced, fil, bcl, bis, ceb, war, hil, ilo}]` (translation columns blank for ASPSI to fill); `write_sheet(rows, path)`; CLI `python automation/export_messages_sheet.py --out runtime-messages-for-translation.csv [--all]` (default = only ids referenced in the .apc; `--all` = every registry entry)

- [ ] **Step 1: Write the failing test**

```python
# deliverables/CSPro/automation/test_export_messages_sheet.py
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import export_messages_sheet as ems  # noqa: E402


def test_rows_from_registry_marks_referenced(tmp_path):
    reg = tmp_path / "messages-registry.json"
    reg.write_text(json.dumps({"1001": {"text": "Age must be 18 or above."}, "1002": {"text": "Unused."}}), encoding="utf-8")
    apc = tmp_path / "X.ent.apc"
    apc.write_text("if AGE < 18 then errmsg(1001); endif;", encoding="utf-8")
    rows = ems.rows_from_registry("F1", reg, apc)
    by = {r["id"]: r for r in rows}
    assert by["1001"]["referenced"] is True and by["1001"]["english"] == "Age must be 18 or above."
    assert by["1002"]["referenced"] is False
    assert all(by["1001"][l] == "" for l in ["fil", "bcl", "bis", "ceb", "war", "hil", "ilo"])


def test_list_shaped_registry(tmp_path):
    reg = tmp_path / "r.json"
    reg.write_text(json.dumps([{"id": 7, "text": "Seven"}]), encoding="utf-8")
    assert ems.rows_from_registry("F3", reg)[0]["id"] == "7"
```

- [ ] **Step 2: Run test to verify it fails** — `python -m pytest automation/test_export_messages_sheet.py -q` → `ModuleNotFoundError`.

- [ ] **Step 3: Write minimal implementation**

```python
#!/usr/bin/env python3
"""export_messages_sheet.py — runtime error/validation messages as a translation sheet for ASPSI.

Runtime messages are OUT OF SCOPE for the Aug-21 import (no messages.<loc>.json exists and the
Aug-21 PDFs do not carry them). This exports the English registry so ASPSI's translators can
fill the seven columns; wiring the result through cspro_helpers.numberize_errmsgs is a later
decision. Nothing under F<n>/ is modified.

    python automation/export_messages_sheet.py --out runtime-messages-for-translation.csv [--all]
"""
import argparse, csv, io, json, re, sys
from pathlib import Path

CSPRO = Path(__file__).resolve().parent.parent
APC = {"F1": "FacilityHeadSurvey.ent.apc", "F3": "PatientSurvey.ent.apc", "F4": "HouseholdSurvey.ent.apc"}
LOCS = ["fil", "bcl", "bis", "ceb", "war", "hil", "ilo"]
COLS = ["instrument", "id", "english", "referenced"] + LOCS
ERRMSG = re.compile(r"errmsg\(\s*(\d+)")


def _entries(reg):
    if isinstance(reg, dict):
        for k, v in reg.items():
            if k.startswith("_"):
                continue
            yield str(k), (v.get("text") if isinstance(v, dict) else v) or ""
    else:
        for v in reg:
            yield str(v.get("id")), v.get("text") or ""


def rows_from_registry(inst, registry_path, apc_path=None):
    reg = json.loads(Path(registry_path).read_text(encoding="utf-8"))
    live = set(ERRMSG.findall(Path(apc_path).read_text(encoding="utf-8", errors="ignore"))) if apc_path else set()
    rows = []
    for mid, text in _entries(reg):
        row = {"instrument": inst, "id": mid, "english": text, "referenced": mid in live}
        row.update({l: "" for l in LOCS})
        rows.append(row)
    return rows


def write_sheet(rows, path):
    with io.open(path, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in COLS})


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--all", action="store_true", help="include registry ids the .apc never references")
    a = ap.parse_args(argv)
    rows = []
    for inst, apc in APC.items():
        reg = CSPRO / inst / "messages-registry.json"
        if not reg.exists():
            print(f"{inst}: no messages-registry.json - skipped"); continue
        r = rows_from_registry(inst, reg, CSPRO / inst / apc)
        rows += r if a.all else [x for x in r if x["referenced"]]
    write_sheet(rows, a.out)
    print(f"{len(rows)} messages -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run test to verify it passes** — `python -m pytest automation/test_export_messages_sheet.py -q` → `2 passed`.

- [ ] **Step 5: Verify/gate** — `python automation/export_messages_sheet.py --out runtime-messages-for-translation.csv` Expected: `N messages -> …` with N > 0 for each of the three instruments present; open the csv: every `english` cell is a full sentence, the seven locale columns are empty; `git status --short F1 F3 F4` unchanged.

- [ ] **Step 6: Record** — note in the status file (Task 44) that runtime messages remain English by design, with the sheet path for ASPSI.

### Task 47: Close-out records — wiki source, ASPSI status note, memory-note updates, log

**Files:**
- Create: `wiki/sources/Source - Revised Deliverable 2 Translated Questionnaires (Aug 21).md`
- Modify: `wiki/entities/ASPSI.md`, `wiki/concepts/CSPro.md` (one paragraph each)
- Create: `deliverables/CSPro/patch-notes/2026-08-28-aug21-translations-status-for-aspsi.md`, `deliverables/CSPro/patch-notes/2026-08-28-memory-note-updates.md`
- Create: `docs/uat-fix-evidence/<EVDATE>-aug21-translations/README.md` (root index over the F1/F2/F4/F3 subfolders)
- Modify: `log.md`
- Test: placeholder grep (Step 5)

**Interfaces:**
- Consumes: `wiki/sources/Source - DOH Deliverable 2 Translated Questionnaires (June 5).md` (shape to mirror); the four wave notes + `TRANSLATION-STATUS-2026-08-28.md` (Task 44); worklist counts (Task 45); memory files `project_aspsi_translations_pipeline.md`, `project_aspsi_cspro_translations.md`, `project_aspsi_f2_pwa_state.md`, `project_aspsi_capi_psa_release.md` (the entries the updates note proposes — the note is written here; the memory files themselves are updated by the main session, not by this task)
- Produces: the wiki source page (what the Aug-21 pack is, 28 files, layout quirks per instrument: F2-Bicolano inline echo, F1-Tagalog ICF para-2 English line, F3-Tagalog 06/05 header, monolingual F4 PDFs), the ASPSI-facing status (versions live, coverage table, worklist + runtime-message sheet attached, source defects to fix in the next pack), the memory-update list, the evidence index

- [ ] **Step 1: Wiki source page** — mirror the June-5 source page's headings (`Provenance`, `Files`, `How it was ingested`, `Known defects in the source`, `Where it landed`), citing `raw/Survey-Instruments-2026-08-21/` (gitignored, on disk), the extractor/merge tools by path, the four wave notes and the status file.

- [ ] **Step 2: Entity/concept updates** — `wiki/entities/ASPSI.md`: one paragraph "Revised Deliverable 2 (Aug 21, 2026)" linking the source page; `wiki/concepts/CSPro.md`: one paragraph on the name-scoped Aug-21 pipeline (`anchor_extract.py` → `apply_aug21.py` → `run_aug21_gates.ps1` → generators) replacing the June-5 text-keyed description.

- [ ] **Step 3: ASPSI status note** — `deliverables/CSPro/patch-notes/2026-08-28-aug21-translations-status-for-aspsi.md`: plain-language summary for Carl to send from the ASPSI address: what shipped (four versions, dates), the coverage table (from Task 44), attachments (`translator-worklist-aug21.xlsx`; `runtime-messages-for-translation.csv` only if Task 46 was run, otherwise one line "runtime error messages stay English; a translator sheet is available on request"), the source defects list, a **not in this build** section (runtime messages; F2 chrome beyond the consent screen; F3 115.x Shape-B; the DOH Aug-21 *Review of Deliverable 2* manuals feedback — no instrument/translation items, handed to the manuals lane), and the ask (fill the worklist rows; fix the four paper defects in the next pack). Evidence index `docs/uat-fix-evidence/<EVDATE>-aug21-translations/README.md`: one table row per instrument subfolder → version, deploy date, key PNGs, byte-verify result.

- [ ] **Step 4: Memory-note updates** — `deliverables/CSPro/patch-notes/2026-08-28-memory-note-updates.md` listing, per memory file, the one-line change: `project_aspsi_translations_pipeline.md` (Aug-21 set IMPORTED, name-scoped pipeline, overrides file), `project_aspsi_cspro_translations.md` (F1 4.1.0 / F4 3.2.0 / F3 6.1.0 live with Aug-21 maps; ICF/notes per language), `project_aspsi_f2_pwa_state.md` (spec `2026-08-2x-m4`, flat store still English-keyed; consent screen Part-I paragraphs per locale from Aug-21), `project_aspsi_capi_psa_release.md` (unchanged — PSA set frozen; DEV channel after), `project_aspsi_deliverable2_revised_aug21.md` (the spec's driving entry: pack location `raw/Survey-Instruments-2026-08-21/`, status IMPORTED across F1 4.1.0 / F2 m4 / F4 3.2.0 / F3 6.1.0 with dates, evidence path `docs/uat-fix-evidence/<EVDATE>-aug21-translations/`, worklist sent to ASPSI on <date>, DOH manuals-feedback item routed to the manuals lane), `MEMORY.md` index line.

- [ ] **Step 5: Verify/gate** — `Select-String -Path "deliverables/CSPro/patch-notes/2026-08-28-*.md","wiki/sources/Source - Revised Deliverable 2 Translated Questionnaires (Aug 21).md","docs/uat-fix-evidence/*-aug21-translations/README.md" -Pattern "<\?>|<date>|<URL|2026-08-2x|NN%"` returns nothing; every relative link in the wiki page resolves (`Test-Path` each); `git status --short docs/uat-fix-evidence` shows only the new root README.

- [ ] **Step 6: Record** — `git add docs/uat-fix-evidence/<EVDATE>-aug21-translations/README.md; git commit -m "evidence: Aug-21 translations index"` (sanctioned evidence commit); prepend the close-out entry to `log.md` (`### 2026-08-28 - Aug-21 translations close-out`: versions, coverage deltas, worklist counts, open items: 115.x Shape-B deferred, r25 GPS residue, F2 id-scoped re-key parked, runtime messages English (translator sheet deferred to a separate request — Task 46 skipped unless run), DOH Aug-21 *Review of Deliverable 2* → manuals lane (no instrument/translation items)). Everything else (wiki, patch-notes, status file, worklist, sheet, CSPro tooling) stays in the working tree for Carl to commit.

---

## Self-review — spec coverage map

| Spec section | Where it lands (task numbers) |
|---|---|
| Task 0 / build-vs-Aug-21-English delta gate (Risks row 3: re-run before every extraction) | Task 0; re-run in Tasks 16, 26, 39 |
| Day-0 extractor refactor (committed, argparse, name-scoped `item:/vs:/val:`, `--generator F3`, glue flags) | Tasks 1–2 |
| Overrides file + schema (every override → a reason; only re-introduced defects) | Task 3; seeded in Tasks 6, 10, 17, 22, 28, 40 |
| Merge tool `apply_aug21.py` (Aug-21 wins, `_meta.sources.aug21`, dry-run default, seed, per-reason scan delta, bridge B/C gate) | Tasks 4–7; run in Tasks 17, 28, 40 |
| Notes layer from the Aug-21 PDFs (`extract_notes --source/--provenance`, Aug-21-wins merge) | Task 8; F4 gate constants Task 29 |
| ICF consent per language (`icf_content.screens_for`, `extract_icf.py`, 08/21/2026 stamp) | Tasks 9–10; wired in Task 11; rendered in Tasks 18, 29, 41 |
| F2 flat-store pipeline (english-strings dump, `anchor_extract_f2.py`, `apply-paper-translations.py`) | Tasks 12–15 |
| Wave 1 — F1 4.1.0 (Q75 align, import, build, compile, deploy, byte-verify, emulator shots, patch note) | Tasks 16–20 |
| Spec Scope In "consent text from the same PDFs" for F2 (Scope Out = F2 chrome *beyond* the consent screen) — `consent.*` chrome keys per locale from the seven F2 PDFs, vitest + e2e assertion | Task 21 |
| Wave 2 — F2 m4 (consent screen, apply, vitest guard, generate, audit, spec stamp, commit+push, deploy, evidence, patch note) | Tasks 21–23 |
| Wave 3 — F4 3.2.0 (Q30/Q35/Q36/Q40/Q67 align, printed gates as notes, delta, extract, merge, notes, stamp, compile, deploy, byte-verify, emulator shots, patch note) | Tasks 24–34 |
| Wave 4a — F3 English alignment (Q47/Q69/Q94/Q96/Q98, 97.2/115.x labels, HIL/ILO fill, pre-import gates + compile + WAR desk render) | Tasks 35–39 |
| Wave 4b — F3 import + 6.1.0 ship (generator-anchored extract, merge, gates, rebuild, HIL desk render, bump, deploy, byte-verify, patch note, evidence) | Tasks 40–42 |
| Spec Verification item 3 / Waves row 4 "as wave 1" — F3 tablet proof from the DEPLOYED package (sideloaded `PatientSurvey.zip`, Q47 + 97.2 in HIL and WAR, ICF in HIL) | Task 43 |
| Spec Risks row 2 — dry-run lists unmatched anchors per locale before any write | `--unmatched` on every wave's dry-run: Tasks 17, 28, 40 |
| Spec Open items — DOH Aug-21 *Review of Deliverable 2* (manuals feedback) logged for the manuals lane; runtime-message sheet deferred (Task 46 optional); memory `project_aspsi_deliverable2_revised_aug21` | Task 47 |
| Wave 5 — close-out (coverage before/after table, translator worklist, runtime-message sheet, wiki source, ASPSI status, memory notes, log) | Tasks 44–47 |
| Spec §F3 bill-detail (97.1/97.2/115.1/115.2 exist, no data-shape change, `paper-only` rows by design) | Tasks 0 (gate rule), 36, 38 |
| Versions F1 4.1.0 / F2 m4 / F4 3.2.0 / F3 6.1.0 | Tasks 18, 23, 30, 42 |
| PSA set frozen at `capi-psa-2026-08-20`, DEV channel | Global Constraints; every `stamp_version.py bump` keeps `channel: dev` (Tasks 18, 30, 42) |
| `raw/` immutable; generator-first; name-scoped-v2; no CSPro commits (evidence + F2 only) | Global Constraints; enforced in every Record step |
| Runtime messages out of scope | Global Constraints; Task 46 (export-only sheet) is OPTIONAL/deferred per the spec's Open items — spec and plan agree that the sheet is not part of this build |

Reconciliations applied while assembling (each earlier section's name won unless a later section carried a verified fact):
1. Extractor output root unified to `out-aug21/<INST>/` (Day-0); the merge tool's default `aug21-extract/` was dropped and `EXTRACT_ROOT` points at `out-aug21`; the `.gitignore` line for `aug21-extract/` was removed (already covered by Task 0's rule).
2. Merge CLI unified to `apply_aug21.py --only INST [--extract DIR]` with the overrides file always read from its default path (Wave-1's `--from DIR --overrides PATH` spelling rewritten); report file name unified to `aug21_apply_diff.json` (Wave-1's `apply_aug21_report.json` dropped).
3. F2 extractor unified to `anchor_extract_f2.py --source --english-strings --out` (Wave-1's `anchor_extract.py --instrument F2 --items PATH` mode dropped); F2 apply unified to `apply-paper-translations.py --extract-dir/--overrides/--apply/--report` with report `out-aug21/F2/apply-report.json`.
4. F2 override shape unified to the locale-nested `{F2: {loc: {English: {keep: text|null, reason}}}}` form; the `drop: true` spelling was removed; `aug21_overrides.validate_overrides` and its test were extended to validate that shape (and to accept `keep: ""` only for `note:`/`icf:` keys).
5. Byte-verify unified to `aug17-tools/byte_verify_aug21.py` with `PROBE_KEYS` for F1/F4/F3 (Wave-3's separate `automation/aug21_byte_verify.py` and Wave-4b's `automation/byte_verify_pen.py` dropped); Wave-4a's inline English/dialect-phrase probe kept as a supplement.
6. `apply_aug21.py` override-mismatch behaviour: WARN (merge-tool section) rather than non-zero exit (Wave-3 wording); every wave treats the WARN as a STOP.
7. Component-suffix stripping (`— Hours/— Minutes`) moved INTO Task 1's `_anchors_from_dict` (Wave-3 precondition) with a test.
8. `extract_notes.py` const-regex widening to `^(_[A-Z0-9_]+)` moved into Task 8 (Wave-3 precondition) with a test.
9. CSWeb host unified to `root@207.148.65.115` (Wave-3's verified "no `csweb` alias" fact) — Wave-1's `csweb.asiansocial.org` rewritten.
10. Evidence folder unified to `docs/uat-fix-evidence/<EVDATE>-aug21-translations/{F1,F2,F4,F3}/` with upper-case subfolders (Wave-4b's `f3/` rewritten).
11. F3 ships 6.1.0 ONCE: Wave-4a's bump/deploy task moved after the Wave-4b import (Task 42) so the reworded questions ship with their translations; the 4a patch note's "translations arrive in the next build" sentence replaced accordingly.
12. The F2-tooling section's own "Wave-2 apply/deploy" tasks and the Wave-1/2 section's F2 tasks (which duplicated each other) were merged into Tasks 22–23, keeping every code block (node coverage one-liner, `f2-coverage.py`, vitest guard, spec-version test, commit here-string, deploy checks); the shorter of the two patch-note texts was dropped in favour of the one with the coverage table.
13. Wave-4b/Wave-5 body text was not supplied in the input (only its interface declaration); Tasks 40–47 were authored from that declaration in the same step shape.
14. Completeness-critic pass (2026-08-25): Task 21 (F2 consent screen from the Aug-21 PDFs) and Task 43 (F3 tablet locale shots from the deployed package) inserted and everything after renumbered (old 21–41 → +1, old 42–45 → +2); patch-note file names unified to `<EVDATE>-<inst>-v<ver>-aug21-translations.md`; `--unmatched` added to the F1/F4 dry-runs; `--whatsnew` removed from the F4 bump; F3 test counts corrected to 14 / 25; Task 10's `FIL_P1` fixture guarded by a verbatim-from-dump test with the Task 8 dump as a hard prerequisite; Task 39's scenario pilot time-boxed with a fallback; Task 46 marked optional/deferred per the spec's Open items; the spec's stale F3 MAJOR-warning sentence recorded as an erratum and fixed in Task 42; `aug21_coverage_baseline.json` listed in the File structure; `project_aspsi_deliverable2_revised_aug21` and the DOH manuals-feedback hand-off added to Task 47.
