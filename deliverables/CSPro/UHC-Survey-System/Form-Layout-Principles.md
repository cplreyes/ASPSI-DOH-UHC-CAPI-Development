# Form-Layout Principles (CSPro FMF)

**Scope:** shared layout rules for all paper-origin CAPI instruments — F1 (Facility Head), F3 (Patient), F4 (Household). F2 (Healthcare Worker) is retired from CSPro and delivered as a PWA; these rules do not apply to it.

**Audience:** anyone building or reviewing a `.fmf` for this project. Each instrument has its own `F<n>-Form-Layout-Plan.md` that inherits from this file and adds section-by-section form inventory.

**Reference:** CSPro 8.0 Users Guide — *CAPI Strategies* (forms, fields, questions, blocks, partial save, prefilling). Where a rule below cites CAPI Strategies, that document is authoritative.

---

## 1. Core design rules

1. **Forms per subsection.** Each questionnaire subsection (e.g., Section A, Section B) is at least one form. Never combine two subsections on one form. Long subsections may split further (see §3).
2. **No scrolling on capture forms.** Every data-entry form must fit the tablet viewport without vertical scroll. If a subsection exceeds the budget (§2), split it at the nearest logical boundary.
3. **Rosters scroll alone.** Only roster (repeating record) forms may scroll, and only within the roster grid. A roster form contains the roster and nothing else — no adjacent non-roster fields. Per CSPro CAPI Strategies.
4. **One logical question per field.** No compound fields. Skip logic is handled in `preproc` / `onfocus` / `postproc`, not by packing multiple questions into one UI control.
5. **Tap targets are touch-sized.** Radio buttons, checkboxes, and dropdown chevrons must be comfortably tappable with an average adult index finger. Avoid dense grid layouts on capture forms.

---

## 2. Screen density budget

Target device: Samsung Galaxy Tab A series, 10.1", 1920×1200, landscape orientation. CSEntry renders at effective ~160 dpi.

| Field type | Row cost |
|---|---|
| Single-line text / numeric / date / time | 1 row |
| Radio group, horizontal (≤ 4 options) | 1 row |
| Radio group, vertical (5–7 options) | 1 row per option |
| Dropdown | 1 row |
| Checkbox list | 1 row per option |
| Multi-line text (≤ 3 visible lines) | 3 rows |
| Section label / separator | 0.5 row |

**Budget:** ~12 rows comfortable, 16 rows hard ceiling. Above 16, split the form.

**Layout default:** single column. Use two columns only for paired short-width fields (e.g., a Yes/No next to a small numeric; a year next to a month). Never split a question's label from its control across columns.

---

## 3. When to split a subsection

Split a subsection into multiple forms when any of these apply:

- Row budget exceeds 16.
- A skip-logic gate creates two disjoint paths with ≥ 4 fields each (put each path on its own form).
- A roster sits inside the subsection (rosters always get their own form — see §1.3).
- A capture trigger (GPS, photo) needs its own affordance (see §6).

Split at the nearest block boundary in the source questionnaire (Q-number contiguous group). Name split forms `SEC_<X>_<suffix>` where `<suffix>` is the topic of the split (e.g., `SEC_C_UHC_awareness`, `SEC_C_UHC_implementation`).

---

## 4. Capture-type defaults

| Source type | Default control | Notes |
|---|---|---|
| Yes/No | Radio group, horizontal | Use shared value set `VS_YES_NO` |
| 3–7 option single-select | Radio group, vertical | — |
| 8+ option single-select | Dropdown | Sort by frequency if known, else source order |
| Multi-select | Checkbox list | Mutual-exclusion rules enforced in `postproc` |
| "Other, specify" | Parent control + follow-up text field | Follow-up field on same form; skip-gated to "Other" selection |
| Short text (≤ 80 chars) | Single-line text | — |
| Long text (> 80 chars) | Multi-line text (3 lines) | — |
| Integer count | Numpad | Range check in `postproc` |
| Decimal / currency | Numpad with decimal | Currency = PHP; 2 decimal places |
| Year | Numpad, 4 digits | Range check: survey-appropriate min–current |
| Month | Dropdown (01–12) or numpad | Dropdown preferred for readability |
| Date | DatePicker | — |
| Time | TimePicker | 24-hour format |
| PSGC (Region / Province / City-Mun / Barangay) | Cascade dropdowns | See §7 |

---

## 5. Tab order

- Top-to-bottom, left-to-right reading order within each form.
- Form order: `FIELD_CONTROL` → Geographic ID → Subsection A → B → … → closing disposition.
- Skip-logic-driven skips use CSPro `skip to` targets. Never override tab order to implement skip logic.
- Enabled/disabled state is set in `onfocus` of the dependent field using the gate expression, not by re-ordering fields.

