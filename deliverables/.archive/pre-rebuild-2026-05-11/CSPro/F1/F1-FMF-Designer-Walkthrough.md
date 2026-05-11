---
type: checklist
project: ASPSI-DOH-CAPI-CSPro-Development
deliverable: F1 FMF Designer-pass walkthrough (E3-F1-001)
date_created: 2026-05-04
sprint: 004
related:
  - deliverables/CSPro/F1/F1-Form-Layout-Plan.md
  - deliverables/CSPro/F1/F1-Skip-Logic-and-Validations.md
  - deliverables/CSPro/F1/FacilityHeadSurvey.fmf
  - deliverables/CSPro/Form-Layout-Principles.md
estimate: ~2-4h hands-on Designer
tags: [cspro, capi, fmf, designer, walkthrough]
---

# F1 FMF Designer Walkthrough — E3-F1-001 close-out checklist

> Pre-Designer prep so the FMF pass runs as a structured walkthrough instead of an open-ended exploration. **Every form's per-row spec lives in `F1-Form-Layout-Plan.md`** — this file is the WALK ORDER + per-form verify checklist + bug-list capture. Open `F1-Form-Layout-Plan.md` in a side pane while you work.

## Pre-flight (~5 min)

- [ ] Open `FacilityHeadSurvey.fmf` in CSPro Designer (the generator skeleton already emits this — confirm via Section A renders with case-control + PSGC blocks first).
- [ ] Open `F1-Form-Layout-Plan.md` in a second pane (this checklist + the plan).
- [ ] Open `F1-Skip-Logic-and-Validations.md` in a third pane (for the skip/gate verification per form).
- [ ] Confirm the linked `.dcf` is at 12 records / 671 items (Apr 21+22 build with case-control + GPS/photo/PSGC-cascade).
- [ ] Designer settings: zoom to a comfortable level; Form Properties panel docked; Form Tree visible.

## Walk order — 28 forms (~5–10 min/form average; long forms 15 min)

The plan groups forms by source record. Walk top-to-bottom — each form's checklist is at the bottom of this file.

### Phase 1 — Field control + capture (3 forms, ~20 min)

- [ ] **Form 1 — `FC_METADATA`** — case-control block + AAPOR + consent gate.
- [ ] **Form 2 — `FC_GEO`** — PSGC cascade (REGION → PROVINCE_HUC → CITY_MUNICIPALITY → BARANGAY) + facility name + address.
- [ ] **Form 3 — `FC_CAPTURE`** — GPS + verification photo triggers (uses `Capture-Helpers.apc`).

### Phase 2 — Section A (Facility Head profile, 2 forms, ~15 min)

- [ ] **Form 4 — `A1_PROFILE`** — Q1–Q6 demographics + tenure (terminate gate at total tenure <6 months).
- [ ] **Form 5 — `A2_CONSENT_CONTACTS`** — consent-related Q7–Q8 (per spec §A2).

### Phase 3 — Section B (Facility profile, 1 form, ~10 min)

- [ ] **Form 6 — `B_PROFILE`** — Q9–Q11 facility tier / type / catchment.

### Phase 4 — Section C (UHC implementation, 5 forms, ~30 min) ⚠️ LARGEST SECTION

- [ ] **Form 7 — `C1_AWARENESS`** — Q12 gate (No → skip Q13–Q30).
- [ ] **Form 8 — `C2_ACT_BUDGETS`** — Q13–Q20 acts + budgets.
- [ ] **Form 9 — `C3_GUIDELINES`** — Q21–Q26 guidelines + dissemination.
- [ ] **Form 10 — `C4_TRAININGS`** — Q27–Q30 trainings.
- [ ] **Form 11 — `C5_GATE_OUT`** — closes section C, returns to common path.

### Phase 5 — Section D (Yakap Konsulta, 4 forms, ~25 min)

- [ ] **Form 12 — `D1_AWARENESS`** — Q31 gate (No → skip Q32–Q50).
- [ ] **Form 13 — `D2_PATH_A`** — Q31=Yes branch, deep-dive items.
- [ ] **Form 14 — `D3_PATH_B`** — Q31=No branch, IP_GROUP question (PENDING ASPSI confirmation per spec).
- [ ] **Form 15 — `D4_GATE_OUT`** — closes section D.

