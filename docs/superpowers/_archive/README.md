---
title: Superpowers archive
last_updated: 2026-05-08
---

# Superpowers archive

Plans, runbooks, and specs that document **work that has shipped**. Kept for historical reference and learning compounds; not for active iteration.

## Archived 2026-05-08

### Plans (shipped)
- `plans/2026-04-21-gps-photo-capture-f1-f3-f4.md` — GPS+photo capture pass executed 2026-04-21; DCFs reflect it.
- `plans/2026-04-21-psgc-external-lookup-refactor.md` — PSGC refactor shipped 2026-04-21 (PSGC externals + cascade live).
- `plans/2026-04-25-f2-pwa-matrix-view.md` — Matrix view (#18) shipped in v2.0.0.
- `plans/2026-05-01-f2-admin-portal-impl.md` — Admin Portal AP1–AP4 shipped at v2.0.0 2026-05-04.

### Runbooks (executed)
- `runbooks/2026-04-26-f2-auth-cutover.md` — Phase F shipped 2026-05-01 (E4-PWA-013 done).
- `runbooks/2026-05-01-ap0-apps-script-staging-setup.md` — AP0 staging setup; AP4 closed at v2.0.0.
- `runbooks/2026-05-02-f2-admin-portal-prod-cutover.md` — v2.0.0 cutover ran 2026-05-04.
- `runbooks/2026-05-04-e4-aprt-039-m10-sunset-soak-open.md` — M10 sunset closed 2026-05-04 with deletion not rotation (Sprint 004 Day 1 entry pivoted from this runbook's framing).
- `runbooks/2026-05-04-fx-006-as-push.md` — FX-006 dispositioned 2026-05-04 + re-verified 2026-05-05.
- `runbooks/2026-05-04-seed-demo-data.md` — UAT R2 opened 2026-05-04.

### Specs (implemented)
- `specs/2026-04-16-f3-f4-dcf-generators-design.md` — F3/F4 generators built, DCFs Build-ready since 2026-04-21.
- `specs/2026-04-25-f2-pwa-matrix-view-design.md` — Matrix view shipped in v2.0.0.
- `specs/2026-04-26-f2-pwa-auth-rearch-design.md` — Auth re-arch shipped to staging 2026-04-26, prod 2026-05-01.
- `specs/2026-05-01-f2-admin-portal-design.md` — Admin Portal v0.2 shipped at v2.0.0.

## Why these are archived

Active `docs/superpowers/{plans,runbooks,specs}/` directories should contain only **in-flight or upcoming work**. Once a plan is executed and the runbook has run, retaining them in the active directory creates noise during planning sessions.

The archive preserves the historical record (Carl can re-read any of these to understand what was done and why) without cluttering the working set.

## Re-activation

If a runbook needs to be re-run (e.g., a similar production cutover), copy it back to the active directory and update the date prefix; don't edit-in-place in archive.
