# F3 Hiligaynon leg fill (#1706–#1711) — fixed & deployed 2026-09-04

**Build:** F3 Patient Survey **v7.0.9** (compiled 17:35:52, deployed 17:38 MNL).
F1 (v5.0.7) and F4 (v4.0.8) untouched — `.apc` md5 verified unchanged
(`ae6f26453f37191bcc561f14b85e1d97`). Translation layer only: zero .apc/.fmf/.pff
logic changes.

## Scope — the whole leg, not six tickets

The six open Hiligaynon tickets were symptoms of one gap: the Aug-21 import never
wrote the **F3 Hiligaynon question stems**. A machine diff of the Filipino leg
against the Hiligaynon leg found **397 keys / 101 questions** missing — so this
ships the leg, not another ticket-by-ticket tranche.

**147 Hiligaynon cells + 7 notes cells** merged across five classes:

| Class | Count | What |
|---|---|---|
| A | 131 | Clean union adds — new `hil` stems/labels |
| B | 7 | Notes cells (enumerator directives) into `notes.json` |
| C | 10 | Refills of Task-40 extractor held-nulls |
| D | 4 | Q2 legacy `remove:true[bcl]` entries converted to keep-shape |
| E | 2 | Q7_SEX — retired the #1316 remove entry |
| F | 1 | **Deleted** `val:Q2_RELATIONSHIP_VS1:04` (see below) |

## The Q2 grid defect (found by the leg audit, not by a ticket)

The live Hiligaynon map carried `val:Q2_RELATIONSHIP_VS1:04` = "Iloy Tupad Balay"
— a **grid column collision** in the cleared paper that fused the *Mother* and
*Neighbor* words into the **Step-son** option slot. Removing a written map value
needs both a `keep:null` hold *and* deletion of the locale-map row (the schema
can't carry remove+keep in one entry); both were applied, so the option now
renders English rather than a wrong Hiligaynon word.

## Pipeline

classify → per-section verbatim fragment writers (157 cells supplied, **16 dropped
by audit**, 10 notes → 7 after dedup/audit) → union merge (MERGE-WITH-PRIOR: union
keep/force, never overwrite another locale, never demote force:true, never
resurrect a hold; `-f3hil` baks) → `apply_aug21.py --only F3 --fail-on-pre --apply`
(clean, **0 writes to other locales**) → gates + defect sweeps → `generate_dcf.py`
+ `generate_qsf.py` → `verify_questions.py` **PASS F1 323 / F3 377 / F4 335** →
adversarial spot-check (workflow, 157 sampled / 138 cells, **PASS-WITH-FIXES**) →
stamp v7.0.9 → compile → deploy → box zip mtime verified.

## Held for the ASPSI translator worklist — 268 items

Documented, never guessed. The bulk are admin / result-code / geography blocks the
cleared Hiligaynon source prints **English-only**, plus 17 flagged paper defects.
These render English until ASPSI supplies cleared text — an untranslated cell whose
source prints English is not a build defect.

## Retest (testers)

CSEntry → **remove** the app → **Add Application → from CSWeb** → fresh case.
The ⋮ Update menu is unreliable; a failed retest on a non-fresh build is a false
negative.
