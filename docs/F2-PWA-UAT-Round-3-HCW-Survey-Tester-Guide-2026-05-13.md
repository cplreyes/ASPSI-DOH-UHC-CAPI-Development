# F2 PWA — UAT Round 3 (HCW Survey side) — Tester Guide

**Round:** 3 (testers' numbering)
**Drafted:** 2026-05-11 · **Opens:** 2026-05-13 (Wed AM)
**Side:** HCW survey (PWA enrollment + form completion + submission)
**Coordinator:** Carl Patrick L. Reyes (Data Programmer)
**Window:** Opens Wed 2026-05-13 AM · Closes Fri 2026-05-15 PM (sprint close)

> **Project context.** This is the **DOH UHC Survey Year 2 — Healthcare Worker Survey**. Field rollout uses tablets handed to HCWs (nurses, midwives, physicians, etc.) at sampled health facilities. Round 3's job is twofold: **(a)** verify the three v1.2.0 features shipped 2026-05-01 (exclusive "I don't know" rule, "All of the above" auto-select rule, scale-style matrix) actually work in current prod (v2.0.0), and **(b)** stress-test what Round 2 didn't cover — offline behavior, real device matrix, edge data, resume after force-quit, and token edge cases.

> **Why this round exists.** The three R3 fixes (#266/#267/#268) shipped in v1.2.0 release on 2026-05-01 but the GH issues stayed open as a process gap. Code + unit tests confirm correctness; this round confirms in-form behavior on real devices with real testers. The new-scenarios bundle covers the gaps Round 2 (full-form happy/alt/error pass) didn't touch.

> **Scope of this guide.** PWA-side only — what an HCW sees on the tablet. No Admin Portal testing this round (Admin Portal stays at v2.0.1 from PR #136; no R3 cycle for it).

---

## 1. Quick Reference

| Item | Value |
|---|---|
| **Production PWA URL** | https://f2-pwa.pages.dev |
| **Current prod version** | v2.0.0 (header: `v2.0.0 · spec 2026-04-17-m1`) |
| **Spec — verbatim question text + validation rules** | `deliverables/F2/F2-Spec.md` |
| **Skip logic + branching** | `deliverables/F2/F2-Skip-Logic.md` |
| **Cross-field validation** | `deliverables/F2/F2-Cross-Field.md` |
| **Bug repo** | https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues |
| **Bug-filing label** | `from-uat-round-3-2026-05` (orange — coordinator creates before opening) |
| **Slack channel (blockers + daily check-in)** | `#f2-pwa-uat` on `aspsi-doh-uhc-survey2.slack.com` |
| **Release notes (v1.2.0 — what shipped)** | https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/releases/tag/v1.2.0 |
| **R3 sprint card** | https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/271 |

> Testers don't need any login on the HCW survey side — the tablet token is your authentication.

---

## 2. Tester Roster

| Tester | Role | Assignment | Test devices |
|---|---|---|---|
| **Shan** (ASPSI RA) | Primary tester | All Section 5 scenarios (verify + new) | Real Android tablet primary; iPhone Safari + desktop Firefox secondary |
| **Kidd** (ASPSI main RA) | Cross-coverage tester | All Section 5 scenarios (verify + new) | Real iPad primary; low-end Android phone + desktop Edge secondary |

> **Both testers walk both verify-shipped and new-scenarios sections.** Coverage breadth comes from device variety, not split assignments.

---

## 3. Your Test HCW Assignments (with embedded tokens — REUSED from Round 2)

The tokens minted for Round 2 (2026-05-04) are still valid until **2026-06-03** (30-day TTL). Use the same primary HCW from Round 2 unless you want to test a different role-gated path.

### Primary assignments

| Tester | HCW ID | Persona (from seed) | Facility | Role-gating coverage | Enrollment URL |
|---|---|---|---|---|---|
| **Shan** | `DEMO-HCW-004` | Garcia, Roberto · **Pharmacist/Dispenser** · Male · 29 | DEMO-FAC-RHU-QC-1 (NCR / QC RHU) | Sections A, B, F, H, I, J (no C/D/E1/E2/G — role-gated off) | `https://f2-pwa.pages.dev/enroll?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJkYmUzYTU0ZS03OTIzLTQzYjAtYTk4MS0yYmY1ODQzNGU3N2EiLCJ0YWJsZXRfaWQiOiI1MGE1M2QzYy02ZDE2LTRlYWYtODY3ZC0wNTFlMmEzYzJiZWQiLCJmYWNpbGl0eV9pZCI6IkRFTU8tRkFDLVJIVS1RQy0xIiwiaWF0IjoxNzc3ODg2OTE5LCJleHAiOjE3ODA0Nzg5MTl9.6ytd1Hu66lABXpCuEMdhgl4c3cIgIpLbkwnRTM8P36A` |
| **Kidd** | `DEMO-HCW-007` | (DH-INFANTA HCW — pick **Physician/Doctor** at role-select to exercise Section C/G) | DEMO-FAC-DH-INFANTA (IV-A District Hospital) | All sections A–J | `https://f2-pwa.pages.dev/enroll?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJmMjUzN2YzMy1mNTI2LTQ0ZDYtOGFiYS0yZmM3MzQxZDA0OTIiLCJ0YWJsZXRfaWQiOiI0YjliZDljYi04ZjBhLTQ1MTQtYTE4Yi00Y2ZlZjBmNjA0Y2MiLCJmYWNpbGl0eV9pZCI6IkRFTU8tRkFDLURILUlORkFOVEEiLCJpYXQiOjE3Nzc4ODY5NDEsImV4cCI6MTc4MDQ3ODk0MX0.GXkvyAuKYsDdfbG9PhaKKA1kYMv-jKAh6kAnDBmMVlE` |

> **For Section 5A (verify-shipped):** Kidd MUST pick **Physician/Doctor** at the role-select screen — Section C (Q32 select-all test) is role-gated, only visible to Physician/Nurse/Midwife. Shan's Pharmacist persona doesn't see Section C, so Shan exercises Q25 (Section B) + Section J matrix only for the verify pass.

### Spare HCWs (for re-test or fresh-start scenarios)

Same as Round 2 — see `docs/F2-PWA-UAT-Round-2-HCW-Survey-Tester-Guide-2026-05-04.md` Section 3 spares table for `DEMO-HCW-001/002/003/005/006/008` URLs.

> **DO NOT share these URLs publicly.** Each token mints a session for that specific HCW. If a token leaks, anyone with the URL can submit on behalf of that HCW. Coordinator can revoke/reissue if needed.

---

## 4. Pre-Flight Checks (do these before testing)

1. **Confirm prod version.** Open `https://f2-pwa.pages.dev` on your test device. Header should read `v2.0.0 · spec 2026-04-17-m1`. If it says `v1.x.x`, hard-refresh (Ctrl+Shift+R or pull-down refresh on tablet) — service worker may need to update.
2. **Open DevTools** (F12 on desktop, or Chrome remote debugging from a paired desktop for tablets). Network + Console tabs visible.
3. **Read these reference docs once before testing:**
   - `deliverables/F2/F2-Spec.md` — full questionnaire structure
   - `deliverables/F2/F2-Skip-Logic.md` — all role + facility-type gates
   - Round 2 guide for context on what was previously tested
4. **Confirm your token works:** open your primary URL above, click Verify token, advance to the role-select / Section A screen.

---

## 5. Test Scenarios

Two parts: **5A — Verify shipped (v1.2.0 patterns)** confirms three specific UX rules work as spec'd; **5B — New scenarios** stress-tests gaps Round 2 didn't cover.

For every bug you find, open the spec at the cited section to confirm whether it's a **PWA bug** (deployed code diverges from spec) or a **spec bug** (spec is wrong) — the fix path is different.

### 5A. Verify shipped (v1.2.0 patterns)

These three rules shipped in v1.2.0 (2026-05-01) but were never verified by testers — Round 2 closed before R3 features landed. This pass confirms they work in current prod.

#### 5A.1 — Q25 exclusive "I don't know" rule (Section B)

**What to verify:** In a multi-select question that includes "I don't know" as a choice, selecting "I don't know" clears all other selections; selecting any other choice clears "I don't know."

**Where to find it:** Section B, Q25 — *"Which of the following do you expect to change in your personal work as a health worker under UHC?"* (multi-select; appears for both Pharmacist and Physician roles, so both testers exercise this).

**Test steps:**
- **5A.1.H1 (Happy):** Select Salary + Working hours. Then select "I don't know." Expect: Salary + Working hours both clear; only "I don't know" remains checked.
- **5A.1.H2 (Happy):** With "I don't know" selected, click any other option (e.g., Number of patients). Expect: "I don't know" clears; only Number of patients remains checked.
- **5A.1.A1 (Alt):** Type into "Other (specify)" text field, then select "I don't know." Expect: "Other (specify)" checkbox clears, but the typed text in the companion field persists (Q25_other) — the multi-select array is wiped, the side-channel text field is not.
- **5A.1.E1 (Error):** Select "I don't know" then click Next/Save Draft. Expect: question accepted as answered; no validation error.

#### 5A.2 — Q32 select-all + exclusive (Section C, Physician/Nurse/Midwife only)

**What to verify:** "All of the above" auto-selects every non-exclusive choice; exclusive ("I don't know") still wins over select-all when clicked.

**Where to find it:** Section C, Q32 — *"Which of the following are included in the YAKAP/Konsulta package?"* (multi-select with both `isSelectAll: "All of the above"` and `isExclusive: "I don't know"`). **Section C is role-gated** — only visible to Physician/Nurse/Midwife. Kidd as Physician sees this; Shan as Pharmacist does NOT.

**Test steps:**
- **5A.2.H1 (Happy):** Click "All of the above." Expect: Pap smear, Mammogram, Lipid profile, Thyroid function test, Chest X-ray, Low-dose Chest CT scan, Dental services all auto-check; "All of the above" stays checked; "I don't know" stays unchecked.
- **5A.2.H2 (Happy):** With "All of the above" checked, uncheck Mammogram. Expect: Mammogram unchecks AND "All of the above" auto-unchecks (the "all" claim is no longer accurate); the other 6 stay checked.
- **5A.2.H3 (Happy):** With "All of the above" checked, click "I don't know." Expect: all 7 services unselect, "All of the above" unselects, only "I don't know" remains.
- **5A.2.H4 (Happy):** With "I don't know" checked, click "All of the above." Expect: "I don't know" clears; all 7 services + "All of the above" check.
- **5A.2.H5 (Happy):** Uncheck "All of the above." Expect: all 7 auto-selected services clear; "I don't know" stays whatever it was (likely still unchecked).

#### 5A.3 — Section J matrix grids (Q98–Q125, Job Satisfaction)

**What to verify:** Consecutive scale-style questions sharing the same answer choices render as a matrix table (one statement per row, shared answer columns) instead of stacked one-per-page.

**Where to find it:** Section J, *"Job Satisfaction."* Q98–Q125 contains **two matrix grids** (per #119 R2 issue) where each row is a statement (e.g., *"I am satisfied with my salary"*) and the columns are a Likert scale (Strongly disagree / Disagree / Neutral / Agree / Strongly agree).

**Test steps:**
- **5A.3.H1 (Happy / desktop):** On desktop browser (≥768px wide), open Section J. Expect: questions render as a `<table>` with statement column on the left and 5 Likert columns across the top. Each row has 5 radio buttons. Header row shows "Statement | Strongly disagree | Disagree | Neutral | Agree | Strongly agree."
- **5A.3.H2 (Happy / mobile):** On tablet portrait or phone (<768px), open Section J. Expect: matrix collapses to stacked card-per-statement layout (statement above, radio choices in a horizontal flex row below). NOT the desktop table.
- **5A.3.H3 (Happy):** Click a radio in row 1 (e.g., "Agree" for *"I am satisfied with my salary"*). Expect: only that radio activates; other rows unchanged. Click "Strongly agree" in same row. Expect: previous selection in row 1 clears, "Strongly agree" activates (mutual exclusion within a row, independent across rows).
- **5A.3.A1 (Alt):** Try to navigate to next section without answering all rows. Expect: validation error highlights any unanswered row (required-by-default per spec).
- **5A.3.E1 (Error):** On tablet landscape, check that the matrix doesn't horizontal-scroll-clip the rightmost column ("Strongly agree"). If columns clip, file a bug.

### 5B. New scenarios (Round 2 didn't cover)

Round 2 walked the happy-path form thoroughly. These scenarios stress-test what an HCW might actually do in a real facility with real connection issues.

#### 5B.1 — Offline behavior

**What to verify:** Form continues to work without network; resubmit succeeds when connection returns.

- **5B.1.H1:** Enroll while online (token verifies), advance to Section A. Open DevTools → Network → toggle Offline. Continue answering Section A. Expect: form fills/saves locally without network errors; no error banners.
- **5B.1.H2:** Continue to Section B–F while offline. Expect: progress through all sections, no submission yet.
- **5B.1.H3:** Hit Submit while offline. Expect: a clear "queued for sync" or "will retry when online" indicator (NOT a hard error or silent failure).
- **5B.1.A1:** Turn Network back online. Expect: queued submission auto-syncs within ~30 seconds; success indicator appears. Verify in admin (coordinator can confirm) that the response landed in F2_Responses sheet.
- **5B.1.E1:** Go offline mid-section, refresh the browser tab. Expect: form state restores to where you were (last save point); no data loss.
- **5B.1.E2:** Go offline, kill the browser, reopen. Expect: returning to `f2-pwa.pages.dev` loads the last-saved state (per spec §10.4 — token NOT persisted to localStorage; you'll need to re-paste it from your enrollment URL).

#### 5B.2 — Device matrix (real devices, not emulation)

**What to verify:** Form renders + submits correctly across the real device variety field testers will use.

- **5B.2.H1 (Real Android tablet):** Walk Section A → Section B → submit a draft on a 10"+ Android tablet (Chrome, Edge, or Samsung Internet). Verify: text fields not too small to tap; radio buttons hit reliably; matrix in Section J doesn't overflow; submit works.
- **5B.2.H2 (Low-end Android phone):** Same walk on a low-end / older Android phone (e.g., 5–6" screen, 2GB RAM, Chrome). Verify: app loads in <10s; doesn't crash; form fits the small viewport (mobile fallback layouts work); no layout breakage.
- **5B.2.H3 (iPhone Safari):** Same walk on iPhone Safari. Verify: PWA install prompt works (or at least doesn't break); form interactions work; no Safari-specific layout bugs.
- **5B.2.H4 (Firefox mobile):** Same walk on Firefox mobile (Android). Verify: feature parity with Chrome.
- **5B.2.E1 (Tablet landscape):** Rotate any tablet to landscape mid-form. Expect: layout reflows cleanly; no text overflow; matrix table grows to fill width but doesn't horizontal-scroll on the page itself.

#### 5B.3 — Edge data

**What to verify:** Form handles unusual but valid input without crashing or corrupting.

- **5B.3.H1 (Long text):** In any "Other (specify)" or open-text field, paste a 500-character string. Expect: accepted; preserved on save+reload; submission carries the full text.
- **5B.3.H2 (Special chars):** Type `< > & " ' \ / @ #` and emoji (🏥 👩‍⚕️) into a text field. Expect: characters preserved exactly (no HTML-escape display, no character substitution).
- **5B.3.H3 (Word paste):** Copy text from MS Word (with smart-quote curly characters `"hello"` and en-dashes `–`), paste into a text field. Expect: characters preserved as-is; no formatting cruft injected.
- **5B.3.H4 (Whitespace):** Type leading + trailing spaces in text fields. Expect: accepted (the spec doesn't require trim); on submission, document whether spaces are preserved or trimmed (note in your report).
- **5B.3.E1 (Number overflow):** In Q4 (age) try entering `999`. Expect: validation error per range rules. Try `-1`. Expect: blocked at input (the keypad already filters non-numeric). Try `0`. Expect: validation error if min is set ≥1.
- **5B.3.E2 (Date overflow):** If any date picker is present, try a date in the year 1800 or 2200. Expect: validation error or the picker constrains to a sensible range.

#### 5B.4 — Resume after interruption

**What to verify:** Form survives mid-form interruptions like an HCW closing the tab to handle a patient.

- **5B.4.H1 (Soft close):** Mid-form (e.g., halfway through Section D), close the tab. Reopen `f2-pwa.pages.dev` in a new tab. Re-paste your token. Expect: form resumes at the last-saved state (probably the last question you advanced past, or the start of the section you were on).
- **5B.4.H2 (Hard close):** Mid-form, force-quit the browser (alt-F4 / swipe-up to kill). Reopen. Expect: same resume behavior; no data loss for items already saved.
- **5B.4.H3 (Day-later resume):** Save Draft mid-form. Close everything. Wait at least an hour. Reopen + re-paste token. Expect: form resumes at the saved draft point; token still valid (within 30-day TTL).
- **5B.4.A1 (Cross-device resume):** Save Draft on tablet. Open the same enrollment URL on a different device (e.g., desktop Chrome). Expect: this is **NOT supported** — each token binds to one tablet (per spec). Document what the second device shows (probably re-enrollment from scratch, OR an error).
- **5B.4.E1 (Stale draft):** If you've been mid-form for 2+ days without sync, check whether the local draft is still loadable.

#### 5B.5 — Token edge cases

**What to verify:** Token-paste handles real-world copy-paste mishaps.

- **5B.5.H1 (Clean paste):** Paste your token cleanly into the Step 1 textarea. Expect: Verify button enables; click → Step 2.
- **5B.5.A1 (Trailing whitespace):** Copy your token + 1–2 trailing spaces (common when copy-paste from email). Paste. Expect: Verify still succeeds (whitespace gets trimmed) OR the Verify button greys out with a clear hint.
- **5B.5.A2 (Multi-line paste):** Copy the entire enrollment URL (including `https://...?token=` prefix) and paste into the token textarea. Expect: app extracts the token portion OR shows a clear error like "Paste only the token, not the full URL."
- **5B.5.E1 (Truncated token):** Paste a token with the last ~20 characters chopped off. Expect: Verify fails with a clear error like "Invalid token signature."
- **5B.5.E2 (Reused/already-enrolled token):** Use a token that's already been enrolled on a different device. Expect: either accepts and rebinds OR shows a clear "Already enrolled elsewhere" message. Document which.
- **5B.5.E3 (Expired token):** All current DEMO tokens expire 2026-06-03. Don't worry about this in R3 unless you're testing past that date.

---

## 6. Bug-Filing Format

For every bug you find, open a GitHub Issue at the bug repo. Use this template:

```
**Round 3 scenario:** 5A.x.X1 / 5B.x.X1 / etc.
**Tester:** Shan / Kidd
**Device:** Android tablet (model) / iPhone (model) / desktop Chrome / etc.
**HCW used:** DEMO-HCW-00X
**Section / Question:** Section X / QYY (or "matrix" / "token paste" / etc.)
**Expected:** [what the spec / scenario says should happen]
**Actual:** [what happened]
**Reproduction steps:**
  1. ...
  2. ...
**Severity:** critical / high / medium / low
**Screenshot / video:** [attach if visual]
**Console errors / network failures:** [paste from DevTools if any]
```

Apply the label `from-uat-round-3-2026-05` to every R3 bug. Coordinator triages daily.

---

## 7. Triage Cadence

- **Daily check-in:** Coordinator posts a short status to `#f2-pwa-uat` daily 09:00 PHT (Wed/Thu/Fri) — count of new R3 bugs filed, any critical blockers, fixes-shipped overnight.
- **Sync-up call:** If 5+ open R3 bugs by Thu EOD, coordinator schedules a 15-min Slack huddle Fri AM to triage in real time.
- **R3 close:** Friday 2026-05-15 PM. Coordinator marks #271 closed; remaining open R3 bugs are dispositioned (fix-this-sprint / fix-Sprint-006 / won't-fix-with-rationale).

---

## 8. Why this round matters

Round 1 + Round 2 confirmed the form *works for the happy path with reliable internet on a desktop browser*. Field rollout will hit:
- Real Android tablets (different from desktop Chrome)
- Spotty connections at rural facilities
- HCWs interrupting the form to see patients (resume scenarios)
- Real respondent text with quotes, special chars, and copy-paste from notes
- Tokens emailed/Slack-pasted with trailing whitespace

Round 3's new-scenarios bundle is your last cheap chance to find the field-rollout blockers before pretest pilot. Verify-shipped is bookkeeping (the rules are unit-tested), but a tester finding a regression on real devices would still surface it.

Thanks for testing!
