---
type: analysis
date_created: 2026-08-03
tags: [doh-review, xylee-javier, papi-vs-capi, triage, f2, f4, instrument, capi]
---

# Analysis - XJ Findings Categorized — Paper vs CAPI

Xylee Javier's two PAPI-vs-CAPI reviews (F4 Household, F2 Healthcare Worker, both dated 2026-07-13) were triaged into **149 per-finding GitHub tickets** under epics #850 (F4) and #849 (F2). This page sorts all 149 by **what would have to change to close them**.

Counts are generated from the live GitHub labels (`from-doh-review-xj-2026-07`), not transcribed by hand. Every finding is classified; none are left over.

| Class | What it means | Count |
|---|---|---|
| **Paper / instrument** | The questionnaire itself is wrong or ambiguous. Fixing it changes the PAPI too, and needs ASPSI/DOH agreement. | **14** |
| **CAPI** | The questionnaire is fine; the tablet implementation doesn't match it. Ours to fix in the generators. | **130** |
| **Process** | Not defects — requests for screenshots, specs or test access. | **5** |
| | | **149** |

## The one number that matters

**88 of the 130 CAPI findings — 68% of everything XJ raised — are a single repeated observation:** *"'Other (specify)' free-text 'specify' field missing."* One symptom, 50 F4 questions and 38 F2 questions.

If that is one defect in how the other-specify box is gated, it is one fix and the backlog drops from 149 to about 61. If it is an artefact of XJ reviewing April screenshots that simply didn't capture the follow-up screen, it is **zero** fixes and the backlog drops to 61 anyway.

Either way, **this is the first thing to settle** — it decides whether the remediation is a week or an afternoon. The 2026-07-30 Pretest Report independently flagged **F4 Q141** (in this cluster) with a related-but-opposite symptom — the specify prompt appearing when the option was *not* ticked — which is evidence the gating logic is genuinely wrong rather than merely un-screenshotted.

Excluding that cluster, the remaining CAPI findings are only **42**, spread thinly across eight themes.


## A. Paper / instrument issues — the questionnaire itself would change

**14 of 149 findings.**

### Response options — missing / wrong — 5  <sub>(F4 3 · F2 2)</sub>

| # | Form | Finding |
|---|---|---|
| 870 | F2 | Separate input field for Q71 when Q69='yes' and Q70='yes' (as in PAPI) |
| 875 | F2 | A 'None' option was added in CAPI — confirm intent |
| 902 | F4 | Q11 — inconsistent order of options vs PAPI |
| 904 | F4 | Q29 — no 'Refuse to answer' option in CAPI |
| 905 | F4 | Q103 — missing option 'No, I haven't accessed any form of medical care' |

### Ranges & derived values — 4  <sub>(F4 2 · F2 2)</sub>

| # | Form | Finding |
|---|---|---|
| 866 | F2 | Auto-derive 'Not a physician/dentist' from role in Q5 |
| 871 | F2 | Q35 date design (Year required, Month/Day optional) — apply consistently |
| 899 | F4 | Q18 income bracket — remove note, 'tick'->'select', show dropdown, auto-derive bracket from amount |
| 894 | F4 | Travel-duration limit must allow >1 day (>1440 min) for GIDA households |

### Fieldwork protocol in the instrument — 2  <sub>(F4 2 · F2 0)</sub>

| # | Form | Finding |
|---|---|---|
| 880 | F4 | Only first/final visit recorded — vs manual's 3 callbacks in the Visit Sheet |
| 877 | F4 | Field Control at end — accessible/updatable mid-interview for callbacks? |

### Question wording — 1  <sub>(F4 1 · F2 0)</sub>

| # | Form | Finding |
|---|---|---|
| 903 | F4 | Q22 — inconsistent question wording (house vs household) |

### Codes & cross-form harmonisation — 1  <sub>(F4 1 · F2 0)</sub>

| # | Form | Finding |
|---|---|---|
| 878 | F4 | Justify 'Refused'->'Withdraw Participation/Consent'; harmonize codes/order across forms |

### Skip logic / numbering error — 1  <sub>(F4 0 · F2 1)</sub>

