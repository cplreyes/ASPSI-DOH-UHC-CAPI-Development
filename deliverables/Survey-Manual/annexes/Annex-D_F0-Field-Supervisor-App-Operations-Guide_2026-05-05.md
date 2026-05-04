# Annex D — F0 Field Supervisor App Operations Guide

**Audience:** Field Supervisors (Survey Team Leaders)
**Purpose:** Day-to-day operating reference for the Supervisor App. Covers the five F0 forms, the daily sync workflow, and the escalation flow.

---

## What F0 is

F0 is a CSPro CAPI application that runs in CSEntry on the Field Supervisor's tablet, alongside F1, F3a, F3b, F4a, and F4b. It captures all structured supervisor work — facility visits, HCW master list, daily response monitoring, refusals and replacements, and escalation tickets — and syncs to the same CSWeb server as the enumerator modules.

F0 has five forms; each form opens as a separate case type within the F0 application.

| Form | Trigger | Purpose |
|---|---|---|
| **F0a — Facility Visit Log** | Each time you visit a facility | Captures arrival, courtesy call, endorsement letters, workstation, focal person, departure |
| **F0b — HCW Master List** | Embedded in F0a | Roster of eligible HCWs at the facility (excludes BHWs); the F2 60% denominator |
| **F0c — Daily Response Monitor** | End of every field day | Per-facility response counts vs target; midpoint follow-up flag |
| **F0d — Refusal & Replacement Log** | Whenever a refusal, ineligibility, or replacement happens | Audit chain for sampling weight adjustments |
| **F0e — Issue Ticket** | Whenever you need to escalate | Technical, methodological, ethical, or logistical issues |

---

## F0a — Facility Visit Log

**Open this form** when you arrive at the facility for the courtesy call.

1. Tap **+** in F0a's case-listing screen. The application auto-fills your supervisor code, the date, and prompts for the facility ID (look up from the facility list).
2. Confirm the facility profile (region/province/city/barangay/type/ownership/integration status) — pre-populated from the master facility list.
3. Wait for the **GPS lock** before tapping Start. The app captures arrival timestamp and coordinates automatically.
4. Conduct the courtesy call. As you go, record:
   - Outcome: approved (head present), approved (representative), refused, rescheduled, other
   - Head's name, position, tenure (must be ≥ 6 months per Protocol), contact
   - Endorsement letters delivered (DOH, SJREB, PSA, ASPSI)
   - Workstation arrangement
   - Focal person (name, position, contact, channel)
5. Open **F0b — HCW Master List** as a roster within F0a. Enter one row per eligible HCW. Confirm BHWs are excluded.
6. Confirm F2 distribution: QR poster locations, paper forms left at facility, supervisor tablet staging.
7. Take the **verification photo** of the facility signage or main entrance.
8. Before leaving, tap **End Visit**. The app captures departure timestamp and coordinates and computes total visit duration.

## F0b — HCW Master List

Captured inline within F0a. One row per HCW. Required fields: roster number, role (physician, nurse, midwife, pharmacist, etc.), employment type (regular, contractual, JO, etc.), contact channel. Total count must match the facility's plantilla or staff log.

The F2 admin portal reads this list as the denominator for response-rate calculations.

## F0c — Daily Response Monitor

**Open this form** at the end of every field day at the team's lodging.

1. Select the facility (or facilities) covered today.
2. The form pulls case counts from CSWeb when online: F1, F3a, F3b, F4a, F4b. If offline, enter counts manually from the enumerators' tablet case-listing screens.
3. Add the F2 response count from the F2 admin portal (or estimate from the field if unreachable).
4. Compare against per-facility targets. The form flags facilities below the midpoint trigger (≤ 40%) and below the close-of-window threshold (< 60% for HCW).
5. For each flagged facility, record the action taken: no action, follow-up with focal person, extension requested, escalated to PI.
6. Sync to CSWeb before closing the tablet.

## F0d — Refusal & Replacement Log

**Open this form** for every refusal, ineligibility, or replacement encountered.

1. Select the original case (facility, type, listing position).
2. Reason category: refused listing, refused interview, ineligible, unreachable, infectious/grave (for patients), other.
3. Contact attempts: record up to three attempts (date/method/outcome).
4. If a replacement is being drawn, link the new case via the `REPLACEMENT_FOR` field.
5. The Data Programmer's daily replacement report is generated from this log.

The replacement rate is monitored facility-by-facility and cluster-by-cluster. When a facility approaches 8%, the Field Supervisor escalates to the Survey Manager and Project Lead through F0e.

## F0e — Issue Ticket

**Open this form** for any issue you cannot resolve in the field.

Required fields:
- Type: technical, methodological, ethical, logistical
- Severity: low, medium, high, blocker
- Affected facility / module / case ID
- Description (free text)
- Assignee: Data Programmer / PI / Survey Manager / DOH-PMSMD focal person

Tickets are reviewed daily by the Data Programmer. Severity = Blocker tickets are also pinged to the project Viber group for immediate attention.

---

## Daily sync workflow

1. **Morning** — open F0c and confirm yesterday's counts synced. Note any unsynced cases.
2. **At each facility** — work in F0a from arrival to departure. Sync after each facility visit when network is available.
3. **End of field day at lodging** — open F0c and complete the daily monitor. Resolve any unsynced enumerator cases on the team's tablets. Sync everything before closing the tablet.

---

## Escalation flow

| Trigger | Action |
|---|---|
| HCW response ≤ 40% at midpoint | F0c records follow-up; Field Supervisor contacts focal person |
| HCW response < 60% at window close | F0c records; Field Supervisor requests one-time 3-day extension through supervising RA |
| HCW response still < 60% after extension | F0e to PI; PI + DOH-PMSMD focal person decide retention with weighting or exclusion |
| Replacement rate ≥ 8% per facility | F0e to Survey Manager + Project Lead |
| Replacement rate ≥ 10% per facility | F0e to PI; data flagged for downweighting or exclusion |
| Technical/CAPI issue blocking work | F0e severity = Blocker; Viber ping to project channel |
