---
type: source-summary
source: "[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/2026-05-06-survey-manual-bundle/2026-04-30_DOH-Survey-Protocol-V2-30-April]]"
date_ingested: 2026-05-07
tags: [protocol, sjreb, psa, sampling, eligibility, capi, csweb, patient-listing, hcw-threshold]
---

# Source — DOH Survey Protocol V2 (30 April 2026)

The **master research protocol** for the ASPSI-DOH UHC Survey Year 2, circulated by **[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/Dr Myra Silva-Javier|Dr Myra Silva-Javier]] ("Myra")** to the team on 2026-04-30 with the directive *"Please adjust the survey manual to the protocol"*. **This is the SJREB + PSA submission baseline** and the reference document for all SOPs. ~6,092 lines of operational protocol text. The Apr 30 send included a [[Source - Protocol vs Survey Manual Diff (Apr 30 Myra)|Claude-generated diff]] flagging issues for team discussion.

**Authorship:** Daisy reorganized the inception report into protocol structure; [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/Juvy Chavez-Rocamora|Kidd]] supplied the sampling design from the Survey Manual; Myra ensured cross-document consistency.

## Document structure

| Line | Chapter |
|---|---|
| L11 | Table of Contents |
| L58 | Introduction |
| L88 | Description of the Research Problem |
| L105 | Project Objectives |
| L127 | Significance of the Study |
| L142 | Review of Related Literature |
| L531 | Conceptual Framework |
| L553 | Study Design |
| L644 | Study Sites |
| L749 | Study Population |
| L829 | **Sampling Design** |
| L1187 | **Description of the Measurement Tools** |
| L1305 | Validity and Reliability Testing |
| L1447 | **Data Collection Protocol** |
| L1772 | Data Processing |
| L1801 | Statistical Analysis |
| L1835 | Ethical Considerations |
| L2618 | References |
| L2735 | Annexes |

## Sample design — verbatim numbers

| Instrument | Total | Per-domain | Design effect | Notes |
|---|---|---|---|---|
| **F1 Facility Head** | 1,521 facilities | stratified by facility type × province/HUC × ownership; proportional allocation | — | Replacement cap 5–10% (L1516–L1517) |
| **F2 HCW** | Census within facility | No fixed quota; **60% master-list response threshold per facility** (L1565); 40% midpoint triggers follow-up; 60% gate requires PI/DOH coordination | — | Online link + QR + offline device fallback (L1524–L1528). **BHWs explicitly excluded** (per [[Source - Protocol vs Survey Manual Diff (Apr 30 Myra)|diff]]) |
| **F3 outpatient** | 45 per province/HUC | 95% CI, 5% MoE, 3% expected outpatient prevalence (L1066) | **1.0** | 45% public / 55% private (L1069) |
| **F3 inpatient** | 30 per province/HUC | 95% CI, 5% MoE, 2% expected inpatient prevalence (L912–L913) | **1.0** | 55% public / 45% private (L914–L916) |
| **F3 oversampling** | 50% backup respondents (L959–L961) | per-facility 4–53 patients depending on size/load | — | |
| **F4 household** | **2,672 (1,336 UHC IS + 1,336 non-IS)** (L1153–L1155) | 2-stage stratified cluster (PSU = barangay; SSU = household, systematic); urbanicity stratification per PIDS 2025 (L1137–L1141) | **2.5** (highest of the four) (L1161–L1162) | 50% expected proportion, 95% CI, 3% MoE |

## Eligibility — verbatim by instrument

- **F1 Facility Head** — must have held position ≥6 months (L771); authorized representative permitted with same tenure rule (L878–L882).
- **F2 HCW** — all employed HCWs at sampled facility during data collection, regardless of employment type (L1522–L1523); **BHWs excluded**.
- **F3 patient (inpatient)** — admitted patients preparing for discharge (L789–L791); **resident of same province ≥6 months** (L970); ≥18 years old (L971); excluded if too ill or cognitively impaired (L975–L977); adult representative may respond on behalf (L973–L974).
- **F3 patient (outpatient)** — RHU/health center: patients present OR pre-listed; hospital OPD: patients **post-consultation** (not waiting/mid-consultation) (L807–L814); ≥18 years; ≥6 months residence; same exclusions.
- **F4 household** — one respondent per household, ≥18 years, ≥6 months residence in barangay (L1177–L1178), household head OR primary health-decision-maker (L1179–L1180); same exclusions.

## Data collection mode — what's prescribed

The protocol prescribes **CAPI on Android tablets for F1, F3, F4** (face-to-face, enumerator-administered) and **online self-admin + offline device fallback for F2** (L1206, L1238, L1270, L1487, L1521–L1528). This is **architecturally compatible with the F2 PWA** at v2.0.0 in production — the protocol's "online link + QR code in facility + offline-installed-on-device" model maps onto the PWA's tokenized prefilled URL + offline IndexedDB + service-worker model. CSWeb is mandated as the cloud transmission target with daily 10 PM upload (L1758, L1953–L1956); CSWeb dashboard monitoring with completeness/duration/non-response alerts (L1750–L1756). **Version-numbered CAPI applications** with version recorded on all datasets for traceability (L1443–L1445).

## Patient listing — operational rules

