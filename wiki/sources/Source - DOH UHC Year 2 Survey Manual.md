---
type: source-summary
source: "[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/DOH UHC Year 2_Survey Manual Apr 28]]"
date_ingested: 2026-05-02
tags: [survey-manual, fieldwork, sop, capi, papi, hcw-protocol, quality-control, aspsi]
---

# Source — DOH UHC Year 2 Survey Manual

> **March 2026 dated, Apr 28 2026 working version** (`raw/DOH UHC Year 2_Survey Manual Apr 28.docx`).
> ASPSI-authored field manual for survey team leaders (STLs) and survey enumerators (SEs). Covers the full chain from facility selection through interview administration, quality control, and data processing.
>
> **Carl's role in this manual** — ASPSI is asking for Carl's input on the **HCW protocol** and the **CSPro install/use section**. The CSPro section in this Apr 28 version is still legacy SPEED 2023 content (Project_SPEED_2023, `aspsi.database2023@gmail.com`/`DBAspsi#23`); Carl's UHC Year 2 rewrite lives at `deliverables/Survey-Manual/CSPro-Section-Draft_2026-04-29.md` and supersedes it.
>
> Tracked under Epic 7 Documentation (`E7-DOC-001`); review iteration owner: [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/Juvy Chavez-Rocamora|Juvy]] / Kidd (main RA).

## Document arc

The manual flows from background → ground rules → fieldwork:

1. **Background of the study** — Year 1 → Year 2 motivation; expansion to 107 UHC IS + 13 non-UHC IS; specific objectives (national/regional/HUC/ICC representation, data utilization framework, stakeholder dissemination).
2. **Definition of terms** — PhilHealth, UHC Law, YAKAP/Konsulta, GAMOT, BUCAS, ZBB, NBB, PCFs, hospital levels, in/outpatient, 4Ps, EMRs, plus consultation modalities.
3. **The Survey Manual** — Six clusters of survey teams (Table 1 — see below); ASPSI provides facility lists and replacement protocol pointer.
4. **Standard Operating Procedure** — Selection of facilities (sample plan tables by region/province/HUC); coordination with LGUs; initial health facility visit.
5. **Data Collection Protocol** — Per-instrument fieldwork (F1 facility head, F2 HCW, F3 patient, F3b patient listing, F4 household).
6. **Field Logistic and Procedure** — Reminders for handling wide-ranging questionnaires, sensitive questions, "others" responses.
7. **Instructions for Administration of the Questionnaire** — Consent, **CSPro install/use guide**, questionnaire numbering scheme, questionnaire walkthrough.
8. **Quality Control** — Data transfer/extraction, post-survey activities, data processing pipeline, duties & responsibilities of STLs and SEs, NDU.

## Field structure (Table 1)

Six survey-team clusters cover the country; **6 RAs + 20 FSs + 100 SEs** total mobilization for **1,521 health facilities** across **120 UHC IS + non-UHC IS**:

| Cluster | Regions | UHC/Non-UHC IS | Facilities | Team |
|---|---|---|---|---|
| 1 | CAR, I, II | 18 | 204 | 1 RA, 3 FS, 15 SE |
| 2 | NCR, III | 27 | 431 | 1 RA, 4 FS, 20 SE |
| 3 | IV-A, IV-B, V | 18 | 284 | 1 RA, 3 FS, 15 SE |
| 4 | VI, VII, VIII, NIR | 22 | 247 | 1 RA, 4 FS, 20 SE |
| 5 | IX, X, XI | 18 | 189 | 1 RA, 3 FS, 15 SE |
| 6 | XII, XIII, BARMM | 17 | 166 | 1 RA, 3 FS, 15 SE |

Sampling allocation table (per-province/HUC) sets uniform target per-province quotas of **67 outpatients + 45 inpatients** across the 88 listed provinces/HUCs.

## Key protocol facts (data-collection chapter)

