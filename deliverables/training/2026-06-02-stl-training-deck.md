---
type: deliverable
kind: training-deck
audience: Survey Team Leaders (STLs)
prepared_by: Carl Patrick L. Reyes
date_drafted: 2026-06-02
status: draft-for-review
related_task: E7-TRAIN-002
companion_to:
  - training/2026-06-02-capi-enumerator-training-deck.md
  - Survey-Manual/CAPI-PWA-Stakeholder-Section_2026-05-02.md
tags: [training, capi, stl, sync, field-replacement, end-of-day-review, e7]
---

# STL Training Deck — Sync, Field Replacement & End-of-Day Review

> **How to use this file.** Each `---`-separated block is one slide; the **Slide** line is the title, bullets are on-screen, *Facilitator notes* are spoken. Render with Marp / `pandoc -t pptx` / Google Slides. `[Screenshot slot: …]` is filled once the CSWeb dashboard + F1/F3/F4 apps are live for the project.
>
> **Audience:** STLs, who supervise enumerators (SEs) within a cluster. **Assumes** STLs have already taken the enumerator CAPI walkthrough — this deck is the *supervision* layer on top of it. **Duration:** ~half-day.

---

### Slide 1 — Title

**UHC Survey Year 2 — Survey Team Leader Training**
Questionnaire numbers · End-of-day review · Sync verification · Field replacement

ASPSI CAPI Team · DOH UHC Survey Year 2

*Facilitator notes:* The STL is the hinge between the field and the data team. Most data quality and data-loss risk is managed at the STL level — this deck is about those controls.

---

### Slide 2 — Your job in one line

> **You make sure every eligible interview is captured correctly, accounted for, and on the server by 10 PM — and that no data is lost when a tablet breaks.**

- You don't enter data; you **assure** it.
- You own the **questionnaire-number ranges**, the **end-of-day review**, and the **field-replacement** protocol.
- You are the **first escalation point** for your SEs.

*Facilitator notes:* Anchor the whole session on these three owned processes. Everything else supports them.

---

### Slide 3 — Where you sit in the pipeline

| Role | Contribution |
|---|---|
| ASPSI CAPI team | Build apps, provision tablets, resolve technical issues |
| Cluster supervising RA | Cluster oversight; daily dashboard reconciliation |
| **You — STL** | **Pre-assign Q-numbers; supervise SEs; check cases before sync; reconcile flags vs diaries** |
| Survey Enumerators (SEs) | Conduct interviews; sync daily before 10 PM |
| Data manager | Approved/On-Hold review; logic checks ≥2×/week |

*Facilitator notes:* Headcount frame: ~6 supervising RAs, 20 field supervisors, 100 SEs. You sit directly above your team of SEs.

---

### Slide 4 — Process 1: Questionnaire numbers

- You **pre-assign questionnaire-number ranges** to each SE *before* fieldwork starts.
- Ranges must **not overlap** between SEs — overlapping IDs cause case collisions on the server.
- SEs enter the number you assigned at case start — they don't invent one.
- Keep a written assignment log (SE ↔ range ↔ instrument) you can reconcile against.

[Screenshot slot: example questionnaire-number assignment log]

*Facilitator notes:* This is the single most common cause of avoidable data problems. Walk through allocating ranges for a 5-SE team live.

---

### Slide 5 — Process 2: End-of-day review (before sync)

Each evening, before your SEs sync, do a completeness pass:

- Every **expected** case for the day exists on the tablet.
- Cases are **accepted** (in the completed list), not stuck in-progress.
- **Verification photo** present and usable for each case.
- **GPS** captured (no obvious zero/blank coordinates).
- Disposition codes make sense (refusals, ineligibles, partials logged correctly).

Then have the SE **sync** while you confirm the result.

*Facilitator notes:* "Accepted, photo, GPS, disposition" is the four-point checklist. An un-accepted case will not sync — catch it now, not next morning.

---

### Slide 6 — Process 3: Sync verification

- SE taps **↻** → waits for **"Sync successful"** (app stays open during sync).
- **Daily deadline: before 10 PM**, so ASPSI sees yesterday's cases next morning.
- You confirm each SE's sync landed:
  - **Next morning**, check the **CSWeb dashboard** completed-case count against your day's expected count + your assignment log.
  - Each case is tagged with **source tablet, sync timestamp, enumerator identity** — use these to reconcile.
- Mismatch → investigate before the team moves on.

[Screenshot slot: CSWeb project dashboard — completed counts by enumerator]

*Facilitator notes:* The dashboard is your reconciliation tool. Teach the habit: expected (from diary + log) vs landed (dashboard). Gaps are either un-synced tablets or un-accepted cases.

---

### Slide 7 — When a sync fails

1. Confirm **connectivity** (Wi-Fi / mobile data actually working).
2. **Retry once.**
3. Still failing → **escalate to the ASPSI CAPI team** — do not reinstall or delete anything.
4. Reassure the SE: **completed cases remain on the tablet** and will sync once resolved. **No data is lost.**
5. Log the un-synced tablet and follow up next connectivity window.

*Facilitator notes:* The instinct to "fix" by deleting/reinstalling is the real risk. Your message to SEs: stop, escalate, data is safe.

