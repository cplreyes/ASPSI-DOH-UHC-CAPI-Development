# F2 PWA — UAT Round 2 (HCW Survey side) — Tester Guide

**Round:** 2 (testers' numbering)
**Drafted:** 2026-05-04
**Side:** HCW survey (PWA enrollment + form completion + submission)
**Companion guide:** `docs/F2-PWA-UAT-Round-2-Admin-Portal-Tester-Guide-2026-05-04.md` (Admin Portal side, for Kidd)
**Coordinator:** Carl Patrick L. Reyes (Data Programmer)
**Window:** Opens 2026-05-04 evening · No hard close (rolling; daily triage)

> **Project context.** This is the **DOH UHC Survey Year 2 — Healthcare Worker Survey**. Field rollout uses tablets handed to HCWs (nurses, midwives, physicians, etc.) at sampled health facilities. The HCW pastes a tablet token (issued by ASPSI ops) into the PWA, which authenticates them, gates them to the right facility, and runs them through the questionnaire. Round 2's job is to break the **HCW-facing flow** before field rollout.

> **Scope of this guide.** PWA-side only — what an HCW sees on the tablet, from "I just received this token" to "Submitted, thank you." Admin-portal-side testing (Reissue Token, DLQ, Audit, etc.) is in the companion guide above.

---

## 1. Quick Reference

| Item | Value |
|---|---|
| **Production PWA URL** | https://f2-pwa.pages.dev |
| **Spec — verbatim question text + validation rules** | `deliverables/F2/F2-Spec.md` (Sections A–J, Q1–Q125 with Q108 omitted) |
| **Skip logic + branching** | `deliverables/F2/F2-Skip-Logic.md` |
| **Cross-field validation** | `deliverables/F2/F2-Cross-Field.md` |
| **Bug repo** | https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues |
| **Bug-filing label** | `from-uat-round-2-2026-05` |
| **Slack channel (blockers only)** | `#f2-pwa-uat` on `aspsi-doh-uhc-survey2.slack.com` |
| **Release notes** | https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/releases/tag/v2.0.0 |

> Testers don't need any login on the HCW survey side — the tablet token is your authentication.

---

## 2. Tester Roster

| Tester | Focus | Test devices to use |
|---|---|---|
| **Shan** (ASPSI RA) | Primary HCW Survey tester — exhaustive question-by-question pass | Tablet (Android or iPad) primary; desktop Chrome secondary |
| _additional testers TBD_ | _Carl to fill_ | _per assignment_ |

If you're a tester not listed here, ping coordinator before testing — token assignment is per-tester.

---

## 3. Your Test HCW Assignments (with embedded tokens)

Each row below is **one prod-signed enrollment URL** for one demo HCW on the prod PWA. Open the URL on your test device → it auto-fills the token textarea → click Verify token → you're enrolled.

> **DO NOT share these URLs publicly.** Each token mints a session for that specific HCW. If a token leaks, anyone with the URL can submit on behalf of that HCW. Coordinator can revoke/reissue if needed.

### Primary assignment — Shan

| HCW ID | Persona (from seed) | Facility | Status pre-test | Enrollment URL |
|---|---|---|---|---|
| `DEMO-HCW-004` | Garcia, Roberto · **Pharmacist/Dispenser** · Male · 29 | DEMO-FAC-RHU-QC-1 (NCR / QC RHU) | enrolled, no submission yet | `https://f2-pwa.pages.dev/enroll?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJkYmUzYTU0ZS03OTIzLTQzYjAtYTk4MS0yYmY1ODQzNGU3N2EiLCJ0YWJsZXRfaWQiOiI1MGE1M2QzYy02ZDE2LTRlYWYtODY3ZC0wNTFlMmEzYzJiZWQiLCJmYWNpbGl0eV9pZCI6IkRFTU8tRkFDLVJIVS1RQy0xIiwiaWF0IjoxNzc3ODg2OTE5LCJleHAiOjE3ODA0Nzg5MTl9.6ytd1Hu66lABXpCuEMdhgl4c3cIgIpLbkwnRTM8P36A` |

> **Why this HCW:** Pharmacist role doesn't trigger the role-conditional gates for Sections C / D / E1 / E2 / G — clean baseline run. Status is `enrolled` (no prior submission), so you'll exercise the full happy-path flow without colliding with seeded responses.

### Spare HCWs (for additional testers or re-test scenarios)

| HCW ID | Persona | Facility | Status pre-test | Notes | URL |
|---|---|---|---|---|---|
| `DEMO-HCW-001` | Cruz, Juan · **Physician/Doctor** · Male · 42 | DEMO-FAC-RHU-QC-1 | submitted (seed) | Use for: re-submit / already-submitted edge-case testing. Section C/D/E1/E2/G **all visible** for Physician role. | `https://f2-pwa.pages.dev/enroll?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJkMjZhZThkMS03MDg3LTQwMDctODU0MC04NGFmNjM1YzM3MjEiLCJ0YWJsZXRfaWQiOiI2YWE0Nzc5Zi04NWUyLTQ1ZTgtOGE2OC00YTQ0NDFhZWVjZTciLCJmYWNpbGl0eV9pZCI6IkRFTU8tRkFDLVJIVS1RQy0xIiwiaWF0IjoxNzc3ODg2OTAyLCJleHAiOjE3ODA0Nzg5MDJ9._bexwLn1kN1EaHTKD2CUgrkaLfdiJW9NB_YvGjasUEA` |
| `DEMO-HCW-002` | Santos, Maria · **Nurse** · Female · 35 | DEMO-FAC-RHU-QC-1 | submitted (seed) | Use for: Nurse-role gating tests (Section G hidden). | `https://f2-pwa.pages.dev/enroll?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiI0MjI2MzRmNy04YmQ4LTRiYjktYmE2Yy0xMjgwNTM3NTIwMWEiLCJ0YWJsZXRfaWQiOiIzMjg4YWEwZi05MmViLTRiYmEtYmI1My03ZjE4ZWQyMmVmZjEiLCJmYWNpbGl0eV9pZCI6IkRFTU8tRkFDLVJIVS1RQy0xIiwiaWF0IjoxNzc3ODg2OTA4LCJleHAiOjE3ODA0Nzg5MDh9.3N9y_p0B8xea0g4vGHpb47AL_kXQxUR_hD2jrpdU1ro` |
| `DEMO-HCW-003` | Reyes, Ana · **Midwife** · Female · 38 | DEMO-FAC-RHU-QC-1 | submitted (seed) | Use for: Midwife-role gating. | `https://f2-pwa.pages.dev/enroll?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiI1YzcwMDY4OS1lNjMyLTQxYWMtYWZlOC0wZWI5YzVlNjNmNjYiLCJ0YWJsZXRfaWQiOiIzNTBlZmRlZS02N2ZhLTQzM2QtYjI1Zi0wOWExYTdjMmEyMmEiLCJmYWNpbGl0eV9pZCI6IkRFTU8tRkFDLVJIVS1RQy0xIiwiaWF0IjoxNzc3ODg2OTEzLCJleHAiOjE3ODA0Nzg5MTN9.Z4ldTlYvXG1JD-YkcdNbMGSNJDfMJrbJrRMBJH37Mds` |
| `DEMO-HCW-005` | Bautista, Lorna · **Barangay Health Worker** · Female · 51 | DEMO-FAC-RHU-QC-1 | submitted (seed) | Use for: BHW-role gating (most sections gated off). | `https://f2-pwa.pages.dev/enroll?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiIyNDYxYTVkZS1mNjc5LTQ1ODQtODU2OS0wYTEzMTFkZTQ1YjYiLCJ0YWJsZXRfaWQiOiJkZjYyY2U1NS04OGQ0LTRkOGItOGE1MC1iNGE0YjlhNGYwMDIiLCJpYXQiOjE3Nzc4ODY5MjksImV4cCI6MTc4MDQ3ODkyOSwiZmFjaWxpdHlfaWQiOiJERU1PLUZBQy1SSFUtUUMtMSJ9.7hmKYy0XIxH8cu9jGh24x4nP3VDJCFWLZIvw_Hwj98o` |
| `DEMO-HCW-006` | Mendoza, Liza · **Physician/Doctor** · Female · 47 | **DEMO-FAC-DH-INFANTA** (IV-A District Hospital) | submitted (seed) | Use for: cross-facility testing — different region, different facility-type gates. | `https://f2-pwa.pages.dev/enroll?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJkMWUxOWVjNC0yOWEzLTQ1MDAtOGNmNy1lMmNkODI5MzU5NjciLCJ0YWJsZXRfaWQiOiJiYTUyNzRkZi0zZGVjLTRhNTgtYTgzMS1lZWY5OGQ4YWIwZGUiLCJmYWNpbGl0eV9pZCI6IkRFTU8tRkFDLURILUlORkFOVEEiLCJpYXQiOjE3Nzc4ODY5MzUsImV4cCI6MTc4MDQ3ODkzNX0.ZmfhDGpwrR6uLPYM1RYX2u-3PmYMhWXEoc4lL3IgJ9g` |
| `DEMO-HCW-007` | (DH-INFANTA HCW) | DEMO-FAC-DH-INFANTA | enrolled, no submission yet | Spare for additional Round 2 testers. | `https://f2-pwa.pages.dev/enroll?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJmMjUzN2YzMy1mNTI2LTQ0ZDYtOGFiYS0yZmM3MzQxZDA0OTIiLCJ0YWJsZXRfaWQiOiI0YjliZDljYi04ZjBhLTQ1MTQtYTE4Yi00Y2ZlZjBmNjA0Y2MiLCJmYWNpbGl0eV9pZCI6IkRFTU8tRkFDLURILUlORkFOVEEiLCJpYXQiOjE3Nzc4ODY5NDEsImV4cCI6MTc4MDQ3ODk0MX0.GXkvyAuKYsDdfbG9PhaKKA1kYMv-jKAh6kAnDBmMVlE` |
| `DEMO-HCW-008` | (DH-INFANTA HCW) | DEMO-FAC-DH-INFANTA | enrolled, no submission yet | Spare for additional Round 2 testers. | `https://f2-pwa.pages.dev/enroll?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiI2ZDVmMjQ4Zi1kN2VhLTRiMTMtOTkzMC1lODc3YmU3MzJkZmQiLCJ0YWJsZXRfaWQiOiI5YmJiY2YwMy04MWI2LTQ5YmMtOGJkYy0yZGM5MDhiNjFlZmMiLCJmYWNpbGl0eV9pZCI6IkRFTU8tRkFDLURILUlORkFOVEEiLCJpYXQiOjE3Nzc4ODY5NDgsImV4cCI6MTc4MDQ3ODk0OH0.e7HWJJmea2bBr9cDdDouPAyHl6RdEYowcpOBTRsaOu4` |

**Tokens are 30-day TTL** (issued 2026-05-04, expire 2026-06-03). If a token expires before you finish testing, ping coordinator for a fresh issue.

---

## 4. Pre-Flight Checks (do these before testing)

1. **Open `https://f2-pwa.pages.dev` in Chrome on your test device.** Confirm the HCW survey root loads (Verde paper background, "UHC Survey Y2 — Healthcare Worker Survey Questionnaire" header, "Enroll" / "STEP 1: TABLET TOKEN" panel).
2. **Open DevTools** (F12 on desktop, or Chrome remote debugging from a paired desktop for tablets). Network + Console tabs visible.
3. **Read these reference docs once before testing:**
   - `deliverables/F2/F2-Spec.md` — full questionnaire structure with verbatim question text
   - `deliverables/F2/F2-Skip-Logic.md` — all role + facility-type gates
   - `deliverables/F2/F2-Validation.md` — required-field + range + format rules
4. **Confirm your token works:** open the primary URL above, click Verify, advance to the role-select / Section A screen.

---

## 5. Test Scenarios

The questionnaire has **Sections A–J, ~124 items (Q1–Q125 with Q108 missing).** Test each section with three lenses:

| Lens | What you're checking |
|---|---|
| **Happy** | Does the form work as the spec says it should? |
| **Alternative** | Same flow with non-default inputs (Back button, browser refresh, role switch, partial save / resume) |
| **Error** | Bad inputs, validation triggers, network drops, unexpected user actions |

For every bug you find, open the spec at the cited section to confirm whether it's a **PWA bug** (deployed code diverges from spec) or a **spec bug** (spec is wrong) — the fix path is different.

### 5.1 Token-paste enrollment

#### Happy

- **A.1.H1** — Tap your assignment URL on the tablet → token auto-fills → Verify → role-select screen. Pick the role matching your HCW's seed persona (e.g., DEMO-HCW-004 = Pharmacist/Dispenser).
- **A.1.H2** — Manually paste only the token *string* (everything after `?token=` in the URL) into the textarea. Same result.
- **A.1.H3** — On the admin's QR code (in companion guide's Reissue flow), scan from your tablet camera; URL opens; token verifies.

