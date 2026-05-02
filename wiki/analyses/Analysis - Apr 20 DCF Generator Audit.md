---
type: analysis
date_created: 2026-04-20
tags: [apr20, dcf, generators, f1, f2, f3, f4, audit, ingest-batch-apr20]
---

# Analysis — Apr 20 DCF Generator Audit

Per-generator audit of what needs to change in each F-series DCF generator against the [Apr 20 submission](Source%20-%20Annex%20G%20DOH%20Recommendations%20Matrix.md) questionnaires. Output of **Step 3** of the Apr 20 re-ingest plan.

**Key:** this is an **audit report**, not a patch. Each change item identifies *which generator function + which record* needs work. Actual patching is downstream task work.

## Baseline (what the generators emit today)

Emitted DCF files currently target the **Apr 08 baseline**:

| Instrument | Generator | Records | Total items | Emitted file |
|---|---|---|---|---|
| F1 | `deliverables/CSPro/F1/generate_dcf.py` | 11 | **655** | `FacilityHeadSurvey.dcf` |
| F3 | `deliverables/CSPro/F3/generate_dcf.py` | 15 | **387** | `PatientSurvey.dcf` |
| F4 | `deliverables/CSPro/F4/generate_dcf.py` | 20 | **460** (incl. 3 repeating: C/H/J) | `HouseholdSurvey.dcf` |

F2 has no DCF generator — it's the Google Forms / PWA track (`f2-pwa/`). F2 audit is handled separately below.

## F1 — Facility Head (`deliverables/CSPro/F1/generate_dcf.py`) — DONE

**Apr 20 source:** 37 pp, 166 main-survey items (up from ~126 Apr 08, +40).

**Status (2026-04-20):** All P1/P2 items landed. Generator emits 11 records / 655 items against Apr 20 source. PSGC value sets self-served from PSA 1Q 2026 (no longer inbound from ASPSI).

### Changes to patch

| Priority | Generator fn | Record | Change | Annex G driver | Status |
|---|---|---|---|---|---|
| **P1** | `build_section_c()` | `C_UHC_IMPLEMENTATION` | **Add Q32–34**: DOH IS / PhilHealth Dashboard submission flag, submission frequency, 12-option checklist of reports actually used for decision-making (incl. YAKAP/Konsulta utilization, NBB compliance, ZBB compliance). | #3 (EMR-use-in-decision-making) | ✅ Done |
| **P1** | `build_section_c()` | `C_UHC_IMPLEMENTATION` | **Verify Q40–42**: explicit separate items for NBB / ZBB / no-copayment implementation since UHC Act. | #1, #19 | ✅ Present as separate `uhc9_item` blocks |
| **P1** | `build_section_e()` | `E_BUCAS_GAMOT` | **Verify coverage Q101–117**: BUCAS Q101–107, GAMOT Q108–117. Record name `E_BUCAS_GAMOT` matches new section title. | #1 | ✅ Full Q101–117 coverage |
| **P1** | `build_section_g()` | `G_SERVICE_DELIVERY` | **Restructure into 4 subsections**: NBB Q135–137, ZBB Q138–140, LGU Support Q148–153, Referral Q154–162. | #1, #19, #22 | ✅ Item names match Apr 20 numbering |
| P2 | `build_section_e()` | label only | Section E label update: "Expanded Health Programs" → "Awareness on Expanded Health Programs (BUCAS and GAMOT)". | #1 | ✅ Done |
| P3 | `build_geographic_id()` | `HEALTH_FACILITY_AND_GEOGRAPHIC_IDENTIFICATION` | PSGC value sets wired from PSA 1Q 2026 publication. Length 10 on all four items (full 10-digit PSGC). Cascading parent-filter logic lives in PROC, not DCF — follow-on task. | — | ✅ Wired (43,803 value-set entries) |
| — | file-level docstring | — | Swap authority reference from "April 8 2026" → "Apr 20 2026 submission". | — | ✅ Done |

### Net item delta (actual vs. predicted)

Predicted: 655 → 700–720. Actual: **stayed at 655** — the Apr 20 structural additions were absorbed within the commit that dropped the old secondary-data items (commit `28f772c`, "drop secondary data"). Net-zero item count, but the question mix shifted to Apr 20 scope.

### Remaining follow-ons

- **CSPro PROC cascading filter** for child PSGC dropdowns (parent chains are in the CSVs; logic belongs in form PROC).
- **E2-F1-010 Designer walkthrough sign-off** against the current `FacilityHeadSurvey.dcf` — separate task.

## F3 — Patient (`deliverables/CSPro/F3/generate_dcf.py`)

**Apr 20 source:** 178 items (up from ~126 Apr 08, +52). Now covers inpatient + outpatient (was outpatient-leaning).

