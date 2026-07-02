# ASPSI Go/No-Go — pre-test open decisions

**Date:** 2026-06-27 · **Context:** F1/F3/F4 are pre-test ready (audit done, fixes deployed + runtime-verified). The items below are the *only* things still open, and they are **decisions, not code/test work**. None blocks the instruments from running on-device; they affect data pooling, spec ambiguity, doc hygiene, and tester comms.

**How to use:** each item has a recommended call. Accept it, or override. Items needing ASPSI's intended behavior are flagged 🔵 (Kidd/Myra answer the *rule*; you decide whether/how to ask).

---

## ✅ Decisions (Carl, 2026-06-27)
- **A — harmonization:** ETL, **no instrument churn.** All XI-01/04/05/06 resolved in the ETL/codebook layer. No CSPro changes.
- **B — spec decisions:** **GO** — surface all three to ASPSI as written (F4-VAL-01 Q141.1, F1-LOGIC-02 Q152 §2/§3.8, F1-QC-01 Q63 wording). Builds unchanged pending ASPSI's rulings.
- **C — spec-doc hygiene:** **GO** — DONE. "SUPERSEDED — generator is source of truth" banners added to F1/F3/F4 `*-Skip-Logic-and-Validations.md` (2026-06-27).
- **D — tester comms:** **GO** — `TESTER-NOTE-questionnaire-number-2026-06-27.md` approved to relay to testers via ASPSI.

**Routing:** B (3 items) + D (tester note) go to ASPSI/Kidd-Myra via Carl. A + C need no ASPSI action.

---

## A. Cross-instrument harmonization — pooling risk only, nothing a tester sees

> **Blanket recommendation: NO-GO on instrument changes — resolve in the ETL/codebook layer.** Re-coding instruments mid-round risks regressions for zero on-device benefit; the breakout-DB pipeline already normalizes codes. Standardize *only* if ASPSI wants identical raw codes across instruments for a specific reason.

| id | divergence | recommended call |
|---|---|---|
| **XI-01** | exclusive "IDK/None" checkbox code: F1 = **09** (07 on Q58), F3/F4 = **90** | ETL: derived harmonized flag + documented per-instrument map. **No instrument change.** |
| **XI-04** | Yes/No/Don't-know: F3 DK = **3**, F4 insurance-roster DK = **55** | ETL: derived DK flag. **No instrument change.** |
| **XI-05** | Result-of-Visit raw codes (Postponed 2 vs 3, Incomplete 4 vs 3) | ETL: single derived AAPOR disposition var. **No instrument change.** |
| **XI-06** | categorical DK/Refuse not uniform (amount-level -98/-99 already is) | ETL: one codebook DK/Refuse table + derived flags. **No instrument change.** |

**Your call:** ☐ Accept (handle all four in ETL) ☐ Standardize one or more now (name which)

---

## B. Spec-decision findings — need ASPSI's intended rule 🔵

| id | issue | options | recommendation |
|---|---|---|---|
| **F4-VAL-01** 🔵 | Q141.1 (no-receipt bill amount) is **always asked** — its spec'd "no-receipt" gate option doesn't exist on Q141 (codes 01–07) | (a) add the option + gate, or (b) **drop the gate** (the ≤Q139 cap check stays either way) | **(b) drop the gate** unless ASPSI specifically wants the no-receipt branch — simplest, no data loss |
| **F1-LOGIC-02** 🔵 | Q152 = "Neither"(3): spec **§2** says fall through to Q153, **§3.8** says skip — the spec contradicts itself | ASPSI rules which section is authoritative | hold for ASPSI; one-line apc change once they rule (current build follows §2) |
| **F1-QC-01** 🔵 | Q63 English stem changed "DAYS"→"month/s" + a 5th option added — an unauthorized verbatim-wording change | keep (ASPSI approves) or revert to paper | hold for ASPSI sign-off (verbatim-English is their call) |

**Your call:** ☐ Surface B-items to Kidd/Myra as written ☐ Pre-decide F4-VAL-01 = drop gate, only escalate F1-LOGIC-02 + F1-QC-01

---

## C. Spec-doc hygiene — low-stakes, recommend GO

The F3/F4 spec docs trail the UAT-evolved generators (6 intentional departures in F4 alone). A maintainer trusting the stale spec could "re-fix" intended behavior and regress closed UAT items.

> **Recommended: GO** — add a prominent **"SUPERSEDED — see generator inline comments"** banner to the affected spec docs (F4-DOC-01, F3-QC-01/02/03, F1-QC-02). No behavior change; pure doc safety. I can do this now on your OK.

**Your call:** ☐ Go (I banner the docs) ☐ Defer

---

## D. Tester communication — recommend GO

The **case-key PSGC gate** is new: a dummy/placeholder Questionnaire Number is now rejected at field 1. Testers must enter a real PSGC number or they're blocked before the interview starts.

> **Recommended: GO** — relay the tester note (`TESTER-NOTE-questionnaire-number-2026-06-27.md`, already drafted) to testers via ASPSI before the round opens.

**Your call:** ☐ Go (send the tester note) ☐ Edit first (swap the example facility, etc.)

---

### One-line summary for the go/no-go
- **A (harmonization):** recommend ETL, no instrument churn.
- **B (spec decisions):** 3 items genuinely need ASPSI; F4-VAL-01 you can pre-decide (drop gate).
- **C (docs):** banner them — I can do it now.
- **D (testers):** send the case-key note.

*Nothing here blocks pre-test execution. The instruments are ready; these are the clean-up and pooling decisions.*
