---
title: "02 — Phase 0–2: Foundation"
category: deliverable
tags: [capi, cspro, scaffolding, ingestion, knowledge-base, uhc-y2]
last_updated: 2026-05-08
status: draft
---

# 02 — Phase 0–2: Foundation

The first three phases of the [[CAPI-Development-Workflow|CAPI Development Workflow]] template are the **foundation lift** — once-per-engagement work that has to be done well *before* the schema, the skip logic, and the build can move at speed. This guide is the UHC Year 2 instance of those three phases, assembled from the project CLAUDE.md, the Khurshid corpus, and the 12 CSPro concept pages already in `wiki/concepts/`.

The three phases are sequenced for a reason:

| Phase | Output | Why first |
|---|---|---|
| **Phase 0 — Project scaffolding** | Folder tree, CLAUDE.md trio, contract ingest, mode decision per instrument, toolchain installs | Everything downstream assumes the layout, the contractual envelope, and the toolchain. Skipping Phase 0 means Phase 3 can't generate, Phase 8 can't deploy, and the contract-vs-scope conversation never has a paper trail. |
| **Phase 1 — Source ingestion (per instrument)** | `raw/<Instrument> <date>.pdf` (immutable), `raw/<Instrument>.txt` (grep-able), `wiki/sources/Source - <Instrument>.md` (citable) | Phase 4 (skip-logic walk) cites question numbers + page numbers. Phase 3 (`.dcf` generator) reads the text extract. Both are blocked until ingestion is done. |
| **Phase 2 — Tool knowledge base (one-time per consultant)** | 12 CSPro concept pages + CSWeb concept set + CSEntry Android concept set + Khurshid corpus pointer | Phase 3+ uses CSPro vocabulary on every line. Without the concept pages you re-read the 958-page Users Guide every time you forget what `onfocus` fires before. The concept set replaces re-reading. |

> **All three phases are upstream of build.** Time spent here is the cheapest time on the project. Phase 4 bug-hunts on a stable foundation are short; Phase 4 bug-hunts on a half-ingested questionnaire are bottomless.

---

## Phase 0 — Project scaffolding

**Objective**: Stand up the working environment and lock down the contractual reality before any technical work. *(One-time per engagement.)*

### 0.1 PARA + LLM Wiki folder structure

UHC Year 2 lives inside Carl's analytiflow PARA vault as `1_Projects/ASPSI-DOH-CAPI-CSPro-Development/`. The folder schema follows the project-level CLAUDE.md (see `1_Projects/ASPSI-DOH-CAPI-CSPro-Development/CLAUDE.md`) and the vault-level CLAUDE.md at `analytiflow/CLAUDE.md`.

The directory tree:

```
1_Projects/ASPSI-DOH-CAPI-CSPro-Development/
├── CLAUDE.md                       # project schema + LLM Wiki operating rules
├── index.md                        # content catalog of every wiki page + every deliverable
├── log.md                          # chronological record of every operation (ingests, queries, lints)
│
├── raw/                            # INPUT — source documents, immutable. LLM reads, never modifies.
│   ├── Annex F1 ... April 20.pdf       # original questionnaire, dated by version
│   ├── Annex F3 ... April 20.pdf
│   ├── Annex F4 ... April 20.pdf
│   ├── ASPSI Signed CSA ... Dec 15 2025.pdf
│   ├── Revised Inception Report ... April 20.pdf
│   ├── DOH Survey Protocol V2 ... April 30.pdf
│   ├── CSPro 8.0 Users Guide.pdf
│   └── ...                             # other annexes (A, B, C, D, E, G, H, I, J)
│
├── wiki/                           # KNOWLEDGE — LLM-generated markdown. LLM owns it.
│   ├── sources/                        # one summary page per ingested source
│   │   ├── Source - Annex F1 Facility Head Survey Questionnaire.md
│   │   ├── Source - Annex F3 Patient Survey Questionnaire.md
│   │   ├── Source - Annex F4 Household Survey Questionnaire.md
│   │   ├── Source - Signed CSA Dec 15 2025.md
│   │   ├── Source - CSPro 8.0 Complete Users Guide.md
│   │   ├── Source - DOH Survey Protocol V2 (30 April).md
│   │   └── ...
│   ├── entities/                       # people, organizations, places, products
│   │   ├── ASPSI.md
│   │   ├── DOH-PMSMD.md
│   │   ├── SJREB.md
│   │   ├── Dr Paulyn Claro.md
│   │   ├── Dr Myra Silva-Javier.md
│   │   ├── Juvy Chavez-Rocamora.md
│   │   └── ...
│   ├── concepts/                       # ideas, frameworks, patterns spanning sources
│   │   ├── CSPro.md
│   │   ├── CSPro Data Dictionary.md
│   │   ├── CSPro Logic Events.md
│   │   ├── F-Series Value Set Conventions.md
│   │   ├── PSGC Value Sets.md
│   │   └── ...                            # 12 CSPro concept pages enumerated in §2 below
│   └── analyses/                       # comparisons, syntheses, queries that earned a permanent home
│       ├── Analysis - Project Intelligence Brief.md
│       └── Analysis - Apr 20 DCF Generator Audit.md
│
├── deliverables/                   # OUTPUT — authored work products. LLM may write here on request.
│   ├── CSPro/                          # all CAPI artifacts live under one root
│   │   ├── cspro_helpers.py                # shared item-builder + value-set library
│   │   ├── export_dcf_to_xlsx.py           # second-opinion review export
│   │   ├── shared/                         # cross-instrument lookups (PSGC) + reusable PROC
│   │   │   ├── build_psgc_lookups.py
│   │   │   ├── psgc_region.{dcf,dat}
│   │   │   ├── psgc_province.{dcf,dat}
│   │   │   ├── psgc_city.{dcf,dat}
│   │   │   ├── psgc_barangay.{dcf,dat}
│   │   │   └── PSGC-Cascade.apc
│   │   ├── F1/
│   │   │   ├── generate_dcf.py
│   │   │   ├── FacilityHeadSurvey.dcf
│   │   │   ├── FacilityHeadSurvey.fmf       # form file (Designer-edited, generator skeleton)
│   │   │   ├── FacilityHeadSurvey.apc       # PROC logic
│   │   │   ├── F1-Skip-Logic-and-Validations.md
│   │   │   ├── inputs/
│   │   │   │   ├── F1_clean.txt                 # text extract
│   │   │   │   └── psgc_*.csv                   # PSA 1Q 2026 PSGC source-of-truth CSVs
│   │   │   └── test-cases/                      # mock cases for regression
│   │   ├── F3/                              # mirrors F1
│   │   └── F4/                              # mirrors F1
│   ├── F2/                             # PWA track — separate stack, referenced for case-ID + ops
│   ├── Survey-Manual/                  # Carl's CSPro install section + case-ID brief
│   └── UHC-Survey-CAPI-Guide/          # this guide
│
├── templates/                       # REUSABLE — boilerplate for repeated use within this project
│   └── ...                              # CSV value-set templates, codebook stub, etc.
│
└── scrum/                           # per-project Scrum: Product Backlog + Sprint Backlog + standups
    ├── product-backlog.md
    ├── sprint-NN/
    │   ├── sprint-backlog.md
    │   ├── 2026-MM-DD-standup.md
    │   └── retro.md
    └── ...
```

