# Crosswalk Screenshot-Capture Punch-List

**Source:** per-instrument visual countercheck of the four paper↔CAPI/web crosswalks (F1, F2, F3, F4), 2026-06-19.
**Scope:** the right-hand (CAPI/web) column only. Paper pages are all real, correct, and complete — no paper captures needed.
**Finding that drives this list:** no pairings are *broken* and no image files are *missing*. The gaps are **coverage** — F3 and F4 have **zero** native screenshots (their entire right column is borrowed F1 screens), F1 is partial, and F2 is complete.

Image dir for all captures: `deliverables/CSWeb/landing/docs/img/`
Filename convention: `f{N}-capi-{slug}.png` (F2 uses `f2-web-section-{x}.png`).

---

## Priority tiers at a glance

| Tier | What | Why first |
|---|---|---|
| **P0** | The check-box / roster control, captured natively **per instrument** | Single highest-leverage item — it is the *only* pending control and clears 37 placeholders across F1/F3/F4 (F1 ×14, F3 ×10, F4 ×13) |
| **P1** | F3 + F4 native control-type set | They have 0 native shots; right now 100% borrowed from F1's "FacilityHeadSurvey" app |
| **P2** | F1 polish (Q1 re-shot, consent/Section-D flow, weak proxies) | F1 is the reference instrument; tighten the few soft spots |
| **P3** | F2 — **no captures**, one numbering confirmation only | F2 is done |

A check-box capture is per-instrument because the app title bar and option text differ (the borrowed shots literally read "FacilityHeadSurvey"). One representative check-box screen per instrument clears all that instrument's check-box placeholders.

---

## P0 — The universal check-box / roster control (do this first)

One native capture of the check-box multi-select (and the roster, where it differs) per instrument.

- [ ] **F1** check-box multi-select → `f1-capi-checkbox.png`
  Clears placeholders at: Q34 (reports used for decisions), Q49–Q50 (quality & access challenges), Q104–Q105 (BUCAS services & factors), Q117 (GAMOT stock-out response), Q121 + the ×13 "why difficult to comply" battery, Q165–Q166 (professional development).
- [ ] **F3** check-box multi-select → `f3-capi-checkbox.png`
  Clears: Q35–Q37, Q85, Q86, Q87, Q93–Q94, Q114, Q148–Q149, Q171.
- [ ] **F3** roster (matrix→checkbox+roster pilot) → `f3-capi-roster.png`
  Clears: Q92 (how consultation paid — roster). *(Ties to the Option B roster pilot.)*
- [ ] **F4** check-box multi-select → `f4-capi-checkbox.png`
  Clears: Q52/Q53, Q55, Q56, Q65/Q66, Q77/Q78, Q85, Q103, Q106/Q107, Q128, Q141/Q143, Q195/Q196, Q202.

---

## P1 — F3 native captures (currently 0 native; 55 borrowed-F1 proxies + 10 pending)

F3's whole right column is F1 screens used as control-type stand-ins. To make it a true F3 crosswalk, capture one **native F3 CSEntry** screen per control type below, then repoint the reused `f1-capi-*` references. Capture the **weak proxies** first — they currently misrepresent the control, not just the content.

**Weak proxies — capture native F3 screens (highest value):**
- [ ] 5-point rating scale → `f3-capi-rating-scale.png` — covers Q131–Q135, Q136–Q140, Q178 (now shown as a plain single-select list, not a rating scale).
- [ ] Payment / multi-source amount matrix → `f3-capi-amount-matrix.png` — covers Q98, Q107, Q113 (now shown as a single number-pad, not a matrix).

**Standard control types — one native F3 capture each (replaces borrowed F1 proxy):**
- [ ] Yes/No single-select → `f3-capi-yesno.png` (replaces reused `f1-capi-c-uhc-entry.png`)
- [ ] Short single-select → `f3-capi-single-select.png` (replaces reused `f1-capi-b-facility-profile.png`)
- [ ] Long single-select → `f3-capi-long-select.png` (replaces reused `f1-capi-c-attribution.png`)
- [ ] Number-pad / numeric entry → `f3-capi-number.png` (replaces reused `f1-capi-q3-q4-demographics.png`)

