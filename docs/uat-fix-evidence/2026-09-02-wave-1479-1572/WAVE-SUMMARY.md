# UAT translation wave #1479–#1572 — fix evidence (2026-09-02)

**Builds deployed to CSWeb 2026-09-02 (17:00 CST):** F1 **v5.0.2** · F3 **v7.0.4** · F4 **v4.0.4**
(compile screenshots + deploy-success screenshots in this directory; label-only wave — F1/F3
`.apc` md5 unchanged vs the 09-01 discipline reference, F4 label-only with verify_questions PASS).

## What this wave was

94 tester tickets filed 2026-09-02 (10:51–15:35 CST): the Bicolano/Cebuano leg of the Aug-21
translation-import gap that the 2026-09-01 register forecast — question **stems** (`item:` keys)
were never imported for BCL/CEB (plus 12 F1 BIS/HIL tickets and 1 English spec question).
One root cause per batch, all verified key-by-key against the locale maps and the cleared
paper sources.

## What shipped

- **384 override keys merged** into `aug21-overrides.json` (84 new, 300 locale-adds into
  existing entries) + **28 notes.json cells**; per-locale map rows written: F3 bcl 83 / ceb 56,
  F4 bcl 158 / ceb 10, F1 bis 18; 9 poisoned rows removed across locales.
- Recipes per the standing classes: stem keeps, split-box (one paper question → several CAPI
  boxes), battery/grid stems, glued-directive strips, WARN-force where the map held a
  different non-null value (20 predicted force pairs).
- **Gates (all clean):** duplicate-label STRICT 0/0 · defect sweep clean · scan delta no
  reason grew (1443) · `verify_questions` **F1 PASS 323/323 · F3 PASS 377/377 · F4 PASS
  335/335** (0 dead conditions, 0 bad skips).
- **Adversarial spot-check PASS:** 24/24 sampled keys character-identical to the paper
  sources; 0 English edits; carve-outs intact (Q115.1/.2 rows stay English per the accepted
  hold; parked items untouched).

## Not closed by this build

- **#1570** (F1 BIS Q75): the 426-char paper paragraph exceeds the 255-char dcf label cap —
  held null per the ILO #1333 precedent; awaits an ASPSI translator condensation.
- **#1568** (F1 HIL Q11.1): the known HIL option-4 stutter in the cleared source —
  `status:blocked`, awaits corrected HIL text.
- **#1524 / #1558 / #1560**: closed as-designed / matches-cleared-source (see their threads).

## Known renders-English-by-design after this build

Rows whose cleared paper prints English (or where map poison was removed): e.g. F3
Creatinine/Diabetes rows, BCL Q45 stem + DNR directive, Q18 bracket rows, Q148 rows
01/02/05/16/17. These are correct renders of the cleared source, not misses.

Provenance: classification + fixes by staged agent workflows with adversarial verification
(register: `deliverables/CSPro/automation/wave-1479-1572-register.json`); merged, rebuilt,
regenerated and gate-checked 2026-09-02.