**Folder rules** (from `analytiflow/CLAUDE.md` + the project CLAUDE.md):

1. **`raw/` is immutable.** Original questionnaires, contracts, and reference PDFs land here untouched. Datestamp the filename for any artifact that will rev (every questionnaire annex carries an `April 08`, `April 20`, etc. suffix). The LLM reads these and never modifies them.
2. **`wiki/` is LLM-owned.** Every source gets a summary page in `wiki/sources/`. Every recurring noun (person, org, system) gets an entity page. Every framework or pattern gets a concept page. Pages are linked aggressively via Obsidian wikilinks; orphans are linted out.
3. **`deliverables/` is authored output.** CAPI applications, generators, specs, this guide. Never put a dropped/received file here — that's `0_Inbox/` or `raw/`.
4. **`templates/` is for boilerplate** scoped to *this* project. Cross-project templates live in `2_Areas/IT-Standards/templates/` (e.g. the [[CAPI-Development-Workflow|workflow template]] this guide instantiates).
5. **`scrum/` holds the per-project Scrum** (Product Backlog + Sprint Backlogs + standups) per the user's per-project Scrum convention. No external tracker.
6. **Kebab-case folder names**, vault-wide. No spaces in folder paths; use `Kebab-Case` for vault folders. (File names inside the wiki use Title Case for readability — `Source - Annex F1 Facility Head Survey Questionnaire.md`.)

### 0.2 The CLAUDE.md + index.md + log.md trio

Three files at the project root govern how Claude operates inside the project:

| File | Purpose | When to update |
|---|---|---|
| `CLAUDE.md` | The project's operating schema. Defines folder layout, page types (`source-summary`, `entity`, `concept`, `analysis`, `overview`), conventions (links, tags, headings, citations), and the Ingest/Query/Lint workflows. Read at the start of every session. | When the schema changes — e.g. adding a new page type, a new convention, a new operating rule. Rare. |
| `index.md` | The content catalog. Every wiki page (sources, entities, concepts, analyses) + every deliverable is listed with a one-line annotation. The mental model: "if a page exists and isn't reachable from `index.md`, it's an orphan." | Every time a page is created, renamed, or substantially repurposed. Update inside the same operation that creates the page. |
| `log.md` | The chronological record of operations — what was ingested, what was queried, what was linted, with date and one-line summary. | Append a row after every significant operation. The log is what makes the wiki auditable. |

A typical session begins with Claude reading `CLAUDE.md` (operating rules) then `index.md` (what's already known) before answering a query. Updates always include `index.md` + `log.md` so the catalog and audit trail stay in lockstep.

**Sample CLAUDE.md skeleton** (this project already has one — see [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/CLAUDE|the project CLAUDE.md]]):

```markdown
# LLM Wiki Schema

This vault is a **knowledge base for the <PROJECT NAME>**: <one-sentence project description>.

## Directory Structure

/raw/              — INPUT: Source documents to be ingested. Immutable.
/wiki/             — KNOWLEDGE: LLM-generated markdown pages.
  /wiki/sources/   — Source summary pages (one per ingested source).
  /wiki/entities/  — Entity pages (people, orgs, places, products).
  /wiki/concepts/  — Concept pages (ideas, theories, frameworks, patterns).
  /wiki/analyses/  — Analysis pages (comparisons, syntheses, explorations).
/deliverables/     — OUTPUT: Work products authored by the user (often with LLM help).
/templates/        — REUSABLE: Project-scoped boilerplate.
/index.md          — Content catalog of all wiki pages.
/log.md            — Chronological record of all operations.
/CLAUDE.md         — This file. The schema and operating rules.

## Page Types
<frontmatter templates per type>

## Conventions
<links, tags, headings, citations, contradictions, filenames>

## Operations
<Ingest, Query, Lint workflows>

## Rules
<NEVER modify /raw/, ALWAYS update index.md and log.md, etc.>
```

**Sample `index.md` skeleton**:

```markdown
# <Project Name>

<one-paragraph project description>

## Project Structure

- `deliverables/` — authored outputs
- `raw/` — inputs received
- `wiki/` — LLM Wiki

## Wiki Catalog

### Sources
- `[[wiki/sources/Source - <Title>]]` — *one-line annotation, version, key numbers*

### Entities
- `[[wiki/entities/<Name>]]` — *role / org / function*

### Concepts
- `[[wiki/concepts/<Concept>]]` — *one-line definition*

### Analyses
- `[[wiki/analyses/Analysis - <Title>]]` — *one-line scope*

## Deliverables
<grouped by instrument or stream>
```

**Sample `log.md` row**:

```markdown
## 2026-04-20

- Ingested `raw/Annex F1 Facility Head Survey Questionnaire April 20.pdf`. Created `wiki/sources/Source - Annex F1 Facility Head Survey Questionnaire.md`. Updated `index.md`. F1 grew from 126 items (Apr 08) to 166 items (Apr 20) — flagged in Analysis - Apr 20 DCF Generator Audit.
```

The trio is enough to keep the project navigable for both Carl and any future Claude session.

### 0.3 Contract / CSA ingestion

The first **non-tooling** ingest in Phase 0 is the signed Consultancy Services Agreement. The CSA fixes the contractual envelope — person-month allocation, payment tranches, late-penalty clause, and the Terms of Reference (TOR) that the entire build is delivering against. Without the CSA captured, every later scope conversation is unanchored.

**Drop the original PDF in `raw/`**:

```
raw/ASPSI Signed CSA Dec 15 2025.pdf
```

**Summarize into a wiki source page** at `wiki/sources/Source - Signed CSA Dec 15 2025.md`. The page captures, at minimum:

- **PM allocation**: 6.0 person-months × PHP 65,000 = PHP 390,000 total.
- **Tranches**: 4 deliverable-based payments, gated by acceptance of specific deliverables.
- **Late penalty**: 1% per day on the affected tranche.
- **TOR**: 10 enumerated duties, copied verbatim into the source page so they're grep-able and citable when scope shifts.
- **Counterparty signatures**: who signed for ASPSI (Juvy Chavez-Rocamora as ASPSI President), who signed for the CAPI Developer (Carl), date.
- **Cross-link** to the DOH-side TOR (`Source - DOH TOR UHC Survey Year 2`) so the ASPSI-side and DOH-side scopes can be diffed when the client requests something.

**Why this matters in Phase 0**: every later phase intersects the CSA. Phase 5 dictionary corrections that come from a client request need to be checkable against the TOR; Phase 9 pretest sign-off triggers a tranche release; Phase 11 closeout closes the last tranche. The CSA wiki page is referenced from the Phase-tranche map so each tranche's deliverables are unambiguous.

### 0.4 Mode-per-instrument decision

UHC Year 2 has four instruments. The Phase 0 mode decision is the call on which delivery mode each one runs in:

