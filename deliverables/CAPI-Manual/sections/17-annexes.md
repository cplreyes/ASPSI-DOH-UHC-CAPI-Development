<!--
CAPI Manual — Section XVII. Annexes
Quick-reference cards + tables. Code-list annexes B (status), C (result codes), D (errors) are
filled from the live F1/F3/F4 value sets (PatientSurvey/FacilityHeadSurvey/HouseholdSurvey .dcf:
ENUM_RESULT_FIRST/FINAL_VISIT, BREAKOFF, CASE_DISPOSITION; .apc errmsg strings) as of 2026-06-28.
H (support contacts) is the one ASPSI-supplied item — names/numbers are filled by ASPSI at release.
-->

# XVII. Annexes

Quick-reference cards to print or keep on the tablet. The code lists below are taken **directly from the deployed F1/F3/F4 instruments** (their result-of-visit, interview-status, and disposition value sets, and the apps' own error messages).

---

## A. CAPI Login Quick Guide

1. Open **CSEntry** → tap **LoginApp** → green **➕**.
2. Enter **username**, advance; enter **password**, advance.
3. **Check the role banner** is yours (e.g. `se-004 — Enumerator`).
4. Tap your tool (**F1 / F3 / F4**) to start.
5. To switch user / end the day: **exit back to LoginApp**.
*Errors:* "Incorrect password." → re-type · "Unknown username." → update LoginApp · "No role found…" → sign in via LoginApp. (**§IV**)

---

## B. Case / Assignment Status Codes

Two things describe a case's status: what you **see in the CSEntry case list**, and the app's **automatic disposition code** (`CASE_DISPOSITION`, stored with every case and visible on the server).

**What you see in the case list:**

| Status | Meaning | Next step |
|---|---|---|
| Not started | On your sheet, key not yet entered | Start it (**§IX**) |
| Partial (in progress) | Started, not yet accepted — saved | Resume + finish (**§XII·6**) |
| Complete | Finished and **Accepted** | Sync / hand to supervisor (**§XIII**) |
| Synced | Reached the server (merged by key) | Keep on tablet until confirmed |

**Automatic disposition code (`CASE_DISPOSITION`, set by the app):**

| Code | Disposition |
|---|---|
| **0** | In progress |
| **1** | Completed |
| **2** | Partial / not completed |

---

## C. Final Result Codes

These are the exact **Result of Visit** codes built into each tool (recorded at the closing screen for the first and, where used, the final visit). **They differ by instrument** — use the row set for the tool you are in.

**F1 — Facility Head**

| Code | Result of visit |
|---|---|
| **1** | Completed |
| **2** | Postponed |
| **3** | Refused |
| **4** | Incomplete |

**F3 — Patient**

| Code | Result of visit |
|---|---|
| **1** | Completed |
| **2** | Completed at the Hospital |
| **3** | Postponed |
| **4** | Incomplete |
| **5** | Completed at Home |
| **6** | Withdraw Participation / Consent |

**F4 — Household**

| Code | Result of visit |
|---|---|
| **1** | Completed |
| **2** | Postponed |
| **3** | Incomplete |
| **4** | Withdraw Participation / Consent |

**Interview status (`BREAKOFF`) — same in all three tools.** Leave on **Continue** unless you must end early; choosing 2–4 routes you straight to the closing result and skips the remaining questions.

| Code | Interview status |
|---|---|
| **1** | Continue interview |
| **2** | Respondent withdrew |
| **3** | Postponed / reschedule |
| **4** | Stop — other (incomplete) |

---

## D. Common Error Messages and Solutions

Grouped by type, with **real examples from the F1/F3/F4 tools**. Wording varies by question; the *kind* of message tells you what to do.

**Sign-in (LoginApp)**

| Message | Means | Do |
|---|---|---|
| "Incorrect password." | Password didn't match | Re-type (case-sensitive) (**§IV·4**) |
| "Unknown username." | Account not in this build | Update / re-add LoginApp (**§IV·7**) |
| "No role found from login…" | Opened a tool without LoginApp | Sign in via LoginApp (**§IV·4**) |

**Out-of-range (a value is outside what's allowed)** — re-enter a valid value.

| Example message | Do |
|---|---|
| "Age must be 0–120." / "Age (NN) is below 18 — a facility head must be an adult. Please re-enter." | Correct the entry (**§XI·6**) |
| "Household size must be 1–30." / "Birth month must be 1–12." / "Birth year must be between 1900 and …" | Enter a value in range |
| "Amount cannot be negative." | Enter 0 or a positive amount |

**Consistency / cross-check (two answers disagree)** — fix whichever is wrong.

| Example message | Do |
|---|---|
| "Final-visit date cannot be earlier than the first-visit date." | Correct the date (**§XI·7**) |
| "Children (NN) cannot exceed household size (NN)." | Reconcile the two counts |
| "NN day(s) of stay but 0 nights — nights cannot be 0 …" | Correct days/nights |

**Multi-select / "Other"** — answer the prompt before moving on.

| Example message | Do |
|---|---|
| "Tick at least one payment source before continuing." | Select ≥1 option (**§XI·3**) |
| "'Other' was ticked — please specify." | Type the "Other" text |
| "Please enter an amount greater than 0 — you selected this as a paid source." | Enter the amount, or untick the source |

**Case / sync / hub**

| Message | Means | Do |
|---|---|---|
| "Case could not be found" | Case already removed/synced (lifecycle) | Not data loss; check list, ask supervisor (**§XII·6**) |
| "No supervisor host found" | Bluetooth host not started | Host taps Assign/Collect first (**§XIV·1**) |

---

## E. Daily Sync Checklist (enumerator)

- [ ] All today's interviews **completed and accepted** (**§XII·4**).
- [ ] Tablet has a **working connection** (or plan to use the supervisor **Collect → Relay**).
- [ ] Run **Sync** in each tool used (**§XIII·2**).
- [ ] Saw the **success** message for each.
- [ ] Nothing left **unsynced** on the tablet overnight.
- [ ] Tablet **charging** for tomorrow.

---

## F. Supervisor CAPI Checklist

- [ ] Each enumerator has their **EA + target** (Assign Enumeration Area) (**§XIV·1**).
- [ ] Bluetooth on for assign/collect handoffs.
- [ ] **Collect Interviews from Enumerators** at day's end (**§XIV·2**).
- [ ] **Relay Collected Interviews to CSWeb** with internet (**§XIV·3**).
- [ ] **Coverage report** (and CSWeb) checked against targets (**§XIV·4**).
- [ ] Any case needing correction sent back to the enumerator to fix + re-send (**§XIV·6**).
- [ ] Nothing stranded on a tablet.

---

## G. Troubleshooting Decision Tree

```
Problem?
├─ Can't sign in? ─────────→ §IV·4 (errors) / §IV·5 (password) → still stuck → escalate §XV·L
├─ No assignments? ────────→ supervisor re-send §VI·2
├─ Stuck mid-interview? ───→ required field / check §XI·6–7 ; frozen → close+reopen (work saved) §XV·E
├─ GPS won't fix? ─────────→ outdoors + Location on + wait §VIII·1
├─ Can't sync? ────────────→ check internet + CSWeb login §XIII·5 ; stale → remove+re-add
├─ Bluetooth (hub)? ───────→ host starts first §XIV·1
└─ Lost/stolen/damaged? ──→ report to supervisor IMMEDIATELY §XVI·F
```

---

## H. CAPI Support Contact List

> 📝 **This is the only field left for ASPSI to fill at release** — the names and numbers depend on the round's roster. Print this page and complete it during training; everything else in this manual is final.

| Role | Name | Contact (call / text / Viber) | For |
|---|---|---|---|
| Team supervisor | ______________________ | ______________________ | Day-to-day field issues, credentials, reassignment |
| CAPI / IT support | ______________________ | ______________________ | App won't open, sync/Bluetooth failures, device escalations |
| Data manager | ______________________ | ______________________ | CSWeb / data questions, missing synced cases |
| Survey coordinator (ASPSI) | ______________________ | ______________________ | Protocol questions, schedule, escalation of last resort |

*Tip: save these four numbers in the tablet's contacts before fieldwork, and keep this card in the field bag.*

---

**Related sections:** all — these annexes summarise the procedures in §I–XVI.
