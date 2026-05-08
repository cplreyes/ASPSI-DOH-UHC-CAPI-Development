---
type: concept
tags: [workflow, sign-off, qa, scrum, conventions]
source_count: 0
---

# Forward-Only Sign-Off

Standing working convention on this project: **design stages drive through to a testable artifact without formal gates; test bugs loop back to the owning source doc to be fixed.** There is no separate "design sign-off" checkpoint between a spec and the build that consumes it.

## The rule

1. Each design artifact (spec, skip logic, validation inventory, cross-field rules, cover-block text) is drafted and committed.
2. The next stage (build / generator / test) starts as soon as the artifact is usable — even if earlier artifacts are still in draft or unreviewed.
3. When a tester finds a bug, the fix is **not** treated as a gate failure. Instead, it's routed back to the **owning source doc** — the place where the wrong decision lives — and the build regenerates from the corrected source.
4. Reviewers' reads happen in parallel with build work, not before it.

## Why

- Solo-dev pipeline with a 1%/day late penalty (see [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/sources/Source - Signed CSA Dec 15 2025|Source - Signed CSA]]). Formal sign-off gates would serialize work and burn calendar days waiting for reviews that usually come back clean anyway.
- Every artifact in the F2 pipeline (spec → skip logic → validation → cross-field → Apps Script → live Form) is derived from the previous one. A defect in any layer surfaces loudest in testing, so testing is treated as the acceptance feedback loop.
- The artifacts are **reproducible from source**: the F1 DCF regenerates from `generate_dcf.py`, the F2 Form regenerates from `Spec.gs`. Re-running a build after a source fix is cheap.

## How it shows up in current pipelines

The rule applies wherever a generator + spec produces a regenerable artifact. Two live examples:

### F1 CSPro CAPI (in flight)

`deliverables/CSPro/F1/generate_dcf.py` regenerates `FacilityHeadSurvey.dcf` from `F1-Skip-Logic-and-Validations.md` + `cspro_helpers.py`. Bug-routing pattern:

| Symptom | Fix in |
|---|---|
| Wrong item label, missing question, wrong choices | `F1-Skip-Logic-and-Validations.md` + `generate_dcf.py` |
| Wrong skip logic, validation misfires | `F1-Skip-Logic-and-Validations.md` + `cspro_helpers.py` |
| GPS / photo capture wiring | `shared/Capture-Helpers.apc` + `generate_dcf.py` |
| PSGC cascade item options | `shared/PSGC-Cascade.apc` + external lookup dicts |

Rule: **never hand-edit `FacilityHeadSurvey.dcf` in CSPro Designer** — patch the generator and regenerate. F3/F4 follow the same pattern via their respective `generate_dcf.py` files. Memory: `feedback_f1_dcf_generator_source_of_truth.md`.

### F2 PWA (production at v2.0.0)

`deliverables/F2/PWA/app/spec/F2-Spec.md` is the canonical spec; the PWA codebase under `app/src/` consumes it. Bug-routing pattern:

| Symptom | Fix in |
|---|---|
| Wrong item label, missing question, wrong choices | `app/spec/F2-Spec.md` + spec-driven render |
| Wrong section routing, skip logic doesn't fire | `app/spec/F2-Spec.md` + `app/src/lib/router.tsx` |
| Wrong validation, range rejects valid values | `app/spec/F2-Spec.md` + `app/src/lib/validation.ts` |
| Submit failure, missing audit row | `worker/src/` (Worker JWT proxy) + `backend/src/` (Apps Script) |
| Admin Portal RBAC misfires | `worker/src/admin/rbac.ts` + `backend/src/Admin*.js` |
| Visual identity drift | `app/DESIGN.md` + `tailwind.config.ts` Verde aliases |

The earlier Google Forms / Apps-Script F2 pipeline (`F2-Spec.md` + `F2-Build-Handoff.md` + `apps-script/`) was retired 2026-04-17 alongside the track itself; old `F2-Build-Handoff.md` references in the wiki are kept for historical context only. See [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/concepts/F2 Google Forms Track|F2 Google Forms Track]] for the superseded design.

## How this differs from conventional Scrum

- Classic Scrum has a **Definition of Done** per story; here, DoD is per-sprint, not per-artifact. An artifact is "done enough" when the next stage can start.
- Classic Scrum has a **review** ceremony with stakeholders blessing deliverables. Here, stakeholder review runs asynchronously — ASPSI reviews F2 cover-block text, the LSS debrief surfaces process changes, but none of these block the build loop.

## Memory

- `memory/feedback_forward_signoff_loopback_bugs.md` — the rule's authoring context. Originated Sprint 001 after the Apr 13 LSS reveal that formal gates were costing more calendar days than they saved.