### Facility head (F1) — interviewer-administered, on-site
- Facility head = RHU/UHU physician (PCFs) or Chief of Hospital / Medical Director (hospitals).
- Interview ideally same day as courtesy call; if facility head unavailable, designated representative is permitted with facility head's approval.
- **Advance copy** of survey provided so the facility can pre-collect required information (staffing, lab/service costs, DOH licensing, *Konsulta* accreditation). Secondary data is requested via **DOH endorsement letter** prior to the interview.
- **Duration:** 30 minutes – 1 hour.
- See [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F1 Facility Head Survey Questionnaire]] for the instrument and [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex A Data to be Collected and Sources]] for the secondary-data templates.

### Healthcare worker (F2) — self-administered (the protocol Carl is reviewing)
- **Primary mode:** self-admin online form, distributed via the **facility's primary communication channel** (Viber, Facebook Messenger) by the assigned facility contact person. Confirmed during the courtesy call; verified on day of visit.
- **Paper fallback** for poor-internet contexts: enumerator drops paper forms with the facility contact at start of facility visit day, collects at end of day.
- Enumerators also distribute QR codes / paper consent forms to any HCWs encountered on-site during the visit.
- **Target sample:** **4–53 HCWs per facility** depending on facility size and patient load; aim for ≥1 HCW per role (physician, nurse, midwife, pharmacist, dispenser, nutritionist/dietitian).
- **Open window:** form stays open throughout data collection period; **target close = 1 week after facility visit**. If no role is met after 1 week, enumerator re-contacts facility contact for re-cascade.
- **Incentive:** lottery, **1-in-~50 chance of PHP 1,000** (mirrors the F2 ICF token in [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex H Informed Consent Forms]]).
- Aligns with the project's three-path F2 capture model — see [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/F2 Google Forms Track]] for historical context (the actual F2 build is the PWA at `deliverables/F2/PWA/app/`, with paper-encoder workflow planned in Sprint AP4 of the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/F2 Admin Portal]]).

### Patient (F3) — interviewer-administered
- **Inpatient inclusion:** scheduled for discharge on data-collection day; resident of same province as facility ≥6 months; ≥18 years.
- **Outpatient inclusion:** municipal residents present at facility, plus pre-listed for medical consultation at time of data collection (sampling frame source).
- **Exclusion:** too ill to participate, cognitive deficits preventing comprehension.
- **Proxy rule:** household head / health-decision-maker may respond on patient's behalf.
- See [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F3 Patient Survey Questionnaire]] and [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F3b Patient Listing Protocol]].

### Household (F4) — interviewer-administered
- Sampled via interval-walking from listed patient households; details in [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F4 Household Survey Questionnaire]].

### Replacement protocol (cross-instrument)
- **3-visit minimum** before a facility/respondent is replaceable (matches [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex D Replacement Protocol]]).
- ASPSI maintains the alternative-respondent / alternative-facility lists.

## Quality Control workflow

### Data transfer & extraction
- **Daily sync ≤ 10 PM** required of all enumerators (CSPro → server) for next-morning fieldwork progress monitoring.
- **Interim extraction** during first full week of data collection — completeness, programmed QC checks, data-quality flags reviewed.
- Weekly extractions thereafter for completed-interview counts and outlier verification.

### Post-survey processing pipeline
- Programmer downloads from server (manual states **SPSS format**) and hands to data manager + assistant data managers.
- Each completed interview classified **Approved** or **On Hold**:
  - **Approved** — passed initial review.
  - **On Hold** — clarification/validation needed; bounces back to survey team.
- **Logic & consistency checks** (≥ 2× weekly) on top of the in-CAPI built-in logic — frequency tables, cross-tabs, outlier analysis on continuous variables, inter-field consistency (impossible combos like male-pregnant), interview-duration anomalies.
- **Final cleaning** is batch-mode after fieldwork closes — extreme-value rechecks across the dataset as a whole.

### Roles & duties (§2.5)
- **STL:** training, recruit local enumerators, manage replacements, check CAPI completeness/accuracy, coordinate with ASPSI Coordinator + Research Associate, ensure forms collation, liquidate cash advances.
- **SE:** training, schedule/contact respondents, conduct **4–5 interviews/day**, ensure form completeness, submit Enumerator's List + Diary + cash vouchers.
- **NDU:** Both STLs and SEs sign a Non-Disclosure Undertaking (Appendix F).

## CSPro install/use section — STALE (Carl's rewrite supersedes)