---

### Slide 8 — Process 4: Field replacement protocol

When a tablet is **lost, stolen, broken, or unresponsive:**

- **Report immediately** up the chain; the CAPI team can **revoke that device's sync access** without affecting already-uploaded data.
- Issue a **spare tablet** (pre-imaged, in the cluster kit) and **re-assign the SE's remaining Q-number range** to the new device.
- **In-flight (un-synced) cases on a dead tablet:** if the device can still power on, attempt one sync first. If it cannot, those un-synced cases are **at risk** — log exactly which case IDs were affected so the data manager knows what to expect (or to re-collect).
- Update your assignment log: SE ↔ **new** device ID.

[Screenshot slot: spare-tablet issue / device-swap log]

*Facilitator notes:* The key distinction: **synced** cases are safe on the server regardless of the tablet's fate; **un-synced** cases die with an unrecoverable device. This is *why* the 10 PM daily sync rule exists. Make this connection explicit.

---

### Slide 9 — Lost or stolen tablet (security)

- Treat as a potential **data + privacy incident**, not just a hardware loss.
- Report immediately → CAPI team **revokes sync access / remote-wipes** the device.
- Note any **un-synced cases** that may have been on it (data-loss assessment).
- The device held respondent data — escalate per the incident chain so privacy obligations (NDU, RA 10173) are met.

*Facilitator notes:* Tie to the Data Privacy & Security Plan incident process. "A lost tablet is a privacy event" — don't sit on it.

---

### Slide 10 — Handling On-Hold returns

- The data manager classifies each case **Approved** or **On-Hold**.
- **On-Hold** cases come back with a note on what needs review.
- You route the case to the right SE, who **amends and re-submits**; it re-enters the review queue.
- Track On-Hold turnaround — agreed window — so corrections don't pile up at fieldwork close.

*Facilitator notes:* On-Hold is normal and recoverable. Your role: fast routing + closing the loop, not letting returns stagnate.

---

### Slide 11 — Daily diary reconciliation

- SEs keep a **daily diary** of visits/attempts.
- You cross-reference the diary against the **dashboard** and the **flagged-case list** from the data manager.
- Discrepancies (a diary visit with no landed case; a flagged case with no diary entry) get investigated; persistent issues → respondent re-contact under the same consent procedures.

*Facilitator notes:* The diary is the ground truth of effort; the dashboard is the ground truth of captured data. Reconciling the two catches both data loss and protocol drift.

---

### Slide 12 — Data security responsibilities

- Everyone on your team has signed the **NDU** — enforce it.
- One SE ↔ one assigned tablet, **signed for**; no sharing of devices/logins.
- No respondent data leaves the device/server; no manual file deletion.
- Track every device in your cluster; **all tablets returned to ASPSI at close**.
- ASPSI is NPC-registered (**PIC-000-358-2021**) with appointed DPOs — confidentiality is contractual.

*Facilitator notes:* The STL is the local custodian of both devices and confidentiality. Device inventory discipline now prevents a turnover headache later.

---

### Slide 13 — Your daily rhythm (summary)

**Morning:** reconcile yesterday's dashboard vs log/diary; resolve gaps; distribute On-Hold returns.
**During the day:** support SEs; field any escalations; manage spares.
**Evening:** four-point end-of-day review per SE → confirm sync **before 10 PM** → log any failures/swaps.

*Facilitator notes:* Give them this as a printed daily checklist card. Repetition of the rhythm is what keeps a cluster clean.

---

### Slide 14 — Escalation ladder

- **SE technical/data issue →** you (STL) first.
- **Can't resolve / app or sync fault →** ASPSI **CAPI team**.
- **Lost-stolen device / privacy event →** report up immediately (incident chain).
- **Suspicious data / protocol concern →** supervising RA + data manager.

*Facilitator notes:* "STL first, then CAPI team" for tech; privacy events jump straight up. Fill in the actual contact names/Viber group on the contact card before deployment.

---

### Slide 15 — Wrap-up & checkout

- You can allocate non-overlapping **Q-number ranges**.
- You can run the **four-point end-of-day review** and **verify sync** on the dashboard.
- You can execute a **tablet swap** without losing accounted data — and you know which cases are at risk when you can't.
- You know your **escalation ladder** and your **security duties**.

*Facilitator notes:* Checkout activity: simulate a broken-tablet swap (revoke → spare → range re-assign → log) and a dashboard-vs-log reconciliation with a deliberate gap.

---

### Appendix A — STL daily checklist (printable)

- [ ] AM: dashboard count = expected (log + diary)? gaps resolved?
- [ ] AM: On-Hold returns routed to SEs.
- [ ] PM: per SE — all expected cases present & **accepted**.
- [ ] PM: per case — photo + GPS + sensible disposition.
- [ ] PM: each SE **synced & confirmed before 10 PM**.
- [ ] PM: any sync failure / device swap logged + escalated.

### Appendix B — Pending before main fieldwork

- Real **CSWeb dashboard screenshots** + the project **server name/URL**.
- Confirmed **escalation contacts** (CAPI team, supervising RA, incident chain).
- Final **device-inventory / assignment-log templates** for the cluster kit.