- **Inpatient:** discharge/billing area only, not wards (L980–L982, L1012–L1014); CSPro generates random waiting intervals between approaches; new interval after each refusal (L1025–L1035); 50% oversampling backup; multi-station coordination via supervisor for >3 billing stations (L1008–L1011).
- **Outpatient (RHU):** systematic interval from daily consultation list, random start (L1647–L1655); enumerate every nth patient until quota met; no additional interviews beyond quota (L1667–L1670).
- **Outpatient (hospital OPD):** convenience-intercept post-consultation within systematic target (L1086–L1093).
- **Patient Listing Form documents** total list count, starting point, interval, completed/refused/ineligible (L1664–L1666). [[Source - Survey Manual Appendix F — Patient Listing Form|Appendix F]] is the paper template.

## Operational details that touch the data dictionary

- **Daily CSWeb upload by 10 PM** (L1758); first-week + then-weekly interim extractions (L1759–L1761).
- **Facility Contact Log** — date, time, method, outcome of all contact attempts; min 3 attempts on separate days/times before non-responsive classification (L1505–L1508).
- **Visit Sheet (F4 household)** — at least 3 contact attempts at different days/times; reason codes for non-contact/refusal (L1681–L1684, L1709, L1733).
- **Interview duration benchmarks (for QC):** F1 ~1h, F2 30m, F3 ≥1h, F4 1–1.5h (L1408–L1409, L1469, L1536, L1596–L1597, L1678).
- **Respondent identifiers separated from PII for analysis** (L1808–L1813); facility codes + geographic codes are the link.
- **Partial interviews** not counted unless respondent explicitly agreed to continue (L2339–L2342).
- **'Don't know' designated** for facility-head responses when recall fails (L1494–L1495).

## Items that may have moved on or are at risk

> [!info] Cross-checks against current PIB / sprint state
> - **F2 PWA decision (2026-04-17)** is architecturally consistent with Protocol V2's "online + offline + paper" prescription — no contradiction.
> - **F1 Designer sign-off CLOSED 2026-05-04** (E2-F1-010) used [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/F-Series Value Set Conventions|F-Series Value Set Conventions]] (NA = highest-code-at-field-width) and AAPOR 2023 11-code; protocol does not redefine these.
> - **PSGC self-served from PSA 1Q 2026** (memory `project_aspsi_psgc_value_sets.md`) — protocol does not specify PSGC version, but [[Source - Survey Manual Appendix D — Case ID Format + Facility Master|Appendix D]] anchors the case-ID + facility master list to PSA 1Q 2026, consistent with Carl's pipeline.
> - **HCW 60% threshold gate** (L1565, L1584–L1591) is operationally significant — F2 PWA Admin Portal may need to surface a per-facility response-rate widget that hits 40% midpoint trigger and 60% gate.

## Annex placeholders / TODO markers

- **Multiple "Annex XX" placeholders** for Patient Listing Form (L984, L1628), Visit Sheet (L1709), questionnaire annexes (L1488, L1616, L1712), consent forms (L1601, L1688), F4 replacement (L1732). [[Source - Survey Manual Appendix F — Patient Listing Form|Appendix F]] (Patient Listing Form) and [[Source - Survey Manual Appendix C — Endorsement Letters|Appendix C]] are circulated; some others remain pending in the working bundle.
- **DOH Facility Registry citation** flagged TODO at L833–L834: *"ADD DETAILS ON THE NAME OF LIST AND YEAR IT WAS GENERATED"*.
- **F4 barangay listing method UNRESOLVED** (L1172–L1174): protocol asks whether *"a fresh household listing is conducted before systematic random sampling, or whether an existing list is used"* — affects sampling frame validity.
- **Email encryption standard** flagged TODO at L1946: *"All emails containing study data will be encrypted (USING?)"*.
- **Multi-station logic for >3 billing stations** is supervisor-discretion, no documented algorithm (L1010–L1011).

## Open questions for Kidd / Myra (Carl-relevant)

1. **Facility head 6-month tenure rule** (L771) — enforced at facility selection or only at consent? What if a head was appointed post-sampling?
2. **HCW response-threshold authority** — who (PI / Data Manager / DOH) authorizes facility exclusion or reweighting at 60% gate?
3. **F4 barangay listing method** — fresh listing vs existing? Affects F4 case-ID width planning.
4. **PIDS 2025 urbanicity codes** — does Myra/DOH have the coding framework so CSPro can classify barangays correctly?
5. **CAPI version amendment log** — which artifact tracks amendments (CSWeb metadata field, GSD doc, sprint backlog)?
6. **Partial interview resumption** — does explicit consent to resume re-trigger ICF re-administration?

## Cross-references

- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Revised Inception Report|Source - Revised Inception Report]] — protocol is the SJREB-shaped descendant of the IR.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - DOH UHC Year 2 Survey Manual|Source - DOH UHC Year 2 Survey Manual]] (Apr 28) — superseded by [[Source - Survey Manual Working File (2026-05-06 Kidd)|the May 6 Working File]] which is being aligned to this protocol.
- [[Source - Protocol vs Survey Manual Diff (Apr 30 Myra)|Source - Protocol vs Survey Manual Diff]] — Claude-generated diff Myra circulated alongside this protocol.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/F2 Admin Portal|F2 Admin Portal]] — HCW 60% threshold + master list denominator capture is a concrete admin-portal requirement traceable to this protocol.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/Questionnaire Numbering Convention|Questionnaire Numbering Convention]] — the 12-digit `RR-PP-MMM-FF-CCC` scheme adopted 2026-05-05 carries through into [[Source - Survey Manual Working File (2026-05-06 Kidd)|the Working File]] (with a respondent-type encoding twist worth checking).
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/SJREB|SJREB]], [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/PSA|PSA]], [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/DOH-PMSMD|DOH-PMSMD]] — submission targets.
