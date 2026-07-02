# F2 PWA — UAT Round 5 (HCW Survey side) — Tester Guide

**Round:** 5 (testers' numbering) · **Type:** Regression re-test (production v2.1.0)
**Drafted:** 2026-06-21 · **Opens:** 2026-06-22 (Mon AM) · **Closes:** 2026-06-27 (Fri PM)
**Side:** HCW survey (PWA enrollment + full form completion + submission + sync)
**Companion guide:** `docs/F2-PWA-UAT-Round-5-Admin-Portal-Tester-Guide-2026-06.md` (Admin Portal side — all four testers walk both)
**Coordinator:** Carl Patrick L. Reyes (Data Programmer)
**Window:** Opens Mon 2026-06-22 AM · Closes Fri 2026-06-27 PM

> **⚠️ Round 5 caveats (read first).** (1) **English-only mode is temporarily ON** (`VITE_ENGLISH_ONLY`, since 2026-06-16) — the **language switcher is hidden**, so do **not** test the 7-locale switching this round (the locales are still wired, just hidden). (2) **Worker-deploy gap:** CI's version-stamped Worker deploy is currently failing, so a brand-new *backend* route may not be on staging — if a backend action 404s/500s, flag it but note it may be the deploy gap, not a code regression.

> **Project context.** This is the **DOH UHC Survey Year 2 — Healthcare Worker Survey**. Field rollout hands tablets to HCWs (nurses, midwives, physicians, pharmacists, etc.) at sampled health facilities. Rounds 1–3 were scripted scenario sweeps that found and fixed 90+ issues. **Round 5 is a full regression re-test of the shipped `v2.1.0` build** — a complete end-to-end walk of the live HCW survey on a realistic populated environment, the way fieldwork actually runs. The job is not to re-walk a checklist; it is to **run the survey the way fieldwork actually will** — enroll cold, complete the whole form under real conditions (offline, interruptions, real devices), submit, and watch it sync — and surface anything that would slow, confuse, or break a real enumerator or HCW.

> **Why this round exists.** Round 3's fixes shipped as **v2.1.0** (2026-06-01) — a wave of ~30 closures including the survey-content changes from Dr. Myra Silva-Javier's 2026-05-21 decisions (Q47/Q110 "None", Q52 exclusivity, Q35 partial-date, Q36 multi-select, Q9-vs-Q4 hard block, Q39 option removal, Q125 new option). Those landed but have **never been walked end-to-end as a complete survey by a tester acting like a real respondent**. R5 is the rehearsal that proves the whole instrument holds together — content, flow, offline, sync — before it meets a real HCW.

> **Scope of this guide.** HCW-side only — what an enumerator/HCW sees on the tablet. Admin-side monitoring (Responses, Sync Report, Map, DLQ, reconciliation) has its own companion guide; all four testers walk both, because in a real field day the same people who hand out tablets also monitor the dashboard.

---

## ⚠️ Coordinator pre-flight (Carl — do BEFORE opening the round)

R5 runs on **staging**, not production, by design:

- **Why staging:** the dry-run generates dozens of throwaway submissions. Those must NOT land in the production `F2_Responses` sheet that real fieldwork will use. Staging also lets us run `seedDemoData()` (the prod guard rail refuses it), giving every tester a fully-populated, story-telling environment — 3 facilities, 12 HCWs, 9 prior responses, a DLQ entry, files, audit history.
- **If you'd rather dry-run on prod instead:** seed-demo will refuse; you'd mint fresh tokens via Admin Portal → Data → HCWs → **Create HCW** (prod-signed JWTs), and skip the seed. Doable, but you then pollute prod and have to `purgeDemoData` after. Staging is the recommended target. Flip the URLs throughout both guides if you choose prod.

**Steps (≈10 min, from `docs/superpowers/runbooks/2026-05-04-seed-demo-data.md`):**

1. **Confirm staging carries v2.1.0+.** Push/redeploy `staging` to match `main` if it's behind, so testers exercise the shipped R3 fixes. Staging header should read `v2.1.0 · spec 2026-04-17-m1` or later.
2. **Re-seed clean:** in the **`F2-PWA-Backend-Staging`** Apps Script project, run `purgeDemoData()` then `seedDemoData()`. Confirm the log shows `hcws: {added: 12}` and `responses: {added: 9}`. (Guard rail requires `PROP_ENV=staging` — already set; see runbook Step 2.)
3. **Mint fresh enrollment URLs** for the test HCWs below: Admin Portal → Data → HCWs → **Reissue Token** on each assigned HCW → copy the enrollment URL. (Reissue mints a fresh 30-day JWT, invalidating any stale one.)
4. **Paste the fresh URLs into Section 3** of this guide (the `‹PASTE …›` cells). Tokens are staging-signed and resolve only against staging.
5. **Create the round tracking issue** `[E6-PWA-NNN] UAT Round 5 (R5) — HCW + Admin, staging, v2.1.0` and the label **`from-uat-round-5-2026-06`** (color it distinctly). Drop the issue # into Section 1.
6. **Announce** in `#f2-pwa-uat` with the open/close window.

> Until steps 1–6 are done, this guide is a draft. Don't send it to testers with empty token cells.

---

## 1. Quick Reference

| Item | Value |
|---|---|
| **Staging PWA URL** | https://staging.f2-pwa.pages.dev |
| **Target prod version under test** | v2.1.0 (`v2.1.0 · spec 2026-04-17-m1`) — staging must be deployed to match |
| **Spec — verbatim question text + validation rules** | `deliverables/F2/F2-Spec.md` (and `deliverables/F2/PWA/app/spec/F2-Spec.md`) |
| **Skip logic + branching** | `deliverables/F2/F2-Skip-Logic.md` |
| **Cross-field validation** | `deliverables/F2/F2-Cross-Field.md` |
| **What changed in v2.1.0 (read before testing)** | `deliverables/F2/PWA/app/CHANGELOG.md` → v2.1.0 section |
| **Bug repo** | https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues |
| **Bug-filing label** | `from-uat-round-5-2026-06` (coordinator creates before opening) |
| **Slack channel (blockers + daily check-in)** | `#f2-pwa-uat` on `aspsi-doh-uhc-survey2.slack.com` |
| **R5 tracking issue** | `#722` — `[E6-PWA-722]` |

> Testers don't need any login on the HCW survey side — the tablet token in your enrollment URL is your authentication.

---

## 2. Tester Roster

Shan, Kidd, and Marriz (from Round 3), plus **Aly** (new RA). In a real field day these are your roles; play them.

| Tester | Role | Field persona for the dry-run | Test devices |
|---|---|---|---|
| **Shan** (ASPSI RA) | Primary enumerator | **Pharmacist/Dispenser** — exercises the role-gated-OFF path (no C/D/E1/E2/G) | Real Android tablet primary; iPhone Safari + desktop Firefox secondary |
| **Kidd** (ASPSI main RA) | Enumerator (full-coverage persona) | **Physician/Doctor** — MUST pick Physician at role-select to exercise the all-sections path incl. Section G | Real iPad primary; low-end Android phone + desktop Edge secondary |
| **Marriz** (ASPSI Data Manager) | Enumerator + ops-monitor | **Nurse** — covers C/D/E1/E2 (G hidden); ALSO owns the live Admin-side monitoring during the dry-run (see companion guide) | Whatever's available — variety welcome |
| **Aly** (ASPSI RA, new) | Enumerator | **Midwife** — covers C/D/E1/E2 incl. Q44 NBB/ZBB (G hidden); adds the Midwife role-gating path | Whatever's available — variety welcome |

> **All four complete the WHOLE survey at least once for their persona.** A dry-run is not spot-checks; it's the full instrument start to finish. Persona variety means Pharmacist / Physician / Nurse / Midwife hit different role-gated paths, so between the four you cover every section. Marriz additionally keeps the Admin dashboard open as she/the team will on a real field day.

---

## 3. Your Test HCW Assignments (FRESH staging tokens — minted at round open)

> Staging tokens **minted 2026-06-09** (30-day TTL → ~2026-07-09). They resolve only against `staging.f2-pwa.pages.dev`. The R2/R3 prod tokens expired 2026-06-03 and do not apply.

### Primary assignments

| Tester | HCW ID | Persona (from seed) | Facility | Role-gating coverage | Enrollment URL |
|---|---|---|---|---|---|
| **Shan** | `DEMO-HCW-004` | Pharmacist/Dispenser | DEMO-FAC-RHU-QC-1 (NCR / QC RHU) | Sections A, B, F, H, I, J (C/D/E1/E2/G gated off) | `https://staging.f2-pwa.pages.dev/enroll?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJlZDdkYjAxNC04MTkzLTRmYzctYTdmZC1hYjFiODY1Yjc5ZGYiLCJ0YWJsZXRfaWQiOiJlNGFkZTBjZC1hMDI1LTQ1NWQtODYxMi01ZWE5MTZhMjhjZDUiLCJmYWNpbGl0eV9pZCI6IkRFTU8tRkFDLVJIVS1RQy0xIiwiaWF0IjoxNzgwOTU5NjYzLCJleHAiOjE3ODM1NTE2NjN9.GkjYeR0opTw1oNU5occHobB_Uvlscd4rNzI71BGnr_Q` |
| **Kidd** | `DEMO-HCW-007` | Physician/Doctor (pick at role-select) | DEMO-FAC-DH-INFANTA (IV-A District Hospital) | All sections A–J | `https://staging.f2-pwa.pages.dev/enroll?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiI3MDljMGM3Ni03MjRiLTRjYWEtOTJjOS1jZGFiYjE0YjMzNjciLCJ0YWJsZXRfaWQiOiIxYThiZGRkOS04MDY1LTRjMGUtYjY0Mi05MTMxMTMzOTQ2MzUiLCJmYWNpbGl0eV9pZCI6IkRFTU8tRkFDLURILUlORkFOVEEiLCJpYXQiOjE3ODA5NTk2NjgsImV4cCI6MTc4MzU1MTY2OH0.4rzLX5Ab9gfoWPvPdrjl4A3GfLWfFcf79uqIknTo1eY` |
| **Marriz** | `DEMO-HCW-002` | Nurse | DEMO-FAC-RHU-QC-1 (NCR / QC RHU) | A, B, C, D, E1, E2, F, H, I, J (Section G hidden — Nurse) | `https://staging.f2-pwa.pages.dev/enroll?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJjMzVlMjc5My01MjM1LTQ1NGEtOWQzNy02M2E2NDE4OWIxYmMiLCJ0YWJsZXRfaWQiOiI4MjIxNzNiNi04NzA0LTQzMjctOWQwNy01ZWQ3NjI0ZDg2MjIiLCJmYWNpbGl0eV9pZCI6IkRFTU8tRkFDLVJIVS1RQy0xIiwiaWF0IjoxNzgwOTU5NjcyLCJleHAiOjE3ODM1NTE2NzJ9.V0X1VVxnLzU1jXY-6qOMCO-0ntuVXuw3Bdo3Fyf6mrI` |
| **Aly** | `DEMO-HCW-005` | Midwife (pick at role-select) | DEMO-FAC-RHU-QC-1 (NCR / QC RHU) | A, B, C, D, E1, E2, F, H, I, J (Section G hidden — Midwife) | `https://staging.f2-pwa.pages.dev/enroll?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiI5MmNkNjdjYS1lOTJkLTRkM2MtOTk0OC01OTg4ZmYxYzEyMDgiLCJ0YWJsZXRfaWQiOiIwODFkNDQ2NS05YWYzLTQzNTktYjlmMi0xNmI1MTVmZGM0MGEiLCJmYWNpbGl0eV9pZCI6IkRFTU8tRkFDLVJIVS1RQy0xIiwiaWF0IjoxNzgwOTc2MzcwLCJleHAiOjE3ODM1NjgzNzB9.J9NnujEkV0HBafAJJWNKN8QvcQ9Q0iWao6LMBm1vvAU` |

### Second-pass HCWs (for the multi-respondent-per-facility realism in 5D)

To rehearse what a facility actually generates — several HCWs submitting from one site — each tester also enrolls a **second** HCW from the seed and completes at least Sections A–B on it. Use any of `DEMO-HCW-001/003/005/006/008/009/010/011/012`. Coordinator pastes 1–2 spare URLs per tester here:

| Tester | Spare HCW ID(s) | Enrollment URL(s) |
|---|---|---|
| **Shan** | `DEMO-HCW-001` | `https://staging.f2-pwa.pages.dev/enroll?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiI2ZmUyMDhmZi1iNTljLTRkOTItYmE0OC0wZWYzNGZiN2ZhNjgiLCJ0YWJsZXRfaWQiOiJkYWJjM2I3Ny1jYWVhLTQ3YjMtYTNjOC03MWY2YjY0MTU2YWMiLCJmYWNpbGl0eV9pZCI6IkRFTU8tRkFDLVJIVS1RQy0xIiwiaWF0IjoxNzgwOTU5Njc1LCJleHAiOjE3ODM1NTE2NzV9.8ckq8O3pwrii0yMkFP23Jl-oMz98T-QHf_QYHo6kYB8` |
| **Kidd** | `DEMO-HCW-003` | `https://staging.f2-pwa.pages.dev/enroll?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiIxMDZmNjA4ZC0yNzhlLTQ5M2EtOWRlYS05NjI1NDk5YmM3NDEiLCJ0YWJsZXRfaWQiOiJhZjIxMWIyYi1iMmYwLTRlZTktODViZS1jMzgzODdlMmE1ODIiLCJmYWNpbGl0eV9pZCI6IkRFTU8tRkFDLVJIVS1RQy0xIiwiaWF0IjoxNzgwOTU5Njc5LCJleHAiOjE3ODM1NTE2Nzl9.wEB7WP330JyfqIJ5CL0X_gmLNHCnxpEi1DoirjDfUF0` |
| **Marriz** | reuse `DEMO-HCW-001` / `DEMO-HCW-003` above (both QC-RHU) | — |

> **DO NOT share these URLs publicly.** Each token mints a session for that specific HCW. Coordinator can revoke/reissue if one leaks.

---

## 4. Pre-Flight Checks (each tester, before testing)

1. **Confirm staging + version.** Open `https://staging.f2-pwa.pages.dev`. Header should read `v2.1.0 · spec 2026-04-17-m1` (or later). If it shows an older version, hard-refresh (Ctrl+Shift+R / pull-to-refresh) so the service worker updates. If it still lags, ping the coordinator — staging may need a redeploy.
2. **Open DevTools** (F12 on desktop; Chrome remote debugging from a paired desktop for tablets). Keep Network + Console tabs visible — you'll toggle Offline and capture errors from here.
3. **Skim the references once:** the **v2.1.0 CHANGELOG section** (so you know what's new), plus `F2-Spec.md` + `F2-Skip-Logic.md` for the sections your persona walks.
4. **Confirm your token works:** open your primary enrollment URL — the token should auto-prefill the textbox and enable Verify immediately (shipped 2026-05-12). Click Verify → advance to role-select / Section A. (Empty textbox after opening the URL = regression; file it.)

---

## 5. The Dry-Run

Run it as a field day, in order. **5A → 5B → 5C → 5D** is one continuous pass per persona; **5E** is a short adversarial coda. Treat yourself as the enumerator *and* the HCW.

For anything that looks wrong, open the spec at the cited section to decide whether it's a **PWA bug** (deployed code diverges from spec) or a **survey-design question** (the spec/wording itself is contested — those get routed to the survey team, not fixed as code). When in doubt, file it and say which you think it is.

### 5A — Cold enrollment (act like Day 1 of fieldwork)

**What you're rehearsing:** receiving the tablet and onboarding an HCW from a clean slate.

- **5A.1** On a real device, open your primary enrollment URL **in a fresh/incognito context** (or clear site data first). Expect: token auto-prefilled, Verify enabled, one tap → role-select / Section A. Time it — note how many seconds from tap to first question on a real tablet / a low-end phone.
- **5A.2** At the role-select screen, pick your persona's role (Shan→Pharmacist, Kidd→Physician, Marriz→Nurse, Aly→Midwife). Confirm the section sidebar immediately reflects role-gating (e.g. Shan sees no C/D/E1/E2/G; Kidd sees all; Marriz/Aly see C/D/E1/E2 but not G).
- **5A.3** Enroll your **second** HCW (Section 3 spare) the same way on the same device. Expect: a clean switch — no leftover answers from the first HCW bleeding into the second. (This is what happens when an enumerator finishes one HCW and starts the next.)

### 5B — Full questionnaire completion under field conditions

**What you're rehearsing:** an HCW completing the entire survey in a real facility — not on perfect wifi.

- **5B.1 (full happy walk):** Complete **every section your persona sees, end to end**, with plausible real answers. Don't rush past validation — when the form blocks you, confirm the message is clear and correct.
- **5B.2 (offline stretch):** Partway through (around Section C/D for full personas, Section B for Pharmacist), DevTools → Network → **Offline**. Keep answering. Expect: no error banners, answers save locally, you can keep advancing.
- **5B.3 (interruption + resume):** Mid-section, close the tab (simulate the HCW stepping away for a patient). Reopen `staging.f2-pwa.pages.dev`, re-paste your token if prompted. Expect: form resumes at the last-saved point, no data loss.
- **5B.4 (force-quit):** Once during the walk, fully kill the browser/app and reopen. Expect: same clean resume.
- **5B.5 (rotation, tablets):** Rotate the tablet to landscape mid-form at least once. Expect: layout reflows cleanly; the Section J matrix grows to fit, no page-level horizontal scroll.

### 5C — Content correctness spot-checks (v2.1.0 / Myra 2026-05-21 changes)

**What you're rehearsing:** confirming the questionnaire content that changed actually reads and behaves as the survey team decided. Check these **as you reach them** during 5B — they're inline, not a separate pass. Compare against `F2-Spec.md` verbatim wording.

| # | Q | What shipped in v2.1.0 | Confirm |
|---|---|---|---|
| **5C.1** | **Q47** (Section D) | New **"None"** option, standalone | Selecting "None" auto-clears all other selections; selecting any other option clears "None". Multi-select retained otherwise. (Nurse/Physician personas.) |
| **5C.2** | **Q110** (Section J) | New **"None"** option, standalone | Same exclusive behavior as Q47. (All personas reach Section J.) |
| **5C.3** | **Q52** (Section E) | **"No significant impact"** made mutually exclusive with the top options | Selecting "No significant impact" clears + disables the top options; selecting a top option disables "No significant impact". Multi-select retained among the others. (Nurse/Physician.) |
| **5C.4** | **Q125** (Section J) | (i) New option **"Transfer to a new facility (in the Philippines) with the same role"**; (ii) **"Retire"** now standalone (auto-clears others) | New option present + worded verbatim; "Retire" auto-clears others; multi-select retained for the rest. ⚠ If the new option text or its translation looks off, that's a **survey-design/translation** item — flag, don't fix. |
| **5C.5** | **Q35** (Section C) | Year required; **month + day each independently optional** (Don't-Know allowed per component) | Year blank → blocked; month and/or day blank or DK → allowed to advance. (Physician.) |
| **5C.6** | **Q36** (Section C) | Switched **single-answer → multi-select**, with re-derived skip into Q39 | Multiple reasons selectable; routing into Q39 fires when any applying reason is chosen and skips Q39 when only the non-applying reason is chosen. (Physician.) |
| **5C.7** | **Q9 vs Q4** (Section A) | **Hard block:** `tenure_years < (age − 20)` | Enter age=40, tenure years=25 (i.e. ≥ age−20) → blocked with "Years of service must be less than age minus 20." Enter a valid combo → proceeds. (All personas.) |
| **5C.8** | **Q39** (Section C) | Removed the **"Not a physician/dentist"** option from the value set | That option no longer appears in Q39. (Physician.) |
| **5C.9** | **Q11** (Section A) | **No change** — whole-hour integers only (Myra confirmed) | Decimals rejected; whole hours 1–24 accepted. (Confirms the close-as-designed call held.) |

> If any 5C item is **missing, mis-worded, or misbehaving**, file it referencing the v2.1.0 issue if you can (e.g. `Regression of #310` for Q47). Verbatim wording mismatches are high-value — flag them for the survey team.

### 5D — Submission + sync at field realism

**What you're rehearsing:** end of an HCW interview, and what the data team sees.

- **5D.1 (submit online):** Finish a full survey and Submit while online. Expect: clear success indicator (not silent, not "no submission yet"). Note the time.
- **5D.2 (submit offline → auto-sync):** On your second HCW, complete to the end while **offline**, hit Submit. Expect: a clear "queued / will retry when online" state. Then go back online. Expect: auto-sync within ~30s, success indicator appears.
- **5D.3 (multi-respondent-per-facility):** Coordinate so that **both QC-RHU personas (Shan + Marriz) submit from the same facility**. On the Admin side (companion guide 5B/5D), confirm both land and the Sync Report / Map show two submissions at one site — this is the realistic per-facility pattern.
- **5D.4 (confirm landing):** Tell the coordinator/Marriz your HCW ID + submit time. They confirm it appears in **Data → Responses** on staging with the right answers, and the response detail matches what you entered (especially your 5C answers). This closes the loop a real field day depends on.

### 5E — Adversarial coda (the things most likely to bite in the field)

A short, sharp pass — not exhaustive. Pick the ones that fit your device.

- **5E.1 (real respondent text):** In any "Other (specify)" field, type special chars `< > & " ' /` + an emoji (🏥) + a smart-quote phrase pasted from notes (`"hello" – world`). Expect: preserved exactly through save + submit; no HTML-escape display, no cruft.
- **5E.2 (number edges):** In Q4 (age) try `999`, `-1`, `0` → expect range validation / input filtering. In Q9 try `0` years + `0` months → expect the 0+0 block.
- **5E.3 (long text):** Paste a 500-char string into an open-text field → accepted, preserved on reload + submit.
- **5E.4 (day-later resume):** Save a draft mid-form, close everything, come back the next testing session, re-paste token → resumes at the draft point; token still valid (30-day TTL).
- **5E.5 (token mishaps):** Paste your token with trailing whitespace, then with the full `https://…?token=` URL prefix into the textbox → expect graceful handling or a clear "paste only the token" hint. Paste a truncated token → clear "invalid token signature" error.

---

## 6. Bug-Filing Format

Open a GitHub Issue at the bug repo for every finding. Template:

```
**Round 5 (dry-run) step:** 5A.x / 5B.x / 5C.x / 5D.x / 5E.x
**Type:** PWA bug  OR  survey-design/wording question (your best guess)
**Tester / persona:** Shan (Pharmacist) / Kidd (Physician) / Marriz (Nurse)
**Device:** Android tablet (model) / iPhone (model) / desktop Chrome / etc.
**HCW used:** DEMO-HCW-00X
**Section / Question:** Section X / QYY (or "enrollment" / "submission" / "matrix" / etc.)
**Expected:** [what the spec / step says should happen]
**Actual:** [what happened]
**Reproduction steps:**
  1. ...
  2. ...
**Severity:** critical / high / medium / low
**Field impact:** [would this slow/confuse/block a real enumerator or HCW? how badly?]
**Screenshot / video:** [attach if visual]
**Console errors / network failures:** [paste from DevTools]
```

Apply the label `from-uat-round-5-2026-06` to every R5 issue and link it to the tracking issue. Coordinator triages daily.

---

## 7. Triage Cadence

- **Daily check-in:** Coordinator posts to `#f2-pwa-uat` daily 09:00 PHT — new R5 findings, criticals, overnight fixes.
- **Mid-round sync:** If a critical surfaces that would block the real pretest (enrollment broken, submit failing, a content error heading to PSA), coordinator calls a same-day 15-min Slack huddle — don't wait for round close.
- **R5 close:** Friday 2026-06-27 PM. Coordinator reconciles the tracking issue; open items dispositioned (fix-now / next-sprint / route-to-survey-team / won't-fix-with-rationale). Findings that are survey-design/wording are routed, not coded.

---

## 8. Why this round matters

Rounds 1–3 were lab passes — scripted scenarios on desktop browsers, then on real devices. They were right for finding defects. **Round 5 is a regression rehearsal of the shipped build.** The live pretest is when actual HCWs at actual facilities meet this survey. Before the next pilot batch, we want one honest run-through that proves the shipped `v2.1.0` still holds:

- **A whole survey completes** for each role, not just isolated sections.
- **The v2.1.0 content changes read and behave as the survey team decided** — because a wording error caught here is cheap; the same error caught at PSA or in the field is not.
- **The offline → resume → sync loop holds** under the interruptions a real facility throws at it.
- **A facility's worth of submissions lands cleanly** and the data team can see it in real time.

If R5 runs clean, we walk into the pretest confident. If it doesn't, this is the last cheap place to find out. Thanks for testing — and treat it like the real day.
