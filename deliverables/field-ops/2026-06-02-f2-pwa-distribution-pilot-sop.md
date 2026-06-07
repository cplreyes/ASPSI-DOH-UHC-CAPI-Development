---
type: deliverable
kind: sop
audience: ASPSI field leads · facility contact persons · data manager
prepared_by: Carl Patrick L. Reyes
date_drafted: 2026-06-02
status: draft-for-review
related_tasks: [E5-PWA-004, E5-PWA-005, E5-PWA-006, E5-PWA-007]
companion_to:
  - training/2026-06-02-f2-hcw-self-admin-one-pager.md
  - Survey-Manual/CAPI-PWA-Stakeholder-Section_2026-05-02.md
  - security/Data-Privacy-and-Security-Plan.md
tags: [field-ops, f2, pwa, distribution, pilot, sop, e5]
---

# F2 (Healthcare Worker) Distribution & Pilot SOP

Operational procedures for the **self-administered F2 PWA** (production v2.x): how facilities receive and distribute the survey link, how non-respondents are reminded, how completion is tracked, and the pilot-batch go/no-go gate before full rollout.

> **Grounding.** F2 flow, the 3-day window, the per-facility link, and the paper-encoder fallback come from the **Survey Manual stakeholder section** §2.2. Respondent-facing steps mirror the **F2 HCW one-pager**. Completion tracking uses the **Admin Portal** (HCWs + Responses tabs). Privacy obligations per the **Data Privacy & Security Plan**.
>
> **⟨CONFIRM⟩ markers** are values ASPSI must lock (reminder cadence numbers, pilot sample size + success thresholds). Everything else is specified.

---

## 1. HCW distribution-list SOP  ·  *(E5-PWA-004 / #186)*

How the F2 link reaches healthcare workers, who confirms enrollment, and the escalation path.

