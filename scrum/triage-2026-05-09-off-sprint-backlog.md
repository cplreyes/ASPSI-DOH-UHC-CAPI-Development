---
title: Off-Sprint Backlog Triage — 2026-05-09
date: 2026-05-09
trigger: Carl — "do off-sprint backlogs" → "triage the ~64 backlog"
prerequisite_completed: UAT Round 2 tester docs ingested (raw + wiki source-summary + GH labels normalized)
---

# Off-Sprint Backlog Triage — 2026-05-09

> Saturday read-only triage prep, in advance of Monday's planned Sprint 005 kickoff. After this triage, R2 label coverage and stale-blocked corrections are now in place.

## Snapshot

| Bucket | Count | Action |
|---|---|---|
| Sprint 005 committed (Goal A + Goal B) | 10 | No action — already on the docket |
| UAT R2 fixed-pending-verify (PR #113 cascade) | 25 | Batch-close on Shan/Kidd R2 sign-off |
| UAT R2 still-blocked | 2 | Auto-resolves with E4-APRT-041 (Sprint 005 Tier 2) |
| UAT R2 open work — survey-side (F2 HCW) | 14 | Slate for **Sprint 006 v2.0.2 (Mon 2026-05-18 → Fri 2026-05-22)** (or v2.0.1 stretch) |
| UAT R2 open work — admin-portal | 6 | Slate for **Sprint 006 v2.0.2 (Mon 2026-05-18 → Fri 2026-05-22)** (or v2.0.1 stretch) |
| CAPI / Phase 2 follow-ups | 2 | Sprint 005 Goal A (#131) + Phase 2 plan (#135) |
| **Total open issues** | **64** | |
| **Total off-Sprint-005 (true triage scope)** | **54** | |

---

## Sprint 005 — already claimed (no action)

Per `docs/superpowers/plans/2026-05-11-sprint-005-v2-0-1-plan.md`:

**Tier 1 (security + lockout, ~6.5h)**
- #133 E4-APRT-050 — Orphan-admin guard + self-delete guard
- #134 E4-APRT-051 — Change-password UI
- #57 E4-APRT-045 — JWT password_must_change server-enforce
- #56 E4-APRT-044 — RBAC role-version cache stale-entry fix
- #65 E4-APRT-043 — Production ADMIN_PASSWORD_HASH deletion

**Tier 2 (visible UX gaps, ~4.5h)**
- #66 E4-APRT-048 — `last_login_at` write path
- #58 E4-APRT-041 — Create-HCW UI in Admin Portal
- #64 E4-APRT-042 — Per-tester admin user accounts hardening

**Tier 3 stretch**
- #132 E4-APRT-049 — Design-review 5-fix sweep
- #63 E4-APRT-037 — Concurrency tests

---

## Bucket 1 — UAT R2 fixed-pending-verify (25 issues)

All resolved by **PR #113** (sessionStorage auth + deep-link + map clamp), merged Sprint 004. Awaiting Shan/Kidd re-verify against staging/prod.

| Cluster | Issues | Resolution path |
|---|---|---|
| Session/refresh persistence | #68, #71, #97*, #103, #104*, #105* | sessionStorage with TTL (PR #113) |
| Login copy-string + flow | #70, #72 | (Note: copy-string fix may still be partial) |
| Reissue Token / HCWs flow | #85, #86, #87, #88 | Cascade-resolved by session fix |
| Map Report PH-bounds | #89, #90 | maxBounds + minZoom=5 (PR #113) |
| Audit + DLQ surface | #79, #80, #82, #83 | Mixed — verify each |
| Files / Data Settings | #91, #92, #94, #95, #96 | Mixed — verify each |
| Users — non-existing role | #99 | Verify |
| Layout — Responses + audit | #78 | Date filter persistence |

`*` = re-labeled today from `status:blocked` → `status:fixed-pending-verify` after PR #113 cascade analysis.

**Recommended action**: Shan + Kidd run R2 verification pass against staging Mon-Tue Sprint 005; close all 25 in batch on R2 sign-off. Triage owner: tester-driven, not Sprint 005 work.

---

## Bucket 2 — UAT R2 still-blocked (2 issues)

| # | Title | Blocker | Auto-resolves on |
|---|---|---|---|
| #106 | 5.17 Encode dashboard (E.H1, E.H2) | No HCW list available | E4-APRT-041 (Sprint 005 Tier 2 — Create-HCW UI ships HCW list) |
| #107 | 5.17 Encode dashboard (E.H3, E.E1, E.E2) | Same as #106 | E4-APRT-041 |

**Recommended action**: No discrete work; mark for re-test after E4-APRT-041 lands Wed-Thu of Sprint 005.

---

## Bucket 3 — UAT R2 open work, F2 HCW Survey side (14 issues)

These are genuine open bugs not addressed by PR #113 or Sprint 005 v2.0.1. **Recommended target: Sprint 006 v2.0.2 (Mon 2026-05-18 → Fri 2026-05-22)** (or pull as Sprint 005 stretch if headroom allows).

### 3a — Skip-logic / role-gating regressions (5)

| # | Code | Severity (proposed) | Theme |
|---|---|---|---|
| #114 | C.E1 | **critical** | Sections C/D/E visible to wrong personas (3 personas tested, all sections leaked) — data integrity |
| #116 | Q44 | high | Section D auto-proceeds to E despite Q45–Q47 unanswered |
| #115 | C.E2 | medium | Force-nav to /section/c redirects to A but answers retained |
| #117 | — | medium (enhancement) | Section E1/E2 split suggestion for pharmacist auto-skip |
| #112 | B.E2 | high | Q25 multi-select advances with 0 selections; "None of the above" missing |

### 3b — Data loss in long sections (2 — likely shared root cause)

| # | Section | Severity (proposed) |
|---|---|---|
| #118 | Section G — Q87/Q88 redirect-back to F + answers vanish + X icon despite complete | **critical** |
| #119 | Section J — Q98–Q125 redirect-back to I + answers vanish in matrix grids + submit before Q124/Q125 | **critical** |

> ⚠️ **Investigate as a unit**: both sections lose answers on back-navigation in matrix-style or long sections. Likely shared bug in the section-state-on-back-nav code path. Single root-cause investigation > two patches.

### 3c — Sync / submission (3)

| # | Code | Severity (proposed) | Detail |
|---|---|---|---|
| #122 | S.E2 | high | Double-submit creates two responses (no client_submission_id dedup) |
| #120 | 5.13 | high | Submission + Sync section header issues |
| #121 | S.A1/A2/E1 | medium | Offline submit doesn't show queued msg; refresh redirects to A; DLQ inconclusive |

### 3d — Validation (1)

| # | Code | Severity (proposed) |
|---|---|---|
| #110 | A.2.E8 / Q9 | medium — Months field doesn't auto-zero when Years entered |

### 3e — Copy-string drift (2 — Token paste error messages)

| # | Code | Severity (proposed) |
|---|---|---|
| #108 | A.1.E2 | low — "Token rejected" should be "Token malformed" |
| #109 | A.1.E3 | low — "Token rejected" should be "You're offline" |

### 3f — PASS observation (keep as audit record OR close)

| # | Code | Disposition |
|---|---|---|
| #111 | B.E1 | **Carl decision needed**: close with PASS comment OR keep open as verified-pass record |

---

## Bucket 4 — UAT R2 open work, Admin Portal side (6 issues)

| # | Code | Severity (proposed) | Detail |
|---|---|---|---|
| #102 | RB.H3 | high (security) | Add User/Role visible but submit doesn't proceed; no audit/DLQ download — pairs with Sprint 005 #56 RBAC fix |
| #93 | F.E4 | medium (i18n) | Non-ASCII filename → "Signature Mismatch" — likely R2 sig regression |
| #98 | U.A2 | medium | Bulk Import not visible (admin write-path missing UI) |
| #100 | U.E3 | low | Bulk Import couldn't perform — cascade from #98 |
| #84 | D.A1, D.E2 | medium | DLQ replay + delete buttons missing |
| #69 | L.E2/E3/E4 (header) | low (copy-string) | Section-header issue covering throttle msg + copy-string + L.E4 incomplete data |

**Recommended action**: Slate for Sprint 006 v2.0.2 (Mon 2026-05-18 → Fri 2026-05-22) batch. #102 may largely auto-resolve with Sprint 005 #56 (RBAC role-version cache fix) — re-verify after Sprint 005 closes.

---

## Bucket 5 — CAPI / Phase 2 (2 issues)

| # | Title | Status |
|---|---|---|
| #131 | E3-F1-088 — Phase 1 sync mechanic resolution (syncdata external-dict + CSDB binding) | **In Sprint 005 Goal A** — last 5% of Phase 1 build |
| #135 | E3-F1-PHASE2-PLAN — Phase 2 plan + scope confirmation | Sprint 005 Goal A planning artifact |

Both already in Sprint 005's Goal A scope per `scrum/sprint-current.md`.

---

## Recommended Actions for Monday's Triage Session

1. **Confirm severity/type labels per issue** in Buckets 3 + 4 (proposed in this report; ~20 issues).
2. **Disposition #111** — close with PASS comment or keep as audit record.
3. **Resolve #118 title mismatch** — verify whether v2.0.0 questionnaire's Section G is "KAP on Fees" or "KAP on Professional Setting"; rename title accordingly.
4. **Pull stretch into v2.0.1** — if Sprint 005 headroom realized: candidates are **#118 + #119** (data loss in G/J — critical, likely shared root cause investigation) and **#114** (role-gating regression — critical for data integrity).
5. **Plan Sprint 006 v2.0.2 (Mon 2026-05-18 → Fri 2026-05-22) milestone** — slate Buckets 3 + 4 minus anything pulled into Sprint 005 stretch. Likely ~20 issues.
6. **R2 sign-off plan** — coordinate with Shan + Kidd to schedule the verification pass for the 25 `status:fixed-pending-verify` issues; batch-close on sign-off.
7. **#106 / #107 re-test** — schedule for after E4-APRT-041 lands (Wed-Thu Sprint 005).

---

## Mutations Applied 2026-05-09 (this triage prep session)

- **Batch A** (label coverage): added `round:2` + `from-uat-round-2-2026-05` to 20 placeholder issues — #69, #84, #93, #98, #100, #102, #108, #109, #110, #111, #112, #114, #115, #116, #117, #118, #119, #120, #121, #122
- **Batch B** (surface label): added `surface:admin-portal` to 6 admin-side placeholders — #69, #84, #93, #98, #100, #102
- **Batch C** (semantic correction): #97, #104, #105 re-labeled `status:blocked` → `status:fixed-pending-verify` per PR #113 cascade-fix; explanatory comment posted on each
- **Wiki ingest**: 2 tester docx files staged at `raw/UAT-Round-2-2026-05-tester-feedback/`; source-summary at `wiki/sources/Source - UAT Round 2 Tester Feedback (2026-05) - HCW Survey + Admin Portal.md`; `index.md` + `log.md` updated

R2 label coverage: was 27, now 47 issues. Status breakdown: 25 fixed-pending-verify, 20 no-status (need triage), 2 blocked.

## Open Questions for Carl — Resolved 2026-05-09

All originally-flagged decisions resolved during the same Saturday triage session:

- ~~**Pull #118 + #119 (G/J data loss) into Sprint 005?**~~ — **PULLED 2026-05-09** as Tier 1.5 R2 critical pull-ins. Combined investigation, 3–6h. See Sprint 005 plan §Tier 1.5.
- ~~**#114 role-gating regression**~~ — **PULLED 2026-05-09** as Tier 1.5. 2–3h estimate.
- ~~**#122 double-submit dedup**~~ — **PULLED 2026-05-09** as Tier 1.5. 1–2h estimate. (Added to pull-ins; was implicit critical from severity sweep.)
- ~~**#118 title rename**~~ — **RENAMED 2026-05-09** to "Section G — back-nav loses answers at Q87/Q88 + X icon despite ✓ + redirect to F (KAP on Professional Setting, Charging, And Reimbursement)" using canonical v2.0.0 spec heading from `deliverables/F2/PWA/app/src/generated/items.ts:2371`.
- ~~**#111 (B.E1 PASS) disposition**~~ — **CLOSED 2026-05-09** with PASS comment citing tester verbatim + cross-reference to wiki source-summary.
- ~~**Sprint 006 cadence**~~ — **CONFIRMED 2026-05-09:** Sprint 006 v2.0.2 runs Mon 2026-05-18 → Fri 2026-05-22 (rolling 1-week Mon-Fri cadence following Sprint 005 close). Plan doc to be drafted at Sprint 005 close.

Sprint 005 budget grew from ~15h committed to ~21–26h committed after the 4 Tier 1.5 pulls; headroom now 0–4h. Tier 3 polish (#132 design sweep, #63 concurrency tests) defers to v2.0.2 if Sprint 005 schedule slips.
