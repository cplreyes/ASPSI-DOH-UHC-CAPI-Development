# CAPI UAT Round 4 — Plan & End-to-End Field Test (F1 / F3 / F4)

**Instruments:** F1 Facility Head · F3 Patient · F4 Household (CSPro/CSEntry → CSWeb)
**Build under test:** the 2026-06-12 Round-4 build (see "What's new" below)
**Mirror of:** the F2 PWA UAT process (same GitHub repo, labels, and feedback flow)
**Status:** plan — opens when the R4 build is deployed to CSWeb and the 3 Slack channels exist

---

## 1. Goal
Prove the three CAPI instruments work end-to-end **the way a real fieldwork day runs** — from an enumerator installing the app, through the interview, the nightly sync, to stakeholders monitoring the data on CSWeb — and capture every issue in GitHub so we can triage → fix → verify to zero, exactly like the F2 rounds.

## 2. What's new in the R4 build (what testers should notice)
- **Combined-view screens** — related questions are grouped on one page instead of one-per-screen (≈5–6× fewer taps).
- **GPS auto-fetch** — coordinates fill in by themselves (no "Capture GPS" button); fields lock once a fix is found.
- **Verification photo at the END** — the last step, and **only when the visit actually happened** (Completed/Incomplete); skipped for Refused/Postponed/Withdraw.
- **Other-specify gating** — the "specify" box appears/required only when "Other" is ticked; cleared/skipped otherwise.
- **Exclusive-option warning** — ticking "None"/"I don't know"/"Not applicable" with other options shows a soft warning.
- **Single 12-digit Questionnaire Number** with auto-filled Region/Province/City names; date pickers; auto-advance.

## 3. Roles & Slack channels
| Role | Who | What they do in R4 | Channel |
|---|---|---|---|
| **Enumerator (tester)** | ASPSI SEs | Install → run the scenario interviews → sync → file findings | per instrument below |
| **Team Leader / STL** | ASPSI STL | End-of-day reconciliation; sanity-check per-stream counts; reproduce issues | same channels |
| **Monitor / Stakeholder** | ASPSI (Kidd/Myra) + DOH | Watch CSWeb (Sync Report, map, counts) — confirm cases arrive & look right | `#capi-development` |
| **Dev (Carl)** | — | Triage GitHub issues → fix → re-deploy → ask for re-verify | all |

**Per-instrument tester channels (create these):** **`#f1-uat`**, **`#f3-uat`**, **`#f4-uat`**.

## 4. Demo data
Same valid test facility for all three — prefix **`010280001`** (Region I / Ilocos Norte test facility, passes PSGC validation). Each tester appends their **3-digit number**; use the per-instrument ranges so cases don't collide on the server:

| Instrument | App name | QN range | Example | Notes |
|---|---|---|---|---|
| **F1** | FacilityHeadSurvey | `010280001` + **1xx** | `010280001101` | facility GPS + photo |
| **F3** | PatientSurvey | `010280001` + **5xx** | `010280001501` | Patient Type (OP/IP); patient-home address cascade; 2 GPS |
| **F4** | HouseholdSurvey | `010280001` + **6xx** | `010280001601` | household roster (multiple members); HH GPS |

- **Server:** `https://csweb.asiansocial.org/csweb/api` · **Login:** `setest` / *(admin-provided)* · sync direction = upload (`put`).
- Each tester uses a **distinct last-3-digits per case** (e.g. 101, 102…). The team can pre-assign blocks per tester.
- Enter **reasonable but obviously-test** values; one **Completed** and one **Refused** case per tester at minimum.

## 5. Test scenarios (= the dropdown in the GitHub form)
| ID | Scenario | F1 | F3 | F4 |
|---|---|:--:|:--:|:--:|
| TC-1 | Completed interview (full walk, GPS, photo, sync) | ✓ | ✓ | ✓ |
| TC-2 | Refused / Withdrawn — interview ends, **no photo** | ✓ | ✓ | ✓ |
| TC-3 | Partial save + resume | ✓ | ✓ | ✓ (mid-roster) |
| TC-4 | "Other (specify)" appears only when Other ticked | ✓ | ✓ | ✓ |
| TC-5 | Select-all + exclusive-option warning | ✓ | ✓ | ✓ |
| TC-6 | Patient-type routing (Outpatient vs Inpatient) | — | ✓ | — |
| Roster | Repeating members — asks once each, stops at the count | — | — | ✓ |

