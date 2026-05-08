---
type: source-summary
source: "[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/2026-05-06-survey-manual-bundle/2026-04-30_Protocol-vs-Survey-manual]]"
date_ingested: 2026-05-07
tags: [protocol, survey-manual, diff, sampling, eligibility, hcw-threshold, patient-listing]
---

# Source — Protocol vs Survey Manual Diff (2026-04-30 Myra)

A **Claude-generated comparison** circulated by [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/Dr Myra Silva-Javier|Myra]] on 2026-04-30 alongside [[Source - DOH Survey Protocol V2 (30 April)|Protocol V2]]. Compares the **Respondent Selection (RS) Document** (Apr 28 Survey Manual) against the **Survey Protocol (SP, Protocol V2)** across all four modules, identifying gaps and conflicts. Myra's directive: *"Please adjust the survey manual to the protocol."* ~188 lines.

## Document structure

- **Part 1** — Points in RS document NOT in SP (i.e., manual-only operational detail)
- **Part 2** — Tabulated differences per module (F1 / F2 / F3 / F4)

## Items in RS (Survey Manual) but NOT in Protocol V2

### LGU + facility coordination (pre-data-collection)
- Office of the Mayor visit + endorsement letter routing (with DOH national endorsement, SJREB clearance, PSA clearance attached)
- Facility's official endorsement letter at courtesy call
- Patient listing day scheduling + focal-person identification
- Temporary survey-team workstation assignment

### F1 Facility Head — manual-only details
- Representative-permitted-with-conditions language
- Advance copy of survey provided for secondary-data prep
- Secondary data: staffing, costs, lab service prices, DOH licensing, Konsulta accreditation
- Explicit ~1 hour duration in Manual; SP buries it in Data Collection Protocol chapter

