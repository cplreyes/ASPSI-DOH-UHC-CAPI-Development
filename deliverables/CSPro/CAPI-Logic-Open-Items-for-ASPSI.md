# CAPI Logic — Open Items for ASPSI Clarification

**Date:** 2026-06-09 · **Instruments:** F3 Patient Survey, F4 Household Survey
**Why this exists:** while completing the F3/F4 CAPI skip/validation logic, four items
could not be finalized because the **reviewed spec and the built data dictionary
disagree**, or the spec explicitly routes a question to ASPSI. Each is stated with the
exact conflict and a **recommended default** — confirming the default (or correcting it)
unblocks the build. None require DOH input; these are instrument-design calls.

Everything else from the desk-test pass is done (case-key fix, consent terminators,
skip logic, other-specify enforcement, select-all "≥1 ticked", Section N subtotals).

---

## 1. F3 — Q113 → Q114.1 skip (PhilHealth already availed)

- **Spec (Skip-Logic G–I, line 470):** if `Q113_PAY_08` (Hospital bill paid via PhilHealth)
  = Yes, **skip Q114** (the "why did you NOT avail PhilHealth" question) and go to **Q114.1**.
- **Dictionary shows:** there is **no `Q114_*` field**. The only Q114-area items are
  `Q1141_*` (Q114.1 "other items in the bill") and `Q1142_*` (Q114.2). The "why-not-availed
  PhilHealth" question (Q114) does not exist in the dcf.
- **Question:** Was Q114 ("why not availed PhilHealth") intentionally dropped, or is it
  missing from the dictionary? If it exists under another name, what is it?
- **Recommended default (pending answer):** treat Q114 as not present; **no skip rule needed**
  (Q113 already flows into Q1141). If Q114 should exist, ASPSI to provide its item name + codes
  and we add `Q113_PAY_08 = 1 → skip to Q1141_1`.

## 2. F4 — Q23 water-source branch (which codes open Q24 vs Q25)

- **Spec (Skip-Logic Section B + §3.3):** `Q24_FAUCET_SHARE` is asked for *piped/faucet*
  sources; `Q25_TUBE_SHARE` for *dug well / tube well / spring* sources.
- **Dictionary shows `Q23_WATER_SOURCE` has only 4 codes**, which don't match those five
  spec categories:
  `1 = Faucet inside the house` · `2 = Tubed/piped well` · `3 = Dug well` · `4 = Other (specify)`.
- **Question:** Map the 4 dcf codes to the two follow-ups. Specifically:
  - Which code(s) should enable **Q24 (faucet-share)** — `1` only, or `1` and `2`?
  - Which code(s) should enable **Q25 (tube-share)** — `2` and `3`, or `3` only?
- **Recommended default (pending answer):** `Q24` enabled when `Q23 = 1` (faucet inside);
  `Q25` enabled when `Q23 in 2, 3` (tubed/piped or dug well); `Q23 = 4` (Other) skips both.
  Confirm or correct, and we wire the two gate skips.

## 3. F4 — Max-roster "unusual size" soft warning (#168, second half)

- **Status:** roster count vs `Q19_HH_SIZE_TOTAL` reconciliation is implemented (errmsg when
  they differ). The spec also mentions a **soft warning at "unusual" household sizes**, but no
  threshold is given. `Q19_HH_SIZE_TOTAL > 10` already triggers a soft "unusually large" warning.
- **Question:** Is a separate roster-size soft warning needed beyond the existing `Q19 > 10`
  one, and if so at what member count (e.g. > 12, > 15)?
- **Recommended default (pending answer):** none — the existing `Q19 > 10` soft warning covers
  it; no second threshold. Confirm, or give the count and we add it.

## 4. F4 — Section J (Health-Seeking) per-member loop (#166)

- **Spec (§996, already routed to ASPSI):** the Apr-20 source says Section J "loops over
  household members." The dcf currently treats Section J as **respondent-level** (`maximum: 1`,
  closed-by-design 2026-04-21), matching the singular "you/your household member" phrasing.
- **Question:** Does Section J ask the health-seeking items **per household member** (repeating,
  like the roster) or **once for the respondent**?
- **Recommended default (pending answer):** keep **respondent-level** (current build). If it must
  be per-member, this is a dictionary/roster restructure (re-derive Section J as a repeating
  group keyed to the roster) — flag the rework scope before we proceed.

---

### Not blocked on ASPSI (we will encode from the existing spec; listed for awareness)
- **Select-all exclusive-option rules** ("I don't know" / "None" / "There are no benefits"
  cannot be combined with other options). The spec lists the exact exclusive code per group
  (F3 §3.5–3.14); we will encode those from the spec (auto-detecting them by label proved
  unreliable, so we use the spec's explicit codes).
- **Per-item numeric range + cross-field validations** (~80 rules across F3 §3.5–3.14 and the
  F4 equivalents). Fully specified — next implementation batch, no ASPSI input needed.
