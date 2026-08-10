# CAPI UAT Round 6 — Close-out

**Date:** 2026-07-14 · **Round window:** 2026-06-30 → 07-05 *(target; gated on ASPSI importing the CSWeb tester accounts)* · **Surface:** Supervisor & Enumerator Hub (`LoginApp` → `MenuApp`) · **Build:** HUB v1.0.1 (2026-07-03) · **Label:** `from-uat-round-6-2026-06` · **Tracking:** #807

> ## ⏳ VERDICT: PENDING FINAL SWEEP
>
> Everything below is settled **except the last line**. R6 closes the moment the pretest
> sweep comes back clean — real field credentials → download the assigned EA → open a
> case → sync it through, run on the **cleaned database with the real accounts**.
>
> That sweep is R6's exit evidence and the pretest's version lock-in, in one pass.
> Flip the verdict to **CLOSED** and close #807 + #831 when it lands.

## Why this round was still open

Not because work was outstanding. **All 27 R6 findings are closed `completed`** — zero parked as `not planned`, zero deferred. The tracking issue's "Open findings" list is empty. The round stayed open because its exit gate (ASPSI importing the CSWeb tester accounts) slipped, and nobody ran the closeout afterward.

Unlike F1/F3/F4 — which have a tooling-enforced field-readiness gate (`check_field_ready.py`, green as of 2026-07-14) — **the Hub has never had an equivalent sign-off.** R6 *is* that sign-off. This note is it.

## What R6 tested

- **Login → role-filtered menu** — supervisor vs enumerator render the correct grouped menu.
- **Conduct F1/F3/F4 from the menu** + back-to-menu (`OnExit` return).
- **Bluetooth choreography** (2-tablet, supervisor + enumerator pair):
  - Supervisor **Assign Enumeration Area** → enumerator **Receive Assigned Data**
  - Enumerator **Send My Interviews to Supervisor** → supervisor **Collect Interviews from Enumerators** (host accumulates by 12-digit key, non-destructive)
- **Relay Collected Interviews to CSWeb** (supervisor → server).
- **Live coverage reports** (View my report / Survey report — real per-instrument counts).
- **Offline EA map** (View EA on Map — works with no signal).

Teams under test: 8 accounts across 2 teams, with Aidan (`fs-01`) and Ms. Marriz (`fs-02`) each holding dual roles on **opposite** teams so neither supervised themselves.

## The two open issues, dispositioned

**#807 — the R6 tracking issue itself.** Closes with this note.

**#831 — "F2 — Removal of one response in the Admin Portal."** **Not a Hub defect, and not a defect at all.** Shan filed it as *"Pass with comment"* on 2026-07-02: a test response submitted 2026-07-03 10:44 AM at facility `DEMO-FAC-RHU-QC-1` was encoded with a token in the HCW ID field — her words: *"This is a human error."* She asked for the row to be removed.

It is **resolved by the pretest database cleanup** (`deliverables/CSWeb/pretest-cleanup-2026-07-14.sql`, §3), which deletes all 41 F2 test responses — that row included. No code change, no fix; the request is satisfied by the clean-start purge. Close it against the cleanup.

## Exit criterion

Mirrors R5's, adapted to the Hub:

1. **Zero open R6-labeled issues** — every tester finding fixed-and-deployed or explicitly dispositioned. ✅ (27/27 completed; #831 dispositioned above)
2. **No new tester-blocking finding** since the last deploy cycle. ✅ (no Hub findings since 2026-07-03)
3. **Final sweep passes on the clean database with real field credentials.** ⏳ **← the one open item**

## Caveat — reopen triggers

"0 open" ≠ "every path tester-verified." R6 reopens on:

- **Stale-build false negatives** — CSEntry's "Update Installed Applications" can miss a CSWeb redeploy. The reliable update path is **remove + re-add**. A desk-test failure on a *confirmed-fresh* build is a genuine reopen trigger; one on a stale build is not.
- **Hub redeploy after the identity change** — if Aidan's final list renames or replaces the `se-*`/`fs-*` accounts, the Bluetooth roster binds to those usernames and the Hub package **must be redeployed** before the field can pull assignments. A redeploy invalidates this sweep; re-run it.

## Field posture — the Hub is not a single point of failure

Bluetooth assignment distribution is the **convenience** path. The **reliable** path is the printed assignment sheets — `generate_assignments.py` says so in its own docs: *"assignment-sheets.html → print; hand each enumerator their page (type the keys)."*

If Bluetooth misbehaves at Mayondon or either facility, enumerators type their 12-digit keys off paper and the pretest proceeds. The Hub failing degrades convenience, not data collection.

## Round state going into the pretest

| Round | Surface | State |
|---|---|---|
| R5 | F1 / F3 / F4 instruments | **CLOSED** 2026-06-29 (79 issues) |
| **R6** | **Supervisor & Enumerator Hub** | **⏳ pending final sweep** |
| P5 re-enroll (#836) | F2 HCW — post-migration | **OPEN, not started** — Thursday's item |

Closing R6 leaves **one** open round (P5/F2) going into the field, instead of three.
