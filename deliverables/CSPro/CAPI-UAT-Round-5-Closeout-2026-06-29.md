# CAPI UAT Round 5 — Close-out

**Date:** 2026-06-29 · **Round window:** 2026-06-22 → 06-27 · **Instruments:** F1 (Facility Head), F3 (Patient), F4 (Household), on-device via CSEntry/CSWeb · **Label:** `from-uat-round-5-2026-06`

## Verdict: CLOSED

All **79** R5-labeled issues are resolved — **0 open**. Breakdown: **78 fixed-and-deployed** (closed `completed`) + **1 deferred** (closed `not planned`). R5 issues were created 2026-06-21 → 06-26 and all closed by **2026-06-27**; the board has stood at zero since. The round is **declared closed as of 2026-06-29**.

## Exit criterion (operationalized here)

R5 is closed on this basis — the field-readiness exit the Sprint 012 `E0-UAT-REFRAME` item called for:

1. **Zero open R5-labeled issues** — every tester finding is either fixed-and-deployed or explicitly dispositioned.
2. **No new tester-blocking finding** since the last deploy cycle — the `capi-uat-triage` loop ran multiple quiet cycles with no new actionable tester activity (last new urgent was #617, resolved).
3. **ASPSI-owned items carved out** — translations and spec/structural decisions are ASPSI's to resolve; they do not block the R5 close and are tracked separately (see *Parked to ASPSI* below).

> Wiring this exit into the triage loop's **automatic stop-condition** remains a separate tooling to-do (the second half of `E0-UAT-REFRAME`). This note operationalizes the criterion and applies it manually for R5.

## What shipped (R5)

- F3/F4 skip-logic fixes + `select_all`→checkbox conversions, roster corrections, Section K/L/M/N batches.
- **F4 Section-N #617 urgent** — protected subtotal going `NOTAPPL` on a blank panel amount blocked the interview; fixed by coalescing blank amounts to 0 across all four panels (Q157/177/182/185).
- **PhilHealth reinstatement** built + deployed during R5: F3 Q38.1/Q38.2 (#764), F4 Q45.1 (#794) / Q45.2 (#795) — CSWeb 06-25/27. ASPSI supplied the value sets via the tickets.
- Full per-deploy log: `deliverables/CSPro/automation/triage-state.json`.

## The 1 deferred item

- **#728 — Geographic Identification (F1–F4)** — closed `not planned`. Cosmetic CSEntry render artifact: the letter after a multi-byte ñ is uppercased on screen (e.g. "Biñan" → "BiñAn"). **Data is stored correctly — display-only.** Not generator-fixable; accepted as cosmetic.

## Caveat — reopen triggers

"0 open" ≠ "every path tester-verified." An R5 issue can reopen on:

- **Stale-build false negatives** — CSEntry's "Update Installed Applications" can miss a CSWeb redeploy; the fix is **remove + re-add** (this already caused a transient #617 reopen). A desk-test failure on a *confirmed-fresh* build is the reopen trigger.

## Parked to ASPSI (not part of the R5 close; tracked separately)

- **Translations** — Filipino/Tagalog + Ilocano/Hiligaynon fallbacks. The language switcher is built; English-only by design until ASPSI delivers strings. Master lists in tracking epics **#369** (F3) / **#370** (F4).
- **F4 Section-C structural cluster** — numbering, reorder, name-piping, education classification, in-law options — need ASPSI spec (#525/#602/#608/#610/#612/#613/#614).
- **Spec / design decisions** — surfaced in `deliverables/CSPro/ASPSI-GO-NOGO-2026-06-27.md` (B-items) + `deliverables/CSPro/CAPI-Logic-Open-Items-for-ASPSI.md`.

None of the parked items block the instruments from running on-device.

## Next

- **Pretest is ASPSI-scheduled** (SJREB clearance + tablets + field logistics). Carl's lane ends at field-ready. The R5 close confirms F1/F3/F4 are **field-ready** pending only the ASPSI-owned decisions above — then the deliverable chain (D4 → D5 → D6) resumes to engagement close.

---
*Generated 2026-06-29 from the GitHub R5 label (`from-uat-round-5-2026-06`, 79 issues) + `triage-state.json` + the 2026-06-27 readiness / go-no-go notes.*
