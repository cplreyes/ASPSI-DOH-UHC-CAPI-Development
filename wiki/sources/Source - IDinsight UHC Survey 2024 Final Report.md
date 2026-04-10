---
type: source-summary
source: "[[raw/[FOR SHARING] DOH UHC Survey 2024 Final Report.pdf]]"
date_ingested: 2026-04-10
tags: [year-1, idinsight, baseline, methodology, surveycto, predecessor]
---

# Source — IDinsight UHC Survey 2024 Final Report (Year 1)

The **predecessor** to the [[wiki/concepts/UHC Survey Year 2|UHC Survey Year 2]]: the full final report of the **first round** of the DOH UHC Survey, designed and conducted by [[wiki/entities/IDinsight|IDinsight]] under commission from [[wiki/entities/DOH-PMSMD|DOH-PMSMD]]. 224 pages, version 5 (December 2024); originally submitted June 28, 2024 by Dr. Alice A. Redfern (Associate Director, IDinsight) as Principal and Coordinating Investigator.

> [!important] Why this matters for Carl's Year 2 work
> Year 1 used **SurveyCTO**, not CSPro. The Year 2 switch to [[wiki/concepts/CSPro|CSPro]] is therefore a deliberate stack change, not a continuation. Carl is **not** inheriting any usable CAPI artefacts from Year 1 — he is rebuilding the data collection layer from scratch against the same indicator framework. The Year 1 report is most useful as **content reference** (questionnaire scope, indicator definitions, sample design, field operations) and as a **comparability anchor** (Year 2 must produce indicators commensurable with Year 1).

## Authors

| Name | Title / Email |
|---|---|
| Dr. Alice Redfern, MBBS | Lead author, PCI — alice.redfern@idinsight.org |
| Dr. Liza von Grafenstein, PhD | liza.grafenstein@idinsight.org |
| Meg Battle, MPH | meg.battle@idinsight.org |
| Alec Lim | alec.lim@idinsight.org *(named DOH-PMSMD counterpart for Year 1)* |
| Dominique Sy, MSc | dominique.sy@idinsight.org |
| Isabel del Rosario, MSc | isabel.delrosario@idinsight.org |
| Gio Hernandez | gio.hernandez@idinsight.org |

Field Managers: Darahlyn Biel-Romualdo, Flynn Ayugat. Operations: Marilou Blen, Laura Villanueva. Research support: Anjani Balu, Hannah Reynolds, Priyanka Dua. Training: Jerick Chan.

## Acknowledged Stakeholders

- **DOH-PMSMD**: Undersecretary Kenneth G. Ronquillo, Mr. Lindsley Jeremiah Villarante, Ms. Reneelyn Pimentel, Ms. Chrys Paita
- **DOH bureaus**: HHRDB, HFSRB, HFDB
- **External experts**: Dr. Valerie Ulep, Dr. Eduardo Banzon, Dr. Albert Domingo (now Year 2 PMSMD Undersecretary), Mr. Ian Nuevo, Cong. Stella Quimbo
- **LGU pilot/training sites**: Marikina, Parañaque, La Union, Baguio City, Mandaue City, Cagayan de Oro City

## Scope and Sample (Year 1)

| Survey Module | n (achieved) | Sample Frame | Sampling Method |
|---|---|---|---|
| **Facility Head** | **1,135** facilities | Stratified random across UHCIS × facility type, drawn from DOH NHFR + PhilHealth Konsulta accredited list + DOH Malasakit private list | Single-stage stratified, finite population correction. 5 strata: rural PCF, urban PCF, L1, L2, L3 hospitals |
| **Healthcare Worker** | **11,582** HCWs | Quota sampling within each sampled facility | Two-stage cluster (facility → HCW). Mode: online SurveyCTO form OR paper double-encoded |
| **Patient (household)** | **7,824** patients | Patient exit listing at each sampled facility, then household visits | Two-stage cluster (facility → patient → household). Patient survey + companion survey + household-member roster |
| **Household members** | **31,674** | Roster within sampled patient households | (rolled into patient survey) |

- **Coverage**: 70 active UHCIS (Masbate City excluded mid-fieldwork after MoU non-renewal — facility/HCW data still partially collected with smaller sample, no household data).
- **Calendar**: Data collection **February – May 2024**.
- **Precision targets**: National (active UHCIS only) MoE < 0.05; Regional MoE 0.10; Provincial / HUC / ICC UHCIS-level MoE 0.10–0.15.
- **Languages translated**: English original → Filipino (Tagalog), Cebuano (Bisaya), Hiligaynon, Ilokano, Waray, Bikol. Back-translated for accuracy.
- **Response rates**: Facility 98.0%, HCW 142.6% (over-quota in many regions), Patient 96.3%.

## Survey Module Structure (Year 1)

The Year 1 report describes the same conceptual structure that Year 2 inherits, with one major addition (Year 2 adds a standalone **household survey** in addition to the patient-exit-derived household component):