| # | Form | Finding |
|---|---|---|
| 869 | F2 | Possible 'proceed to Q63' typo (Q62?) + who answers Q62 given Q61 skip |

## B. CAPI issues — the instrument is fine, the implementation is not

**130 of 149 findings.**

### Other-specify free-text field missing — 88  <sub>(F4 50 · F2 38)</sub>

**F4 (50):** Q5, Q10, Q11, Q17, Q23, Q38, Q45.2, Q46, Q52, Q53, Q55, Q56, Q58, Q59, Q61, Q65, Q66, Q70, Q71, Q74, Q77, Q78, Q79, Q80, Q82, Q85, Q88, Q91, Q92, Q93, Q94, Q101, Q102, Q103, Q106, Q107, Q109, Q110, Q111, Q113, Q121, Q127, Q128, Q133, Q134, Q137, Q141, Q143, Q194, Q199

<sub>tickets #950–#999</sub>

**F2 (38):** Q2, Q5, Q6, Q13, Q15, Q17, Q18, Q19, Q20, Q21, Q22, Q23, Q24, Q25, Q34, Q36, Q37, Q39, Q42, Q43, Q45, Q46, Q47, Q50, Q52, Q55, Q56, Q57, Q60, Q62, Q92, Q93, Q94, Q109, Q110, Q112, Q123, Q124

<sub>tickets #912–#949</sub>

### Missing on-screen text from PAPI — 11  <sub>(F4 4 · F2 7)</sub>

| # | Form | Finding |
|---|---|---|
| 872 | F2 | Missing instruction before Q98 (applicable up to Q107) |
| 873 | F2 | Missing instruction before Q113 (applicable up to Q120) |
| 868 | F2 | Sub-header 'E2. Awareness of GAMOT Package' missing |
| 867 | F2 | Sub-header 'E1. Awareness of and perceptions on BUCAS' missing |
| 864 | F2 | 'Select one answer only' instruction not observed |
| 863 | F2 | Employment-type definitions from PAPI not shown in CAPI |
| 858 | F2 | Red-asterisk required-field mark has no legend |
| 911 | F4 | Q186-Q194 — section intro/overarching question not observed |
| 896 | F4 | 'Select all that apply' instruction missing on some questions |
| 889 | F4 | Section titles/introductions missing or out of order |
| 876 | F4 | Consent Form section from PAPI not found in CAPI |

### Session & navigation behaviour — 8  <sub>(F4 4 · F2 4)</sub>

| # | Form | Finding |
|---|---|---|
| 857 | F2 | Session timeout / expiration handling — clarify |
| 856 | F2 | Resume a partially-completed questionnaire from last save — clarify |
| 855 | F2 | Autosave on connectivity loss / interruption — clarify |
| 854 | F2 | Navigation controls (Next/Back/Go-To/navigator) not shown |
| 884 | F4 | Session timeout / expiration handling — clarify |
| 883 | F4 | Resume incomplete interviews from last save — clarify |
| 882 | F4 | Autosave on interruption — clarify |
| 881 | F4 | Navigation controls not shown |

### Screen layout & input design — 6  <sub>(F4 5 · F2 1)</sub>

| # | Form | Finding |
|---|---|---|
| 865 | F2 | Add input labels/units (Year(s)/Day(s)/Hour(s)) — Q9/Q10/Q11 |
| 898 | F4 | Q15 external-list note + open-text field — consider dropdown/searchable selection |
| 909 | F4 | Q67 travel time — HH:MM split into Hours/Minutes; combine + show question once |
| 906 | F4 | Q199 — amount range not shown |
| 910 | F4 | Household Expenditure section — heavy repetition; group per item |
| 888 | F4 | Question text displayed twice throughout the CAPI screens |

### Validation — exclusivity & single/multi — 6  <sub>(F4 3 · F2 3)</sub>

| # | Form | Finding |
|---|---|---|
| 862 | F2 | Check single-answer items don't allow multi-select, and vice versa |
| 861 | F2 | Multi-answer: prevent simultaneous selection of exclusive options |
| 860 | F2 | Multi-answer: block exclusive options when a listed/Other option is chosen |
| 893 | F4 | Check single-answer items don't allow multi-select, and vice versa |
| 892 | F4 | Multi-answer: prevent simultaneous selection of exclusive options |
| 891 | F4 | Multi-answer: block exclusive options when a listed/Other option is chosen |

