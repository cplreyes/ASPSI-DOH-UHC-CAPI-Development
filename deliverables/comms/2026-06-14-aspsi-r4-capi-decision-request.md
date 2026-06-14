---
type: deliverable
kind: decision-request
audience: ASPSI survey-design (Dr. Myra Silva-Javier · Merlyne) · routed via Kidd
prepared_by: Carl Patrick L. Reyes
reporter: Marriz (GitHub mmgarciano) — F3 Patient Survey UAT tester
date_drafted: 2026-06-14
status: draft-for-Carl-review-before-sending
tags: [comms, decision-request, aspsi, capi, f3, uat-round-4, questionnaire-design]
---

# F3 Patient Survey — CAPI UAT Round 4 Decision Request

**Purpose.** Every routing, translation, and validation finding from the R4 F3 sweep (issues #488–#515, plus carried-over items) has been fixed and deployed **except** the items below — these are questionnaire-content/design calls that only ASPSI can make. The development side is done and waiting on each one.

**How to use.** Each row is a *confirm-this* or a short *either/or*. I've pre-filled a **recommended answer** with the rationale and noted what it unblocks and the build effort once confirmed. For most you can reply **"confirm"** (or amend). All are F3; none block the other instruments.

**Reporter.** Every item below was raised by a single F3 tester — **Marriz** (GitHub `mmgarciano`) — during her Round 4 F3 walkthrough on 2026-06-13/14 (the same sweep as issues #488–#515). These are a field-tester's flags, not yet ASPSI-design positions. The **Route** note on each row says whether it's a design call for Dr. Myra / Merlyne or something **Marriz can likely confirm herself** (the concrete gaps she identified).

> Context: F3 R4 is otherwise cleared — 15 deploys this round closed ~80 findings (routing, Tagalog, 'Other (specify)' boxes, facility-name piping). These 6 decisions + 2 translation strings are the remaining gate.

---

## Section 1 — Questionnaire design & content decisions

| # | Decision needed | Recommended answer (confirm / amend) | Unblocks · effort · route |
|---|---|---|---|
| 1 | **Mid-interview withdrawal path.** If a respondent withdraws partway, the enumerator currently can't reach the Result/disposition screen to record "not completed" — all gated answers are required first. How should a break-off be recorded? | **Add a "respondent withdrew" toggle on the Field-Control form** that jumps straight to the Result-of-Visit disposition and ends the case. Please confirm the **disposition code** to record (e.g. *"Partially completed — respondent withdrew"*). Alternative: leave as-is (enumerator discards the case — loses the partial + the reason). | **#515** · ~half-day once the disposition code is given · **Route: Dr. Myra** (field-flow design) |
| 2 | **GAMOT block area-gating.** Q152–Q159 are meant only for respondents in **areas with the GAMOT program**, but nothing in F3 captures area-level GAMOT availability (Q152 only asks individual *awareness*). | **Is there a definitive list of GAMOT-program areas?** If **yes** → send it and I'll auto-gate Q152–Q159 by the captured location (cleanest, zero enumerator burden). If **no** → keep Q152 ("heard of GAMOT?") as the entry + the on-screen enumerator note (current behaviour). | **#495** · auto-gate = moderate (needs the area list); keep-as-is = none · **Route: Dr. Myra / sampling** (is there a GAMOT-area list?) |
| 3 | **Q178 "Not applicable" option.** Q178 (satisfaction with the referral) includes option 6 "Not applicable", but Q178 is only asked when Q162 = Yes (a referral exists), so the tester flags it as redundant. | **Clarify what Q178 rates.** If it rates the **referral act** (always rateable once a referral is made) → **remove option 6**. If it rates the **visit experience** (Q169 can be "not yet visited") → **keep 6** for the not-yet-visited case. The spec already soft-warns when Q169 = Yes and Q178 = 6. | **#514** · trivial (remove a value) once decided · **Route: Dr. Myra** (Q178 intent) |
| 4 | **Q157 "got everything from GAMOT" value.** Q157 ("where did you get the **rest** of the medicines") has no option for a respondent who obtained **all** their medicines from GAMOT (no remainder). | **Add a value** such as *"Got all medicines from GAMOT — not applicable"*. Please supply the **exact English wording** (and its Tagalog) and I'll add it. | **#500** · trivial (add a value) once wording given · **Route: Marriz can likely confirm** (a gap she found) |
| 5 | **Q148 "medicines" field (reads as a duplicate of Q147).** After the 2026-06-12 Q148 redesign, there's an extra free-text "medicines" field after the Q148 condition checkboxes that looks like a duplicate of Q147 (medications list). | **What is Q148 meant to capture?** If Q147 already captures the full meds list → **drop the Q148 medicines-text field** (conditions-only). If you want a **condition ↔ medicine linkage** → keep it but **relabel clearly** (e.g. *"Which medicine(s) for which condition?"*). This also resolves the "Q147 = NONE → how to answer Q148?" question. | **#491** (+ #490 follow-up) · drop = trivial; relabel = small · **Route: Dr. Myra** (Q148 redesign intent) |
| 6 | **Q150 exact paper wording.** The tester asks that Q150 carry the **exact paper-questionnaire wording** (the CAPI currently uses a short label). This is an English-content change, so it's your call. | **Send the exact Q150 text** you want shown and I'll update the English label; the Tagalog follows. (Per our translations-only rule, I won't change survey wording without your confirmation.) | **#493** · trivial once wording given · **Route: Dr. Myra / Merlyne** (content owner) |

---

## Section 2 — Tagalog strings to supply

Two option labels have **no translation in the ASPSI Filipino source** (v2.1.2), so they currently render in English. Not decisions — just need the strings. (I will **not** machine-translate them.) **Route: Marriz / whoever holds the Filipino source.**

| # | Where | English option | Needed |
|---|---|---|---|
| 7 | Q149 (where you buy/receive medicines) | **"Barangay Health Station"** | Tagalog |
| 8 | Q177 (why you chose a hospital) | **"ZBB eligibility"** | Tagalog |

---

## What's NOT in this sheet (so you know it's handled)

- **All routing/skip bugs, Tagalog for the main questions + option lists, section scripts, 'Other (specify)' boxes, and facility-name piping** — fixed and deployed; testers retest after remove + re-add.
- **Device-dependent** items (e.g. the #391 crash) — blocked on the test-device / emulator path, not on you.
- One thing to **verify on retest, not decide**: facility-name piping renders the captured name — if it shows blank, the facility capture step needs wiring (we'll know from the retest).

*Prepared for Carl's review before any send. All items raised by Marriz (`mmgarciano`), F3 UAT tester, R4 sweep 2026-06-13/14 — see the per-row **Route** for who answers each. The design-level calls (#515, #495, #514, #491) need Dr. Myra; #500 + the two translation strings Marriz can likely confirm herself.*