*(Plus the P0 check-box + roster above.)*

---

## P1 — F4 native captures (currently 0 native; 48 borrowed-F1 proxies + 13 pending)

Same situation as F3 — built from 5 reused F1 screens. Capture native F4 equivalents; prioritize the special screens that have no real analog.

**Special screens — no native equivalent exists, capture first:**
- [ ] Household roster (loop) → `f4-capi-roster.png` — Q30–Q34 (now stood in by `f1-capi-q1-name.png`).
- [ ] Private-insurance sub-roster → `f4-capi-subroster.png` — Q47–Q50.
- [ ] Expenditure grid → `f4-capi-expenditure-grid.png` — Q144–Q185 food / non-food / health-product batteries (now stood in by the single number-pad).

**Standard control types — one native F4 capture each:**
- [ ] Yes/No single-select → `f4-capi-yesno.png` (replaces `f1-capi-c-uhc-entry.png`)
- [ ] Short single-select → `f4-capi-single-select.png` (replaces `f1-capi-b-facility-profile.png`)
- [ ] Long single-select / rating → `f4-capi-long-select.png` (replaces `f1-capi-c-attribution.png`)
- [ ] Number-pad → `f4-capi-number.png` (replaces `f1-capi-q3-q4-demographics.png`)
- [ ] Free-text + keyboard → `f4-capi-freetext.png` (replaces `f1-capi-q1-name.png`)

*(Plus the P0 check-box above.)*

---

## P2 — F1 polish (real shots exist; tighten the soft spots)

- [ ] **Q1 re-shot** — `f1-capi-q1-name.png` currently shows the **"Respondent name and signature"** cover field; the literal "1. What is your name?" panel only appears in the nav tree. Re-capture so the main panel shows Q1 itself. *(Optional — control type is already correct.)*
- [ ] **Informed Consent sequence** — replace the `flow-ph` placeholder on the consent page-pair row with the real CSEntry consent screens.
- [ ] **Section D page-pair** — replace the `flow-ph` placeholder with the real Section D opening screens.
- [ ] *(Decide, don't necessarily capture)* text-only caption rows with no image at all: Q13/Q16, Q15/Q18, Q32, Q33, Q35/Q37, the Q65 ×9 "why difficult" battery, Q75–Q78. Either capture representative screens or leave them as intentional text-only rows.

**Known, intentional, not a bug:** Sections D–H reuse 6 control screenshots ~30× as honest "shown: the matching control" illustrations. Fine to leave; flagged only so it's a deliberate choice.

---

## P3 — F2 (complete — no captures)

F2's 10 web-section screenshots are all real and correctly paired; the one placeholder (Informed Consent) is intentional for the self-administered PWA.

- [ ] **Confirm, don't capture:** the **I/J question-number drift**. On paper, Section I (Facility Support) = Q86/Q87 and Section J (Job Satisfaction) = Q88–Q100+; on web, Section I shows its satisfaction item as Q96 while Section J's battery starts at Q86. Pairing and content are correct — confirm the renumbering is intentional.

---

## Capture-count summary

| Instrument | Net new native captures | Re-shots | Placeholders cleared | Non-capture actions |
|---|---|---|---|---|
| F1 | 2 (consent, Section D) | 1 (Q1) + 1 (check-box) | 14 | decide text-only rows |
| F2 | 0 | 0 | 0 | 1 (confirm I/J numbering) |
| F3 | 7 + check-box + roster | — | 10 | repoint reused `f1-capi-*` refs |
| F4 | 8 + check-box | — | 13 | repoint reused `f1-capi-*` refs |

**Do-first:** the per-instrument **check-box capture (P0)** — one screen each clears 37 placeholders and is the only universally-pending control.
