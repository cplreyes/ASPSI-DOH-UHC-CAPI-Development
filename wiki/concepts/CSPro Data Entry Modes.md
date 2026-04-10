---
type: concept
tags: [cspro, data-entry, capi, system-controlled, operator-controlled, skip-logic]
source_count: 1
---

# CSPro Data Entry Modes

CSPro data entry applications run in one of two modes — **operator-controlled** or **system-controlled** — chosen at application creation under `Options → Data Entry`. The choice has cascading effects on path tracking, allowed values, special-key behavior, and skip philosophy. For [[wiki/concepts/UHC Survey Year 2|UHC Survey Year 2]] all CAPI apps (F1, F3, F4) run in **system-controlled** mode, which is the recommended setting for CAPI surveys.

## Operator-controlled vs. system-controlled

| Property | Operator-controlled | System-controlled |
|---|---|---|
| Default for | Simple ad-hoc apps, censuses (PAPI keying) | Complex surveys, **all CAPI** |
| Special data entry keys | Active (operator can override flow) | Mostly disabled (operator cannot bypass logic) |
| Data entry path tracking | Off | On |
| `notappl` values | Allowed implicitly | Only allowed when defined in a value set |
| Logic enforcement | Operator can bypass | Strict — logic always runs |
| Aligns with | Heads-down keying | Heads-up and CAPI |

## Heads-down vs heads-up keying

- **Heads-down** — operator looks at the paper questionnaire, not the screen. Speed and accuracy are the priority. On-screen checks are minimal; consistency errors are resolved later in batch edits. Used for high-volume census keying. Operators don't need subject-matter knowledge.
- **Heads-up** — operator switches between paper and screen, catches errors as they go, makes decisions to resolve them on the spot. Used for surveys (lower volume, higher complexity). Operators must be trained on the subject matter. **CAPI is always heads-up by definition.**

For ASPSI's DOH surveys, the enumerator *is* the interviewer, so the heads-up / system-controlled / CAPI alignment is non-negotiable.

## Skip philosophy

CSPro distinguishes operator-controlled and application-controlled (automatic) skips:

- **Manual skip** — every field has a "skip field" target. Pressing `+` on the numpad jumps the cursor to that target. Default target is "next field". Operator-driven; matches operator-controlled mode and heads-down keying.
- **Automatic skip** — application logic decides whether to skip based on prior responses (e.g., skip the children section if the respondent has no children). Driven by the application; matches system-controlled mode and CAPI.

The trade-off: automatic skips speed up complex flows but a single mis-keyed prior answer can misdirect the cursor and confuse the enumerator. The Complete User's Guide cautions that automatic skips must be **well-documented** so enumerators understand when the cursor will move non-sequentially.

## Data entry path

- **Path on** (system-controlled, always): CSEntry remembers the order in which fields were entered. Going backwards walks fields in reverse-entry order; skipped fields stay skipped on the way back. To enter a previously-skipped field, the operator must go back further and change the answer that triggered the skip. This is what enforces the integrity of CAPI flows.
- **Path off** (operator-controlled, always): going backwards walks the literal field order, including fields that were skipped on the way forward.

## Implications for the project

1. **F1, F3, F4 are all system-controlled CAPI** — no override toggle needed; this is the default when creating a new CAPI Data Entry Application.
2. **All skips in F3 outpatient/inpatient routing and F4 household-conditional sections are automatic** — driven by `if`/`skip`/`advance` in the field's `preproc` or `onfocus`. They must be documented in the enumerator manual so interviewers know when the cursor will jump.
3. **`notappl` discipline** — under system-controlled mode, every legitimate "not applicable" answer for F1/F3/F4 must be explicitly defined in the value set. Anywhere logic needs to set a field to `notappl`, the value set must already permit it.
4. **No keyboard escape hatches** — enumerators cannot bypass validation. Every `errmsg` plus `reenter` in the consistency edits will block forward motion until resolved. This makes thorough error-message wording critical for usability.

## Sources

- (Source: [[wiki/sources/Source - CSPro 8.0 Complete Users Guide]])
