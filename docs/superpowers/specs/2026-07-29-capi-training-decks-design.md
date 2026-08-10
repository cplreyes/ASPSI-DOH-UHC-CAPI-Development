# CAPI Training Decks (Field Supervisor + Field Enumerator) — Design

- **Date:** 2026-07-29
- **Author:** Carl Patrick Reyes (with Claude)
- **Status:** Design approved — spec under review
- **Deliverable:** two presentation-ready `.pptx` decks for Carl's named sessions in the
  UHC Survey Year 2 field trainings (August 2026)
- **Supersedes:** `UHC-Y2-CAPI-Training-CReyes-DRAFT.pptx` (66 slides) and
  `UHC-Y2-CAPI-Training-CReyes-PRESENTATION.pptx` (24 slides), both built 2026-07-27.
  **Carl's decision 2026-07-29: do not carry these forward — build new.**

## 1. Why

Myra issued two five-day training programmes (ingested 2026-07-29:
[[Source - Field Supervisor Training Program (MESJ 2026-07-28 FINAL)]] and
[[Source - Field Enumerator Training Program (v2 MESJ 2026-07)]]). **Carl ("CReyes") is the
named in-charge of the CAPI sessions in both** — the only individual named for technical
content in either document.

The July decks cannot be patched to fit, for three independent reasons:

1. **They were built against a superseded draft.** That draft gave Carl Modules 7–10; the
   FINAL programme gives him **Module 6 "Using CAPI"** plus four walkthroughs.
2. **F4 Household was explicitly excluded** from those decks (assigned to Aidan). The FINAL
   programme assigns the 14:30 Household walkthrough to **"CReyes & Assigned RAs"** — an
   entire instrument of missing content.
3. **They are supervisor-only.** There is no enumerator deck for a cohort of ~122–125 FEs
   trained across four simultaneous venues.

## 2. Benchmark (what comparable surveys do)

| Programme | Shape | CAPI practice |
|---|---|---|
| **DHS** | ~4-week main training after a pretest round | 3 days field practice in non-sampled clusters; mock + demonstration interviews; **9-module Master Trainer package with example tests and an on-device QuizApp** |
| **MICS6** | Template agenda; **CSPro on tablets — our exact toolchain** | 2 days field practice + 1 pilot day; supervisors receive an **additional supervision module** |
| **LSMS (World Bank)** | Progressive practice ladder | **group practice → front-of-class role-play → classroom interviews with on-site respondents → field practice**; CAPI taught as a **module distinct from questionnaire content**; competency scored via written tests + scoring matrices |

**Three design consequences:**

- **Compression.** Our programme does in **five days** what DHS spends ~4 weeks on. The CAPI
  sessions therefore cannot be lecture-shaped — every slide must drive a hands-on action.
- **Separation.** MICS and LSMS both split *using the software* from *the questionnaire
  content*. Myra's programmes already do this (Module 6/9 = using CAPI, then per-instrument
  walkthroughs), so the module library follows the same seam.
