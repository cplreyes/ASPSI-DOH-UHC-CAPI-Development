# UHC Survey Year 2 — Tabulation Findings (plain brief)

**For:** Ms. Myra + team — 3:00 PM meeting, 2026-07-06
**From:** Carl (Data Programmer)
**Based on:** the PSA-approved list of 197 tables (SSRCS Form 1, §II-9, signed 2026-06-15)

> **What I did:** I checked all **197 tables PSA expects us to produce** against the actual questions in our F1/F3/F4/F2 questionnaires — to see which ones we can build straight from the interview, and which ones need a decision or extra data first.
>
> **Note:** no interviews have happened yet (pre-test not run), so the sample tables below are **examples of the layout only** — the numbers are made up.

---

## 1. The short version

| Annex | Form | Tables | ✅ Ready | 🟡 Needs a decision | ⛔ Can't collect as-is |
|---|---|---:|---:|---:|---:|
| 1. Facility | F1 | 36 | 31 | 4 | 1 |
| 2. Patient | F3 | 105 | 74 | 30 | 1 |
| 3. Household | F4 | 36 | 29 | 7 | 0 |
| 4. Health worker | F2 | 20 | 13 | 6 | 1 |
| **Total** | | **197** | **147** | **47** | **3** |

- **147 tables (75%) are ready** — the question is in the form; we can build these the moment data comes in.
- **47 tables (24%) need one decision each** — we can build them, but I used the closest question we asked, or I need us to agree how to compute or who to count. I just need a yes/no so the numbers mean what DOH wants.
- **3 tables can't be built from the forms as they are** — the questionnaire simply doesn't ask for it.

**None of this holds up the pre-test.** It's about locking the analysis so the final tables are defensible.

---

## ⭐ To decide faster — my recommendation

I've put a **recommended choice on every item below.** If you're happy with them, you can **approve them as a batch and only flag the ones you'd do differently** — that settles all 50 in one pass. In short:
- **The 3 can't-build tables:** keep 2 as clearly-relabeled substitutes, and get the 3rd from DOH HR records. *(§2)*
- **The 47 decisions:** accept the closest-question stand-ins (relabeled), adopt the standard computation methods I list, and use the plain group definitions I propose. *(§3)*
- **The 3 duplicated tables:** produce once. *(§4)*

The Excel tracker (separate file) lists all 50 with my recommendation and a blank column for your decision.

---

## 2. The 3 tables we can't build as-is

| Table | What it asks | Why we can't | ⭐ My recommendation |
|---|---|---|---|
| **1.6** | % of facility heads who have **heard of how to apply for DOH licensing** | We never asked this. Closest: Q118 (are they licensed) and Q121 (which requirements are hard). | **Relabel to Q121 "facilities that find licensing requirements difficult"** — a usable, related figure. (Fallback: drop.) |
| **2.51** | Average **out-of-pocket paid for the room** (inpatient + outpatient) | The bill questions have no separate "room" line — expenses are recorded by who paid, not by item. | **Replace with "total confinement out-of-pocket"** — we have this and it's more useful than nothing. (Fallback: drop.) |
| **4.2** | Average **staffing shortage %** per facility (vacant vs. required posts) | Neither F2 nor F1 asks how many posts are required vs. filled. | **Deliver headcount only (Table 4.1) from the survey; compute the shortage % separately from DOH HR / plantilla records.** |

---

## 3. The 47 tables that need one decision each

Every table here **can be built** — it just needs one thing agreed. Full list in the appendix.

