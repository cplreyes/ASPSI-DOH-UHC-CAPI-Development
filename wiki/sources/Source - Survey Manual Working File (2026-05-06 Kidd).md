---
type: source-summary
source: "[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/2026-05-06-survey-manual-bundle/2026-05-06_Survey-Manual-Working-File-Kidd]]"
date_ingested: 2026-05-07
tags: [survey-manual, fieldwork, sop, capi, hcw, csentry, kidd, working-file]
---

# Source — Survey Manual Working File (2026-05-06 Kidd)

The **live ASPSI-internal Survey Manual** as of 2026-05-06 evening, shared by [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/Juvy Chavez-Rocamora|Kidd]] via Google Docs link in the *"Re: Survey Manual — CAPI inputs"* thread (`https://docs.google.com/document/d/17nI_FcJi8F2lDQ7lg95SvC9G4qWS71YCytjSTbNeFDU`). This is the operational manual for Survey Team Leaders + enumerators — **Kidd's update of the Apr 28 manual** integrating Carl's [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - DOH UHC Year 2 Survey Manual|3-doc CAPI inputs package]] (sent 2026-05-05) AND aligning to [[Source - DOH Survey Protocol V2 (30 April)|Myra's Protocol V2]]. ~2,222 lines (exported as docx).

> [!info] Status
> Working file — distribution tables for Household Sampling still pending per Kidd's email. Open for early consistency check by the team.

## Document structure

- **L13** Background of the Study
- **L75** Definition of Terms
- **L212** The Survey Manual
  - **L221** §3.1 Survey Teams (Table 1: 6 clusters, 6 RAs / 20 FSs / 100 SEs / 1,521 facilities)
  - **L315** §3.2 Sample Size
  - **L596** §3.3 SOP for Data Collection
  - **L669** §3.4 Data Collection Protocol
    - **L777–L960** §3.4.1.3 Patient Listing
- **L1135** §4 Internal QC + Regular Supervision
- **L1202–L1239** Field Logistic reminders (CAPI + Supervisor App usage blocks)
- **L1254–L1309** **CSPro / CSEntry installation guide**
- **L1311** §5 The Survey Questionnaire
  - **L1313–L1382** **Questionnaire numbering scheme**
- **L1870** §6 Quality Control
  - **L1873–L1930** Data transfer, extraction, cleaning, processing

## Diff vs Apr 28 manual

**Added:**
- Full **CSPro / CSEntry installation guide** (L1254–L1309) — verbatim from Carl's Survey-Manual-CAPI-Inputs (replaces legacy SPEED 2023 / Dropbox / `aspsi.database2023@gmail.com` instructions).
- **Supervisor App reminders block** (L1219–L1239) — facility visit log, HCW master list capture, Daily Response Monitor, Refusal & Replacement Log, Issue Ticket escalation.
- **12-digit questionnaire numbering scheme** (L1313–L1382) — see below.
- **Daily 10 PM CSWeb sync mandate** (L1877–L1879).
- **Initial Data Cleaning workflow** (L1915–L1930) — SPSS download, Approved vs On Hold classification.

**Removed / superseded:**
- Legacy Dropbox sync instructions (formerly SPEED 2023 / `Project_SPEED_2023` / `DBAspsi#23` credentials).

**Reworded:**
- Patient listing randomization wording tightened (L900–L907) — see below; **but the underlying procedure was NOT updated to Carl's May 5 refinement** (flag).

## How Carl's CAPI inputs landed

| Carl's section | Working File treatment | Verdict |
|---|---|---|
| **CSEntry installation guide** | L1254–L1309 — verbatim with screenshot placeholders stripped | ✅ Verbatim |
| **HCW Survey self-admin guide** (Annex 1 §1.2) | **NOT INTEGRATED.** Manual still uses Apr 28 generic HCW protocol (L764–L810) | ⚠ **Significant gap.** Carl's three-capture-path detail + Field Supervisor / Data Encoder duties + administration portal flow is missing |
| **Data transfer** | L1877–L1879 — paraphrased to single 10 PM daily sync | ⚠ Carl's three-point sync (end-of-interview / end-of-day / on-demand) simplified to one daily sync; loses redundancy |
| **Bench testing** | **NOT INTEGRATED.** No pre-deployment bench-testing gate documented in §6 QC | ⚠ **Significant gap.** Without explicit bench-testing protocol, field teams have no documented pre-field validation gate |
| **Supervisor App operations** (Annex 1 §1.3) | Referenced (L655, L1219–L1239) but not detailed inline. Annex 1 §1.1 cited (L1309) for troubleshooting | Partial — operational steps assumed to live in attached Annex 1 |
| **HCW Master List as denominator** | L1225–L1227 — *"Capture the master Healthcare Worker list ... at the courtesy call. The list is the official denominator for response-rate monitoring"* | ✅ Adopted, but the **60% threshold itself is not explicitly stated** in the manual text |

## Patient Listing — divergence

Working File (L900–L907): *"CSPro will generate a random number n within an interval of 1–10, instructing the enumerators to wait for n minutes before listing the second patient who enters the station after the time interval... Once they finish listing, CSPro will generate another random number, and the enumerators will repeat the same process."*

This is the **Apr 28 baseline procedure** (per-patient random interval with re-approach). It does **NOT** match Carl's May 5 refined methodology:

> Carl's Survey-Manual-CAPI-Inputs (lines 30–32): *"enumerators conduct continuous listing during the designated listing window, capturing every eligible patient who passes through the listing station... the Patient Listing application designates the **first two-thirds** of the listed pool as main respondents and the **last third** as backup respondents, in the order patients were listed."*

Carl's note in his draft (lines 44–45): *"This procedure follows the methodology validated in the UHC Survey Year 1 (IDinsight, 2024)."*

> [!info] Two methodologies in play; Working File preserves the older one
> The Working File's per-patient-random-interval procedure is **already the F3b protocol Carl wrote** in April — see [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F3b Patient Listing Protocol|Source - Annex F3b Patient Listing Protocol]]: *"CSPro-driven randomization: generates a random interval 1–10 minutes; enumerator waits n minutes, approaches the next patient, lists them, and repeats."* So the Working File is **not** "reverting" or "dropping" Carl's content — it's preserving the F3b protocol intact.
>
> The divergence is that Carl's **May 5 CAPI Inputs** introduced a *new* refinement (continuous listing during designated window → first-2/3 main + last-1/3 backup post-window systematic split) that the Working File didn't pick up. [[Source - DOH Survey Protocol V2 (30 April)|Protocol V2]] (L1025–L1035) also uses the per-patient-interval wording, suggesting alignment to the older F3b spec.
>
> Practical disposition: held for [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/Dr Myra Silva-Javier|Myra]]'s active review pass per memory `feedback_defer_clarifications_during_upstream_review.md`. After her edits land, the residual question is whether Carl's May 5 refinement should be retired (preserve F3b protocol as-is) or pushed through (update F3b + Protocol V2 + Working File together).

## Questionnaire numbering — variant of Carl's brief

Working File scheme (L1313–L1382, **adopted**):

> *"The 12-digit coding... first 6 digits... Region, Province, Municipality... Digits 7–8 (Facility Number)... Digits 9–10 (Respondent Type)... Digits 11–12 (Response Number)."*
>
> Example: **`035401-01-22-03`** = Region III (`03`) / Pampanga (`5`) / Magalang (`401`) / 1st sampled facility (`01`) / **Respondent Type 22 = HCW** / 3rd HCW respondent.

Respondent type codes (L1332–L1340): **11 = Facility Head, 22 = HCW, 33 = Patient, 44 = Household.**

> [!warning] Variant of Carl's adopted scheme
> Carl's [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Questionnaire Numbering Convention|Questionnaire Numbering Convention]] (adopted 2026-05-05) defined the 12-digit format as `RR-PP-MMM-FF-CCC` = Region 2 + Prov 2 + Mun 3 + Facility 2 + **Case 3** (3-digit sequence with 001–699 active / 700–899 replacement / 900–999 refused partitioning).
>
> The Working File instead splits the last 5 digits as **Respondent Type 2 + Sequence 2** (`-CC-CCC` interpretation) using **doubled-digit codes** (11/22/33/44) for respondent type. This implies a **per-respondent-type sequence per facility** (max 99 per type per facility).
>
> Differences:
> - Sequence width: **2 vs 3 digits** — 99 max per type per facility vs 999 max per facility. Per [[Source - Survey Manual Appendix B — Sample Distribution|Appendix B]], max F3 outpatient is 45/facility, F3 inpatient 30/facility, F1 = 1/facility, F2 ≤ 53/facility, F4 ≤ ~50/facility per cluster. **2 digits is sufficient operationally** but loses the active/replacement/refused partition headroom Carl's brief reserved.
> - Respondent type embedded in numbering vs implicit in instrument file — both work; Working File's choice makes cross-instrument deduplication easier but couples respondent type to ID width.
>
> Action: discuss with Kidd whether to (a) accept Working File scheme + retire Carl's `-CCC` partitioning, or (b) push Carl's brief through, or (c) keep both with documented mapping. Refusal handling rule (refused/cancelled get a different number outside designated set, slot filled from ASPSI replacement DB, L1373–L1379) is consistent across both versions — the operational behavior is the same; only the digit layout differs.

## Coding / disposition / refusal handling

- **Interview Result Codes (L1408–L1410):** [1] Completed, [2] Postponed, [3] Refused, [4] Incomplete.
- **Refusal handling (L1373–L1379):** refused/cancelled cases get a different questionnaire number outside the designated set; emptied slots filled from ASPSI replacement database.
- **Appendix D reference** (L1381–L1382) for "field codes" — but [[Source - Survey Manual Appendix D — Case ID Format + Facility Master|Appendix D]] is actually case-ID + facility master, **not a refusal-reason / disposition code table**.
- **No explicit refusal-reason codes** in the Working File. Carl's Annex 1 §1.3 (Refusal and Replacement Log reason categories) **not embedded**.

## Procurement / device specs

Tablets are referenced (L1051, L1206, L1256, L1261–L1263) with functional requirements (Wi-Fi or mobile data, internet, CAPI app provisioned before deployment) but **no hardware specs** (RAM, storage, Android version, processor). Carl's tablet procurement spec sent to Juvy 2026-04-29 (recommended/affordable/modest tiers) is **not referenced** in the Working File. Decision needed: whether to embed the spec in the manual or keep it procurement-side only.

## Inconsistencies + flags for Kidd

1. **Patient Listing methodology divergence** — see callout above; reconcile with Kidd before F3 listing CAPI app proceeds.
2. **HCW self-admin guide missing** — Carl's Annex 1 §1.2 not in main manual; clarify whether it should be inline or in an annex.
3. **Bench testing not in §6 QC** — recommend Kidd add a pre-deployment bench-testing gate sub-section.
4. **Questionnaire numbering variant** — see callout above; reconcile sequence width + respondent-type encoding choice.
5. **Three-point sync simplified to one daily sync** — operational implication: tablet failure mid-day risks losing case data; Carl's three-point model provides redundancy.
6. **HCW 60% threshold** not stated explicitly in manual text — only the master-list-as-denominator framing.
7. **Tablet hardware specs absent** — coordinate with Juvy on whether to embed.

## Open / placeholder text

- "List of selected respondents will be provided to the enumerators for household listing" (L2065) — mechanism not specified.
- Appendix D inline reference (L1381) — codes not shown inline; cross-check against [[Source - Survey Manual Appendix D — Case ID Format + Facility Master|Appendix D]] which turns out to be case-ID + facility master, not codes.

## Cross-references

- [[Source - DOH Survey Protocol V2 (30 April)|Protocol V2]] — the doc this manual is being aligned to.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - DOH UHC Year 2 Survey Manual|Source - DOH UHC Year 2 Survey Manual]] (Apr 28) — predecessor, superseded by this Working File.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Questionnaire Numbering Convention|Questionnaire Numbering Convention]] — Carl's adopted scheme; reconcile vs Working File variant.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Forward-Only Sign-Off|Forward-Only Sign-Off]] — Patient Listing methodology divergence is exactly the kind of issue this rule says to route back to the owning source doc (here, Carl's Survey-Manual-CAPI-Inputs draft).
- [[Source - Survey Manual Appendix A — RA Contacts|Appendix A]], [[Source - Survey Manual Appendix B — Sample Distribution|Appendix B]], [[Source - Survey Manual Appendix C — Endorsement Letters|Appendix C]], [[Source - Survey Manual Appendix D — Case ID Format + Facility Master|Appendix D]], [[Source - Survey Manual Appendix E — UHC IS and non-IS|Appendix E]], [[Source - Survey Manual Appendix F — Patient Listing Form|Appendix F]] — companion appendices in the same Drive folder.