| Section | Module | Coverage |
|---|---|---|
| i | Introduction & Informed Consent | Per-survey intro |
| ii | Respondent Profile | Sociodemographics: age, gender, PPI wealth quartile, education, insured status, residence (PSGC barangay urban/rural) |
| **I. Household / Patient questionnaire** | I.A Awareness · I.B Registration · I.C Health-seeking behavior · I.D Patient satisfaction & provider responsiveness · I.E Service delivery process · I.F Financial Risk Protection (CHE, distress financing, forgone care) | Patient experience & FRP |
| **II. Facility Head** | II.A Awareness/Registration (PhilHealth, DOH licensing, Konsulta) · II.B Service delivery & costing | Facility-level barriers — direct ancestor of Year 2 Annex F1 |
| **III. Healthcare Worker** | III.A Awareness/Registration · III.B HCW satisfaction (support, professional development, compensation) | HRH & worker satisfaction — direct ancestor of Year 2 Annex F2 |

## Stack: SurveyCTO (NOT CSPro)

- **Coding tool**: SurveyCTO Desktop (form authoring)
- **Field tool**: SurveyCTO Collect on enumerator-provided mobile phones
- **Mode**: CAPI throughout, with paper back-up for HCW survey when online forms were impractical (paper forms double-encoded by enumerators); rural patient surveys sometimes by phone
- **Forms developed**:
  1. Facility head SurveyCTO form
  2. Online HCW SurveyCTO form + paper form
  3. Patient listing SurveyCTO form
  4. Patient + household-member questionnaire SurveyCTO form
- **Piloting**: Initial small-scale facility visits in La Union, Marikina, Parañaque (NCR); larger dry run in Baguio (Northern Luzon), Marikina (NCR), Cebu (Visayas), Cagayan de Oro (Mindanao).

## Key Findings (Year 1) — Baseline for Year 2 comparability

**Awareness**
- 99.0% of facility heads and 85.8% of HCWs aware of Konsulta — but only **24.1% of patients** in UHCIS have ever heard of UHC; **18.7%** have heard of Konsulta.

**PhilHealth registration**
- **25.5%** of patients report not being registered or not knowing if they are registered, despite the automatic enrollment policy.
- 92.4% of eligible inpatients pay nothing out of pocket for basic accommodation. But significant OOP and CHE remain, especially in private hospitals.

**Konsulta package**
- 71.3% of facilities in active UHCIS are Konsulta-accredited. Average facility offers 6 of 13 diagnostic services.
- Only 11.2% of patient population registered to Konsulta; only 6.8% have ever seen their Konsulta provider.
- 43.6% of facilities have received any of their expected capitation payments — timeliness is a concern.
- 25.2% of facilities believe patient registration is "not their responsibility" — accountability gap.

**HCPNs**
- 74.1% of facilities have a network of specialists; 85.9% have signed MoUs/MoAs.
- PCFs lag (71.7% vs L1 84.1%, L2 91.3%). E-referrals least common method.
- **75.2% of patients in UHCIS attended hospitals/specialist care without any referral** — gatekeeping is failing.

**Human Resources for Health**
- Understaffing common, especially in PCFs; task-shifting widespread.
- Job satisfaction high overall but compensation timeliness is the top dissatisfier.

**Governance**
- LHSML doesn't sufficiently monitor implementation outcomes; KRAs not correlated with progress.

**Patient experience of care**
- **Accessibility**: General/preventive checkups uncommon. "Not feeling sick enough" is the top reason for forgone care, then high cost. Lower-income, less-educated, uninsured, younger patients least likely to access preventive care.
- **Quality**: 83.5% national overall satisfaction; 84.3% provider responsiveness. Wide regional disparities. Weak spots: basic amenities (70.1%), choice of provider (76.8%).
- **FRP**: In the past 6 months, **25.3% of households had at least one person forgo care for financial reasons**; 18.2% had someone reduce care; **37.9% have taken loans or sold household assets** to pay for healthcare.

## Policy Recommendations (Year 1)

1. **Build trust in public primary care** by improving implementation of core UHC policies. Includes appointing a bureau to oversee primary care/UHC, simplifying PhilHealth registration, enhancing Konsulta uptake, prioritizing health workforce.
2. **Comprehensive communications campaign** with general dissemination, targeted initiatives for vulnerable groups, and facility touchpoint materials.
3. **Targeted price cap on inpatient bills for vulnerable households**, especially private hospital care where most financial risk occurs.

## Cross-References

- Year 2 successor survey: [[wiki/concepts/UHC Survey Year 2]]
- Conducted by: [[wiki/entities/IDinsight]]
- Commissioned by: [[wiki/entities/DOH-PMSMD]]
- Year 2 implementer (replaces IDinsight): [[wiki/entities/ASPSI]]
- Year 2 instruments that inherit Year 1 indicator scope: [[wiki/sources/Source - Annex F1 Facility Head Survey Questionnaire|F1]], [[wiki/sources/Source - Annex F2 Healthcare Worker Survey Questionnaire|F2]], [[wiki/sources/Source - Annex F3 Patient Survey Questionnaire|F3]], [[wiki/sources/Source - Annex F4 Household Survey Questionnaire|F4]] (F4 is new in Year 2 — separate household survey, not a patient-derived household component)
- Year 2 stack: [[wiki/concepts/CSPro]] (replaces SurveyCTO)
- Year 2 inception: [[wiki/sources/Source - Revised Inception Report]]
- Operational analysis: [[wiki/analyses/Analysis - Project Intelligence Brief]]
