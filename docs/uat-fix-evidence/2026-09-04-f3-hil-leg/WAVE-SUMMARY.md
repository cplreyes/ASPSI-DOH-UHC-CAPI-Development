# F3 Hiligaynon leg fill (#1706–#1711) — fixed & deployed 2026-09-04

**Build:** F3 Patient Survey **v7.0.10** (compiled 17:48:54, deployed 17:52 MNL).
v7.0.9 shipped the leg fill at 17:38; v7.0.10 adds two extraction defects found by the
post-deploy verification sweep (below).
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

## Two further extraction defects — found by the post-deploy sweep, fixed in v7.0.10

Verifying #1709's coverage surfaced a defect the ticket didn't name, so the leg got a
machine sweep for the same signature (a question number starting mid-string followed by
an English run). Both are **pre-existing Aug-21 import damage**, not from the leg fill:

1. **`val:Q93_LABS_VS1:12` / `val:Q94_LAB_CODE_VS1:12`** (in #1709's Q92–94 scope) held
   `'None 94. How much was the cost of ['` — the extractor glued the English option label,
   the locale word, and the *next* question's English stem. Present in **three** locales
   (HIL, WAR, BCL). The cleared F3 paper carries **no per-option list for Q93**, and every
   other code in the set is untranslated, so a single contaminated option inside an
   otherwise-English list is worse than a uniformly English one: **removed in all three
   locales and held** (same uniformity ruling as #1568). 5 map rows deleted + holds written.

2. **`val:Q171_WHY_NOT_VS1:04`** (HIL) held
   `'Naga worry bahin sa dugang nga gasto 172. Was the visit to ['`. Here the label itself
   is correct — `text-aug21/F3_HIL.txt` L5300–5301 prints
   `☐ Worried about additional costs☐ Naga` / `worry  bahin sa dugang nga gasto`, split
   across a line wrap — and only the glued tail is garbage. **Trimmed to the verbatim span**,
   not removed.

The same sweep across F1 and F4 found 4 more hits of this class (F1 BCL
`record:D_YAKAP_KONSULTA`, F4 FIL `record:C_HOUSEHOLD_ROSTER`, and two F4 WAR
`ENUM_RESULT_*` values holding a whole collapsed option list). They are pre-existing, tied
to no open ticket, and are being handled as a separate change set rather than riding along
in an F3 build.

## Pipeline

classify → per-section verbatim fragment writers (157 cells supplied, **16 dropped
by audit**, 10 notes → 7 after dedup/audit) → union merge (MERGE-WITH-PRIOR: union
keep/force, never overwrite another locale, never demote force:true, never
resurrect a hold; `-f3hil` baks) → `apply_aug21.py --only F3 --fail-on-pre --apply`
(clean, **0 writes to other locales**) → gates + defect sweeps → `generate_dcf.py`
+ `generate_qsf.py` → `verify_questions.py` **PASS F1 323 / F3 377 / F4 335** →
adversarial spot-check (workflow, 157 sampled / 138 cells, **PASS-WITH-FIXES**) →
stamp v7.0.9 → compile → deploy → box zip mtime verified → post-deploy bleed sweep →
two defects fixed → regenerate → verify PASS → stamp v7.0.10 → compile 17:48:54 →
deploy 17:52 → box zip mtime verified.

## Held for the ASPSI translator worklist — 268 items

Documented, never guessed. The bulk are admin / result-code / geography blocks the
cleared Hiligaynon source prints **English-only**, plus 17 flagged paper defects.
These render English until ASPSI supplies cleared text — an untranslated cell whose
source prints English is not a build defect.

## Retest (testers)

CSEntry → **remove** the app → **Add Application → from CSWeb** → fresh case.
The ⋮ Update menu is unreliable; a failed retest on a non-fresh build is a false
negative.