Full step-by-step is in each tester guide: `docs/F1-…`, `docs/F3-…`, `docs/F4-CSEntry-Tester-Install-and-Test-Guide-2026-06.md`.

## 6. End-to-end fieldwork flow (what we're really testing)
```
Enumerator                        Server (CSWeb, Elestio)            Monitor / Stakeholder
──────────                        ───────────────────────            ─────────────────────
Install CSEntry  ─┐
Download app from CSWeb ──────────►  app package served
Run interview (TC-1…)
  GPS auto + photo at end
Sync (upload, put) ───────────────►  case stored ──► nightly
                                     csweb:process-cases (5-min cron)
                                     breaks case into the F1/F3/F4
                                     breakout DB ──────────────────►  Sync Report tab: case appears
                                                                      Map Report: GPS pin shows
                                                                      Per-stream counts update
STL end-of-day reconcile ◄──────────────────────────────────────────  counts cross-checked vs field tally
File finding in GitHub  ──► triage (Carl) ──► fix ──► re-deploy ──► tester re-verifies
```
**Monitor checklist (CSWeb, `https://csweb.asiansocial.org/csweb/`):** after testers sync, confirm for each instrument — (a) the case shows in **Sync Report**; (b) the **View case** modal opens and the answers look right; (c) the **Map Report** pin appears for cases with a real GPS fix (desk cases are blank); (d) per-stream **counts** look correct (F3 OP vs IP). *(GPS pins need a real outdoor fix — indoor/desk test cases will be blank, which is expected.)*

## 7. Raising issues in GitHub (just like F2)
- **Form:** `https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/new?template=capi_uat_feedback.yml` — tester picks **Instrument**, **Scenario**, **Result**, describes it, attaches a screenshot. Auto-labelled `uat-feedback` + `from-uat-round-4-capi-2026-06`.
- **Triage** adds the instrument epic label (`epic:f1` / `epic:f3` / `epic:f4`), a `severity:*`, and links it to that instrument's **R4 tracking issue**.
- **Tracking issues (one per instrument):** **F1 → #368 · F3 → #369 · F4 → #370** — roll up all findings for that instrument; mirror the F2 `#271`-style tracker. Driven to zero via the `uat-round-closeout` workflow.
- **Flow:** file → triage → `status:investigating` → fix + re-deploy → `status:fixed-pending-verify` → tester re-tests → close.

## 8. Exit criteria (round closes when)
- Every tester completed **TC-1 + TC-2** on their instrument and synced successfully.
- Each instrument's **Completed** case is **visible + correct in CSWeb** (Sync Report + counts), with a GPS pin for at least one real-outdoor case.
- All filed issues are **dispositioned** (fixed-and-verified, or deferred with a reason) — open count driven to **0** per instrument.
- F4 **roster** and F3 **OP/IP routing** confirmed working on a real device.

## 9. Setup checklist (before opening the round)
- [ ] **Deploy the R4 build ×3 to CSWeb** (the standard handoff — carries combined views + photo move/gate + other-specify + exclusivity + F1 G1/G2/G3).
- [ ] **Create the 3 Slack channels** `#f1-uat` `#f3-uat` `#f4-uat`; add testers + STLs; pin the relevant tester guide in each.
- [ ] **Commit + push** the new issue form `.github/ISSUE_TEMPLATE/capi_uat_feedback.yml` so the GitHub links work.
- [x] `from-uat-round-4-capi-2026-06` label + the 3 R4 tracking issues created (**#368 F1 · #369 F3 · #370 F4**).
- [ ] Pre-assign each tester a **QN block** (last-3-digits) per the ranges above.
- [ ] Share the per-instrument **tester guide** + the **setest** password with each tester.
- [ ] *(Optional)* extend the existing `uat-slack-*` GitHub Actions to post new F1/F3/F4 issues into the matching channel.

---
*Companion files: the three tester guides in `docs/`, the issue form `.github/ISSUE_TEMPLATE/capi_uat_feedback.yml`, and the R4 tracking issues in GitHub.*