The manual's **§ Guidelines on installing/using of CSPro** (around p. 60-ish of the docx, lines 1765–1858 in the markdown extraction) walks tablet enumerators through 13 steps (install Dropbox → install CSEntry → grant permissions → Add Application via Dropbox → install Project_SPEED_2023 → enter cases → sync). It carries SPEED-2023-era branding:

- Application name: **Project_SPEED_2023**
- Sync account: **aspsi.database2023@gmail.com / DBAspsi#23**
- Sync target: **Dropbox** (not CSWeb)

> [!warning] Stack mismatch
> The Apr 28 manual still describes a **Dropbox sync model** for CSPro (`aspsi.database2023@gmail.com` Dropbox), but the UHC Year 2 architecture per the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSWeb]] track is **CSWeb-based sync** with Apache + MySQL/MariaDB on the project server. Carl's rewrite at `deliverables/Survey-Manual/CSPro-Section-Draft_2026-04-29.md` reflects the CSWeb model and current credentials. The legacy text needs to be replaced wholesale, not patched.

GPS capture is correctly mentioned in Step 12 ("Make sure the **GPS location** icon is enabled to capture GPS coordinates of the respondent's location") — that piece survives the rewrite and aligns with the [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/GPS and Photo Capture]] design.

## Questionnaire numbering scheme (§ Survey Questionnaire walkthrough)

- **9-digit case ID:** first 6 digits = Region/Province/Municipality numerical code; last 3 digits = enumerator's per-day respondent counter.
- Example: `035401004` = Central Luzon Pampanga Magalang, 4th interview of the day.
- STLs preassign respondent-number ranges to enumerators to prevent collisions.
- Refused/cancelled cases get a different numerical range; the empty respondent slot is filled by the next replacement establishment from ASPSI's database.
- The manual's code lookup tables are placeholder ("to replace with actual codes once protocols are finalized") — the scheme is defined but the codes for UHC Year 2's actual facilities aren't yet baked in.

> [!note] Implication for F1/F3/F4 case-control block
> The F1/F3/F4 dictionaries currently use `QUESTIONNAIRE_NO` length-6 plus a separate `INTERVIEWER_ID` and case-control fields. The manual's 9-digit composite (6 PSGC + 3 sequence) collapses respondent counter into the case ID. If ASPSI wants the manual scheme literal, the dictionaries' case-control block needs a 3-digit `RESPONDENT_NO` field added and `QUESTIONNAIRE_NO` should remain 6-digit (PSGC). See `deliverables/CSPro/F1/generate_dcf.py` for current shape — adjust there per "generator is source of truth".

## Other survey instructions (cross-cutting)

- Enumerators identify ASPSI to respondents — NPC registration **PIC-000-358-2021**, website `https://www.asiansocial.org/`.
- Project Coordinator contact (printed in the manual): **[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/Juvy Chavez-Rocamora|Ms. Juvy Rocamora]]**, 2nd Floor, MG Building 10001 Mt. Halcon St., Los Baños, Laguna 4030; `aspsiglobal@gmail.com` / `aspsi.doh.uhc.survey2@gmail.com`; 63-49-536-3448.

## Cross-references

**Concepts**
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/UHC Survey Year 2]] — overall study
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSPro]] / [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/CSWeb]] — toolchain
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/F2 Google Forms Track]] — historical track context for the HCW protocol
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/F2 Admin Portal]] — current F2 PWA admin/encoder build
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/GPS and Photo Capture]] — capture spec referenced in Step 12

**Entities**
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/ASPSI]] — manual author
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/DOH-PMSMD]] — endorsement letter origin
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/Juvy Chavez-Rocamora]] — Project Coordinator contact printed in manual

**Other sources referenced inside the manual**
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F1 Facility Head Survey Questionnaire]]
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F2 Healthcare Worker Survey Questionnaire]]
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F3 Patient Survey Questionnaire]]
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F3b Patient Listing Protocol]]
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex F4 Household Survey Questionnaire]]
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex H Informed Consent Forms]]
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex D Replacement Protocol]]
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex B List of UHC Integration Sites]]
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex C List of Non UHC Integration Sites]]
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Annex A Data to be Collected and Sources]]
