---
type: source-summary
source: "[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/Survey-Instruments-2026-08-17/]]"
date_ingested: 2026-08-18
tags: [questionnaire, survey-instrument, f1-facility, f2-hcw, f3-patient, f4-household, ingest-batch-aug17, capi-update-pending]
---

# Source - Updated Survey Instruments (2026-08-17)

**The updated UHC Year 2 survey tool instruments** — four .docx files received 2026-08-17 (folder
"Survey Instrument_August17"; filenames stamped "Aug 18"), moved to `raw/Survey-Instruments-2026-08-17/`.
**These are the instruments the CAPI builds (CSPro F1/F3/F4 + F2 PWA) will be updated against** — Carl's
directive on ingest, 2026-08-18. **Carl reviewed the ingest findings the same day and confirmed them**: F2's
renumbering confirmed, F3/F4 findings accepted, and the F1 Secondary-Data/consent question resolved (annex in
the PAPI, kept in the CAPI — see the F1 highlights below).

> [!important] Supersession status
> This set supersedes the **Apr 20** instruments ([[Source - Annex F1 Facility Head Survey Questionnaire|F1]] ·
> [[Source - Annex F2 Healthcare Worker Survey Questionnaire|F2]] · [[Source - Annex F3 Patient Survey Questionnaire|F3]] ·
> [[Source - Annex F4 Household Survey Questionnaire|F4]]) as the **instrument reference**. The deployed CAPI
> builds still implement the Apr 20 baseline (+ approved changes like the PhilHealth reinstatement) until the
> update task runs. It also effectively closes the wait-and-see posture of
> [[Source - DOH June Questionnaire Comments (PARKED) 2026-06-19]] — see "Parked-comments resolution" below.

**Internal version markers: none.** No document carries a date, version string, or footer — the only round
markers are the running head "Universal Health Care (UHC) Survey — Year 2" and the Year-2 ASPSI mailbox in the
consent contacts. Word **highlighting** (surviving extraction as `{.mark}` spans) marks the Year-2 edits.
No tracked changes — clean documents.

**Working copies:** pandoc extractions + full per-instrument structural inventories (sections, gating, skip
maps, anomaly catalogs, with line citations) at `deliverables/CSPro/instruments-aug17-extract/` (local-only,
gitignored — verbatim derivative of raw/).

## The four instruments at a glance

| Instrument | Internal title | Apr 20 baseline | Aug 17 set | Numbering vs build |
|---|---|---|---|---|
| **F1** Facility Head | Facility Head Survey Questionnaire | 166 items, Sections A–H + Secondary Data | **Q1–Q153 + 33 decimal subs = 186 items**, A–H; **Secondary Data module absent from the docx — annex-packaged, NOT dropped** (Carl 2026-08-18; consent script still promises it) | **Fully renumbered + restructured** |
| **F2** Healthcare Worker | Healthcare Worker Survey Questionnaire | 124 items in 125 slots (Q108 gap), A–J | **Q1–Q124 continuous + 11 decimal subs + 71a/b = 137 items**, A–J (E split into E1/E2) | **Renumbered** (gap closed; new sub-items) |
| **F3** Patient | **"In-Patient and Out-Patient Survey Questionnaire"** (retitled) | 178 items, A–L | **Q1–Q178 + Q38.1/Q38.2** (PhilHealth reinstatement retained) + 4 unnumbered artifact items, A–L | **Stable** — surgical edits only |
| **F4** Household | Household Survey Questionnaire | 202 items, A–Q | **Q1–Q202 + 4 decimal subs** (2.1, 45.1, 45.2, 89.1), lettered B–Q (A demoted to an unlettered block) | **Stable** — content-level edits |

## Parked-comments resolution

The [[Source - DOH June Questionnaire Comments (PARKED) 2026-06-19|June comment batch]] was parked pending
SJREB/PSA review + pretest. This consolidated set shows what actually made it in:

| Parked item | Outcome in the Aug 17 set |
|---|---|
| **F1: two-step conversion** of ~18 "changed since 2019 / result of UHC Act?" items | ✅ **ADOPTED** — Sections C battery: Q10–Q20 + Q24–Q35 each pair a Yes/No stem with a `.1` attribution probe (6–7 option set). All highlighted as new. This is the largest F1 rework, now real. |
| **F2: two-step preliminaries** (equipment/supplies/EMR etc.) | ✅ **ADOPTED** — Section B battery Q13–Q24 + eleven `.1` sub-items, fully highlighted. |
| **F2: burnout emphasis reduced/removed** (older Annex G #23) | ❌ NOT adopted — the burnout battery survives as Q113–Q120 (8-item frequency grid). |
| **F3: new expenditure block after Q18 + FIES assets replacing Q24–Q28** | ❌ NOT adopted — instead light-touch: highlighted income-band ladder added under Q18, `None` options on Q24–Q26. Asset trio (refrigerator/TV/washing machine) now at Q27–Q29 unchanged in kind. |
| **F3: billed-vs-paid separation (#168–171)** | Partly — the two unnumbered bill-itemization items after Q97/Q115 got explicit Yes/No wrappers + `None` options (highlighted), not a full restructure. |
| **F4: adopt DOH's PIDS/DHS-format household questionnaire** ("major revision") | ❌ NOT adopted — F4 keeps its structure and numbering. Changes are content-level (below). |

## What's new across the set (cross-cutting)

- **GAMOT** (*Guaranteed and Accessible Medications for Outpatient Treatment*) is the flagship new program
  module in **all four instruments**: F1 Q95–Q98 (+ stock-out block Q99–Q104), F2 Section E2 Q53–Q55 (brings
  the pharmacist cadre into scope), F3 Q152–Q157, F4 Q69–Q78. F3/F4 carry a **partial-rollout area gate**:
  *"Enumerator: Applicable only to respondents in areas with GAMOT."*
- **ZBB parallel items**: F2 now mirrors every NBB item with a ZBB twin (Q44–Q47 + three Section-G pairs) on a
  strict facility fork — **ZBB → DOH-retained hospitals only; NBB → all public hospitals**. F3 adds
  inpatient-only ZBB items (Q122–Q123); F4 Section M mirrors Section L.
- **"Quantified Free Service"** — new payment-source category (*"fees directly charged to hospital budget"*)
  added, highlighted, to F3's Q98/Q113 source-of-funds rosters and F4's Q142 settlement matrix.
- **Income-band ladder** (7 highlighted bands, `< PhP12,030` → `> PhP240,600`) layered onto the open income
  amount in F3 Q18 and F4 Q18, with `-98`/`-99` sentinels.
- **"YAKAP/Konsulta" dual branding everywhere** — never either name alone; both tokens must survive variable
  naming and translation.
- **Shared consent architecture**: identical PART I / PART II Certificate with a shared *Respondent Type* row
  (`☐ Facility Head ☐ Inpatient ☐ Outpatient ☐ Household Head`), SJREB + DOH (Lindsley Jeremiah D.
  Villarante) + ASPSI ([[Dr Paulyn Claro|Paulyn Jean A. Claro]], `inquiry.aspsi.doh.uhc.survey2@gmail.com`)
  contact table. Incentives now printed: **Php 100 token** (F3, F4), **PhP 1,000 raffle** (F2).
- **Result-of-visit codes diverge by instrument**: F1/F2 `1 Completed · 2 Postponed · 3 Refused · 4 Incomplete`;
  **F3 has 6 codes** (adds *Completed at the Hospital*, *Completed at Home*, *Withdraw Participation/Consent*);
  **F4 has 4 codes with no "Refused"** (*1 Completed · 2 Postponed · 3 Incomplete · 4 Withdraw*). Affects the
  BREAKOFF → Result-of-Visit / CASE_DISPOSITION mapping.
- **English-only source masters** — no bilingual content anywhere, consent included. All new/changed English
  (the F1/F2 attribution batteries, GAMOT modules, QFS, income bands) **has no cleared translation yet**; the
  June-5 translated set remains authoritative only for carried-over wording, and F1/F2's renumbering breaks
  question-number joins (CSPro maps key on item name + English, so re-keys survive, but paper-side translation
  is an ASPSI deliverable to come).

## Per-instrument highlights

### F1 — restructured (see `F1-inventory.md` for the full map)
Sections: A Profile (Q1–6) · B Facility (Q7–8) · C UHC Implementation (Q9–37 + 32 subs) · D YAKAP/Konsulta
(Q38–87, three accreditation-gated blocks) · E BUCAS+GAMOT (Q88–104) · F DOH Licensing (Q105–121, 13-question
fan-out) · G Service Delivery (Q122–149: NBB/ZBB/OOP-Malasakit-MAIFIP/LGU/Referral) · H HRH (Q150–153).
New Q21–Q23 DOH-IS/PhilHealth-Dashboard use-for-decision-making items; new PHO-protocol governance probes
Q139–Q140; hybrid numeric+band duration items (Q49/Q50/Q107). **Eight skip-logic defects catalogued** (Q67
contradicts the accreditation banner; Q65/Q68–Q71 missing exits; Q137→Q141 orphans Q139–Q140; Q148 mislabeled
SELECT ALL; Section E banner contradicts its own awareness gates; Q94 gate mismatch; Q117 inserted mid-sequence;
Q102 duplicates Q101 ungated). **Secondary Data module absent from the docx — resolved, NOT dropped.**
Carl's ruling on review (2026-08-18, verbatim): *"Consent is annex in PAPI, should still be in the CAPI"* —
the material the questionnaire body no longer carries is **annex-packaged in the PAPI**, and the **CAPI keeps
it**: the consent flow stays in the CAPI app, and the Secondary Data records the consent script promises remain
part of the build. Open question closed; no ASPSI confirmation needed.

### F2 — renumbered; PWA spec impact (see `F2-inventory.md`)
Sections A–J; E split E1 (BUCAS) / E2 (GAMOT). **Cadre routing rewritten**: pharmacists/dispensers skip C–E1
and enter at E2; all other non-core cadres enter at F Q56; **Section G (Q63–Q90 professional fees, incl. new
RVU items) is physicians/dentists only**, reached through per-option routing on Q61/Q62. New Q47 ZBB-challenges
checklist; employment-type definition block under Q2; DOLE hours note under Q11. Defects: Q121 gates on Q114
(should be Q113); `Preventative`/`Preventive` gate-string mismatch; Q25 option with no follow-up; Q36 stem
contradicts its accredited-path context; 8 list questions with **ambiguous select-one/select-all cardinality**.
The Apr 20 `F2-Spec.md`/skip-logic/validation docs are now stale against this version.

### F3 — stable numbering, surgical edits (see `F3-inventory.md`)
Retitled "In-Patient and Out-Patient Survey Questionnaire". Q38.1/Q38.2 (PhilHealth reinstatement) retained —
matches the deployed build. 21 highlighted edits (QFS, PhilHealth/NBB relabel, income bands, None options,
Q148 coding code 19, bill-item wrappers). **Two `Note for CAPI Version` blocks instruct that outpatient (G) and
inpatient (H) blocks be front-loaded before primary care utilization** — deliberate paper-vs-CAPI order
divergence. Defects to fix, not replicate: broken `Q124-Q25` routing banner (should be Q125); two Word
auto-number restarts (unnumbered `1.`/`2.` items after Q97 and Q115); duplicate item 15 in Q98; Q159
"Not applicable" jumps over the Section-L gate Q162.

### F4 — stable numbering, content-level edits (see `F4-inventory.md`)
Sections B–Q (A demoted); household roster C1–C5 = six-pass loop over 10 fixed rows, respondent pinned to row 1
with back-fill from Section B. **Largest highlighted region: the whole Q139–Q143 hospital-bill decomposition
module** (incl. the 16-source Q142 settlement matrix). Q34 relationship code 13 (Grandfather/Grandmother)
appended. Q202's COVID-19 option highlighted (legacy flag). Expenditure grids explicitly expect CAPI computed
totals (`[DO NOT ASK]` rows Q157/Q177/Q182/Q185). Defects: stale `(Only answer if 'Yes' in 120)` cross-ref
(should be Q45); Q11↔Q40 education code-list mismatch; three coexisting sentinel families (−98/−99, −55, 88);
Q135's hidden dependency on Q130.

## CAPI update implications (for the coming task)

1. **F1 is a rebuild-scale change**: full renumber (153+subs vs 166), new two-step battery (decimal
   sub-questions — CSPro naming needs a convention, e.g. Q10_1), new modules. **Consent flow and Secondary
   Data records stay in the CAPI** (annex-packaged in the PAPI, not dropped — Carl 2026-08-18).
   `generate_dcf.py`/`generate_apc.py` for F1 take the brunt.
2. **F2 PWA spec regeneration**: renumbering + new B battery + rewritten cadre routing + G gating. The
   translation maps key on English text, so carried-over strings survive; all-new English needs ASPSI dialect
   text later.
3. **F3/F4 are patch-scale**: stable numbering means the existing dcf/apc structures mostly hold; apply the
   highlighted deltas + fix (not replicate) the paper's routing defects. F3's front-load notes may reorder
   CAPI forms relative to paper — reconcile with [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Questionnaire Numbering Convention|Questionnaire Numbering Convention]] /
   [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/GPS and Photo Capture|GPS and Photo Capture]] ordering rules before restructuring.