### Changes to patch

| Priority | Generator fn | Record | Change | Annex G driver |
|---|---|---|---|---|
| **P1** | `build_section_b()` | `B_PATIENT_PROFILE` | **Add Q32**: Is household a 4Ps beneficiary? (Yes/No). Currently 12 items → 13. | #11 |
| **P1** | `build_section_d()` | `D_PHILHEALTH_REG` | **Add Q45 value set**: PhilHealth member category (Formal / Informal / Indigent / Sponsored / Lifetime / Senior / OFW / Qualified dependents / Don't know / Other). Item may already exist in the 41-item count — verify label + value set matches Apr 20 wording. | #4 |
| **P1** | `build_section_g()` | `G_OUTPATIENT_CARE` | **Add OOP-outside-facility lines Q108–112**: medicines purchased outside hospital (amount, source), services outside hospital (amount). Extend existing OOP items. Currently 68 items. | #10 |
| **P1** | `build_section_h()` | `H_INPATIENT_CARE` | **Verify inpatient-aligned OOP items**: Apr 20 confirms inpatient scope — check that inpatient OOP questions mirror outpatient Q108–112 additions. Currently 44 items. | #10, #15 |
| **P1** | `build_section_l()` | `L_REFERRALS` | **Verify / extend Q162–178**: referral follow-through items (did you visit referred facility, did PCP follow up, did they write for specialist, rating). Current 29 items — likely already covers most of this, but verify labels + Q# alignment. | #15 |
| P2 | `build_section_f()` | `F_HEALTH_SEEKING` | **Verify "bypassing PCF" indicator** exists or add if missing. | #22 |
| P2 | section labels | all sections | Section title updates: C → "Awareness on Universal Health Care (UHC)"; D → "PhilHealth Registration and Health Insurance"; F → "Patient's Health-Seeking Behavior"; K → "Access to Medicines"; L → "Experiences and Satisfaction on Referrals". | — |
| P3 | `build_f3_geo_id()` | `PATIENT_GEO_ID` | Wire PSGC value sets from `deliverables/CSPro/F1/inputs/psgc_*.csv` via `load_psgc_value_set()` — same pattern as F1. Length 10 on all four PSGC items. | — |
| — | file-level docstring | — | Authority reference Apr 08 → Apr 20. | — |

### Expected net item delta

F3 grows from 387 → **roughly 430–450 items**. Most growth lands in `B_PATIENT_PROFILE` (+1 for 4Ps), `G_OUTPATIENT_CARE` (+5-10 for OOP outside facility), and `H_INPATIENT_CARE` (+similar OOP additions).

### Risk flags

- **Q45 value set**: if Apr 08 generator encoded a smaller PhilHealth-category value set, the Q45 item may need a value-set swap, not just a label update. Direct comparison with Apr 20 Q45 wording required.
- **Inpatient vs outpatient routing**: F3's Sections G and H are mutually conditional. The Apr 20 scope expansion to full inpatient coverage might require tightening or loosening this routing — check `F3-Skip-Logic` doc if it exists.

## F4 — Household (`deliverables/CSPro/F4/generate_dcf.py`)

**Apr 20 source:** 202 items across 17 sections. Community-survey framing confirmed.

### Changes to patch

| Priority | Generator fn | Record | Change | Annex G driver |
|---|---|---|---|---|
| **P1** | `build_section_f()` | `F_BUCAS_AWARENESS` | **Grow from awareness-only to awareness+utilization**. Currently only 4 items — needs new utilization items (have you/anyone used BUCAS, when, what for, satisfaction). Section title adds "and Utilization". | #1 |
| **P1** | `build_section_h()` | `H_PHILHEALTH_REG` (repeating 20) | **Add PhilHealth member category item** (same value set as F3 Q45). Per-member roster item. Currently 34 items → 35 per-member. | #4 |
| **P1** | `build_section_j()` | `J_HEALTH_SEEKING` (repeating 20) | **Verify household-level health-seeking items** work for members irrespective of facility-visit gate. May require removing an upstream gate item. Currently 36 items per member. | #12 |
| P1 | `build_section_n()` | `N_HOUSEHOLD_EXPENDITURES` | **Verify WHO HH expenditures module** sub-tables A (food), B (non-food non-health), E (health). Currently 108 items — confirm structure matches Apr 20 3-sub-table layout. | #11 |
| **P1** | `build_section_p()` | `P_FINANCIAL_RISK` | **Expand** from 4 items to cover Q197–199 (delayed care, saw doctor without treatment, willingness-to-pay consultation). | #12 |
| P2 | section labels | all sections | Section title updates: F → "Bagong Urgent Care and Ambulatory Service (BUCAS) Awareness and Utilization"; Section C → "Household Roster and Characteristics"; G → "Access to Medicines". | — |
| P2 | `build_section_l()` / `build_section_m()` | `L_NBB_AWARENESS`, `M_ZBB_AWARENESS` | **Verify awareness + utilization** coverage. Currently 23 and 44 items — reconcile against Apr 20 L and M content. | #1, #7, #19 |
| P3 | `build_f4_geo_id()` | `HOUSEHOLD_GEO_ID` | Wire PSGC value sets from `deliverables/CSPro/F1/inputs/psgc_*.csv` via `load_psgc_value_set()` — same pattern as F1. Length 10 on all four PSGC items. | — |
| — | file-level docstring | — | Authority reference Apr 08 → Apr 20. | — |

### Expected net item delta

F4 grows from 460 → **roughly 485–510 items** (roster-expanded counts). Most growth in F (BUCAS utilization), H (+1 per roster row × 20 rows), P (+5-8 items).

### Risk flags

- **Roster fields multiply by 20**: adding 1 item to `H_PHILHEALTH_REG` means +20 in the total DCF item count. Keep an eye on this when comparing the net delta.
- **Sampling-frame change (not DCF)**: community-survey framing (interval sampling from patient HH) affects field workflow and CAPI enumerator UX, not the DCF schema.

## F2 — Healthcare Worker (`f2-pwa/` — Google Forms track)

No DCF generator. F2 is handled via the [[F2 Google Forms Track]] — HCW self-administered via Google Forms, generated by the Apps Script bundle at `deliverables/F2/apps-script/`.

### Changes to patch

| Priority | Artifact | Change | Annex G driver |
|---|---|---|---|
| **P1** ✅ DONE | `deliverables/F2/F2-Spec.md` | ~~Re-audit 114-item spec against Apr 20 PDF (125 items). Expect +11 items — likely in Sections D (NBB+ZBB explicit naming), E (BUCAS+GAMOT explicit naming).~~ Audit completed during Apr 20 ingest; F2-Spec is now the 124-item Apr 20 build (Q1–Q125 with Q108 gap). | #1 |
| **P1** | `deliverables/F2/F2-Skip-Logic.md` | Regenerate routing graph against new item numbering. | — |
| P1 | `deliverables/F2/F2-Validation.md` | Refresh required-flag + numeric-range inventory for +11 new items. | — |
| P2 | `deliverables/F2/F2-Cross-Field.md` | Verify 20 POST rules still apply post-renumbering. | — |
| P2 | `f2-pwa/` | Regenerate question tree from Apr 20 spec. | — |
| P3 | Burnout block Q114–122 | **Decision gate** — Annex G #23 says reduce/remove. Apr 20 retains. Flag for Dr. Claro before build. | #23 |
| — | F2 cover-block rewrite | **No longer a build gate** — F2 is self-admin-first (Google Forms / PWA) with guided-interviewer fallback; the PDF's interviewer-style cover-block text is formality only. | — |

## Cross-cutting: PSGC

All four instruments carry REGION / PROVINCE_HUC / CITY_MUNICIPALITY / BARANGAY geographic items. **Resolved (2026-04-20):** PSGC value sets self-served from PSA 1Q 2026 Publication and wired into F1 via `inputs/parse_psgc.py` + `cspro_helpers.load_psgc_value_set()`. F2/F3/F4 reuse the same CSVs when their geographic-ID blocks are patched. See [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/PSGC Value Sets|PSGC Value Sets]].

## Recommended patching order

1. **F1 first** — `build_section_c()` Q32–34 + Section G subsection restructure is the highest-impact + highest-risk change. F1 also still has active Designer walkthrough (E2-F1-010) in flight.
2. **F3 second** — Q32 4Ps + Q45 value set are small, mechanical. OOP-outside-facility items in G/I are the larger diff.
3. **F4 third** — F_BUCAS expansion + H PhilHealth-category addition are straightforward; Section N WHO expenditures verification is the biggest unknown.
4. **F2 (Google Forms) in parallel** — no DCF dependency; spec re-audit can go alongside F1 work.

## Cross-references

- Change-rationale map: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex G DOH Recommendations Matrix|Annex G DOH Recommendations Matrix]]
- F1 source page: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F1 Facility Head Survey Questionnaire]]
- F2 source page: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F2 Healthcare Worker Survey Questionnaire]]
- F3 source page: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F3 Patient Survey Questionnaire]]
- F4 source page: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F4 Household Survey Questionnaire]]
- F3b source page: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F3b Patient Listing Protocol]]
- Ingest plan: `memory/project_apr20_ingest_plan.md`
