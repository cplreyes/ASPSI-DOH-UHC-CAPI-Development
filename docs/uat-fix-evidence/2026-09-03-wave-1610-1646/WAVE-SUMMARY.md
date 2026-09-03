# UAT translation wave — tranches 4+5 (#1610–#1646) — fixed & deployed 2026-09-03

**Builds:** F4 Household Survey **v4.0.6** (deployed 16:06 MNL) · F1 Facility Head Survey **v5.0.4** (deployed 16:08 MNL). F3 untouched (stays v7.0.5).

## Scope — 37 tickets, one root cause
The Aug-21 translation import never wrote the question **stems** for the F4 **Bisaya** leg
(24 tickets, #1610–#1639 bis + #1643), plus 7 genuine F4 **Cebuano** continuations into
Sections I/K/M/N, and 6 F1 **Waray** tickets (#1640–#1642, #1644–#1646) on the known
all-locale extract-miss / override-carried keys. Fixes are translation-layer only —
**zero .apc/.fmf logic changes; byte-identical discipline held.**

## Pipeline
classify (34+3 issues) → verbatim fragment (268 entry keys + 29 notes cells; ticket-image
transcription for held-null refills, paper dumps otherwise, machine-checked containment) →
union merge (`-t4` baks; 0 conflicts, 0 force demotions, 0 locale collateral) →
apply_aug21 F4+F1 + gates (scan totals improved 1482→1443) → generate_dcf +
generate_qsf → verify_questions **PASS F1 323 / F3 377 / F4 335** → adversarial
spot-check (**120 samples, PASS-WITH-FIXES**) → stamp → Designer compile
(F4 16:04:22, F1 16:07:02 — shots attached) → auto_deploy (both "deploy succeeded" —
shots attached) → box zip mtimes verified.

## Spot-check fixes folded in before ship
1. **F1 `generate_qsf.py` now builds the dictionary in memory** (F3/F4 parity) — the qsf
   was previously rendered from the 255-capped .dcf, truncating long stems on-device.
   Heals the 520-char WAR Q75 (#1646) plus 5 pre-existing capped stems (Q75 fil/bcl/ceb/hil,
   Q45_PERF_INDICATORS bis).
2. F4 `val:Q65_CONDITIONS_VS1:09` — bis unioned into the remove ruling (renders English
   "Diabetes" like all locales, ILO/FIL/BCL/CEB precedent).
3. F4 `val:Q65_CONDITIONS_VS1:03` — poisoned June "bakuna" row removed + bis hold
   (renders English "Immunization"; BIS paper's "Pagpabakuna" flagged for committee).

## Not-in-build (by design)
- **#1624 (BIS Q90), #1622 (BIS Q78 stem):** the cleared Bisaya paper prints English —
  routed to the ASPSI translator worklist (cleared-source-prints-English rule).
- **#1637 (BIS Q186):** stem already translated and deployed since Sep-01 — intro:186
  notes cells added for six locales; stale-build retest advised (remove + re-add).
- **CEB Q142 battery:** held — the cleared Cebuano paper prints that grid English-only.
- Standing carve-outs still render English by ruling: F4 Q65:03/:09, Q70:06, Q45_2:02/:03;
  F1 Q45_PERF_INDICATORS_VS1:04 (fil-scoped).
- Known cosmetic residue pending a `notes_lookup` instrument-precedence ruling: two F4
  Bisaya helper/directive lines render F3's cleared June wording instead of the Aug-21
  print (#1611/#1619 directive cells — values stored, shadowed cross-instrument).

## Retest (testers)
CSEntry → **remove** the app → **Add Application → from CSWeb** (re-download) → fresh case.
The ⋮ Update menu is unreliable; a failed retest on a non-fresh build is a false negative.
