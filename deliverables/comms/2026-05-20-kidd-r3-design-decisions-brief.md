# F2 PWA UAT Round 3 — 9 Design-Decision Questions for Survey-Design Disposition

**Draft date:** 2026-05-20
**From:** Carl (Data Programmer)
**For:** Kidd (ASPSI main RA) — please coordinate with Mam Merlyne / Dr Myra as needed
**Status:** Local draft, not yet sent

---

## Why this brief

Round 3 of the F2 PWA HCW-Survey UAT (closed 2026-05-15) surfaced **9 observations from Marriz** that are **questionnaire-content / validation-policy calls**, not CAPI defects. Per the role split — Data Programmer implements the spec; ASPSI survey-design team owns wording, option sets, and validation policy — each one needs a survey-design ruling before any code changes.

All 9 are tracked in GitHub with the `design-decision` + `status:blocked` labels (now applied). They cannot be closed until you (or Mam Merlyne / Dr Myra) disposition them. **One-pass review of this brief** is much cheaper than walking the 9 GitHub threads individually.

For each item below: **Decision needed** is the specific call to make; **Implementation cost** is what landing it on the PWA would take after a go-ahead.

---

## Summary table

| # | GH | Section / Item | Question type | Recommended default* |
|---|---|---|---|---|
| 1 | [#303](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/303) | A · Q11 | Allow decimal hours? | Keep integer (spec-anchored) |
| 2 | [#304](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/304) | E · Q52 | "No significant impact" exclusivity | Make exclusive |
| 3 | [#305](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/305) | A · Q9 | Cross-field constraint Q9 < Q34? | Add 0-zero block; defer cross-field |
| 4 | [#306](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/306) | C · Q35 | Don't-Know / Can't-Recall code? | Add DK code |
| 5 | [#307](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/307) | C · Q36 | Multi-select + stem re-wording | Survey-design call — no default |
| 6 | [#309](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/309) | C · Q39 | Remove "Not a physician/dentist"? | Keep + make exclusive |
| 7 | [#310](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/310) | D · Q47 | Add "None" option | Add (exclusive) |
| 8 | [#311](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/311) | J · Q110 | Add "None" option | Add (exclusive) |
| 9 | [#312](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/312) | J · Q125 | Multi-response + contradiction guard | Single-response (current) |

*Default = what I'd implement absent your call. None are binding — flag any I should reverse.

---

## Details

### 1. #303 — Section A Q11 — decimal hours

**Marriz observation:** Q11 only allows whole numbers; part-time HCWs may answer 3.5 hours.

**Current implementation:** `F2-Spec.md` Q11 specifies **integer hours, 1–24**; `F2-Validation.md` matches. PWA enforces.

**Decision needed:** Keep integer, or allow 1-decimal precision (e.g., 3.5)?

**Implementation cost if changed:** One-line schema change (number `step=0.5`); ~10 min including a regression test.

---

### 2. #304 — Section E Q52 — "No significant impact" exclusivity

**Marriz observation:** Q52 multi-select allows "No significant impact" to be ticked alongside other options — contradictory.

**Current implementation:** Multi-select with no exclusivity constraint.

**Decision needed:** Should "No significant impact" be **exclusive** (auto-deselects other options when chosen, and vice-versa)? This is the standard convention for sentinel options in survey instruments.

**Implementation cost if changed:** Add `exclusive: true` flag on the option in the spec; engine already supports the pattern (used elsewhere in F2). ~15 min including test.

---

### 3. #305 — Section A Q9 — cross-field validation against Q34

**Marriz observation:** Q9 'Year' subfield should not be ≥ Q34 (Age). Also, 0 in both subfields should not be allowed.

**Current implementation:** Q9 accepts any non-negative integer per subfield; no cross-field check against Q34.

**Decision needed:** Two sub-decisions —
- (a) Block 0+0 (tenure of 0 years AND 0 months)? — recommend **yes**, it's almost certainly a data-entry slip.
- (b) Add a cross-field constraint `Q9.years < Q34`? — recommend **defer** unless you want it; it triggers a question about *what* the failure UX should be (block? warn? require a comment?). Easier to disposition after seeing real respondent behaviour.

**Implementation cost if changed:** (a) ~15 min, (b) ~30–60 min depending on UX choice.

---

### 4. #306 — Section C Q35 — Don't Know / Can't Recall code

**Marriz observation:** Q35 asks for a date; respondent may not remember.

**Current implementation:** Date field, no escape code.

**Decision needed:** Add a "Don't Know / Can't Recall" code (likely value `9999` or a checkbox alongside the date input)? Across the F-series we use `9` / `99` / `999` as the highest-value code at field width (per project convention — not the DHS 7/97 convention).

**Implementation cost if changed:** ~30 min; includes spec note, downstream validation update, tester guide line.

---

### 5. #307 — Section C Q36 — multi-select + stem re-wording

**Marriz observation:** Two issues —
- (a) Q36 currently single-select; could be multi like Q39.
- (b) When Q34 = "Yes (already accredited)", Q36 stem "Why is your facility *applying*…" reads as future-tense; suggest re-word to past-tense "Why did your facility *apply* for…".

**Marriz already raised both with Mam Merlyne** (per her comment on #307).

**Current implementation:** Single-select; verbatim stem matches the questionnaire as supplied.

**Decision needed:** Two questionnaire-content calls. Per project memory `feedback_verbatim_questionnaire_labels`, I do **not** paraphrase item labels — wording changes are entirely survey-design owners' call. Awaiting Mam Merlyne's disposition.

**Implementation cost if changed:** (a) single→multi ~15 min. (b) re-word stem is ~5 min once final wording is set; if a conditional stem is wanted (different text per Q34 branch), ~30 min.

---

### 6. #309 — Section C Q39 — "Not a physician/dentist" option

**Marriz observation:** Two issues —
- (a) Remove the "Not a physician/dentist" option entirely — Q38 already captures the same fact.
- (b) If kept, the option can currently be selected *with* other options, which doesn't make sense.

**Current implementation:** Option present, multi-select with no exclusivity.

**Decision needed:** Same pattern as #304 — recommend **keep + make exclusive** unless you specifically want it removed. Removing it requires a spec sign-off because it's an option-set change; making it exclusive is a behavior change with the same UX as the standard sentinel pattern.

**Implementation cost if changed:** Exclusivity-only ~15 min. Option removal ~10 min + skip-logic check.

---

### 7. #310 — Section D Q47 — "None" option for ZBB challenges

**Marriz observation:** No "None" option for respondents who had no challenges with ZBB-covered patients.

**Current implementation:** Multi-select with no "None" / "Not applicable" sentinel.

**Decision needed:** Add a "None" option (exclusive — auto-deselects other options when chosen)? Standard pattern across most multi-select items in the instrument.

**Implementation cost if changed:** ~15 min including test.

---

### 8. #311 — Section J Q110 — "None" option for additional resources

**Marriz observation:** Same pattern as #310 — no "None" option for "no additional resources needed".

**Current implementation:** Multi-select, no sentinel.

**Decision needed:** Same as #310 — add "None" (exclusive)? Recommend yes for consistency.

**Implementation cost if changed:** ~15 min including test.

---

### 9. #312 — Section J Q125 — multi-response for HCW future plans

**Marriz observation:** Q125 currently allows multi-select; combinations like "Retire" + "Transfer to new facility" are mutually contradictory.

**Current implementation:** Multi-select.

> **Note:** Marriz's report listed test result as "Pass" — the observation is a forward-looking concern about respondent data quality, not a defect.

**Decision needed:** Three options —
- (a) Keep multi-select unconstrained (current).
- (b) Multi-select with exclusivity rules between specific options (e.g., "Retire" exclusive vs. "Transfer"). Requires you to enumerate which pairs are exclusive.
- (c) Convert to single-select.

Recommend (c) single-select as the simplest answer — career-future questions are typically single-response across the survey research literature, and it eliminates the contradiction class.

**Implementation cost if changed:** (b) ~30–60 min depending on rule complexity; (c) ~15 min.

---

## What I need from you

For each of the 9 items above, one of:
- **Approve recommended default** — I implement after R3 close.
- **Approve alternative** — name which.
- **Defer** — leave open, no implementation; explicit "decide later" so the issue stays parked rather than ambiguous.
- **Escalate** — punt to Mam Merlyne / Dr Myra; tell me the routing.

Once dispositioned, I'll close the GitHub issues with the disposition recorded inline, and (if any approve implementation) slot the work into Sprint 007 or earlier per priority.

---

## Out-of-scope clarification

This brief covers **R3 design-decisions only**. The Carl-actionable R3 bugs are tracked separately:
- **#294** — P0 Apps Script deploy gap (clasp redeploy; my responsibility, in flight)
- **#314** — high-severity matrix rehydrate bug (root-caused, architectural fix queued; my responsibility)
- All other R3 findings — already fixed via PRs #332 / #333 / #334 / #335 (5 fixes shipped 2026-05-19)
