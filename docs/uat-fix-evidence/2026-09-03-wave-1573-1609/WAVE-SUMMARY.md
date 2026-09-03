# UAT translation wave, tranches 2+3 (#1573–#1609) — fix evidence (2026-09-03)

**Builds deployed to CSWeb 2026-09-03 ~09:40–09:44:** F1 **v5.0.3** · F3 **v7.0.5** · F4
**v4.0.5** (compile screenshots + F3 deploy-success shot in this directory; box-side zip
mtimes verified 01:40/01:42/01:44 UTC). F1 rides along because tranche 2's Bisaya Q153 fix
landed after yesterday's v5.0.2 deploy.

## Scope

37 tickets filed 2026-09-02 afternoon/evening: tranche 2 (#1573–#1594: F3 Bisaya 20, F1
Bisaya 1, F4 Cebuano 1) + tranche 3 (#1595–#1609: F3 Bisaya G/K 7, F4 Cebuano B–G 8). Same
single root cause as tranche 1: the Aug-21 import never wrote the bis/ceb question stems.

## What shipped (on top of yesterday's 384-key tranche 1)

- Tranche 2: **107 keys merged** (88 map rows: F3-bis 78, F1-bis 2, F4-ceb 8) + 7 notes
  cells. The 258-char Q18 Bisaya stem ships **verbatim** (the adversarial spot-check
  established the over-255 rule: qsf renders full text, the dcf 255 label cut is
  display-only) — **#1577 is fully fixed**.
- Tranche 3: **87 keys merged** (66 map rows: F3-bis 15, F4-ceb 51) + 6 notes cells,
  including the all-locale Q54 hold lifted for Cebuano and the Section C roster set.
- Gates clean on every apply (duplicate-label STRICT 0/0, defect sweeps clean, scan delta
  stable, bridge 0); `verify_questions` F1 323/323 · F3 377/377 · F4 335/335 on every cycle.
- Adversarial spot-checks: t2 caught + fixed a wrongly-held Q18 entry; t3 caught + fixed a
  missing `generate_qsf` rebuild (stems verified rendering post-fix). Union integrity: zero
  prior-locale clobbers across 87/87 checked keys.

## Notes per ticket class

- **#1602**: not a defect — Q62's Cebuano has been in the map since the Aug-27 import and
  shipped in v4.0.x; classified stale-build; retest on v4.0.5 after remove+re-add.
- **Cleared-source-English rows** (render English because the cleared paper does): F4 CEB
  Q39 civil status, Q46:07/:09, Q65:05/:18, Q70 Social Media/LGU rows; F1 BIS Q111/Q112
  rows. Correct renders, not misses.
- **Still held for ASPSI translators**: #1570 (F1 BIS Q75 condensation), #1568 (HIL
  option-4 stutter). Paper defects observed are listed in the wave register for the
  translator worklist.

Register: `deliverables/CSPro/automation/wave-1479-1572-register.json` (tranches 1–3).
