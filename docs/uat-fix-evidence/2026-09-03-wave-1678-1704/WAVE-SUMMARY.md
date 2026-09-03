# UAT translation wave — tranche 7 (#1678–#1704) — fixed & deployed 2026-09-03

**Builds:** F4 Household Survey **v4.0.7** (deployed 18:13 MNL) · F3 Patient Survey
**v7.0.7** (deployed 18:14 MNL). F1 untouched (stays v5.0.5, verified byte-identical).

## Scope — 27 tickets
The F4 **Waray** leg (24 tickets — a near ticket-for-ticket mirror of tranche 4's Bisaya
sweep: Sections B/C/D/G/I/K/M/N/P/Q, same Aug-21 import stem-gap root cause) and the first
3 F3 **Hiligaynon** tickets (#1701, #1703, #1704 — Section B). Unlike the Bisaya print,
the Waray paper genuinely translates Q78 and the Q142 payment grid — **all 27 tickets got
build fixes; zero cleared-English closures.** Translation layer only — zero
.apc/.fmf/.pff changes.

## Pipeline
classify (27, keyed off the tranche-4 recipe map) → verbatim fragment (185 F4-WAR +
7 F3-HIL cells + 11 notes, 8 new keys; ticket images + paper dumps, machine-checked) →
union merge via `merge_t7.py` (zero merge anomalies; 24 sanctioned held-null/poisoned-map
replacements; `-t7` baks; F1 hash-verified untouched) → apply F4+F3 + gates (scan totals
steady at 1443, nothing grew) → generate_dcf + generate_qsf → verify_questions **PASS
F1 323 / F3 377 / F4 335** → adversarial spot-check (**232 samples, straight PASS —
zero defects introduced; all 192 values verbatim-verified**) → stamp → compile
(F4 18:12:01, F3 18:13:40) → deploy → box zip mtimes verified.

## Held for translator rulings (14 items, flagged — never guessed)
The Waray print carries several defects the build must not import: the Q65:03
"Highboold" duplicate, a Cebuano-contaminated Q46:06 row, Section N period-label
mismatches ("past month" printed under week/6-month/12-month columns), a duplicated
Q202:01 translation, the omitted Q29 socio-economic block, and CAPI-only OTHER_TXT
labels with no paper analog. These render English (or hold their prior state) until
ASPSI supplies cleared text; itemized on the tracking issues.

## Retest (testers)
CSEntry → **remove** the app → **Add Application → from CSWeb** → fresh case.