### Group A — "I used the closest question we asked — is that OK?" (~17 tables)
The table asks for something a little different from what the form actually asks, so I used the nearest question.
- **Examples:** 1.1 (used "knows how to start applying" — we never asked "heard of the process") · 1.15 (used "why not satisfied" — but only unhappy people were asked, so the base is skewed) · 2.18 & 3.15 (people **said** they know what a generic drug is — we didn't test if they're right) · 4.17 / 4.18 (we asked if they plan to leave — but not specifically "within one year").
- **What I need:** a yes/no on whether the stand-in is acceptable (and I'll rename the table to match what we really asked), or tell me to drop it.
- ⭐ **My recommendation:** **accept all the stand-ins and let me relabel each table to what we actually asked** (e.g. 1.1 → "knows how to start applying"). Keeps all 17 tables, honestly labeled — flag only any you'd rather drop.

### Group B — "We need to agree how to compute it" (~25 tables)
These are combined scores or totals where **the exact method changes the answer.**
- Money-related: 2.22–2.25 and 3.19–3.22 (free/subsidized medicine, sources of subsidy, financial assistance) · **2.29 — catastrophic health spending** (how much OOP counts as "catastrophic," at 25% and 40% of income) · 2.26 / 2.27 (No Balance Billing / Zero Balance Billing).
- Patient-experience scores: 2.47 (responsiveness) · 2.48 / 2.49 (dignity, autonomy, confidentiality) · 2.50 (overall experience).
- Health-worker tables: 4.1 (staff count per facility) · 4.12 (facilities offering enough training) · 4.15 / 4.16 (job satisfaction, top satisfaction factors).
- **What I need:** DOH/ASPSI to confirm the exact method — which answers count as "free," the catastrophic-spending cut-offs, which questions make up each score, and how we roll health-worker answers up to the facility.
- ⭐ **My recommendation (standard methods — approve as a set):** **catastrophic spending (2.29)** = compute it on **F4 (household), Capacity-to-Pay**: health out-of-pocket ÷ (total household spending − food), at **25% & 40%** — F4 already collects this via its Section N expenditure module (see the separate **CTP alignment note**); *this replaces my earlier "÷ income" note* · **"free/subsidized"** = the free / donation / "got it free" answer codes · each **experience score** = simple average of its Section-J questions (1–5) · **staff-per-facility** = average number of workers we interviewed per facility. Flag any where DOH wants a specific formula.

### Group C — "We need to agree who to count" (~5 tables)
The table names a group the form doesn't tag.
- "In the HCPN network" (2.14, 3.11) · "was billed" (2.25, 3.22) · "went through registration, even if unsuccessful" (3.9). The form never marks who belongs to these groups, so we have to define it.
- **What I need:** agree the plain definition of each group so the totals are consistent.
- ⭐ **My recommendation (practical definitions — approve unless DOH has official ones):** "in HCPN" = **referred from a primary-care provider / Konsulta** · "was billed" = **final bill greater than zero** · "went through registration" = **has a registration date on record**.

---

## 4. A few data-handling notes (for the data manager)

These affect how the tables are built, separate from the decisions above:
1. **Multiple-answer questions** (e.g. "where did you get the medicine — tick all") have to be split into one yes/no per option before counting. Please confirm the option/code lists per question.
2. **Expenses are entered line by line** (a mini-table per person); we add them up per person to get total out-of-pocket. We need one rule for blanks vs. zero vs. "don't know."
3. **Group C's "who to count"** groups (HCPN, billed, registered) are worked out, not asked — one agreed rule, applied once.
4. **Facility type and level** on patient/household tables come from the **facility master list**, not from the interview — so we need a clean, complete facility list to match on.
5. **Inpatient vs. outpatient won't always match** — some questions only apply to one (e.g. "rooms" is inpatient only; "sold assets to pay" is outpatient only), so a/b table pairs may differ.
6. **A few tables are printed twice** in the PSA list with identical wording (2.49 = 2.48, 3.25 = 3.24, 4.5 = 4.4). ⭐ **Recommend: produce once** (drop the identical reprints).

---

## 5. Sample tables (layout only — numbers are made up)

What the finished tables will look like. All are **weighted to represent the population**.

### Sample 1 — Facility (F1) · a "ready" table
**Percentage of facility heads, by facility type** *(example)*

| Answer | RHU | Gov't hospital | Private hospital | **All** |
|---|---:|---:|---:|---:|
| Yes | 61.2 | 78.4 | 70.9 | **66.5** |
| No | 35.1 | 18.3 | 26.0 | **30.4** |
| Don't know | 3.7 | 3.3 | 3.1 | **3.1** |
| **Total** | 100.0 | 100.0 | 100.0 | **100.0** |

<sub>Facility type comes from the facility list. Made-up figures.</sub>

### Sample 2 — Patient (F3) · a "how to compute" table (Group B)
**Catastrophic health spending, by income group** *(example)*

| Income group | Spent ≥25% of income · UHC-IS | ≥25% · Non-UHC-IS | Spent ≥40% · UHC-IS | ≥40% · Non-UHC-IS |
|---|---:|---:|---:|---:|
| Poorest fifth | 22.4 | 31.8 | 12.1 | 18.9 |
| Middle fifth | 9.8 | 14.1 | 4.3 | 6.7 |
| Richest fifth | 3.2 | 4.6 | 1.0 | 1.7 |
| **All** | **11.3** | **16.1** | **5.4** | **8.4** |

<sub>⚠ Compute on **F4 (household), Capacity-to-Pay**: health OOP ÷ (total household spending − food), at 25% / 40%. See the CTP alignment note. Made-up figures.</sub>

### Sample 3 — Patient (F3) · a "closest question" table (Group A)
**% who would go to YAKAP/Konsulta first, by province** *(example)*

| Province | Inpatient | Outpatient |
|---|---:|---:|
| Laguna | 48.6 | 55.2 |
| Cavite | 44.1 | 51.7 |
| … | … | … |
| **Overall** | **46.0** | **53.1** |

<sub>⚠ We didn't ask this directly — used "knows to book Konsulta when sick" + "has a primary care provider." Made-up figures.</sub>

### Sample 4 — Health worker (F2) · a "how to compute" table (Group B)
**Average number of health workers per facility, by facility level** *(example)*

| Facility level | Doctors | Nurses | Midwives | Allied health | **Total** |
|---|---:|---:|---:|---:|---:|
| RHU | 1.4 | 3.2 | 2.8 | 1.1 | **8.5** |
| District hospital | 6.7 | 18.4 | 4.2 | 7.9 | **37.2** |
| Provincial hospital | 14.2 | 41.6 | 6.1 | 19.3 | **81.2** |
| Private hospital | 9.8 | 33.1 | 3.4 | 15.7 | **62.0** |

<sub>⚠ Counted from how many workers we interviewed per facility (F2 covers all workers in the chosen facilities). Need to confirm this counting rule. Made-up figures.</sub>

---

## 6. What I need from the meeting

**Decisions (DOH / ASPSI):**
1. The **3 can't-build tables** (1.6, 2.51, 4.2) — stand-in, drop, or get outside data?
2. The **~17 "closest question" tables** — is each stand-in OK (I'll rename to match), or drop?
3. The **~25 "how to compute" tables** — confirm the methods (free-medicine codes, catastrophic-spending cut-offs, the experience-score questions, the worker-to-facility count).
4. The **~5 "who to count" tables** — agree the definition of HCPN / billed / registered.
5. The **duplicated tables** (2.49, 3.25, 4.5) — one or both?

**Data to give me:**
6. The **facility master list** (clean IDs, type, level) — used for every "by facility type/level" table.
7. The **option/code lists** for the tick-all questions.
8. For **4.2** (if we keep it): DOH HR / plantilla figures.
9. Confirmation of the **weights** (how each interview is scaled to the population).

**For the data manager to note:**
10. Rule for adding up expenses (blank vs. zero vs. "don't know").
11. Keep the "don't know / refused" codes consistent across forms.
12. Data file must open in **Stata 12** (already set on my side).

---

## Appendix — all 47 tables that need a decision

*Needs: **[Q]** confirm the closest question · **[M]** agree how to compute · **[W]** agree who to count · **[L]** from the facility list*

*⭐ My recommendation follows the tag: **Q** → accept the stand-in + relabel · **M** → adopt the standard method (§3B) · **W** → use the agreed definition (§3C) · **L** → build once the facility list is supplied. Per-row recommendations are in the Excel tracker.*

| Table | Form | What it needs | Needs |
|---|---|---|---|
| 1.1 | F1 | No "heard of the process" question; used "knows how to start" (non-accredited only) | Q |
| 1.10 | F1 | Used "where patients go" for services not offered; no 6-month window | Q |
| 1.15 | F1 | Used "why not satisfied" — only unhappy people were asked (skewed base) | Q |
| 1.22 | F1 | F1 only counts referrals sent out; the success outcome is on the patient form | Q·W |
| 2.9a | F3 | No direct "first place you'd go"; used "knows to book Konsulta" + "has a provider" | Q |
| 2.9b | F3 | No direct "first place you'd go"; used "knows to book Konsulta" + "has a provider" | Q |
| 2.14 | F3 | No marker for "in the HCPN network" — must define it | W |
| 2.18 | F3 | People said they know a generic drug; not tested for correctness | Q |
| 2.22a | F3 | "Free/subsidized medicine" pieced together from payment-source answers | M |
| 2.22b | F3 | "Free/subsidized medicine" pieced together from payment-source answers | M |
| 2.23a | F3 | Subsidy source from "got it free" codes; no LGU/employer option | M |
| 2.23b | F3 | Subsidy source from "got it free" codes; no LGU/employer option | M |
| 2.24a | F3 | Financial assistance pieced from assistance codes + MAIFIP | M |
| 2.24b | F3 | Financial assistance pieced from assistance codes | M |
| 2.25a | F3 | Same as 2.24a; "was billed" group has to be worked out | M·W |
| 2.25b | F3 | Same as 2.24b; "was billed" group has to be worked out | M·W |
| 2.26 | F3 | No Balance Billing — eligibility and receipt both worked out | M·W |
| 2.27 | F3 | Zero Balance Billing — no direct "received it"; inferred | M·W |
| 2.29 | F3 | Catastrophic spending — need the out-of-pocket rule + 25%/40% cut-offs | M |
| 2.31 | F3 | "Sold assets to pay" is outpatient only (not asked of inpatients) | Q |
| 2.32 | F3 | No direct "cut back on care"; used "reduced essential spending" + cost reasons | Q |
| 2.33a | F3 | Add up inpatient expenses; facility type from the facility list | L |
| 2.33b | F3 | Add up outpatient expenses; facility type from the facility list | L |
| 2.35a | F3 | Used visit-transport cost as stand-in; level of care from the facility list | Q·L |
| 2.35b | F3 | Used travel-cost rows as stand-in; level of care from the facility list | Q·L |
| 2.47a | F3 | Responsiveness score from Section J ("rooms" is inpatient only) | M |
| 2.47b | F3 | Responsiveness score from Section J | M |
| 2.48a | F3 | Dignity / autonomy / confidentiality score | M |
| 2.48b | F3 | Dignity / autonomy / confidentiality score | M |
| 2.49a | F3 | Printed the same as 2.48a — keep both or just one? | M |
| 2.49b | F3 | Printed the same as 2.48b — keep both or just one? | M |
| 2.50a | F3 | Overall experience score; broken down by status, sex, residence, facility level | M·L |
| 2.50b | F3 | Overall experience score; broken down by status, sex, residence, facility level | M·L |
| 2.52 | F3 | Consultation out-of-pocket from OPD rows + inpatient doctor's fee | M |
| 3.9 | F4 | No "went through registration (even if unsuccessful)" marker; approximated | W |
| 3.11 | F4 | No HCPN marker; used referral-from-primary-care; YAKAP not separated | W |
| 3.15 | F4 | Said they know a generic drug; not tested for correctness | Q |
| 3.19 | F4 | Free/subsidized medicine from "got GAMOT" + "got it free" codes | M |
| 3.20 | F4 | Subsidy source; no employer/dedicated-source option | M |
| 3.21 | F4 | Financial assistance from "how paid" codes | M |
| 3.22 | F4 | Same as 3.21; "was billed" group worked out from the bill amount | M·W |
| 4.1 | F2 | Staff count = how many workers we interviewed per facility | M |
| 4.12 | F2 | Facility-level % rolled up from worker answers — need the rule | M |
| 4.15 | F2 | Job satisfaction combined from the agreement-grid questions | M |
| 4.16 | F2 | Top satisfaction factors from the two grids | M |
| 4.17 | F2 | Asked if they plan to leave — but not specifically "within a year" | Q |
| 4.18 | F2 | Reasons for leaving; "within a year" not captured | Q·W |

*Prepared 2026-07-06 from the tabulation plan (`deliverables/tabulation-plan/`).*