- **Modularity.** DHS ships a Master Trainer **package of modules with tests**, not a deck.
  This project's own earlier gap analysis reached the same conclusion independently
  (`Analysis - DHS Benchmark vs ASPSI CAPI Gap Analysis`, finding **G8**: *"Aug training is
  contractual; a hands-on module set beats lecture slides"*).

Sources: [DHS – Training Field Staff](https://dhsprogram.com/pubs/pdf/DHSM3/Training_Field_Staff_for_DHS_Surveys_Oct2009.doc) ·
[DHS Data Quality MR30](https://dhsprogram.com/pubs/pdf/MR30/MR30.pdf) ·
[LSMS – A Practical Guide to Fieldwork Training](https://lsms-worldbank.github.io/pg2sq-training/) ·
[UNICEF MICS – CAPI](https://mics.unicef.org/node/3131)

## 3. Architecture — modular library composed into two decks

**Chosen: modular (option B).** Content for the four instruments is identical for both
audiences; only the framing differs. Authoring each topic once avoids double maintenance,
and the modules double as the **train-the-trainer kit** the RAs need to run the three
enumerator venues Carl cannot attend.

### 3.1 Module library

| # | Module | Content | Decks |
|---|---|---|---|
| **A** | Why CAPI | What changes vs paper; the four instruments at a glance | both |
| **B** | Install & connect | Add Application from CSWeb; the server address; updating by **remove + re-add** | both |
| **C** | Login & your assignment | Hub sign-in, role menu, case list | both |
| **D** | Navigating a questionnaire | Question types; **Required / Soft Warning / Hard Warning**; DK/RF; suspend & resume | both |
| **E** | F1 Facility Head | The 13 real sections from `F1/*.fmf` | both |
| **F** | F2 Health Care Worker | Self-administered via QR/link — **not CSEntry**; the instrument that behaves differently | both |
| **G** | F3 Patients (in/outpatient) | The Patient-Type gate branch; cost matrices | both |
| **H** | F4 Household | **New content — now Carl's slot**; roster + expenditure blocks | both |
| **I** | Completing a case | Result-of-Visit / BREAKOFF codes | both |
| **J** | Sync to CSWeb | Daily by 10:00 PM; upload-failed handling | both |
| **K** | Troubleshooting & escalation | **FE → FS → RA → Data Programmer** (never IT direct) | both |
| **L** | Monitoring from CAPI data | Console: sync dashboard, coverage, data quality | **FS pack only** (see §6) |

### 3.2 Composition — Field Supervisor deck

Mapped to the FINAL programme's Day 2 (Los Baños, August 2026):

| Slot | Duration | Programme item | Modules |
|---|---|---|---|
| 08:00–09:00 | 60 min | **Module 6: Using CAPI** | A + B + C + D |
| 09:00–10:30 | 90 min | Walkthrough — FACILITY HEAD (F1) | E **+ I + J + K** |
| 10:30–12:00 | 90 min | Walkthrough — HEALTH CARE WORKER (F2) | F |
| 13:00–14:30 | 90 min | Walkthrough — PATIENTS (inpatient and outpatient) | G |
| 14:30–16:00 | 90 min | Walkthrough — HOUSEHOLD | H |

**F1 carries the full case lifecycle.** There is no free slot at the end of the day (16:00 is
the RAs' Field Implementation Plan session), and one hour is too little for A+B+C+D+I+J+K.
So the F1 session teaches **one complete case end to end** — start → navigate → complete
(**I**) → sync (**J**) → what to do when it breaks (**K**). F2, Patients and Household are
then taught as *deltas* against that established spine, which is also the progressive-practice
shape the LSMS guide recommends.

### 3.3 Composition — Field Enumerator deck

Mapped to the Version-2 programme:

| Slot | Duration | Programme item | Modules |
|---|---|---|---|
| Day 2 · 08:00–09:00 | 60 min | **Module 9: CAPI Installation** | A + B + C + D |
| Day 2 · 09:00–12:00 | 180 min | Walkthrough — FACILITY HEAD (F1) | E **+ I + J + K** |
| Day 2 · 13:00–15:00 | 120 min | Walkthrough — HEALTH CARE WORKER (F2) — *no in-charge named, see §6* | F |
| Day 2 · 15:00–17:00 | 120 min | Walkthrough — PATIENTS (in and out) | G |
| Day 3 · 08:00–12:00 | 240 min | Walkthrough — HOUSEHOLD | H |

The enumerator slots are markedly longer than the supervisor's (F1 gets 180 minutes vs 90;
Household 240 vs 90) — appropriate, since enumerators must reach execution-level fluency
while supervisors need recognition-level fluency. The same modules therefore carry an
**extended drill set** in the FE deck: more repetitions of the mock interview, and the
error-path drills (validation failure, interrupted case, failed sync) actually performed
rather than demonstrated.

Enumerator framing differs from supervisor framing in two places only: Module A leads on
*doing the interview* rather than *overseeing it*, and Module K stops at "report to your
Field Supervisor" (the enumerator exam's own correct answer) instead of continuing up the
escalation chain.

## 4. Slide grammar

Every content slide is a **do-along**, never a lecture bullet list:

```
ASSERTION TITLE          — one idea, stated as a claim ("Sync fails closed, not silently")
[ real tablet screen ]   — the actual screenshot, framed, never a mock
YOU DO →                 — 2–4 imperative steps the trainee performs on their own tablet
CHECK                    — the drill or checkpoint question
```

Structural rules:
- **One idea per slide.** No slide carries two teaching points.
- **Every instrument module ends in a mock interview drill** (the programmes' stated
  assessment method for Day 2), and every module ends with a checkpoint drawn from the
  programmes' own daily-quiz / pre-post items — the DHS example-tests pattern.
- **Section pills** mark module boundaries so a facilitator can find their place mid-day.
- Speaker-notes field carries facilitator timing and the common-problem/what-to-do pair.

## 5. Build

**Format:** presentation-ready `.pptx`, **Verde Executive palette** (Carl's July selection):
INK `0E3B2C` · emerald `1B6B4C` · gold `C9A227` · cream `F5F2E9` · body ink `1A241E`;
**Georgia** titles, **Calibri** body; gold slide numbers and eyebrows; section-pill motif.

**Tooling:** `pptxgenjs` via a `build_deck.js` per deck, run with
`NODE_PATH="$(npm root -g)"`. Shared module content lives in a single
`modules.js` data file that both deck builders import — this is what makes the library
modular in practice rather than by convention.

**Screenshots — no mockups, all real.** Three established sources:
1. `deliverables/CAPI-Manual/img/` — **24 real device captures**, already curated per section.
2. `DOH_CAPI_Manual_July27.docx` — **46 embedded tablet captures**; extract with
   `unzip -j <docx> "word/media/*"`, then map image → caption by grepping `media/image` with
   `-B2` context in the pandoc markdown.
3. **F2 live capture** via the throwaway local server recipe (prod facility slugs are
   inactive, so a prod screenshot is impossible): a small `screenshot-server.ts` in
   `PWA/server/` plus a side build with `VITE_F2_PROXY_URL` pointed at it — the API origin
   is baked in at build time. Clear the service worker before capturing.

Images are letterboxed via a recorded aspect-ratio map, never stretched.

**Content grounding:** the two training programmes; Ma'am Silva's Field Supervisors and
Survey Enumerators manuals + CAPI topic outline and style guide; the completed **CAPI Manual**
(17 sections) as the reference text; and **real section maps read from the CSPro `.fmf`
files** for F1/F3 (and F4 for the new Module H) so the walkthroughs match the deployed app
rather than the paper questionnaire.

**Render/QA on this machine:** LibreOffice Portable at
`/c/xampp/LibreOfficePortable/App/LibreOffice64/program/soffice.com` (the pptx skill's
`soffice.py` wrapper is AF_UNIX-only and fails on Windows); `pdftoppm` is absent — render
PDF pages with **PyMuPDF (fitz)** to eyeball every slide before delivery.

**Delivery:** build into the job tmp directory and deliver with `SendUserFile`. Never write
over a file in Downloads that may be open — PowerPoint holds an EBUSY lock.

## 6. Decisions, dependencies and things deliberately not built

**The server address is a hard dependency.** Module B teaches the address ~145 people will
type into CSEntry. The console and sync API now answer on **`capi.asiansocial.org`**, with
`csweb.asiansocial.org` kept alive as a legacy alias for the existing fleet. The decks will
teach **`capi.asiansocial.org/csweb/api`**, which requires the announce-day cutover to land
**before** training — otherwise trainees install against an address the fleet hasn't moved
to. Flagged as a scheduling dependency on ASPSI, not a blocker on deck authoring.

**Module L is a handoff pack, not a session Carl delivers.** The supervisor programme
assigns Day-3 monitoring (M9–M11, including *"generate performance data from CAPI"*) to the
**UHC Y2 Project Team**, not to CReyes. Since that content is Carl's system, Module L is
built as slides the Project Team can present, and is shipped alongside the FS deck rather
than inside it.

**F2's monitoring story needs reconciliation.** Silva's manual describes F2 as monitored
through CSWeb; the live system runs a **separate HCW console** on its own subdomain. The
July decks resolved this by matching the manual. **This spec keeps that choice** — teach
what the manual says, because trainees are examined against the manual — and records the
discrepancy for a later reconciliation with Myra rather than silently teaching either one.

**Open question for Myra (not resolved here):** the enumerator programme's 13:00 F2
walkthrough names **no in-charge**, although the equivalent slot in the supervisor
programme is Carl's. Module F is built for both decks on the assumption it is his; if Myra
assigns it elsewhere, the module drops out of the FE composition without affecting anything
else — which is precisely the benefit of the modular architecture.

**Not in scope:** the written facilitator guide (the speaker-notes field carries timings and
common problems, which is sufficient for Carl to present from); trainee handouts; the
pre/post examination papers (Myra supplies these as Appendices A and B); and any redesign of
the four-simultaneous-sites staffing problem, which is an ASPSI scheduling decision.

## 7. Success criteria

- Two presentation-ready `.pptx` decks, each composed from the shared module library, each
  mapping slot-for-slot onto its programme's real timetable.
- **F4 Household covered** — the gap the superseded decks left open.
- Every screenshot real; zero mockups; zero unfilled placeholder boxes.
- Every module ends in a drill; every instrument module ends in a mock-interview drill.
- Every slide visually verified by rendering the built `.pptx` to images before delivery.
- Both decks delivered to Carl as files; no reliance on the Downloads folder.