| Instrument | Mode | Decision rationale |
|---|---|---|
| **F1 Facility Head** | CAPI (CSPro tablet) | Interviewer-administered. Respondent (facility head) may have variable digital literacy; interviewer needs to read questions aloud and follow skip logic without burdening the respondent. Tablet GPS auto-captures facility location. Field connectivity is regional and intermittent — periodic CSWeb sync handles the gap. |
| **F3 Patient** | CAPI (CSPro tablet) | Interviewer-administered. Patients (outpatient + inpatient) have variable literacy and physical capacity (post-discharge for IP). Interviewer fills the form during a face-to-face session. Auto-GPS at facility. |
| **F4 Household** | CAPI (CSPro tablet) | Interviewer-administered. Household members include children and elderly; literacy is heterogeneous; interviewer is the only realistic data-entry actor. Roster-heavy (household members, expenditures) — CSPro repeating records handle this cleanly. |
| **F2 Healthcare Worker** | Self-admin Web (PWA) | Literate professional respondent (doctors, nurses, midwives, pharmacists). They have their own device — phone, laptop, desktop — and reliable enough connectivity to load a web form. Self-admin is faster and avoids enumerator scheduling friction. Per the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - DOH Survey Protocol V2 (30 April)|DOH Survey Protocol V2]], F2 is mandated as "online/offline PWA-compatible" — the Protocol V2 is the SJREB + PSA submission baseline, so the mode is locked. |

**Documented decision**: F1 / F3 / F4 = CAPI on CSPro/CSEntry; F2 = self-admin PWA. This guide covers the CAPI track only; F2 is referenced where it intersects (shared case-ID convention, shared backend operations) but otherwise has its own build artifact set under `deliverables/F2/PWA/`.

The mode decision is captured at the top of `00-Architecture.md` and referenced from the Inception Report ingest page, the Protocol V2 ingest page, and this section. Once recorded, scope creep that proposes "let's also do F1 self-admin" can be checked against the recorded rationale and the Protocol V2 mandate.

### 0.5 CSPro Designer install

The CSPro authoring environment runs on Windows (the LLM-Wiki workstation is Windows 11 Pro per the project env). Install steps follow the Khurshid 2022-03-14 walkthrough (CSPro 7.7.1 in the video; **for UHC Year 2 use 7.7+**, currently CSPro 8.0 is the project baseline since the dictionaries are emitted in CSPro 8.0 JSON).

**Steps** **(Khurshid 2022-03-14)**:

1. **Microsoft Visual C++ Re-distributable prerequisites**: Khurshid's exact list — `2008, 10, 12, 13, 15, 17`. Install all six 64-bit packages before installing CSPro. *"In order to successfully install and run the WAMP server, please make sure that you have installed the following Microsoft Visual C++ Re-distributable packages: 2008, 10, 12, 13, 15 and 17."* The same prerequisites apply to CSPro Designer.
2. **Download CSPro 8.0** (or latest 7.7+) from the US Census Bureau site (`csprousers.org`).
3. **Run installer**, accept license, accept defaults — standard Windows installer flow.
4. **Verify**: launch CSPro Designer; the splash screen should report version 8.0 (or whatever was installed).

**Application folder convention** **(Khurshid 2022-03-27)**: Khurshid uses numbered subfolders under each application root for deterministic ordering and easy file-picker navigation. The convention is:

```
app-<name>/
├── 101_<main>/        # main application — .ent, .dcf, .fmf, .apc
├── 102_EXT_DIC/       # external dictionaries (lookup tables)
├── 103_EXT_DATA/      # external data files (.dat consumed by external dictionaries)
└── 104_excel/         # source Excel files for conversion (Tools → Excel to CSPro)
```

UHC Year 2 deviates from this convention slightly because the CAPI artifacts are version-controlled inside `deliverables/CSPro/<Instrument>/` and the cross-instrument lookups (PSGC) sit in `deliverables/CSPro/shared/`. The numbered-subdir convention is preserved in spirit — each instrument has its own subfolder with its own `inputs/` and the shared lookups have their own folder — but without the literal numeric prefixes since the file system is under git and folder ordering matters less than the link from `index.md`.

Khurshid's keyboard shortcut for new folders applies: `Ctrl+Shift+N` in Explorer, then enter the folder name.

### 0.6 Python toolchain setup

Every `.dcf` is generated by a Python script. Phase 3 will not run without a working Python toolchain.

| Tool | Version | Why |
|---|---|---|
| **Python** | 3.10+ | F-strings, structural pattern matching, `match` statements, `pathlib` improvements all assumed by the helpers. |
| **`uv`** | latest | Project-standard package + virtualenv manager. Faster than pip; deterministic lockfiles. |
| **`pyproject.toml`** | per-project | Declares dependencies (`pandas`, `pdfplumber`, `python-docx`, project-internal `cspro_helpers`). |
| **Local virtualenv** | `.venv/` | Isolates project deps from system Python. `uv venv` creates it; `uv sync` installs from the lockfile. |

**Bootstrap (one-time per workstation)**:

```powershell
# Python 3.10+ from python.org or the Microsoft Store
python --version    # verify >= 3.10

# Install uv (Windows PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
uv --version

# Create the project venv + install deps
cd C:\Users\analy\Documents\analytiflow\1_Projects\ASPSI-DOH-CAPI-CSPro-Development
uv venv
uv sync
```

**Sample `pyproject.toml`** (project-root level, owned by `deliverables/CSPro/`):

```toml
[project]
name = "uhc-y2-cspro"
version = "0.1.0"
description = "UHC Year 2 CSPro CAPI generators"
requires-python = ">=3.10"
dependencies = [
    "pandas>=2.0",
    "pdfplumber>=0.10",
    "python-docx>=1.0",
    "openpyxl>=3.1",       # for export_dcf_to_xlsx
]

[tool.uv]
dev-dependencies = [
    "pytest>=8.0",
    "ruff>=0.4",
]
```

The shared helpers module at `deliverables/CSPro/cspro_helpers.py` is the import point for every generator (`from cspro_helpers import yes_no_item, select_one, build_geo_id, ...`). Phase 3 covers this module in depth — Phase 0 just needs the runtime to be ready.

### 0.7 Git repo bootstrap

The GitHub repo `cplreyes/ASPSI-DOH-UHC-CAPI-Development` is public as of 2026-04-23 (renamed from `ASPSI-DOH-CAPI-CSPro-Development`). The local folder name is unchanged. Versioning is handled manually outside this guide; the repo URL exists so external collaborators can clone it. No further git commentary belongs in the foundation phase.

### 0.8 Phase 0 exit criteria

A checklist; flip these to `[x]` as each lands:

- [ ] Project folder exists at `1_Projects/<Project>/` with `raw/`, `wiki/sources`, `wiki/entities`, `wiki/concepts`, `wiki/analyses`, `deliverables/`, `templates/`, `scrum/`.
- [ ] `CLAUDE.md`, `index.md`, `log.md` exist at the project root and reflect the project's actual schema.
- [ ] Signed CSA dropped in `raw/`; `wiki/sources/Source - Signed CSA Dec 15 2025.md` summarizes PM allocation, tranches, penalty, TOR.
- [ ] DOH-side TOR ingested at `wiki/sources/Source - DOH TOR UHC Survey Year 2.md` and cross-linked from the CSA page.
- [ ] Mode-per-instrument decision recorded (F1/F3/F4 = CAPI; F2 = PWA) with rationale and Protocol V2 citation.
- [ ] CSPro Designer installed and launches; version recorded in `index.md` (CSPro 8.0).
- [ ] Wampserver / CSWeb installs are *not* part of Phase 0 — those happen in Phase 8 (see [[06-Phase-8-CSWeb-and-Tablets]]). Khurshid 2022-03-14 covers both, but only the Designer step belongs to the developer's workstation.
- [ ] Python 3.10+ + `uv` installed; `.venv` created; `pyproject.toml` committed; `uv sync` runs clean.
- [ ] GitHub remote exists and the local repo is connected (manual; not in scope here).

When all boxes are checked, Phase 1 can start.

---

## Phase 1 — Source ingestion *(per instrument)*

**Objective**: Bring each questionnaire under version control as a citable, line-addressable artifact, and capture related instruments (annexes, value-set spreadsheets, translation bundles).

### 1.1 The "drop dated PDF in `raw/`, never edit" rule

