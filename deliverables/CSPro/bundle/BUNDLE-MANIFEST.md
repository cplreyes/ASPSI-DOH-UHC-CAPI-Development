---
type: deliverable
kind: deployment-bundle-spec
audience: Carl (Data Programmer); CSWeb admin (dictionary upload); field-deploy
date: 2026-06-07
sprint: 009
satisfies: GOAL-capi-instruments-e2e SUCCESS CRITERION #7 (deployable bundle exists)
related: [deliverables/CSPro/CSPro-Compile-and-Desk-Test-Runbook.md, deliverables/CSPro/2026-06-07-multilang-verify-worksheet.md]
tags: [cspro, deploy, bundle, csweb, tablet, s009]
---

# CAPI Deployable-Bundle Spec — F1 / F3 / F4

Defines the **deployable bundle** the goal requires (criterion #7) and the one-command
assembler that produces it. The bundle is assembled **from current artifacts on demand**
(not pre-copied) so it never goes stale across the IRON-RULE fix-loop or a Designer recompile.

## What a bundle contains (per instrument)

```
dist/
  shared/                       # resolves the ../shared/ #includes + external dicts
    Capture-Helpers.apc         #   (#include'd by every .ent.apc)
    PSGC-Cascade.apc            #   (#include'd by every .ent.apc)
    psgc_region.dcf  + .dat     # 4 PSGC external dicts + their lookups
    psgc_province.dcf + .dat
    psgc_city.dcf     + .dat
    psgc_barangay.dcf + .dat
  F1/  FacilityHeadSurvey.ent + .dcf + .fmf            + .ent.apc
  F3/  PatientSurvey.ent       + .dcf + .generated.fmf + .ent.apc
  F4/  HouseholdSurvey.ent     + .dcf + .generated.fmf + .ent.apc
```

The `dist/<INSTRUMENT>/` + sibling `dist/shared/` layout preserves the `../shared/` relative
`#include` so the bundled `.ent.apc` resolves exactly as in the source tree.

## The assembler

`build_bundle.py` (this folder):
- **`python build_bundle.py`** — audit only. Reports per-instrument readiness; writes nothing.
- **`python build_bundle.py --assemble`** — copies the *current* artifacts into `dist/` for every
  instrument whose `.ent` is present **and current**. Stale/pending instruments are skipped.

### Readiness gates (why "present" is not enough)
1. **components present** — `.dcf` + `.fmf` + `.ent.apc` exist.
2. **`.ent` present** — only Designer produces it (no honest headless entry compile; verified
   runbook 2026-06-04). Absent → `PENDING`.
3. **`.ent` current** — its mtime must be **newer** than every component. An `.ent` older than a
   regenerated `.dcf`/`.ent.apc` is a **STALE binding** (Designer must re-open → re-sync → recompile);
   reported `STALE`, not `READY`. This guards against shipping an out-of-date binding.

## Current readiness (2026-06-07, audit)

| Instrument | components | `.ent` | bundle |
|---|---|---|---|
| F1 Facility Head | all present | **STALE** — April `.ent` predates today's regenerated `.dcf`/`.ent.apc` (19:13) | BLOCKED |
| F3 Patient | all present | **PENDING** — not yet bound | BLOCKED |
| F4 Household | all present | **PENDING** — not yet bound | BLOCKED |

**All three blocked on the one human-gated step: the Designer compile that (re-)binds a current
`.ent`.** Shared payload (10 files) is complete. Everything the agent can prepare is prepared; the
assembler turns a clean compile into a deployable bundle in one command.

## Path to a READY bundle (per instrument)
1. Designer: open the `.ent` → Id-block re-sync (F1) → insert the 4 PSGC dicts → **Build ▸ Compile** clean.
   (This refreshes the `.ent` so it is no longer STALE.)
2. Desk-test passes per `2026-06-07-multilang-verify-worksheet.md` (all declared languages).
3. `python build_bundle.py` → instrument now reports **READY**.
4. `python build_bundle.py --assemble` → `dist/<INSTRUMENT>/` produced.
5. Deploy: CSWeb dictionary upload (the `.dcf`s incl. the 4 PSGC) + tablet sync (E4-CSWeb-003).

> Bundle = the stop line of this goal (OUT OF SCOPE: CSWeb provisioning, tablet procurement,
> pretest). Produce the signed-off `.ent`s and the bundle is done.