### Phase 6 — Section E (BUCAS + GAMOT, 2 forms, ~15 min)

- [ ] **Form 16 — `E1_BUCAS`** — Q51–Q60 BUCAS items.
- [ ] **Form 17 — `E2_GAMOT`** — Q61–Q75 GAMOT items.

### Phase 7 — Section F (DOH licensing, 2 forms, ~15 min)

- [ ] **Form 18 — `F1_LICENSING`** — Q76–Q120.
- [ ] **Form 19 — `F2_Q121_GRID`** — Q121 dynamic value-set grid (uses PENDING_DESIGN_Q121 default).

### Phase 8 — Section G (Service delivery, 4 forms, ~25 min)

- [ ] **Form 20 — `G1_NBB`** — newborn screening (NBB items, PENDING_DESIGN_NBB_SPLIT default).
- [ ] **Form 21 — `G2_ZBB`** — Z-package items.
- [ ] **Form 22 — `G3_LGU_REFERRAL`** — LGU + referral linkages.
- [ ] **Form 23 — `G4_GATE_OUT`** — closes section G.

### Phase 9 — Section H (Human resources, 1 form, ~10 min)

- [ ] **Form 24 — `H_HR`** — Q163–Q166 (Q166 nurse list uses `PENDING_DESIGN_Q166_NURSES_INCLUDE_AUDITS` default).

### Phase 10 — Roster stubs (4 forms, ~10 min total — verify stub-only, no per-row design)

- [ ] **Form 25 — `SEC_HOSP_CENSUS_STUB`** — empty roster (PENDING_DESIGN_SECONDARY_DATA_AS_STUBS).
- [ ] **Form 26 — `SEC_HCW_ROSTER_STUB`** — empty roster.
- [ ] **Form 27 — `SEC_YK_SERVICES_STUB`** — empty roster.
- [ ] **Form 28 — `SEC_LAB_PRICES_STUB`** — empty roster.

> Verify stubs render without warnings; confirm no questions defined; mark for "fill at LSS-decides-secondary-data-shape" in deferred bug list.

## Per-form verify checklist (apply to each of 28 forms)

For every form in the walk, run this 7-point check. Notes inline; bugs to bug-list section below.