#### Alternative

- **A.1.A1** — After enrollment, close the tab and reopen `f2-pwa.pages.dev` directly (no token). Expect: token-paste screen again (the tablet doesn't persist the token to localStorage by design — spec §10.4).
- **A.1.A2** — Re-paste the same token after closing/reopening; should resume your in-progress survey state where you left off.

#### Error

- **A.1.E1** — Manually edit the URL to change `f2-pwa.pages.dev` to `staging.f2-pwa.pages.dev` and try the same token. Expect: "Token rejected" (cross-environment tokens never verify).
- **A.1.E2** — Truncate the token string (delete the last 10 chars) and paste. Expect: "Token malformed" — clear error, no crash.
- **A.1.E3** — Verify token while **offline** (DevTools → Network → Offline; or airplane mode). Expect: graceful "you're offline" hint with retry, no infinite spinner.
- **A.1.E4** — After ASPSI ops re-issues your token (coordinator does this from admin portal), the OLDER token should be rejected when pasted. Try it. Expect: "Token revoked / superseded" message.

### 5.2 Section A — Healthcare Worker Profile (Q1–Q11)

> **Project context:** Q5 (role) drives every downstream gate — Sections C / D / E1 / E2 / G all branch on it. Q7 (private practice) is conditional only for public-facility respondents and gates Q8.

**Items to verify present:**
- Q1 multi-field name (Last / First / Middle Initial — Middle Initial optional)
- Q2 employment type — single + "Other (specify)"
- Q3 sex at birth — single (Male / Female only)
- Q4 age — number, min 18
- Q5 role — single + "Other (specify)" — 16 choices
- Q6 specialty — single + "Other (specify)" — 22 choices, optional
- Q7 private practice (conditional gate)
- Q8 time split (only if Q7=Yes AND public facility)
- Q9 tenure — dual input (years + months)
- Q10 days/week — number 1–7
- Q11 hours/day — number 1–24

**Happy:**
- A.2.H1 — Fill every required item with valid values; tap Next; advance to Section B.

**Alternative:**
- A.2.A1 — Pick role "Other (specify)" — text field appears; required when Other selected.
- A.2.A2 — On Q5, pick "Nurse"; advance and verify Section G is hidden in nav. Go back to Q5, change to "Physician/Doctor"; verify Section G appears.
- A.2.A3 — Fill Q1 with multi-byte/Filipino characters (e.g., "Reyes-Ñiño"). Should accept; submission should preserve.

**Error:**
- A.2.E1 — Leave Q1 First Name empty → required validation triggers; Next blocked.
- A.2.E2 — Q4 age = 17 → range validation rejects (min 18 per spec).
- A.2.E3 — Q4 age = 999 → range validation rejects (sane max).
- A.2.E4 — Q4 age = "abc" → format validation rejects.
- A.2.E5 — Q10 days/week = 8 → range rejects.
- A.2.E6 — Q11 hours/day = 25 → range rejects.
- A.2.E7 — Pick role "Other" but leave the specify-text empty → "specify required" validation.
- A.2.E8 — On Q9, enter only Years (leave Months empty) → confirm whether Months is required or auto-zero per spec. File bug if behavior diverges from `F2-Spec.md` Q9.

### 5.3 Section B — UHC Awareness (Q12–Q30)

> **Project context:** 19 items measuring awareness of UHC and expected changes due to its implementation. Q21 + Q22 added in Apr 20 spec (DOH licensing + PhilHealth accreditation status). Q25 → Q26–30 is the split of an old single matrix into overview-multi + per-domain conditionals.

**Happy:**
- B.H1 — Walk every item; check exactly one option for single-selects, ≥1 for multi-selects.
- B.H2 — Q25 (overview multi) — pick 2 domains; verify Q26–Q30 visibility matches your selection (only the picked domains' detail items show).

**Alternative:**
- B.A1 — On Q25, pick all domains; Q26–Q30 all visible. Then unpick one; verify the corresponding Q26-30 item disappears AND any answer you'd entered for that item is cleared (or preserved — note actual behavior).

**Error:**
- B.E1 — Skip Q25 entirely; advance — confirm whether Q26–Q30 are auto-skipped or whether you're blocked. Per spec, conditional logic on Q25 should auto-skip the dependents.
- B.E2 — Multi-select with 0 selections → if "None of the above" is a choice, it should be the only valid 0-selection state; otherwise "at least one" required.

### 5.4 Section C — YAKAP/Konsulta (Q31–Q40, role-gated)

> **Project context:** Section C only shown to HCWs whose role is in scope per Q5 (Physician, Nurse, Midwife, BHW typically — confirm against `F2-Skip-Logic.md`). For DEMO-HCW-004 (Pharmacist), this section should be **hidden**.

**Happy:**
- C.H1 — When testing with a Physician/Nurse/Midwife persona (e.g., DEMO-HCW-001 / 002 / 003), Section C should appear in nav between B and D. Walk every item.

**Error:**
- C.E1 — When testing with a non-gated persona (e.g., DEMO-HCW-004 Pharmacist), Section C should be **hidden**. If it appears, file a bug.
- C.E2 — Force-navigate to `/section/c` URL when role-gated off. Expect: redirect or 404; not silent display.

### 5.5 Section D — NBB/ZBB Awareness (Q41–Q47, role-gated)

> **Project context:** No Balance Billing / Zero Balance Billing awareness. Role-gated like Section C.

Same testing pattern as 5.4 — verify visibility per role; verify gating per `F2-Skip-Logic.md`.

### 5.6 Section E1 — BUCAS (Q48–Q52, role + facility-gated)

> **Project context:** BUCAS (Botika sa Barangay / specific PhilHealth program — verify against project glossary). Role + facility-type-gated.

**Happy:**
- E1.H1 — When persona role + facility match the gate, items render in expected order.

**Error:**
- E1.E1 — When persona is gated off, section is hidden.
- E1.E2 — Cross-check: if facility type changes (e.g., DH vs RHU), gate behavior should match `F2-Skip-Logic.md`. Test with DEMO-HCW-006 (DH-INFANTA, Physician) vs DEMO-HCW-001 (RHU-QC-1, Physician) and note differences.

### 5.7 Section E2 — GAMOT (Q53–Q55, role + facility-gated)

Same pattern as E1.

### 5.8 Section F — Referrals & Satisfaction (Q56–Q62)

> **Project context:** 7 items on referral patterns and satisfaction with the referral system. Not role-gated — visible to all.

**Happy:**
- F.H1 — Walk every item; confirm singles render single-select, multis render multi-select.

**Error:**
- F.E1 — Cross-field rules per `F2-Cross-Field.md` — exercise any rules surfaced there (e.g., if referral count > 0, follow-up satisfaction question must be answered).

### 5.9 Section G — KAP on Fees (Q63–Q90, physician/dentist only, facility-type splits)

> **Project context:** Knowledge / Attitudes / Practice on fees. Largest section (28 items). Only visible to Physician/Doctor or Dentist roles. Has facility-type-split variants for DOH-retained vs public non-DOH-retained vs other.

**Happy:**
- G.H1 — Test with DEMO-HCW-001 (Physician/Doctor) — Section G appears with full content.
- G.H2 — If a Dentist persona is added to the seed (or coordinator provisions one), test the Dentist variant.

**Error:**
- G.E1 — Test with DEMO-HCW-004 (Pharmacist) — Section G must be **hidden**.
- G.E2 — Verify facility-type split: DEMO-HCW-001 (RHU-QC-1) vs DEMO-HCW-006 (DH-INFANTA) should see different Q70-ish range items per spec — confirm against `F2-Spec.md` Section G facility-split notes.

### 5.10 Section H — Task Sharing (Q91–Q95)

> **Project context:** 5 items on task delegation patterns within the facility. Not role-gated.

Standard testing — verify each item, validation rules per spec.

### 5.11 Section I — Facility Support (Q96–Q97)

> **Project context:** 2 items on facility-level support (training, supervision). Quick section.

Standard testing.

### 5.12 Section J — Job Satisfaction (Q98–Q125, two matrix grids + terminal branch)

> **Project context:** Largest section (27 items, with Q108 omitted). Two matrix grids — verify they render correctly on tablet (matrix grids are the highest-risk type for layout regressions on small screens). Section ends with a terminal branch leading to END OF SURVEY.

**Happy:**
- J.H1 — Walk both matrix grids: rows × columns rendering, every cell selectable, no overlap or scroll bug.
- J.H2 — Final terminal branch leads to a "you're done" / "Submit" affordance.

**Alternative:**
- J.A1 — On a matrix, fill some cells, advance to next item, come back — values preserved in the right cells.

**Error:**
- J.E1 — Matrix layout breaks on tablet portrait → file with screenshot. (Memory: FX-017 touch-target gap is a known issue.)
- J.E2 — Submit a matrix with some cells unfilled — confirm whether per-row required-validation triggers (per spec) or whether matrix is fully optional.

### 5.13 Submission + Sync

#### Happy

- S.H1 — Final Submit while online → green check / thank-you screen.
- S.H2 — Within 10s, the row appears in F2_Responses (coordinator confirms via Admin Portal → Data → Responses).
- S.H3 — `source_path = self_admin`; `submission_lat` / `submission_lng` populated if you allowed geolocation; `app_version = 2.0.0`.

#### Alternative

- S.A1 — Submit while **offline** (DevTools Offline). Expect: queued state, "will sync when online." Toggle online; expect auto-sync within ~30s.
- S.A2 — Refresh after submit → thank-you state persists; no duplicate row.
- S.A3 — Submit with geolocation **denied** → completes; lat/lng empty.

#### Error

- S.E1 — Toggle offline immediately after Submit, before sync completes. Wait 60s. Expect: submission lands in DLQ; coordinator confirms via Admin Portal.
- S.E2 — Tap Submit twice rapidly → only one F2_Responses row (deduped by `client_submission_id`).

### 5.14 Cross-cutting tablet UX

- **Tablet portrait** — every screen renders; touch targets are reachable. (Note FX-017: some touch targets <44px on tablet outside the sidebar — known issue.)
- **Tablet landscape** — same.
- **Service Worker** — second visit loads faster (cache hit). Offline visit shows graceful state.
- **Browser refresh mid-survey** — values restore.
- **Browser back button** — returns to previous section without losing values.

---

## 6. Bug Filing Protocol

**One bug per issue.** File on GitHub Issues with the label below. For **blockers** (can't enroll, can't submit, data lost), ALSO ping `#f2-pwa-uat` Slack so it surfaces faster than the daily triage cycle.

### Issue title format

`[F2 UAT R2 PWA] <short title>` — e.g., `[F2 UAT R2 PWA] Q4 accepts age=17 (spec says min 18)`

### Issue body template

```markdown
**Tester:** Shan
**Date / time (PHT):** 2026-05-XX HH:MM
**Device + browser + OS:** Tablet name / Chrome version / Android or iPad version
**Severity:** blocker | high | medium | low
**Scenario ID:** A.2.E2 (from Section 5 of this guide)
**HCW used:** DEMO-HCW-004
**Question / Section:** Q4 / Section A

**Steps to reproduce:**
1. …
2. …
3. …

**Expected:** (cite spec line if applicable — e.g., `F2-Spec.md` Section A → Q4 says "min 18")

**Actual:**

**Screenshot / video:** (attach)

**Console / Network evidence:** (paste relevant errors, request IDs)
```

### Label

`from-uat-round-2-2026-05`

### Severity guidance

| Severity | Definition | Channel |
|---|---|---|
| **Blocker** | Survey can't enroll · can't submit · data lost · prod down | GitHub + Slack `#f2-pwa-uat` |
| **High** | Major flow broken with workaround · visibly incorrect data · skip-logic regression | GitHub |
| **Medium** | Inconvenient bug · wrong copy · missing tooltip · cross-browser visual diff | GitHub |
| **Low** | Cosmetic · polish · low-frequency · UX nit | GitHub |

> **Spec divergence vs PWA bug:** if the deployed PWA behavior contradicts `F2-Spec.md`, that's a **PWA bug** (file as such). If the PWA matches the spec but the spec itself feels wrong, that's a **spec bug** — file separately and tag the coordinator; spec changes go through the project lifecycle, not a quick patch.

---

## 7. Cadence

- **Daily triage** — coordinator reviews new issues each morning at standup; tags severity, assigns owner, sets target ship.
- **Blockers** — same-day patches when possible; you'll be asked to re-test on staging before the patch hits prod.
- **High** — next-day patches.
- **Medium / Low** — queue for Sprint 005 unless trivial (≤30 min fix).
- **Round closes** — when the issue list is drained or coordinator declares cutover. No fixed deadline; rolling.

---

## 8. After Round 2 Closes

- Coordinator sweeps `from-uat-round-2-2026-05`-labeled issues and writes a one-page summary at `deliverables/F2/PWA/qa-reports/uat-round-2-summary-2026-05-XX.md`.
- All `DEMO-*`-tagged seed data is removed via `purgeDemoData()` on the prod AS project.
- Your tester credentials (if any provisioned) stay for ongoing UAT; revoke as needed.
- v2.0.1 patch ships with the bundle of fixes; Round 3 uses an updated guide.

---

*Drafted 2026-05-04 by Carl Patrick L. Reyes. Test scenario inventory adapted from `deliverables/F2/F2-Spec.md` (verbatim questionnaire) + `deliverables/F2/F2-Skip-Logic.md` (gating) + `deliverables/F2/F2-Validation.md` (rules) + `deliverables/F2/F2-Cross-Field.md` (cross-field constraints). File issues against the GitHub repo with the label above; coordinator monitors daily.*