---

## 6. `FIELD_CONTROL` and capture triggers

### 6.1 `FIELD_CONTROL` block

- Always the first form in every instrument.
- Contents: survey metadata (survey code, region / province / city-mun / barangay), interviewer ID, date started, AAPOR disposition code, consent flag.
- **Consent gate:** if consent = No (or AAPOR refusal), the case skips all data-entry forms and jumps directly to the closing disposition form.
- Partial-save is enabled from this form onward; prefilling applies to date and interviewer ID if a resume.

### 6.2 Capture triggers (GPS, photo)

- Type-Z off-form records (e.g., `REC_FACILITY_CAPTURE` for F1) hold the captured values: latitude, longitude, accuracy, timestamp, photo filename.
- Triggers are **placed on a capture form**, not on the off-form record itself. A trigger is a button-style field that invokes an `.apc` helper.
- Naming convention: trigger field label reads as an action ("Capture GPS", "Take Verification Photo"). The field itself stores a yes/no completion flag.
- Helpers live in `shared/Capture-Helpers.apc`:
  - `ReadGPSReading()` — writes latitude, longitude, accuracy, timestamp into the capture record.
  - `TakeVerificationPhoto()` — writes filename using pattern `case-{QUESTIONNAIRE_NO}-verification.jpg`.
- Placement: put capture triggers on a dedicated capture form near the end of `FIELD_CONTROL` or at a natural break (e.g., after Geographic ID for F1). Do not interleave with data-entry questions.

---

## 7. PSGC cascade placement

- Geographic identification is its own dedicated form, placed immediately after `FIELD_CONTROL` and before any substantive subsection.
- Cascade order: **Region → Province → City/Municipality → Barangay.** Each level is a dropdown; the lower levels are disabled until the parent is filled.
- Mechanism:
  - External lookup dictionaries under `shared/`: `psgc_region.dcf`, `psgc_province.dcf`, `psgc_city.dcf`, `psgc_barangay.dcf`.
  - On each dependent field, `onfocus` calls the matching procedure in `shared/PSGC-Cascade.apc`, which uses `loadcase()` + `setvalueset()` to populate the child options filtered by the parent's selection.
- Do not hard-code PSGC options into `.dcf` value sets. All PSGC values come from the external dictionaries so updates (split / rename barangays) are a data refresh, not a code change.

---

## 8. Roster forms

- One roster per form. No adjacent non-roster fields.
- Column order on the roster grid follows the source questionnaire order.
- The roster form may scroll vertically (occupant-direction) and, if column count demands, horizontally within the grid — but the form shell (header, add/remove controls) stays pinned.
- Add/remove/edit controls use CSEntry defaults unless the questionnaire specifies otherwise.
- Validation at roster level runs in the record's `postproc` (cross-row consistency) or the field's `postproc` (cell-level).

---

## 9. Shared helpers and assets

| Asset | Location | Purpose |
|---|---|---|
| `Capture-Helpers.apc` | `deliverables/CSPro/shared/` | GPS read + verification photo helpers |
| `PSGC-Cascade.apc` | `deliverables/CSPro/shared/` | Loads + sets value sets for the 4-level PSGC cascade |
| `psgc_*.dcf` / `psgc_*.dat` | `deliverables/CSPro/shared/` | External PSGC lookup dictionaries (region, province, city, barangay) |
| `build_psgc_lookups.py` | `deliverables/CSPro/shared/` | Generator for the PSGC `.dat` files |
| `cspro_helpers.py` | `deliverables/CSPro/` | Python helpers used by every instrument's `generate_dcf.py` |

Every instrument's `FacilityHeadSurvey.ent.apc` (or equivalent) includes `Capture-Helpers.apc` and `PSGC-Cascade.apc` via CSPro include directive. Do not duplicate their bodies per instrument.

---

## 10. Review checklist

Before signing off a `.fmf`:

- [ ] Every subsection maps to ≥ 1 form; no subsection spans forms with another subsection.
- [ ] Every non-roster capture form fits the viewport without scroll (row budget ≤ 16).
- [ ] Every roster is on its own form.
- [ ] `FIELD_CONTROL` is first; Geographic ID (PSGC cascade) is second.
- [ ] Consent refusal skips all data-entry forms.
- [ ] Capture triggers are on capture forms, not data-entry forms.
- [ ] Tab order is reading-order; no skip logic implemented via tab reordering.
- [ ] All "Other, specify" follow-ups are on the same form as their parent.
- [ ] No PSGC values hard-coded.
- [ ] All shared helpers included, not duplicated.
