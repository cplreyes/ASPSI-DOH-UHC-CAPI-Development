---
type: deliverable
kind: qa-workflow
audience: Shan (QA tester) · Carl (data programmer) · ASPSI data manager (triager)
prepared_by: Carl Patrick L. Reyes
date_drafted: 2026-06-03
status: draft-for-review
related_task: E6-CAPI-005
companion_to:
  - .github/ISSUE_TEMPLATE/capi_bug_report.yml
tags: [qa, capi, testing, bug-triage, handoff, e6]
---

# CAPI QA Handoff Workflow (F1 / F3 / F4)

Extends the F2 PWA QA tester workflow to the **CSPro/CSEntry CAPI instruments**. Defines how desk-test + pretest defects get **reported, triaged, fixed, and re-verified** — and the one thing that makes CAPI different from the PWA: **fixes go through the generator, never the `.apc` by hand.**

> **Why a separate flow.** The F2 PWA fix path is *edit code → PR → deploy*. The CAPI fix path is *edit `generate_*.py` → regenerate → pre-flight → Designer compile → re-test*. Same triage + severity + labels; different fix mechanics. This doc + `capi_bug_report.yml` are the CAPI half of the QA system.

---

## 1. Roles

| Role | In this workflow |
|---|---|
| **QA tester (Shan)** | Runs the desk-test / smoke-test / pretest scenarios; files each defect via the **CAPI Bug Report** template; re-verifies fixes. |
| **Triager (data manager)** | Labels each report (epic + type + severity + source); assigns to the fix batch. |
| **Data programmer (Carl)** | Fixes at the **generator**, regenerates, re-runs pre-flight, hands back a compiled build; marks `status:fixed-pending-verify`. |

---

## 2. The loop

```
tester runs a scenario
   └─> files a CAPI Bug Report (.github template)        [label: bug]
        └─> triager adds:  epic:f1|f3|f4 · type:* · severity:* · from-capi-desk-test|from-capi-pretest
             └─> Carl fixes at generate_apc.py / generate_dcf.py  (NEVER the .apc/.dcf by hand)
                  └─> regenerate → `python preflight_validate.py` (exit 0) → Designer compile
                       └─> label status:fixed-pending-verify, comment the build date
                            └─> tester re-runs the same scenario
                                 ├─ passes → close
                                 └─ fails  → reopen / comment, back to Carl
```

---

## 3. Severity rubric (CAPI)

Mirrors the F2 rubric, with CAPI examples. The tester picks it in the template; the triager applies the matching `severity:` label.

| Severity | Means | CAPI examples |
|---|---|---|
| **Critical** (`severity:critical`) | Data loss, case won't save/sync, or the interview can't proceed | Case won't accept/save; sync fails for all cases; a Designer **compile error** blocks the build; consent/eligibility gate doesn't fire |
| **High** (`severity:high`) | Wrong data captured — interview still completes | Skip routes to the wrong question; a hard validation accepts an out-of-range value (or blocks a valid one); PSGC cascade allows a mismatched barangay; F4 roster loses/duplicates a member |
| **Medium** (`severity:medium`) | Display / layout / UX; data is captured correctly | Question shows on the wrong screen; a label is truncated; a soft warning's wording is unclear |
| **Low** (`severity:low`) | Cosmetic | Typo, spacing, label wording |

---

## 4. Label taxonomy (reuse the F2 scheme)

- **Instrument:** `epic:f1` · `epic:f3` · `epic:f4`
- **Type** (from the template's Bug type): `type:skip-logic` · `type:validation` · `type:sync` · `type:visual` · `type:i18n` — plus, for CAPI specifics, propose adding **`type:roster`** (F4 occurrence flow), **`type:gps-photo`**, **`type:psgc`**, **`type:compile`**.
- **Severity:** `severity:critical|high|medium|low`
- **Source:** propose adding **`from-capi-desk-test`** and **`from-capi-pretest`** (parallel to the existing `from-uat-round-N-YYYY-MM`).
- **Status:** `status:investigating` · `status:fixed-pending-verify` · `status:blocked` (e.g. waiting on a questionnaire-design decision → also tag `design-decision`).

> **Milestone:** group a fix sweep as a milestone (e.g. *CAPI desk-test fix batch 1*) so the pretest debrief (#199) can point at a closed batch — mirrors the F2 `v1.3.x` batch pattern.

---

## 5. The generator-fix rule (the CAPI-specific discipline)

When a CAPI bug is real:

1. **Find the source table**, not the symptom: a wrong skip → `SKIP_RULES` / `ROUTING_PROCS` in `deliverables/CSPro/<F>/generate_apc.py`; a wrong item/value set → `generate_dcf.py`; a form-layout issue → `generate_fmf.py` (F3/F4) or the static `.fmf` (F1).
2. **Edit the generator + regenerate.** Never hand-edit the `.apc`/`.dcf`/`.fmf` in Designer — the next regenerate would silently overwrite it (the generator-over-hand-edit rule).
3. **Re-run pre-flight:** `python deliverables/CSPro/preflight_validate.py` (exit 0 = symbols resolve) before handing back.
4. **Designer compile + a quick CSEntry pass**, then `status:fixed-pending-verify` + comment the build date so the tester knows which build to re-test.

---

## 6. Tester quick-start (Shan)

1. Run a scenario from the desk-test plan (#193 F1 / #194 F3 / #195 F4).
2. Hit something wrong? → **New issue → CAPI Bug Report** → fill instrument, where (Q-number/PROC), context, type, steps, expected vs actual, severity, screenshot.
3. When a fix lands (`status:fixed-pending-verify`), re-run the **same** scenario on the noted build; comment pass/fail.

---

## Issue coverage
| Section | Issue |
|---|---|
| `.github/ISSUE_TEMPLATE/capi_bug_report.yml` (template) + §3 rubric + §4 labels | #197 (E6-CAPI-005) |

**Operational follow-ups (not blocking this deliverable):** create the proposed `from-capi-*` / `type:roster|gps-photo|psgc|compile` labels in the repo; create the first *CAPI desk-test fix batch* milestone when desk-testing starts (#193–195). Feeds the pretest debrief → Epic 3 fix batch (#199).