4. **Paper defect log → ASPSI**: each inventory's anomaly section is effectively a questionnaire errata list
   ASPSI may want before printing (broken cross-references, duplicate numbering, contradictory gates).
5. **Translations**: new English content across all four has no cleared translations; expect a follow-on
   translation delivery. Do not re-join the June-5 corpus onto F1/F2 by question number.

## Cross-references

- Superseded baselines: [[Source - Annex F1 Facility Head Survey Questionnaire]] ·
  [[Source - Annex F2 Healthcare Worker Survey Questionnaire]] · [[Source - Annex F3 Patient Survey Questionnaire]] ·
  [[Source - Annex F4 Household Survey Questionnaire]]
- Parked-comment cycle this set closes: [[Source - DOH June Questionnaire Comments (PARKED) 2026-06-19]] ·
  [[Source - PAPI vs CAPI HCW Review (XJ 2026-07)]] · [[Source - PAPI vs CAPI Household Review (XJ 2026-07)]]
- Programme concept: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/UHC Survey Year 2|UHC Survey Year 2]]
- Translation reference (question-number join now unsafe for F1/F2): [[Source - DOH Deliverable 2 Translated Questionnaires (June 5)]]
- People/orgs: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/Dr Paulyn Claro|Dr Paulyn Claro]] ·
  [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/ASPSI|ASPSI]] ·
  [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/DOH-PMSMD|DOH-PMSMD]] ·
  [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/SJREB|SJREB]]

## Sources

- Raw files: `raw/Survey-Instruments-2026-08-17/` — F1/F2/F3/F4 `*_UHC Year 2_Aug18.docx` (main checkout;
  raw/ is gitignored and does not materialize in worktrees)
- Working extraction + inventories: `deliverables/CSPro/instruments-aug17-extract/` (local-only)
