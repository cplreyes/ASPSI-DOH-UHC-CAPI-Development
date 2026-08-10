# Catastrophic Health Expenditure — Capacity-to-Pay vs. the questionnaires

**For:** 3 PM tabulation meeting, 2026-07-06 · **Relates to:** Table 2.29 (the only CHE table)

## 1. The method (from the reference)

Catastrophic health expenditure (CHE) = a household crosses a threshold. Two approaches:

| | Budget Share | **Capacity-to-Pay (what we need)** |
|---|---|---|
| Formula | OOP ÷ (total expenditure **or income**) | OOP ÷ (total expenditure **− basic needs**) |
| Basic needs | — | **Sub-1:** actual food · **Sub-2:** standard food · **Sub-3:** standard food + rent + utilities |
| Thresholds | 10% & 25% | **25% & 40%** (Sub-1) · 40% (Sub-2, Sub-3) |

**Numerator (both):** out-of-pocket health payments. **The difference is the denominator.**

---

## 2. The key finding — the table is on the wrong form

- The **only** CHE table is **2.29**, and it uses **25% & 40%** thresholds → that is the **Capacity-to-Pay** method.
- But 2.29 is assigned to **F3 (Patient)**, and **F3 cannot do Capacity-to-Pay** — it only collects **income (Q18)** and **per-visit health costs**. It has **no household total spending, and no food / rent / utilities spending**.
- The form that **can** do it is **F4 (Household)** — it has the **Section N household-expenditure module (WHO/SHA)**: food, non-food, and health spending, plus income.

➡ **Recommendation: compute Table 2.29 from F4 (Household), not F3.** F4 already carries everything the method needs.

---

## 3. What Capacity-to-Pay needs → what we already have

| The method needs | Already asked? | Where (F4) |
|---|---|---|
| **Numerator — health out-of-pocket** | ✅ Yes | Section N health items → auto-subtotals **Q177** (12-mo), **Q182** (6-mo), **Q185** (1-mo) |
| **Total household expenditure** | ✅ Yes | Section N = food + non-food (1/6/12-mo) + health (sum in the ETL — see note 4) |
| **Basic needs: food** (Sub-1, actual) | ✅ Yes | **Q157** food subtotal (auto-computed) |
| **Basic needs: rent + utilities** (Sub-3) | ✅ Yes | Non-food rows: **rent/rental, water, electricity, fuel** |
| **Income** (for the budget-share alternative) | ✅ Yes | **Q18** (amount + bracket), plus Q186 / Q195 |

**Bottom line: F4 needs no new questions for Sub-1 (actual food) or Sub-3 (food + rent + utilities).**

---

## 4. What's missing / to be supplied

1. **Standard subsistence amounts** — Sub-methods **2 and 3** compare against a *standard* basic-needs basket (a benchmark, e.g. the **PSA food threshold / subsistence poverty line** by area). This is **external data, not a survey question.** *Supply the PSA figure if we run Sub-2/Sub-3.* **Sub-1 (actual food) needs nothing external.**
2. **Which non-food rows count as "rent" and "utilities"** — the module lists them by category; the ETL must pick the exact codes (rent/rental · water · electricity · fuel/LPG/firewood). *Confirm the code list with the data manager.*
3. **Reference period** — Section N mixes 1-, 6-, and 12-month recall, and there is **no auto-computed "total expenditure"** (only food + 3 health subtotals are auto). The ETL must **annualize**: non-food 1-mo ×12, 6-mo ×2, 12-mo ×1; food annualized; and use the **12-month health total (Q177)** so numerator and denominator cover the same year. *Confirm 12-month as the reference period.*
4. **OOP definition** — confirm the Section N health amounts are **net of PhilHealth/insurance** (true out-of-pocket), not gross.
5. **Patients ≠ households** — 2.29's printed universe is *patients* (F3), but F3 patients aren't linked to F4 households. If DOH specifically wants CHE **among patients**, F3 can only do **budget-share on income (Q18)** — a different method (10%/25%). *Decision needed: household-level CHE (F4, correct) or patient-level (F3, budget-share only).*

---

## 5. What to ask / add

- **F4 (Household): no questionnaire change needed.** The WHO/SHA module already captures total spending, food, rent, and utilities — so Sub-1 and Sub-3 are computable today. *(No change during the freeze.)*
- **F3 (Patient): no change recommended.** Adding a full household-consumption module to a patient survey isn't feasible — move CHE to F4 instead.
- **External:** obtain the **PSA subsistence-food / basic-basket thresholds** only if DOH wants Sub-2/Sub-3.

---

## 6. Recommendation to lock at the meeting (Table 2.29)

**Compute 2.29 on F4 (Household), Capacity-to-Pay:**
- **Numerator** = household health OOP over 12 months (**Q177**).
- **Denominator** = total annual household expenditure **− actual food (Q157)** = **Sub-method 1**, reported at **25% and 40%** (matches the committed thresholds).
- **Optional sensitivity** = Sub-method 3 (− food − rent − utilities) at 40%, if DOH supplies/blesses the basic-needs basket.
- Keep **budget-share on income (Q18)** only as a secondary comparison if DOH wants the patient-level angle — labeled clearly at 10%/25%.

> This **supersedes** the earlier tracker note for 2.29 ("OOP ÷ income"). The tracker + brief are being updated to point 2.29 at F4 with the Capacity-to-Pay (Sub-1) method above.

*Prepared 2026-07-06 from the F4 Section N module + the tabulation plan.*
