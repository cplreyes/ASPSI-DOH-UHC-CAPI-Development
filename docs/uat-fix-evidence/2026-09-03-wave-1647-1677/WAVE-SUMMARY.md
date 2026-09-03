# UAT translation wave — tranche 6 (#1647–#1677) — fixed & deployed 2026-09-03

**Builds:** F3 Patient Survey **v7.0.6** (deployed 16:47 MNL) · F1 Facility Head Survey
**v5.0.5** (deployed 16:49 MNL). F4 untouched (stays v4.0.6, verified byte-identical).

## Scope — 31 tickets
The first F3 **Waray** leg (25 tickets, Sections B–K: the same Aug-21 import stem-gap root
cause as every prior locale leg, plus WARN-force replacements of poisoned June map values —
doubled spans, glued directives, orphan glyphs, grid contamination), 3 more F1 **Waray**
(#1647–#1649: Q86, Q107, Q143 — the exact keys the tranche-4 machine-diff pre-empted), and
the first 3 F1 **Hiligaynon** (#1655, #1659, #1663). Translation layer only — zero
.apc/.fmf/.pff changes.

## Pipeline
classify (31) → verbatim fragment (139 entry keys + 7 notes cells, 40 new override keys;
ticket images + paper dumps, machine-checked containment) → union merge with 19 legacy
shape conversions + 35 sanctioned WARN-force replacements (`-t6` baks; first merge attempt
rolled back byte-identical after a script sentinel bug, re-run clean) → apply F3+F1 + gates
(scan totals 1482→1443) → generate_dcf + generate_qsf → verify_questions **PASS
F1 323 / F3 377 / F4 335** → adversarial spot-check (**all 139 entries, 3 verification
layers, PASS-WITH-FIXES** — sole defect was stale register bookkeeping) → stamp → compile
(F3 16:46:59, F1 16:48:43) → deploy (both succeeded) → box zip mtimes verified.

## Not-in-build (by design)
- **#1660 (Q109), #1661 (Q112), #1664 (Q121), #1674 (Q92 stem):** the cleared Waray paper
  prints these stems in English → translator worklist; retest riders only.
- **Held pending rulings** (flagged, never guessed): Q1142 amount-row composition,
  Q1141/Q1142 OTHER_TXT labels (no paper analog), Q92 amount-tail composition,
  READ_ONE:WAR wording (paper prints two variants), intro:131 fill-token style, Q147
  list directive routing.
- Standing carve-outs unchanged; Q115.1/.2 hold respected; over-255 WAR Q18 (296 chars)
  imports verbatim and renders full on-device.

## Retest (testers)
CSEntry → **remove** the app → **Add Application → from CSWeb** → fresh case.
