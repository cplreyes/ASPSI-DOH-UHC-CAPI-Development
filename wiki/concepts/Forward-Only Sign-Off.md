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

## How it shows up in the F2 pipeline

- `deliverables/F2/F2-Build-Handoff.md` ships [[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/wiki/entities/Shan Lait|Shan]] a **bug-routing table** keyed by symptom → source doc:

  | Symptom | Fix in |
  |---|---|
  | Wrong label text, missing question, wrong choices | `F2-Spec.md` + `apps-script/Spec.gs` |
  | Wrong section routing, skip logic doesn't fire | `F2-Skip-Logic.md` + `apps-script/Spec.gs` (branchTo map) |
  | Wrong required flag, numeric range rejects valid values | `F2-Validation.md` + `apps-script/Spec.gs` |
  | POST rule mis-fires (wrong flag, wrong drop) | `F2-Cross-Field.md` + `apps-script/OnSubmit.gs` |
  | Apps Script crashes, routing mis-wires | `apps-script/FormBuilder.gs` or `Code.gs` |
  | Consent or cover-block wording | `F2-Cover-Block-Rewrite-Draft.md` + `apps-script/Spec.gs` (SEC-COVER) |

- After a fix, `rebuildForm()` trashes the old Form + Sheet and rebuilds fresh. Shan's test submissions on the old Form are expected to be lost — every rebuild cycle starts clean.
- Sprint 001 Day 3 (2026-04-15) proceeded straight from design bundle (013/014/015/016) into the E3-F2-GF Apps Script generator **without waiting** on Shan's review of the design bundle, per this rule. Test bugs will route back to the owning source doc as usual.

## How this differs from conventional Scrum

- Classic Scrum has a **Definition of Done** per story; here, DoD is per-sprint, not per-artifact. An artifact is "done enough" when the next stage can start.
- Classic Scrum has a **review** ceremony with stakeholders blessing deliverables. Here, stakeholder review runs asynchronously — ASPSI reviews F2 cover-block text, the LSS debrief surfaces process changes, but none of these block the build loop.

## Memory

- `memory/feedback_forward_signoff_loopback_bugs.md` — the rule's authoring context. Originated Sprint 001 after the Apr 13 LSS reveal that formal gates were costing more calendar days than they saved.
