---
type: deliverable
kind: weekly-status-template
audience: internal (Carl + project record)
sender: Carl Patrick L. Reyes
related_task: E0-010
status: stable
version: 1.0
formalized: 2026-05-04
tags: [weekly-status, internal, e0-010, e0-011]
---

# Weekly Status — Template (Internal) · v1.0

> Reusable format for the weekly internal status snapshot, owned by Carl (Data Programmer). **Internal-only** — not sent to ASPSI Mgmt Committee or DOH. Cadence: one snapshot per ASPSI Sprint week, written EOD Friday at sprint close. Each instance is saved as `weekly-status-YYYY-MM-DD.md` in this same folder.
>
> **Purpose:** consolidate the week into a single artifact that survives between standups and the next sprint plan. Useful inputs: future retro Q&A, periodic ad-hoc updates if Mgmt asks, narrative continuity if Carl needs to brief someone fast. Not a comms send.
>
> **Stability:** v1.0 locked 2026-05-04 (Sprint 004 Day 1 — E0-010 closed). The week-1 instance at `weekly-status-2026-05-01.md` proved the structure end-to-end. Bump version + record changes here if the structure later evolves.

## Conventions

- **Internal voice:** plain, direct, declarative. No "po" / "Ma'am" / "Sir" — this is a self-facing artifact. Code-level detail (PR numbers, SHAs, bug IDs) is fine and sometimes useful for the future-Carl reader; abstraction lives at the layer that's actually informative.
- **Length target:** ≤1 screen of body (~250–500 words). The artifact's value is being scannable a month later, not exhaustive.
- **Anchor on quality and deliverables, not payment deadlines** — surface tranche / deadline exposure as a *risk*, not as the framing. (Memory: `feedback_quality_over_deadline`.)
- **Stay in Carl's lane:** describe ASPSI-side actions and Carl's own work. Do NOT frame items as DOH-facing routing tasks; that's a different lane. (Memory: `feedback_comms_lane_discipline`.)
- **Open items section captures decisions still owed** — to Carl, to ASPSI, to DOH. Lists who-owes-what so future-Carl can pick the thread up cold.

---

## Snapshot scaffold

**Week of:** Mon YYYY-MM-DD → Fri YYYY-MM-DD (Sprint NNN)
**Author:** Carl Patrick L. Reyes
**Status:** internal artifact, not sent

### Headline

*[1–2 sentences on the most consequential thing this week. Anchor on deliverable progress or a decision that landed. If a critical risk shifted, lead with that instead.]*

### Closed this week

- *[Deliverable-level bullet — what's now done that wasn't last week. Cite the workstream epic / instrument / PR when useful.]*
- *[…]*

### In flight (next week)

- *[Top 3–5 active items, each with the responsible role and a target close. Carry-forwards from this sprint + planned next-sprint commits.]*
- *[…]*

### Open items / decisions owed

- *[Decisions that haven't landed and the owner. E.g., "Tablet procurement tier — owner: ASPSI Mgmt; ask sent 2026-04-29." OR "F2 burnout reduction-vs-removal confirmation — owner: ASPSI internal review." OR "Tranche 2 official revised deadline — owner: DOH-PMSMD, surfaced via ASPSI."]*
- *[If none: "No open decisions blocking next sprint."]*

### Risks on the watchlist

- *[1–3 material risks. One-sentence mitigation status each. Cull anything that's already absorbed or stale.]*
- *[…]*

### Deliverable production state (informational)

*[1–2 sentences on the production-side state of CAPI deliverables under D1–D6 / Tranches 1–4. Framing: "what's submission-ready on our side" + "what's pending external". Out-of-scope items (tranche acceptance + submission timing) stay informational only per `feedback_tranche_tracking_out_of_scope.md` — no active tracking, no recommendations to chase deadlines.]*

---

## Drafter notes

- Pull source material from `scrum/sprint-current.md` (committed items + status), `scrum/product-backlog.md` § Status at a Glance, the Friday standup, and `log.md` tail. The standup's "Yesterday (Done)" + sprint board snapshot is usually 80% of "Closed this week"; `log.md` adds the inter-sprint and weekend bookkeeping the standup might miss.
- For "In flight", reuse the next sprint's likely shape (carry-forwards from this sprint + planned next-sprint commits). If next sprint isn't planned yet, lead with the carry-forwards.
- For "Open items", scan epic files for items still tagged blocked or with external owners. Don't manufacture entries.
- For "Risks", default to the existing watchlist in `product-backlog.md` (Risks & Watchlist section).
- If the snapshot turns into a Mgmt-facing send later (template was originally drafted for that), the conversion is mechanical — add a `To:` block, soften the voice, drop code-level detail. The information itself transfers cleanly.