Every questionnaire version received from ASPSI / DOH is dropped in `raw/` with the version date in the filename — `Annex F1 Facility Head Survey Questionnaire April 20.pdf`. The original is **never edited**. When a new version arrives, the old one stays (it's history); the new one lands beside it with its own date.

**Why immutable raw**:

1. **Diffability** — Phase 4 spec walks need to compare "what was the question text on April 08 vs April 20?" If the old PDF was overwritten, that diff is lost.
2. **Audit trail** — when a finding traces back to a specific question wording, the cited version has to exist in `raw/` exactly as the questionnaire team produced it.
3. **No accidental drift** — if Phase 1 ingestion edited the PDF (e.g. to fix a typo), every downstream artifact would silently diverge from the version the client believes is canonical.

The project CLAUDE.md is unambiguous: *"NEVER modify files in `/raw/`. They are immutable source documents."*

### 1.2 Text extraction

PDFs are not grep-able as-is. Phase 4 (skip-logic walks) and Phase 3 (generator inputs) both need a `.txt` extract. The extract is **derived data** — it lives in `deliverables/CSPro/<Instrument>/inputs/` (or wherever the consuming generator is), not in `raw/`. If the extraction tool changes, the extract is regenerated, never hand-corrected.

**Recommended path: `pdfplumber` in Python.** Pandoc handles many formats but `pdfplumber` gives more control over column-aware extraction, which matters for questionnaire PDFs where question number / question text / response options share rows.

**Snippet** — `scripts/extract_questionnaire.py`:

```python
"""Extract a questionnaire PDF to a clean text file for grep + generator input."""
import argparse
import re
from pathlib import Path

import pdfplumber


def extract(pdf_path: Path, out_path: Path) -> None:
    """Extract every page of the PDF into a single .txt with page markers."""
    lines: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_no, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            # collapse runs of whitespace inside lines but preserve line breaks
            page_lines = [re.sub(r"\s+", " ", ln).strip() for ln in text.splitlines()]
            page_lines = [ln for ln in page_lines if ln]
            lines.append(f"\n===== PAGE {page_no} =====\n")
            lines.extend(page_lines)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out_path} ({len(lines)} lines)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", type=Path)
    ap.add_argument("out", type=Path)
    args = ap.parse_args()
    extract(args.pdf, args.out)
```

**Run** — produce `F1_clean.txt` from the April 20 PDF:

```powershell
uv run python scripts\extract_questionnaire.py `
    raw\Annex F1 Facility Head Survey Questionnaire April 20.pdf `
    deliverables\CSPro\F1\inputs\F1_clean.txt
```

The output is grep-able and addressable by line number, which is what Phase 4's skip-walk and the cross-field rule citations rely on. The `===== PAGE N =====` marker preserves page-citation accuracy.

**Pandoc fallback** — for PDFs where `pdfplumber` mis-detects column boundaries (rare, mostly for two-column Filipino translations), pandoc can be tried:

```powershell
pandoc "raw\Annex F1 Facility Head Survey Questionnaire April 20.pdf" `
    -o deliverables\CSPro\F1\inputs\F1_pandoc.txt --to plain
```

The `pdfplumber` output is preferred when the two diverge.

### 1.3 Wiki source page template

Every source — questionnaire, annex, contract, reference manual, meeting minutes — gets exactly one page in `wiki/sources/`. The page is the citation target for everything downstream. The exemplar is [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F1 Facility Head Survey Questionnaire|Source - Annex F1 Facility Head Survey Questionnaire]].

**Minimum frontmatter**:

```yaml
---
type: source-summary
source: "[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/Annex F1 Facility Head Survey Questionnaire April 20.pdf]]"
date_ingested: 2026-04-20
tags: [questionnaire, f1, facility-head, capi, uhc-y2]
---
```

**Section template**:

```markdown
# Source - <Title>

> **Version**: <date on the PDF cover page>
> **Pages**: <count>
> **Item count**: <n items>
> **Mode**: <CAPI | self-admin | paper>
> **Sections**: <A, B, C, ... — list>

## What this is

<one paragraph: who issued it, when, what it's for>

## Section map

| Section | Pages | Items | Topic |
|---|---|---|---|
| A | 1–3 | 12 | <topic> |
| B | 4–7 | 18 | <topic> |
| ... | ... | ... | ... |

Total: <n items, n pages>.

## Eligibility rules

<who fills this out; gates that determine eligibility>

## Skip-logic notes (initial pass)

<bulleted list of major skip patterns, "go to" markers, conditional sections — full
walk happens in Phase 4>

## Mode-relevant flags

<CAPI-specific notes: dynamic value sets, fills, multi-language; or PWA-specific
notes: self-admin gates, partial save expectations>

## Changes from prior version

<diff against the previous version PDF — item count delta, sections added/removed>

## Cross-references

- Linked from: [[index]], [[02-Phase-0-2-Foundation]], <other guide files>
- Related: [[wiki/sources/Source - <related>]], [[wiki/concepts/<concept>]]
```

The page is grep-able and serves as the citation target for every later artifact: "F1 Q47 (page 12, see [[Source - Annex F1 Facility Head Survey Questionnaire]])".

### 1.4 Per-instrument ingestion checklist

UHC Year 2 has three CAPI instruments. Each one runs through Phase 1 once per version. The April 20 versions are the current baseline.

**F1 — Facility Head** (April 20 ver., 37 pages, 166 items, Sections A–H + Secondary Data):

- [x] `raw/Annex F1 Facility Head Survey Questionnaire April 20.pdf` dropped.
- [x] `deliverables/CSPro/F1/inputs/F1_clean.txt` extracted (pdfplumber).
- [x] `wiki/sources/Source - Annex F1 Facility Head Survey Questionnaire.md` summarizes 37 pp / 166 items / Sections A–H + Secondary Data; +40 items vs Apr 08 noted in change log.
- [x] Linked from `index.md` Wiki Catalog → Sources.
- [ ] Cross-linked from `wiki/sources/Source - Annex G DOH Recommendations Matrix` (the change-rationale source for what changed Apr 08 → Apr 20).

**F3 — Patient** (April 20 ver., 178 items, Sections A–L):

- [x] `raw/Annex F3 Patient Survey Questionnaire April 20.pdf` dropped.
- [x] `deliverables/CSPro/F3/inputs/F3_clean.txt` extracted.
- [x] `wiki/sources/Source - Annex F3 Patient Survey Questionnaire.md` summarizes Sections A–L, CAPI inpatient + outpatient flows, +52 items vs Apr 08.
- [x] Linked from `index.md`.

**F4 — Household** (April 20 ver., 202 items, Sections A–Q):

- [x] `raw/Annex F4 Household Survey Questionnaire April 20.pdf` dropped.
- [x] `deliverables/CSPro/F4/inputs/F4_clean.txt` extracted.
- [x] `wiki/sources/Source - Annex F4 Household Survey Questionnaire.md` summarizes Sections A–Q, community survey, interval sampling from patient HH.
- [x] Linked from `index.md`.

When the next version of any instrument lands, the cycle repeats: drop the new PDF in `raw/` (with its own date), regenerate the `*_clean.txt`, append a "Changes from prior version" section to the existing wiki page (don't create a second page — there's still only one F1 source). The version marker in the PDF filename plus the change log section preserves history.

### 1.5 Related-instrument ingestion

Beyond the four questionnaires, UHC Year 2 has a pile of annexes that also need source pages. Each is consulted regularly during Phases 3–10:

| Annex | What it is | Why CAPI cares |
|---|---|---|
| **Annex A — Data to be Collected and Sources** | Data-to-sources crosswalk + CHE methodology + F1 Secondary Data template (Patient Load, HR matrix, YAKAP/Konsulta services + pricing). | F1's Secondary Data record is *defined* by Annex A. Without ingest, the F1 generator can't model the secondary-data section. |
| **Annex B — List of UHC Integration Sites** | 107 UHC IS as of Nov 2025, by integration year × region × class. | Sampling-frame input for F1/F4. The facility master in `deliverables/Survey-Manual/Appendix-D` references Annex B + C. |
| **Annex C — List of Non-UHC Integration Sites** | 13 non-UHC IS as of Nov 2025. | Sampling-frame input for F1/F4. |
| **Annex D — Replacement Protocol** | ≥3-visit minimum contact protocol; same-stratum substitution; 5–10% facility cap; enumerator discretion banned. | Field-ops protocol that the FIELD_CONTROL block in CAPI must enforce (disposition codes + replacement reason coding). |
| **Annex E — Suggested Indicators** | 104-indicator matrix × 8 HLRQs with DOH RETAIN/AMEND/OMIT verdicts and Year 2 source crosswalk. | Drives the Phase 11 codebook + Phase 10 interim cross-tabs. |
| **Annex G — DOH Recommendations Matrix** | 23 remarks from PMSMD / ADB (Xylee Javier) / DOH 11th EXECOM Sep 2024, with ASPSI response per remark. | Change-rationale map for the Apr 20 questionnaire revisions. Cite this when explaining "why does Q47 exist?" |
| **Annex H — Informed Consent Forms** | 4 ICFs (F1/F2/F3/F4); F3/F4 PhP 100 token + witness clause; F2 PhP 1,000 raffle. | The CAPI intro screens must mirror this verbatim. SJREB-approvable text. |
| **Annex I — Dummy Tables** | 51 tabulation specs: A1–A14 (F1), B1–B10 (F2), C1–C18 (F3), D1–D9 (F4). | Drives the Phase 10 CSTab cross-tab definitions and Phase 11 codebook. |

Each annex gets its own `wiki/sources/Source - Annex <Letter> <Title>.md` summary page following the §1.3 template. Each is linked from `index.md`. Phase 4 and Phase 5 cross-link annexes wherever a question's design rationale traces back to a remark in Annex G.

### 1.6 PSGC source ingestion

PSGC (Philippine Standard Geographic Code) is the geographic backbone for every CAPI instrument — region / province / city / barangay codes appear on every cover sheet. The PSA 1Q 2026 PSGC drop is treated like any other source:

- **Source CSVs** at `deliverables/CSPro/F1/inputs/psgc_*.csv`. (F1's `inputs/` is the canonical home; F3 and F4 read from the same CSVs via the shared lookup pipeline.)
- **Generator** at `deliverables/CSPro/shared/build_psgc_lookups.py` reads the CSVs and emits four external-dictionary `.dcf` + fixed-width `.dat` pairs (`psgc_region`, `psgc_province`, `psgc_city`, `psgc_barangay`).
- **Reusable CSPro logic** at `deliverables/CSPro/shared/PSGC-Cascade.apc` exposes four functions (`FillRegionValueSet`, `FillProvinceValueSet`, `FillCityValueSet`, `FillBarangayValueSet`) called from each form's `onfocus` events to drive the cascading region → province → city → barangay dropdowns.
- **Concept page** at [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/PSGC Value Sets|PSGC Value Sets]] documents the architecture and the reason for externalization (DCFs shrink 17 MB → ~1 MB).

The PSGC pipeline is the prototype for *any* large external value set in this project. New large lookups (e.g. facility master from Survey Manual Appendix D) follow the same pattern: CSV in `inputs/`, generator in `shared/`, external dictionary, `.apc` cascade module if cascading.

### 1.7 Khurshid's ingestion alternatives

Khurshid documents two GUI alternatives to the Python-generator approach:

**Excel-to-CSPro tool (Khurshid 2023-01-12)** — `Tools → Excel to CSPro`. Two tabs:

- **Tab 1**: convert an Excel data file into a CSPro `.dat` using a column-mapping wizard. Per-record mapping to worksheet, per-item mapping to column, four case-management modes (create new / modify-add / modify-add-or-delete / skip-if-newer). Use `Assign default mappings` if Excel column order matches dictionary item order.
- **Tab 2**: auto-generate a CSPro dictionary from an Excel sheet's contents. Click **Analyze Worksheet**, then per column set Include / Name / ID / Numeric / Alpha length / Decimal handling / Create-value-set (only for numerics with <500 unique values) / Zero-fill / Explicit decimal char. Emit dictionary, level, record names from a single **Name Prefix**.

**Multi-worksheet conversion (Khurshid 2023-01-16)** — for an Excel file with two related sheets (e.g. `housing` + `person`), generate one dictionary per sheet first, then **copy the record** between dictionaries: open `housing_dict` → Record Properties → `Ctrl+C` → open `census_dict` → Record Properties → `Ctrl+V` → choose **After** → set the merged person record max to 30 → save. Then use `View → Layout` (`Ctrl+L`) to verify the **record-type indicator is at starting position 1** (auto-merge sometimes places it elsewhere). The Item-to-Column mapping in the conversion wizard requires `Assign default mappings` per record — clicking it once doesn't fan out across all records.

**Why we don't use these for UHC Year 2** — the project's first design rule is **generator over hand-edit**. A `.dcf` produced by a Python generator can be regenerated from the spec on every revision; a `.dcf` produced through a GUI wizard can only be regenerated by walking through the wizard again, with no commit log of what changed. Khurshid's Tab-2 generator and the multi-sheet merge produce *one-shot* dictionaries that have no reproducible re-emit path; that breaks the rule.

**Where Khurshid's tools still earn their keep** — for **one-off ingest of legacy spreadsheets**:

- Annex A's secondary-data templates (Patient Load matrix, HR matrix, YAKAP/Konsulta service-and-pricing tables) arrive as Excel. If we ever need to materialize them as CSPro lookup data for a CAPI feature, Khurshid 2023-01-12 Tab-1 (data conversion) is the fastest path — the dictionary is hand-authored once in our generator, and the data is a one-shot conversion through Tools → Excel to CSPro.
- The PSGC bootstrap could have used Khurshid's Tab-1 to convert PSA's master CSVs to `.dat`. We didn't, because the Python generator at `build_psgc_lookups.py` produces the same output and stays under version control as code, not as a wizard interaction. Same trade-off in miniature.

The **`Tools → Reformat`** function (also part of Khurshid's repertoire) is useful for legacy data ingest where the column layout differs from what the generated `.dcf` expects. Reformat is one-shot and thus follows the same "use for legacy ingest, never for evolving sources" rule.

### 1.8 Phase 1 exit criteria

- [ ] Every questionnaire (F1 / F3 / F4) has a dated PDF in `raw/` and a `_clean.txt` extract under `deliverables/CSPro/<Instrument>/inputs/`.
- [ ] Every questionnaire has a wiki source page with frontmatter, full section map, page count, item count, eligibility rules, skip-logic notes, mode-relevant flags, and a "Changes from prior version" section if applicable.
- [ ] Every annex (A, B, C, D, E, G, H, I) has a wiki source page.
- [ ] Every wiki source page is linked from `index.md`.
- [ ] PSGC source CSVs are in place and the `shared/` lookup pipeline emits region / province / city / barangay `.dcf` + `.dat`.
- [ ] You can run `grep "Q47" deliverables/CSPro/F1/inputs/F1_clean.txt` and find the question text + page boundary.
- [ ] You can cite *any* question by page and number: "F1 Q47 page 12, [[Source - Annex F1 Facility Head Survey Questionnaire]]".

When all rows pass, Phase 4 (skip-logic spec) can begin against a stable base.

---

## Phase 2 — Tool knowledge base *(reusable across instruments)*

**Objective**: Build a focused vocabulary of toolchain concepts before writing any generator or PROC code. Done **once per consultant per stack**; reused on every project on that stack.

### 2.1 Why this phase exists

The CSPro 8.0 Users Guide is **958 pages**. It is comprehensive, accurate, and unindexed for the kinds of questions a CAPI developer asks day-to-day — "what fires before what?", "how do I switch a value set at runtime?", "what's the order of preproc / postproc / onfocus / killfocus?".

Re-reading the Users Guide every time a question lands does not scale. Phase 2 inverts the access pattern: extract the relevant patterns into focused **concept pages** keyed to the developer's mental questions, then maintain those pages as living documents.

The cost is one investment week of reading + summarizing per stack (CSPro, CSWeb, CSEntry Android). The payoff is that every subsequent phase queries a 1–3 page concept doc instead of grepping a 958-page PDF.

### 2.2 The 12 CSPro concept pages

UHC Year 2's `wiki/concepts/` already holds the 12 CSPro concept pages enumerated below. Each is anchored on the relevant chapter of the Users Guide and tightened to project-relevant patterns.

1. **[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Data Dictionary|CSPro Data Dictionary]]** — `.dcf` schema: levels, records, items (numeric / alpha / binary), value sets, ID items, subitems, relations, modes (Relative vs Absolute), dictionary types (Main / External / Working / Special Output), multi-language dictionaries, `View → Dictionary Analysis` lint pass, security / encryption.
2. **[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Language Fundamentals|CSPro Language Fundamentals]]** — PROC GLOBAL, declarations, logic objects, variables, expressions, operators, the `numeric` / `alpha` / `string` / `array` / `dictionary` / `valueset` types.
3. **[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Logic Events|CSPro Logic Events]]** — `preproc` / `postproc` / `onfocus` / `killfocus` / `onoccchange` order of execution. **Critical for skip wiring** — getting the event wrong means logic fires at the wrong time and skips don't trigger as the questionnaire reads.
4. **[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Data Entry Modes|CSPro Data Entry Modes]]** — system- vs operator-controlled; heads-up vs heads-down. UHC Year 2 is system-controlled across the board (CAPI default).
5. **[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Capture Types|CSPro Capture Types]]** — Text Box, Radio, Drop Down, Number Pad, Date, etc. Per-item rendering choice tuned for tablet entry speed.
6. **[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro CAPI Strategies|CSPro CAPI Strategies]]** — forms, fields, questions, blocks, partial save, prefilling, scrolling rules, system-controlled organization, FAQ section placement.
7. **[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Question Text and Fills|CSPro Question Text and Fills]]** — fills (`~~item~~`), HTML in question text, conditional question text, color conventions (interviewer-read vs interviewer-instruction).
8. **[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Multi-Language Applications|CSPro Multi-Language Applications]]** — multi-language labels, `tr`, `setlanguage`. Relevant to UHC Year 2 because Filipino + 6 dialects (per May 4 meeting) are in scope, but the dictionary itself stays English; multi-language is at the CAPI label layer.
9. **[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Synchronization|CSPro Synchronization]]** — sync architecture, `sync*` functions, troubleshooting.
10. **[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Batch Editing|CSPro Batch Editing]]** — CSBatch, structure / validity / consistency checks, hot decks, imputation.
11. **[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Tabulation|CSPro Tabulation]]** — CSTab, cross-tabs, area processing, weights, summary stats. Drives Annex I dummy-table production.
12. **[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/F-Series Value Set Conventions|F-Series Value Set Conventions]]** — *(project-internal)* the rule that **NA = highest valid code at the field width** (9 / 99 / 999), and **never** use CSPro's special value `notappl` in a value set (it collides with skip-handling). Ratified at F1 Designer sign-off, applies to F1/F3/F4.

These 12 pages are the **vocabulary floor** — Phase 3+ assumes the developer can answer "what is preproc?", "what is a value set?", "what is a block?" without re-reading the Users Guide.

### 2.3 Sample concept page

The format below is the project standard. Frontmatter declares page type + tags + source count; H2 sections break the topic into named patterns; tables enumerate fixed sets (event order, properties, options); code blocks show paste-ready idioms; H2 `Project relevance` ties the concept to UHC Year 2 specifics. Excerpt from [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro Logic Events|CSPro Logic Events]]:

```markdown
---
type: concept
tags: [cspro, logic, procedural, events, blocks, consistency-edits]
source_count: 1
---

# CSPro Logic Events

CSPro data entry applications execute logic at well-defined points in the
data entry lifecycle. Understanding the order of these events is essential
for writing correct skip logic, validations, and prefills — and for placing
each piece of code in the right procedure so it fires at the right time.

## The procedural sections

Every dictionary element (form file, level, form, roster, record, item,
block) can have one or more procedural sections attached. The available
sections, in firing order:

| Section | Fires |
|---|---|
| `preproc` | **Before** entering the element. Use for initialization, prefills, conditional skips. |
| `onfocus` | When the cursor arrives on the element. Use for value-set switching, dynamic question text setup. |
| `onoccchange` | When the current occurrence of a repeated element changes (rosters). |
| `killfocus` | When the cursor leaves the element. Use for cross-field validations that should fire as the operator moves on. |
| `postproc` | **After** the element is fully entered. Use for end-of-block consistency edits. |

## Default event order

For a two-level data entry application with no skip/advance statements,
the natural flow is:

    Form File preproc
        Level 1 preproc
            Form 1 preproc
            Form 1 onfocus
                Field 1.1 preproc
                Field 1.1 onfocus
                (entry of Field 1.1)
                Field 1.1 killfocus
                Field 1.1 postproc
                ...

## Project relevance

- **Block usage for date entry** — F1, F3, F4 all collect dates (interview date,
  birth date, last visit). Use a block per date so all three fields appear on
  one tablet screen and the validation runs in the block's `postproc`.
- **`onfocus` for value-set switching** — F3 outpatient/inpatient routing and
  F4 person-conditional questions both follow the MyCAPI walkthrough's
  `setvalueset` in `onfocus` pattern.
- **`postproc` for cross-field consistency** — every "if A, then B" check in
  the F1/F3/F4 questionnaires (e.g., facility type vs services offered, age
  vs fertility questions) should live in the `postproc` of the field that
  triggers the check, with `errmsg` + `reenter` for blocking corrections.

## Sources

- (Source: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSPro 8.0 Complete Users Guide]])
```

The **Project relevance** section is what turns a generic CSPro topic into a UHC Year 2 design decision — it's the bridge from "what CSPro does" to "what this project does with it." Every concept page should carry that section.

### 2.4 CSWeb concept set

CSPro is the authoring tool; CSWeb is the sync server. Phase 8 (CSWeb provisioning + tablet bring-up) needs its own vocabulary, parallel to the CSPro set. The CSWeb concept set:

- **[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSWeb|CSWeb]]** — overall architecture: Wampserver (Apache + MySQL + PHP) hosts CSWeb; tablets sync via the CSWeb API URL (`http://<host>/<csweb-folder>/api/`); cases land in the MySQL backing DB.
- **CSWeb dashboards** — five built-in dashboards (Sync Report, Map Report, etc.) scoped via the **5-dashboards permission axis**. Per-dashboard visibility is configured per role / per user.
- **CSWeb roles** — two built-in roles: **Administrator** (full access, can manage users + permissions), **Standard User** (configurable scope). Per the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - CSWeb Users Guide|CSWeb Users Guide]], permission is on **two axes**: (1) which dashboards the role/user can see, (2) per-dictionary up/down (can sync data up to server / can pull data down to tablet).
- **CSWeb sync sessions** — a single sync round-trip is one session: the tablet authenticates with the CSWeb server, the server checks the user has up-permission for the dictionary the tablet wants to push, the cases are uploaded, the server records the session, and the tablet acknowledges.
- **CSWeb backing DB** — MySQL DB created in phpMyAdmin during install **(Khurshid 2022-03-14)**. Khurshid uses `test_application` as the example DB name; UHC Year 2 will use a project-specific name (e.g. `aspsi_doh_uhc_y2`). The root account password is set in phpMyAdmin → Privileges → root → Edit privileges → Change password, then re-used in the CSWeb setup script. The setup script asks for: database name, host (`localhost`), DB user (`root`), DB password (the one just set), CSWeb admin password (separate credential for the `admin` web login), path to file directory, CSWeb API URL.
- **CSWeb CSV bulk user import** — Standard Users can be created in bulk from a CSV file. Useful for provisioning the full enumerator + STL roster at once. Format documented in the CSWeb Users Guide source page.