- [ ] **Visible without scrolling** at 7-inch tablet viewport (CSPro Designer's preview at typical CAPI tablet target). Per `Form-Layout-Principles.md` row budget: ≤8 rows / ≤12 controls of any kind. Forms exceeding budget split per the plan.
- [ ] **Control type matches spec** — Numpad / Dropdown / Radio horizontal / DatePicker / TimePicker / Single-line text / Multi-line text per the per-row table in `F1-Form-Layout-Plan.md`. Designer's default control choice may need flipping for some fields (e.g., generator-default for select_one is dropdown; spec may want radio horizontal for ≤4 options).
- [ ] **Tab order** — left-to-right, top-to-bottom. No "jumping" between controls.
- [ ] **Required-field markers** visible on hard-required fields. Soft fields render without the marker.
- [ ] **Validation rules attached** — for fields with validation per spec §4.1–§4.16, confirm Field Properties has the validation expression set (or note "to be added in PROC").
- [ ] **Skip/gate logic placeholder** — gate-bearing fields (Q12, Q31, Q51, etc.) should have at minimum a comment placeholder. Actual `.apc` PROC code lands per `F1-Skip-Logic-and-Validations.md` §4.x — verify per-section, not per-form.
- [ ] **Helper `.apc` attachment** — for FC_GEO (PSGC-Cascade.apc), FC_CAPTURE (Capture-Helpers.apc), confirm the helper file is referenced at the form / global PROC level and the relevant `onfocus`/`onkey` handlers point to the documented function names (`ReadGPSReading()`, `TakeVerificationPhoto()`, `setvalueset()` cascade triggers).

## Roster-scrolls-alone discipline (Phase 10 stub forms only)

Per `Form-Layout-Principles.md`, roster forms scroll independently of the parent form (no nested scroll). For SEC_* stubs:

- [ ] Roster control set to scroll vertically with explicit max height (~6–8 rows visible).
- [ ] Parent form does NOT scroll while roster is scrollable.
- [ ] "Add row" button fixed at the bottom of the roster region, not inside it.

(For Sprint 004 these are stubs — the discipline is captured but the per-row design lands when LSS finalizes the secondary-data structure.)

## Bug list (capture as you walk)

> Format: `[FX-FMF-NNN] [SEVERITY] form# title — symptom + expected + Designer state.`

Critical / High (blocks sign-off):
- (none yet)

Medium (defer with rationale ok):
- (none yet)

Low (cosmetic / polish):
- (none yet)

Deferred (with rationale, count toward "explicitly deferred" in DoD):
- (none yet)

## Sign-off section — paste into log.md when complete

After all 28 forms walked + bug list dispositioned:

```markdown
### E3-F1-001 — F1 FMF Designer pass — sign-off note

- **Closed YYYY-MM-DD, Sprint 004 Day N.** F1 FMF Section-A-onwards walkthrough complete in CSPro Designer (28 forms across 12 records / 671 items).
- **Walkthrough scope confirmed:** all 28 forms render at 7-inch tablet viewport without scroll (excepting the 4 SEC_* roster stubs which scroll-alone per the plan); control types match `F1-Form-Layout-Plan.md`; tab order linear; required-field markers attached; helper `.apc` files (PSGC-Cascade, Capture-Helpers) referenced at the right scope.
- **Bugs:** {N} found, {M} fixed during walk, {K} explicitly deferred with rationale (see `F1-FMF-Designer-Walkthrough.md` Bug list).
- **F1 → CAPI-runtime-ready.** Unblocks CAPI build / desk-test phase (E2 testing track in Epic 6).
- **Generator discipline:** any FMF schema changes during the walk got patched in `F1-Form-Layout-Plan.md` (the spec) first; `FacilityHeadSurvey.fmf` is treated as a generated artifact like the DCF — generator file is the source of truth.
```

## What NOT to do during the walk

- **Don't hand-edit the FMF in Designer for any change you can capture in the form-layout-plan.** Per memory `feedback_f1_dcf_generator_source_of_truth.md`, the generator stays canonical — Designer-side edits drift from spec. If a form needs a different control type or row order, mark it in the Bug list, fix `F1-Form-Layout-Plan.md`, regenerate (when the FMF generator is built).
  - **Exception during transition:** until the FMF generator catches up to the DCF generator's discipline, Designer-side fixes for cosmetic-only items (label wording, control alignment) can land directly. Schema-level changes (new field, new gate) MUST go through the spec.
- **Don't promise specific bug fixes during the walk.** Capture in Bug list, disposition at the end. Mid-walk patching breaks rhythm.
- **Don't run the FMF in CSEntry** as part of this walkthrough — that's CAPI runtime testing (Epic 6, separate task). E3-F1-001 is Designer-side layout verification only.
- **Don't sign off if any HIGH bug is open** without an explicit deferral rationale. Three-sprint-carry status retired with E2-F1-010; this is a different gate.

## Estimated session shape

| Phase | Time | Cumulative |
|---|---|---|
| Pre-flight | 5 min | 5 min |
| Phase 1 (FC) | 20 min | 25 min |
| Phase 2 (A) | 15 min | 40 min |
| Phase 3 (B) | 10 min | 50 min |
| Phase 4 (C) | 30 min | 1h 20min |
| **Mid-walk break** | 5 min | 1h 25min |
| Phase 5 (D) | 25 min | 1h 50min |
| Phase 6 (E) | 15 min | 2h 5min |
| Phase 7 (F) | 15 min | 2h 20min |
| Phase 8 (G) | 25 min | 2h 45min |
| Phase 9 (H) | 10 min | 2h 55min |
| Phase 10 (rosters) | 10 min | 3h 5min |
| Bug-list disposition + sign-off | 15 min | 3h 20min |

**Total: ~3h 20min, comfortably inside the 4h estimate.** If the walk goes faster than this — likely, given E2-F1-010 sign-off was much faster than its 4h budget — then E2-F3-010 / E2-F4-010 stretch becomes very pullable into the same day.
