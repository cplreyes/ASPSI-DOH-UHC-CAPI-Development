# F2 PWA — UAT Guide for ASPSI Staff

**Version:** v1.1.0 UAT Round 1
**Staging URL:** https://5466a539.f2-pwa-staging.pages.dev
**Bug Report Link:** https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/new?template=uat_feedback.yml
**UAT Coordinator:** Carl Patrick Reyes (carlpatricklreyes@gmail.com)

---

## Before You Start

1. Open **Chrome** on your tablet or laptop. The app works best on Chrome.
2. Navigate to the staging URL above.
3. **Do not use your real HCW ID.** Use the test IDs provided by the UAT coordinator.
4. After each test scenario, file your result using the Bug Report Link above.

---

## Test Personas

Run the full scenario set twice — once per persona:

| Persona | HCW ID (test) | Role to select | Notes |
|---------|---------------|---------------|-------|
| Persona A | `UAT-NURSE-01` | Nurse | Tests clinical-care sections (C, D) |
| Persona B | `UAT-PHYS-01` | Physician/Doctor | Tests physician section (G) |

---

## Test Scenarios

### TC-001 — Enrollment (fresh device)

**Goal:** Confirm a new user can enroll successfully.

**Steps:**
1. Open the staging URL. You should see the Enroll screen.
2. Enter HCW ID: `UAT-NURSE-01`
3. Tap **Refresh facility list**. Wait for the list to populate.
4. Select any facility from the dropdown.
5. Tap **Enroll**.

**Expected:** The form opens showing Section A — Healthcare Worker Profile.

---

### TC-002 — Section A: Healthcare Worker Profile

**Goal:** Confirm all required fields in Section A can be answered.

**Steps:**
1. After TC-001, you are on Section A.
2. Fill in your name fields (Last, First, Middle).
3. Select your employment type.
4. Select sex at birth.
5. Enter age (must be 18 or older).
6. Select your role.
7. Answer whether you practice at a private facility.
8. Enter tenure at this facility (years and months).
9. Enter days per week and hours per day.

**Expected:** After filling the last required field, the form automatically advances to Section B within 1 second.

---

### TC-003 — Auto-advance

**Goal:** Confirm the form moves to the next section automatically when all required fields are filled.

**Steps:**
1. In any incomplete section, fill in the last required field.
2. Do not click any button.

**Expected:** The form slides to the next section automatically within about 1 second.

---

### TC-004 — Section Navigation Lock

**Goal:** Confirm you cannot skip ahead to a future section.

**Steps:**
1. While on Section A (before filling all required fields), open the section menu (tap the ☰ icon on mobile, or look at the left sidebar on desktop).
2. Try clicking on Section C, D, or any section you have not yet reached.

**Expected:** A message appears saying "Complete sections in order — finish the current section first." Section C does not open.

---

### TC-005 — Language Switch

**Goal:** Confirm the form displays correctly in Filipino.

**Steps:**
1. Tap the language toggle in the top-right corner. Switch to **Filipino**.
2. Scroll through Section A and read the question labels.
3. Switch back to **English**.

**Expected:** All questions change language immediately. No data is lost when switching.

---

### TC-006 — Save Draft and Resume

**Goal:** Confirm an in-progress form can be saved and resumed.

**Steps:**
1. Fill in a few fields in Section A but do not complete the section.
2. Tap **Save Draft** (top-right of the form area).
3. Close the browser tab completely.
4. Reopen the staging URL.

**Expected:** The form resumes from where you left off. All previously entered data is still there.

---

### TC-007 — Complete All Sections A–J

**Goal:** Walk through the complete survey from start to finish.

**Steps:**
1. Starting from Section A, fill all required fields in each section.
2. Let the form auto-advance, or use the **→** arrow button to advance manually.
3. Continue through all 10 sections (A through J).
4. After Section J, the form should show the **Review** screen.

**Expected:** All 10 sections appear with a green checkmark ✓ in the section menu. The Review screen shows all your answers grouped by section.

**Things to watch for:**
- Questions that appear or disappear based on earlier answers (skip logic)
- The section menu on the left/top showing green ✓, red ✗, or grey status per section
- Any question that looks confusing or incorrectly worded

---

### TC-008 — Review and Edit

**Goal:** Confirm answers can be corrected before final submission.

**Steps:**
1. On the Review screen, find any section.
2. Tap the **Edit** button next to that section.
3. Change one answer.
4. Tap **Next** to return to the review.

**Expected:** The Review screen reflects the changed answer. No other answers are lost.

---

### TC-009 — Final Submit

**Goal:** Confirm the form submits successfully.

**Steps:**
1. On the Review screen, tap **Submit**.

**Expected:** A "Thank you" screen appears confirming the response is saved. The Sync page shows one pending submission.

---

### TC-010 — Offline Behavior

**Goal:** Confirm the app works without internet and syncs when reconnected.

**Steps:**
1. Complete enrollment (TC-001) while online.
2. Turn off Wi-Fi / airplane mode on your device.
3. Fill in Section A and save the draft.
4. Turn Wi-Fi back on.
5. Go to the **Sync** tab.
6. Tap **Sync now**.

**Expected:** The submission status changes to "Synced" after a few seconds.

---

## Section Quick Reference

| Section | Topic | Required Questions |
|---------|-------|--------------------|
| A | Healthcare Worker Profile | Name, employment type, sex, age, role, private practice, tenure, workload |
| B | UHC Awareness | 13 yes/no questions about UHC implementation |
| C | YAKAP/Konsulta | Awareness and practice on PhilHealth packages |
| D | No Balance Billing (NBB/ZBB) | Awareness on billing policies |
| E | BUCAS and GAMOT | Awareness of health programs |
| F | Referrals and Satisfaction | Referral methods and satisfaction rating |
| G | KAP — Professional Setting | Charging, reimbursement, clinical practices (Physician/Dentist only) |
| H | Task Sharing | Scope of practice and task sharing |
| I | Facility Support | Support from the facility |
| J | Job Satisfaction | 25 satisfaction and intention questions |

---

## How to Report a Bug

1. Click: https://github.com/cplreyes/ASPSI-DOH-UHC-CAPI-Development/issues/new?template=uat_feedback.yml
2. Fill in the form — you need a free GitHub account, or email your report to the UAT coordinator.
3. Include: which test scenario, what happened, what you expected, and a screenshot if possible.

---

## Known Issues (Out of Scope for Round 1)

- Section titles are not yet translated to Filipino (English placeholders in use).
- Facility list is populated from a test server — in production, your real facility will appear.

---

## Sign-off

After completing all 10 test scenarios with Persona A and Persona B, email the UAT coordinator with:

> "I have completed UAT Round 1. Result: [Pass / Pass with comments / Fail]. Comments: [...]"

Final approval is required from the ASPSI lead before production deployment.