The CSWeb concept set anchors Phase 8. Carl reads it once and Phase 8 becomes a runbook of "do step X from concept page Y" rather than a chase through the CSWeb Users Guide.

### 2.5 CSEntry Android concept set

CSEntry Android is the runtime that runs the `.pen` package on tablets. Phase 6 (build) and Phase 7 (testing) need its vocabulary:

- **CSEntry app lifecycle** — the `.pen` package is installed once; cases are stored locally; sync moves them to CSWeb. App-update path: push a new `.pen` (or PFF) to the tablet over USB / cloud / sync. The app does not auto-update from a server; that's a deliberate out-of-the-box choice (apps are pinned per fieldwork wave).
- **Partial save** — interviews can be saved incomplete and resumed. Triggered by `OnStop` (operator presses Stop / Alt+F4 on tablet) or by an interview interruption. The `ispartial` function tests whether the current case is a partial save.
- **Sync trigger** — on Android, sync can be triggered by: (a) operator manually from the menu, (b) `syncconnect` / `syncdata` calls in PROC logic, (c) periodic schedule if configured. The Phase 8 deployment will use a combination — operator-triggered for end-of-day uploads + automatic on-app-launch for downloading config updates.
- **Paradata GPS** — CSPro's `gps` function captures lat/long; UHC Year 2 wires this into the FIELD_CONTROL block per the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/GPS and Photo Capture|GPS and Photo Capture]] concept page. Auto-capture at facility arrival (F1/F3) and at household entry (F4); end-of-interview verification photo per the same concept page.
- **File-based vs window-based trace** **(Khurshid 2023-09-19)** — `trace(on)` outputs to a debug window on Windows, but **window-based trace output is ignored on Android**. For tablet debugging, use the file-based form: `trace(on, "trace_file.txt");` (append) or `trace(on, "trace_file.txt", clear);` (wipe before writing). The file lands in the application folder; pull it off the tablet via USB or sync to inspect. **File-based trace is REQUIRED for Android** debugging — without it, field-reported issues that don't reproduce on Windows have no telemetry. Phase 7 testing leans on this; Phase 10 fieldwork support uses it for live-investigation of enumerator-reported anomalies.