### Instructions that should be programmed — 4  <sub>(F4 4 · F2 0)</sub>

| # | Form | Finding |
|---|---|---|
| 897 | F4 | Q1 'Ask all questions in this section unless a skip rule applies' note — remove if skips programmed |
| 901 | F4 | Address-based eligibility — automate rather than manual instruction |
| 900 | F4 | Filter instructions ('Only answer if.../Ask if...') retained in question text |
| 895 | F4 | Automate enumerator notes (skip/eligibility/validation) instead of displaying |

### Identifiers, geo & GPS — 4  <sub>(F4 4 · F2 0)</sub>

| # | Form | Finding |
|---|---|---|
| 887 | F4 | Geocodes status + GPS lat/long capture/record/validation method |
| 886 | F4 | Geographic ID incomplete + implement cascading Region->Province->City->Barangay |
| 885 | F4 | Questionnaire Number: 9-digit PAPI vs 12-digit CAPI — inconsistency |
| 879 | F4 | Visit-date format PAPI M-D-Y vs CAPI YYYYMMDD — rationale |

### Roster & loop workflow — 2  <sub>(F4 2 · F2 0)</sub>

| # | Form | Finding |
|---|---|---|
| 907 | F4 | Household roster (Q30-Q50) — member-level loop workflow + visible member identifier |
| 908 | F4 | Roster — auto-populate already-collected respondent info for confirmation |

### F2 platform difference — 1  <sub>(F4 0 · F2 1)</sub>

| # | Form | Finding |
|---|---|---|
| 851 | F2 | Interface differs from other CAPI instruments — clarify platform + rationale |

## C. Process — not defects; requests for evidence or access

**5 of 149 findings.**

### Evidence / access requests — 5  <sub>(F4 1 · F2 4)</sub>

| # | Form | Finding |
|---|---|---|
| 874 | F2 | Q6 has no screenshot in CAPI |
| 859 | F2 | Provide a skip-pattern matrix / programming specs / test-environment access |
| 853 | F2 | Screenshots omit QN / Informed Consent / Field Control / Geographic ID sections |
| 852 | F2 | Provide full/near-final CAPI screenshots for review |
| 890 | F4 | Provide skip-pattern matrix / programming specs / test-environment access |

---

## How to read this against the pretest

Two independent reviews now overlap, and where they agree the finding is real rather than an observation gap:

| Theme | XJ | Pretest (2026-07-30) |
|---|---|---|
| Other-specify gating | 88 findings, "field missing" | F4 Q141 — prompt fires when option **not** ticked ("CAPI error bug") |
| Exclusive options | 6 findings, "block exclusive when another is chosen" | 22 F4 questions — soft warning only, wants **hard validation** |
| Missing definitions on screen | F2 employment-type definitions, F4 sub-headers | F4 Q46 PhilHealth descriptions, F3 Q53 "primary care provider" |
| Wording drift PAPI vs CAPI | F4 Q22 house/household | F4 Q22 house/household — **same finding** |
| Response options | F4 Q29 no "Refuse", Q103 missing option | F3 Q97.2 "None", F4 Q24 "n/a", Q34 grandparent, Q18 DK |

**Three clusters carry almost everything**: other-specify gating, exclusive-option validation, and PAPI text that never made it onto the screen. Between them they account for 105 of XJ's 149 and the bulk of the pretest list too.

## Status

All 149 tickets are **open and parked** under milestone #7 (post-pretest remediation). Parking was the right call while the pretest ran — the pretest has now finished and independently confirmed parts of the review, so the parked posture is due for review.

Related: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/analyses/Analysis - XJ PAPI-vs-CAPI Reviews vs Current CAPI Build|the original XJ analysis]], [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/PAPI-to-CAPI Translation Review Criteria|PAPI-to-CAPI Translation Review Criteria]], [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/Xylee Javier (XJ)|Xylee Javier]].
