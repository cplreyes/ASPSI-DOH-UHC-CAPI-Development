---
type: source-summary
source_hcw: "[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/UAT-Round-2-2026-05-tester-feedback/ROUND 2 (HCW Test Survey)]]"
source_admin: "[[1_Projects/ASPSI-DOH-CAPI-CSPro-Development/raw/UAT-Round-2-2026-05-tester-feedback/Admin Portal side Feedback and Observation]]"
date_ingested: 2026-05-09
tags: [uat, round-2, f2-pwa, admin-portal, tester-feedback, shan]
---

# Source — UAT Round 2 Tester Feedback (2026-05): HCW Survey + Admin Portal

Tester: **Shan** (ASPSI RA, QA Tester) — see [[../entities/Sean]].

Two structured tester docs received from Shan covering the **F2 PWA v2.0.0** UAT Round 2 against production:

- `ROUND 2 (HCW Test Survey).docx` — 14 observations across the HCW Survey side (Sections A–J, Sync/Submission)
- `Admin Portal side Feedback and Observation.docx` — observations across all admin sub-tabs (Login, Data dashboard, Reports, Files, Data Settings, Users, RBAC, Encode)

Both staged at `raw/UAT-Round-2-2026-05-tester-feedback/` on 2026-05-09. Tester observations are **already filed as 27 individual GitHub Issues** (#68–#122 range) — most opened 2026-05-07. This source-summary is the canonical synthesis + cross-reference.

## Round Status (as of 2026-05-09)

- **27 GH issues open** with tester content; **22 are `status:fixed-pending-verify`** awaiting Shan re-verify against PR [#113](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/pull/113) (sessionStorage auth + deep-link + map clamp; merged Sprint 004).
- **3 stale-label issues** (#97 #104 #105) — currently `status:blocked` but PR #113 cascade-fixes them; should be re-labeled `status:fixed-pending-verify`.
- **2 still-blocked issues** (#106 #107) — Encode dashboard, auto-resolves once HCWs Create flow ships (E4-APRT-041 in Sprint 005).
- **Sprint 005 v2.0.1 hotfix release** addresses the remaining systemic gaps: orphan-admin guard (E4-APRT-050), change-password UI (E4-APRT-051), `password_must_change` server-enforce (E4-APRT-045), RBAC role-version cache (E4-APRT-044).

## HCW Survey — Cross-Reference (14 observations)

| Tester # | Code | Section / Question | Result | GH Issue |
|---|---|---|---|---|
| 1 | A.1.E2 | Token-paste enrollment — truncated token | Fail (wrong msg) | [#108](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/108) |
| 2 | A.1.E3 | Token-paste enrollment — offline | Fail (wrong msg) | [#109](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/109) |
| 3 | A.2.E8 | Q9 Section A — Months auto-zero | Fail | [#110](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/110) |
| 4 | B.E1 | Section B Q25 skip → auto-skip Q26–Q30 | **Pass** | [#111](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/111) |
| 5 | B.E2 | Section B Q25 multi-select 0 selections | Fail (None-of-the-above missing; advances anyway) | [#112](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/112) |
| 6 | C.E1 | Section C YAKAP/Konsulta — role-gating off | Fail (C/D/E visible to all 3 personas tested) | [#114](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/114) |
| 7 | C.E2 | Section C — force-nav to /section/c | Fail (redirects to A; sections lock but data retained) | [#115](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/115) |
| 8 | Q44 | Section D NBB/ZBB Q41–Q47 | Fail (proceeds to E despite Q45–47 unanswered) | [#116](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/116) |
| 9 | — | Section E1/E2 split suggestion | Suggestion | [#117](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/117) |
| 10 | G | Section G — KAP on Professional Setting (Q87/Q88) | Fail (data loss; redirects back; X icon despite complete) | [#118](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/118) ⚠️ title mismatch |
| 11 | J | Section J — Job Satisfaction | Fail (data loss; redirects to I; submits with Q124–Q125 unanswered) | [#119](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/119) |
| 12 | S.A1/S.A2 | Sync — offline submit | Fail (no queued msg; refresh → Section A) | [#120](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/120), [#121](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/121) |
| 13 | S.E1 | Sync — submit then offline before sync → DLQ | Inconclusive (no DLQ entry; tester unsure of repro) | [#121](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/121) |
| 14 | S.E2 | Sync — double-submit dedup | Fail (two responses recorded) | [#122](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/122) |

> [!warning] Title/body mismatch — #118
> Issue title: *"Section G — KAP on Fees (Q63–Q90, physician/dentist only, facility-type splits)"* — taken from UAT Tester Guide structure.
> Issue body: *"Section G — KAP on Professional Setting"* (Q87/Q88) — tester's actual experience.
> The Section G label drifted between the Mar 27 questionnaire spec and the UAT Tester Guide. Resolve by checking the live questionnaire's Section G headings; rename title to match.

> [!note] B.E1 passed — keep as PASS-record
> Tester item #4 (B.E1) is a passing observation, not a bug. #111 should remain open as a verified-pass record OR be closed with a comment confirming pass.

## Admin Portal — Cross-Reference (~30 observations across 16 sub-areas)

| Tester area | Code | Observation | GH Issue |
|---|---|---|---|
| #4 Layout | — | Auto-logout on refresh | [#68](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/68) ✅ fixed-pending-verify |
| 5.1 Login | L.H2 | Land on Data dashboard fails — change-password loop | [#70](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/70) ✅ |
| 5.1 Login | L.A1 | "Not working" | [#71](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/71) ✅ |
| 5.1 Login | L.A2 | Deep-link not preserved after re-login | [#71](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/71) ✅ |
| 5.1 Login | L.E1 | "Username or password is incorrect" should be "Invalid credentials" | [#72](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/72) ✅ |
| 5.1 Login | L.E2 | Throttle msg works after N>10 | [#69](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/69) (header) |
| 5.1 Login | L.E3 | Same copy-string issue as L.E1 | [#69](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/69) (header) |
| 5.1 Login | L.E4 | Not completed; no data displayed | [#69](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/69) (header) |
| 5.2 Responses | R.H2 | DEMO-HCW-* not directly clickable; VIEW button works | [#78](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/78) ✅ |
| 5.2 Responses | — | Date auto-fills "05/05/2026" on refresh | [#78](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/78) ✅ |
| 5.3 Audit | A.H2 | Request ID column missing | [#79](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/79) |
| 5.3 Audit | A.A1 | Row not clickable; no detail panel | [#80](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/80) |
| 5.3 Audit | A.E1 | No dash present (assumed no bug) | [#79](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/79) |
| 5.3 Audit | — | Date auto-fills "04/29/2026" on refresh | [#82](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/82) |
| 5.4 DLQ | D.H1 | Demo entry not clickable | [#83](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/83) ✅ |
| 5.4 DLQ | D.A1 | No replay button | [#84](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/84) |
| 5.4 DLQ | D.E2 | No delete button | [#84](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/84) |
| 5.5 HCWs | H.H2 | Reissue button visible without row selection | [#85](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/85) ✅ |
| 5.5 HCWs | H.H3 | Mono URL/QR/copy missing in modal | [#86](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/86) ✅ |
| 5.5 HCWs | H.H5 | QR not displayed; couldn't scan | [#87](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/87) ✅ |
| 5.5 HCWs | H.A1/A2/E1–E4 | Cascaded — couldn't perform | [#88](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/88) ✅ |
| 5.7 Map | M.A2 | Map doesn't stay focused on PH | [#89](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/89) ✅ |
| 5.7 Map | M.E2 | Bug observed | [#90](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/90) ✅ |
| 5.9 Files | F.H2 | Download not available | [#91](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/91) ✅ |
| 5.9 Files | F.A2 | Same filename allowed; no suffix disambig | [#92](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/92) ✅ |
| 5.9 Files | F.E4 | "Signature Mismatch" on non-ASCII filename | [#93](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/93) |
| 5.10 Data Settings | DS.H2/E2 | Included Columns not visible | [#94](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/94) |
| 5.10 Data Settings | DS.A2 | No disable button | [#95](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/95) |
| 5.10 Data Settings | DS.E1 | Saves with empty fields (auto-inputs F2) | [#96](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/96) |
| 5.11 Quota | Q.A1 | Couldn't test — auto-logout on refresh | [#97](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/97) ⚠️ stale-blocked label |
| 5.12 Users | U.A2 | Bulk Import not visible | [#98](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/98) |
| 5.12 Users | U.E2 | Cannot input non-existing role | [#99](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/99) |
| 5.12 Users | U.E3 | Bulk Import — couldn't perform | [#100](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/100) |
| 5.14 RBAC | RB.H3 | Role-lacks-permission msg + Add User submit fails + no audit/DLQ download | [#102](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/102) |
| 5.14 RBAC | RB.E1 | Direct URL → auto-logout (not 403/redirect) | [#103](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/103) ✅ |
| 5.14 RBAC | RB.E2 | Auto-logout on refresh | [#104](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/104) ⚠️ stale-blocked label |
| 5.16 Sidebar | N.H2 | Auto-logout on refresh | [#105](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/105) ⚠️ stale-blocked label |
| 5.17 Encode | E.H1/H2 | No HCW list — couldn't perform | [#106](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/106) blocked on E4-APRT-041 |
| 5.17 Encode | E.H3/E1/E2 | Couldn't perform | [#107](https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/107) blocked on E4-APRT-041 |

✅ = currently `status:fixed-pending-verify` (per PR #113); ⚠️ = stale label needing correction.

## Themes Across Both Sides

1. **Session-refresh / persistence (DOMINANT THEME)** — Auto-logout on every refresh appears in 7+ observations across Layout, RBAC, Sidebar, Quota, and indirectly blocks Encode testing. Root cause: admin tokens were in-memory only (spec §10.4). Fixed in PR #113 via sessionStorage with TTL.
2. **Copy-string drift** — "Username or password is incorrect" vs "Invalid credentials"; "Token rejected" vs "Token malformed"/"You're offline". Multiple instances; suggests a centralized error-message audit pass.
3. **Skip-logic / role-gating regressions** — Sections C/D/E visible to wrong personas (C.E1); Q45–47 not enforced before D→E (Q44); Section E1/E2 not pharmacist-skipped (suggestion #9).
4. **Data loss in long sections** — Section G and Section J both lose answers on back-navigation. Likely shared root cause; deserves dedicated investigation rather than per-section patches.
5. **Admin write paths missing UI** — Files download missing (F.H2); DLQ replay/delete missing (D.A1, D.E2); Bulk Import not visible (U.A2); Disable button missing (DS.A2); HCW Create flow not yet shipped (cascades to Encode E.H1/H2).
6. **Filter/persistence quirks** — Date filter auto-fills on refresh in Responses + Audit (#78, #82); minor but consistent.

## Open Questions for Triage

- **#118 title fix** — confirm whether Section G in the v2.0.0 questionnaire is "KAP on Fees" (Q63–Q90) or "KAP on Professional Setting" (Q87–Q88) before renaming.
- **B.E1 disposition** — close #111 with PASS comment OR keep open as audit record?
- **S.E1 inconclusive** — request tester re-run with explicit DLQ-trigger steps OR mark wontfix-tester-error.
- **Stale-blocked labels** — confirm PR #113 fixes #97 #104 #105 then re-label `status:fixed-pending-verify`.

## Related

- Tester guides used: `docs/F2-PWA-UAT-Round-2-{HCW-Survey,Admin-Portal}-Tester-Guide-2026-05-04.md`
- PR #113: sessionStorage auth + deep-link + map clamp (fixes 12 R2 issues)
- Sprint 005 plan: [[../../docs/superpowers/plans/2026-05-11-sprint-005-v2-0-1-plan]]
- Tester: [[../entities/Sean]]