### 2.6 Khurshid corpus as a teaching layer

Phase 2 isn't only about the Users Guides. The **Khurshid Arshad CAPI corpus** (74 videos at `3_Resources/Learning-Materials/mentors/khurshid-arshad/`) is a parallel teaching layer — pattern-by-pattern, with code that has been tried in real censuses and household surveys. Each video has a `techniques.md` card file at `videos/<date>_<title>_<youtube-id>/techniques.md` (the four read for this guide are listed in the bibliography in §2.8).

The corpus is **organized by CAPI phase** in [[3_Resources/Learning-Materials/mentors/khurshid-arshad/_index|the corpus index]]. The "By CAPI phase" section maps each video to the workflow phase it belongs to — Phase 0, Phase 1, Phase 3, Phase 6, Phase 7, etc. The recommendation is straightforward:

> **Before each phase, read the Khurshid videos tagged for that phase.**

For Phase 0–2 (this guide), the relevant cards are:

- **Phase 0 — Project scaffolding**: Khurshid 2022-03-14 (CSPro / CSWeb / Wampserver install), Khurshid 2022-03-27 (folder convention).
- **Phase 1 — Source ingestion**: Khurshid 2023-01-12 (Excel-to-CSPro), Khurshid 2023-01-16 (multi-worksheet conversion).
- **Phase 2 — Tool knowledge base**: read the corpus index's "By CSPro topic" section to spot tutorials on the 12 concepts; cherry-pick where the Users Guide is unclear (logic events, dynamic value sets, trace function, rosters).