### 1.1 Per-facility link
- Each sampled facility gets its **own per-facility survey link** (do **not** reuse another facility's link — provenance + completion tracking depend on it).
- ⟨CONFIRM⟩ whether links are per-facility or per-HCW tokenized; the Admin Portal **HCWs tab** is the enrollment registry and **Reissue-token** is the recovery path for a broken/expired link.

### 1.2 Distribution flow
1. **Identify the facility contact person** (focal person) per facility during sampling/visit planning.
2. **Hand off the link** to the focal person through the facility's **primary communication channel** (Viber / Facebook Messenger / email).
3. The focal person **distributes to all eligible HCWs** in that facility via the same channel, alongside the **HCW one-pager**.
4. **Confirm distribution on visit day:** the visiting enumerator confirms with the focal person that the link went out (recorded against the facility).
5. **Poor-connectivity facilities:** drop **paper questionnaires** at the start of the visit day; the enumerator collects them before departure for **paper-encoder** entry through the same instrument (lands in the same store, flagged `source_path = paper_encoded`).

### 1.3 Enrollment confirmation & escalation
- **Confirmed** = focal person acknowledges receipt + distribution; recorded per facility.
- **Escalation path** when a facility hasn't engaged: enumerator → STL/field lead → ASPSI field coordinator → (if needed) the facility's DOH/LGU point of contact. A **fresh link** is reissued from the Admin Portal if the original was lost/expired.
- ⟨CONFIRM⟩ the named field coordinator + the facility-side escalation contact.

---

## 2. Reminder cadence & automation  ·  *(E5-PWA-005 / #187)*

Periodic nudges to non-respondents within the **3-day completion window** and shortly after.

### 2.1 Cadence (recommended — ⟨CONFIRM⟩ final numbers)
| When | Action | Channel | By whom |
|---|---|---|---|
| **Day 0** | Initial link + one-pager | Facility primary channel | Focal person |
| **Day 1** | Gentle reminder ("link still open, ~2 days left") | Same channel | Focal person |
| **Day 3** | Final-day reminder ("closes today") | Same channel | Focal person |
| **Day +1** (post-window) | Coverage check → trigger paper fallback for stragglers if facility coverage is low | — | ASPSI field lead |

- Keep reminders **light and non-coercive** — participation is voluntary (Privacy Plan §4); always include an **opt-out** ("reply STOP / no further reminders").
- **Stop reminding** an HCW once their submission lands (avoid nagging completers — see §3 for who's done).

### 2.2 Automation options
- **Lightweight (recommended to start):** the focal person sends templated reminders on the schedule above; ASPSI provides the message templates.
- **Assisted:** ASPSI field lead reads the **completion dashboard (§3)** each morning and pushes a per-facility "X of Y done" nudge to focal persons whose coverage lags.
- ⟨CONFIRM⟩ whether to wire an automated digest (the project already runs a GitHub-Actions → Slack UAT digest pattern that could be adapted to a daily per-facility coverage post for the field team — internal-facing, not respondent-facing).

---

## 3. HCW completion tracking  ·  *(E5-PWA-006 / #188)*

> **No separate tool to build — tracking is the Admin Portal.** "Who's done, who's pending, by facility" is read directly off the live portal:

- **HCWs tab** — enrollment registry: one row per HCW with **token state** (enrolled / submitted / revoked) and submission status. Filter by `facility_id` to see a facility's roster + who has submitted.
- **Responses tab** — every submission; filter by **facility** and **source_path** (self-admin vs paper-encoded) to count completions per facility and confirm coverage.
- **Reports → Sync Report** — submission counts aggregated by region / province / facility (snapshot coverage view).

**Daily tracking routine (ASPSI field lead):**
1. Open HCWs tab filtered by active pilot/rollout facilities → note enrolled vs submitted per facility.
2. Cross-check Responses (by facility, both source paths) for the completion count.
3. Flag facilities below the coverage target → trigger §2 reminders or §1.2 paper fallback.

⟨CONFIRM⟩ if a dedicated per-facility "% complete" widget is wanted beyond the existing tabs — that would be a small Reports enhancement, not a new system.

---

## 4. Pilot batch SOP  ·  *(E5-PWA-007 / #189; executes as #190)*

A small facility cohort proves the end-to-end F2 flow before full rollout.

### 4.1 Sample
- ⟨CONFIRM⟩ pilot cohort: recommend **3–5 facilities** spanning the connectivity range (good Wi-Fi, mobile-data-only, and one poor-signal/paper-fallback site) to exercise every path.
- Include enough HCWs to be meaningful: ⟨CONFIRM⟩ target ~⟨N⟩ HCWs total.

### 4.2 Success criteria (recommended — ⟨CONFIRM⟩ thresholds)
- **Distribution works:** every pilot facility's focal person received + distributed the link (100%).
- **Completion:** ≥ ⟨CONFIRM, e.g. 60%⟩ of invited HCWs submit within the 3-day window.
- **Data integrity:** submissions land in the store with correct facility + `source_path`; consent recorded; no malformed/blocked submissions traced to the app.
- **Paper fallback works:** at the poor-signal site, paper forms collected + encoded land correctly (`paper_encoded`).
- **No P1/P2 defects** surfaced in the pilot (use the existing UAT severity rubric + bug template).

### 4.3 Go / no-go
- **GO to full rollout** if all success criteria hold and any defects are ≤ P3 with workarounds.
- **NO-GO / iterate** if distribution, completion, integrity, or a P1/P2 defect fails → fix, then re-run a focused pilot on the failed path before scaling.
- Record the decision (date, who, evidence: dashboard counts + bug list) — this is the rollout gate of record.

---

## Issue coverage map
| Section | Field-ops issue |
|---|---|
| 1 Distribution-list | #186 (E5-PWA-004) |
| 2 Reminder cadence & automation | #187 (E5-PWA-005) |
| 3 Completion tracking | #188 (E5-PWA-006) |
| 4 Pilot batch | #189 (E5-PWA-007) — executed by #190 |

**Pending ⟨CONFIRM⟩ before rollout:** per-facility vs per-HCW link model; named field coordinator + facility escalation contacts; final reminder-cadence numbers + opt-out wording; pilot cohort size + completion/success thresholds; whether to wire the automated coverage digest. The live pilot run itself is #190.