### F2 HCW — manual-only details
- **Target 4–53 HCWs per facility** depending on UHC IS size + patient load
- Aim: ≥1 HCW per role (physician/nurse/midwife/...)
- **Distribution channels: Viber, Facebook Messenger** (manual specifies; SP doesn't)
- Paper form drop-off via designated contact, end-of-day collect
- QR codes proactively distributed to encountered HCWs
- **Lottery odds: 1-in-~50 chance of PHP 1,000** (manual specifies odds; SP only says "raffle")
- 1-week post-visit follow-up if targets not met

### F3 Patient — eligibility + listing protocols
- **Patient residency requirement** — must be resident of same province ≥6 months (SP doesn't state residency for patients)
- **RHU sampling frame** — municipal residents present OR pre-listed (SP omits "municipal residents")
- **Exclusion criteria explicit** — "too ill" / cognitive deficits (SP implies but doesn't list as formal criterion)
- **50% oversampling** of required patients as backup for non-response
- **Outpatient listing** — bottleneck identification, registration/OPD triage positioning, multi-station handling, **CSPro-generated interval randomization**
- **Inpatient listing** — billing/discharge stationing, no-ward-entry rule, multi-station handling
- **Other situations** — refusal documentation in CSPro + new random number; minors / elderly / infirm engagement of adult representative; specialty clinic in separate building (list at both, divide target equally)
- **Listing data captured** — PII (patient + companion), distance from home, mode of transport, subdivision/non-subdivision, contact info, **CSPro tagging as "patient exit survey" or "follow-up household survey"**

### F4 Household — manual-only details
- Explicit 4 UHC IS + 4 non-IS sites *since 2020* (UHC IS designation date)
- Field-team responsibilities: tablets, CAPI, manual, protocols, ID cards, travel guidelines, monitoring, consent, refusal docs, completeness, data security/privacy

## Tabulated differences (RS vs SP)

The diff produces one comparison table per module. **Highlights for CAPI:**

### F1 Facility Head
- **Sampling method:** RS doesn't formalize (focuses on field protocol); SP specifies stratified random sampling × proportional allocation
- **6-month tenure requirement** — SP only
- **Replacement rate cap 5–10%** — SP only (RS is silent)
- **Private hospital additional eligibility** (SJREB acceptance without separate review, 15–30 day completion, fee waiver) — SP only
- **Availability protocol:** RS allows up to 3 options (same-day rep / rep with permission / reschedule); SP requires 3 contact attempts on 3 separate days before non-responsive

### F2 HCW
- **Response threshold:** RS implies via 1-week follow-up; **SP mandates 60% of master list with 40% midpoint trigger** + one-time 3-working-day extension
- **BHWs:** RS doesn't mention; **SP explicitly excludes**
- **Reminder policy:** RS implies follow-up coordination; **SP allows single neutral reminder only — no individual worker may be approached/pressured**
- **Distribution channel:** RS lists Viber/FB Messenger/QR/paper; SP says "online link, QR code posted in facility, offline version installed on a device/machine"
- **Incentive:** RS says 1-in-~50 odds; SP says "raffle for PHP 1,000, weekly draws"

### F3 Patient (Inpatient + Outpatient)
- **Inpatient residency:** RS = same province ≥6 months; **SP = no residency requirement**
- **Inpatient age:** RS = ≥18 (with adult-representative provision); SP = no minimum age but adult representative may sign consent
- **Outpatient residency:** RS = municipal residents (RHU); SP = no residency requirement
- **Outpatient post-consultation rule:** SP **explicitly distinguishes** (OPD respondents must be post-consultation, not waiting/mid-consultation); RS doesn't
- **Listing method:** RS = CSPro-generated interval + 50% oversampling + station logic; SP = systematic interval from consultation list (RHU) + intercept at OPD/discharge (hospital)
- **Stopping rule:** RS doesn't state for outpatients; **SP mandates stop at quota** (no additional even with time + patients)
- **Tokens:** RS doesn't state; SP = PHP 500 raffle entry + PHP 100 token for household respondents

### F4 Household
- **Site selection logic:** RS has 4 UHC IS + 4 non-IS per island group; SP same logic, labels as "first stage of selection", references IR Table 4, **explicitly notes total = 16 UHC IS + 16 non-IS**
- **PSU definition:** RS = barangays in sampled PSUs; **SP = barangays as PSUs, classified by urbanicity (urban/rural), proportionate allocation (PIDS 2025 design)**
- **Stratification within sites:** RS doesn't describe; **SP requires barangays stratified by urbanicity before PSU selection**
- **SSU selection method:** RS doesn't describe; **SP = systematic random sample from household listing, interval-based, no pre-identification by name/address**
- **Household listing:** RS doesn't mention; **SP flags as TODO** — fresh listing vs existing list?
- **Sample size:** Both = 2,672 households; SP adds computation assumptions (50% expected proportion, 95% CI, 3% MoE, design effect 2.5)
- **Design effect = 2.5** — SP only; **highest of the four modules**
- **Respondent eligibility:** SP adds "only one respondent per household, following LFS design"
- **Interview duration 60–90 min** — SP only
- **Non-contact protocol:** SP requires ≥3 visits at different days/times before non-contact + Visit Sheet with reason codes
- **Replacement basis:** SP defines (vacant, non-residential, unsafe; or repeated contact failures after 3 documented visits; drawn from same barangay cluster); RS doesn't detail

## Why this matters for Carl

The diff is the **operational checklist** for what needs alignment in the manual. Items where the **Survey Manual** is more detailed than the Protocol (e.g., CSPro-driven listing, field channels, oversampling, station logic) are typically **CAPI-implementation rules** that Carl's specs need to honor; items where the **Protocol** is more detailed (e.g., HCW 60% threshold, F4 urbanicity stratification, replacement rate caps, no-ward-entry rule) are **regulatory/sampling-design rules** that Carl needs to surface in the F-series CAPI apps + admin portal (e.g., a per-facility HCW response-rate widget hitting 40%/60% thresholds).

## Cross-references

- [[Source - DOH Survey Protocol V2 (30 April)|Protocol V2]] — the SP side of the diff.
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - DOH UHC Year 2 Survey Manual|Source - DOH UHC Year 2 Survey Manual]] (Apr 28) — the RS side of the diff.
- [[Source - Survey Manual Working File (2026-05-06 Kidd)|Survey Manual Working File]] (May 6) — Kidd's update integrating the diff resolutions; some divergences remain (see callouts there).
- [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/F2 Admin Portal|F2 Admin Portal]] — concrete implementation target for HCW 60% threshold + master-list-as-denominator widgets.