The corpus is *not* a substitute for the Users Guide or the concept pages. It's the teaching layer on top — the Users Guide tells you what CSPro can do; the concept pages tell you how UHC Year 2 uses it; Khurshid shows you somebody else doing it on a real survey, with the gotchas.

### 2.7 Phase 2 exit criteria

- [ ] Each of the 12 CSPro concepts is reachable from `wiki/concepts/` and is linked from `index.md` under "CSPro toolchain (from the 8.0 Users Guide)".
- [ ] The 12 concept pages each carry frontmatter, the standard H2 sections, a "Project relevance" section, and a Sources section pointing back to the Users Guide.
- [ ] CSWeb concept set exists: `CSWeb`, plus dashboards / roles / sync sessions / backing DB / CSV bulk import covered (either as their own pages or as labeled sections inside `CSWeb.md`).
- [ ] CSEntry Android concept set exists: lifecycle, partial save, sync trigger, paradata GPS, file-based vs window-based trace.
- [ ] [[3_Resources/Learning-Materials/mentors/khurshid-arshad/_index|the Khurshid corpus index]] is linked from `index.md` and from this Phase 2 doc; the "By CAPI phase" section is the recommended pre-read for each phase.
- [ ] You can answer "how does CSPro do X?" by reading at most one concept page, **without** opening the 958-page Users Guide.

When the exit criteria pass, Phase 3 (the `.dcf` generator) can move at speed — every helper function, every event-placement decision, every value-set encoding can cite a concept page rather than re-reasoning from scratch.

### 2.8 Reading bibliography for this guide

This Phase 0–2 guide was assembled from the following sources, all readable from the project vault:

- [[CAPI-Development-Workflow|CAPI Development Workflow template]] — Phases 0, 1, 2 (the "what" each phase produces).
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/CLAUDE|Project CLAUDE.md]] — folder schema, page types, conventions, operations, rules.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/index|Project index.md]] — current wiki catalog (sources, entities, concepts, analyses) and deliverable inventory.
- **(Khurshid 2022-03-14)** — `2022-03-14_cspro-how-to-install-wampserver-cspro-and-csweb-server_wSCsiWpe5Mk/techniques.md` — VC++ prerequisites, Wampserver install, CSPro Designer install, CSWeb deployment, phpMyAdmin DB creation, CSWeb setup script.
- **(Khurshid 2022-03-27)** — `2022-03-27_tutorial1-create-login-application-in-cspro_HjtqgsCppV4/techniques.md` — application folder convention with numbered subdirs, external dictionary single-level constraint, ID items + zero-fill, decimal-character semantics, form-build keyboard shortcuts, protected fields.
- **(Khurshid 2023-01-12)** — `2023-01-12_tutorial-on-excel-to-cspro_EoUqSqDg7vY/techniques.md` — Excel-to-CSPro Tab 1 (data) + Tab 2 (dictionary); analyze-worksheet wizard; default mappings; record-max for multi-occurrence imports.
- **(Khurshid 2023-01-16)** — `2023-01-16_tutorial-on-create-a-dictionary-and-dataset-using-multi-work_KBu7nkwirJ8/techniques.md` — multi-worksheet conversion; copy-paste record between dictionaries; record-type indicator at starting position 1; per-record assign-default-mappings.
- **(Khurshid 2023-09-19)** — `2023-09-19_tutorial-on-trace-function_LtjiYZosfJg/techniques.md` — `trace(on)` / `trace(off)`; file-based trace required for Android; `clear` keyword to wipe the trace file each launch.
- 12 CSPro concept pages under `wiki/concepts/`. The four read in detail for this guide: `CSPro Data Dictionary`, `CSPro Logic Events`, `CSPro CAPI Strategies`, `F-Series Value Set Conventions`.

---

## Cross-phase: living docs and updates

The three artifacts produced by Phases 0–2 are **living documents**. None of them is "done" once written — they're updated whenever the project teaches a new lesson.

### The CAPI Workflow template

The reusable template at `2_Areas/IT-Standards/templates/CAPI-Development-Workflow.md` is the master living document. The convention is documented in the template itself:

> *"Append a row each time a project teaches you something new. The workflow gets sharper with every instrument."*

The template's **Living-document log** tracks the refinements: F1 codification (2026-04-10), F2 PWA codification (2026-04-25). Each row says what was added and which project taught it. Every UHC Year 2 instrument that ships should append a row when it teaches a generalizable lesson — not a project-specific lesson, but a workflow-level one (e.g. "added Phase 7 file-based-trace requirement after F1 Android testing").

When this guide finds a phase pattern that should be promoted into the template — e.g. the `0.6 Python toolchain setup` block — it goes into the template, not just here. The template is the cross-project version; this guide is the UHC Year 2 instance.

### Concept pages

The 12 CSPro concept pages were initially written from the Users Guide. As fieldwork progresses, each one should grow a **"Field findings"** section recording what reality teaches:

```markdown
## Field findings

- **2026-MM-DD (F3 pretest)**: discovered that `setvalueset` in `onfocus`
  fires **before** the field's `preproc` — meaning a `preproc`-driven
  default value cannot reference the value set chosen by `onfocus`.
  Workaround: set the default in `onfocus` after `setvalueset`, not
  in `preproc`. Pattern documented in
  [[F3-Skip-Logic-and-Validations]] §<n>.
```

The "Field findings" section turns a static concept page into a **per-project codebook of CSPro behavior** — something the next project starting on the same stack reads first to skip the gotchas. This is how the concept set pays off across more than one engagement: the first project pays the documentation cost, every subsequent project reads the result.

### Source pages

Source pages also live. When a new version of an annex lands (e.g. F4 April 30 supersedes F4 April 20), the F4 source page gets a new `## Changes from prior version` block; the previous PDF stays in `raw/` (with its date in the filename); the new PDF lands beside it. The source page never gets duplicated — there is one F4 source page across the project's lifetime, with version history embedded.

### What "living document" rules out

The living-doc convention is *not* a license for lazy edits. The rules:

1. **Frontmatter `last_updated` bumps** every time the body changes meaningfully.
2. **Append, don't rewrite.** A "Field findings" entry is dated and additive; it doesn't quietly change a previously-correct sentence.
3. **Explicit deprecation.** If a previously documented pattern no longer applies, mark it `> [!warning] Superseded by ...` rather than deleting it. The history matters when a future reader hits the old pattern in legacy code.
4. **Cross-link the trigger.** When a finding gets added, link to the artifact that surfaced it — the standup, the bug, the meeting note — so the trail is complete.

The same rules apply to this guide. When Phase 0–2 changes substantively (a new instrument, a new toolchain prereq, a new concept page), the change lands here with a `last_updated` bump and an explicit note, not a silent rewrite.

---

## Next

[[03-Phase-3-5-Spec-and-Generators]] — the Python `.dcf` generator, the skip-logic spec, and the three-tier validation classification (HARD / SOFT / GATE) that turns this foundation into a build-ready dictionary.
